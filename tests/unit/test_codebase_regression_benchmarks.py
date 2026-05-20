"""Focused tests for M21.5 codebase regression benchmark fixtures.

The benchmark surface is local-only and advisory-only. It records fixture refs,
expected outcomes, observed outcomes, and report artifacts without cloning live
repositories, reading credentials, or persisting raw source content.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.operations.codebase_regression_benchmarks import (
    BenchmarkFixture,
    build_codebase_regression_benchmark_report,
    load_codebase_regression_benchmark_manifest,
    write_codebase_regression_benchmark_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "codebase_repos"


def test_codebase_regression_benchmarks_report_expected_outcomes(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixtures" / "codebase_repos"
    (fixture_root / "single_python_module" / "src").mkdir(parents=True)
    (fixture_root / "single_python_module" / "tests").mkdir(parents=True)
    (fixture_root / "single_python_module" / "src" / "example.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    (fixture_root / "single_python_module" / "tests" / "test_example.py").write_text(
        "from example import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    (fixture_root / "missing_test_anchor" / "src").mkdir(parents=True)
    (fixture_root / "missing_test_anchor" / "src" / "untested.py").write_text(
        "def untested():\n    return 'needs-test'\n", encoding="utf-8"
    )
    (fixture_root / "malformed_runtime_ref_case").mkdir(parents=True)

    fixtures = (
        BenchmarkFixture(
            fixture_id="single-python-module",
            fixture_ref="single_python_module",
            expected_outcome="pass",
            observed_outcome="pass",
            rationale="module and test anchor exist",
        ),
        BenchmarkFixture(
            fixture_id="missing-test-anchor",
            fixture_ref="missing_test_anchor",
            expected_outcome="warning",
            observed_outcome="warning",
            rationale="source exists without test anchor",
        ),
        BenchmarkFixture(
            fixture_id="malformed-runtime-ref-case",
            fixture_ref="malformed_runtime_ref_case",
            expected_outcome="expected_issue",
            observed_outcome="expected_issue",
            rationale="fixture documents unsafe runtime ref expectations",
        ),
    )

    report = build_codebase_regression_benchmark_report(
        fixtures=fixtures, fixture_root=fixture_root
    )

    assert report.schema_id == "hisys.codebase_regression.benchmark.v1"
    assert report.total_fixture_count == 3
    assert report.pass_count == 1
    assert report.warning_count == 1
    assert report.expected_issue_count == 1
    assert report.mismatch_count == 0
    assert report.passed_fixture_ids == ("single-python-module",)
    assert report.warning_fixture_ids == ("missing-test-anchor",)
    assert report.expected_issue_fixture_ids == ("malformed-runtime-ref-case",)
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert all(not ref.startswith("/") for ref in report.fixture_refs)
    assert all(".." not in Path(ref).parts for ref in report.fixture_refs)
    assert "def add" not in report.model_dump_json()

    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    refs = write_codebase_regression_benchmark_report(
        instance_root=instance_root, date="20260520", report=report
    )

    expected_json = (
        "runtime-boundary/codebase-regression-benchmarks/20260520/benchmark-report.json"
    )
    expected_md = (
        "runtime-boundary/codebase-regression-benchmarks/20260520/benchmark-report.md"
    )
    assert refs["json_ref"] == expected_json
    assert refs["markdown_ref"] == expected_md
    assert refs["external_call_made"] is False
    assert refs["mutation_performed"] is False
    assert refs["raw_source_content_persisted"] is False
    data = json.loads((instance_root / expected_json).read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.codebase_regression.benchmark.v1"
    assert data["pass_count"] == 1
    assert data["warning_count"] == 1
    assert data["expected_issue_count"] == 1
    markdown = (instance_root / expected_md).read_text(encoding="utf-8")
    assert "external_call_made: false" in markdown
    assert "raw_source_content_persisted: false" in markdown


def test_codebase_regression_benchmark_manifest_paths_are_bounded() -> None:
    manifest = load_codebase_regression_benchmark_manifest(
        FIXTURE_ROOT / "benchmark_manifest.json", fixture_root=FIXTURE_ROOT
    )
    report = build_codebase_regression_benchmark_report(
        fixtures=manifest.fixtures, fixture_root=FIXTURE_ROOT
    )

    assert manifest.schema_id == "hisys.codebase_regression.benchmark_manifest.v1"
    assert len(manifest.fixtures) == 5
    assert report.total_fixture_count == 5
    assert set(report.fixture_ids) == {
        "empty-repo",
        "single-python-module",
        "docs-code-mix",
        "missing-test-anchor",
        "malformed-runtime-ref-case",
    }
    assert report.pass_count == 2
    assert report.warning_count == 2
    assert report.expected_issue_count == 1
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
