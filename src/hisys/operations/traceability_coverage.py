"""Deterministic advisory traceability coverage reporting.

M21.1 keeps this surface pure and fixture-local: callers provide bounded anchor
sets, the reporter computes sorted IDs/counts, and the optional writer persists
only JSON/Markdown summaries under ``runtime-boundary/traceability-coverage``.
No source bodies, credentials, network calls, publication, or action authority
are involved.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_TRACEABILITY_RUNTIME_PREFIX = "runtime-boundary/traceability-coverage"
_REQUIREMENT_ID_PATTERN = re.compile(r"HISYS-[A-Z]+-[A-Z0-9]+(?:-\d+)?")
_TEST_ID_PATTERN = re.compile(r"STD-[A-Z0-9_-]+")


class TraceabilityAnchors(BaseModel):
    """Bounded traceability anchor universe for coverage computation."""

    requirement_ids: tuple[str, ...]
    design_requirement_refs: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    interface_requirement_refs: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    test_requirement_refs: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    test_ids: tuple[str, ...] = ()
    test_requirement_links: dict[str, tuple[str, ...]] = Field(default_factory=dict)


class TraceabilityCoverageReport(BaseModel):
    """Small advisory report; contains IDs/counts only, not raw source text."""

    schema_id: str = "hisys.traceability.coverage.v1"
    requirement_count: int
    covered_requirement_count: int
    coverage_ratio: float
    unreferenced_requirements: tuple[str, ...]
    orphan_test_ids: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize_ids(ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(ids)))


def _referenced_requirements(anchors: TraceabilityAnchors) -> set[str]:
    referenced: set[str] = set()
    for mapping in (
        anchors.design_requirement_refs,
        anchors.interface_requirement_refs,
        anchors.test_requirement_refs,
    ):
        for req_id, refs in mapping.items():
            if refs:
                referenced.add(req_id)
    return referenced


def _ids_from_file(path: Path, pattern: re.Pattern[str]) -> tuple[str, ...]:
    """Return sorted unique IDs matched in one bounded local text file."""

    if not path.is_file():
        return ()
    text = path.read_text(encoding="utf-8")
    return tuple(sorted(dict.fromkeys(pattern.findall(text))))


def load_repo_traceability_anchors(repo_root: Path) -> TraceabilityAnchors:
    """Load deterministic traceability anchors from local repo files.

    The loader records only IDs and relative file refs. It does not persist raw
    source content, resolve credentials, or perform external calls.
    """

    root = repo_root.resolve()
    schema_refs: dict[str, list[str]] = {}
    schemas_dir = root / "src" / "hisys" / "schemas"
    for path in sorted(schemas_dir.glob("*.py")):
        if path.name in {"__init__.py", "base.py"}:
            continue
        for req_id in _ids_from_file(path, _REQUIREMENT_ID_PATTERN):
            schema_refs.setdefault(req_id, []).append(path.relative_to(root).as_posix())

    traceability_doc = root / "docs" / "traceability" / "README.md"
    design_refs = {
        req_id: (traceability_doc.relative_to(root).as_posix(),)
        for req_id in _ids_from_file(traceability_doc, _REQUIREMENT_ID_PATTERN)
    }
    requirement_ids = tuple(sorted(set(schema_refs) | set(design_refs)))

    trace_test = root / "tests" / "integration" / "test_trace_path.py"
    test_req_ids = _ids_from_file(trace_test, _REQUIREMENT_ID_PATTERN)
    test_ids = _ids_from_file(trace_test, _TEST_ID_PATTERN) or ("tests/integration/test_trace_path.py",)
    test_requirement_links = {test_id: test_req_ids for test_id in test_ids}

    return TraceabilityAnchors(
        requirement_ids=requirement_ids,
        design_requirement_refs=design_refs,
        interface_requirement_refs={req_id: tuple(paths) for req_id, paths in schema_refs.items()},
        test_requirement_refs={req_id: (trace_test.relative_to(root).as_posix(),) for req_id in test_req_ids},
        test_ids=test_ids,
        test_requirement_links=test_requirement_links,
    )


def build_traceability_coverage_report(
    anchors: TraceabilityAnchors,
) -> TraceabilityCoverageReport:
    """Build a deterministic advisory coverage report from bounded anchor IDs."""

    requirement_ids = _normalize_ids(anchors.requirement_ids)
    referenced = _referenced_requirements(anchors)
    covered = tuple(req_id for req_id in requirement_ids if req_id in referenced)
    unreferenced = tuple(req_id for req_id in requirement_ids if req_id not in referenced)
    orphan_tests = tuple(
        test_id
        for test_id in _normalize_ids(anchors.test_ids)
        if not anchors.test_requirement_links.get(test_id)
    )
    coverage_ratio = round(len(covered) / len(requirement_ids), 4) if requirement_ids else 1.0

    return TraceabilityCoverageReport(
        requirement_count=len(requirement_ids),
        covered_requirement_count=len(covered),
        coverage_ratio=coverage_ratio,
        unreferenced_requirements=unreferenced,
        orphan_test_ids=orphan_tests,
    )


def _validate_date(date: str) -> None:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid traceability coverage date: {date!r}")


def render_traceability_coverage_markdown(report: TraceabilityCoverageReport) -> str:
    lines = [
        f"# Traceability Coverage Report — {report.schema_id}",
        "",
        "## Boundary",
        "",
        "- advisory_only: true",
        "- requires_human_review: true",
        "- external_call_made: false",
        "- mutation_performed: false",
        "- raw_source_content_persisted: false",
        "",
        "## Coverage",
        "",
        f"- requirement_count: {report.requirement_count}",
        f"- covered_requirement_count: {report.covered_requirement_count}",
        f"- coverage_ratio: {report.coverage_ratio}",
        "",
        "## Unreferenced Requirements",
        "",
    ]
    lines.extend(f"- `{req_id}`" for req_id in report.unreferenced_requirements)
    if not report.unreferenced_requirements:
        lines.append("- none")
    lines.extend(["", "## Orphan Tests", ""])
    lines.extend(f"- `{test_id}`" for test_id in report.orphan_test_ids)
    if not report.orphan_test_ids:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_traceability_coverage_report(
    *, instance_root: Path, date: str, report: TraceabilityCoverageReport
) -> dict[str, object]:
    """Persist report JSON/Markdown under the instance runtime boundary."""

    _validate_date(date)
    rel_dir = f"{_TRACEABILITY_RUNTIME_PREFIX}/{date}"
    json_ref = f"{rel_dir}/coverage-report.json"
    md_ref = f"{rel_dir}/coverage-report.md"
    json_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=json_ref
    )
    md_path = resolve_instance_runtime_ref(instance_root=instance_root, relative_ref=md_ref)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_traceability_coverage_markdown(report), encoding="utf-8")
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
