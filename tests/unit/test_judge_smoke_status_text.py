"""Judge subsystem-local advisory smoke status-text rendering tests.

These tests pin ``render_judge_smoke_status_text``: a Judge-only, deterministic,
read-only renderer that turns either the full smoke report produced by
``build_judge_smoke_report`` or the compact summary produced by
``summarize_judge_smoke_report`` into a short, human/agent-readable status text
so an operator sees Judge smoke readiness at a glance (pass/fail, fixture/check
counts, any failed checks or fixture mismatches, the bundle fingerprint
identity) without parsing the full report or its embedded panel review bundle.

The renderer must be deterministic and side-effect free: it performs no live
provider/model call, no raw provider API call, no network request, no credential
lookup, no vault/evidence mutation, no remote push, and no publication. It
preserves the Judge authority locks recorded in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md`` by repeating that the result is
advisory only and that human review is required.

The CLI text mode is::

    PYTHONPATH=src:. python3 -m hisys.judge.smoke --text
"""

from __future__ import annotations

import copy
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


def _report() -> dict:
    from hisys.judge.smoke import build_judge_smoke_report

    return build_judge_smoke_report()


def _summary() -> dict:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        summarize_judge_smoke_report,
    )

    return summarize_judge_smoke_report(build_judge_smoke_report())


def _text() -> str:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        render_judge_smoke_status_text,
    )

    return render_judge_smoke_status_text(build_judge_smoke_report())


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


def test_renderer_importable_and_callable() -> None:
    from hisys.judge import smoke

    assert hasattr(smoke, "render_judge_smoke_status_text")
    assert callable(smoke.render_judge_smoke_status_text)


def test_renderer_returns_plain_string() -> None:
    text = _text()

    assert isinstance(text, str)
    assert text
    assert "\n" in text  # short multi-line status block


def test_renderer_reports_pass_for_passing_smoke() -> None:
    text = _text()

    assert "Judge Advisory Smoke Status: PASS" in text


def test_renderer_includes_fixture_and_check_counts() -> None:
    text = _text()
    report = _report()

    assert (
        f"Fixtures matched expectation: {report['fixture_count']}/"
        f"{report['fixture_count']}" in text
    )
    assert f"Checks passed: {len(report['checks'])}/{len(report['checks'])}" in text


def test_renderer_includes_gate_status_counts() -> None:
    text = _text()

    assert "Gate status counts:" in text
    for status in (
        "advisory_pass",
        "advisory_fail",
        "advisory_block",
        "advisory_needs_human_review",
        "rejected",
    ):
        assert f"{status}=1" in text


def test_renderer_includes_fingerprint_algorithm_and_digest() -> None:
    text = _text()
    report = _report()

    assert (
        f"Bundle fingerprint ({report['bundle_fingerprint_algorithm']}): "
        f"{report['bundle_fingerprint']}" in text
    )


def test_renderer_states_advisory_only_and_human_review() -> None:
    text = _text()

    assert "Advisory only: yes" in text
    assert "Requires human review: yes" in text


def test_renderer_repeats_non_authorization_note() -> None:
    from hisys.judge.gate_result import JUDGE_GATE_NON_AUTHORIZATION_NOTE

    text = _text()

    assert f"Note: {JUDGE_GATE_NON_AUTHORIZATION_NOTE}" in text


def test_renderer_omits_failure_lines_when_passing() -> None:
    text = _text()

    assert "Failed checks:" not in text
    assert "Fixture mismatches:" not in text


def test_renderer_surfaces_failed_checks_and_mismatches() -> None:
    from hisys.judge.smoke import render_judge_smoke_status_text

    text = render_judge_smoke_status_text(_failing_report())

    assert "Judge Advisory Smoke Status: FAIL" in text
    assert "Fixtures matched expectation: 1/2" in text
    assert "Checks passed: 1/2" in text
    assert "Failed checks: check_two" in text
    assert "Fixture mismatches: mismatched_case" in text
    assert "Bundle fingerprint (sha256): deadbeef" in text


def test_renderer_accepts_summary_or_report_equivalently() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        render_judge_smoke_status_text,
        summarize_judge_smoke_report,
    )

    report = build_judge_smoke_report()
    summary = summarize_judge_smoke_report(report)

    assert render_judge_smoke_status_text(report) == render_judge_smoke_status_text(
        summary
    )


def test_renderer_does_not_mutate_input() -> None:
    from hisys.judge.smoke import render_judge_smoke_status_text

    report = _failing_report()
    before = copy.deepcopy(report)
    render_judge_smoke_status_text(report)
    assert report == before


def test_renderer_is_deterministic() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        render_judge_smoke_status_text,
    )

    report = build_judge_smoke_report()
    assert render_judge_smoke_status_text(report) == render_judge_smoke_status_text(
        report
    )


def test_text_cli_returns_zero_and_emits_text_not_json() -> None:
    completed = _run_judge_smoke("--text")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.startswith("Judge Advisory Smoke Status: PASS")
    # The text mode must not emit JSON.
    try:
        json.loads(completed.stdout)
    except json.JSONDecodeError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("--text must not emit JSON")


def test_text_cli_matches_renderer_of_builder() -> None:
    completed = _run_judge_smoke("--text")
    assert completed.returncode == 0, completed.stderr

    assert completed.stdout == _text() + "\n"


def test_default_and_summary_cli_still_emit_json() -> None:
    default = _run_judge_smoke()
    assert default.returncode == 0, default.stderr
    assert json.loads(default.stdout)["kind"] == "advisory_smoke_report"

    summary = _run_judge_smoke("--summary")
    assert summary.returncode == 0, summary.stderr
    assert json.loads(summary.stdout)["kind"] == "advisory_smoke_status"


def test_text_and_summary_are_mutually_exclusive() -> None:
    completed = _run_judge_smoke("--text", "--summary")

    assert completed.returncode != 0
    assert "not allowed with" in completed.stderr or "mutually exclusive" in (
        completed.stderr.lower()
    )
