"""RED/GREEN tests for the codebase source-inspection decision packet (M19.1).

The decision packet is the fifth increment of
`SPEC-HISYS-CODEBASE-ANALYSIS-001`. It is a pure reviewer that consumes
already-loaded codebase-analysis artifacts (inventory, Python symbol index,
scope map + validation plan, and risk-boundary scan) and decides whether
the four-file bundle is complete enough for human review.

Allowed decision values per ralph.md Milestone M19 are exactly
``complete_for_human_review`` and ``blocked_needs_more_evidence``. The
reviewer must explicitly reject ``approved``, ``safe_to_deploy``, and
``ready_for_live_action`` decision values; those are not safety boundaries
this packet may cross.

M19.1 covers the missing-artifact case: the reviewer takes None for any
required artifact and returns ``blocked_needs_more_evidence`` with the
missing categories enumerated. M19.2..M19.5 will add full-bundle review,
safe-ref resolution, the CLI + Markdown writer, and docs/traceability.
"""

from __future__ import annotations

import typing
from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

from hisys.operations.codebase_analysis import (
    CodebaseInventory,
    CodebaseRiskScan,
    CodebaseScopeMap,
    CodebaseSourceInspectionDecision,
    CodebaseValidationPlan,
    PythonSymbolIndex,
    review_codebase_source_inspection,
)


# Minimal helper builders used across the missing-artifact tests. Each
# returns a record with the correct schema id and the safety invariants
# the reviewer is contractually required to honor.
def _inventory() -> CodebaseInventory:
    return CodebaseInventory(repo_root="/tmp/fixture")


def _symbol_index() -> PythonSymbolIndex:
    return PythonSymbolIndex(repo_root="/tmp/fixture")


def _scope_map() -> CodebaseScopeMap:
    return CodebaseScopeMap(
        repo_root="/tmp/fixture",
        inventory_schema_id="hisys.codebase.inventory",
        symbol_index_schema_id="hisys.codebase.symbol_index",
    )


def _validation_plan() -> CodebaseValidationPlan:
    return CodebaseValidationPlan()


def _risk_scan() -> CodebaseRiskScan:
    return CodebaseRiskScan(repo_root="/tmp/fixture")


def test_decision_record_is_pydantic_with_safety_invariants():
    decision = CodebaseSourceInspectionDecision(
        decision="blocked_needs_more_evidence",
        missing_evidence=["inventory"],
    )

    assert isinstance(decision, BaseModel)
    assert decision.schema_id == "hisys.codebase.source_inspection_decision"
    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == ["inventory"]
    assert decision.validation_findings == []
    assert decision.unresolved_blockers == []
    assert decision.raw_source_content_persisted is False
    assert decision.action_authorized is False
    assert decision.external_call_made is False
    assert decision.mutation_performed is False
    assert decision.publication_or_live_action_approved is False


@pytest.mark.parametrize(
    "rejected_value",
    ["approved", "safe_to_deploy", "ready_for_live_action"],
)
def test_decision_record_rejects_unsafe_decision_values(rejected_value):
    with pytest.raises(ValidationError):
        CodebaseSourceInspectionDecision(decision=rejected_value)


def test_decision_record_decision_field_only_allows_two_values():
    field = CodebaseSourceInspectionDecision.model_fields["decision"]
    allowed = set(get_args(field.annotation))
    assert allowed == {
        "complete_for_human_review",
        "blocked_needs_more_evidence",
    }


def test_review_returns_blocked_when_all_artifacts_missing():
    decision = review_codebase_source_inspection(
        inventory=None,
        symbol_index=None,
        scope_map=None,
        validation_plan=None,
        risk_scan=None,
    )

    assert isinstance(decision, CodebaseSourceInspectionDecision)
    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == sorted(
        [
            "inventory",
            "symbol_index",
            "scope_map",
            "validation_plan",
            "risk_scan",
        ]
    )
    assert decision.action_authorized is False
    assert decision.raw_source_content_persisted is False


def test_review_returns_blocked_when_inventory_missing():
    decision = review_codebase_source_inspection(
        inventory=None,
        symbol_index=_symbol_index(),
        scope_map=_scope_map(),
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == ["inventory"]


def test_review_returns_blocked_when_symbol_index_missing():
    decision = review_codebase_source_inspection(
        inventory=_inventory(),
        symbol_index=None,
        scope_map=_scope_map(),
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == ["symbol_index"]


def test_review_returns_blocked_when_scope_map_missing():
    decision = review_codebase_source_inspection(
        inventory=_inventory(),
        symbol_index=_symbol_index(),
        scope_map=None,
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == ["scope_map"]


def test_review_returns_blocked_when_validation_plan_missing():
    decision = review_codebase_source_inspection(
        inventory=_inventory(),
        symbol_index=_symbol_index(),
        scope_map=_scope_map(),
        validation_plan=None,
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == ["validation_plan"]


def test_review_returns_blocked_when_risk_scan_missing():
    decision = review_codebase_source_inspection(
        inventory=_inventory(),
        symbol_index=_symbol_index(),
        scope_map=_scope_map(),
        validation_plan=_validation_plan(),
        risk_scan=None,
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == ["risk_scan"]


def test_review_records_unresolved_blockers_as_blocking():
    decision = review_codebase_source_inspection(
        inventory=_inventory(),
        symbol_index=_symbol_index(),
        scope_map=_scope_map(),
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
        unresolved_blockers=["secret-scan: hit_count>0 in fixture run"],
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.unresolved_blockers == [
        "secret-scan: hit_count>0 in fixture run"
    ]
    # No artifact is missing, so missing_evidence stays empty; the blocker
    # alone is sufficient to gate the decision.
    assert decision.missing_evidence == []


def test_review_missing_evidence_is_sorted_for_determinism():
    # Pass artifacts out of canonical order to confirm the missing list is
    # not order-sensitive — the reviewer must emit a deterministic, sorted
    # missing-evidence enumeration for downstream writers.
    decision = review_codebase_source_inspection(
        inventory=None,
        symbol_index=_symbol_index(),
        scope_map=None,
        validation_plan=_validation_plan(),
        risk_scan=None,
    )

    assert decision.missing_evidence == sorted(
        ["inventory", "scope_map", "risk_scan"]
    )


def test_review_two_runs_are_deterministic_for_missing_bundle():
    first = review_codebase_source_inspection(
        inventory=None,
        symbol_index=None,
        scope_map=None,
        validation_plan=None,
        risk_scan=None,
    )
    second = review_codebase_source_inspection(
        inventory=None,
        symbol_index=None,
        scope_map=None,
        validation_plan=None,
        risk_scan=None,
    )

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_review_safety_envelope_is_invariant_on_blocked_decision():
    decision = review_codebase_source_inspection(
        inventory=None,
        symbol_index=None,
        scope_map=None,
        validation_plan=None,
        risk_scan=None,
    )

    assert decision.action_authorized is False
    assert decision.raw_source_content_persisted is False
    assert decision.external_call_made is False
    assert decision.mutation_performed is False
    assert decision.publication_or_live_action_approved is False
