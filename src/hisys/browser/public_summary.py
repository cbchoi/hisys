"""Public browser beta run summary artifacts."""

from __future__ import annotations

import json
from typing import Mapping

from ..config import InstanceRoot


def write_public_browser_run_summary(
    *,
    instance: InstanceRoot,
    yyyymmdd: str,
    request_id: str,
    topic: str,
    source_urls: list[str],
    transport_kinds: list[str],
    final_decision: str,
    remaining_blockers: list[str],
    refs: Mapping[str, str],
    external_call_made: bool,
    mutation_performed: bool,
) -> str:
    """Write one public-beta operator summary without approving live/public action."""

    if mutation_performed:
        raise ValueError("public browser run summary cannot record mutation_performed=true")

    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_ref = f"reports/run-summaries/{yyyymmdd}/public-browser-run-summary.json"
    payload = {
        "schema_id": "hisys.public_browser_run_summary",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "source_urls": source_urls,
        "transport_kinds": transport_kinds,
        "external_call_made": external_call_made,
        "mutation_performed": False,
        "final_decision": final_decision,
        "remaining_blockers": remaining_blockers,
        "publication_or_live_action_approved": False,
        "human_approval_required_for_consequential_use": True,
        "action_taken": "none",
        "artifact_refs": dict(refs),
    }
    summary_path = instance.root / summary_ref
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.with_suffix(".md").write_text(_render_public_browser_run_summary_md(payload), encoding="utf-8")
    return summary_ref


def _render_public_browser_run_summary_md(payload: Mapping[str, object]) -> str:
    refs = payload.get("artifact_refs", {})
    ref_lines = []
    if isinstance(refs, Mapping):
        ref_lines = [f"- {key}: `{value}`" for key, value in refs.items()]
    blocker_lines = [f"- {item}" for item in payload.get("remaining_blockers", [])]
    if not blocker_lines:
        blocker_lines = ["- none"]
    return "\n".join(
        [
            "# Public Browser Run Summary",
            "",
            f"- request_id: `{payload['request_id']}`",
            f"- topic: {payload['topic']}",
            f"- final_decision: `{payload['final_decision']}`",
            f"- transport_kinds: `{', '.join(str(item) for item in payload.get('transport_kinds', []))}`",
            f"- external_call_made: `{str(payload['external_call_made']).lower()}`",
            f"- mutation_performed: `{str(payload['mutation_performed']).lower()}`",
            f"- publication_or_live_action_approved: `{str(payload['publication_or_live_action_approved']).lower()}`",
            f"- action_taken: `{payload['action_taken']}`",
            "",
            "Human approval is still required for any public, live, consequential, publication, outreach, or mutation action.",
            "",
            "## Artifact refs",
            "",
            *ref_lines,
            "",
            "## Remaining blockers",
            "",
            *blocker_lines,
            "",
        ]
    )
