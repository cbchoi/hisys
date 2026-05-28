"""Judge advisory gate-result panel report tests.

These tests pin the Judge-only, read-only composition of one or more advisory
gate-result packets into a single bounded advisory panel report.
``build_judge_advisory_panel_report`` bundles the panel summary
(``summarize_judge_gate_result_packets``) and the human-review work queue
(``build_judge_human_review_work_queue``) over the same gate-result packets into
one plain, deterministic, JSON-serializable mapping.

The composition is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the report stays
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
    from hisys.judge import build_judge_advisory_panel_report

    assert callable(build_judge_advisory_panel_report)


def test_bundles_panel_summary_and_work_queue() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report([_packet("pass"), _packet("block")])

    assert report["subsystem"] == "judge"
    assert report["kind"] == "advisory_gate_result_panel_report"
    assert report["packet_count"] == 2
    assert report["panel_summary"]["kind"] == "advisory_gate_result_panel_summary"
    assert (
        report["human_review_work_queue"]["kind"]
        == "advisory_gate_result_human_review_work_queue"
    )


def test_panel_summary_matches_standalone() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_report,
        summarize_judge_gate_result_packets,
    )

    packets = [_packet("pass"), _packet("fail"), _rejected_packet()]
    report = build_judge_advisory_panel_report(packets)

    assert report["panel_summary"] == summarize_judge_gate_result_packets(packets)


def test_work_queue_matches_standalone() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_report,
        build_judge_human_review_work_queue,
    )

    packets = [_packet("pass"), _packet("block"), _rejected_packet()]
    report = build_judge_advisory_panel_report(packets)

    assert (
        report["human_review_work_queue"]
        == build_judge_human_review_work_queue(packets)
    )


def test_top_level_keys_are_the_expected_stable_set() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report([_packet("pass")])

    assert set(report) == {
        "subsystem",
        "kind",
        "packet_count",
        "panel_summary",
        "human_review_work_queue",
        "authority_locks",
        "non_authorization_note",
    }


def test_subsystem_and_kind_are_pinned() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report([_packet("pass")])

    assert report["subsystem"] == "judge"
    assert report["kind"] == "advisory_gate_result_panel_report"


def test_empty_input_is_deterministic_and_advisory() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report([])

    assert report["packet_count"] == 0
    assert report["panel_summary"]["packet_count"] == 0
    assert report["panel_summary"]["most_restrictive_gate_status"] is None
    assert report["human_review_work_queue"]["packet_count"] == 0
    assert report["human_review_work_queue"]["queue"] == []
    assert report["authority_locks"]["advisory_only"] is True
    assert report["authority_locks"]["requires_human_review"] is True


def test_report_is_json_serializable_and_round_trips() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report(
        [_packet("pass"), _packet("block"), _rejected_packet()]
    )
    restored = json.loads(json.dumps(report))

    assert restored == report


def test_pins_top_level_authority_locks() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    locks = build_judge_advisory_panel_report([_packet("pass")])["authority_locks"]

    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True


def test_includes_non_authorization_note() -> None:
    from hisys.judge import (
        JUDGE_GATE_NON_AUTHORIZATION_NOTE,
        build_judge_advisory_panel_report,
    )

    report = build_judge_advisory_panel_report([_packet("pass")])

    assert report["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_grants_no_execution_authority() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report([_packet("pass")])

    assert set(report["authority_locks"]) == {
        "advisory_only",
        "requires_human_review",
    }
    serialized = json.dumps(report)
    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in serialized


def test_report_is_order_independent() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    forward = build_judge_advisory_panel_report(
        [_packet("pass"), _packet("block"), _packet("fail")]
    )
    reverse = build_judge_advisory_panel_report(
        [_packet("fail"), _packet("block"), _packet("pass")]
    )

    assert forward == reverse


def test_accepts_a_generator_input() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report(
        _packet(v) for v in ("pass", "fail")
    )

    assert report["packet_count"] == 2
    assert report["panel_summary"]["packet_count"] == 2
    assert report["human_review_work_queue"]["packet_count"] == 2
    assert [
        entry["gate_status"]
        for entry in report["human_review_work_queue"]["queue"]
    ] == ["advisory_fail", "advisory_pass"]


def test_does_not_mutate_input_packets() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    packet = _packet("pass")
    before = json.dumps(packet)

    build_judge_advisory_panel_report([packet])

    assert json.dumps(packet) == before


def test_returns_independent_mappings() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    packets = [_packet("pass")]
    first = build_judge_advisory_panel_report(packets)
    second = build_judge_advisory_panel_report(packets)

    first["report_marker"] = "mutated"
    first["panel_summary"]["gate_status_counts"]["advisory_pass"] = 999
    first["human_review_work_queue"]["queue"].append(
        {"packet_id": "x", "gate_status": "y"}
    )
    assert "report_marker" not in second
    assert second["panel_summary"]["gate_status_counts"]["advisory_pass"] == 1
    assert second["human_review_work_queue"]["queue"] == [
        {"packet_id": "JDP-pass", "gate_status": "advisory_pass"}
    ]


def test_is_deterministic() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    packets = [_packet("pass"), _packet("block")]
    first = build_judge_advisory_panel_report(packets)
    second = build_judge_advisory_panel_report(packets)

    assert first == second


def test_report_packet_count_matches_nested_counts() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report(
        [_packet("pass"), _packet("fail"), _packet("block"), _rejected_packet()]
    )

    assert report["packet_count"] == 4
    assert report["panel_summary"]["packet_count"] == 4
    assert report["human_review_work_queue"]["packet_count"] == 4


def test_malformed_entries_are_carried_through_both_views() -> None:
    from hisys.judge import build_judge_advisory_panel_report

    report = build_judge_advisory_panel_report(
        [_packet("pass"), {"no_gate_status": True}, ["not", "a", "mapping"]]
    )

    assert report["packet_count"] == 3
    assert report["panel_summary"]["most_restrictive_gate_status"] == "malformed"
    assert report["human_review_work_queue"]["queue"][0]["gate_status"] == "malformed"
