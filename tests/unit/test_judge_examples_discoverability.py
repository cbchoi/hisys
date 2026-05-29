"""Discoverability tests for committed Judge example artifacts.

The Judge example directory is an agent/human entry point for local fixture smoke
evidence. This test pins the small README/index contract so future agents can
find the full smoke report, compact status review bundle, producer commands, and
authority boundary without reading implementation code first.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "docs" / "examples" / "judge"
README = EXAMPLES / "README.md"
SMOKE_REPORT = EXAMPLES / "judge-advisory-smoke-report.json"
STATUS_BUNDLE = EXAMPLES / "judge-advisory-smoke-status-review-bundle.json"


def test_judge_examples_readme_indexes_committed_artifacts() -> None:
    assert README.exists(), "missing Judge example artifact README/index"
    text = README.read_text(encoding="utf-8")

    assert "# Judge example artifacts" in text
    assert "judge-advisory-smoke-report.json" in text
    assert "judge-advisory-smoke-status-review-bundle.json" in text
    assert "Full local fixture smoke report" in text
    assert "Compact discoverability artifact" in text


def test_judge_examples_readme_records_producer_commands() -> None:
    text = README.read_text(encoding="utf-8")

    for mode in (
        "--format json",
        "--summary",
        "--text",
        "--status-bundle",
        "--status-bundle-canonical",
        "--status-bundle-fingerprint",
    ):
        assert f"PYTHONPATH=src:. python3 -m hisys.judge.smoke {mode}" in text


def test_judge_examples_readme_preserves_authority_boundary() -> None:
    text = README.read_text(encoding="utf-8").lower()

    for phrase in (
        "local fixture evidence only",
        "advisory-only",
        "requires-human-review",
        "does not authorize execution",
        "no live provider",
        "no escalation-authority keys",
    ):
        assert phrase in text


def test_judge_examples_index_matches_existing_artifact_files() -> None:
    text = README.read_text(encoding="utf-8")

    assert SMOKE_REPORT.exists()
    assert STATUS_BUNDLE.exists()
    assert SMOKE_REPORT.name in text
    assert STATUS_BUNDLE.name in text
