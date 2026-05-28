"""Judge advisory panel review bundle fingerprint tests.

These tests pin the Judge-only, read-only content fingerprint of an advisory
panel review bundle (the mapping produced by
``build_judge_advisory_panel_review_bundle``). The fingerprint is a stable hex
digest computed over the canonical JSON serialization produced by
``serialize_judge_advisory_panel_review_bundle`` (the canonical byte/text
source), for local diffing/deduplication tooling. The fingerprint function
returns the digest string only.

The fingerprint is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the fingerprinted
bundle stays advisory-only and always requires human review, matching the Judge
authority boundary in ``src/hisys/judge/ralph.md`` and
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


def _fingerprint(*verdicts: str) -> str:
    from hisys.judge import fingerprint_judge_advisory_panel_review_bundle

    return fingerprint_judge_advisory_panel_review_bundle(_bundle(*verdicts))


def test_export_is_available_from_judge_package() -> None:
    from hisys.judge import fingerprint_judge_advisory_panel_review_bundle

    assert callable(fingerprint_judge_advisory_panel_review_bundle)


def test_algorithm_constant_is_exported_and_named() -> None:
    from hisys.judge import (
        JUDGE_ADVISORY_PANEL_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM,
    )

    assert JUDGE_ADVISORY_PANEL_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM == "sha256"


def test_returns_a_string() -> None:
    assert isinstance(_fingerprint("pass"), str)


def test_digest_is_lowercase_hex_of_fixed_length() -> None:
    digest = _fingerprint("pass", "block")

    assert len(digest) == 64
    assert all(char in "0123456789abcdef" for char in digest)


def test_matches_sha256_of_canonical_serialization() -> None:
    import hashlib

    from hisys.judge import (
        fingerprint_judge_advisory_panel_review_bundle,
        serialize_judge_advisory_panel_review_bundle,
    )

    bundle = _bundle("pass", "fail", "block")
    canonical = serialize_judge_advisory_panel_review_bundle(bundle)
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    assert fingerprint_judge_advisory_panel_review_bundle(bundle) == expected


def test_is_deterministic_across_calls() -> None:
    from hisys.judge import fingerprint_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "block", "fail")

    assert fingerprint_judge_advisory_panel_review_bundle(
        bundle
    ) == fingerprint_judge_advisory_panel_review_bundle(bundle)


def test_sensitive_to_content_changes() -> None:
    assert _fingerprint("pass") != _fingerprint("block")


def test_same_digest_for_insertion_order_equivalent_bundles() -> None:
    from hisys.judge import fingerprint_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "block")
    reordered = {key: bundle[key] for key in reversed(list(bundle))}

    assert fingerprint_judge_advisory_panel_review_bundle(
        reordered
    ) == fingerprint_judge_advisory_panel_review_bundle(bundle)


def test_empty_bundle_fingerprints() -> None:
    import hashlib

    from hisys.judge import (
        build_judge_advisory_panel_review_bundle,
        fingerprint_judge_advisory_panel_review_bundle,
        serialize_judge_advisory_panel_review_bundle,
    )

    bundle = build_judge_advisory_panel_review_bundle([])
    digest = fingerprint_judge_advisory_panel_review_bundle(bundle)

    assert digest == hashlib.sha256(
        serialize_judge_advisory_panel_review_bundle(bundle).encode("utf-8")
    ).hexdigest()
    assert len(digest) == 64


def test_rejected_packet_preserved_through_canonical_source() -> None:
    from hisys.judge import (
        build_judge_advisory_panel_review_bundle,
        fingerprint_judge_advisory_panel_review_bundle,
    )

    rejected_bundle = build_judge_advisory_panel_review_bundle(
        [_packet("pass"), _rejected_packet()]
    )
    clean_bundle = build_judge_advisory_panel_review_bundle(
        [_packet("pass"), _packet("pass")]
    )

    rejected_digest = fingerprint_judge_advisory_panel_review_bundle(rejected_bundle)

    # The rejected outcome is part of the canonical content, so its fingerprint
    # is stable and distinct from an otherwise-similar all-clean bundle.
    assert rejected_digest == fingerprint_judge_advisory_panel_review_bundle(
        rejected_bundle
    )
    assert rejected_digest != fingerprint_judge_advisory_panel_review_bundle(
        clean_bundle
    )


def test_does_not_mutate_input() -> None:
    import copy

    from hisys.judge import fingerprint_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "block")
    before = copy.deepcopy(bundle)

    fingerprint_judge_advisory_panel_review_bundle(bundle)

    assert bundle == before


def test_grants_no_escalation_authority() -> None:
    from hisys.judge import fingerprint_judge_advisory_panel_review_bundle

    bundle = _bundle("pass", "block")
    digest = fingerprint_judge_advisory_panel_review_bundle(bundle)

    # The function returns only a digest string -- no packet, no authority
    # object, no escalation handle -- and leaves the advisory-only locks intact.
    assert isinstance(digest, str)
    assert bundle["authority_locks"] == {
        "advisory_only": True,
        "requires_human_review": True,
    }
    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in bundle["authority_locks"]
