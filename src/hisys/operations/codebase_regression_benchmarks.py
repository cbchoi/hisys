"""Local-only advisory regression benchmark fixture reports for M21.5.

This module records expected/observed outcomes for tiny synthetic fixture
repositories. It does not clone repositories, call network services, resolve
credentials, run analyzers, or persist raw source content. Callers supply the
fixture records explicitly or through a bounded local manifest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

Outcome = Literal["pass", "warning", "expected_issue"]
_DATE_PATTERN = re.compile(r"^\d{8}$")
_BENCHMARK_RUNTIME_PREFIX = "runtime-boundary/codebase-regression-benchmarks"


class BenchmarkFixture(BaseModel):
    """One bounded local fixture benchmark expectation."""

    fixture_id: str
    fixture_ref: str
    expected_outcome: Outcome
    observed_outcome: Outcome | None = None
    rationale: str = ""
    consumer_refs: tuple[str, ...] = ()


class BenchmarkFixtureManifest(BaseModel):
    """Manifest of local fixture repositories for codebase-analysis benchmarks."""

    schema_id: str = "hisys.codebase_regression.benchmark_manifest.v1"
    fixtures: tuple[BenchmarkFixture, ...]


class CodebaseRegressionBenchmarkReport(BaseModel):
    """Bounded advisory benchmark report; refs/counts only."""

    schema_id: str = "hisys.codebase_regression.benchmark.v1"
    total_fixture_count: int
    fixture_ids: tuple[str, ...]
    fixture_refs: tuple[str, ...]
    passed_fixture_ids: tuple[str, ...]
    warning_fixture_ids: tuple[str, ...]
    expected_issue_fixture_ids: tuple[str, ...]
    mismatch_fixture_ids: tuple[str, ...]
    pass_count: int
    warning_count: int
    expected_issue_count: int
    mismatch_count: int
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize(items: list[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(items)))


def _fixture_display_ref(*, fixture_root: Path, fixture_ref: str) -> str:
    if not fixture_ref:
        raise ValueError("fixture_ref must be a non-empty relative path")
    candidate = Path(fixture_ref.replace("\\", "/"))
    if candidate.is_absolute() or any(part in {"", ".."} for part in candidate.parts):
        raise ValueError(f"unsafe fixture_ref: {fixture_ref!r}")
    root_real = fixture_root.resolve()
    fixture_path = (fixture_root / candidate).resolve()
    try:
        fixture_path.relative_to(root_real)
    except ValueError as exc:
        raise ValueError(f"fixture_ref escapes fixture_root: {fixture_ref!r}") from exc
    if not fixture_path.exists():
        raise ValueError(f"fixture_ref does not exist: {fixture_ref!r}")
    return candidate.as_posix()


def build_codebase_regression_benchmark_report(
    *, fixtures: tuple[BenchmarkFixture, ...] | list[BenchmarkFixture], fixture_root: Path
) -> CodebaseRegressionBenchmarkReport:
    """Build a deterministic local advisory benchmark report from fixtures."""

    ids: list[str] = []
    refs: list[str] = []
    passed: list[str] = []
    warnings: list[str] = []
    expected_issues: list[str] = []
    mismatches: list[str] = []

    for fixture in fixtures:
        ids.append(fixture.fixture_id)
        refs.append(
            _fixture_display_ref(fixture_root=fixture_root, fixture_ref=fixture.fixture_ref)
        )
        observed = fixture.observed_outcome or fixture.expected_outcome
        if observed != fixture.expected_outcome:
            mismatches.append(fixture.fixture_id)
            continue
        if fixture.expected_outcome == "pass":
            passed.append(fixture.fixture_id)
        elif fixture.expected_outcome == "warning":
            warnings.append(fixture.fixture_id)
        elif fixture.expected_outcome == "expected_issue":
            expected_issues.append(fixture.fixture_id)

    return CodebaseRegressionBenchmarkReport(
        total_fixture_count=len(fixtures),
        fixture_ids=_normalize(ids),
        fixture_refs=_normalize(refs),
        passed_fixture_ids=_normalize(passed),
        warning_fixture_ids=_normalize(warnings),
        expected_issue_fixture_ids=_normalize(expected_issues),
        mismatch_fixture_ids=_normalize(mismatches),
        pass_count=len(passed),
        warning_count=len(warnings),
        expected_issue_count=len(expected_issues),
        mismatch_count=len(mismatches),
    )


def load_codebase_regression_benchmark_manifest(
    manifest_path: Path, *, fixture_root: Path
) -> BenchmarkFixtureManifest:
    """Load a bounded local benchmark manifest and validate fixture refs."""

    manifest_real = manifest_path.resolve()
    root_real = fixture_root.resolve()
    try:
        manifest_real.relative_to(root_real)
    except ValueError as exc:
        raise ValueError("benchmark manifest must be inside fixture_root") from exc
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = BenchmarkFixtureManifest.model_validate(data)
    for fixture in manifest.fixtures:
        _fixture_display_ref(fixture_root=fixture_root, fixture_ref=fixture.fixture_ref)
    return manifest


def render_codebase_regression_benchmark_markdown(
    report: CodebaseRegressionBenchmarkReport,
) -> str:
    """Render the bounded benchmark report as Markdown."""

    def _section(title: str, items: tuple[str, ...]) -> list[str]:
        lines = [f"## {title}", ""]
        if items:
            lines.extend(f"- `{item}`" for item in items)
        else:
            lines.append("- none")
        lines.append("")
        return lines

    lines = [
        f"# Codebase Regression Benchmark Report — {report.schema_id}",
        "",
        "## Boundary",
        "",
        "- advisory_only: true",
        "- requires_human_review: true",
        "- external_call_made: false",
        "- mutation_performed: false",
        "- raw_source_content_persisted: false",
        "",
        "## Counts",
        "",
        f"- total_fixture_count: {report.total_fixture_count}",
        f"- pass_count: {report.pass_count}",
        f"- warning_count: {report.warning_count}",
        f"- expected_issue_count: {report.expected_issue_count}",
        f"- mismatch_count: {report.mismatch_count}",
        "",
    ]
    lines.extend(_section("Passed Fixtures", report.passed_fixture_ids))
    lines.extend(_section("Warning Fixtures", report.warning_fixture_ids))
    lines.extend(_section("Expected Issue Fixtures", report.expected_issue_fixture_ids))
    lines.extend(_section("Mismatched Fixtures", report.mismatch_fixture_ids))
    lines.extend(_section("Fixture Refs", report.fixture_refs))
    return "\n".join(lines)


def write_codebase_regression_benchmark_report(
    *, instance_root: Path, date: str, report: CodebaseRegressionBenchmarkReport
) -> dict[str, object]:
    """Persist benchmark JSON/Markdown under the instance runtime boundary."""

    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid benchmark report date: {date!r}")
    rel_dir = f"{_BENCHMARK_RUNTIME_PREFIX}/{date}"
    json_ref = f"{rel_dir}/benchmark-report.json"
    md_ref = f"{rel_dir}/benchmark-report.md"
    json_path = resolve_instance_runtime_ref(instance_root=instance_root, relative_ref=json_ref)
    md_path = resolve_instance_runtime_ref(instance_root=instance_root, relative_ref=md_ref)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        render_codebase_regression_benchmark_markdown(report), encoding="utf-8"
    )
    return {
        "schema_id": report.schema_id,
        "json_ref": json_ref,
        "markdown_ref": md_ref,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
    }


__all__ = [
    "BenchmarkFixture",
    "BenchmarkFixtureManifest",
    "CodebaseRegressionBenchmarkReport",
    "build_codebase_regression_benchmark_report",
    "load_codebase_regression_benchmark_manifest",
    "render_codebase_regression_benchmark_markdown",
    "write_codebase_regression_benchmark_report",
]
