"""Judge advisory gate-result panel summary tests.

These tests pin the Judge-only, read-only aggregation of one or more advisory
gate-result packets into a bounded advisory panel summary.
``summarize_judge_gate_result_packets`` consumes the JSON-serializable packets
produced by ``build_judge_gate_result_packet`` and returns a plain,
deterministic mapping carrying the counts per gate status, the most-restrictive
advisory outcome, and the pinned Judge authority locks.

The aggregation is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the summary stays
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


def _rejected_packet() -> dict:
    from hisys.judge import build_judge_gate_result_packet, render_judge_gate_result

    payload = _payload("pass")
    del payload["rationale"]
    return build_judge_gate_result_packet(render_judge_gate_result(payload))


def test_export_is_available_from_judge_package() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    assert callable(summarize_judge_gate_result_packets)


def test_summarizes_multiple_packets_with_counts_per_gate_status() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("pass"), _packet("pass"), _packet("block")]
    )

    assert summary["subsystem"] == "judge"
    assert summary["kind"] == "advisory_gate_result_panel_summary"
    assert summary["packet_count"] == 3
    assert summary["gate_status_counts"] == {
        "advisory_block": 1,
        "advisory_pass": 2,
    }


def test_counts_include_rejected_packets() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("pass"), _rejected_packet()]
    )

    assert summary["packet_count"] == 2
    assert summary["gate_status_counts"]["rejected"] == 1
    assert summary["gate_status_counts"]["advisory_pass"] == 1


def test_most_restrictive_is_block_over_pass_and_fail() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("pass"), _packet("fail"), _packet("block")]
    )

    assert summary["most_restrictive_gate_status"] == "advisory_block"


def test_most_restrictive_needs_human_review_over_pass() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("pass"), _packet("needs_human_review")]
    )

    assert summary["most_restrictive_gate_status"] == "advisory_needs_human_review"


def test_most_restrictive_fail_over_needs_human_review() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("needs_human_review"), _packet("fail")]
    )

    assert summary["most_restrictive_gate_status"] == "advisory_fail"


def test_rejected_is_most_restrictive_over_advisory_statuses() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("block"), _rejected_packet()]
    )

    assert summary["most_restrictive_gate_status"] == "rejected"


def test_single_packet_summary() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets([_packet("fail")])

    assert summary["packet_count"] == 1
    assert summary["gate_status_counts"] == {"advisory_fail": 1}
    assert summary["most_restrictive_gate_status"] == "advisory_fail"


def test_empty_input_is_deterministic_and_advisory() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets([])

    assert summary["packet_count"] == 0
    assert summary["gate_status_counts"] == {}
    assert summary["most_restrictive_gate_status"] is None
    assert summary["authority_locks"]["advisory_only"] is True
    assert summary["authority_locks"]["requires_human_review"] is True


def test_summary_is_json_serializable_and_round_trips() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("pass"), _packet("block"), _rejected_packet()]
    )
    restored = json.loads(json.dumps(summary))

    assert restored == summary


def test_summary_pins_top_level_authority_locks() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    locks = summarize_judge_gate_result_packets([_packet("pass")])["authority_locks"]

    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True


def test_summary_includes_non_authorization_note() -> None:
    from hisys.judge import (
        JUDGE_GATE_NON_AUTHORIZATION_NOTE,
        summarize_judge_gate_result_packets,
    )

    summary = summarize_judge_gate_result_packets([_packet("pass")])

    assert summary["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_summary_grants_no_execution_authority() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets([_packet("pass")])

    assert set(summary["authority_locks"]) == {
        "advisory_only",
        "requires_human_review",
    }
    serialized = json.dumps(summary)
    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in serialized


def test_summary_is_order_independent() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    forward = summarize_judge_gate_result_packets(
        [_packet("pass"), _packet("block"), _packet("fail")]
    )
    reverse = summarize_judge_gate_result_packets(
        [_packet("fail"), _packet("block"), _packet("pass")]
    )

    assert forward == reverse


def test_malformed_entry_is_counted_and_most_restrictive() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [_packet("pass"), {"no_gate_status": True}, ["not", "a", "mapping"]]
    )

    assert summary["packet_count"] == 3
    assert summary["gate_status_counts"]["malformed"] == 2
    assert summary["most_restrictive_gate_status"] == "malformed"


def test_accepts_a_generator_input() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        _packet(v) for v in ("pass", "fail")
    )

    assert summary["packet_count"] == 2
    assert summary["gate_status_counts"] == {"advisory_fail": 1, "advisory_pass": 1}


def test_gate_status_counts_values_are_plain_ints() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    counts = summarize_judge_gate_result_packets([_packet("pass")])[
        "gate_status_counts"
    ]

    assert isinstance(counts, dict)
    assert all(isinstance(value, int) for value in counts.values())


def test_summary_is_deterministic() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    packets = [_packet("pass"), _packet("block")]
    first = summarize_judge_gate_result_packets(packets)
    second = summarize_judge_gate_result_packets(packets)

    assert first == second


def test_summary_returns_independent_mappings() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    packets = [_packet("pass")]
    first = summarize_judge_gate_result_packets(packets)
    second = summarize_judge_gate_result_packets(packets)

    first["panel_marker"] = "mutated"
    first["gate_status_counts"]["advisory_pass"] = 999
    assert "panel_marker" not in second
    assert second["gate_status_counts"]["advisory_pass"] == 1


def test_summary_does_not_mutate_input_packets() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    packet = _packet("pass")
    before = json.dumps(packet)

    summarize_judge_gate_result_packets([packet])

    assert json.dumps(packet) == before


def test_top_level_keys_are_the_expected_stable_set() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets([_packet("pass")])

    assert set(summary) == {
        "subsystem",
        "kind",
        "packet_count",
        "gate_status_counts",
        "most_restrictive_gate_status",
        "authority_locks",
        "non_authorization_note",
    }


def test_all_bounded_statuses_and_rejected_are_counted() -> None:
    from hisys.judge import summarize_judge_gate_result_packets

    summary = summarize_judge_gate_result_packets(
        [
            _packet("pass"),
            _packet("fail"),
            _packet("block"),
            _packet("needs_human_review"),
            _rejected_packet(),
        ]
    )

    assert summary["packet_count"] == 5
    assert summary["gate_status_counts"] == {
        "advisory_block": 1,
        "advisory_fail": 1,
        "advisory_needs_human_review": 1,
        "advisory_pass": 1,
        "rejected": 1,
    }
    assert summary["most_restrictive_gate_status"] == "rejected"
