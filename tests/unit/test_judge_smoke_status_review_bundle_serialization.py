"""Judge subsystem-local advisory smoke status review bundle serialization tests.

These tests pin ``serialize_judge_smoke_status_review_bundle``: a Judge-only,
deterministic, read-only serialization of the smoke status review bundle
produced by ``build_judge_smoke_status_review_bundle`` into a single canonical
JSON text string with stable sorted keys (compact separators, no insignificant
whitespace) for local logging/diffing tooling. The serializer returns the
string only and serializes the bundle as given, so the pinned
advisory-only/requires-human-review locks and the non-authorization note survive
verbatim in the text. This mirrors the gate-result
``serialize_judge_advisory_panel_review_bundle`` lineage.

The serializer is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the serialized bundle
stays advisory-only and always requires human review, matching the Judge
authority boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.

The CLI canonical status-bundle mode is::

    PYTHONPATH=src:. python3 -m hisys.judge.smoke --status-bundle-canonical
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def _serialized() -> str:
    from hisys.judge.smoke import serialize_judge_smoke_status_review_bundle

    return serialize_judge_smoke_status_review_bundle(_bundle())


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


def _keys_are_recursively_sorted(value: Any) -> bool:
    if isinstance(value, dict):
        keys = list(value.keys())
        if keys != sorted(keys):
            return False
        return all(_keys_are_recursively_sorted(v) for v in value.values())
    if isinstance(value, list):
        return all(_keys_are_recursively_sorted(v) for v in value)
    return True


def test_serializer_importable_and_callable() -> None:
    from hisys.judge import smoke

    assert hasattr(smoke, "serialize_judge_smoke_status_review_bundle")
    assert callable(smoke.serialize_judge_smoke_status_review_bundle)


def test_returns_a_string() -> None:
    assert isinstance(_serialized(), str)


def test_round_trips_to_the_bundle() -> None:
    bundle = _bundle()
    from hisys.judge.smoke import serialize_judge_smoke_status_review_bundle

    assert json.loads(serialize_judge_smoke_status_review_bundle(bundle)) == bundle


def test_keys_are_recursively_sorted() -> None:
    reloaded = json.loads(_serialized())

    assert _keys_are_recursively_sorted(reloaded)


def test_is_compact_single_line() -> None:
    serialized = _serialized()

    # Actual newlines in the status_text are escaped to "\\n" in JSON text, so
    # the canonical string carries no literal newline of its own. (Content
    # substrings like ", " inside status_text are not insignificant whitespace;
    # canonical separators are pinned by test_is_canonical_form.)
    assert "\n" not in serialized


def test_is_canonical_form() -> None:
    from hisys.judge.smoke import serialize_judge_smoke_status_review_bundle

    bundle = _bundle()

    assert serialize_judge_smoke_status_review_bundle(bundle) == json.dumps(
        bundle, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def test_is_deterministic() -> None:
    from hisys.judge.smoke import serialize_judge_smoke_status_review_bundle

    bundle = _bundle()

    assert serialize_judge_smoke_status_review_bundle(
        bundle
    ) == serialize_judge_smoke_status_review_bundle(bundle)


def test_independent_of_input_key_insertion_order() -> None:
    from hisys.judge.smoke import serialize_judge_smoke_status_review_bundle

    bundle = _bundle()
    reordered = {key: bundle[key] for key in reversed(list(bundle))}

    assert serialize_judge_smoke_status_review_bundle(
        reordered
    ) == serialize_judge_smoke_status_review_bundle(bundle)


def test_does_not_mutate_input() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_status_review_bundle,
        serialize_judge_smoke_status_review_bundle,
    )

    bundle = build_judge_smoke_status_review_bundle(_failing_report())
    before = copy.deepcopy(bundle)

    serialize_judge_smoke_status_review_bundle(bundle)

    assert bundle == before


def test_preserves_advisory_authority_locks() -> None:
    reloaded = json.loads(_serialized())

    assert reloaded["authority_locks"] == {
        "advisory_only": True,
        "requires_human_review": True,
    }


def test_no_escalation_authority_keys_after_round_trip() -> None:
    reloaded = json.loads(_serialized())

    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in reloaded["authority_locks"]


def test_includes_non_authorization_note() -> None:
    from hisys.judge import JUDGE_GATE_NON_AUTHORIZATION_NOTE

    reloaded = json.loads(_serialized())

    assert reloaded["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_round_trip_preserves_summary_and_status_text() -> None:
    bundle = _bundle()
    reloaded = json.loads(_serialized())

    assert reloaded["summary"] == bundle["summary"]
    assert reloaded["status_text"] == bundle["status_text"]


def test_accepts_summary_or_report_equivalently() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        build_judge_smoke_status_review_bundle,
        serialize_judge_smoke_status_review_bundle,
        summarize_judge_smoke_report,
    )

    report = build_judge_smoke_report()
    summary = summarize_judge_smoke_report(report)

    from_report = serialize_judge_smoke_status_review_bundle(
        build_judge_smoke_status_review_bundle(report)
    )
    from_summary = serialize_judge_smoke_status_review_bundle(
        build_judge_smoke_status_review_bundle(summary)
    )

    assert from_report == from_summary


def test_failing_report_surfaces_after_round_trip() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_status_review_bundle,
        serialize_judge_smoke_status_review_bundle,
    )

    bundle = build_judge_smoke_status_review_bundle(_failing_report())
    reloaded = json.loads(serialize_judge_smoke_status_review_bundle(bundle))

    assert reloaded["smoke_passed"] is False
    assert reloaded["summary"]["failed_check_names"] == ["check_two"]
    assert reloaded["summary"]["fixture_mismatch_labels"] == ["mismatched_case"]
    assert "Judge Advisory Smoke Status: FAIL" in reloaded["status_text"]


def test_canonical_cli_returns_zero_and_emits_canonical_text() -> None:
    completed = _run_judge_smoke("--status-bundle-canonical")

    assert completed.returncode == 0, completed.stderr
    # Single canonical JSON object on stdout (plus the trailing newline the CLI
    # writes); the JSON text itself carries no insignificant whitespace.
    stdout = completed.stdout
    assert stdout.endswith("\n")
    payload = json.loads(stdout)
    assert payload["kind"] == "advisory_smoke_status_review_bundle"
    assert payload["smoke_passed"] is True


def test_canonical_cli_matches_serializer() -> None:
    completed = _run_judge_smoke("--status-bundle-canonical")
    assert completed.returncode == 0, completed.stderr

    assert completed.stdout == _serialized() + "\n"


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


def test_canonical_mutually_exclusive_with_other_output_modes() -> None:
    for other in ("--text", "--summary", "--status-bundle"):
        completed = _run_judge_smoke("--status-bundle-canonical", other)
        assert completed.returncode != 0
        assert "not allowed with" in completed.stderr or "mutually exclusive" in (
            completed.stderr.lower()
        )
