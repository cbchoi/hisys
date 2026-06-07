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
    "altas_search",
    "dars_panel_readiness",
    "run_dars_panel_golden",
    "judge_advisory",
]
FUTURE_TOOL_NAMES = ["altas_status", "dars_status", "judge_status"]

_ALTAS_FIXTURE_SOURCE_CONNECTORS_YAML = """default_mode: fixture_only
policy:
  live_network_enabled: true
  require_human_approval_for_external_call: true
  allow_credentials: false
  allow_mutation: false
  require_allowlist: true
  require_provenance_record: true
connectors:
  general_web_search:
    connector_id: general_web_search
    connector_type: web_search
    enabled: true
    mode: read_only
    external_call_allowed: true
    requires_human_approval: true
    approval_policy_ref: POLICY-LIVE-SEARCH-001
    allowed_domains:
      - search.local.fixture
      - api.search.local.fixture
    disallowed_domains: []
    forbidden_actions:
      - login
      - credential_use
      - form_submit
      - upload
      - purchase
      - post
      - mutation
      - access_control_bypass
    output_schema: EvidencePackage
    manual_smoke_only: true
    manual_smoke_env_var: HISYS_ALLOW_LIVE_SEARCH_SMOKE
    smoke_test_in_ci: false
"""

_ALTAS_DEFAULT_FIXTURE_SEARCH = {
    "results": [
        {
            "title": "Local fixture search result for MCP altas_search",
            "url": "https://search.local.fixture/results/mcp-altas-search",
            "snippet": (
                "Fixture-injected search transport result for the MCP altas_search "
                "wrapper; no external call or live provider was contacted."
            ),
        }
    ]
}


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


_LOCAL_FIXTURE_DISCLOSURE: dict[str, Any] = {
    "result_basis": "Local fixture",
    "execution_mode": "local_fixture",
    "llm_service_used": False,
    "operator_notice": "Local fixture result: no LLM service or live provider was used.",
}


def _add_local_fixture_disclosure(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(_LOCAL_FIXTURE_DISCLOSURE)
    return payload


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

    inline_request_ref: str | None = None
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
        inline_request_ref = _safe_ref(root, resolved_request_path)

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
    if inline_request_ref is not None:
        runtime_refs.append(inline_request_ref)
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


def _ensure_altas_fixture_config(instance_root: Path) -> tuple[Path, Path]:
    config_dir = instance_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "source-connectors.yaml"
    if not config_path.exists():
        config_path.write_text(_ALTAS_FIXTURE_SOURCE_CONNECTORS_YAML, encoding="utf-8")
    fixture_path = config_dir / "fixture-search.json"
    if not fixture_path.exists():
        fixture_path.write_text(
            json.dumps(_ALTAS_DEFAULT_FIXTURE_SEARCH, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return config_path, fixture_path


def hisys_altas_search(
    *,
    instance_root: str | Path,
    date: str,
    request_id: str,
    topic: str,
    user_opinion: str | None = None,
    provider_url_ref: str | None = None,
    credential_ref: str | None = None,
    provider: str | None = None,
    provider_response_fixture: str | None = None,
) -> McpToolResultEnvelope:
    if provider_url_ref or credential_ref or provider or provider_response_fixture:
        return _blocked(
            "altas_search",
            "live provider altas_search arguments rejected; this MCP wrapper only supports fixture transport",
        )
    root = Path(instance_root)
    root.mkdir(parents=True, exist_ok=True)
    config_path, fixture_path = _ensure_altas_fixture_config(root)
    cli_args = [
        sys.executable,
        "-m",
        "hisys.cli.main",
        "search-topic",
        "--instance",
        str(root),
        "--config",
        str(config_path),
        "--date",
        date,
        "--request-id",
        request_id,
        "--topic",
        topic,
        "--approval-ref",
        "APPROVAL-MCP-ALTAS-FIXTURE-SMOKE-001",
        "--transport-fixture-search",
        str(fixture_path),
    ]
    if user_opinion:
        cli_args.extend(["--user-opinion", user_opinion])
    cli_env = _cli_env()
    cli_env["HISYS_ALLOW_LIVE_SEARCH_SMOKE"] = "1"
    result = run_hisys_cli(cli_args, timeout_seconds=120, env=cli_env)
    command_args = [
        "search-topic",
        "--instance",
        str(root),
        "--config",
        str(config_path),
        "--date",
        date,
        "--request-id",
        request_id,
        "--topic",
        topic,
        "--approval-ref",
        "APPROVAL-MCP-ALTAS-FIXTURE-SMOKE-001",
        "--transport-fixture-search",
        str(fixture_path),
    ]
    report_ref = f"reports/run-summaries/{date}/search-topic-report.json"
    report = _read_json(root / report_ref)
    report_status_completed = report.get("status") == "completed"
    payload: dict[str, Any] = _add_local_fixture_disclosure({
        "schema_id": "hisys.mcp.altas_search.v1",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "transport_kind": "fixture_injected",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
        "live_external_action_authorized": False,
        "command_args": command_args,
        "search_topic_report": report,
        "stdout": redact_text(result.stdout),
        "stderr": redact_text(result.stderr),
        "returncode": result.returncode,
        "timed_out": result.timed_out,
    })
    artifact_refs = _safe_existing_artifact_refs(root, [report_ref])
    if result.returncode != 0 or not report_status_completed:
        return McpToolResultEnvelope(
            status="needs_more_evidence",
            tool_name="altas_search",
            artifact_refs=artifact_refs,
            payload=payload,
            error=summarize_cli_error(result) if result.returncode != 0 else None,
        )
    return McpToolResultEnvelope(
        status="ok",
        tool_name="altas_search",
        artifact_refs=artifact_refs,
        payload=payload,
    )


def hisys_dars_panel_readiness(
    *, instance_root: str | Path, date: str
) -> McpToolResultEnvelope:
    root = Path(instance_root)
    root.mkdir(parents=True, exist_ok=True)
    cli_args = [
        sys.executable,
        "-m",
        "hisys.cli.main",
        "dars-panel-readiness",
        "--instance",
        str(root),
        "--date",
        date,
        "--format",
        "json",
        "--write-report",
    ]
    result = run_hisys_cli(cli_args, timeout_seconds=120, env=_cli_env())
    report_ref = f"reports/run-summaries/{date}/dars-panel-readiness-status.json"
    report = _read_json(root / report_ref)
    payload: dict[str, Any] = _add_local_fixture_disclosure({
        "schema_id": "hisys.mcp.dars_panel_readiness.v1",
        "schema_version": "0.1.0",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "publication_or_live_action_approved": False,
        "live_external_action_authorized": False,
        "command_args": [
            "dars-panel-readiness",
            "--instance",
            str(root),
            "--date",
            date,
            "--format",
            "json",
            "--write-report",
        ],
        "readiness_report": report,
        "stdout": redact_text(result.stdout),
        "stderr": redact_text(result.stderr),
        "returncode": result.returncode,
        "timed_out": result.timed_out,
    })
    artifact_refs = _safe_existing_artifact_refs(root, [report_ref])
    if result.returncode != 0:
        return McpToolResultEnvelope(
            status="needs_more_evidence",
            tool_name="dars_panel_readiness",
            artifact_refs=artifact_refs,
            payload=payload,
            error=summarize_cli_error(result),
        )
    status = "ok" if report.get("fixture_panel_complete") is True else "needs_more_evidence"
    return McpToolResultEnvelope(
        status=status,
        tool_name="dars_panel_readiness",
        artifact_refs=artifact_refs,
        payload=payload,
    )


def hisys_run_dars_panel_golden(
    *, instance_root: str | Path, date: str, request_id: str
) -> McpToolResultEnvelope:
    root = Path(instance_root)
    root.mkdir(parents=True, exist_ok=True)
    cli_args = [
        sys.executable,
        "-m",
        "hisys.cli.main",
        "run-dars-panel-golden",
        "--instance",
        str(root),
        "--date",
        date,
        "--request-id",
        request_id,
        "--format",
        "json",
    ]
    result = run_hisys_cli(cli_args, timeout_seconds=240, env=_cli_env())
    report_ref = f"reports/run-summaries/{date}/dars-panel-round-report.json"
    report = _read_json(root / report_ref)
    payload: dict[str, Any] = _add_local_fixture_disclosure({
        "schema_id": "hisys.mcp.run_dars_panel_golden.v1",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "publication_or_live_action_approved": False,
        "live_external_action_authorized": False,
        "command_args": [
            "run-dars-panel-golden",
            "--instance",
            str(root),
            "--date",
            date,
            "--request-id",
            request_id,
            "--format",
            "json",
        ],
        "round_report": report,
        "stdout": redact_text(result.stdout),
        "stderr": redact_text(result.stderr),
        "returncode": result.returncode,
        "timed_out": result.timed_out,
    })
    artifact_refs = _safe_existing_artifact_refs(root, [report_ref])
    if result.returncode != 0:
        return McpToolResultEnvelope(
            status="needs_more_evidence",
            tool_name="run_dars_panel_golden",
            artifact_refs=artifact_refs,
            payload=payload,
            error=summarize_cli_error(result),
        )
    status = "ok" if report.get("advisory_only") is True else "needs_more_evidence"
    return McpToolResultEnvelope(
        status=status,
        tool_name="run_dars_panel_golden",
        artifact_refs=artifact_refs,
        payload=payload,
    )


def hisys_judge_advisory(
    *, instance_root: str | Path, date: str, request_id: str
) -> McpToolResultEnvelope:
    root = Path(instance_root)
    report_dir = root / "reports" / "run-summaries" / date
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "judge-advisory.json"
    md_path = report_dir / "judge-advisory.md"
    report_payload: dict[str, Any] = _add_local_fixture_disclosure({
        "schema_id": "hisys.mcp.judge_advisory.v1",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "date": date,
        "advisory_only": True,
        "requires_human_review": True,
        "decision": "advisory_pending_human_review",
        "external_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "live_external_action_authorized": False,
        "human_approval_required": True,
    })
    json_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        "\n".join(
            [
                "# Hisys MCP Judge Advisory",
                "",
                f"- request_id: `{request_id}`",
                f"- date: `{date}`",
                "- advisory_only: `true`",
                "- requires_human_review: `true`",
                "- publication_performed: `false`",
                "- live_external_action_authorized: `false`",
                "- result_basis: `Local fixture`",
                "- execution_mode: `local_fixture`",
                "- llm_service_used: `false`",
                "",
                "This advisory is bounded, fail-closed, and must be reviewed by a human ",
                "approver before any downstream publication or live action.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    envelope_payload = dict(report_payload)
    envelope_payload["publication_or_live_action_approved"] = False
    return McpToolResultEnvelope(
        status="ok",
        tool_name="judge_advisory",
        artifact_refs=[_safe_ref(root, json_path), _safe_ref(root, md_path)],
        payload=envelope_payload,
        human_approval_required=True,
    )


__all__ = [
    "hisys_altas_search",
    "hisys_altas_status",
    "hisys_dars_panel_readiness",
    "hisys_dars_status",
    "hisys_environment_status",
    "hisys_health_status",
    "hisys_investigate_domain",
    "hisys_judge_advisory",
    "hisys_judge_status",
    "hisys_list_run_artifacts",
    "hisys_release_readiness",
    "hisys_run_dars_panel_golden",
    "hisys_show_artifact",
    "list_hisys_mcp_tool_names",
    "run_hisys_cli",
]
