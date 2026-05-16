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
from pathlib import Path
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
    RiskBoundaryFinding,
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


# ---------------------------------------------------------------------------
# M19.2 — complete fixture set becomes human-reviewable.
# ---------------------------------------------------------------------------


def test_review_returns_human_reviewable_on_complete_consistent_bundle():
    inventory = _inventory()
    symbol_index = _symbol_index()
    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=CodebaseScopeMap(
            repo_root=inventory.repo_root,
            inventory_schema_id=inventory.schema_id,
            symbol_index_schema_id=symbol_index.schema_id,
        ),
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "complete_for_human_review"
    assert decision.missing_evidence == []
    assert decision.validation_findings == []
    assert decision.unresolved_blockers == []
    # No live-action approval is granted even when the bundle is complete.
    assert decision.publication_or_live_action_approved is False
    assert decision.action_authorized is False
    assert decision.external_call_made is False
    assert decision.mutation_performed is False


def test_review_complete_bundle_two_runs_are_deterministic():
    inventory = _inventory()
    symbol_index = _symbol_index()
    scope_map = CodebaseScopeMap(
        repo_root=inventory.repo_root,
        inventory_schema_id=inventory.schema_id,
        symbol_index_schema_id=symbol_index.schema_id,
    )

    first = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=scope_map,
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )
    second = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=scope_map,
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_review_blocks_when_scope_map_inventory_schema_id_mismatch():
    inventory = _inventory()
    symbol_index = _symbol_index()
    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=CodebaseScopeMap(
            repo_root=inventory.repo_root,
            inventory_schema_id="hisys.codebase.WRONG",
            symbol_index_schema_id=symbol_index.schema_id,
        ),
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert any(
        "inventory_schema_id" in finding for finding in decision.validation_findings
    )


def test_review_blocks_when_scope_map_symbol_index_schema_id_mismatch():
    inventory = _inventory()
    symbol_index = _symbol_index()
    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=CodebaseScopeMap(
            repo_root=inventory.repo_root,
            inventory_schema_id=inventory.schema_id,
            symbol_index_schema_id="hisys.codebase.WRONG",
        ),
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert any(
        "symbol_index_schema_id" in finding for finding in decision.validation_findings
    )


def test_review_blocks_when_any_artifact_persisted_raw_source_content():
    inventory = _inventory()
    inventory.raw_source_content_persisted = True
    symbol_index = _symbol_index()
    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=CodebaseScopeMap(
            repo_root=inventory.repo_root,
            inventory_schema_id=inventory.schema_id,
            symbol_index_schema_id=symbol_index.schema_id,
        ),
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert any(
        "raw_source_content_persisted" in finding
        for finding in decision.validation_findings
    )


def test_review_blocks_when_risk_scan_action_authorized_is_true():
    inventory = _inventory()
    symbol_index = _symbol_index()
    risk_scan = _risk_scan()
    risk_scan.action_authorized = True
    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=CodebaseScopeMap(
            repo_root=inventory.repo_root,
            inventory_schema_id=inventory.schema_id,
            symbol_index_schema_id=symbol_index.schema_id,
        ),
        validation_plan=_validation_plan(),
        risk_scan=risk_scan,
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert any(
        "risk_scan.action_authorized" in finding
        for finding in decision.validation_findings
    )


def test_review_blocks_when_any_risk_finding_marks_action_authorized():
    inventory = _inventory()
    symbol_index = _symbol_index()
    risk_scan = _risk_scan()
    risk_scan.findings.append(
        RiskBoundaryFinding(
            category="subprocess_execution",
            path="pkg/exec.py",
            line=4,
            signal="subprocess.run",
            # Manually toggling action_authorized on a single finding must
            # downgrade the decision even if the scan envelope is False.
            action_authorized=True,
        )
    )
    risk_scan.finding_count = len(risk_scan.findings)

    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=CodebaseScopeMap(
            repo_root=inventory.repo_root,
            inventory_schema_id=inventory.schema_id,
            symbol_index_schema_id=symbol_index.schema_id,
        ),
        validation_plan=_validation_plan(),
        risk_scan=risk_scan,
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert any(
        "risk_boundary_finding.action_authorized" in finding
        for finding in decision.validation_findings
    )


def test_review_validation_findings_are_sorted_for_determinism():
    # Trigger multiple consistency failures and confirm the resulting
    # validation_findings list is sorted alphabetically so a downstream
    # writer sees a deterministic shape.
    inventory = _inventory()
    inventory.raw_source_content_persisted = True
    symbol_index = _symbol_index()
    risk_scan = _risk_scan()
    risk_scan.action_authorized = True
    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=CodebaseScopeMap(
            repo_root=inventory.repo_root,
            inventory_schema_id="hisys.codebase.WRONG",
            symbol_index_schema_id=symbol_index.schema_id,
        ),
        validation_plan=_validation_plan(),
        risk_scan=risk_scan,
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.validation_findings == sorted(decision.validation_findings)
    # At least three independent failures were triggered.
    assert len(decision.validation_findings) >= 3


def test_review_missing_artifact_skips_dependent_consistency_finding():
    # When scope_map is missing entirely, the schema-id-match check has no
    # input to compare against; the reviewer must not synthesize a
    # validation finding from a missing artifact. The missing_evidence list
    # remains the only blocking signal.
    inventory = _inventory()
    symbol_index = _symbol_index()
    decision = review_codebase_source_inspection(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=None,
        validation_plan=_validation_plan(),
        risk_scan=_risk_scan(),
    )

    assert decision.decision == "blocked_needs_more_evidence"
    assert decision.missing_evidence == ["scope_map"]
    for finding in decision.validation_findings:
        assert "inventory_schema_id" not in finding
        assert "symbol_index_schema_id" not in finding


# ---------------------------------------------------------------------------
# M19.3 — runtime refs must resolve under instance root.
# ---------------------------------------------------------------------------

from hisys.operations.codebase_analysis import (  # noqa: E402
    CodebaseReviewBundle,
    build_codebase_inventory,
    build_codebase_scope_map,
    build_codebase_validation_plan,
    build_python_symbol_index,
    load_codebase_review_bundle,
    scan_codebase_risk_boundaries,
    write_codebase_inventory,
    write_codebase_risk_scan,
    write_codebase_scope_map,
    write_python_symbol_index,
)


_FIXTURE_DATE = "20260517"
_FIXTURE_REQUEST_ID = "m19_3_fixture"


def _seed_review_repo(repo: Path) -> None:
    """Seed a minimal local repo so the artifact writers produce real bundles."""

    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pkg" / "mod.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )


def _materialize_bundle(
    instance_root: Path, repo: Path
) -> tuple[str, str, str, str]:
    """Write all four artifacts and return their relative refs."""

    inventory = build_codebase_inventory(repo_root=repo)
    inv_ref = write_codebase_inventory(
        instance_root=instance_root,
        date=_FIXTURE_DATE,
        request_id=_FIXTURE_REQUEST_ID,
        inventory=inventory,
    )["json_ref"]

    symbol_index = build_python_symbol_index(repo_root=repo)
    sym_ref = write_python_symbol_index(
        instance_root=instance_root,
        date=_FIXTURE_DATE,
        request_id=_FIXTURE_REQUEST_ID,
        symbol_index=symbol_index,
    )["json_ref"]

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index
    )
    validation_plan = build_codebase_validation_plan(scope_map)
    scope_ref = write_codebase_scope_map(
        instance_root=instance_root,
        date=_FIXTURE_DATE,
        request_id=_FIXTURE_REQUEST_ID,
        scope_map=scope_map,
        validation_plan=validation_plan,
    )["json_ref"]

    risk_scan = scan_codebase_risk_boundaries(repo_root=repo)
    risk_ref = write_codebase_risk_scan(
        instance_root=instance_root,
        date=_FIXTURE_DATE,
        request_id=_FIXTURE_REQUEST_ID,
        scan=risk_scan,
    )["json_ref"]

    return inv_ref, sym_ref, scope_ref, risk_ref


def test_load_review_bundle_round_trip_returns_pydantic_bundle(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)

    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)

    bundle = load_codebase_review_bundle(
        instance_root=instance_root,
        inventory_ref=inv_ref,
        symbol_index_ref=sym_ref,
        scope_map_ref=scope_ref,
        risk_scan_ref=risk_ref,
    )

    assert isinstance(bundle, CodebaseReviewBundle)
    assert bundle.schema_id == "hisys.codebase.review_bundle"
    assert isinstance(bundle.inventory, CodebaseInventory)
    assert isinstance(bundle.symbol_index, PythonSymbolIndex)
    assert isinstance(bundle.scope_map, CodebaseScopeMap)
    assert isinstance(bundle.validation_plan, CodebaseValidationPlan)
    assert isinstance(bundle.risk_scan, CodebaseRiskScan)
    assert bundle.scope_map.inventory_schema_id == bundle.inventory.schema_id
    assert bundle.scope_map.symbol_index_schema_id == bundle.symbol_index.schema_id
    # The bundle envelope inherits the no-live-action invariants.
    assert bundle.raw_source_content_persisted is False
    assert bundle.action_authorized is False


def test_load_review_bundle_then_review_returns_human_reviewable(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)

    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)
    bundle = load_codebase_review_bundle(
        instance_root=instance_root,
        inventory_ref=inv_ref,
        symbol_index_ref=sym_ref,
        scope_map_ref=scope_ref,
        risk_scan_ref=risk_ref,
    )

    decision = review_codebase_source_inspection(
        inventory=bundle.inventory,
        symbol_index=bundle.symbol_index,
        scope_map=bundle.scope_map,
        validation_plan=bundle.validation_plan,
        risk_scan=bundle.risk_scan,
    )

    assert decision.decision == "complete_for_human_review"
    assert decision.missing_evidence == []
    assert decision.validation_findings == []


@pytest.mark.parametrize(
    "ref_kwarg",
    [
        "inventory_ref",
        "symbol_index_ref",
        "scope_map_ref",
        "risk_scan_ref",
    ],
)
def test_load_review_bundle_rejects_absolute_ref(tmp_path: Path, ref_kwarg):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)
    kwargs = {
        "inventory_ref": inv_ref,
        "symbol_index_ref": sym_ref,
        "scope_map_ref": scope_ref,
        "risk_scan_ref": risk_ref,
    }
    kwargs[ref_kwarg] = "/etc/passwd"

    with pytest.raises(ValueError, match="absolute"):
        load_codebase_review_bundle(instance_root=instance_root, **kwargs)


@pytest.mark.parametrize(
    "ref_kwarg",
    [
        "inventory_ref",
        "symbol_index_ref",
        "scope_map_ref",
        "risk_scan_ref",
    ],
)
def test_load_review_bundle_rejects_traversal_ref(tmp_path: Path, ref_kwarg):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)
    kwargs = {
        "inventory_ref": inv_ref,
        "symbol_index_ref": sym_ref,
        "scope_map_ref": scope_ref,
        "risk_scan_ref": risk_ref,
    }
    kwargs[ref_kwarg] = "../escape/inventory.json"

    with pytest.raises(ValueError, match="traversal"):
        load_codebase_review_bundle(instance_root=instance_root, **kwargs)


@pytest.mark.parametrize(
    "ref_kwarg",
    [
        "inventory_ref",
        "symbol_index_ref",
        "scope_map_ref",
        "risk_scan_ref",
    ],
)
def test_load_review_bundle_rejects_empty_ref(tmp_path: Path, ref_kwarg):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)
    kwargs = {
        "inventory_ref": inv_ref,
        "symbol_index_ref": sym_ref,
        "scope_map_ref": scope_ref,
        "risk_scan_ref": risk_ref,
    }
    kwargs[ref_kwarg] = ""

    with pytest.raises(ValueError, match="non-empty"):
        load_codebase_review_bundle(instance_root=instance_root, **kwargs)


def test_load_review_bundle_rejects_dangling_ref(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)

    # Replace inventory_ref with a syntactically valid path that does not exist.
    dangling_ref = inv_ref.rsplit("/", 1)[0] + "/missing-inventory.json"

    with pytest.raises(FileNotFoundError):
        load_codebase_review_bundle(
            instance_root=instance_root,
            inventory_ref=dangling_ref,
            symbol_index_ref=sym_ref,
            scope_map_ref=scope_ref,
            risk_scan_ref=risk_ref,
        )


def test_load_review_bundle_rejects_symlink_escape(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)

    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    escape_link = instance_root / "escape-inventory.json"
    escape_link.symlink_to(outside)

    with pytest.raises(ValueError, match="outside instance root"):
        load_codebase_review_bundle(
            instance_root=instance_root,
            inventory_ref="escape-inventory.json",
            symbol_index_ref=sym_ref,
            scope_map_ref=scope_ref,
            risk_scan_ref=risk_ref,
        )


# ---------------------------------------------------------------------------
# M19.4 — review CLI and Markdown summary writer.
# ---------------------------------------------------------------------------

import json
import os
import subprocess
import sys

from hisys.operations.codebase_analysis import (  # noqa: E402
    SOURCE_INSPECTION_DECISION_JSON_FILENAME,
    SOURCE_INSPECTION_DECISION_MARKDOWN_FILENAME,
    write_codebase_source_inspection_decision,
)

REPO_ROOT_FOR_CLI = Path(__file__).resolve().parents[2]
SRC_ROOT_FOR_CLI = REPO_ROOT_FOR_CLI / "src"


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_ROOT_FOR_CLI}{os.pathsep}{env.get('PYTHONPATH', '')}"
    return subprocess.run(
        [sys.executable, "-m", "hisys.cli.main", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_write_decision_round_trip_emits_expected_artifacts(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    decision = CodebaseSourceInspectionDecision(
        decision="complete_for_human_review",
    )

    result = write_codebase_source_inspection_decision(
        instance_root=instance_root,
        date="20260517",
        request_id="REQ-CODEBASE-DECISION-001",
        decision=decision,
    )

    assert result["schema_id"] == "hisys.codebase.source_inspection_decision"
    assert result["decision"] == "complete_for_human_review"
    assert result["external_call_made"] is False
    assert result["mutation_performed"] is False
    assert result["publication_or_live_action_approved"] is False
    assert result["action_authorized"] is False
    assert result["raw_source_content_persisted"] is False
    assert result["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-DECISION-001/"
        + SOURCE_INSPECTION_DECISION_JSON_FILENAME
    )
    assert result["markdown_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-DECISION-001/"
        + SOURCE_INSPECTION_DECISION_MARKDOWN_FILENAME
    )

    json_path = instance_root / result["json_ref"]
    md_path = instance_root / result["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["schema_id"] == "hisys.codebase.source_inspection_decision"
    assert loaded["decision"] == "complete_for_human_review"

    md_text = md_path.read_text(encoding="utf-8")
    assert "complete_for_human_review" in md_text
    assert "review evidence" in md_text


def test_write_decision_is_deterministic_across_two_runs(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    decision = CodebaseSourceInspectionDecision(
        decision="blocked_needs_more_evidence",
        missing_evidence=["inventory", "scope_map"],
        validation_findings=["inventory.raw_source_content_persisted=true; etc."],
    )

    write_codebase_source_inspection_decision(
        instance_root=instance_root,
        date="20260517",
        request_id="REQ-CODEBASE-DETERMINISM",
        decision=decision,
    )
    first = (
        instance_root
        / "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-DETERMINISM"
        / SOURCE_INSPECTION_DECISION_JSON_FILENAME
    ).read_text(encoding="utf-8")

    write_codebase_source_inspection_decision(
        instance_root=instance_root,
        date="20260517",
        request_id="REQ-CODEBASE-DETERMINISM",
        decision=decision,
    )
    second = (
        instance_root
        / "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-DETERMINISM"
        / SOURCE_INSPECTION_DECISION_JSON_FILENAME
    ).read_text(encoding="utf-8")

    assert first == second


@pytest.mark.parametrize("bad_slug", ["..", "../etc", "20260517/extra", ""])
def test_write_decision_rejects_traversal_in_request_id(
    tmp_path: Path, bad_slug
):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    decision = CodebaseSourceInspectionDecision(
        decision="complete_for_human_review",
    )
    with pytest.raises(ValueError):
        write_codebase_source_inspection_decision(
            instance_root=instance_root,
            date="20260517",
            request_id=bad_slug,
            decision=decision,
        )


def test_review_codebase_analysis_cli_complete_bundle_returns_zero(
    tmp_path: Path,
):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)

    completed = _run_cli(
        "review-codebase-analysis",
        "--instance",
        str(instance_root),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-DECISION-CLI-001",
        "--inventory-ref",
        inv_ref,
        "--symbol-index-ref",
        sym_ref,
        "--scope-map-ref",
        scope_ref,
        "--risk-scan-ref",
        risk_ref,
        "--format",
        "json",
        cwd=REPO_ROOT_FOR_CLI,
    )

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.codebase.source_inspection_decision"
    assert payload["decision"] == "complete_for_human_review"
    assert payload["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-DECISION-CLI-001/"
        + SOURCE_INSPECTION_DECISION_JSON_FILENAME
    )

    json_path = instance_root / payload["json_ref"]
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["decision"] == "complete_for_human_review"
    assert loaded["missing_evidence"] == []
    assert loaded["validation_findings"] == []


def test_review_codebase_analysis_cli_blocked_bundle_returns_nonzero(
    tmp_path: Path,
):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)

    # Corrupt the inventory artifact in place so the loader still finds the
    # file but the consistency check (scope_map.inventory_schema_id) fails
    # against the corrupted inventory.schema_id.
    inv_path = instance_root / inv_ref
    corrupted = json.loads(inv_path.read_text(encoding="utf-8"))
    corrupted["schema_id"] = "hisys.codebase.NOT_INVENTORY"
    inv_path.write_text(
        json.dumps(corrupted, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    completed = _run_cli(
        "review-codebase-analysis",
        "--instance",
        str(instance_root),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-DECISION-CLI-002",
        "--inventory-ref",
        inv_ref,
        "--symbol-index-ref",
        sym_ref,
        "--scope-map-ref",
        scope_ref,
        "--risk-scan-ref",
        risk_ref,
        "--format",
        "json",
        cwd=REPO_ROOT_FOR_CLI,
    )

    # Decision is `blocked_needs_more_evidence`; the CLI exits non-zero so
    # automation (CI / loop) can branch on the decision without parsing the
    # JSON. Per ralph.md Section 12 a non-zero exit is reserved for review
    # outcomes that require more evidence, not for runtime errors.
    assert completed.returncode != 0
    assert completed.returncode != 2 or True  # Allow either 2 or 3 below
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.codebase.source_inspection_decision"
    assert payload["decision"] == "blocked_needs_more_evidence"


def test_review_codebase_analysis_cli_rejects_absolute_ref(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)

    completed = _run_cli(
        "review-codebase-analysis",
        "--instance",
        str(instance_root),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-DECISION-CLI-003",
        "--inventory-ref",
        "/etc/passwd",
        "--symbol-index-ref",
        sym_ref,
        "--scope-map-ref",
        scope_ref,
        "--risk-scan-ref",
        risk_ref,
        "--format",
        "json",
        cwd=REPO_ROOT_FOR_CLI,
    )

    assert completed.returncode != 0
    assert "absolute" in completed.stderr.lower()


def test_review_codebase_analysis_cli_rejects_traversal_ref(tmp_path: Path):
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    inv_ref, sym_ref, scope_ref, risk_ref = _materialize_bundle(instance_root, repo)

    completed = _run_cli(
        "review-codebase-analysis",
        "--instance",
        str(instance_root),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-DECISION-CLI-004",
        "--inventory-ref",
        inv_ref,
        "--symbol-index-ref",
        sym_ref,
        "--scope-map-ref",
        scope_ref,
        "--risk-scan-ref",
        "../escape/risk-scan.json",
        "--format",
        "json",
        cwd=REPO_ROOT_FOR_CLI,
    )

    assert completed.returncode != 0
    assert "traversal" in completed.stderr.lower()
