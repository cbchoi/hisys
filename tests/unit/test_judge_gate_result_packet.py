"""Judge advisory gate-result packet projection tests.

These tests pin the Judge-only JSON-serializable projection of a rendered
advisory gate result. ``build_judge_gate_result_packet`` consumes a
:class:`JudgeGateResult` (the value returned by ``render_judge_gate_result``)
and returns a plain, deterministic, JSON-serializable mapping so the advisory
gate outcome can be consumed by local tooling.

The projection is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- every projected packet
stays advisory-only and always requires human review, matching the Judge
authority boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.
"""

from __future__ import annotations

import json


def _valid_payload() -> dict:
    return {
        "packet_id": "JDP-0042",
        "decision_subject_ref": "claim://altas/retrieval-packet/0042",
        "verdict": "pass",
        "rationale": "Evidence corroborated; opposition raised no blocking risk.",
        "evidence_refs": ["evidence://store/handle/aaa", "altas://retrieval/bbb"],
        "opposition_refs": ["dars://opposition/packet/ccc"],
    }


def _rendered_result(payload: dict | None = None):
    from hisys.judge import render_judge_gate_result

    return render_judge_gate_result(payload or _valid_payload())


def test_export_is_available_from_judge_package() -> None:
    from hisys.judge import build_judge_gate_result_packet

    assert callable(build_judge_gate_result_packet)


def test_projects_rendered_result_to_a_plain_mapping() -> None:
    from hisys.judge import build_judge_gate_result_packet

    packet = build_judge_gate_result_packet(_rendered_result())

    assert isinstance(packet, dict)
    assert packet["subsystem"] == "judge"
    assert packet["kind"] == "advisory_gate_result"
    assert packet["rendered"] is True
    assert packet["gate_status"] == "advisory_pass"
    assert packet["verdict"] == "pass"
    assert packet["packet_id"] == "JDP-0042"


def test_packet_is_json_serializable_and_round_trips() -> None:
    from hisys.judge import build_judge_gate_result_packet

    packet = build_judge_gate_result_packet(_rendered_result())
    restored = json.loads(json.dumps(packet))

    assert restored == packet


def test_packet_carries_headline_and_body_text() -> None:
    from hisys.judge import build_judge_gate_result_packet

    result = _rendered_result()
    packet = build_judge_gate_result_packet(result)

    assert packet["headline"] == result.headline
    assert packet["body"] == result.body


def test_packet_pins_top_level_authority_locks() -> None:
    from hisys.judge import build_judge_gate_result_packet

    locks = build_judge_gate_result_packet(_rendered_result())["authority_locks"]

    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True


def test_packet_includes_non_authorization_note() -> None:
    from hisys.judge import (
        JUDGE_GATE_NON_AUTHORIZATION_NOTE,
        build_judge_gate_result_packet,
    )

    packet = build_judge_gate_result_packet(_rendered_result())

    assert packet["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_decision_packet_projection_is_jsonable_lists() -> None:
    from hisys.judge import build_judge_gate_result_packet

    decision = build_judge_gate_result_packet(_rendered_result())["decision_packet"]

    assert decision is not None
    assert decision["packet_id"] == "JDP-0042"
    assert decision["decision_subject_ref"] == "claim://altas/retrieval-packet/0042"
    assert decision["verdict"] == "pass"
    assert decision["evidence_refs"] == [
        "evidence://store/handle/aaa",
        "altas://retrieval/bbb",
    ]
    assert decision["opposition_refs"] == ["dars://opposition/packet/ccc"]
    assert isinstance(decision["evidence_refs"], list)
    assert isinstance(decision["opposition_refs"], list)


def test_decision_packet_projection_pins_safe_authority_locks() -> None:
    from hisys.judge import build_judge_gate_result_packet

    locks = build_judge_gate_result_packet(_rendered_result())["decision_packet"][
        "authority_locks"
    ]

    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True
    assert locks["live_external_action_authorized"] is False
    assert locks["mutation_authorized"] is False
    assert locks["publication_authorized"] is False
    assert locks["human_review_removal_authorized"] is False


def test_no_authority_lock_in_projection_is_escalated() -> None:
    from hisys.judge import build_judge_gate_result_packet

    packet = build_judge_gate_result_packet(_rendered_result())

    assert packet["authority_locks"]["advisory_only"] is True
    assert packet["authority_locks"]["requires_human_review"] is True
    for key, value in packet["decision_packet"]["authority_locks"].items():
        if key in ("advisory_only", "requires_human_review"):
            assert value is True
        else:
            assert value is False


def test_all_bounded_verdicts_project_distinct_gate_status() -> None:
    from hisys.judge import build_judge_gate_result_packet

    statuses = set()
    for verdict in ("pass", "fail", "block", "needs_human_review"):
        payload = _valid_payload()
        payload["verdict"] = verdict
        packet = build_judge_gate_result_packet(_rendered_result(payload))
        assert packet["rendered"] is True
        assert packet["verdict"] == verdict
        assert packet["gate_status"] == f"advisory_{verdict}"
        statuses.add(packet["gate_status"])
    assert len(statuses) == 4


def test_rejected_result_projects_failures_and_no_decision_packet() -> None:
    from hisys.judge import build_judge_gate_result_packet

    payload = _valid_payload()
    del payload["rationale"]
    packet = build_judge_gate_result_packet(_rendered_result(payload))

    assert packet["rendered"] is False
    assert packet["gate_status"] == "rejected"
    assert packet["verdict"] is None
    assert packet["packet_id"] is None
    assert packet["decision_packet"] is None
    assert "judge_decision_packet_missing_field:rationale" in packet["failures"]


def test_rejected_projection_is_json_serializable_and_advisory() -> None:
    from hisys.judge import build_judge_gate_result_packet

    payload = _valid_payload()
    del payload["packet_id"]
    packet = build_judge_gate_result_packet(_rendered_result(payload))

    json.dumps(packet)
    assert packet["authority_locks"]["advisory_only"] is True
    assert packet["authority_locks"]["requires_human_review"] is True
    assert packet["non_authorization_note"]


def test_rejected_projection_carries_unsupported_source_failure() -> None:
    from hisys.judge import build_judge_gate_result_packet, render_judge_gate_result

    packet = build_judge_gate_result_packet(
        render_judge_gate_result(["not", "a", "packet"])
    )

    assert packet["rendered"] is False
    assert "judge_gate_result_unsupported_source" in packet["failures"]


def test_warnings_are_projected_as_a_list() -> None:
    from hisys.judge import SCHEMA_VALIDITY_WARNING, build_judge_gate_result_packet

    packet = build_judge_gate_result_packet(_rendered_result())

    assert isinstance(packet["warnings"], list)
    assert SCHEMA_VALIDITY_WARNING in packet["warnings"]


def test_failures_and_warnings_are_lists_not_tuples() -> None:
    from hisys.judge import build_judge_gate_result_packet

    packet = build_judge_gate_result_packet(_rendered_result())

    assert isinstance(packet["failures"], list)
    assert isinstance(packet["warnings"], list)


def test_projection_is_deterministic() -> None:
    from hisys.judge import build_judge_gate_result_packet

    result = _rendered_result()
    first = build_judge_gate_result_packet(result)
    second = build_judge_gate_result_packet(result)

    assert first == second


def test_projection_returns_independent_mappings() -> None:
    from hisys.judge import build_judge_gate_result_packet

    result = _rendered_result()
    first = build_judge_gate_result_packet(result)
    second = build_judge_gate_result_packet(result)

    first["evidence_marker"] = "mutated"
    assert "evidence_marker" not in second


def test_projection_does_not_mutate_the_gate_result() -> None:
    from hisys.judge import build_judge_gate_result_packet

    result = _rendered_result()
    before_failures = result.failures
    before_warnings = result.warnings
    before_evidence = result.packet.evidence_refs

    build_judge_gate_result_packet(result)

    assert result.failures == before_failures
    assert result.warnings == before_warnings
    assert result.packet.evidence_refs == before_evidence


def test_top_level_keys_are_the_expected_stable_set() -> None:
    from hisys.judge import build_judge_gate_result_packet

    packet = build_judge_gate_result_packet(_rendered_result())

    assert set(packet) == {
        "subsystem",
        "kind",
        "rendered",
        "gate_status",
        "verdict",
        "packet_id",
        "headline",
        "body",
        "failures",
        "warnings",
        "authority_locks",
        "decision_packet",
        "non_authorization_note",
    }
