"""Judge subsystem-local advisory smoke status review bundle fingerprint tests.

These tests pin ``fingerprint_judge_smoke_status_review_bundle``: a Judge-only,
deterministic, read-only content fingerprint of the smoke status review bundle
produced by ``build_judge_smoke_status_review_bundle``. The fingerprint is a
stable lowercase hex digest computed over the canonical JSON serialization
produced by ``serialize_judge_smoke_status_review_bundle`` (the canonical
byte/text source), for local diffing/deduplication tooling. The fingerprint
function returns the digest string only. This mirrors the gate-result
``fingerprint_judge_advisory_panel_review_bundle`` lineage.

The fingerprint is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the fingerprinted
bundle stays advisory-only and always requires human review, matching the Judge
authority boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.

The CLI fingerprint status-bundle mode is::

    PYTHONPATH=src:. python3 -m hisys.judge.smoke --status-bundle-fingerprint
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _run_judge_smoke(*args: str) -> subprocess.CompletedProcess[str]:
    env_pythonpath = f"{SRC}:{ROOT}"
    return subprocess.run(
        [sys.executable, "-m", "hisys.judge.smoke", *args],
        cwd=str(ROOT),
        env={
            "PYTHONPATH": env_pythonpath,
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _bundle() -> dict:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        build_judge_smoke_status_review_bundle,
    )

    return build_judge_smoke_status_review_bundle(build_judge_smoke_report())


def _fingerprint() -> str:
    from hisys.judge.smoke import fingerprint_judge_smoke_status_review_bundle

    return fingerprint_judge_smoke_status_review_bundle(_bundle())


def _failing_report() -> dict:
    """A synthetic smoke report exercising the failure / mismatch path."""

    return {
        "subsystem": "judge",
        "kind": "advisory_smoke_report",
        "mode": "local_fixture_in_process",
        "smoke_passed": False,
        "fixtures": [
            {
                "label": "matched_case",
                "gate_status": "advisory_pass",
                "outcome_matches_expectation": True,
                "advisory_only_locked": True,
                "requires_human_review_locked": True,
                "no_escalation_authority": True,
            },
            {
                "label": "mismatched_case",
                "gate_status": "advisory_fail",
                "outcome_matches_expectation": False,
                "advisory_only_locked": True,
                "requires_human_review_locked": True,
                "no_escalation_authority": True,
            },
        ],
        "checks": [
            {"name": "check_one", "passed": True},
            {"name": "check_two", "passed": False},
        ],
        "bundle_fingerprint": "deadbeef",
        "bundle_fingerprint_algorithm": "sha256",
        "bundle_serialized_byte_length": 123,
    }


def test_fingerprint_importable_and_callable() -> None:
    from hisys.judge import smoke

    assert hasattr(smoke, "fingerprint_judge_smoke_status_review_bundle")
    assert callable(smoke.fingerprint_judge_smoke_status_review_bundle)


def test_algorithm_constant_is_exported_and_named() -> None:
    from hisys.judge.smoke import (
        JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM,
    )

    assert JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM == "sha256"


def test_returns_a_string() -> None:
    assert isinstance(_fingerprint(), str)


def test_digest_is_lowercase_hex_of_fixed_length() -> None:
    digest = _fingerprint()

    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(char in "0123456789abcdef" for char in digest)


def test_matches_sha256_of_canonical_serialization() -> None:
    from hisys.judge.smoke import (
        fingerprint_judge_smoke_status_review_bundle,
        serialize_judge_smoke_status_review_bundle,
    )

    bundle = _bundle()
    canonical = serialize_judge_smoke_status_review_bundle(bundle)
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    assert fingerprint_judge_smoke_status_review_bundle(bundle) == expected


def test_is_deterministic_across_calls() -> None:
    from hisys.judge.smoke import fingerprint_judge_smoke_status_review_bundle

    bundle = _bundle()

    assert fingerprint_judge_smoke_status_review_bundle(
        bundle
    ) == fingerprint_judge_smoke_status_review_bundle(bundle)


def test_same_digest_for_insertion_order_equivalent_bundles() -> None:
    from hisys.judge.smoke import fingerprint_judge_smoke_status_review_bundle

    bundle = _bundle()
    reordered = {key: bundle[key] for key in reversed(list(bundle))}

    assert fingerprint_judge_smoke_status_review_bundle(
        reordered
    ) == fingerprint_judge_smoke_status_review_bundle(bundle)


def test_sensitive_to_content_changes() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_status_review_bundle,
        fingerprint_judge_smoke_status_review_bundle,
    )

    passing_bundle = _bundle()
    failing_bundle = build_judge_smoke_status_review_bundle(_failing_report())

    assert fingerprint_judge_smoke_status_review_bundle(
        passing_bundle
    ) != fingerprint_judge_smoke_status_review_bundle(failing_bundle)


def test_failing_report_fingerprint_is_stable() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_status_review_bundle,
        fingerprint_judge_smoke_status_review_bundle,
    )

    bundle = build_judge_smoke_status_review_bundle(_failing_report())

    assert fingerprint_judge_smoke_status_review_bundle(
        bundle
    ) == fingerprint_judge_smoke_status_review_bundle(bundle)


def test_does_not_mutate_input() -> None:
    from hisys.judge.smoke import fingerprint_judge_smoke_status_review_bundle

    bundle = _bundle()
    before = copy.deepcopy(bundle)

    fingerprint_judge_smoke_status_review_bundle(bundle)

    assert bundle == before


def test_grants_no_escalation_authority() -> None:
    from hisys.judge.smoke import fingerprint_judge_smoke_status_review_bundle

    bundle = _bundle()
    digest = fingerprint_judge_smoke_status_review_bundle(bundle)

    # The function returns only a digest string and leaves the advisory-only
    # locks intact -- no packet, no authority object, no escalation handle.
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


def test_fingerprint_cli_returns_zero_and_emits_identity_packet() -> None:
    completed = _run_judge_smoke("--status-bundle-fingerprint")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.endswith("\n")
    payload = json.loads(completed.stdout)
    assert payload["kind"] == "advisory_smoke_status_review_bundle_fingerprint"
    assert payload["subsystem"] == "judge"
    assert payload["smoke_passed"] is True
    assert payload["fingerprint_algorithm"] == "sha256"
    assert payload["fingerprint"] == _fingerprint()


def test_fingerprint_cli_identity_packet_preserves_locks_and_note() -> None:
    from hisys.judge import JUDGE_GATE_NON_AUTHORIZATION_NOTE

    completed = _run_judge_smoke("--status-bundle-fingerprint")
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)

    assert payload["authority_locks"] == {
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
        assert forbidden not in payload["authority_locks"]
    assert payload["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_default_and_other_modes_cli_still_work() -> None:
    default = _run_judge_smoke()
    assert default.returncode == 0, default.stderr
    assert json.loads(default.stdout)["kind"] == "advisory_smoke_report"

    summary = _run_judge_smoke("--summary")
    assert summary.returncode == 0, summary.stderr
    assert json.loads(summary.stdout)["kind"] == "advisory_smoke_status"

    text = _run_judge_smoke("--text")
    assert text.returncode == 0, text.stderr
    assert text.stdout.startswith("Judge Advisory Smoke Status: PASS")

    status_bundle = _run_judge_smoke("--status-bundle")
    assert status_bundle.returncode == 0, status_bundle.stderr
    assert json.loads(status_bundle.stdout)["kind"] == (
        "advisory_smoke_status_review_bundle"
    )

    canonical = _run_judge_smoke("--status-bundle-canonical")
    assert canonical.returncode == 0, canonical.stderr
    assert json.loads(canonical.stdout)["kind"] == (
        "advisory_smoke_status_review_bundle"
    )


def test_fingerprint_mutually_exclusive_with_other_output_modes() -> None:
    for other in ("--text", "--summary", "--status-bundle", "--status-bundle-canonical"):
        completed = _run_judge_smoke("--status-bundle-fingerprint", other)
        assert completed.returncode != 0
        assert "not allowed with" in completed.stderr or "mutually exclusive" in (
            completed.stderr.lower()
        )
