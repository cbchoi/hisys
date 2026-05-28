"""Judge subsystem-local advisory smoke harness tests.

These tests pin the Judge-only, in-process, fixture-driven smoke harness that
drives the full bounded advisory pipeline end to end:

    validate decision packet
      -> render advisory gate result
      -> project gate-result packet
      -> build advisory panel report / review bundle
      -> serialize canonical JSON
      -> fingerprint the bundle

The harness must be deterministic and side-effect free: it performs no live
provider/model call, no raw provider API call, no network request, no
credential lookup, no vault/evidence mutation, no remote push, and no
publication. It exercises only built-in fixtures in process and preserves the
Judge authority locks recorded in ``src/hisys/judge/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.

The smoke command is::

    PYTHONPATH=src:. python3 -m hisys.judge.smoke

It emits a deterministic JSON smoke report to stdout and exits ``0`` when the
smoke passed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
JUDGE_RALPH = ROOT / "src" / "hisys" / "judge" / "ralph.md"
SMOKE_EVIDENCE = ROOT / "docs" / "examples" / "judge" / "judge-advisory-smoke-report.json"

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


def test_smoke_module_importable_and_exposes_builder() -> None:
    from hisys.judge import smoke

    assert hasattr(smoke, "build_judge_smoke_report")
    assert callable(smoke.build_judge_smoke_report)


def test_smoke_module_exposes_builtin_fixtures() -> None:
    from hisys.judge import smoke

    assert isinstance(smoke.JUDGE_SMOKE_FIXTURES, tuple)
    assert len(smoke.JUDGE_SMOKE_FIXTURES) > 0
    assert callable(smoke.main)


def test_smoke_report_records_identity_and_local_mode() -> None:
    report = _report()

    assert report["subsystem"] == "judge"
    assert report["kind"] == "advisory_smoke_report"
    assert report["mode"] == "local_fixture_in_process"
    assert report["fixture_count"] == len(report["fixtures"])
    assert report["fixture_count"] > 0


def test_smoke_report_passes() -> None:
    report = _report()

    assert report["smoke_passed"] is True
    assert all(check["passed"] is True for check in report["checks"])


def test_smoke_report_pins_authority_locks() -> None:
    locks = _report()["authority_locks"]

    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True
    for name in _ESCALATION_LOCKS:
        assert locks[name] is False


def test_smoke_report_records_no_side_effects() -> None:
    side_effects = _report()["side_effects"]

    assert side_effects["performed_live_provider_call"] is False
    assert side_effects["performed_credential_lookup"] is False
    assert side_effects["performed_network_call"] is False
    assert side_effects["performed_remote_push"] is False
    assert side_effects["performed_vault_mutation"] is False
    assert side_effects["performed_evidence_mutation"] is False
    assert side_effects["performed_cross_subsystem_call"] is False


def test_smoke_fixtures_cover_verdict_range_and_rejected_path() -> None:
    report = _report()
    statuses = {fixture["gate_status"] for fixture in report["fixtures"]}

    assert "advisory_pass" in statuses
    assert "advisory_fail" in statuses
    assert "advisory_block" in statuses
    assert "advisory_needs_human_review" in statuses
    assert "rejected" in statuses


def test_smoke_each_fixture_outcome_matches_expectation() -> None:
    for fixture in _report()["fixtures"]:
        assert fixture["outcome_matches_expectation"] is True
        assert fixture["gate_status"] == fixture["expected_gate_status"]
        assert fixture["rendered"] == fixture["expected_rendered"]


def test_smoke_every_fixture_preserves_advisory_locks() -> None:
    for fixture in _report()["fixtures"]:
        assert fixture["advisory_only_locked"] is True
        assert fixture["requires_human_review_locked"] is True
        assert fixture["no_escalation_authority"] is True


def test_smoke_bundle_packet_count_matches_fixture_count() -> None:
    report = _report()
    bundle = report["panel_review_bundle"]

    assert bundle["kind"] == "advisory_gate_result_panel_review_bundle"
    assert bundle["packet_count"] == report["fixture_count"]
    assert isinstance(bundle["report_text"], str)
    assert "Judge Advisory Panel Report" in bundle["report_text"]


def test_smoke_bundle_fingerprint_is_stable_hex_digest() -> None:
    report = _report()

    assert report["bundle_fingerprint_algorithm"] == "sha256"
    digest = report["bundle_fingerprint"]
    assert isinstance(digest, str)
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(ch in "0123456789abcdef" for ch in digest)


def test_smoke_bundle_serialization_round_trips() -> None:
    report = _report()
    bundle = report["panel_review_bundle"]

    serialized = json.dumps(bundle, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert report["bundle_serialized_byte_length"] == len(serialized.encode("utf-8"))
    assert json.loads(serialized) == bundle


def test_smoke_report_is_deterministic() -> None:
    from hisys.judge.smoke import build_judge_smoke_report

    assert build_judge_smoke_report() == build_judge_smoke_report()


def test_smoke_report_is_json_serializable() -> None:
    report = _report()

    text = json.dumps(report, sort_keys=True)
    assert json.loads(text) == report


def test_smoke_command_returns_zero_and_valid_json() -> None:
    completed = _run_judge_smoke()

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["subsystem"] == "judge"
    assert payload["kind"] == "advisory_smoke_report"
    assert payload["smoke_passed"] is True


def test_smoke_command_matches_builder_output() -> None:
    completed = _run_judge_smoke("--format", "json")
    assert completed.returncode == 0, completed.stderr

    assert json.loads(completed.stdout) == _report()


def test_smoke_command_does_not_mutate_controller_file() -> None:
    before = JUDGE_RALPH.read_text(encoding="utf-8")
    completed = _run_judge_smoke()
    assert completed.returncode == 0, completed.stderr
    after = JUDGE_RALPH.read_text(encoding="utf-8")
    assert before == after


def test_smoke_evidence_artifact_matches_builder_output() -> None:
    assert SMOKE_EVIDENCE.exists(), f"missing committed smoke evidence: {SMOKE_EVIDENCE}"
    recorded = json.loads(SMOKE_EVIDENCE.read_text(encoding="utf-8"))

    assert recorded == _report()
