"""R4H Hermes-mediated DARS productization-prep surface.

Traceability:
- HISYS-FR-DARS-CP-012
- HISYS-T-DARS-CP-014
- DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-PRODUCTIZATION-PREP

This module records a governed request/response contract for the R4H
Hermes-mediated advisory path. It does not call Hermes, Codex, a raw provider API,
or any external service; it writes only local prep artifacts and preserves human
review as mandatory for consequential use.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "hisys.dars.r4h_hermes_mediated_productization_prep"
SCHEMA_VERSION = "0.1.0"
ACCEPTED_CLAIM = "r4h_hermes_mediated_productization_prep_ready_for_human_review"
TRACEABILITY = ["HISYS-FR-DARS-CP-012", "HISYS-T-DARS-CP-014"]


def build_r4h_productization_prep(*, yyyymmdd: str) -> dict[str, Any]:
    """Build the local/read-only R4H productization-prep packet."""

    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "date": yyyymmdd,
        "traceability": TRACEABILITY,
        "accepted_claim": ACCEPTED_CLAIM,
        "active_branch": "R4H",
        "active_transport_kind": "hermes_mediated_model_advisory",
        "active_evidence_refs": [
            "docs/reports/dars-r4h-hermes-mediated-panel-advisory-2026-05-24.md",
            "docs/examples/dars/hermes-mediated-r4h-multi-critic-panel.advisory.json",
            "docs/reports/dars-r4h-hermes-mediated-panel-review-gate-proceed-2026-05-24.md",
        ],
        "supported_use_cases": [
            "human-reviewed advisory critique of a bounded candidate and evidence set",
            "logical consistency review of claim-ladder and branch-disposition packets",
            "evidence-governance review of no-mutation/no-publication/no-credential boundaries",
        ],
        "supported_critic_roles": [
            "logical_consistency_critic",
            "evidence_governance_critic",
        ],
        "request_contract": {
            "schema_id": "hisys.dars.r4h_hermes_mediated_request",
            "required_fields": [
                "request_id",
                "objective",
                "candidate_refs",
                "evidence_refs",
                "critic_roles",
                "human_review_ref",
            ],
            "forbidden_fields": [
                "raw_prompt_secret",
                "credential_ref",
                "api_key",
                "mutation_authority",
                "publication_authority",
                "release_authority",
            ],
            "constraints": {
                "candidate_refs_are_local_or_controlled_refs": True,
                "evidence_refs_are_local_or_controlled_refs": True,
                "critic_roles_subset_of_supported_roles": True,
                "allowed_actions": "advisory_only",
                "requires_human_review": True,
            },
        },
        "response_contract": {
            "schema_id": "hisys.dars.r4h_hermes_mediated_response",
            "required_fields": [
                "request_id",
                "critic_findings",
                "aggregate_findings",
                "boundary_flags",
                "human_review_required_for_consequential_use",
            ],
            "allowed_statuses": ["completed", "blocked", "failed"],
            "claim_boundary": "Hermes-mediated advisory findings only; no Codex subprocess or raw-provider readiness claim",
        },
        "report_contract": {
            "json_ref_pattern": "reports/run-summaries/<YYYYMMDD>/dars-r4h-productization-prep.json",
            "markdown_ref_pattern": "reports/run-summaries/<YYYYMMDD>/dars-r4h-productization-prep.md",
            "operator_message_required": "This is not a Codex CLI subprocess success claim.",
        },
        "deferred_transport_relation": {
            "deferred_branch": "R4C",
            "deferred_transport_kind": "codex_cli_subprocess_prompt_mode",
            "deferred_reason": "Codex CLI refresh_token_reused before critique output or panel boundary evidence",
            "future_task": "DARS-LIVE-RELEASE-R4C-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS",
            "r4c_is_not_blocker_for_r4h_productization_prep": True,
        },
        "boundary_flags": {
            "codex_cli_subprocess_call": False,
            "codex_cli_subprocess_completion_claim": False,
            "raw_provider_api_call_by_hisys": False,
            "raw_provider_api_readiness": False,
            "adapter_native_readiness": False,
            "r5_unattended_readiness": False,
            "r7_release_candidate_readiness": False,
            "r8_release_execution_readiness": False,
            "credential_lookup_by_hisys": False,
            "mutation_performed": False,
            "publication_performed": False,
            "external_notification_performed": False,
            "release_action_performed": False,
            "allowed_actions": "advisory_only",
            "requires_human_review": True,
            "human_review_required_for_consequential_use": True,
        },
        "not_accepted_upgrades": [
            "r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings",
            "codex_cli_subprocess_prompt_mode_completed",
            "raw_provider_api_readiness",
            "adapter_native_readiness",
            "bounded_unattended_advisory_operation_ready",
            "release_candidate_ready",
            "released_for_controlled_advisory_use",
        ],
        "next_safe_task": "DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-REQUEST-RESPONSE-HARNESS",
    }


def write_r4h_productization_prep_report(
    *, instance_root: Path, yyyymmdd: str, packet: dict[str, Any]
) -> dict[str, str]:
    """Persist the productization-prep packet as JSON and Markdown reports."""

    report_dir = instance_root / "reports" / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_ref = f"reports/run-summaries/{yyyymmdd}/dars-r4h-productization-prep.json"
    markdown_ref = f"reports/run-summaries/{yyyymmdd}/dars-r4h-productization-prep.md"
    (instance_root / json_ref).write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (instance_root / markdown_ref).write_text(render_r4h_productization_prep_markdown(packet), encoding="utf-8")
    return {"json_ref": json_ref, "markdown_ref": markdown_ref}


def render_r4h_productization_prep_markdown(packet: dict[str, Any]) -> str:
    """Render a deterministic operator-facing Markdown report."""

    flags = packet["boundary_flags"]
    deferred = packet["deferred_transport_relation"]
    return "\n".join(
        [
            "# DARS R4H Hermes-mediated productization prep",
            "",
            f"- schema: `{packet['schema_id']}@{packet['schema_version']}`",
            f"- accepted_claim: `{packet['accepted_claim']}`",
            f"- active_branch: `{packet['active_branch']}`",
            f"- active_transport_kind: `{packet['active_transport_kind']}`",
            f"- request_schema: `{packet['request_contract']['schema_id']}`",
            f"- response_schema: `{packet['response_contract']['schema_id']}`",
            f"- supported_critic_roles: `{', '.join(packet['supported_critic_roles'])}`",
            f"- deferred_branch: `{deferred['deferred_branch']}`",
            f"- future_r4c_task: `{deferred['future_task']}`",
            f"- codex_cli_subprocess_call: `{str(flags['codex_cli_subprocess_call']).lower()}`",
            f"- raw_provider_api_call_by_hisys: `{str(flags['raw_provider_api_call_by_hisys']).lower()}`",
            f"- credential_lookup_by_hisys: `{str(flags['credential_lookup_by_hisys']).lower()}`",
            f"- mutation_performed: `{str(flags['mutation_performed']).lower()}`",
            f"- publication_performed: `{str(flags['publication_performed']).lower()}`",
            f"- release_action_performed: `{str(flags['release_action_performed']).lower()}`",
            f"- requires_human_review: `{str(flags['requires_human_review']).lower()}`",
            "",
            "This is not a Codex CLI subprocess success claim.",
            "This prep packet does not authorize raw provider API calls, credential lookup, mutation, publication, release action, external notification, or removal of human review.",
            "",
        ]
    )


def render_r4h_productization_prep_text(packet: dict[str, Any]) -> str:
    """Render a one-line operator summary."""

    flags = packet["boundary_flags"]
    return (
        "dars r4h productization prep: "
        f"accepted_claim={packet['accepted_claim']} "
        f"active_transport_kind={packet['active_transport_kind']} "
        f"requires_human_review={str(flags['requires_human_review']).lower()} "
        f"codex_cli_subprocess_call={str(flags['codex_cli_subprocess_call']).lower()}"
    )
