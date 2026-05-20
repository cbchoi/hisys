# Milestone M20.2 — Incomplete Codebase Artifact Bundle Gate Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for Milestone M20 Task M20.2 — incomplete codebase artifact bundle gating — after M20.1 accepted refs-only `codebase_artifact_refs`.

**Goal:** Implement M20.2 so a codebase-domain request with incomplete or unreadable codebase-analysis bundle refs yields a deterministic advisory `needs_more_evidence` result instead of attempting enrichment or silently ignoring the bundle.

**Architecture:** Keep the M20.1 refs-only field as the input boundary. Add one small bundle-gating helper in `src/hisys/domain/use_cases.py` that classifies `InvestigationWorkProduct.codebase_artifact_refs` by expected codebase-analysis artifact role and records missing/invalid bundle categories on the work product. The helper must not authorize action, publish, call a model, clone repositories, or add CLI flags. M20.2 may read only local runtime-boundary JSON via the existing safe chokepoint if the GREEN path requires checking file presence/schema id; full enrichment remains M20.3.

**Tech Stack:** Python 3.11, dataclasses, Pydantic v2, pytest. No new dependency.

**Context Packet:** Required source handles: `src/hisys/domain/layers.py` (`InvestigationWorkProduct`), `src/hisys/domain/use_cases.py` (`CodeInvestigationLayer`, M20.1 helpers), `src/hisys/operations/codebase_analysis.py` (`CodebaseReviewBundle`, `load_codebase_review_bundle`, schema IDs, `resolve_instance_runtime_ref`), `src/hisys/schemas/domain_investigation.py` (`DomainInvestigationResult` quality gate semantics), `tests/unit/test_codebase_domain_artifact_bridge.py`, domain regression tests, `docs/traceability/README.md`, and `ralph.md`. Omit raw codebase-analysis fixture content from active context until the RED test creates minimal local JSON fixtures or deliberately uses missing refs.

**Boundary Record:** Local tests/docs/code mutation and local commit are allowed after validation. Remote push is not authorized. No live external call, repo clone, credential resolution, browser/network access, publication, destructive Git, or runtime action authorization. M20.2 is gating only; M20.3 owns enrichment into `DomainInvestigationResult`, M20.4 owns CLI arguments, and M20.5 owns public/docs finish.

---

## Accepted decisions

1. **Gating before enrichment:** M20.2 classifies bundle completeness and evidence sufficiency before any enrichment surface is added.
2. **Advisory result only:** incomplete bundles produce `quality_gate="needs_more_evidence"` and `requires_human_review=True`; they never produce approval, safe-to-deploy, or live-action language.
3. **Role names are canonical:** expected roles are `inventory`, `symbol_index`, `scope_map`, `validation_plan`, and `risk_scan`, matching `_REQUIRED_ARTIFACT_NAMES` in `src/hisys/operations/codebase_analysis.py`.
4. **No CLI change:** Tests construct `DomainInvestigationRequest` directly. `investigate-domain --codebase-artifact-ref` is deferred to M20.4.
5. **Minimal field addition:** Add only the smallest work-product fields needed for gating, e.g. `codebase_missing_evidence: list[str] = field(default_factory=list)` and optionally `codebase_bundle_gate: str = "not_applicable"`. Do not reshape `DomainInvestigationRequest`, `DomainSourceRef`, or `DomainInvestigationResult` in this increment.
6. **Safe local reads only if needed:** Prefer a pure ref-role completeness gate first. If schema-id validation is implemented in M20.2, read local files only through `resolve_instance_runtime_ref` or `load_codebase_review_bundle`; do not open caller refs directly.
7. **Traceability required:** Update `docs/traceability/README.md` and `ralph.md` in the implementation increment.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm M20.1 is current and the working tree is clean.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:** branch `dars`, HEAD at or after `d87bc96 feat: accept codebase artifact bundle refs`, domain gate 15 passed, DARS gate 48 passed.

---

## Task 1: RED — incomplete bundle records missing evidence on the work product

**Objective:** Add a failing test that a codebase request with only inventory and symbol-index refs records missing `scope_map`, `validation_plan`, and `risk_scan` evidence and keeps the advisory gate at `needs_more_evidence`.

**Files:**

- Modify: `tests/unit/test_codebase_domain_artifact_bridge.py`

**Test sketch:**

```python
def test_code_investigation_layer_records_incomplete_bundle_missing_evidence(tmp_path: Path) -> None:
    request = _build_codebase_request(
        refs=[
            ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/inventory.json"),
            ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/symbol-index.json"),
        ],
    )

    work_product = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements")).investigate(
        request=request,
        context=_context(tmp_path),
    )

    assert work_product.codebase_bundle_gate == "needs_more_evidence"
    assert work_product.codebase_missing_evidence == ["risk_scan", "scope_map", "validation_plan"]
    assert work_product.requires_human_review is True
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py::test_code_investigation_layer_records_incomplete_bundle_missing_evidence -q
```

**Expected RED:** `AttributeError` for missing `codebase_bundle_gate` or `codebase_missing_evidence`.

---

## Task 2: GREEN — classify bundle role completeness

**Objective:** Add the smallest production logic to classify refs by artifact role.

**Files:**

- Modify: `src/hisys/domain/layers.py`
- Modify: `src/hisys/domain/use_cases.py`

**Implementation sketch:**

```python
CODEBASE_REQUIRED_ARTIFACT_ROLES = ("inventory", "symbol_index", "scope_map", "validation_plan", "risk_scan")

def _codebase_artifact_role(ref: str) -> str | None:
    filename = ref.rsplit("/", 1)[-1]
    if filename == "inventory.json":
        return "inventory"
    if filename in {"symbol-index.json", "symbol_index.json"}:
        return "symbol_index"
    if filename in {"scope-map.json", "scope_map.json"}:
        return "scope_map"
    if filename in {"validation-plan.json", "validation_plan.json"}:
        return "validation_plan"
    if filename in {"risk-scan.json", "risk_scan.json"}:
        return "risk_scan"
    if filename == "source-inspection-decision.json":
        return "source_inspection_decision"  # optional M20.3/M20.5 input, not required for M20.2
    return None
```

Add dataclass fields:

```python
codebase_bundle_gate: str = "not_applicable"
codebase_missing_evidence: list[str] = field(default_factory=list)
```

In `CodeInvestigationLayer.investigate`, compute roles from `codebase_artifact_refs`. If there are no refs, keep `not_applicable` and `[]`. If refs exist and any required role is missing, set `codebase_bundle_gate="needs_more_evidence"` and sorted missing role names. If all required roles are present, set `codebase_bundle_gate="candidate_complete"` and `[]`; do not enrich the final result yet.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py -q
```

Expected: existing two tests plus the new missing-evidence test pass.

---

## Task 3: RED/GREEN — complete role set is candidate-complete but not passed

**Objective:** Pin that completeness classification is not final approval.

**Files:**

- Modify: `tests/unit/test_codebase_domain_artifact_bridge.py`
- Modify if needed: `src/hisys/domain/use_cases.py`

**Test sketch:**

```python
def test_code_investigation_layer_marks_complete_bundle_candidate_complete(tmp_path: Path) -> None:
    request = _build_codebase_request(refs=[...five required refs...])
    work_product = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements")).investigate(
        request=request,
        context=_context(tmp_path),
    )
    assert work_product.codebase_bundle_gate == "candidate_complete"
    assert work_product.codebase_missing_evidence == []
    assert work_product.requires_human_review is True
```

**Expected:** RED may fail because the complete case is still `needs_more_evidence`; GREEN should be a minimal branch using the role set. Do not set `quality_gate="passed"` in M20.2; that belongs to M20.3 after enrichment/review evidence is surfaced.

---

## Task 4: Documentation, gate, and commit

**Files:**

- Modify: `docs/traceability/README.md`
- Modify: `ralph.md`

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add src/hisys/domain/layers.py src/hisys/domain/use_cases.py tests/unit/test_codebase_domain_artifact_bridge.py docs/traceability/README.md ralph.md
git commit -m "feat: gate incomplete codebase artifact bundles"
```

---

## Stop conditions

Stop and report if implementation requires changing `DomainInvestigationRequest`, adding CLI flags, surfacing enriched bundle content into `DomainInvestigationResult`, accepting external refs, cloning repositories, reading raw source files, or authorizing action/publication. These are outside M20.2.

## Follow-on increments

- **M20.3:** read/validate a complete local bundle through existing safe loaders and surface summarized codebase evidence into `DomainInvestigationResult.investigation_data`.
- **M20.4:** add repeatable CLI artifact-ref argument and fixture smoke.
- **M20.5:** docs/gate finish and Hisys milestone checkpoint.
