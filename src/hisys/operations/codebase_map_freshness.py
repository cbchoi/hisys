"""Advisory codebase map freshness/drift reporting.

M21.4 keeps this surface pure and fixture-local: callers pass an instance
root, a current date, and a max-age threshold; the checker classifies each
existing ``runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/``
partition as ``fresh``, ``stale``, ``incomplete``, or ``unsafe_partition``
by reading directory listings and file presence only; and the writer
persists JSON/Markdown summaries under
``runtime-boundary/codebase-map-freshness``. The checker never reads
artifact bodies, never repairs or regenerates partitions, never calls the
system clock or ``.git`` metadata, and never authorizes live action.
"""

from __future__ import annotations

import json
import re
from datetime import date as _date
from pathlib import Path

from pydantic import BaseModel

from hisys.operations.codebase_analysis import (
    INVENTORY_RUNTIME_PREFIX,
    resolve_instance_runtime_ref,
)

_DATE_PATTERN = re.compile(r"^\d{8}$")
_REQUIRED_FILES: tuple[str, ...] = (
    "inventory.json",
    "symbol-index.json",
    "scope-map.json",
    "risk-scan.json",
)
_FRESHNESS_RUNTIME_PREFIX = "runtime-boundary/codebase-map-freshness"


class CodebaseMapFreshnessReport(BaseModel):
    """Bounded advisory freshness report; partition refs/counts only."""

    schema_id: str = "hisys.codebase_map.freshness.v1"
    current_date: str
    max_age_days: int
    current_head_short: str | None = None
    fresh_partitions: tuple[str, ...]
    stale_partitions: tuple[str, ...]
    incomplete_partitions: tuple[str, ...]
    unsafe_partitions: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize(refs: list[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def _partition_age_days(yyyymmdd: str, current_date: _date) -> int:
    year = int(yyyymmdd[:4])
    month = int(yyyymmdd[4:6])
    day = int(yyyymmdd[6:8])
    return (current_date - _date(year, month, day)).days


def build_codebase_map_freshness_report(
    *,
    instance_root: Path,
    current_date: _date,
    max_age_days: int,
    current_head_short: str | None = None,
) -> CodebaseMapFreshnessReport:
    """Classify codebase-analysis partitions by freshness and completeness."""

    fresh: list[str] = []
    stale: list[str] = []
    incomplete: list[str] = []
    unsafe: list[str] = []

    root_dir = instance_root / INVENTORY_RUNTIME_PREFIX
    if not root_dir.is_dir():
        return CodebaseMapFreshnessReport(
            current_date=current_date.isoformat(),
            max_age_days=max_age_days,
            current_head_short=current_head_short,
            fresh_partitions=(),
            stale_partitions=(),
            incomplete_partitions=(),
            unsafe_partitions=(),
        )

    for date_dir in sorted(p for p in root_dir.iterdir() if p.is_dir()):
        date_name = date_dir.name
        for request_dir in sorted(p for p in date_dir.iterdir() if p.is_dir()):
            partition_rel = (
                f"{INVENTORY_RUNTIME_PREFIX}/{date_name}/{request_dir.name}"
            )
            try:
                resolved = resolve_instance_runtime_ref(
                    instance_root=instance_root, relative_ref=partition_rel
                )
            except ValueError:
                unsafe.append(partition_rel)
                continue
            if not _DATE_PATTERN.fullmatch(date_name):
                unsafe.append(partition_rel)
                continue
            present = {p.name for p in resolved.iterdir() if p.is_file()}
            if any(req not in present for req in _REQUIRED_FILES):
                incomplete.append(partition_rel)
                continue
            if _partition_age_days(date_name, current_date) > max_age_days:
                stale.append(partition_rel)
            else:
                fresh.append(partition_rel)

    return CodebaseMapFreshnessReport(
        current_date=current_date.isoformat(),
        max_age_days=max_age_days,
        current_head_short=current_head_short,
        fresh_partitions=_normalize(fresh),
        stale_partitions=_normalize(stale),
        incomplete_partitions=_normalize(incomplete),
        unsafe_partitions=_normalize(unsafe),
    )


def render_codebase_map_freshness_markdown(
    report: CodebaseMapFreshnessReport,
) -> str:
    """Render the bounded advisory freshness report as Markdown."""

    def _list_block(title: str, items: tuple[str, ...]) -> list[str]:
        lines = [f"## {title}", ""]
        if not items:
            lines.append("- none")
        else:
            lines.extend(f"- `{item}`" for item in items)
        lines.append("")
        return lines

    head = report.current_head_short if report.current_head_short else "n/a"
    lines = [
        f"# Codebase Map Freshness Report — {report.schema_id}",
        "",
        "## Boundary",
        "",
        "- advisory_only: true",
        "- requires_human_review: true",
        "- external_call_made: false",
        "- mutation_performed: false",
        "- raw_source_content_persisted: false",
        "",
        "## Inputs",
        "",
        f"- current_date: {report.current_date}",
        f"- max_age_days: {report.max_age_days}",
        f"- current_head_short: {head}",
        "",
        "## Counts",
        "",
        f"- fresh_partitions: {len(report.fresh_partitions)}",
        f"- stale_partitions: {len(report.stale_partitions)}",
        f"- incomplete_partitions: {len(report.incomplete_partitions)}",
        f"- unsafe_partitions: {len(report.unsafe_partitions)}",
        "",
    ]
    lines.extend(_list_block("Fresh Partitions", report.fresh_partitions))
    lines.extend(_list_block("Stale Partitions", report.stale_partitions))
    lines.extend(_list_block("Incomplete Partitions", report.incomplete_partitions))
    lines.extend(_list_block("Unsafe Partitions", report.unsafe_partitions))
    return "\n".join(lines)


def write_codebase_map_freshness_report(
    *,
    instance_root: Path,
    date: str,
    report: CodebaseMapFreshnessReport,
) -> dict[str, object]:
    """Persist the report JSON/Markdown under the instance runtime boundary."""

    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid freshness report date: {date!r}")
    rel_dir = f"{_FRESHNESS_RUNTIME_PREFIX}/{date}"
    json_ref = f"{rel_dir}/freshness-report.json"
    md_ref = f"{rel_dir}/freshness-report.md"
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
    md_path.write_text(
        render_codebase_map_freshness_markdown(report), encoding="utf-8"
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
    "CodebaseMapFreshnessReport",
    "build_codebase_map_freshness_report",
    "render_codebase_map_freshness_markdown",
    "write_codebase_map_freshness_report",
]
