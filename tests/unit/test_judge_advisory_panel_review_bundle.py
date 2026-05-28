"""Judge advisory panel review bundle tests.

These tests pin the Judge-only, read-only bundling of a JSON advisory panel
report (the mapping produced by ``build_judge_advisory_panel_report``) and its
human-readable text rendering (produced by
``render_judge_advisory_panel_report_text``) into one deterministic,
JSON-serializable advisory panel review bundle carrying both the ``report``
mapping and its ``report_text`` for local tooling and human review.

The bundle builder is pure and side-effect free: it performs no live
provider/model call, no raw provider API call, no network request, no
credential lookup, no vault or evidence mutation, no remote push, no
publication, and no cross-subsystem call. It grants no execution authority --
the bundle stays advisory-only and always requires human review, matching the
Judge authority boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.
"""

from __future__ import annotations


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


def _bundle(*verdicts: str) -> dict:
    from hisys.judge import build_judge_advisory_panel_review_bundle

    return build_judge_advisory_panel_review_bundle([_packet(v) for v in verdicts])


def test_export_is_available_from_judge_package() -> None:
    from hisys.judge import build_judge_advisory_panel_review_bundle

    assert callable(build_judge_advisory_panel_review_bundle)


def test_returns_a_mapping() -> None:
    assert isinstance(_bundle("pass"), dict)


def test_has_stable_top_level_keys() -> None:
    assert set(_bundle("pass", "block")) == {
        "subsystem",
        "kind",
        "packet_count",
        "report",
        "report_text",
        "authority_locks",
        "non_authorization_note",
    }


def test_subsystem_and_kind() -> None:
    bundle = _bundle("pass")

    assert bundle["subsystem"] == "judge"
    assert bundle["kind"] == "advisory_gate_result_panel_review_bundle"


def test_report_matches_panel_report_builder() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_report,
        build_judge_advisory_panel_review_bundle,
    )

    packets = [_packet("pass"), _packet("block")]
    bundle = build_judge_advisory_panel_review_bundle(packets)

    assert bundle["report"] == build_judge_advisory_panel_report(packets)


def test_report_text_matches_text_renderer() -> None:
    from hisys.judge import render_judge_advisory_panel_report_text

    bundle = _bundle("pass", "fail", "block")

    assert bundle["report_text"] == render_judge_advisory_panel_report_text(
        bundle["report"]
    )


def test_report_text_is_a_string() -> None:
    assert isinstance(_bundle("pass")["report_text"], str)


def test_packet_count_matches_report() -> None:
    bundle = _bundle("pass", "fail", "block")

    assert bundle["packet_count"] == 3
    assert bundle["packet_count"] == bundle["report"]["packet_count"]


def test_authority_locks_pinned_with_no_escalation_keys() -> None:
    locks = _bundle("pass", "block")["authority_locks"]

    assert locks == {"advisory_only": True, "requires_human_review": True}


def test_includes_non_authorization_note() -> None:
    from hisys.judge import JUDGE_GATE_NON_AUTHORIZATION_NOTE

    bundle = _bundle("pass")

    assert bundle["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_empty_bundle() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_review_bundle,
        render_judge_advisory_panel_report_text,
    )

    bundle = build_judge_advisory_panel_review_bundle([])

    assert bundle["packet_count"] == 0
    assert bundle["report"]["packet_count"] == 0
    assert bundle["report_text"] == render_judge_advisory_panel_report_text(
        bundle["report"]
    )
    assert "Packets reviewed: 0" in bundle["report_text"]


def test_is_json_serializable() -> None:
    import json

    bundle = _bundle("pass", "fail", "block")
    reloaded = json.loads(json.dumps(bundle))

    assert reloaded == bundle


def test_is_deterministic() -> None:
    from hisys.judge import build_judge_advisory_panel_review_bundle

    packets = [_packet("pass"), _packet("block"), _packet("fail")]

    assert build_judge_advisory_panel_review_bundle(
        packets
    ) == build_judge_advisory_panel_review_bundle(packets)


def test_one_shot_iterable_populates_bundle() -> None:
    from hisys.judge import build_judge_advisory_panel_review_bundle

    packets = [_packet("pass"), _packet("block")]
    bundle = build_judge_advisory_panel_review_bundle(p for p in packets)

    assert bundle["packet_count"] == 2
    assert bundle["report"]["panel_summary"]["packet_count"] == 2
    assert bundle["report"]["human_review_work_queue"]["packet_count"] == 2
    assert "Packets reviewed: 2" in bundle["report_text"]


def test_does_not_mutate_inputs() -> None:
    import copy

    from hisys.judge import build_judge_advisory_panel_review_bundle

    packets = [_packet("pass"), _packet("block")]
    before = copy.deepcopy(packets)

    build_judge_advisory_panel_review_bundle(packets)

    assert packets == before


def test_returns_fresh_independent_mapping() -> None:
    from hisys.judge import build_judge_advisory_panel_review_bundle

    packets = [_packet("pass")]
    first = build_judge_advisory_panel_review_bundle(packets)
    second = build_judge_advisory_panel_review_bundle(packets)

    assert first is not second
    assert first["report"] is not second["report"]
    assert first["authority_locks"] is not second["authority_locks"]


def test_rejected_packet_surfaces_in_bundle() -> None:
    from hisys.judge import build_judge_advisory_panel_review_bundle

    bundle = build_judge_advisory_panel_review_bundle(
        [_packet("pass"), _rejected_packet()]
    )

    assert bundle["report"]["panel_summary"]["most_restrictive_gate_status"] == (
        "rejected"
    )
    assert "Most restrictive gate status: rejected" in bundle["report_text"]


def test_malformed_entry_surfaces_in_bundle() -> None:
    from hisys.judge import build_judge_advisory_panel_review_bundle

    bundle = build_judge_advisory_panel_review_bundle(
        [_packet("pass"), {"no_gate_status": True}]
    )

    assert bundle["report"]["panel_summary"]["most_restrictive_gate_status"] == (
        "malformed"
    )
    assert "Most restrictive gate status: malformed" in bundle["report_text"]


def test_no_escalation_authority_keys_in_top_level_locks() -> None:
    locks = _bundle("pass", "block")["authority_locks"]

    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in locks
