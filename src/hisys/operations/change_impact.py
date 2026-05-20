"""Advisory change-impact reporting.

M21.6 keeps this surface pure and local-only: callers supply a bounded list of
changed file refs and an existing M21.1 :class:`TraceabilityAnchors` value, and
the analyzer maps each changed ref to impacted requirement IDs, test IDs/refs,
design/interface refs, or runtime-boundary refs. The optional writer persists
only JSON/Markdown summaries under
``runtime-boundary/change-impact/<YYYYMMDD>/``. The analyzer never repairs,
deletes, retries, fetches remotely, shells out to ``git``, calls
``date.today()``, or otherwise authorizes live action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref
from hisys.operations.traceability_coverage import TraceabilityAnchors

_DATE_PATTERN = re.compile(r"^\d{8}$")
_RUNTIME_BOUNDARY_ROOT = "runtime-boundary/"
_CHANGE_IMPACT_PREFIX = "runtime-boundary/change-impact"


class ChangeImpactRequest(BaseModel):
    """Bounded intake record for the change-impact analyzer."""

    instance_root: Path
    repo_root: Path
    changed_file_refs: tuple[str, ...]
    current_head_short: str | None = None


class ChangeImpactReport(BaseModel):
    """Small advisory report; contains IDs/refs/counts only, not raw source."""

    schema_id: str = "hisys.change_impact.v1"
    current_head_short: str | None = None
    changed_ref_count: int
    impacted_requirement_ids: tuple[str, ...]
    impacted_test_id_or_refs: tuple[str, ...]
    impacted_design_or_interface_refs: tuple[str, ...]
    impacted_runtime_boundary_refs: tuple[str, ...]
    unmapped_changed_refs: tuple[str, ...]
    unsafe_changed_refs: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize(refs: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def _is_unsafe_changed_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.split("/")
    return any(part == ".." for part in parts)


def _design_ref_to_requirements(
    anchors: TraceabilityAnchors,
) -> dict[str, tuple[str, ...]]:
    index: dict[str, set[str]] = {}
    for req_id, refs in anchors.design_requirement_refs.items():
        for ref in refs:
            index.setdefault(ref, set()).add(req_id)
    for req_id, refs in anchors.interface_requirement_refs.items():
        for ref in refs:
            index.setdefault(ref, set()).add(req_id)
    return {ref: tuple(sorted(req_ids)) for ref, req_ids in index.items()}


def _test_ref_to_requirements(
    anchors: TraceabilityAnchors,
) -> dict[str, tuple[str, ...]]:
    index: dict[str, set[str]] = {}
    for req_id, refs in anchors.test_requirement_refs.items():
        for ref in refs:
            index.setdefault(ref, set()).add(req_id)
    for test_id in anchors.test_ids:
        for req_id in anchors.test_requirement_links.get(test_id, ()):
            index.setdefault(test_id, set()).add(req_id)
    return {ref: tuple(sorted(req_ids)) for ref, req_ids in index.items()}


def build_change_impact_report(
    *,
    request: ChangeImpactRequest,
    anchors: TraceabilityAnchors,
) -> ChangeImpactReport:
    """Classify each changed ref into the advisory impact vocabulary."""

    design_index = _design_ref_to_requirements(anchors)
    test_index = _test_ref_to_requirements(anchors)

    impacted_reqs: set[str] = set()
    impacted_tests: set[str] = set()
    impacted_design: set[str] = set()
    impacted_runtime: set[str] = set()
    unmapped: list[str] = []
    unsafe: list[str] = []

    for ref in request.changed_file_refs:
        if _is_unsafe_changed_ref(ref):
            unsafe.append(ref)
            continue
        mapped = False
        if ref in design_index:
            mapped = True
            impacted_design.add(ref)
            impacted_reqs.update(design_index[ref])
        if ref in test_index:
            mapped = True
            impacted_tests.add(ref)
            impacted_reqs.update(test_index[ref])
        if ref.startswith(_RUNTIME_BOUNDARY_ROOT):
            mapped = True
            impacted_runtime.add(ref)
        if not mapped:
            unmapped.append(ref)

    return ChangeImpactReport(
        current_head_short=request.current_head_short,
        changed_ref_count=len(request.changed_file_refs),
        impacted_requirement_ids=_normalize(impacted_reqs),
        impacted_test_id_or_refs=_normalize(impacted_tests),
        impacted_design_or_interface_refs=_normalize(impacted_design),
        impacted_runtime_boundary_refs=_normalize(impacted_runtime),
        unmapped_changed_refs=_normalize(unmapped),
        unsafe_changed_refs=_normalize(unsafe),
    )


def _validate_date(date: str) -> None:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid change-impact report date: {date!r}")


def render_change_impact_markdown(report: ChangeImpactReport) -> str:
    """Render a bounded Markdown summary for the change-impact report."""

    lines = [
        f"# Change-Impact Report — {report.schema_id}",
        "",
        "## Boundary",
        "",
        "- advisory_only: true",
        "- requires_human_review: true",
        "- external_call_made: false",
        "- mutation_performed: false",
        "- raw_source_content_persisted: false",
        "",
        "## Context",
        "",
        f"- current_head_short: {report.current_head_short or 'none'}",
        f"- changed_ref_count: {report.changed_ref_count}",
        "",
        "## Impacted Requirements",
        "",
    ]
    if report.impacted_requirement_ids:
        lines.extend(f"- `{req_id}`" for req_id in report.impacted_requirement_ids)
    else:
        lines.append("- none")

    lines.extend(["", "## Impacted Tests", ""])
    if report.impacted_test_id_or_refs:
        lines.extend(f"- `{ref}`" for ref in report.impacted_test_id_or_refs)
    else:
        lines.append("- none")

    lines.extend(["", "## Impacted Design or Interface Refs", ""])
    if report.impacted_design_or_interface_refs:
        lines.extend(
            f"- `{ref}`" for ref in report.impacted_design_or_interface_refs
        )
    else:
        lines.append("- none")

    lines.extend(["", "## Impacted Runtime-Boundary Refs", ""])
    if report.impacted_runtime_boundary_refs:
        lines.extend(f"- `{ref}`" for ref in report.impacted_runtime_boundary_refs)
    else:
        lines.append("- none")

    lines.extend(["", "## Unmapped Changed Refs", ""])
    if report.unmapped_changed_refs:
        lines.extend(f"- `{ref}`" for ref in report.unmapped_changed_refs)
    else:
        lines.append("- none")

    lines.extend(["", "## Unsafe Changed Refs", ""])
    if report.unsafe_changed_refs:
        lines.extend(f"- `{ref}`" for ref in report.unsafe_changed_refs)
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def write_change_impact_report(
    *, instance_root: Path, date: str, report: ChangeImpactReport
) -> dict[str, object]:
    """Persist report JSON/Markdown under the instance runtime boundary."""

    _validate_date(date)
    rel_dir = f"{_CHANGE_IMPACT_PREFIX}/{date}"
    json_ref = f"{rel_dir}/impact-report.json"
    md_ref = f"{rel_dir}/impact-report.md"
    json_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=json_ref
    )
    md_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=md_ref
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_change_impact_markdown(report), encoding="utf-8")
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
