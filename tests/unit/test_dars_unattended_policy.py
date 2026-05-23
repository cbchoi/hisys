"""DARS R5 standing approval policy validator tests.

Traceability: HISYS-FR-DARS-CP-013, HISYS-T-DARS-CP-015,
DARS-LIVE-RELEASE-R5-UNATTENDED-PREP,
docs/runbooks/dars-unattended-advisory-operation.md.

These tests verify the standing approval policy contract only. They perform no
live provider/model call, no credential lookup, and no network access.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from hisys.agents.dars_unattended_policy import (
    STANDING_APPROVAL_POLICY_SCHEMA_ID,
    validate_standing_approval_policy,
)


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_POLICY = ROOT / "docs" / "examples" / "dars" / "unattended-standing-approval.example.json"
NOW = "2026-05-23T12:00:00Z"


def _example_policy() -> dict[str, object]:
    return json.loads(EXAMPLE_POLICY.read_text(encoding="utf-8"))


def _error_codes(data: dict[str, object], *, now: str = NOW) -> set[str]:
    report = validate_standing_approval_policy(
        data,
        config_ref="test://standing-approval",
        now=now,
    )
    return {issue.code for issue in report.issues if issue.severity == "error"}


def test_standing_approval_example_policy_passes_validator() -> None:
    report = validate_standing_approval_policy(
        _example_policy(),
        config_ref=str(EXAMPLE_POLICY),
        now=NOW,
    )

    assert report.schema_id == STANDING_APPROVAL_POLICY_SCHEMA_ID
    assert report.valid is True
    assert not {issue.code for issue in report.issues if issue.severity == "error"}
    assert {
        issue.code for issue in report.issues if issue.severity == "warning"
    } == {"standing_approval_does_not_authorize_live_action_by_itself"}


@pytest.mark.parametrize(
    ("now", "expected_code"),
    [
        ("2026-05-22T23:59:59Z", "standing_approval_not_active"),
        ("2026-06-23T00:00:01Z", "standing_approval_not_active"),
    ],
)
def test_standing_approval_policy_rejects_inactive_validity_window(
    now: str, expected_code: str
) -> None:
    assert expected_code in _error_codes(_example_policy(), now=now)


def test_standing_approval_policy_rejects_missing_request_class_allowlist() -> None:
    data = _example_policy()
    data.pop("request_class_allowlist")

    assert "request_class_allowlist_missing" in _error_codes(data)


def test_standing_approval_policy_rejects_live_canary_in_prep_example() -> None:
    data = _example_policy()
    data["request_class_allowlist"] = ["dars_live_provider_advisory_canary"]

    assert "request_class_not_allowed_for_prep" in _error_codes(data)


def test_standing_approval_policy_rejects_missing_budget_rate_and_kill_switch() -> None:
    data = _example_policy()
    for field in (
        "cost_budget_ref",
        "max_runs",
        "max_runs_per_hour",
        "rate_limit_per_minute",
        "max_prompt_bytes_per_run",
        "max_output_bytes_per_run",
        "kill_switch_ref",
    ):
        data.pop(field)

    codes = _error_codes(data)
    assert "budget_or_rate_caps_missing" in codes
    assert "kill_switch_ref_missing" in codes


def test_standing_approval_policy_rejects_missing_audit_retention() -> None:
    data = _example_policy()
    data.pop("audit_retention_ref")

    assert "audit_retention_ref_missing" in _error_codes(data)


def test_standing_approval_policy_rejects_authority_flags() -> None:
    data = _example_policy()
    data["requires_post_run_human_review"] = False
    data["mutation_allowed"] = True
    data["publication_allowed"] = True
    data["external_action_allowed"] = True

    codes = _error_codes(data)
    assert "post_run_human_review_required" in codes
    assert "unattended_authority_rejected" in codes


def test_standing_approval_policy_rejects_raw_secret_fields() -> None:
    data = _example_policy()
    data["api_key"] = "sk-fake_unattended_policy_secret_value"

    assert "raw_secret_field_rejected" in _error_codes(data)


def test_standing_approval_policy_rejects_secret_looking_nested_values() -> None:
    data = _example_policy()
    data["circuit_breakers"] = copy.deepcopy(data["circuit_breakers"])
    assert isinstance(data["circuit_breakers"], dict)
    data["circuit_breakers"]["diagnostic"] = "hf_" + "unattended_policy_secret_value"

    assert "raw_secret_value_rejected" in _error_codes(data)
