"""Advisory architecture-candidate generation.

M21.7 keeps this surface pure and fixture-local: callers pass in already-trusted
M21.1 / M21.4 / M21.6 report payloads, and the generator emits bounded
``ArchitectureCandidate`` records labeled only as ``advisory_candidate`` or
``advisory_candidate_low_evidence``. Imperative wording such as
``recommended``, ``required``, ``approved``, ``must``, ``next step``, or
``should`` is intentionally avoided in all candidate ``summary`` / ``rationale``
fields; an explicit unit test pins that invariant. The generator never opens
raw source, never calls ``subprocess``, never reads ``.git/``, never calls
``date.today()``, and never authorizes live action.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_ARCH_CAND_PREFIX = "runtime-boundary/architecture-candidates"
_MAX_COVERAGE_CANDIDATES = 10
_MAX_FRESHNESS_CANDIDATES = 10
_MAX_CROSS_SIGNAL_CANDIDATES = 10

CandidateStrength = Literal["advisory_candidate", "advisory_candidate_low_evidence"]
CandidateKind = Literal[
    "coverage_gap",
    "freshness_drift",
    "change_impact_concentration",
    "cross_signal_alignment",
]


class ArchitectureCandidateInputs(BaseModel):
    """Bounded intake record for the architecture-candidate generator."""

    instance_root: Path
    coverage_report: dict[str, Any] | None = None
    freshness_report: dict[str, Any] | None = None
    change_impact_report: dict[str, Any] | None = None
    current_head_short: str | None = None


class ArchitectureCandidate(BaseModel):
    candidate_id: str
    kind: CandidateKind
    summary: str
    supporting_refs: tuple[str, ...]
    recommendation_strength: CandidateStrength
    rationale: str


class ArchitectureCandidateReport(BaseModel):
    schema_id: str = "hisys.architecture_candidates.v1"
    current_head_short: str | None = None
    candidate_count: int
    candidates: tuple[ArchitectureCandidate, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _sorted_unique_strings(values: Any) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(sorted({str(v) for v in values}))


def _coverage_gap_candidates(payload: dict[str, Any]) -> list[ArchitectureCandidate]:
    unreferenced = _sorted_unique_strings(payload.get("unreferenced_requirements"))
    if not unreferenced:
        return []
    candidates: list[ArchitectureCandidate] = []
    for index, req_id in enumerate(unreferenced[:_MAX_COVERAGE_CANDIDATES], start=1):
        candidates.append(
            ArchitectureCandidate(
                candidate_id=f"cand-coverage-gap-{index:03d}",
                kind="coverage_gap",
                summary=(
                    f"observation: requirement {req_id} appears in M21.1 coverage "
                    "as unreferenced by design/interface/test anchors"
                ),
                supporting_refs=(req_id,),
                recommendation_strength="advisory_candidate_low_evidence",
                rationale=(
                    "M21.1 coverage payload listed this requirement under "
                    "unreferenced_requirements; observation only, no action "
                    "authorized"
                ),
            )
        )
    return candidates


def _freshness_drift_candidates(payload: dict[str, Any]) -> list[ArchitectureCandidate]:
    stale = _sorted_unique_strings(payload.get("stale_partitions"))
    if not stale:
        return []
    candidates: list[ArchitectureCandidate] = []
    for index, partition_ref in enumerate(stale[:_MAX_FRESHNESS_CANDIDATES], start=1):
        candidates.append(
            ArchitectureCandidate(
                candidate_id=f"cand-freshness-drift-{index:03d}",
                kind="freshness_drift",
                summary=(
                    f"observation: codebase-analysis partition {partition_ref} "
                    "appears in M21.4 freshness as stale relative to caller-"
                    "supplied max_age_days"
                ),
                supporting_refs=(partition_ref,),
                recommendation_strength="advisory_candidate_low_evidence",
                rationale=(
                    "M21.4 freshness payload listed this partition under "
                    "stale_partitions; observation only, no repair authorized"
                ),
            )
        )
    return candidates


def _change_impact_concentration_candidate(
    payload: dict[str, Any],
) -> list[ArchitectureCandidate]:
    impacted_reqs = _sorted_unique_strings(payload.get("impacted_requirement_ids"))
    changed_ref_count = payload.get("changed_ref_count")
    if not impacted_reqs:
        return []
    if not isinstance(changed_ref_count, int) or changed_ref_count > 10:
        return []
    supporting_refs = tuple(impacted_reqs) + _sorted_unique_strings(
        payload.get("impacted_design_or_interface_refs")
    )
    return [
        ArchitectureCandidate(
            candidate_id="cand-change-impact-concentration-001",
            kind="change_impact_concentration",
            summary=(
                "observation: a small change set "
                f"(changed_ref_count={changed_ref_count}) intersects "
                f"{len(impacted_reqs)} requirement IDs per M21.6"
            ),
            supporting_refs=supporting_refs,
            recommendation_strength="advisory_candidate",
            rationale=(
                "M21.6 change-impact payload reported impacted_requirement_ids "
                "and a bounded changed_ref_count; observation only, no action "
                "authorized"
            ),
        )
    ]


def _cross_signal_alignment_candidates(
    coverage_payload: dict[str, Any] | None,
    impact_payload: dict[str, Any] | None,
) -> list[ArchitectureCandidate]:
    if not coverage_payload or not impact_payload:
        return []
    unreferenced = set(
        _sorted_unique_strings(coverage_payload.get("unreferenced_requirements"))
    )
    impacted = set(
        _sorted_unique_strings(impact_payload.get("impacted_requirement_ids"))
    )
    overlap = sorted(unreferenced & impacted)
    if not overlap:
        return []
    candidates: list[ArchitectureCandidate] = []
    for index, req_id in enumerate(
        overlap[:_MAX_CROSS_SIGNAL_CANDIDATES], start=1
    ):
        candidates.append(
            ArchitectureCandidate(
                candidate_id=f"cand-cross-signal-alignment-{index:03d}",
                kind="cross_signal_alignment",
                summary=(
                    f"observation: requirement {req_id} appears as unreferenced "
                    "in M21.1 coverage and as impacted in M21.6 change-impact"
                ),
                supporting_refs=(req_id,),
                recommendation_strength="advisory_candidate",
                rationale=(
                    "M21.1 and M21.6 payloads each reference this requirement "
                    "ID under their respective gap/impact partitions; "
                    "observation only, no action authorized"
                ),
            )
        )
    return candidates


def build_architecture_candidate_report(
    *, inputs: ArchitectureCandidateInputs
) -> ArchitectureCandidateReport:
    """Produce a bounded advisory candidate report from trusted payloads."""

    candidates: list[ArchitectureCandidate] = []
    if inputs.coverage_report:
        candidates.extend(_coverage_gap_candidates(inputs.coverage_report))
    if inputs.freshness_report:
        candidates.extend(_freshness_drift_candidates(inputs.freshness_report))
    if inputs.change_impact_report:
        candidates.extend(
            _change_impact_concentration_candidate(inputs.change_impact_report)
        )
    candidates.extend(
        _cross_signal_alignment_candidates(
            inputs.coverage_report, inputs.change_impact_report
        )
    )

    ordered = tuple(sorted(candidates, key=lambda c: c.candidate_id))
    return ArchitectureCandidateReport(
        current_head_short=inputs.current_head_short,
        candidate_count=len(ordered),
        candidates=ordered,
    )


def _validate_date(date: str) -> None:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid architecture-candidates report date: {date!r}")


def render_architecture_candidates_markdown(
    report: ArchitectureCandidateReport,
) -> str:
    """Render a bounded Markdown summary for the candidate report."""

    lines = [
        f"# Architecture Candidates Report — {report.schema_id}",
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
        f"- candidate_count: {report.candidate_count}",
        "",
        "## Candidates",
        "",
    ]
    if not report.candidates:
        lines.append("- none")
    else:
        for candidate in report.candidates:
            lines.append(f"### {candidate.candidate_id}")
            lines.append("")
            lines.append(f"- kind: `{candidate.kind}`")
            lines.append(
                f"- recommendation_strength: `{candidate.recommendation_strength}`"
            )
            lines.append(f"- summary: {candidate.summary}")
            lines.append("- supporting_refs:")
            for ref in candidate.supporting_refs:
                lines.append(f"  - `{ref}`")
            lines.append(f"- rationale: {candidate.rationale}")
            lines.append("")
    return "\n".join(lines)


def write_architecture_candidate_report(
    *,
    instance_root: Path,
    date: str,
    report: ArchitectureCandidateReport,
) -> dict[str, object]:
    """Persist report JSON/Markdown under the instance runtime boundary."""

    _validate_date(date)
    rel_dir = f"{_ARCH_CAND_PREFIX}/{date}"
    json_ref = f"{rel_dir}/architecture-candidates-report.json"
    md_ref = f"{rel_dir}/architecture-candidates-report.md"
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
        render_architecture_candidates_markdown(report), encoding="utf-8"
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
