"""Transport-independent Hisys MCP tool wrappers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from hisys.operations.release_readiness import GateStatus

from hisys.environment_config import environment_config_status
from hisys.operations.health import collect_health_status
from hisys.operations.release_readiness import QualityGateResult, build_release_readiness_report

from .cli_adapter import run_hisys_cli
from .contracts import McpToolResultEnvelope

BASE_TOOL_NAMES = [
    "health_status",
    "environment_status",
    "investigate_domain",
    "list_run_artifacts",
    "show_artifact",
    "release_readiness",
]
FUTURE_TOOL_NAMES = ["altas_status", "dars_status", "judge_status"]


def _safe_ref(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _blocked(tool_name: str, error: str) -> McpToolResultEnvelope:
    return McpToolResultEnvelope(status="blocked", tool_name=tool_name, error=error)


def _artifact_ref_is_safe(ref: str) -> bool:
    path = Path(ref)
    return not path.is_absolute() and ".." not in path.parts and path.suffix in {".json", ".md"}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {"value": value}


def list_hisys_mcp_tool_names(*, expose_future_tools: bool = False) -> list[str]:
    names = list(BASE_TOOL_NAMES)
    if expose_future_tools:
        names.extend(FUTURE_TOOL_NAMES)
    return names


def hisys_health_status(*, instance_root: str | Path, date: str) -> McpToolResultEnvelope:
    root = Path(instance_root)
    report = collect_health_status(root)
    payload = report.model_dump(mode="json")
    payload.update(
        {
            "schema_id": "hisys.health_status_report",
            "schema_version": "0.1.0",
            "external_call_made": False,
            "mutation_performed": False,
            "publication_or_live_action_approved": False,
            "execution_authorized": False,
        }
    )
    report_dir = root / "reports" / "run-summaries" / date
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "hisys-health-status.json"
    md_path = report_dir / "hisys-health-status.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# Hisys Health Status",
                "",
                f"- overall_status: `{payload['overall_status']}`",
                "- external_call_made: `false`",
                "- mutation_performed: `false`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return McpToolResultEnvelope(
        status="ok" if report.overall_status == "ok" else "needs_more_evidence",
        tool_name="health_status",
        artifact_refs=[_safe_ref(root, json_path), _safe_ref(root, md_path)],
        payload=payload,
    )


def hisys_show_artifact(*, instance_root: str | Path, artifact_ref: str) -> McpToolResultEnvelope:
    if not _artifact_ref_is_safe(artifact_ref):
        return _blocked("show_artifact", f"unsafe or unsupported artifact ref: {artifact_ref}")
    root = Path(instance_root).resolve()
    path = (root / artifact_ref).resolve()
    if not str(path).startswith(str(root)):
        return _blocked("show_artifact", f"unsafe artifact ref: {artifact_ref}")
    if not path.is_file():
        return McpToolResultEnvelope(status="error", tool_name="show_artifact", error=f"artifact not found: {artifact_ref}")
    text = path.read_text(encoding="utf-8")
    payload: dict[str, Any] = {"ref": artifact_ref, "text": text}
    if path.suffix == ".json":
        payload["json"] = _read_json(path)
    return McpToolResultEnvelope(status="ok", tool_name="show_artifact", artifact_refs=[artifact_ref], payload=payload)


def hisys_list_run_artifacts(
    *, instance_root: str | Path, date: str, request_id: str | None = None
) -> McpToolResultEnvelope:
    root = Path(instance_root)
    search_roots = [root / "reports" / "run-summaries" / date, root / "data" / "evidence-packages" / date]
    refs: list[str] = []
    artifacts: list[dict[str, Any]] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for path in sorted([*search_root.glob("*.json"), *search_root.glob("*.md")]):
            if request_id and request_id not in path.name:
                # Preserve run-summary files only when no request-specific filter is needed.
                if "run-summaries" not in path.as_posix():
                    continue
            ref = _safe_ref(root, path)
            refs.append(ref)
            artifacts.append({"ref": ref, "format": path.suffix.lstrip("."), "bytes": path.stat().st_size})
    return McpToolResultEnvelope(
        status="ok",
        tool_name="list_run_artifacts",
        artifact_refs=refs,
        payload={"date": date, "request_id": request_id, "artifacts": artifacts},
    )


def hisys_environment_status(*, environment_config: str | Path) -> McpToolResultEnvelope:
    payload = environment_config_status(environment_config)
    payload["command_args"] = ["environment-status", "--config", str(environment_config), "--format", "json"]
    return McpToolResultEnvelope(status="ok", tool_name="environment_status", payload=payload)


def _request_mentions_live_action(request: dict[str, Any]) -> bool:
    if request.get("allow_live_actions") is True:
        return True
    for source in request.get("sources", []) or []:
        if isinstance(source, dict) and str(source.get("source_type", "")).lower() in {"web", "public_web", "live"}:
            return True
    return False


def hisys_investigate_domain(*, instance_root: str | Path, request: dict[str, Any], date: str) -> McpToolResultEnvelope:
    if _request_mentions_live_action(request):
        return _blocked("investigate_domain", "live source or live action request rejected without explicit MCP approval contract")
    return McpToolResultEnvelope(
        status="needs_more_evidence",
        tool_name="investigate_domain",
        payload={"date": date, "instance_root": str(instance_root), "formal_hisys_status": "not_run_from_mcp_first_slice"},
    )


def hisys_release_readiness(
    *,
    instance_root: str | Path,
    date: str,
    quality_gates: list[str],
    trace_refs: list[str],
    known_gaps: list[str],
) -> McpToolResultEnvelope:
    parsed_gates: list[QualityGateResult] = []
    for item in quality_gates:
        parts = item.split(":", 2)
        if len(parts) == 3:
            parsed_gates.append(QualityGateResult(name=parts[0], status=cast(GateStatus, parts[1]), evidence=parts[2]))
    report = build_release_readiness_report(
        runtime_root=instance_root,
        quality_gates=parsed_gates,
        trace_path_refs=trace_refs,
        known_gaps=known_gaps,
    )
    root = Path(instance_root)
    report_dir = root / "reports" / "run-summaries" / date
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "hisys-release-readiness.json"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return McpToolResultEnvelope(
        status="ok" if report.overall_status == "ready_for_review" else "needs_more_evidence",
        tool_name="release_readiness",
        artifact_refs=[_safe_ref(root, json_path)],
        payload=report.model_dump(mode="json"),
    )


__all__ = [
    "hisys_environment_status",
    "hisys_health_status",
    "hisys_investigate_domain",
    "hisys_list_run_artifacts",
    "hisys_release_readiness",
    "hisys_show_artifact",
    "list_hisys_mcp_tool_names",
    "run_hisys_cli",
]
