"""Advisory codebase evidence portfolio reporting.

M22 keeps this surface pure and local-only: callers supply bounded evidence
line references (M21, DARS_PANEL_LOCAL_COMPLETION, or caller-named lines), and
the builder aggregates artifact refs, schema ids, quality-gate refs, and
bounded counts. The optional writer persists only JSON/Markdown summaries
under ``runtime-boundary/codebase-evidence-portfolio``. The builder never
opens artifact bodies, crawls ``runtime-boundary/``, calls Git or
``subprocess``, contacts the network, executes subagents, or authorizes live
action.
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
_PORTFOLIO_PREFIX = "runtime-boundary/codebase-evidence-portfolio"


class EvidenceLineRef(BaseModel):
    """One caller-supplied local evidence-line reference."""

    line_label: str
    artifact_refs: tuple[str, ...] = ()
    schema_ids: tuple[str, ...] = ()
    quality_gate_refs: tuple[str, ...] = ()
    implemented_surface_count: int = 0
    human_gated_surface_count: int = 0


class CodebaseEvidencePortfolioRequest(BaseModel):
    """Caller-supplied portfolio inputs; no implicit clock or git read."""

    instance_root: Path
    date: str
    line_refs: tuple[EvidenceLineRef, ...] = ()
    current_head_short: str | None = None


class CodebaseEvidencePortfolioReport(BaseModel):
    """Bounded advisory portfolio aggregating local evidence-line refs."""

    schema_id: str = "hisys.codebase_evidence_portfolio.v1"
    date: str
    current_head_short: str | None = None
    source_lines: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    schema_ids: tuple[str, ...] = ()
    quality_gate_refs: tuple[str, ...] = ()
    implemented_surface_count: int = 0
    human_gated_surface_count: int = 0
    unsafe_refs: tuple[str, ...] = ()
    unsafe_line_labels: tuple[str, ...] = ()
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    allowed_actions: str = "advisory_only"


def _normalize(refs: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def _is_unsafe_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        return True
    return False


def build_codebase_evidence_portfolio_report(
    *, request: CodebaseEvidencePortfolioRequest
) -> CodebaseEvidencePortfolioReport:
    """Aggregate caller-supplied evidence-line refs into the portfolio report."""

    if not _DATE_PATTERN.fullmatch(request.date):
        raise ValueError(f"invalid portfolio date: {request.date!r}")

    valid_labels: list[str] = []
    unsafe_labels: list[str] = []
    artifact_refs: set[str] = set()
    schema_ids: set[str] = set()
    quality_gate_refs: set[str] = set()
    unsafe_refs: set[str] = set()
    implemented_total = 0
    human_gated_total = 0

    for line in request.line_refs:
        if not _LINE_LABEL_PATTERN.fullmatch(line.line_label):
            unsafe_labels.append(line.line_label)
            continue
        valid_labels.append(line.line_label)
        for ref in line.artifact_refs:
            if _is_unsafe_ref(ref):
                unsafe_refs.add(ref)
            else:
                artifact_refs.add(ref)
        for ref in line.quality_gate_refs:
            if _is_unsafe_ref(ref):
                unsafe_refs.add(ref)
            else:
                quality_gate_refs.add(ref)
        for sid in line.schema_ids:
            if sid:
                schema_ids.add(sid)
        implemented_total += int(line.implemented_surface_count)
        human_gated_total += int(line.human_gated_surface_count)

    return CodebaseEvidencePortfolioReport(
        date=request.date,
        current_head_short=request.current_head_short,
        source_lines=_normalize(valid_labels),
        artifact_refs=_normalize(artifact_refs),
        schema_ids=_normalize(schema_ids),
        quality_gate_refs=_normalize(quality_gate_refs),
        implemented_surface_count=implemented_total,
        human_gated_surface_count=human_gated_total,
        unsafe_refs=_normalize(unsafe_refs),
        unsafe_line_labels=_normalize(unsafe_labels),
    )


def render_codebase_evidence_portfolio_markdown(
    report: CodebaseEvidencePortfolioReport,
) -> str:
    """Render bounded Markdown for the portfolio report (refs + counts only)."""

    head = report.current_head_short or "n/a"
    lines: list[str] = [
        "# Codebase Evidence Portfolio (advisory)",
        "",
        f"- schema_id: {report.schema_id}",
        f"- date: {report.date}",
        f"- current_head_short: {head}",
        f"- implemented_surface_count: {report.implemented_surface_count}",
        f"- human_gated_surface_count: {report.human_gated_surface_count}",
        f"- advisory_only: {str(report.advisory_only).lower()}",
        f"- requires_human_review: {str(report.requires_human_review).lower()}",
        f"- external_call_made: {str(report.external_call_made).lower()}",
        f"- mutation_performed: {str(report.mutation_performed).lower()}",
        (
            "- raw_source_content_persisted: "
            f"{str(report.raw_source_content_persisted).lower()}"
        ),
        f"- allowed_actions: {report.allowed_actions}",
        "",
        "## Source lines",
        "",
    ]
    if report.source_lines:
        lines.extend(f"- {label}" for label in report.source_lines)
    else:
        lines.append("- (none)")
    lines.extend(["", "## Schema IDs", ""])
    if report.schema_ids:
        lines.extend(f"- `{sid}`" for sid in report.schema_ids)
    else:
        lines.append("- (none)")
    lines.extend(["", "## Artifact refs", ""])
    if report.artifact_refs:
        lines.extend(f"- `{ref}`" for ref in report.artifact_refs)
    else:
        lines.append("- (none)")
    lines.extend(["", "## Quality gate refs", ""])
    if report.quality_gate_refs:
        lines.extend(f"- `{ref}`" for ref in report.quality_gate_refs)
    else:
        lines.append("- (none)")
    lines.extend(["", "## Unsafe refs (rejected)", ""])
    if report.unsafe_refs:
        lines.extend(f"- `{ref}`" for ref in report.unsafe_refs)
    else:
        lines.append("- (none)")
    lines.extend(["", "## Unsafe line labels (rejected)", ""])
    if report.unsafe_line_labels:
        lines.extend(f"- `{label}`" for label in report.unsafe_line_labels)
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def write_codebase_evidence_portfolio_report(
    *,
    instance_root: Path,
    date: str,
    report: CodebaseEvidencePortfolioReport,
) -> dict[str, object]:
    """Persist the portfolio JSON + Markdown under the bounded runtime partition."""

    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid portfolio report date: {date!r}")
    rel_dir = f"{_PORTFOLIO_PREFIX}/{date}"
    json_ref = f"{rel_dir}/portfolio-report.json"
    md_ref = f"{rel_dir}/portfolio-report.md"
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
        render_codebase_evidence_portfolio_markdown(report), encoding="utf-8"
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
        "allowed_actions": "advisory_only",
    }


__all__ = [
    "EvidenceLineRef",
    "CodebaseEvidencePortfolioRequest",
    "CodebaseEvidencePortfolioReport",
    "build_codebase_evidence_portfolio_report",
    "render_codebase_evidence_portfolio_markdown",
    "write_codebase_evidence_portfolio_report",
]
