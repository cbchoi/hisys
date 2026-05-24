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
import re
from typing import Any

SCHEMA_ID = "hisys.dars.r4h_hermes_mediated_productization_prep"
SCHEMA_VERSION = "0.1.0"
ACCEPTED_CLAIM = "r4h_hermes_mediated_productization_prep_ready_for_human_review"
TRACEABILITY = ["HISYS-FR-DARS-CP-012", "HISYS-T-DARS-CP-014"]
HARNESS_SCHEMA_ID = "hisys.dars.r4h_request_response_harness"
HARNESS_ACCEPTED_CLAIM = "r4h_hermes_mediated_request_response_harness_closed_for_human_review"
REQUEST_SCHEMA_ID = "hisys.dars.r4h_hermes_mediated_request"
RESPONSE_SCHEMA_ID = "hisys.dars.r4h_hermes_mediated_response"
SUPPORTED_CRITIC_ROLES = ("logical_consistency_critic", "evidence_governance_critic")
FORBIDDEN_REQUEST_FIELDS = (
    "raw_prompt_secret",
    "credential_ref",
    "api_key",
    "mutation_authority",
    "publication_authority",
    "release_authority",
)
_REQUEST_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")


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
        "supported_critic_roles": list(SUPPORTED_CRITIC_ROLES),
        "request_contract": {
            "schema_id": REQUEST_SCHEMA_ID,
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
            "schema_id": RESPONSE_SCHEMA_ID,
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

def validate_r4h_hermes_mediated_request(request: dict[str, Any]) -> dict[str, Any]:
    """Validate a local R4H Hermes-mediated advisory request packet."""

    issue_codes: list[str] = []
    if request.get("schema_id") != REQUEST_SCHEMA_ID:
        issue_codes.append("schema_id_mismatch")

    required_fields = [
        "request_id",
        "objective",
        "candidate_refs",
        "evidence_refs",
        "critic_roles",
        "human_review_ref",
    ]
    for field_name in required_fields:
        if not request.get(field_name):
            issue_codes.append(f"missing_field:{field_name}")

    for field_name in FORBIDDEN_REQUEST_FIELDS:
        if field_name in request:
            issue_codes.append(f"forbidden_field:{field_name}")

    request_id = str(request.get("request_id", ""))
    if request_id and not _REQUEST_ID_RE.fullmatch(request_id):
        issue_codes.append("invalid_request_id")

    for field_name in ("candidate_refs", "evidence_refs"):
        refs = request.get(field_name, [])
        if not isinstance(refs, list) or not all(isinstance(ref, str) and _is_controlled_ref(ref) for ref in refs):
            issue_codes.append(f"invalid_{field_name}")

    critic_roles = request.get("critic_roles", [])
    if not isinstance(critic_roles, list):
        issue_codes.append("invalid_critic_roles")
    else:
        for role in critic_roles:
            if role not in SUPPORTED_CRITIC_ROLES:
                issue_codes.append(f"unsupported_critic_role:{role}")

    human_review_ref = str(request.get("human_review_ref", ""))
    if "human-review-required" not in human_review_ref:
        issue_codes.append("human_review_ref_missing_required_marker")

    return {"valid": not issue_codes, "issue_codes": issue_codes}


def build_r4h_request_response_harness(
    *, yyyymmdd: str, request: dict[str, Any], fixture_findings: dict[str, list[str]] | None = None
) -> dict[str, Any]:
    """Build a local fixture/injected R4H request-response harness packet."""

    validation = validate_r4h_hermes_mediated_request(request)
    roles = [role for role in request.get("critic_roles", []) if role in SUPPORTED_CRITIC_ROLES]
    fixture_findings = fixture_findings or {
        "logical_consistency_critic": [
            "R4H request/response schema is internally consistent with the productization-prep contract."
        ],
        "evidence_governance_critic": [
            "Harness execution is fixture-injected and preserves no-action, no-credential, and human-review boundaries."
        ],
    }
    critic_findings = {role: fixture_findings.get(role, []) for role in roles}
    response_status = "completed" if validation["valid"] else "blocked"
    boundary_flags = {
        "fixture_injected_harness": True,
        "hermes_mediated_model_call_made": False,
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
    }
    response = {
        "schema_id": RESPONSE_SCHEMA_ID,
        "schema_version": "0.1.0",
        "request_id": request.get("request_id", ""),
        "status": response_status,
        "critic_findings": critic_findings,
        "aggregate_findings": [
            "R4H request/response harness is locally closed for human review."
            if validation["valid"]
            else "R4H request/response harness is blocked by request validation issues."
        ],
        "boundary_flags": boundary_flags,
        "human_review_required_for_consequential_use": True,
    }
    return {
        "schema_id": HARNESS_SCHEMA_ID,
        "schema_version": "0.1.0",
        "date": yyyymmdd,
        "traceability": TRACEABILITY,
        "accepted_claim": HARNESS_ACCEPTED_CLAIM,
        "active_branch": "R4H",
        "active_transport_kind": "fixture_injected_hermes_mediated_contract_harness",
        "request": request,
        "request_validation": validation,
        "response": response,
        "boundary_flags": boundary_flags,
        "active_evidence_refs": [
            "docs/reports/dars-r4h-hermes-mediated-productization-prep-2026-05-24.md",
            "docs/examples/dars/hermes-mediated-r4h-productization-prep.example.json",
        ],
        "not_accepted_upgrades": [
            "r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings",
            "codex_cli_subprocess_prompt_mode_completed",
            "raw_provider_api_readiness",
            "adapter_native_readiness",
            "bounded_unattended_advisory_operation_ready",
            "release_candidate_ready",
            "released_for_controlled_advisory_use",
        ],
        "next_safe_task": "DARS-LIVE-RELEASE-R7-RC-SCOPE-DECISION",
    }


def write_r4h_request_response_harness_report(
    *, instance_root: Path, yyyymmdd: str, packet: dict[str, Any]
) -> dict[str, str]:
    """Persist the R4H request/response harness packet as JSON and Markdown."""

    report_dir = instance_root / "reports" / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_ref = f"reports/run-summaries/{yyyymmdd}/dars-r4h-request-response-harness.json"
    markdown_ref = f"reports/run-summaries/{yyyymmdd}/dars-r4h-request-response-harness.md"
    (instance_root / json_ref).write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (instance_root / markdown_ref).write_text(render_r4h_request_response_harness_markdown(packet), encoding="utf-8")
    return {"json_ref": json_ref, "markdown_ref": markdown_ref}


def render_r4h_request_response_harness_markdown(packet: dict[str, Any]) -> str:
    """Render a deterministic R4H request/response harness report."""

    flags = packet["boundary_flags"]
    validation = packet["request_validation"]
    return "\n".join(
        [
            "# DARS R4H request/response harness",
            "",
            f"- schema: `{packet['schema_id']}@{packet['schema_version']}`",
            f"- accepted_claim: `{packet['accepted_claim']}`",
            f"- active_branch: `{packet['active_branch']}`",
            f"- active_transport_kind: `{packet['active_transport_kind']}`",
            f"- request_id: `{packet['request'].get('request_id', '')}`",
            f"- request_valid: `{str(validation['valid']).lower()}`",
            f"- issue_codes: `{', '.join(validation['issue_codes']) or '-'}`",
            f"- fixture_injected_harness: `{str(flags['fixture_injected_harness']).lower()}`",
            f"- hermes_mediated_model_call_made: `{str(flags['hermes_mediated_model_call_made']).lower()}`",
            f"- codex_cli_subprocess_call: `{str(flags['codex_cli_subprocess_call']).lower()}`",
            f"- raw_provider_api_call_by_hisys: `{str(flags['raw_provider_api_call_by_hisys']).lower()}`",
            f"- credential_lookup_by_hisys: `{str(flags['credential_lookup_by_hisys']).lower()}`",
            f"- mutation_performed: `{str(flags['mutation_performed']).lower()}`",
            f"- publication_performed: `{str(flags['publication_performed']).lower()}`",
            f"- release_action_performed: `{str(flags['release_action_performed']).lower()}`",
            f"- requires_human_review: `{str(flags['requires_human_review']).lower()}`",
            "",
            "This is not a live model/provider or Codex subprocess execution claim.",
            "The harness closes only the local request/response contract for human review.",
            "",
        ]
    )


def render_r4h_request_response_harness_text(packet: dict[str, Any]) -> str:
    """Render a one-line R4H harness summary."""

    flags = packet["boundary_flags"]
    return (
        "dars r4h request/response harness: "
        f"accepted_claim={packet['accepted_claim']} "
        f"request_valid={str(packet['request_validation']['valid']).lower()} "
        f"fixture_injected_harness={str(flags['fixture_injected_harness']).lower()} "
        f"requires_human_review={str(flags['requires_human_review']).lower()}"
    )


def _is_controlled_ref(value: str) -> bool:
    return value.startswith(("docs/", "reports/", "runtime-boundary/")) and "://" not in value


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
