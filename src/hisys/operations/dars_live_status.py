"""Local DARS live/unattended operations status surface.

Traceability:
- HISYS-FR-DARS-CP-014
- HISYS-T-DARS-CP-016
- DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK

The status surface is local/read-only. It reports refs and bounded state only;
it does not read credentials, resolve provider secrets, authorize live calls,
activate standing approval, mutate runtime state, publish artifacts, or execute
rollback actions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "hisys.dars_live.status"
SCHEMA_VERSION = "0.1.0"
TRACEABILITY = ["HISYS-FR-DARS-CP-014", "HISYS-T-DARS-CP-016"]


def build_dars_live_status(
    *,
    instance_root: Path,
    yyyymmdd: str,
    policy_refs: list[str],
    standing_approval_ref: str,
    kill_switch_ref: str,
    budget_state_ref: str,
    rollback_runbook_ref: str,
    release_ref: str,
) -> dict[str, Any]:
    """Build a deterministic local DARS live status packet from refs only."""

    instance_root = instance_root.resolve()
    latest_runs = _collect_latest_boundary_refs(instance_root=instance_root, yyyymmdd=yyyymmdd)
    failed_run_count = sum(1 for run in latest_runs if run["status"] != "completed")
    kill_switch = _read_kill_switch(instance_root=instance_root, ref=kill_switch_ref)
    budget = _read_budget_state(instance_root=instance_root, ref=budget_state_ref)
    latest_boundary_refs = [str(run["ref"]) for run in latest_runs]
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "traceability": TRACEABILITY,
        "date": yyyymmdd,
        "policy_refs": list(policy_refs),
        "standing_approval": {
            "ref": standing_approval_ref,
            "activated": False,
            "activation_note": "status reporting does not activate standing approval",
        },
        "kill_switch": kill_switch,
        "budget": budget,
        "latest_boundary_refs": latest_boundary_refs,
        "latest_runs": latest_runs,
        "failed_run_count": failed_run_count,
        "circuit_breakers": {
            "failed_run_count": failed_run_count,
            "state": "attention_required" if failed_run_count else "nominal",
        },
        "rollback": {
            "runbook_ref": rollback_runbook_ref,
            "readiness": "documented" if rollback_runbook_ref else "missing_runbook_ref",
            "instructions_summary": [
                "revoke_standing_approval",
                "disable_provider_policy",
                "rotate_credential_outside_hisys",
                "stop_scheduler_outside_hisys",
                "verify_no_further_runs",
            ],
        },
        "release_ref": release_ref,
        "boundary_flags": {
            "external_call_made": False,
            "credential_lookup_performed": False,
            "mutation_performed": False,
            "publication_performed": False,
            "live_action_authorized": False,
            "standing_approval_activated": False,
        },
        "privacy": {
            "raw_boundary_payload_included": False,
            "credential_values_included": False,
            "refs_only": True,
        },
    }


def _read_kill_switch(*, instance_root: Path, ref: str) -> dict[str, Any]:
    payload = _read_json_ref(instance_root=instance_root, ref=ref)
    if payload is None:
        return {"ref": ref, "available": False, "engaged": True, "reason": "kill_switch_file_missing"}
    return {
        "ref": ref,
        "available": True,
        "engaged": bool(payload.get("kill_switch_engaged", payload.get("engaged", False))),
        "reason": str(payload.get("reason", "unspecified")),
    }


def _read_budget_state(*, instance_root: Path, ref: str) -> dict[str, Any]:
    payload = _read_json_ref(instance_root=instance_root, ref=ref)
    if payload is None:
        return {"state_ref": ref, "available": False}
    return {
        "state_ref": ref,
        "available": True,
        "budget_cap_ref": str(payload.get("budget_cap_ref", "unknown")),
        "used_usd": payload.get("used_usd", "unknown"),
    }


def _read_json_ref(*, instance_root: Path, ref: str) -> dict[str, Any] | None:
    if not ref or ref.startswith("/") or ".." in Path(ref).parts:
        return None
    path = instance_root / ref
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _collect_latest_boundary_refs(*, instance_root: Path, yyyymmdd: str) -> list[dict[str, Any]]:
    boundary_root = instance_root / "runtime-boundary" / "dars-unattended-advisory" / yyyymmdd
    if not boundary_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for path in sorted(boundary_root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        runs.append(
            {
                "ref": path.relative_to(instance_root).as_posix(),
                "request_id": str(payload.get("request_id", path.stem)),
                "status": str(payload.get("status", "unknown")),
                "completed_at": str(payload.get("completed_at", payload.get("created_at", "unknown"))),
                "failure_code": str(payload.get("failure_code", "")),
            }
        )
    return sorted(runs, key=lambda item: (item["completed_at"], item["ref"]), reverse=True)


def write_dars_live_status_report(*, instance_root: Path, yyyymmdd: str, status: dict[str, Any]) -> dict[str, str]:
    """Persist JSON and Markdown status reports under reports/run-summaries."""

    report_dir = instance_root / "reports" / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_ref = f"reports/run-summaries/{yyyymmdd}/dars-live-status.json"
    markdown_ref = f"reports/run-summaries/{yyyymmdd}/dars-live-status.md"
    (instance_root / json_ref).write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (instance_root / markdown_ref).write_text(render_dars_live_status_markdown(status), encoding="utf-8")
    return {"json_ref": json_ref, "markdown_ref": markdown_ref}


def render_dars_live_status_text(status: dict[str, Any], *, json_ref: str) -> str:
    flags = status["boundary_flags"]
    kill_switch = status["kill_switch"]
    return (
        "dars live status: "
        f"kill_switch_engaged={str(kill_switch.get('engaged', True)).lower()} "
        f"failed_run_count={status.get('failed_run_count', 0)} "
        f"latest_boundary_refs={len(status.get('latest_boundary_refs', []))} "
        f"live_action_authorized={str(flags['live_action_authorized']).lower()} "
        f"standing_approval_activated={str(flags['standing_approval_activated']).lower()} "
        f"report={json_ref}"
    )


def render_dars_live_status_markdown(status: dict[str, Any]) -> str:
    flags = status["boundary_flags"]
    kill_switch = status["kill_switch"]
    return "\n".join(
        [
            "# DARS Live Operations Status",
            "",
            f"- schema: `{status['schema_id']}@{status['schema_version']}`",
            f"- date: `{status['date']}`",
            f"- policy_refs: `{', '.join(status.get('policy_refs', []))}`",
            f"- standing_approval_ref: `{status['standing_approval']['ref']}`",
            f"- kill_switch_ref: `{kill_switch.get('ref', '')}`",
            f"- kill_switch_engaged: `{str(kill_switch.get('engaged', True)).lower()}`",
            f"- budget_state_ref: `{status['budget'].get('state_ref', '')}`",
            f"- failed_run_count: `{status.get('failed_run_count', 0)}`",
            f"- latest_boundary_refs: `{', '.join(status.get('latest_boundary_refs', [])) or 'none'}`",
            f"- rollback_runbook_ref: `{status['rollback']['runbook_ref']}`",
            f"- release_ref: `{status['release_ref']}`",
            f"- external_call_made: `{str(flags['external_call_made']).lower()}`",
            f"- credential_lookup_performed: `{str(flags['credential_lookup_performed']).lower()}`",
            f"- mutation_performed: `{str(flags['mutation_performed']).lower()}`",
            f"- publication_performed: `{str(flags['publication_performed']).lower()}`",
            f"- live_action_authorized: `{str(flags['live_action_authorized']).lower()}`",
            f"- standing_approval_activated: `{str(flags['standing_approval_activated']).lower()}`",
            "",
            "This status report is local/read-only evidence. It does not authorize live provider calls, standing approval activation, rollback execution, publication, deployment, or external notification.",
            "",
        ]
    )
