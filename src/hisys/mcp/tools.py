"""Transport-independent Hisys MCP tool wrappers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from hisys.operations.release_readiness import GateStatus

from hisys.environment_config import environment_config_status
from hisys.operations.health import collect_health_status
from hisys.operations.release_readiness import QualityGateResult, build_release_readiness_report

from .cli_adapter import redact_text, run_hisys_cli, summarize_cli_error
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


def _subsystem_status_placeholder(tool_name: str, subsystem: str, readiness_command: list[str] | None = None) -> McpToolResultEnvelope:
    payload: dict[str, Any] = {
        "subsystem": subsystem,
        "implemented": False,
        "gateway_routing_placeholder": True,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    if readiness_command is not None:
        payload["readiness_command_pending_wrap"] = readiness_command
    return McpToolResultEnvelope(
        status="blocked",
        tool_name=tool_name,
        payload=payload,
        error=f"{subsystem} status gateway placeholder is unimplemented; no subsystem command was executed",
    )


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


def hisys_altas_status() -> McpToolResultEnvelope:
    """Fail-closed ALTAS gateway routing placeholder.

    This lane intentionally does not call subsystem commands; it only exposes a
    future tool shape when explicitly requested by tool listing.
    """

    return _subsystem_status_placeholder("altas_status", "ALTAS")


def hisys_dars_status() -> McpToolResultEnvelope:
    """Fail-closed DARS gateway routing placeholder."""

    return _subsystem_status_placeholder(
        "dars_status",
        "DARS",
        ["python", "-m", "hisys.dars.rloo", "--check", "--format", "json"],
    )


def hisys_judge_status() -> McpToolResultEnvelope:
    """Fail-closed Judge gateway routing placeholder.

    This is a readiness/status placeholder only and must not be treated as a
    final authoritative approval decision.
    """

    return _subsystem_status_placeholder(
        "judge_status",
        "Judge",
        ["python", "-m", "hisys.judge.rloo", "--check", "--format", "json"],
    )


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


def _artifact_kind(ref: str) -> str:
    if ref.startswith("reports/run-summaries/"):
        return "run_summary"
    if ref.startswith("data/chief-editor-final-browser-reviews/"):
        return "final_chief_editor_review"
    if ref.startswith("data/browser-dars-revision-resolutions/"):
        return "browser_dars_revision_resolution"
    if ref.startswith("data/dars-browser-reviews/"):
        return "dars_browser_review"
    if ref.startswith("data/chief-editor-reviews/"):
        return "chief_editor_review"
    if ref.startswith("data/evidence-packages/"):
        return "evidence_package"
    if ref.startswith("data/source-access/"):
        return "source_access"
    if ref.startswith("data/investigation-memos/"):
        return "investigation_memo"
    return "artifact"


def hisys_list_run_artifacts(
    *, instance_root: str | Path, date: str, request_id: str | None = None
) -> McpToolResultEnvelope:
    root = Path(instance_root)
    search_roots = [
        root / "reports" / "run-summaries" / date,
        root / "data" / "source-access" / date,
        root / "data" / "evidence-packages" / date,
        root / "data" / "investigation-memos" / date,
        root / "data" / "chief-editor-reviews" / date,
        root / "data" / "dars-browser-reviews" / date,
        root / "data" / "browser-dars-revision-resolutions" / date,
        root / "data" / "chief-editor-final-browser-reviews" / date,
    ]
    refs: list[str] = []
    artifacts: list[dict[str, Any]] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for path in sorted([*search_root.glob("*.json"), *search_root.glob("*.md")]):
            ref = _safe_ref(root, path)
            if request_id and request_id not in path.name and "public-browser" not in path.name:
                continue
            refs.append(ref)
            artifacts.append(
                {"ref": ref, "kind": _artifact_kind(ref), "format": path.suffix.lstrip("."), "bytes": path.stat().st_size}
            )
    return McpToolResultEnvelope(
        status="ok",
        tool_name="list_run_artifacts",
        artifact_refs=refs,
        payload={
            "schema_id": "hisys.run_artifact_index",
            "date": date,
            "request_id": request_id,
            "artifacts": artifacts,
            "external_call_made": False,
            "mutation_performed": False,
        },
    )


def hisys_environment_status(*, environment_config: str | Path) -> McpToolResultEnvelope:
    payload = environment_config_status(environment_config)
    payload["command_args"] = ["environment-status", "--config", str(environment_config), "--format", "json"]
    status = "ok" if payload.get("safe_to_use") is True else "needs_more_evidence"
    return McpToolResultEnvelope(status=status, tool_name="environment_status", payload=payload)


def _request_mentions_live_action(request: dict[str, Any]) -> bool:
    if request.get("allow_live_actions") is True:
        return True
    for source in request.get("sources", []) or []:
        if isinstance(source, dict) and str(source.get("source_type", "")).lower() in {"web", "public_web", "live"}:
            return True
    return False


def _safe_request_path(root: Path, request_path: str | Path) -> Path | None:
    path = Path(request_path)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".json":
        return None
    resolved_root = root.resolve()
    resolved = (resolved_root / path).resolve()
    if not str(resolved).startswith(str(resolved_root)):
        return None
    return resolved


def _repo_src_path() -> str:
    return str(Path(__file__).resolve().parents[2])


def _cli_env() -> dict[str, str]:
    src_path = _repo_src_path()
    existing = os.environ.get("PYTHONPATH")
    return {"PYTHONPATH": f"{src_path}{os.pathsep}{existing}" if existing else src_path}


def _dedupe_refs(refs: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        deduped.append(ref)
    return deduped


def _safe_existing_artifact_refs(root: Path, refs: list[str]) -> list[str]:
    safe_refs: list[str] = []
    for ref in refs:
        if not _artifact_ref_is_safe(ref):
            continue
        path = (root / ref).resolve()
        if str(path).startswith(str(root.resolve())) and path.is_file():
            safe_refs.append(ref)
    return _dedupe_refs(safe_refs)


def _write_inline_investigation_request(root: Path, date: str, request: dict[str, Any]) -> Path:
    request_id = str(request.get("request_id") or "MCP-INLINE-REQUEST")
    safe_request_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in request_id)
    path = root / "reports" / "run-summaries" / date / f"mcp-investigate-domain-request-{safe_request_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def hisys_investigate_domain(
    *,
    instance_root: str | Path,
    request: dict[str, Any] | None = None,
    request_path: str | Path | None = None,
    date: str,
) -> McpToolResultEnvelope:
    root = Path(instance_root)
    if request and request_path:
        return _blocked("investigate_domain", "provide either request or request_path, not both")
    if not request and not request_path:
        return _blocked("investigate_domain", "request or request_path is required")

    if request_path is not None:
        resolved_request_path = _safe_request_path(root, request_path)
        if resolved_request_path is None:
            return _blocked("investigate_domain", f"unsafe or unsupported request_path: {request_path}")
        try:
            request_payload = json.loads(resolved_request_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return McpToolResultEnvelope(status="error", tool_name="investigate_domain", error=f"could not read request_path: {exc}")
        if not isinstance(request_payload, dict):
            return _blocked("investigate_domain", "request_path JSON must be an object")
    else:
        request_payload = request or {}
        if _request_mentions_live_action(request_payload):
            return _blocked("investigate_domain", "live source or live action request rejected without explicit MCP approval contract")
        resolved_request_path = _write_inline_investigation_request(root, date, request_payload)

    if _request_mentions_live_action(request_payload):
        return _blocked("investigate_domain", "live source or live action request rejected without explicit MCP approval contract")

    result = run_hisys_cli(
        [
            sys.executable,
            "-m",
            "hisys.cli.main",
            "investigate-domain",
            "--instance",
            str(root),
            "--request",
            str(resolved_request_path),
            "--date",
            date,
        ],
        timeout_seconds=120,
        env=_cli_env(),
    )
    if result.returncode != 0:
        return McpToolResultEnvelope(
            status="error" if not result.timed_out else "blocked",
            tool_name="investigate_domain",
            error=summarize_cli_error(result),
            payload={
                "command_args": list(result.args),
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "stdout": redact_text(result.stdout),
                "stderr": redact_text(result.stderr),
            },
        )

    report_ref = f"reports/run-summaries/{date}/domain-investigation-report.json"
    report_md_ref = f"reports/run-summaries/{date}/domain-investigation-report.md"
    report = _read_json(root / report_ref)
    runtime_refs = [str(ref) for ref in report.get("runtime_boundary_refs", []) if isinstance(ref, str)]
    tool_result_ref = report.get("tool_result_ref")
    if isinstance(tool_result_ref, str) and tool_result_ref not in runtime_refs:
        runtime_refs.append(tool_result_ref)
    if isinstance(tool_result_ref, str) and tool_result_ref.endswith(".json"):
        runtime_refs.append(tool_result_ref[:-5] + ".md")
    runtime_refs.extend([report_ref, report_md_ref])
    artifact_refs = _safe_existing_artifact_refs(root, runtime_refs)
    status = "ok" if report.get("status") == "completed" and report.get("quality_gate") == "passed" else "needs_more_evidence"
    payload = {
        "schema_id": "hisys.mcp.investigate_domain_result",
        "schema_version": "0.1.0",
        **report,
        "command_args": list(result.args),
        "stdout": redact_text(result.stdout),
        "stderr": redact_text(result.stderr),
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    return McpToolResultEnvelope(status=status, tool_name="investigate_domain", artifact_refs=artifact_refs, payload=payload)


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
    md_path = report_dir / "hisys-release-readiness.md"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    return McpToolResultEnvelope(
        status="ok" if report.overall_status == "ready_for_review" else "needs_more_evidence",
        tool_name="release_readiness",
        artifact_refs=[_safe_ref(root, json_path), _safe_ref(root, md_path)],
        payload=report.model_dump(mode="json"),
    )


__all__ = [
    "hisys_altas_status",
    "hisys_dars_status",
    "hisys_environment_status",
    "hisys_health_status",
    "hisys_investigate_domain",
    "hisys_judge_status",
    "hisys_list_run_artifacts",
    "hisys_release_readiness",
    "hisys_show_artifact",
    "list_hisys_mcp_tool_names",
    "run_hisys_cli",
]
