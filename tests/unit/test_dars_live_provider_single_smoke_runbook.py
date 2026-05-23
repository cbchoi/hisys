"""DARS R3 single-critic live-provider smoke runbook PREP tests.

Traceability: HISYS-FR-DARS-CP-011, HISYS-T-DARS-CP-013,
DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP,
docs/plans/dars-panel-live-provider-unattended-release-final-plan.md.

These tests verify the controlled R3 PREP artifacts only. They run no live
provider call, read no credentials, and rely on no network access. The
actual single live call is a separately approved HUMAN-GATED action that
PREP does not authorize.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.agents.dars_backend_activation import (
    validate_dars_backend_activation_packet,
)
from hisys.agents.dars_live_provider_policy import (
    validate_live_provider_policy_packet,
)


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "runbooks" / "dars-live-provider-single-smoke.md"
EXAMPLE_POLICY = (
    ROOT / "docs" / "examples" / "dars" / "live-provider-single-smoke.policy.example.json"
)
EXAMPLE_ACTIVATION = (
    ROOT
    / "docs"
    / "examples"
    / "dars"
    / "live-provider-single-smoke.activation.example.json"
)


def test_live_provider_single_smoke_runbook_exists() -> None:
    assert RUNBOOK.exists(), f"missing runbook: {RUNBOOK}"


def test_live_provider_single_smoke_runbook_requires_decision_packet_and_budget() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    required_phrases = [
        "decision packet",
        "approval_ref",
        "credential reference",
        "credential_ref",
        "redaction policy",
        "max_prompt_bytes",
        "max_output_bytes",
        "rate_limit_per_minute",
        "cost_budget_ref",
        "advisory_only",
        "requires_human_review=true",
        "HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED",
        "external_call_made=true",
        "mutation_performed=false",
        "publication_performed=false",
        "post-run human review",
    ]
    for phrase in required_phrases:
        assert phrase in text, phrase


def test_live_provider_single_smoke_runbook_documents_stop_conditions() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    required_phrases = [
        "Stop conditions",
        "missing decision packet",
        "raw secret",
        "credential lookup by Hisys",
        "mutation",
        "publication",
        "tool",
        "browser",
        "search",
        "budget violation",
        "rate-limit violation",
        "secret scan hit",
        "output redaction failure",
        "operator uncertainty",
    ]
    for phrase in required_phrases:
        assert phrase in text, phrase


def test_live_provider_single_smoke_runbook_anchors_r1_r2_artifacts() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    required_anchors = [
        "DARS-LIVE-RELEASE-R1-POLICY",
        "DARS-LIVE-RELEASE-R2-ADAPTER",
        "src/hisys/agents/dars_live_provider_policy.py",
        "src/hisys/agents/dars_live_provider_transport.py",
        "src/hisys/agents/dars_live_provider_adapter.py",
        "docs/examples/dars/live-provider-single-smoke.policy.example.json",
        "docs/examples/dars/live-provider-single-smoke.activation.example.json",
    ]
    for anchor in required_anchors:
        assert anchor in text, anchor


def test_live_provider_single_smoke_runbook_does_not_authorize_live_call_by_itself() -> None:
    """The PREP runbook must explicitly remain advisory; it must not authorize the live call."""

    text = RUNBOOK.read_text(encoding="utf-8")
    assert "does not by itself authorize" in text
    assert "human-approved decision packet" in text
    assert "single" in text and "one" in text  # exactly one call per approved smoke


def test_live_provider_single_smoke_example_policy_passes_r1_validator() -> None:
    data = json.loads(EXAMPLE_POLICY.read_text(encoding="utf-8"))
    report = validate_live_provider_policy_packet(
        data,
        config_ref=str(EXAMPLE_POLICY),
        now="2026-05-23T00:00:00Z",
    )

    error_codes = {issue.code for issue in report.issues if issue.severity == "error"}
    assert report.valid is True, f"example policy must pass R1 validator; errors={error_codes}"
    warning_codes = {
        issue.code for issue in report.issues if issue.severity == "warning"
    }
    assert "live_provider_dispatch_not_authorized_by_policy_alone" in warning_codes


def test_live_provider_single_smoke_example_policy_uses_only_credential_reference() -> None:
    data = json.loads(EXAMPLE_POLICY.read_text(encoding="utf-8"))
    ref = data["credential_ref"]
    allowed_schemes = (
        "env://",
        "secret-manager-ref://",
        "vault://",
        "subscription-account-ref://",
        "keychain-ref://",
    )
    assert isinstance(ref, str)
    assert ref.startswith(allowed_schemes), ref
    forbidden = {"api_key", "token", "password", "authorization", "secret"}
    for forbidden_key in forbidden:
        assert forbidden_key not in data, forbidden_key


def test_live_provider_single_smoke_example_activation_passes_validator() -> None:
    data = json.loads(EXAMPLE_ACTIVATION.read_text(encoding="utf-8"))
    report = validate_dars_backend_activation_packet(
        data,
        config_ref=str(EXAMPLE_ACTIVATION),
        now="2026-05-23T00:00:00Z",
    )
    error_codes = {issue.code for issue in report.issues if issue.severity == "error"}
    assert report.valid is True, (
        f"example activation must pass validator; errors={error_codes}"
    )


def test_live_provider_single_smoke_example_activation_matches_example_policy() -> None:
    policy_data = json.loads(EXAMPLE_POLICY.read_text(encoding="utf-8"))
    activation_data = json.loads(EXAMPLE_ACTIVATION.read_text(encoding="utf-8"))

    assert activation_data["approval_ref"] == policy_data["approval_ref"]
    assert activation_data["allowed_actions"] == policy_data["allowed_actions"]
    assert activation_data["endpoint_scope"] == "external_api"
    assert activation_data["human_approved"] is True
    assert activation_data["remote_policy_packet_ref"].endswith(
        "live-provider-single-smoke.policy.example.json"
    )
