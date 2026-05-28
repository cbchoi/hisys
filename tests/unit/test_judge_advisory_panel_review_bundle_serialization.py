"""Judge advisory panel review bundle serialization tests.

These tests pin the Judge-only, read-only serialization of an advisory panel
review bundle (the mapping produced by
``build_judge_advisory_panel_review_bundle``) into a single deterministic,
canonical JSON text string with stable sorted keys for local logging/diffing
tooling. The serializer returns the string only.

The serializer is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the serialized bundle
stays advisory-only and always requires human review, matching the Judge
authority boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.
"""

from __future__ import annotations

from typing import Any


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


def _serialized(*verdicts: str) -> str:
    from hisys.judge import serialize_judge_advisory_panel_review_bundle

    return serialize_judge_advisory_panel_review_bundle(_bundle(*verdicts))


def _keys_are_recursively_sorted(value: Any) -> bool:
    if isinstance(value, dict):
        keys = list(value.keys())
        if keys != sorted(keys):
            return False
        return all(_keys_are_recursively_sorted(v) for v in value.values())
    if isinstance(value, list):
        return all(_keys_are_recursively_sorted(v) for v in value)
    return True


def test_export_is_available_from_judge_package() -> None:
    from hisys.judge import serialize_judge_advisory_panel_review_bundle

    assert callable(serialize_judge_advisory_panel_review_bundle)


def test_returns_a_string() -> None:
    assert isinstance(_serialized("pass"), str)


def test_round_trips_to_the_bundle() -> None:
    import json

    bundle = _bundle("pass", "fail", "block")
    from hisys.judge import serialize_judge_advisory_panel_review_bundle

    assert json.loads(serialize_judge_advisory_panel_review_bundle(bundle)) == bundle


def test_keys_are_recursively_sorted() -> None:
    import json

    reloaded = json.loads(_serialized("pass", "block", "fail"))

    assert _keys_are_recursively_sorted(reloaded)


def test_is_compact_single_line() -> None:
    serialized = _serialized("pass", "block")

    assert "\n" not in serialized


def test_is_canonical_form() -> None:
    import json

    from hisys.judge import serialize_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "fail", "block")

    assert serialize_judge_advisory_panel_review_bundle(bundle) == json.dumps(
        bundle, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def test_is_deterministic() -> None:
    from hisys.judge import serialize_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "block", "fail")

    assert serialize_judge_advisory_panel_review_bundle(
        bundle
    ) == serialize_judge_advisory_panel_review_bundle(bundle)


def test_independent_of_input_key_insertion_order() -> None:
    from hisys.judge import serialize_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "block")
    reordered = {key: bundle[key] for key in reversed(list(bundle))}

    assert serialize_judge_advisory_panel_review_bundle(
        reordered
    ) == serialize_judge_advisory_panel_review_bundle(bundle)


def test_empty_bundle_serializes() -> None:
    import json

    from hisys.judge import (
        build_judge_advisory_panel_review_bundle,
        serialize_judge_advisory_panel_review_bundle,
    )

    bundle = build_judge_advisory_panel_review_bundle([])
    reloaded = json.loads(serialize_judge_advisory_panel_review_bundle(bundle))

    assert reloaded == bundle
    assert reloaded["packet_count"] == 0


def test_does_not_mutate_input() -> None:
    import copy

    from hisys.judge import serialize_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "block")
    before = copy.deepcopy(bundle)

    serialize_judge_advisory_panel_review_bundle(bundle)

    assert bundle == before


def test_preserves_advisory_authority_locks() -> None:
    import json

    reloaded = json.loads(_serialized("pass", "block"))

    assert reloaded["authority_locks"] == {
        "advisory_only": True,
        "requires_human_review": True,
    }


def test_no_escalation_authority_keys_after_round_trip() -> None:
    import json

    reloaded = json.loads(_serialized("pass", "block"))

    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in reloaded["authority_locks"]


def test_includes_non_authorization_note() -> None:
    import json

    from hisys.judge import JUDGE_GATE_NON_AUTHORIZATION_NOTE

    reloaded = json.loads(_serialized("pass"))

    assert reloaded["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_round_trip_preserves_report_and_report_text() -> None:
    import json

    bundle = _bundle("pass", "fail", "block")
    reloaded = json.loads(_serialized("pass", "fail", "block"))

    assert reloaded["report"] == bundle["report"]
    assert reloaded["report_text"] == bundle["report_text"]


def test_rejected_packet_surfaces_after_round_trip() -> None:
    import json

    from hisys.judge import (
        build_judge_advisory_panel_review_bundle,
        serialize_judge_advisory_panel_review_bundle,
    )

    bundle = build_judge_advisory_panel_review_bundle(
        [_packet("pass"), _rejected_packet()]
    )
    reloaded = json.loads(serialize_judge_advisory_panel_review_bundle(bundle))

    assert reloaded["report"]["panel_summary"]["most_restrictive_gate_status"] == (
        "rejected"
    )
