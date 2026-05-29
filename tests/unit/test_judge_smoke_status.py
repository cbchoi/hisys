"""Judge subsystem-local advisory smoke status-summary projection tests.

These tests pin ``summarize_judge_smoke_report``: a Judge-only, deterministic,
read-only projection that turns the full smoke report produced by
``build_judge_smoke_report`` into a compact, CLI-friendly readiness summary so a
human reviewer or local agent can inspect smoke readiness (pass/fail, which
checks failed, which fixtures mismatched, the bundle fingerprint identity)
without parsing the full report or its embedded panel review bundle.

The projection must be deterministic and side-effect free: it performs no live
provider/model call, no raw provider API call, no network request, no credential
lookup, no vault/evidence mutation, no remote push, and no publication. It
preserves the Judge authority locks recorded in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.

The CLI summary mode is::

    PYTHONPATH=src:. python3 -m hisys.judge.smoke --summary
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

_EXPECTED_SUMMARY_KEYS = {
    "subsystem",
    "kind",
    "mode",
    "smoke_passed",
    "fixture_count",
    "fixtures_matched_expectation",
    "fixture_mismatch_labels",
    "gate_status_counts",
    "checks_total",
    "checks_passed",
    "checks_failed",
    "failed_check_names",
    "advisory_locks_preserved_for_all_fixtures",
    "bundle_fingerprint",
    "bundle_fingerprint_algorithm",
    "bundle_serialized_byte_length",
    "authority_locks",
    "non_authorization_note",
}

_ESCALATION_LOCKS = (
    "live_external_action_authorized",
    "mutation_authorized",
    "publication_authorized",
    "remote_push_authorized",
    "human_review_removal_authorized",
)


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


def _report() -> dict:
    from hisys.judge.smoke import build_judge_smoke_report

    return build_judge_smoke_report()


def _summary() -> dict:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        summarize_judge_smoke_report,
    )

    return summarize_judge_smoke_report(build_judge_smoke_report())


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


def test_summary_function_importable_and_callable() -> None:
    from hisys.judge import smoke

    assert hasattr(smoke, "summarize_judge_smoke_report")
    assert callable(smoke.summarize_judge_smoke_report)


def test_summary_records_identity_and_mode() -> None:
    summary = _summary()

    assert summary["subsystem"] == "judge"
    assert summary["kind"] == "advisory_smoke_status"
    assert summary["mode"] == "local_fixture_in_process"


def test_summary_has_exact_top_level_key_set() -> None:
    assert set(_summary().keys()) == _EXPECTED_SUMMARY_KEYS


def test_summary_is_compact_and_omits_bundle() -> None:
    summary = _summary()
    full = _report()

    assert "panel_review_bundle" not in summary
    assert "fixtures" not in summary
    assert "checks" not in summary

    summary_text = json.dumps(summary, sort_keys=True)
    full_text = json.dumps(full, sort_keys=True)
    assert len(summary_text) < len(full_text)


def test_summary_reports_passing_smoke() -> None:
    summary = _summary()

    assert summary["smoke_passed"] is True
    assert summary["checks_failed"] == 0
    assert summary["failed_check_names"] == []
    assert summary["fixture_mismatch_labels"] == []
    assert summary["advisory_locks_preserved_for_all_fixtures"] is True


def test_summary_check_counts_are_consistent() -> None:
    summary = _summary()
    report = _report()

    assert summary["checks_total"] == len(report["checks"])
    assert summary["checks_passed"] + summary["checks_failed"] == summary["checks_total"]
    assert summary["checks_passed"] == summary["checks_total"]


def test_summary_fixture_counts_are_consistent() -> None:
    summary = _summary()
    report = _report()

    assert summary["fixture_count"] == report["fixture_count"]
    assert summary["fixtures_matched_expectation"] == summary["fixture_count"]


def test_summary_gate_status_counts_sum_to_fixture_count_and_sorted() -> None:
    summary = _summary()
    counts = summary["gate_status_counts"]

    assert sum(counts.values()) == summary["fixture_count"]
    assert list(counts.keys()) == sorted(counts.keys())
    for status in (
        "advisory_pass",
        "advisory_fail",
        "advisory_block",
        "advisory_needs_human_review",
        "rejected",
    ):
        assert counts[status] == 1


def test_summary_carries_bundle_identity() -> None:
    summary = _summary()
    report = _report()

    assert summary["bundle_fingerprint"] == report["bundle_fingerprint"]
    assert summary["bundle_fingerprint_algorithm"] == "sha256"
    assert (
        summary["bundle_serialized_byte_length"]
        == report["bundle_serialized_byte_length"]
    )


def test_summary_pins_authority_locks() -> None:
    summary = _summary()
    locks = summary["authority_locks"]

    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True
    for name in _ESCALATION_LOCKS:
        assert locks[name] is False


def test_summary_repeats_non_authorization_note() -> None:
    summary = _summary()
    report = _report()

    assert isinstance(summary["non_authorization_note"], str)
    assert summary["non_authorization_note"] == report["non_authorization_note"]


def test_summary_reflects_failed_checks_and_mismatches() -> None:
    from hisys.judge.smoke import summarize_judge_smoke_report

    summary = summarize_judge_smoke_report(_failing_report())

    assert summary["smoke_passed"] is False
    assert summary["checks_total"] == 2
    assert summary["checks_passed"] == 1
    assert summary["checks_failed"] == 1
    assert summary["failed_check_names"] == ["check_two"]
    assert summary["fixtures_matched_expectation"] == 1
    assert summary["fixture_mismatch_labels"] == ["mismatched_case"]
    assert summary["gate_status_counts"] == {"advisory_fail": 1, "advisory_pass": 1}


def test_summary_does_not_mutate_report() -> None:
    from hisys.judge.smoke import summarize_judge_smoke_report

    report = _failing_report()
    before = copy.deepcopy(report)
    summarize_judge_smoke_report(report)
    assert report == before


def test_summary_is_deterministic() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        summarize_judge_smoke_report,
    )

    report = build_judge_smoke_report()
    assert summarize_judge_smoke_report(report) == summarize_judge_smoke_report(report)


def test_summary_is_json_serializable() -> None:
    summary = _summary()

    text = json.dumps(summary, sort_keys=True)
    assert json.loads(text) == summary


def test_summary_cli_returns_zero_and_compact_json() -> None:
    completed = _run_judge_smoke("--summary")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["kind"] == "advisory_smoke_status"
    assert payload["smoke_passed"] is True
    assert "panel_review_bundle" not in payload


def test_summary_cli_matches_projection_of_builder() -> None:
    completed = _run_judge_smoke("--summary")
    assert completed.returncode == 0, completed.stderr

    assert json.loads(completed.stdout) == _summary()


def test_default_cli_still_emits_full_report() -> None:
    completed = _run_judge_smoke()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["kind"] == "advisory_smoke_report"
    assert "panel_review_bundle" in payload
