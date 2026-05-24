"""DARS R5 unattended advisory runner tests.

Traceability: HISYS-FR-DARS-CP-013, HISYS-T-DARS-CP-015,
DARS-LIVE-RELEASE-R5-UNATTENDED-PREP,
docs/runbooks/dars-unattended-advisory-operation.md.

These tests use only fake/injected transports and temporary instance roots. They
perform no live provider/model call, no credential lookup, and no network access.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.agents.dars_live_provider_transport import FakeLiveProviderTransport
from hisys.config.instance import InstanceRoot
from hisys.operations.dars_unattended_runner import (
    DarsUnattendedAdvisoryRequest,
    DarsUnattendedAdvisoryRunner,
)


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_STANDING_POLICY = ROOT / "docs" / "examples" / "dars" / "unattended-standing-approval.example.json"
EXAMPLE_CANARY_STANDING_POLICY = (
    ROOT / "docs" / "examples" / "dars" / "unattended-standing-approval-canary.example.json"
)
PROVIDER_POLICY = ROOT / "docs" / "examples" / "dars" / "live-provider-panel-smoke.policy.example.json"
ACTIVATION_PACKET = ROOT / "docs" / "examples" / "dars" / "live-provider-panel-smoke.activation.example.json"
CANARY_ACTION_DECISION_PACKET_REF = (
    "docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md"
)
NOW = "2026-05-23T12:00:00Z"
CANARY_NOW = "2026-05-24T12:00:00Z"


def _policy_file(tmp_path: Path, **updates: object) -> Path:
    data = json.loads(EXAMPLE_STANDING_POLICY.read_text(encoding="utf-8"))
    data.update(updates)
    path = tmp_path / "standing-approval.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _request(policy_ref: Path, **updates: object) -> DarsUnattendedAdvisoryRequest:
    fields = {
        "request_id": "DARS_UNATTENDED_REQ_001",
        "source_execution_id": "DARS_UNATTENDED_SRC_001",
        "request_class": "dars_live_provider_advisory_dry_run",
        "standing_approval_policy_ref": str(policy_ref),
        "policy_packet_ref": str(PROVIDER_POLICY),
        "activation_packet_ref": str(ACTIVATION_PACKET),
        "approval_ref": "APPROVAL-DARS-LP-PANEL-SMOKE-20260523-001",
        "backend_id": "dars-live-claude-panel-smoke-001",
        "prompt_packet_ref": "redacted://dars/unattended/prep/request-001",
        "prompt_byte_count": 512,
        "yyyymmdd": "20260523",
        "now": NOW,
    }
    fields.update(updates)
    return DarsUnattendedAdvisoryRequest(**fields)  # type: ignore[arg-type]


def _transport() -> FakeLiveProviderTransport:
    def executor(payload: dict[str, object]) -> dict[str, object]:
        return {
            "critique_text": f"advisory dry-run critique for {payload['request_id']}",
            "output_byte_count": 64,
            "input_tokens": 10,
            "output_tokens": 12,
            "latency_ms": 5,
        }

    return FakeLiveProviderTransport(executor=executor)


def _runner(tmp_path: Path) -> DarsUnattendedAdvisoryRunner:
    return DarsUnattendedAdvisoryRunner(
        instance=InstanceRoot(tmp_path / "instance"),
        transport=_transport(),
        kill_switch_state={"ops://hisys/dars/unattended/kill-switch/manual": "armed"},
    )


def _ledger_payload(instance_root: Path, boundary_ref: str) -> dict[str, object]:
    return json.loads((instance_root / boundary_ref).read_text(encoding="utf-8"))


def test_unattended_runner_blocks_expired_policy_and_writes_ledger(tmp_path: Path) -> None:
    policy_ref = _policy_file(tmp_path, expires_at="2026-05-23T00:00:00Z")
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref))

    assert result.status == "blocked"
    assert result.failure_code == "standing_approval_not_active"
    assert result.adapter_boundary_ref is None
    assert result.ledger_ref is not None
    ledger = _ledger_payload(tmp_path / "instance", result.ledger_ref)
    assert ledger["status"] == "blocked"
    assert ledger["failure_code"] == "standing_approval_not_active"
    assert ledger["external_call_made"] is False
    assert ledger["requires_post_run_human_review"] is True


def test_unattended_runner_requires_kill_switch_and_budget_caps(tmp_path: Path) -> None:
    policy_ref = _policy_file(tmp_path, kill_switch_ref="", max_runs=0)
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref))

    assert result.status == "blocked"
    assert result.failure_code == "standing_approval_policy_invalid"
    assert {"kill_switch_ref_missing", "budget_or_rate_caps_missing"}.issubset(
        result.policy_issue_codes
    )


def test_unattended_runner_rejects_mutation_publication_or_external_action_authority(
    tmp_path: Path,
) -> None:
    policy_ref = _policy_file(
        tmp_path,
        mutation_allowed=True,
        publication_allowed=True,
        external_action_allowed=True,
    )
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref, mutation_allowed=True))

    assert result.status == "blocked"
    assert result.failure_code in {
        "standing_approval_policy_invalid",
        "unattended_authority_rejected",
    }
    assert result.external_action_performed is False
    assert result.mutation_performed is False
    assert result.publication_performed is False


def test_unattended_runner_executes_dry_run_fake_transport_and_writes_audit_ledger(
    tmp_path: Path,
) -> None:
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref))

    assert result.status == "completed"
    assert result.failure_code is None
    assert result.adapter_boundary_ref is not None
    assert result.ledger_ref is not None
    ledger = _ledger_payload(tmp_path / "instance", result.ledger_ref)
    assert ledger["schema_id"] == "hisys.dars.unattended_advisory.ledger_entry"
    assert ledger["policy_id"] == "DARS-UNATTENDED-STANDING-PREP-20260523-001"
    assert ledger["request_class"] == "dars_live_provider_advisory_dry_run"
    assert ledger["mode"] == "dry_run"
    assert ledger["transport_kind"] == "fake_injected_provider_transport"
    assert ledger["external_call_made"] is False
    assert ledger["model_boundary_crossed"] is False
    assert ledger["mutation_performed"] is False
    assert ledger["publication_performed"] is False
    assert ledger["external_action_performed"] is False
    assert ledger["advisory_only"] is True
    assert ledger["requires_human_review"] is True
    assert ledger["requires_post_run_human_review"] is True
    assert ledger["adapter_boundary_ref"] == result.adapter_boundary_ref


def test_unattended_runner_trips_repeated_failure_circuit_breaker(tmp_path: Path) -> None:
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref, consecutive_failures=2))

    assert result.status == "circuit_broken"
    assert result.failure_code == "repeated_failure_threshold_reached"


def test_unattended_runner_trips_cost_threshold_circuit_breaker(tmp_path: Path) -> None:
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref, cost_threshold_reached=True))

    assert result.status == "circuit_broken"
    assert result.failure_code == "cost_threshold_reached"


def test_unattended_runner_blocks_secret_scan_hit(tmp_path: Path) -> None:
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref, secret_scan_passed=False))

    assert result.status == "circuit_broken"
    assert result.failure_code == "secret_scan_hit"


def test_unattended_runner_blocks_policy_mismatch(tmp_path: Path) -> None:
    policy_ref = _policy_file(tmp_path, provider_policy_refs=["docs/examples/dars/other-policy.json"])
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref))

    assert result.status == "blocked"
    assert result.failure_code == "provider_policy_mismatch"


def test_unattended_runner_records_output_redaction_failure(tmp_path: Path) -> None:
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref, output_redaction_passed=False))

    assert result.status == "circuit_broken"
    assert result.failure_code == "output_redaction_failure"


def test_unattended_runner_blocks_canary_request_class_until_canary_mode_exists(
    tmp_path: Path,
) -> None:
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(
        _request(policy_ref, request_class="dars_live_provider_advisory_canary")
    )

    assert result.status == "blocked"
    assert result.failure_code == "request_class_not_allowlisted"
    assert result.external_call_made is False
    assert result.model_boundary_crossed is False
    assert result.mutation_performed is False
    assert result.publication_performed is False
    assert result.external_action_performed is False
    assert result.requires_human_review is True


# DARS-LIVE-RELEASE-R5-CANARY-MODE-PREP canary-mode contract tests


def _canary_policy_file(tmp_path: Path, **updates: object) -> Path:
    data = json.loads(EXAMPLE_CANARY_STANDING_POLICY.read_text(encoding="utf-8"))
    data.update(updates)
    path = tmp_path / "standing-approval-canary.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _canary_request(policy_ref: Path, **updates: object) -> DarsUnattendedAdvisoryRequest:
    fields = {
        "request_id": "DARS_UNATTENDED_CANARY_REQ_001",
        "source_execution_id": "DARS_UNATTENDED_CANARY_SRC_001",
        "request_class": "dars_live_provider_advisory_canary",
        "standing_approval_policy_ref": str(policy_ref),
        "policy_packet_ref": str(PROVIDER_POLICY),
        "activation_packet_ref": str(ACTIVATION_PACKET),
        "approval_ref": "APPROVAL-DARS-LP-PANEL-SMOKE-20260523-001",
        "backend_id": "dars-live-claude-panel-smoke-001",
        "prompt_packet_ref": "redacted://dars/unattended/canary/request-001",
        "prompt_byte_count": 512,
        "yyyymmdd": "20260524",
        "mode": "canary",
        "canary_action_decision_packet_ref": CANARY_ACTION_DECISION_PACKET_REF,
        "now": CANARY_NOW,
    }
    fields.update(updates)
    return DarsUnattendedAdvisoryRequest(**fields)  # type: ignore[arg-type]


def test_unattended_runner_canary_mode_routes_through_fake_transport_and_records_no_live_boundary(
    tmp_path: Path,
) -> None:
    policy_ref = _canary_policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_canary_request(policy_ref))

    assert result.status == "completed"
    assert result.failure_code is None
    assert result.adapter_boundary_ref is not None
    assert result.ledger_ref is not None
    assert result.external_call_made is False
    assert result.model_boundary_crossed is False
    assert result.mutation_performed is False
    assert result.publication_performed is False
    assert result.external_action_performed is False
    assert result.advisory_only is True
    assert result.requires_human_review is True
    assert result.requires_post_run_human_review is True

    ledger = _ledger_payload(tmp_path / "instance", result.ledger_ref)
    assert ledger["mode"] == "canary"
    assert ledger["request_class"] == "dars_live_provider_advisory_canary"
    assert ledger["transport_kind"] == "fake_injected_provider_transport"
    assert ledger["external_call_made"] is False
    assert ledger["model_boundary_crossed"] is False
    assert ledger["mutation_performed"] is False
    assert ledger["publication_performed"] is False
    assert ledger["external_action_performed"] is False
    assert ledger["advisory_only"] is True
    assert ledger["requires_human_review"] is True
    assert ledger["requires_post_run_human_review"] is True
    assert ledger["adapter_mode"] == "dry_run"
    assert ledger["live_provider_model_call_made"] is False
    assert ledger["raw_provider_api_call_by_hisys"] is False
    assert ledger["credential_lookup_by_hisys"] is False
    assert ledger["canary_action_decision_packet_ref"] == CANARY_ACTION_DECISION_PACKET_REF


def test_unattended_runner_canary_mode_blocks_dry_run_request_class(tmp_path: Path) -> None:
    policy_ref = _canary_policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(
        _canary_request(policy_ref, request_class="dars_live_provider_advisory_dry_run")
    )

    assert result.status == "blocked"
    assert result.failure_code == "canary_mode_requires_canary_request_class"


def test_unattended_runner_canary_mode_blocks_inactive_canary_window(tmp_path: Path) -> None:
    policy_ref = _canary_policy_file(
        tmp_path,
        canary_window_start="2026-05-25T00:00:00Z",
        canary_window_end="2026-06-01T00:00:00Z",
    )
    runner = _runner(tmp_path)

    result = runner.run(_canary_request(policy_ref))

    assert result.status == "blocked"
    assert result.failure_code == "canary_mode_policy_invalid"
    assert "canary_window_not_active" in result.policy_issue_codes


def test_unattended_runner_canary_mode_blocks_canary_action_decision_packet_ref_mismatch(
    tmp_path: Path,
) -> None:
    policy_ref = _canary_policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(
        _canary_request(
            policy_ref,
            canary_action_decision_packet_ref="docs/release/other-canary-packet.md",
        )
    )

    assert result.status == "blocked"
    assert result.failure_code == "canary_action_decision_packet_ref_mismatch"


def test_unattended_runner_canary_mode_rejects_request_without_canary_action_decision_packet_ref(
    tmp_path: Path,
) -> None:
    policy_ref = _canary_policy_file(tmp_path)

    with pytest.raises(ValueError, match="canary_action_decision_packet_ref"):
        _canary_request(policy_ref, canary_action_decision_packet_ref=None)


def test_unattended_runner_canary_mode_blocks_canary_policy_in_prep_form(
    tmp_path: Path,
) -> None:
    # Canary request against a prep-only standing approval policy must be blocked
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_canary_request(policy_ref))

    assert result.status == "blocked"
    assert result.failure_code == "canary_mode_policy_invalid"


def test_unattended_runner_dry_run_mode_preserves_dry_run_path(tmp_path: Path) -> None:
    # Regression: the existing dry-run path continues to work.
    policy_ref = _policy_file(tmp_path)
    runner = _runner(tmp_path)

    result = runner.run(_request(policy_ref))

    ledger = _ledger_payload(tmp_path / "instance", result.ledger_ref)
    assert result.status == "completed"
    assert ledger["mode"] == "dry_run"
    assert ledger["request_class"] == "dars_live_provider_advisory_dry_run"
    assert ledger["transport_kind"] == "fake_injected_provider_transport"
    assert ledger["external_call_made"] is False
    assert ledger["adapter_mode"] == "dry_run"
