"""Browser workflow report rendering and persistence helpers."""

from __future__ import annotations

import json
from pathlib import Path

from ..config import InstanceRoot


def _browser_investigation_report(
    *,
    request_id: str,
    topic: str,
    user_opinion: str,
    status: str,
    reason_code: str | None,
    source_urls: list[str],
    source_access_refs: list[str],
    source_evidence_refs: list[str],
    transport_kinds: list[str],
    domain_decision_policy: str,
    resolved_allowed_domains: list[str],
    orchestrator_domain_decision_ref: str | None,
    evidence_package_ref: str | None,
    memo_ref: str | None,
    external_call_made: bool,
    followed_source_urls: list[str] | None = None,
    source_candidates_ref: str | None = None,
    competitive_matrix_ref: str | None = None,
    evidence_sufficiency_ref: str | None = None,
) -> dict[str, object]:
    return {
        "schema_id": "hisys.browser_investigation.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "user_opinion": user_opinion,
        "connector_id": "playwright_read_only",
        "status": status,
        "reason_code": reason_code,
        "source_urls": source_urls,
        "followed_source_urls": followed_source_urls or [],
        "pages_collected": len(source_access_refs),
        "source_access_refs": source_access_refs,
        "source_evidence_refs": source_evidence_refs,
        "transport_kinds": transport_kinds,
        "domain_decision_policy": domain_decision_policy,
        "resolved_allowed_domains": resolved_allowed_domains,
        "orchestrator_domain_decision_ref": orchestrator_domain_decision_ref,
        "evidence_package_ref": evidence_package_ref,
        "source_candidates_ref": source_candidates_ref,
        "competitive_matrix_ref": competitive_matrix_ref,
        "evidence_sufficiency_ref": evidence_sufficiency_ref,
        "memo_ref": memo_ref,
        "external_call_made": external_call_made,
        "mutation_performed": False,
    }


def _write_browser_investigation_report(instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "browser-investigation-report.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = report_dir / "browser-investigation-report.md"
    md_path.write_text(
        "\n".join(
            [
                "# Browser Investigation Report",
                "",
                f"- request_id: `{report['request_id']}`",
                f"- connector_id: `{report['connector_id']}`",
                f"- status: `{report['status']}`",
                f"- pages_collected: `{report['pages_collected']}`",
                f"- external_call_made: `{report['external_call_made']}`",
                f"- mutation_performed: `{report['mutation_performed']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return json_path


def _render_browser_chief_editor_review_md(review: dict[str, object]) -> str:
    return "\n".join([
        f"# Chief Editor Browser Review {review['request_id']}",
        "",
        f"- decision: `{review['decision']}`",
        f"- review_readiness: `{review.get('review_readiness')}`",
        f"- action_taken: `{review['action_taken']}`",
        f"- external_call_made: `{str(review['external_call_made']).lower()}`",
        f"- mutation_performed: `{str(review['mutation_performed']).lower()}`",
        "",
        "## Questions for Devil/DARS",
        "",
        *[f"- {item}" for item in review.get("chief_editor_questions_for_devil_dars", [])],
        "",
    ])


def _render_browser_dars_handoff_md(handoff: dict[str, object]) -> str:
    return "\n".join([
        f"# DARS handoff {handoff['handoff_id']}",
        "",
        f"- target_agent_system: {handoff['target_agent_system']}",
        f"- task: {handoff['task']}",
        f"- allowed_actions: {handoff['allowed_actions']}",
        f"- status: {handoff['status']}",
        f"- evidence_bundle: {', '.join(str(item) for item in handoff['evidence_bundle'])}",
        "",
    ])


def _render_browser_dars_review_md(review: dict[str, object]) -> str:
    findings = [str(item) for item in review.get("adversarial_findings", [])]
    revisions = [str(item) for item in review.get("required_revisions", [])]
    return "\n".join([
        f"# DARS Browser Review {review['request_id']}",
        "",
        f"- decision: `{review['decision']}`",
        f"- allowed_actions: `{review['allowed_actions']}`",
        f"- external_call_made: `{str(review['external_call_made']).lower()}`",
        f"- mutation_performed: `{str(review['mutation_performed']).lower()}`",
        "",
        "## Adversarial Findings",
        "",
        *[f"- {item}" for item in findings],
        "",
        "## Required Revisions",
        "",
        *[f"- {item}" for item in revisions],
        "",
    ])


def _render_browser_dars_revision_resolution_md(resolution: dict[str, object]) -> str:
    return "\n".join([
        f"# Browser DARS Revision Resolution {resolution['request_id']}",
        "",
        f"- decision: `{resolution['decision']}`",
        f"- segment_normalization_status: `{resolution['segment_normalization_status']}`",
        f"- corroboration_mapping_status: `{resolution['corroboration_mapping_status']}`",
        f"- final_acceptance_allowed: `{str(resolution['final_acceptance_allowed']).lower()}`",
        f"- external_call_made: `{str(resolution['external_call_made']).lower()}`",
        f"- mutation_performed: `{str(resolution['mutation_performed']).lower()}`",
        "",
        "## Remaining Blockers",
        "",
        *[f"- {item}" for item in resolution.get("remaining_blockers", [])],
        "",
    ])


def _render_browser_dars_revision_report_md(report: dict[str, object]) -> str:
    return "\n".join([
        "# Browser DARS Revision Resolution Report",
        "",
        f"- request_id: `{report['request_id']}`",
        f"- decision: `{report['decision']}`",
        f"- revision_resolution_ref: `{report['revision_resolution_ref']}`",
        f"- external_call_made: `{str(report['external_call_made']).lower()}`",
        f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
        "",
    ])


def _render_final_browser_acceptance_review_md(review: dict[str, object]) -> str:
    return "\n".join([
        f"# Final Browser Acceptance Review {review['request_id']}",
        "",
        f"- decision: `{review['decision']}`",
        f"- acceptance_scope: `{review['acceptance_scope']}`",
        f"- revision_resolution_ref: `{review['revision_resolution_ref']}`",
        f"- publication_or_live_action_approved: `{str(review['publication_or_live_action_approved']).lower()}`",
        f"- human_approval_required_for_consequential_use: `{str(review['human_approval_required_for_consequential_use']).lower()}`",
        f"- action_taken: `{review['action_taken']}`",
        f"- external_call_made: `{str(review['external_call_made']).lower()}`",
        f"- mutation_performed: `{str(review['mutation_performed']).lower()}`",
        "",
        "## Accepted Conditions",
        "",
        *[f"- {item}" for item in review.get("accepted_conditions", [])],
        "",
    ])


def _render_final_browser_acceptance_report_md(report: dict[str, object]) -> str:
    return "\n".join([
        "# Final Browser Acceptance Review Report",
        "",
        f"- request_id: `{report['request_id']}`",
        f"- decision: `{report['decision']}`",
        f"- final_review_ref: `{report['final_review_ref']}`",
        f"- publication_or_live_action_approved: `{str(report['publication_or_live_action_approved']).lower()}`",
        f"- external_call_made: `{str(report['external_call_made']).lower()}`",
        f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
        "",
    ])

