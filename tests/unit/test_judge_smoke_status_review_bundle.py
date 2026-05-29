"""Judge subsystem-local advisory smoke status review bundle tests.

These tests pin ``build_judge_smoke_status_review_bundle``: a Judge-only,
deterministic, read-only bundling of the compact smoke status summary produced
by ``summarize_judge_smoke_report`` and its short human/agent-readable status
text produced by ``render_judge_smoke_status_text`` into one JSON-serializable
smoke status review bundle, so local tooling gets both the machine view and the
human view of Judge smoke readiness in a single artifact. This mirrors the
gate-result ``build_judge_advisory_panel_review_bundle`` lineage.

The builder is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It grants no execution authority -- the bundle stays
advisory-only and always requires human review, matching the Judge authority
boundary in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.

The CLI status-bundle mode is::

    PYTHONPATH=src:. python3 -m hisys.judge.smoke --status-bundle
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


def _bundle() -> dict:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        build_judge_smoke_status_review_bundle,
    )

    return build_judge_smoke_status_review_bundle(build_judge_smoke_report())


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


def test_builder_importable_and_callable() -> None:
    from hisys.judge import smoke

    assert hasattr(smoke, "build_judge_smoke_status_review_bundle")
    assert callable(smoke.build_judge_smoke_status_review_bundle)


def test_returns_a_mapping() -> None:
    assert isinstance(_bundle(), dict)


def test_has_stable_top_level_keys() -> None:
    assert set(_bundle()) == {
        "subsystem",
        "kind",
        "smoke_passed",
        "summary",
        "status_text",
        "authority_locks",
        "non_authorization_note",
    }


def test_subsystem_and_kind() -> None:
    bundle = _bundle()

    assert bundle["subsystem"] == "judge"
    assert bundle["kind"] == "advisory_smoke_status_review_bundle"


def test_summary_matches_summarizer() -> None:
    bundle = _bundle()

    assert bundle["summary"] == _summary()
    assert bundle["summary"]["kind"] == "advisory_smoke_status"


def test_status_text_matches_renderer_over_same_summary() -> None:
    from hisys.judge.smoke import render_judge_smoke_status_text

    bundle = _bundle()

    assert bundle["status_text"] == render_judge_smoke_status_text(bundle["summary"])


def test_status_text_is_a_string() -> None:
    assert isinstance(_bundle()["status_text"], str)


def test_smoke_passed_mirrors_summary() -> None:
    bundle = _bundle()

    assert bundle["smoke_passed"] is True
    assert bundle["smoke_passed"] == bundle["summary"]["smoke_passed"]


def test_authority_locks_pinned_with_no_escalation_keys() -> None:
    locks = _bundle()["authority_locks"]

    assert locks == {"advisory_only": True, "requires_human_review": True}


def test_includes_non_authorization_note() -> None:
    from hisys.judge import JUDGE_GATE_NON_AUTHORIZATION_NOTE

    bundle = _bundle()

    assert bundle["non_authorization_note"] == JUDGE_GATE_NON_AUTHORIZATION_NOTE


def test_accepts_summary_or_report_equivalently() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        build_judge_smoke_status_review_bundle,
        summarize_judge_smoke_report,
    )

    report = build_judge_smoke_report()
    summary = summarize_judge_smoke_report(report)

    assert build_judge_smoke_status_review_bundle(
        report
    ) == build_judge_smoke_status_review_bundle(summary)


def test_is_json_serializable() -> None:
    bundle = _bundle()
    reloaded = json.loads(json.dumps(bundle))

    assert reloaded == bundle


def test_is_deterministic() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        build_judge_smoke_status_review_bundle,
    )

    report = build_judge_smoke_report()

    assert build_judge_smoke_status_review_bundle(
        report
    ) == build_judge_smoke_status_review_bundle(report)


def test_does_not_mutate_input() -> None:
    from hisys.judge.smoke import build_judge_smoke_status_review_bundle

    report = _failing_report()
    before = copy.deepcopy(report)
    build_judge_smoke_status_review_bundle(report)
    assert report == before


def test_does_not_mutate_summary_input() -> None:
    from hisys.judge.smoke import build_judge_smoke_status_review_bundle

    summary = _summary()
    before = copy.deepcopy(summary)
    build_judge_smoke_status_review_bundle(summary)
    assert summary == before


def test_returns_fresh_independent_mapping() -> None:
    from hisys.judge.smoke import (
        build_judge_smoke_report,
        build_judge_smoke_status_review_bundle,
    )

    report = build_judge_smoke_report()
    first = build_judge_smoke_status_review_bundle(report)
    second = build_judge_smoke_status_review_bundle(report)

    assert first is not second
    assert first["summary"] is not second["summary"]
    assert first["authority_locks"] is not second["authority_locks"]


def test_summary_independent_of_input_summary() -> None:
    from hisys.judge.smoke import build_judge_smoke_status_review_bundle

    summary = _summary()
    bundle = build_judge_smoke_status_review_bundle(summary)

    assert bundle["summary"] == summary
    assert bundle["summary"] is not summary


def test_no_escalation_authority_keys_in_top_level_locks() -> None:
    locks = _bundle()["authority_locks"]

    for forbidden in (
        "live_external_action_authorized",
        "mutation_authorized",
        "publication_authorized",
        "human_review_removal_authorized",
        "remote_push_authorized",
    ):
        assert forbidden not in locks


def test_failing_report_surfaces_in_bundle() -> None:
    from hisys.judge.smoke import build_judge_smoke_status_review_bundle

    bundle = build_judge_smoke_status_review_bundle(_failing_report())

    assert bundle["smoke_passed"] is False
    assert bundle["summary"]["smoke_passed"] is False
    assert bundle["summary"]["failed_check_names"] == ["check_two"]
    assert bundle["summary"]["fixture_mismatch_labels"] == ["mismatched_case"]
    assert "Judge Advisory Smoke Status: FAIL" in bundle["status_text"]
    assert "Failed checks: check_two" in bundle["status_text"]
    assert "Fixture mismatches: mismatched_case" in bundle["status_text"]


def test_status_bundle_cli_returns_zero_and_emits_bundle_json() -> None:
    completed = _run_judge_smoke("--status-bundle")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["kind"] == "advisory_smoke_status_review_bundle"
    assert payload["smoke_passed"] is True


def test_status_bundle_cli_matches_builder() -> None:
    completed = _run_judge_smoke("--status-bundle")
    assert completed.returncode == 0, completed.stderr

    assert json.loads(completed.stdout) == _bundle()


def test_default_summary_text_cli_still_work() -> None:
    default = _run_judge_smoke()
    assert default.returncode == 0, default.stderr
    assert json.loads(default.stdout)["kind"] == "advisory_smoke_report"

    summary = _run_judge_smoke("--summary")
    assert summary.returncode == 0, summary.stderr
    assert json.loads(summary.stdout)["kind"] == "advisory_smoke_status"

    text = _run_judge_smoke("--text")
    assert text.returncode == 0, text.stderr
    assert text.stdout.startswith("Judge Advisory Smoke Status: PASS")


def test_status_bundle_mutually_exclusive_with_text_and_summary() -> None:
    with_text = _run_judge_smoke("--status-bundle", "--text")
    assert with_text.returncode != 0
    assert "not allowed with" in with_text.stderr or "mutually exclusive" in (
        with_text.stderr.lower()
    )

    with_summary = _run_judge_smoke("--status-bundle", "--summary")
    assert with_summary.returncode != 0
    assert "not allowed with" in with_summary.stderr or "mutually exclusive" in (
        with_summary.stderr.lower()
    )
