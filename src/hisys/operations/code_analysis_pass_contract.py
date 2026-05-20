"""M21.8 code-analysis pass-contract evidence adapter and evaluation writer.

This adapter consumes caller-supplied trusted M21.1..M21.7 code-analysis report
payloads and renders an existing
``hisys.contracts.evaluator.EvidenceSummary`` value the existing
``evaluate_pass_contract`` function can score. M21.8 reuses the existing
``PassContractRegistryEntry``, ``EvidenceSummary``, ``PassContractEvaluationResult``,
and ``NeedsMoreEvidenceReason`` types without adding fields or reason codes.

Boundary invariants:

- The adapter only reads caller-supplied dict payloads. It never opens a file
  body, never crawls ``runtime-boundary/`` directly, never calls
  ``subprocess`` or ``.git/``, and never calls ``date.today()``.
- The writer persists JSON/Markdown only under
  ``runtime-boundary/code-analysis-pass-contracts/<YYYYMMDD>/<contract_id>-evaluation.{json,md}``
  through ``resolve_instance_runtime_ref`` and rejects non-``YYYYMMDD`` dates.
- The writer records ``advisory_only=true``, ``requires_human_review=true``,
  ``external_call_made=false``, ``mutation_performed=false``,
  ``raw_source_content_persisted=false``.
- ``boundary_violation_detected`` becomes ``True`` only when the input report
  exposes a non-empty ``unsafe_*`` or ``outside_runtime_boundary_*`` partition.

After M21.8.1.C, four of the five M21.8 PREP question types are supported:
``traceability_coverage_review``, ``runtime_boundary_consistency_review``,
``codebase_map_freshness_review``, and ``change_impact_review``. The remaining
one (``architecture_candidate_review``) raises ``NotImplementedError`` and is
added in a follow-up increment.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from hisys.contracts.evaluator import EvidenceSummary, PassContractEvaluationResult
from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_OUTPUT_PREFIX = "runtime-boundary/code-analysis-pass-contracts"
_EVALUATION_SCHEMA_ID = "hisys.code_analysis_pass_contract.evaluation.v1"

CodeAnalysisQuestionType = Literal[
    "traceability_coverage_review",
    "runtime_boundary_consistency_review",
    "codebase_map_freshness_review",
    "change_impact_review",
    "architecture_candidate_review",
]

_SUPPORTED_QUESTION_TYPES = {
    "traceability_coverage_review",
    "runtime_boundary_consistency_review",
    "codebase_map_freshness_review",
    "change_impact_review",
}
_DEFERRED_QUESTION_TYPES = {
    "architecture_candidate_review",
}


def _coverage_review_summary(coverage_report: dict[str, Any]) -> EvidenceSummary:
    unreferenced = coverage_report.get("unreferenced_requirements") or []
    schema_id = str(coverage_report.get("schema_id", "hisys.traceability.coverage.v1"))
    return EvidenceSummary(
        artifact_refs=[schema_id],
        claims_covered=len(unreferenced) == 0,
        boundary_violation_detected=False,
    )


def _consistency_review_summary(boundary_report: dict[str, Any]) -> EvidenceSummary:
    schema_id = str(
        boundary_report.get("schema_id", "hisys.runtime_boundary.consistency.v1")
    )
    unsafe = list(boundary_report.get("unsafe_refs") or [])
    outside = list(boundary_report.get("outside_runtime_boundary_refs") or [])
    missing = list(boundary_report.get("missing_files") or [])
    malformed = list(boundary_report.get("malformed_json_refs") or [])
    missing_md = list(boundary_report.get("missing_markdown_pair_refs") or [])
    missing_adv = list(boundary_report.get("missing_advisory_flag_refs") or [])
    ok_count = int(boundary_report.get("ok_ref_count", 0))

    boundary_violation = bool(unsafe) or bool(outside)
    has_other_issue = bool(missing) or bool(malformed) or bool(missing_md) or bool(
        missing_adv
    )
    claims_covered = (not boundary_violation) and (not has_other_issue) and ok_count > 0

    artifact_refs: list[str] = []
    if boundary_violation or has_other_issue:
        for ref in (
            *unsafe,
            *outside,
            *missing,
            *malformed,
            *missing_md,
            *missing_adv,
        ):
            if ref not in artifact_refs:
                artifact_refs.append(ref)
    else:
        artifact_refs.append(schema_id)

    return EvidenceSummary(
        artifact_refs=artifact_refs,
        claims_covered=claims_covered,
        boundary_violation_detected=boundary_violation,
    )


def _freshness_review_summary(freshness_report: dict[str, Any]) -> EvidenceSummary:
    schema_id = str(
        freshness_report.get("schema_id", "hisys.codebase_map.freshness.v1")
    )
    fresh = list(freshness_report.get("fresh_partitions") or [])
    stale = list(freshness_report.get("stale_partitions") or [])
    incomplete = list(freshness_report.get("incomplete_partitions") or [])
    unsafe = list(freshness_report.get("unsafe_partitions") or [])

    boundary_violation = bool(unsafe)
    has_other_issue = bool(stale) or bool(incomplete)
    claims_covered = (
        (not boundary_violation) and (not has_other_issue) and bool(fresh)
    )

    artifact_refs: list[str] = []
    if boundary_violation or has_other_issue:
        for ref in (*unsafe, *stale, *incomplete, *fresh):
            if ref not in artifact_refs:
                artifact_refs.append(ref)
    else:
        artifact_refs.append(schema_id)

    return EvidenceSummary(
        artifact_refs=artifact_refs,
        claims_covered=claims_covered,
        boundary_violation_detected=boundary_violation,
    )


def _change_impact_review_summary(
    change_impact_report: dict[str, Any],
    coverage_report: dict[str, Any] | None,
) -> EvidenceSummary:
    unsafe = list(change_impact_report.get("unsafe_changed_refs") or [])
    unmapped = list(change_impact_report.get("unmapped_changed_refs") or [])
    impacted_reqs = list(change_impact_report.get("impacted_requirement_ids") or [])
    impacted_tests = list(change_impact_report.get("impacted_test_id_or_refs") or [])
    impacted_design = list(
        change_impact_report.get("impacted_design_or_interface_refs") or []
    )
    impacted_runtime = list(
        change_impact_report.get("impacted_runtime_boundary_refs") or []
    )

    boundary_violation = bool(unsafe)
    has_impact_signal = bool(
        impacted_reqs or impacted_tests or impacted_design or impacted_runtime
    )
    claims_covered = (
        (not boundary_violation) and (not unmapped) and has_impact_signal
    )

    artifact_refs: list[str] = []
    for ref in (
        *unsafe,
        *impacted_reqs,
        *impacted_tests,
        *impacted_design,
        *impacted_runtime,
        *unmapped,
    ):
        if ref not in artifact_refs:
            artifact_refs.append(ref)

    return EvidenceSummary(
        artifact_refs=artifact_refs,
        claims_covered=claims_covered,
        boundary_violation_detected=boundary_violation,
        contradiction_checked=coverage_report is not None,
    )


def build_code_analysis_evidence_summary(
    *,
    question_type: str,
    coverage_report: dict[str, Any] | None = None,
    boundary_report: dict[str, Any] | None = None,
    freshness_report: dict[str, Any] | None = None,
    benchmark_report: dict[str, Any] | None = None,
    change_impact_report: dict[str, Any] | None = None,
    architecture_candidates_report: dict[str, Any] | None = None,
) -> EvidenceSummary:
    """Render an ``EvidenceSummary`` for the given code-analysis question type."""

    if question_type == "traceability_coverage_review":
        if coverage_report is None:
            raise ValueError(
                "traceability_coverage_review requires coverage_report payload"
            )
        return _coverage_review_summary(coverage_report)
    if question_type == "runtime_boundary_consistency_review":
        if boundary_report is None:
            raise ValueError(
                "runtime_boundary_consistency_review requires boundary_report payload"
            )
        return _consistency_review_summary(boundary_report)
    if question_type == "codebase_map_freshness_review":
        if freshness_report is None:
            raise ValueError(
                "codebase_map_freshness_review requires freshness_report payload"
            )
        return _freshness_review_summary(freshness_report)
    if question_type == "change_impact_review":
        if change_impact_report is None:
            raise ValueError(
                "change_impact_review requires change_impact_report payload"
            )
        return _change_impact_review_summary(
            change_impact_report=change_impact_report,
            coverage_report=coverage_report,
        )
    if question_type in _DEFERRED_QUESTION_TYPES:
        raise NotImplementedError(
            f"{question_type} mapping is deferred to a follow-up M21.8.1 increment"
        )
    raise ValueError(f"unknown code-analysis question type: {question_type}")


def _validate_date(date: str) -> None:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(
            f"invalid code-analysis pass-contract evaluation date: {date!r}"
        )


def _render_markdown(
    *,
    contract_id: str,
    result: PassContractEvaluationResult,
    human_approval_ref: str | None,
) -> str:
    lines = [
        f"# Code-Analysis Pass-Contract Evaluation — {_EVALUATION_SCHEMA_ID}",
        "",
        "## Boundary",
        "",
        "- advisory_only: true",
        "- requires_human_review: true",
        "- external_call_made: false",
        "- mutation_performed: false",
        "- raw_source_content_persisted: false",
        "",
        "## Result",
        "",
        f"- contract_id: `{contract_id}`",
        f"- quality_gate: `{result.quality_gate}`",
        f"- human_approval_ref: {human_approval_ref or 'none'}",
        "",
        "## Blockers",
        "",
    ]
    if not result.blockers:
        lines.append("- none")
    else:
        for blocker in result.blockers:
            lines.append(f"- `{blocker}`")
    lines.append("")
    return "\n".join(lines)


def write_code_analysis_pass_contract_evaluation(
    *,
    instance_root: Path,
    date: str,
    contract_id: str,
    result: PassContractEvaluationResult,
    human_approval_ref: str | None = None,
) -> dict[str, object]:
    """Persist a code-analysis pass-contract evaluation under the instance runtime boundary."""

    _validate_date(date)
    rel_dir = f"{_OUTPUT_PREFIX}/{date}"
    json_ref = f"{rel_dir}/{contract_id}-evaluation.json"
    md_ref = f"{rel_dir}/{contract_id}-evaluation.md"
    json_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=json_ref
    )
    md_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=md_ref
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_id": _EVALUATION_SCHEMA_ID,
        "contract_id": contract_id,
        "quality_gate": result.quality_gate,
        "blockers": list(result.blockers),
        "human_reviewed_use_only": result.human_reviewed_use_only,
        "automatic_promotion_allowed": result.automatic_promotion_allowed,
        "human_approval_ref": human_approval_ref,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
    }
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md_path.write_text(
        _render_markdown(
            contract_id=contract_id,
            result=result,
            human_approval_ref=human_approval_ref,
        ),
        encoding="utf-8",
    )
    return {
        "schema_id": _EVALUATION_SCHEMA_ID,
        "json_ref": json_ref,
        "markdown_ref": md_ref,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
    }
