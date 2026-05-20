"""Advisory runtime-boundary consistency reporting.

M21.3 keeps this surface pure and fixture-local: callers supply a bounded list
of relative runtime-boundary refs, the checker classifies each by safety and
presence, and the optional writer persists only JSON/Markdown summaries under
``runtime-boundary/runtime-boundary-consistency/<YYYYMMDD>/``. The checker
never repairs, deletes, retries, or rewrites the artifacts it inspects, and
never authorizes live action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_RUNTIME_BOUNDARY_ROOT = "runtime-boundary/"
_CONSISTENCY_RUNTIME_PREFIX = "runtime-boundary/runtime-boundary-consistency"
_EXPECTED_ADVISORY_FLAGS = ("advisory_only", "requires_human_review")


class RuntimeBoundaryConsistencyReport(BaseModel):
    """Bounded advisory report shape; contains refs/counts only."""

    schema_id: str = "hisys.runtime_boundary.consistency.v1"
    ok_ref_count: int
    unsafe_refs: tuple[str, ...]
    missing_files: tuple[str, ...]
    malformed_json_refs: tuple[str, ...]
    missing_markdown_pair_refs: tuple[str, ...]
    missing_advisory_flag_refs: tuple[str, ...]
    outside_runtime_boundary_refs: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize(refs: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def build_runtime_boundary_consistency_report(
    *,
    instance_root: Path,
    candidate_refs: Iterable[str],
) -> RuntimeBoundaryConsistencyReport:
    """Classify each ref into the advisory consistency vocabulary."""

    ok: list[str] = []
    unsafe: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    missing_md_pair: list[str] = []
    missing_flags: list[str] = []
    outside_root: list[str] = []

    for ref in candidate_refs:
        if not ref.startswith(_RUNTIME_BOUNDARY_ROOT):
            outside_root.append(ref)
            continue
        try:
            path = resolve_instance_runtime_ref(
                instance_root=instance_root, relative_ref=ref
            )
        except ValueError:
            unsafe.append(ref)
            continue
        if not path.is_file():
            missing.append(ref)
            continue
        if ref.endswith(".json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                malformed.append(ref)
                continue
            if isinstance(data, dict) and any(
                flag not in data for flag in _EXPECTED_ADVISORY_FLAGS
            ):
                missing_flags.append(ref)
                continue
            md_ref = ref[:-5] + ".md"
            try:
                md_path = resolve_instance_runtime_ref(
                    instance_root=instance_root, relative_ref=md_ref
                )
            except ValueError:
                missing_md_pair.append(ref)
                continue
            if not md_path.is_file():
                missing_md_pair.append(ref)
                continue
        ok.append(ref)

    return RuntimeBoundaryConsistencyReport(
        ok_ref_count=len(ok),
        unsafe_refs=_normalize(unsafe),
        missing_files=_normalize(missing),
        malformed_json_refs=_normalize(malformed),
        missing_markdown_pair_refs=_normalize(missing_md_pair),
        missing_advisory_flag_refs=_normalize(missing_flags),
        outside_runtime_boundary_refs=_normalize(outside_root),
    )


def _validate_date(date: str) -> None:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid consistency report date: {date!r}")


def render_runtime_boundary_consistency_markdown(
    report: RuntimeBoundaryConsistencyReport,
) -> str:
    """Render the bounded advisory consistency report as Markdown."""

    def _list_block(title: str, items: tuple[str, ...]) -> list[str]:
        lines = [f"## {title}", ""]
        if not items:
            lines.append("- none")
        else:
            lines.extend(f"- `{item}`" for item in items)
        lines.append("")
        return lines

    lines = [
        f"# Runtime-Boundary Consistency Report — {report.schema_id}",
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
        f"- ok_ref_count: {report.ok_ref_count}",
        f"- unsafe_refs: {len(report.unsafe_refs)}",
        f"- missing_files: {len(report.missing_files)}",
        f"- malformed_json_refs: {len(report.malformed_json_refs)}",
        f"- missing_markdown_pair_refs: {len(report.missing_markdown_pair_refs)}",
        f"- missing_advisory_flag_refs: {len(report.missing_advisory_flag_refs)}",
        f"- outside_runtime_boundary_refs: {len(report.outside_runtime_boundary_refs)}",
        "",
    ]
    lines.extend(_list_block("Unsafe Refs", report.unsafe_refs))
    lines.extend(_list_block("Missing Files", report.missing_files))
    lines.extend(_list_block("Malformed JSON Refs", report.malformed_json_refs))
    lines.extend(
        _list_block("Missing Markdown Pair Refs", report.missing_markdown_pair_refs)
    )
    lines.extend(
        _list_block("Missing Advisory Flag Refs", report.missing_advisory_flag_refs)
    )
    lines.extend(
        _list_block(
            "Outside Runtime-Boundary Refs", report.outside_runtime_boundary_refs
        )
    )
    return "\n".join(lines)


def write_runtime_boundary_consistency_report(
    *,
    instance_root: Path,
    date: str,
    report: RuntimeBoundaryConsistencyReport,
) -> dict[str, object]:
    """Persist the report JSON/Markdown under the instance runtime boundary."""

    _validate_date(date)
    rel_dir = f"{_CONSISTENCY_RUNTIME_PREFIX}/{date}"
    json_ref = f"{rel_dir}/consistency-report.json"
    md_ref = f"{rel_dir}/consistency-report.md"
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
        render_runtime_boundary_consistency_markdown(report), encoding="utf-8"
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
    "RuntimeBoundaryConsistencyReport",
    "build_runtime_boundary_consistency_report",
    "render_runtime_boundary_consistency_markdown",
    "write_runtime_boundary_consistency_report",
]
