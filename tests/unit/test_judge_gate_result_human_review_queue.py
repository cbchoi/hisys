"""Judge advisory gate-result human-review work-queue tests.

These tests pin the Judge-only, read-only projection of one or more advisory
gate-result packets into a bounded human-review work queue.
``build_judge_human_review_work_queue`` consumes the JSON-serializable packets
produced by ``build_judge_gate_result_packet`` and returns a plain,
deterministic mapping that groups packet ids by gate status and surfaces the
packets that most need human review first (most-restrictive gate status first).

The projection is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the queue stays
advisory-only and always requires human review, matching the Judge authority
boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.
"""

from __future__ import annotations

import json


def _payload(verdict: str = "pass") -> dict:
    return {
        "packet_id": f"JDP-{verdict}",
        "decision_subject_ref": f"claim://altas/retrieval-packet/{verdict}",
        "verdict": verdict,
        "rationale": f"Bounded advisory rationale for {verdict}.",
        "evidence_refs": ["evidence://store/handle/aaa"],
        "opposition_refs": ["dars://opposition/packet/ccc"],
    }


def _packet(verdict: str = "pass") -> dict:
    from hisys.judge import build_judge_gate_result_packet, render_judge_gate_result

    return build_judge_gate_result_packet(render_judge_gate_result(_payload(verdict)))


def _packet_with_id(verdict: str, packet_id: str) -> dict:
    from hisys.judge import build_judge_gate_result_packet, render_judge_gate_result

    payload = _payload(verdict)
    payload["packet_id"] = packet_id
    return build_judge_gate_result_packet(render_judge_gate_result(payload))


def _rejected_packet() -> dict:
    from hisys.judge import build_judge_gate_result_packet, render_judge_gate_result

    payload = _payload("pass")
    del payload["rationale"]
    return build_judge_gate_result_packet(render_judge_gate_result(payload))


def test_export_is_available_from_judge_package() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    assert callable(build_judge_human_review_work_queue)


def test_queue_surfaces_most_restrictive_first() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    queue = build_judge_human_review_work_queue(
        [
            _packet("pass"),
            _packet("fail"),
            _packet("block"),
            _packet("needs_human_review"),
        ]
    )["queue"]

    assert [entry["gate_status"] for entry in queue] == [
        "advisory_block",
        "advisory_fail",
        "advisory_needs_human_review",
        "advisory_pass",
    ]


def test_rejected_packet_is_surfaced_above_advisory_statuses() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    queue = build_judge_human_review_work_queue(
        [_packet("pass"), _packet("block"), _rejected_packet()]
    )["queue"]

    assert queue[0]["gate_status"] == "rejected"


def test_malformed_entry_is_surfaced_first_and_grouped() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue(
        [_packet("block"), {"no_gate_status": True}, ["not", "a", "mapping"]]
    )

    assert result["queue"][0]["gate_status"] == "malformed"
    assert result["packet_count"] == 3
    assert len(result["packet_ids_by_gate_status"]["malformed"]) == 2


def test_groups_packet_ids_by_gate_status_sorted() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    grouped = build_judge_human_review_work_queue(
        [
            _packet_with_id("pass", "JDP-b"),
            _packet_with_id("pass", "JDP-a"),
            _packet_with_id("block", "JDP-c"),
        ]
    )["packet_ids_by_gate_status"]

    assert grouped["advisory_pass"] == ["JDP-a", "JDP-b"]
    assert grouped["advisory_block"] == ["JDP-c"]


def test_grouped_keys_are_ordered_most_restrictive_first() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    grouped = build_judge_human_review_work_queue(
        [_packet("pass"), _packet("block"), _packet("fail")]
    )["packet_ids_by_gate_status"]

    assert list(grouped) == ["advisory_block", "advisory_fail", "advisory_pass"]


def test_grouped_ids_total_equals_packet_count() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue(
        [_packet("pass"), _packet("pass"), _packet("block"), _rejected_packet()]
    )

    total = sum(len(ids) for ids in result["packet_ids_by_gate_status"].values())
    assert total == result["packet_count"] == 4


def test_rejected_packet_uses_unidentified_placeholder_id() -> None:
    from hisys.judge import (
        JUDGE_WORK_QUEUE_UNIDENTIFIED_PACKET_ID,
        build_judge_human_review_work_queue,
    )

    queue = build_judge_human_review_work_queue([_rejected_packet()])["queue"]

    assert queue[0]["packet_id"] == JUDGE_WORK_QUEUE_UNIDENTIFIED_PACKET_ID
    assert queue[0]["gate_status"] == "rejected"


def test_queue_entries_have_expected_keys() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    queue = build_judge_human_review_work_queue([_packet("pass")])["queue"]

    assert all(set(entry) == {"packet_id", "gate_status"} for entry in queue)


def test_single_packet_queue() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue([_packet("fail")])

    assert result["packet_count"] == 1
    assert result["queue"] == [{"packet_id": "JDP-fail", "gate_status": "advisory_fail"}]
    assert result["packet_ids_by_gate_status"] == {"advisory_fail": ["JDP-fail"]}


def test_empty_input_is_deterministic_and_advisory() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue([])

    assert result["packet_count"] == 0
    assert result["queue"] == []
    assert result["packet_ids_by_gate_status"] == {}
    assert result["authority_locks"]["advisory_only"] is True
    assert result["authority_locks"]["requires_human_review"] is True


def test_queue_is_json_serializable_and_round_trips() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue(
        [_packet("pass"), _packet("block"), _rejected_packet()]
    )
    restored = json.loads(json.dumps(result))

    assert restored == result


def test_pins_top_level_authority_locks() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    locks = build_judge_human_review_work_queue([_packet("pass")])["authority_locks"]

    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True


def test_includes_non_authorization_note() -> None:
    from hisys.judge import (
        JUDGE_GATE_NON_AUTHORIZATION_NOTE,
        build_judge_human_review_work_queue,
    )

    result = build_judge_human_review_work_queue([_packet("pass")])

    assert result["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_grants_no_execution_authority() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue([_packet("pass")])

    assert set(result["authority_locks"]) == {
        "advisory_only",
        "requires_human_review",
    }
    serialized = json.dumps(result)
    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in serialized


def test_queue_is_order_independent() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    forward = build_judge_human_review_work_queue(
        [_packet("pass"), _packet("block"), _packet("fail")]
    )
    reverse = build_judge_human_review_work_queue(
        [_packet("fail"), _packet("block"), _packet("pass")]
    )

    assert forward == reverse


def test_accepts_a_generator_input() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue(
        _packet(v) for v in ("pass", "fail")
    )

    assert result["packet_count"] == 2
    assert [entry["gate_status"] for entry in result["queue"]] == [
        "advisory_fail",
        "advisory_pass",
    ]


def test_does_not_mutate_input_packets() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    packet = _packet("pass")
    before = json.dumps(packet)

    build_judge_human_review_work_queue([packet])

    assert json.dumps(packet) == before


def test_returns_independent_mappings() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    packets = [_packet("pass")]
    first = build_judge_human_review_work_queue(packets)
    second = build_judge_human_review_work_queue(packets)

    first["queue_marker"] = "mutated"
    first["queue"].append({"packet_id": "x", "gate_status": "y"})
    first["packet_ids_by_gate_status"]["advisory_pass"].append("x")
    assert "queue_marker" not in second
    assert second["queue"] == [
        {"packet_id": "JDP-pass", "gate_status": "advisory_pass"}
    ]
    assert second["packet_ids_by_gate_status"]["advisory_pass"] == ["JDP-pass"]


def test_top_level_keys_are_the_expected_stable_set() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue([_packet("pass")])

    assert set(result) == {
        "subsystem",
        "kind",
        "packet_count",
        "queue",
        "packet_ids_by_gate_status",
        "authority_locks",
        "non_authorization_note",
    }


def test_subsystem_and_kind_are_pinned() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    result = build_judge_human_review_work_queue([_packet("pass")])

    assert result["subsystem"] == "judge"
    assert result["kind"] == "advisory_gate_result_human_review_work_queue"


def test_same_status_entries_ordered_by_packet_id() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    queue = build_judge_human_review_work_queue(
        [_packet_with_id("pass", "JDP-b"), _packet_with_id("pass", "JDP-a")]
    )["queue"]

    assert [entry["packet_id"] for entry in queue] == ["JDP-a", "JDP-b"]


def test_is_deterministic() -> None:
    from hisys.judge import build_judge_human_review_work_queue

    packets = [_packet("pass"), _packet("block")]
    first = build_judge_human_review_work_queue(packets)
    second = build_judge_human_review_work_queue(packets)

    assert first == second
