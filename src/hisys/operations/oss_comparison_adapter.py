"""Advisory approved-OSS comparison adapter (M23, fixture-local).

The adapter compares one caller-named local codebase evidence line against
caller-supplied approved-OSS source descriptors. All inputs are bounded
fixture/config records; the adapter never crawls ``tests/fixtures/``, opens
upstream OSS repositories, calls Git or ``subprocess``, contacts the network,
installs or imports OSS packages, persists raw OSS source content, or
adjudicates licenses. The output is advisory only and never implies repair,
deletion, retry, approval, compliance, or readiness for live action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_LINE_LABEL_PATTERN = re.compile(r"^[A-Z][A-Z0-9_\-]{1,63}$")
_SOURCE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_\-]{1,63}$")
_NOTES_MAX_LENGTH = 1024
_OSS_PREFIX = "runtime-boundary/oss-comparison"


class ApprovedOssSource(BaseModel):
    """Caller-supplied approved-OSS reference descriptor."""

    source_id: str
    source_name: str = ""
    license_tag: str = "n/a"
    category_refs: tuple[str, ...] = ()
    approved_refs: tuple[str, ...] = ()
    local_fixture_refs: tuple[str, ...] = ()
    notes: str = ""


class LocalCodebaseLine(BaseModel):
    """Caller-supplied local codebase evidence-line descriptor."""

    line_label: str
    category_refs: tuple[str, ...] = ()
    portfolio_refs: tuple[str, ...] = ()
    implemented_surface_count: int = 0
    human_gated_surface_count: int = 0


class OssComparisonRequest(BaseModel):
    """Single intake surface for the OSS comparison adapter."""

    instance_root: Path
    date: str
    local_line: LocalCodebaseLine
    approved_sources: tuple[ApprovedOssSource, ...] = ()
    current_head_short: str | None = None


class OssComparisonReport(BaseModel):
    """Bounded advisory OSS comparison report."""

    schema_id: str = "hisys.oss_comparison_adapter.v1"
    date: str
    current_head_short: str | None = None
    local_line_label: str
    compared_source_ids: tuple[str, ...] = ()
    compared_source_license_tags: tuple[str, ...] = ()
    local_category_refs: tuple[str, ...] = ()
    union_category_refs: tuple[str, ...] = ()
    intersection_category_refs: tuple[str, ...] = ()
    local_only_category_refs: tuple[str, ...] = ()
    oss_only_category_refs: tuple[str, ...] = ()
    unsafe_refs: tuple[str, ...] = ()
    unsafe_source_ids: tuple[str, ...] = ()
    unsafe_line_labels: tuple[str, ...] = ()
    compared_source_count: int = 0
    union_category_count: int = 0
    intersection_category_count: int = 0
    local_only_category_count: int = 0
    oss_only_category_count: int = 0
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    live_external_action_authorized: bool = False
    allowed_actions: str = "advisory_only"


def _normalize(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(v for v in values if v is not None)))


def _is_unsafe_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        return True
    return False


def _is_unsafe_notes(notes: str) -> bool:
    if len(notes) > _NOTES_MAX_LENGTH:
        return True
    return any((ch < " " and ch not in "\t\n") for ch in notes)


def build_oss_comparison_report(
    *, request: OssComparisonRequest
) -> OssComparisonReport:
    if not _DATE_PATTERN.fullmatch(request.date):
        raise ValueError(f"invalid oss comparison date: {request.date!r}")

    unsafe_refs: set[str] = set()
    unsafe_source_ids: list[str] = []
    unsafe_line_labels: list[str] = []
    compared_source_ids: list[str] = []
    license_tags: list[str] = []
    oss_category_refs: set[str] = set()

    local_line = request.local_line
    local_line_label = local_line.line_label
    if _LINE_LABEL_PATTERN.fullmatch(local_line_label):
        local_category_refs: set[str] = set(local_line.category_refs)
        for ref in local_line.portfolio_refs:
            if _is_unsafe_ref(ref):
                unsafe_refs.add(ref)
    else:
        unsafe_line_labels.append(local_line_label)
        local_category_refs = set()

    for source in request.approved_sources:
        if not _SOURCE_ID_PATTERN.fullmatch(source.source_id):
            unsafe_source_ids.append(source.source_id)
            continue
        if _is_unsafe_notes(source.notes):
            unsafe_source_ids.append(source.source_id)
            continue
        safe_categories: list[str] = []
        for ref in source.category_refs:
            if _is_unsafe_ref(ref):
                unsafe_refs.add(ref)
                continue
            safe_categories.append(ref)
        for ref in source.approved_refs:
            if _is_unsafe_ref(ref):
                unsafe_refs.add(ref)
        for ref in source.local_fixture_refs:
            if _is_unsafe_ref(ref):
                unsafe_refs.add(ref)
        compared_source_ids.append(source.source_id)
        license_tags.append(source.license_tag or "n/a")
        oss_category_refs.update(safe_categories)

    union_categories = local_category_refs | oss_category_refs
    intersection_categories = local_category_refs & oss_category_refs
    local_only_categories = local_category_refs - oss_category_refs
    oss_only_categories = oss_category_refs - local_category_refs

    return OssComparisonReport(
        date=request.date,
        current_head_short=request.current_head_short,
        local_line_label=local_line_label,
        compared_source_ids=_normalize(compared_source_ids),
        compared_source_license_tags=_normalize(license_tags),
        local_category_refs=_normalize(local_category_refs),
        union_category_refs=_normalize(union_categories),
        intersection_category_refs=_normalize(intersection_categories),
        local_only_category_refs=_normalize(local_only_categories),
        oss_only_category_refs=_normalize(oss_only_categories),
        unsafe_refs=_normalize(unsafe_refs),
        unsafe_source_ids=_normalize(unsafe_source_ids),
        unsafe_line_labels=_normalize(unsafe_line_labels),
        compared_source_count=len(set(compared_source_ids)),
        union_category_count=len(union_categories),
        intersection_category_count=len(intersection_categories),
        local_only_category_count=len(local_only_categories),
        oss_only_category_count=len(oss_only_categories),
    )


def render_oss_comparison_markdown(report: OssComparisonReport) -> str:
    lines: list[str] = []
    lines.append(f"# OSS Comparison Report — {report.schema_id}")
    lines.append("")
    lines.append(f"- date: {report.date}")
    lines.append(f"- current_head_short: {report.current_head_short or 'n/a'}")
    lines.append(f"- local_line_label: {report.local_line_label}")
    lines.append(
        f"- compared_source_count: {report.compared_source_count}"
    )
    lines.append(
        f"- union_category_count: {report.union_category_count}"
    )
    lines.append(
        f"- intersection_category_count: {report.intersection_category_count}"
    )
    lines.append(
        f"- local_only_category_count: {report.local_only_category_count}"
    )
    lines.append(
        f"- oss_only_category_count: {report.oss_only_category_count}"
    )
    lines.append(f"- advisory_only: {str(report.advisory_only).lower()}")
    lines.append(
        f"- requires_human_review: "
        f"{str(report.requires_human_review).lower()}"
    )
    lines.append(
        f"- external_call_made: {str(report.external_call_made).lower()}"
    )
    lines.append(
        f"- mutation_performed: {str(report.mutation_performed).lower()}"
    )
    lines.append(
        "- raw_source_content_persisted: "
        f"{str(report.raw_source_content_persisted).lower()}"
    )
    lines.append(
        "- live_external_action_authorized: "
        f"{str(report.live_external_action_authorized).lower()}"
    )
    lines.append(f"- allowed_actions: {report.allowed_actions}")
    lines.append("")

    def _section(title: str, values: tuple[str, ...]) -> None:
        lines.append(f"## {title}")
        if not values:
            lines.append("- (none)")
        else:
            for value in values:
                lines.append(f"- {value}")
        lines.append("")

    _section("Compared source IDs", report.compared_source_ids)
    _section("Compared license tags", report.compared_source_license_tags)
    _section("Local category refs", report.local_category_refs)
    _section("Union category refs", report.union_category_refs)
    _section("Intersection category refs", report.intersection_category_refs)
    _section("Local-only category refs", report.local_only_category_refs)
    _section("OSS-only category refs", report.oss_only_category_refs)
    _section("Unsafe refs", report.unsafe_refs)
    _section("Unsafe source IDs", report.unsafe_source_ids)
    _section("Unsafe line labels", report.unsafe_line_labels)
    return "\n".join(lines) + "\n"


def write_oss_comparison_report(
    *,
    instance_root: Path,
    date: str,
    report: OssComparisonReport,
) -> dict[str, object]:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid oss comparison report date: {date!r}")
    rel_dir = f"{_OSS_PREFIX}/{date}"
    json_ref = f"{rel_dir}/comparison-report.json"
    md_ref = f"{rel_dir}/comparison-report.md"
    json_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=json_ref
    )
    md_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=md_ref
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        render_oss_comparison_markdown(report), encoding="utf-8"
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
        "live_external_action_authorized": False,
        "allowed_actions": "advisory_only",
    }


__all__ = [
    "ApprovedOssSource",
    "LocalCodebaseLine",
    "OssComparisonRequest",
    "OssComparisonReport",
    "build_oss_comparison_report",
    "render_oss_comparison_markdown",
    "write_oss_comparison_report",
]
