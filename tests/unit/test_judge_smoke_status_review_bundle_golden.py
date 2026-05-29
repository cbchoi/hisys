"""Golden evidence test for the Judge advisory smoke status review bundle.

This pins a committed, deterministic golden artifact for the smoke status
review bundle under ``docs/examples/judge/`` and asserts that the three pure
Judge functions reproduce it byte-for-content:

    build_judge_smoke_status_review_bundle
      -> serialize_judge_smoke_status_review_bundle
      -> fingerprint_judge_smoke_status_review_bundle

It mirrors the committed ``docs/examples/judge/judge-advisory-smoke-report.json``
golden evidence: the artifact is read-only at runtime, deterministic, and
Judge-only. The pure functions do no I/O and grant no execution authority --
the artifact records advisory-only / requires-human-review content with no
escalation lock and no action authorization claim.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE_EVIDENCE = (
    ROOT / "docs" / "examples" / "judge" / "judge-advisory-smoke-status-review-bundle.json"
)

# Pinned content fingerprint of the committed status review bundle (the SHA-256
# digest of its canonical serialization). Any content change changes this digest.
EXPECTED_BUNDLE_FINGERPRINT = (
    "b7242302e3fcece3afc4094e093d1d906ba80e89c2e0277a1e2b89e02839b55d"
)

_ESCALATION_LOCKS = (
    "live_external_action_authorized",
    "mutation_authorized",
    "publication_authorized",
    "remote_push_authorized",
    "human_review_removal_authorized",
)


def _fresh_bundle() -> dict:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        build_judge_smoke_status_review_bundle,
    )

    return build_judge_smoke_status_review_bundle(build_judge_smoke_report())


def test_golden_artifact_exists() -> None:
    assert BUNDLE_EVIDENCE.exists(), (
        f"missing committed smoke status review bundle evidence: {BUNDLE_EVIDENCE}"
    )


def test_golden_artifact_matches_builder_output() -> None:
    recorded = json.loads(BUNDLE_EVIDENCE.read_text(encoding="utf-8"))

    assert recorded == _fresh_bundle()


def test_golden_artifact_is_byte_stable_pretty_json() -> None:
    raw = BUNDLE_EVIDENCE.read_text(encoding="utf-8")
    recorded = json.loads(raw)

    # The committed artifact is pretty-printed with sorted keys plus a trailing
    # newline, exactly as the ``--status-bundle`` CLI emits it. Re-rendering the
    # loaded mapping must reproduce the committed bytes character-for-character.
    assert raw == json.dumps(recorded, indent=2, sort_keys=True) + "\n"


def test_golden_artifact_canonical_serialization_reproduces() -> None:
    from hisys.judge.smoke import serialize_judge_smoke_status_review_bundle

    recorded = json.loads(BUNDLE_EVIDENCE.read_text(encoding="utf-8"))
    fresh = _fresh_bundle()

    canonical_recorded = serialize_judge_smoke_status_review_bundle(recorded)
    canonical_fresh = serialize_judge_smoke_status_review_bundle(fresh)

    assert canonical_recorded == canonical_fresh
    assert json.loads(canonical_recorded) == recorded


def test_golden_artifact_fingerprint_reproduces_pinned_digest() -> None:
    from hisys.judge.smoke import (
        JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM,
        fingerprint_judge_smoke_status_review_bundle,
    )

    recorded = json.loads(BUNDLE_EVIDENCE.read_text(encoding="utf-8"))

    digest = fingerprint_judge_smoke_status_review_bundle(recorded)
    assert JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM == "sha256"
    assert digest == EXPECTED_BUNDLE_FINGERPRINT
    assert digest == fingerprint_judge_smoke_status_review_bundle(_fresh_bundle())


def test_golden_artifact_records_advisory_identity() -> None:
    recorded = json.loads(BUNDLE_EVIDENCE.read_text(encoding="utf-8"))

    assert recorded["subsystem"] == "judge"
    assert recorded["kind"] == "advisory_smoke_status_review_bundle"
    assert recorded["smoke_passed"] is True
    assert isinstance(recorded["status_text"], str)
    assert recorded["summary"]["kind"] == "advisory_smoke_status"


def test_golden_artifact_preserves_authority_locks() -> None:
    recorded = json.loads(BUNDLE_EVIDENCE.read_text(encoding="utf-8"))

    locks = recorded["authority_locks"]
    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True
    # The bundle's top-level locks carry no escalation keys at all.
    for name in _ESCALATION_LOCKS:
        assert name not in locks

    # The embedded summary pins every escalation lock false.
    summary_locks = recorded["summary"]["authority_locks"]
    for name in _ESCALATION_LOCKS:
        assert summary_locks[name] is False


def test_golden_artifact_carries_no_action_authorization_claim() -> None:
    raw = BUNDLE_EVIDENCE.read_text(encoding="utf-8")

    assert "A human reviewer must decide before any action is taken." in raw
    # No live/provider/credential/network/escalation authorization claim leaks in.
    lowered = raw.lower()
    for forbidden in ("api_key", "credential", "authorized\": true"):
        assert forbidden not in lowered
