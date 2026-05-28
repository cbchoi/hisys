"""Judge bounded advisory decision packet schema tests.

These tests pin the Judge-only decision packet schema and its deterministic,
side-effect-free validator. The validator consumes an already-prepared local
packet mapping (for example, an operator-prepared JSON object loaded elsewhere)
and never performs live provider calls, network access, credential lookup,
mutation, publication, remote push, or cross-subsystem calls.

The schema stays inside the Judge authority boundary recorded in
``src/hisys/judge/ralph.md`` and ``docs/design/hisys-subsystem-architecture.md``:
Judge issues bounded advisory judgments and decision packets that remain
advisory-only and always require human review.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict

import pytest


def _valid_payload() -> dict:
    return {
        "packet_id": "JDP-0001",
        "decision_subject_ref": "claim://altas/retrieval-packet/0001",
        "verdict": "needs_human_review",
        "rationale": "Evidence is partially corroborated; opposition raised an open risk.",
        "evidence_refs": ["evidence://store/handle/aaa", "altas://retrieval/bbb"],
        "opposition_refs": ["dars://opposition/packet/ccc"],
    }


def test_module_exports_are_available_from_judge_package() -> None:
    from hisys.judge import (
        JUDGE_VERDICTS,
        JudgeAdvisoryDecisionPacket,
        JudgeDecisionPacketValidation,
        validate_judge_decision_packet,
    )

    assert callable(validate_judge_decision_packet)
    assert isinstance(JUDGE_VERDICTS, tuple)
    assert JudgeAdvisoryDecisionPacket is not None
    assert JudgeDecisionPacketValidation is not None


def test_bounded_verdicts_are_exactly_the_advisory_set() -> None:
    from hisys.judge import JUDGE_VERDICTS

    assert JUDGE_VERDICTS == ("pass", "fail", "block", "needs_human_review")


def test_validate_accepts_minimal_valid_packet() -> None:
    from hisys.judge import validate_judge_decision_packet

    result = validate_judge_decision_packet(_valid_payload())

    assert result.valid is True
    assert result.failures == ()
    assert result.packet is not None
    assert result.packet.packet_id == "JDP-0001"
    assert result.packet.verdict == "needs_human_review"


def test_valid_packet_pins_authority_locks_to_safe_defaults() -> None:
    from hisys.judge import validate_judge_decision_packet

    packet = validate_judge_decision_packet(_valid_payload()).packet
    assert packet is not None
    assert packet.advisory_only is True
    assert packet.requires_human_review is True
    assert packet.live_external_action_authorized is False
    assert packet.mutation_authorized is False
    assert packet.publication_authorized is False
    assert packet.human_review_removal_authorized is False


def test_valid_packet_normalizes_refs_to_tuples() -> None:
    from hisys.judge import validate_judge_decision_packet

    packet = validate_judge_decision_packet(_valid_payload()).packet
    assert packet is not None
    assert packet.evidence_refs == (
        "evidence://store/handle/aaa",
        "altas://retrieval/bbb",
    )
    assert packet.opposition_refs == ("dars://opposition/packet/ccc",)


def test_valid_packet_emits_non_authorization_warning() -> None:
    from hisys.judge import (
        SCHEMA_VALIDITY_WARNING,
        validate_judge_decision_packet,
    )

    result = validate_judge_decision_packet(_valid_payload())
    assert SCHEMA_VALIDITY_WARNING in result.warnings


def test_packet_is_frozen_and_serializable() -> None:
    from hisys.judge import validate_judge_decision_packet

    packet = validate_judge_decision_packet(_valid_payload()).packet
    assert packet is not None

    with pytest.raises(FrozenInstanceError):
        packet.verdict = "pass"  # type: ignore[misc]

    dumped = asdict(packet)
    assert dumped["advisory_only"] is True
    assert dumped["requires_human_review"] is True


def test_all_bounded_verdicts_validate() -> None:
    from hisys.judge import validate_judge_decision_packet

    for verdict in ("pass", "fail", "block", "needs_human_review"):
        payload = _valid_payload()
        payload["verdict"] = verdict
        result = validate_judge_decision_packet(payload)
        assert result.valid is True, (verdict, result.failures)
        assert result.packet is not None
        assert result.packet.verdict == verdict


def test_rejects_non_mapping_payload() -> None:
    from hisys.judge import validate_judge_decision_packet

    result = validate_judge_decision_packet(["not", "a", "mapping"])

    assert result.valid is False
    assert result.packet is None
    assert result.failures == ("judge_decision_packet_not_a_mapping",)


def test_rejects_missing_required_field() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    del payload["packet_id"]
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert result.packet is None
    assert "judge_decision_packet_missing_field:packet_id" in result.failures


def test_rejects_empty_required_string() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["rationale"] = "   "
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_empty_field:rationale" in result.failures


def test_rejects_non_string_required_field() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["packet_id"] = 123
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_field_not_a_string:packet_id" in result.failures


def test_rejects_invalid_verdict() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["verdict"] = "approve_and_execute"
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_invalid_verdict" in result.failures


def test_rejects_non_list_evidence_refs() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["evidence_refs"] = "evidence://store/handle/aaa"
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_evidence_refs_not_a_list" in result.failures


def test_rejects_empty_evidence_refs() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["evidence_refs"] = []
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_evidence_refs_empty" in result.failures


def test_rejects_non_string_evidence_ref() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["evidence_refs"] = ["ok", 7]
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_evidence_ref_not_a_string" in result.failures


def test_rejects_non_list_opposition_refs() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["opposition_refs"] = "dars://opposition/packet/ccc"
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_opposition_refs_not_a_list" in result.failures


def test_allows_empty_opposition_refs() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["opposition_refs"] = []
    result = validate_judge_decision_packet(payload)

    assert result.valid is True
    assert result.packet is not None
    assert result.packet.opposition_refs == ()


def test_opposition_refs_default_to_empty_when_omitted() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    del payload["opposition_refs"]
    result = validate_judge_decision_packet(payload)

    assert result.valid is True
    assert result.packet is not None
    assert result.packet.opposition_refs == ()


def test_rejects_advisory_only_false() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["advisory_only"] = False
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_advisory_only_must_be_true" in result.failures


def test_rejects_requires_human_review_false() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["requires_human_review"] = False
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_requires_human_review_must_be_true" in result.failures


def test_rejects_live_external_action_authorization_escalation() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["live_external_action_authorized"] = True
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_live_external_action_not_authorized" in result.failures


def test_rejects_mutation_authorization_escalation() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["mutation_authorized"] = True
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_mutation_not_authorized" in result.failures


def test_rejects_publication_authorization_escalation() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["publication_authorized"] = True
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_publication_not_authorized" in result.failures


def test_rejects_human_review_removal_escalation() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    payload["human_review_removal_authorized"] = True
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert "judge_decision_packet_human_review_removal_not_authorized" in result.failures


def test_failures_accumulate_for_multiple_problems() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    del payload["rationale"]
    payload["verdict"] = "bogus"
    payload["evidence_refs"] = []
    result = validate_judge_decision_packet(payload)

    assert result.valid is False
    assert result.packet is None
    assert "judge_decision_packet_missing_field:rationale" in result.failures
    assert "judge_decision_packet_invalid_verdict" in result.failures
    assert "judge_decision_packet_evidence_refs_empty" in result.failures


def test_validation_is_deterministic() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    del payload["rationale"]
    payload["verdict"] = "bogus"

    first = validate_judge_decision_packet(payload)
    second = validate_judge_decision_packet(payload)

    assert first == second
    assert first.failures == second.failures


def test_validator_does_not_mutate_input_payload() -> None:
    from hisys.judge import validate_judge_decision_packet

    payload = _valid_payload()
    snapshot = {
        "evidence_refs": list(payload["evidence_refs"]),
        "opposition_refs": list(payload["opposition_refs"]),
    }
    validate_judge_decision_packet(payload)

    assert payload["evidence_refs"] == snapshot["evidence_refs"]
    assert payload["opposition_refs"] == snapshot["opposition_refs"]
