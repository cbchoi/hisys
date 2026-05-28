"""Judge advisory gate-result renderer tests.

These tests pin the Judge-only gate-result renderer. The renderer consumes
either a validated :class:`JudgeAdvisoryDecisionPacket` or an already-prepared
local packet mapping (the same shape the decision-packet validator accepts) and
emits a deterministic, human-readable advisory gate result.

The renderer is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It also grants no execution authority -- every rendered
result stays advisory-only and always requires human review, matching the Judge
authority boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest


def _valid_payload() -> dict:
    return {
        "packet_id": "JDP-0007",
        "decision_subject_ref": "claim://altas/retrieval-packet/0007",
        "verdict": "pass",
        "rationale": "Evidence corroborated; opposition raised no blocking risk.",
        "evidence_refs": ["evidence://store/handle/aaa", "altas://retrieval/bbb"],
        "opposition_refs": ["dars://opposition/packet/ccc"],
    }


def _valid_packet():
    from hisys.judge import validate_judge_decision_packet

    packet = validate_judge_decision_packet(_valid_payload()).packet
    assert packet is not None
    return packet


def test_module_exports_are_available_from_judge_package() -> None:
    from hisys.judge import (
        JUDGE_GATE_REJECTED_STATUS,
        JUDGE_GATE_STATUS_BY_VERDICT,
        JudgeGateResult,
        render_judge_gate_result,
    )

    assert callable(render_judge_gate_result)
    assert isinstance(JUDGE_GATE_STATUS_BY_VERDICT, dict)
    assert isinstance(JUDGE_GATE_REJECTED_STATUS, str)
    assert JudgeGateResult is not None


def test_gate_status_map_covers_exactly_the_bounded_verdicts() -> None:
    from hisys.judge import JUDGE_GATE_STATUS_BY_VERDICT, JUDGE_VERDICTS

    assert set(JUDGE_GATE_STATUS_BY_VERDICT) == set(JUDGE_VERDICTS)
    for verdict, gate_status in JUDGE_GATE_STATUS_BY_VERDICT.items():
        assert gate_status == f"advisory_{verdict}"


def test_renders_validated_packet_instance() -> None:
    from hisys.judge import render_judge_gate_result

    result = render_judge_gate_result(_valid_packet())

    assert result.rendered is True
    assert result.gate_status == "advisory_pass"
    assert result.verdict == "pass"
    assert result.packet_id == "JDP-0007"
    assert result.failures == ()


def test_renders_prepared_mapping_by_validating_it_first() -> None:
    from hisys.judge import render_judge_gate_result

    result = render_judge_gate_result(_valid_payload())

    assert result.rendered is True
    assert result.gate_status == "advisory_pass"
    assert result.packet is not None
    assert result.packet.packet_id == "JDP-0007"


def test_rendered_result_pins_advisory_and_human_review_locks() -> None:
    from hisys.judge import render_judge_gate_result

    result = render_judge_gate_result(_valid_payload())

    assert result.advisory_only is True
    assert result.requires_human_review is True


def test_rendered_result_carries_non_authorization_warning() -> None:
    from hisys.judge import SCHEMA_VALIDITY_WARNING, render_judge_gate_result

    result = render_judge_gate_result(_valid_payload())
    assert SCHEMA_VALIDITY_WARNING in result.warnings


def test_headline_is_human_readable_and_marks_human_review() -> None:
    from hisys.judge import render_judge_gate_result

    result = render_judge_gate_result(_valid_payload())

    assert "ADVISORY_PASS" in result.headline
    assert "human review" in result.headline.lower()


def test_body_includes_subject_verdict_rationale_and_refs() -> None:
    from hisys.judge import render_judge_gate_result

    result = render_judge_gate_result(_valid_payload())
    body = result.body

    assert "JDP-0007" in body
    assert "claim://altas/retrieval-packet/0007" in body
    assert "advisory_pass" in body
    assert "Evidence corroborated; opposition raised no blocking risk." in body
    assert "evidence://store/handle/aaa" in body
    assert "altas://retrieval/bbb" in body
    assert "dars://opposition/packet/ccc" in body


def test_body_states_no_execution_authority_is_granted() -> None:
    from hisys.judge import render_judge_gate_result

    body = render_judge_gate_result(_valid_payload()).body.lower()

    assert "advisory only" in body
    assert "does not authorize" in body
    assert "human" in body


def test_body_renders_none_for_empty_opposition_refs() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    payload["opposition_refs"] = []
    result = render_judge_gate_result(payload)

    assert result.rendered is True
    assert "Opposition refs:" in result.body
    assert "(none)" in result.body


def test_all_bounded_verdicts_render_distinct_gate_statuses() -> None:
    from hisys.judge import render_judge_gate_result

    statuses = set()
    for verdict in ("pass", "fail", "block", "needs_human_review"):
        payload = _valid_payload()
        payload["verdict"] = verdict
        result = render_judge_gate_result(payload)
        assert result.rendered is True
        assert result.verdict == verdict
        assert result.gate_status == f"advisory_{verdict}"
        statuses.add(result.gate_status)
    assert len(statuses) == 4


def test_even_pass_verdict_requires_human_review() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    payload["verdict"] = "pass"
    result = render_judge_gate_result(payload)

    assert result.gate_status == "advisory_pass"
    assert result.requires_human_review is True
    assert "human review" in result.body.lower()


def test_invalid_mapping_is_rejected_not_rendered() -> None:
    from hisys.judge import JUDGE_GATE_REJECTED_STATUS, render_judge_gate_result

    payload = _valid_payload()
    del payload["rationale"]
    payload["verdict"] = "approve_and_execute"
    result = render_judge_gate_result(payload)

    assert result.rendered is False
    assert result.packet is None
    assert result.gate_status == JUDGE_GATE_REJECTED_STATUS
    assert "judge_decision_packet_missing_field:rationale" in result.failures
    assert "judge_decision_packet_invalid_verdict" in result.failures


def test_rejected_result_still_requires_human_review_and_is_advisory() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    del payload["packet_id"]
    result = render_judge_gate_result(payload)

    assert result.rendered is False
    assert result.advisory_only is True
    assert result.requires_human_review is True


def test_rejected_body_lists_validation_failures() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    payload["evidence_refs"] = []
    result = render_judge_gate_result(payload)

    assert result.rendered is False
    assert "rejected" in result.body.lower()
    assert "judge_decision_packet_evidence_refs_empty" in result.body


def test_rejected_result_grants_no_authority_in_body() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    del payload["verdict"]
    body = render_judge_gate_result(payload).body.lower()

    assert "advisory only" in body
    assert "does not authorize" in body


def test_authority_escalation_in_mapping_is_rejected() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    payload["live_external_action_authorized"] = True
    result = render_judge_gate_result(payload)

    assert result.rendered is False
    assert (
        "judge_decision_packet_live_external_action_not_authorized"
        in result.failures
    )


def test_unsupported_source_is_rejected() -> None:
    from hisys.judge import render_judge_gate_result

    result = render_judge_gate_result(["not", "a", "packet"])

    assert result.rendered is False
    assert result.packet is None
    assert "judge_gate_result_unsupported_source" in result.failures


def test_result_is_frozen() -> None:
    from hisys.judge import render_judge_gate_result

    result = render_judge_gate_result(_valid_payload())

    with pytest.raises(FrozenInstanceError):
        result.gate_status = "advisory_block"  # type: ignore[misc]


def test_rendering_is_deterministic() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    first = render_judge_gate_result(payload)
    second = render_judge_gate_result(payload)

    assert first == second
    assert first.body == second.body


def test_renderer_does_not_mutate_input_mapping() -> None:
    from hisys.judge import render_judge_gate_result

    payload = _valid_payload()
    snapshot = {
        "evidence_refs": list(payload["evidence_refs"]),
        "opposition_refs": list(payload["opposition_refs"]),
    }
    render_judge_gate_result(payload)

    assert payload["evidence_refs"] == snapshot["evidence_refs"]
    assert payload["opposition_refs"] == snapshot["opposition_refs"]
    assert "advisory_only" not in payload
