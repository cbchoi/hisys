"""DARS R5 bounded unattended advisory operation documentation tests.

Traceability: HISYS-FR-DARS-CP-013, HISYS-T-DARS-CP-015,
DARS-LIVE-RELEASE-R5-UNATTENDED-PREP,
docs/plans/dars-panel-live-provider-unattended-release-final-plan.md.

These tests verify R5 documentation PREP artifacts only. They run no live
provider call, read no credentials, and rely on no network access. The
standing approval validator and unattended runner are separate RED/GREEN
implementation work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "runbooks" / "dars-unattended-advisory-operation.md"
EXAMPLE_POLICY = ROOT / "docs" / "examples" / "dars" / "unattended-standing-approval.example.json"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def _walk_values(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_walk_values(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_walk_values(nested))
    return values


def test_unattended_operation_runbook_exists() -> None:
    assert RUNBOOK.exists(), f"missing runbook: {RUNBOOK}"


def test_unattended_operation_runbook_defines_standing_approval_contract() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    required_phrases = [
        "StandingApprovalPolicy",
        "DarsUnattendedAdvisoryRunner",
        "request_class_allowlist",
        "provider_policy_refs",
        "activation_packet_refs",
        "budget/rate caps",
        "kill_switch_ref",
        "kill_switch_required=true",
        "audit_ledger_ref",
        "audit_retention_ref",
        "requires_post_run_human_review=true",
        "mutation_allowed=false",
        "publication_allowed=false",
        "external_action_allowed=false",
        "advisory_only=true",
        "raw credential values",
    ]
    for phrase in required_phrases:
        assert phrase in text, phrase


def test_unattended_operation_runbook_defines_runner_and_dry_run_boundaries() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    required_phrases = [
        "dry-run rehearsal",
        "fake/injected transports only",
        "HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true",
        "mode=dry_run",
        "transport_kind=fake",
        "external_call_made=false",
        "model_boundary_crossed=false",
        "mutation_performed=false",
        "publication_performed=false",
        "external_action_performed=false",
        "post-run human review",
    ]
    for phrase in required_phrases:
        assert phrase in text, phrase


def test_unattended_operation_runbook_documents_circuit_breakers_and_stop_conditions() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    required_phrases = [
        "Circuit breaker matrix",
        "standing_approval_not_active",
        "kill_switch_ref_missing",
        "kill_switch_triggered",
        "budget_or_rate_caps_missing",
        "request_class_not_allowlisted",
        "unattended_authority_rejected",
        "provider_policy_mismatch",
        "repeated_failure_threshold_reached",
        "cost_threshold_reached",
        "secret_scan_hit",
        "output_redaction_failure",
        "operator_uncertainty",
        "Stop conditions",
        "credential lookup by Hisys",
        "browser/search/tool authority",
    ]
    for phrase in required_phrases:
        assert phrase in text, phrase


def test_unattended_standing_approval_example_has_required_safe_fields() -> None:
    data = json.loads(EXAMPLE_POLICY.read_text(encoding="utf-8"))
    assert data["policy_id"] == "DARS-UNATTENDED-STANDING-PREP-20260523-001"
    assert data["approval_ref"] == "APPROVAL-DARS-UNATTENDED-PREP-20260523-001"
    assert data["request_class_allowlist"] == ["dars_live_provider_advisory_dry_run"]
    assert data["kill_switch_required"] is True
    assert data["requires_post_run_human_review"] is True
    assert data["mutation_allowed"] is False
    assert data["publication_allowed"] is False
    assert data["external_action_allowed"] is False
    assert data["advisory_only"] is True
    assert data["max_runs"] > 0
    assert data["max_runs_per_hour"] > 0
    assert data["rate_limit_per_minute"] > 0
    assert data["max_prompt_bytes_per_run"] > 0
    assert data["max_output_bytes_per_run"] > 0
    assert data["provider_policy_refs"]
    assert data["audit_ledger_ref"] == "runtime-boundary/dars-unattended-advisory"
    assert data["audit_retention_ref"].startswith("retention://")


def test_unattended_standing_approval_example_is_reference_only() -> None:
    data = json.loads(EXAMPLE_POLICY.read_text(encoding="utf-8"))
    forbidden_keys = {"api_key", "token", "password", "authorization", "credential_value"}
    lowered_keys = {str(key).lower() for key in data.keys()}
    assert forbidden_keys.isdisjoint(lowered_keys)

    for value in _walk_values(data):
        if isinstance(value, str):
            lowered = value.lower()
            assert "bearer " not in lowered
            assert "sk-" not in lowered
            assert "api" + "_key=" not in lowered
            assert "pass" + "word=" not in lowered


def test_traceability_records_r5_documentation_prep_boundary() -> None:
    text = TRACEABILITY.read_text(encoding="utf-8")
    assert "HISYS-FR-DARS-CP-013" in text
    assert "docs/runbooks/dars-unattended-advisory-operation.md" in text
    assert "docs/examples/dars/unattended-standing-approval.example.json" in text
    assert "DOCS-PREP" in text
    assert "HUMAN-GATED ACTION PLANNED" in text
