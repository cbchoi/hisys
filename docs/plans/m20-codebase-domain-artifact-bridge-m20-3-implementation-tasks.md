# Milestone M20.3 — Safe Codebase Bundle Load and Domain Result Enrichment Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for Milestone M20 Task M20.3 after M20.2 refs-only bundle gating was implemented.

**Goal:** Implement M20.3 so a codebase-domain request with a complete local codebase-analysis bundle can be safely loaded through existing runtime-boundary chokepoints and surfaced as bounded, advisory codebase evidence in `DomainInvestigationResult.investigation_data`.

**Architecture:** Reuse the existing safe loader `load_codebase_review_bundle` and its `resolve_instance_runtime_ref` protection. Keep `CodeInvestigationLayer` responsible for refs and role-level gate classification. Add the smallest translation/enrichment seam downstream of the three-layer use case, where `DomainUseCaseResult` is converted into `DomainInvestigationResult`, so complete codebase bundles produce a `DomainEvidencePackage` with summaries/refs/limitations and keep `requires_human_review=True`. Incomplete, invalid, missing, stale-schema, unsafe, or unreadable bundle refs must produce `quality_gate="needs_more_evidence"` and bounded missing/limitation evidence rather than crashing or approving.

**Tech Stack:** Python 3.11, dataclasses, Pydantic v2, pytest. No new dependency.

**Context Packet:** Required source handles: `src/hisys/domain/layers.py` (`DomainUseCaseResult`, `InvestigationWorkProduct`), `src/hisys/domain/use_cases.py` (`CodeInvestigationLayer`, bundle role helpers, aggregation/decision writers), `src/hisys/domain/adapters.py` (`DomainInvestigationContext`), `src/hisys/schemas/domain_investigation.py` (`DomainInvestigationResult`, `InvestigationDataPackage`, `DomainEvidencePackage`, `AlternativeDecisionSet`, `CandidateRecord`, `HisysToolResult`), `src/hisys/operations/codebase_analysis.py` (`CodebaseReviewBundle`, `load_codebase_review_bundle`, `review_codebase_source_inspection`, `CodebaseSourceInspectionDecision`), `tests/unit/test_codebase_domain_artifact_bridge.py`, domain regression tests, `docs/traceability/README.md`, and `ralph.md`. Retrieve exact adapter/translation files before implementation; this Prepare plan records the boundary and first RED only.

**Boundary Record:** Local fixture-only tests/docs/code mutation and local commit are allowed after validation. Remote push is not authorized. No live repo clone, raw source archival, browser/network/model call, credential resolution, external publication, destructive Git, CLI argument expansion, or action authorization. `candidate_complete` and `complete_for_human_review` remain advisory and human-review-required; they do not mean approved/safe-to-deploy/ready-for-live-action.

---

## Accepted decisions

1. **Safe loader chokepoint:** M20.3 must not open arbitrary caller refs directly. Any local file load goes through `load_codebase_review_bundle` / `resolve_instance_runtime_ref` or a wrapper that delegates to them.
2. **Result enrichment lives after use-case composition:** `CodeInvestigationLayer` remains refs/gate-only. Enrichment belongs to the adapter/result translation seam that builds `DomainInvestigationResult.investigation_data`.
3. **Advisory complete only:** A complete, valid bundle may set `quality_gate="passed"` only in the existing Hisys meaning of evidence-ready for human review, while `requires_human_review=True` and forbidden decision values remain absent.
4. **Failure is structured evidence:** Missing files, unsafe refs, schema validation errors, source-inspection decision blockers, and review findings map to `needs_more_evidence` with evidence package limitations/open questions rather than unhandled exceptions.
5. **No CLI change:** Tests construct requests/context directly. Repeatable CLI artifact refs remain M20.4.
6. **No raw source content:** Enriched evidence may include counts, schema IDs, artifact refs, risk categories, scope IDs, validation command refs, and decision refs. It must not persist raw source text.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm M20.2 is current and the working tree is clean.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:** branch `dars`, HEAD at or after `aba9aa6 feat: gate incomplete codebase artifact bundles`, domain gate 17 passed, DARS gate 48 passed.

---

## Task 1: RED — complete local bundle enriches DomainInvestigationResult evidence

**Objective:** Add a failing test that a complete fixture bundle is loaded safely and appears as a bounded codebase evidence package in the full domain result.

**Files:**

- Modify or create: `tests/unit/test_codebase_domain_artifact_bridge.py` or a narrower new file if the adapter seam is separate.
- Inspect before editing: the result translation/adapter file that builds `DomainInvestigationResult`.

**Test sketch:**

```python
def test_codebase_domain_result_enriches_complete_local_bundle(tmp_path: Path) -> None:
    refs = _write_minimal_complete_codebase_bundle(tmp_path, request_id="REQ-M20-3")
    request = _build_codebase_request(refs=[
        ("SRC-INV", refs["inventory"]),
        ("SRC-SYM", refs["symbol_index"]),
        ("SRC-SCOPE", refs["scope_map"]),
        ("SRC-RISK", refs["risk_scan"]),
    ])

    result = _run_codebase_domain_result(request=request, instance_root=tmp_path)

    assert result.quality_gate == "passed"
    assert result.requires_human_review is True
    packages = result.investigation_data.evidence_packages
    codebase_packages = [pkg for pkg in packages if pkg.evidence_type == "codebase_analysis_bundle"]
    assert len(codebase_packages) == 1
    package = codebase_packages[0]
    assert package.evidence_refs == [refs["inventory"], refs["symbol_index"], refs["scope_map"], refs["risk_scan"]]
    assert "approved" not in result.recommendation_summary.lower()
    assert result.external_call_made is False
    assert result.mutation_performed is False
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py::test_codebase_domain_result_enriches_complete_local_bundle -q
```

**Expected RED:** `AttributeError`, missing helper/seam, or assertion failure because the current result has no codebase evidence package/enrichment.

---

## Task 2: GREEN — load bundle through safe chokepoint and build bounded evidence package

**Objective:** Implement the smallest adapter/result translation behavior to make the complete-bundle test pass.

**Files:**

- Modify: the domain adapter/result translation module discovered in Task 0.
- Possibly modify: `src/hisys/domain/layers.py` only if a minimal work-product field is required.
- Do not modify: CLI parser or request schema.

**Implementation constraints:**

- Derive required refs from `InvestigationWorkProduct.codebase_artifact_refs` by role.
- Call `load_codebase_review_bundle(instance_root=..., inventory_ref=..., symbol_index_ref=..., scope_map_ref=..., risk_scan_ref=...)`.
- Build one `DomainEvidencePackage` with:
  - `evidence_type="codebase_analysis_bundle"`
  - summary limited to schema IDs/counts/scope/risk category counts
  - `evidence_refs` and `source_refs` set to runtime-boundary refs, not raw source
  - limitations that preserve advisory-only/human-review boundary
  - `external_call_made=False`, `mutation_performed=False`
- Keep `requires_human_review=True`.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py::test_codebase_domain_result_enriches_complete_local_bundle -q
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py -q
```

---

## Task 3: RED/GREEN — invalid or unsafe bundle yields needs_more_evidence

**Objective:** Pin fail-closed behavior for missing files, unsafe refs, schema mismatch, and source-inspection blockers.

**Files:**

- Modify: `tests/unit/test_codebase_domain_artifact_bridge.py`
- Modify if needed: adapter/result translation module.

**Test sketch:**

```python
def test_codebase_domain_result_maps_unreadable_bundle_to_needs_more_evidence(tmp_path: Path) -> None:
    request = _build_codebase_request(refs=[
        ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3/inventory.json"),
        ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3/symbol-index.json"),
        ("SRC-SCOPE", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3/scope-map.json"),
        ("SRC-RISK", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3/risk-scan.json"),
    ])

    result = _run_codebase_domain_result(request=request, instance_root=tmp_path)

    assert result.quality_gate == "needs_more_evidence"
    assert result.requires_human_review is True
    assert any("unreadable" in limitation or "missing" in limitation for pkg in result.investigation_data.evidence_packages for limitation in pkg.limitations)
    assert result.external_call_made is False
    assert result.mutation_performed is False
```

**Expected:** no unhandled exception escapes the adapter/result translation seam for expected local bundle load failures.

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
git add tests/unit/test_codebase_domain_artifact_bridge.py src/hisys/domain src/hisys/schemas docs/traceability/README.md ralph.md
git commit -m "feat: enrich codebase domain result from local bundle"
```

---

## Stop conditions

Stop and report if implementation requires CLI flags, live external repository access, raw source archival, model/browser/network calls, credential access, destructive Git, publication, or action authorization. Stop and prepare a narrower plan if the adapter/result translation seam is absent or materially different from the expected `DomainInvestigationResult` builder.

## Follow-on increments

- **M20.4:** repeatable CLI artifact-ref argument and fixture smoke.
- **M20.5:** docs/gate finish and Hisys milestone checkpoint.
