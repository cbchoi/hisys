# Milestone M20.1 — Codebase Domain Artifact Bundle Acceptance Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for Milestone M20 Task M20.1 — "RED/GREEN codebase request can reference local artifact bundle" — from `ralph.md` Section 14. It authorizes only local RED/GREEN work after this Prepare checkpoint is committed.

**Goal:** Implement `M20.1`: let a `DomainInvestigationRequest` whose `domain == "codebase"` reference a local codebase-analysis artifact bundle (inventory, symbol-index, scope-map+validation-plan, risk-scan, source-inspection-decision) by ref, and have `CodeInvestigationLayer.investigate` extract those refs into the existing `InvestigationWorkProduct.evidence_refs` without performing any artifact load yet. The bundle reference contract is pinned in this increment; bundle loading, completeness gating, and full enrichment remain deferred to M20.2/M20.3.

**Architecture:** Extend `CodeInvestigationLayer.investigate` (`src/hisys/domain/use_cases.py`) so that when `request.sources` contains entries with `source_type=="runtime_record"` whose `ref` matches the codebase-analysis subtree shape (`runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/<file>.json`), those refs are surfaced as a deterministic, ordered, deduplicated `codebase_artifact_refs: list[str]` field on `InvestigationWorkProduct` (or appended to `evidence_refs` if the field shape cannot be extended in one increment). No artifact JSON is read in this increment; the test pins only that the refs flow through the layer.

**Tech Stack:** Python 3.11, Pydantic v2, dataclasses, pytest. No new runtime dependency.

**Context Packet:** Required source handles are `src/hisys/schemas/domain_investigation.py` (`DomainInvestigationRequest`, `DomainSourceRef`, `SourceType`, `DomainInvestigationResult`, `InvestigationDataPackage`, `DomainEvidencePackage`), `src/hisys/domain/use_cases.py` (`CodeInvestigationLayer`, `_is_requirements_analysis_objective`), `src/hisys/domain/layers.py` (`InvestigationWorkProduct`, `DomainUseCaseContext`), `src/hisys/domain/adapters.py` (`DomainInvestigationContext`, `DomainAdapterRegistry`), `src/hisys/domain/domain_adapters.py` (`StructuredDomainAdapter`), `src/hisys/domain/specs.py` (`codebase_spec`), `src/hisys/operations/codebase_analysis.py` (loader chokepoint `resolve_instance_runtime_ref`, `load_codebase_review_bundle`, schema IDs), `src/hisys/cli/main.py` (`_cmd_investigate_domain` and the existing artifact-ref arguments around line 7513-7602), `docs/traceability/README.md`, `ralph.md`, and the existing `docs/traceability/dars-critic-panel-runtime-traceability.md` precedent for an RTM/README increment row. Validation handles are the focused codebase-domain test suite, the focused panel + CLI regression, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized. Live external repository clone, raw source content archival, model calls, browser/network calls, credential resolution, publication, destructive Git, CLI argument expansion beyond an `--artifact-ref` repeatable flag (deferred to M20.4), parallel execution activation, and downstream action authorization are out of scope. This increment changes one persisted advisory work-product schema field and must update traceability before commit. The new field carries refs only, never inlined artifact content.

---

## Accepted decisions

1. **Refs only, no loads in M20.1:** The layer must accept artifact refs as a typed list and pass them through to the work product. No JSON read, no Pydantic validation against the codebase-analysis schemas, no resolution against `instance_root`. Those concerns belong to M20.2/M20.3.
2. **Existing typed source type reuse:** Use the existing `SourceType` literal `"runtime_record"` to mark codebase-analysis artifact refs in `request.sources`. Do not invent a new source type in this increment.
3. **Subtree-aware extraction:** The layer extracts refs whose path component prefix matches `runtime-boundary/codebase-analysis/` (forward-slash, no leading slash, no `..` segments). Other `runtime_record` refs flow through unchanged in `evidence_refs`. The extraction is a pure string check; no filesystem touch.
4. **Deterministic ordering:** The extracted refs preserve the order they appear in `request.sources` and deduplicate by value while preserving first-occurrence order.
5. **Backward compatibility:** Existing callers that pass no codebase-analysis refs must continue to see `codebase_artifact_refs == []` (or the field absent — the test must pin the chosen shape) and must observe no change to `evidence_refs`, `memo_refs`, `local_search_targets`, `data_source_targets`, or `domain_subtype`.
6. **No CLI change in M20.1:** `investigate-domain` does not gain a new flag in this increment. The new layer behavior is exercised by constructing a `DomainInvestigationRequest` directly in tests. The CLI flag is deferred to M20.4.
7. **No `DomainInvestigationResult` change in M20.1:** The work-product field addition is internal to the layer's output dataclass. Surfacing the bundle into `DomainInvestigationResult.investigation_data` is deferred to M20.3.
8. **Safety envelope unchanged:** `quality_gate`, `external_call_made`, `mutation_performed`, `requires_human_review`, advisory-only synthesis fields, and `DARS` decision placement remain locked exactly as in the current code path.
9. **Traceability required:** Because the layer's work-product surface changes (new field or first-pass extraction logic), update RTM/traceability docs and the Ralph reflection in the same implementation increment.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm current repository state and current GREEN baseline before writing the RED test.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_domain_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py -q || true
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:**

- Branch is `dars`.
- HEAD is at or after `92ed913 feat: record DARS boundary duration`.
- The DARS critic panel focused suite reports `48 passed`.
- The first command surfaces the current codebase/structured-domain baseline; record the number for the Reflection entry. (The exact suite name varies by repo state; use whichever of the three suites exists.)

---

## Task 1: RED — codebase artifact refs flow through `CodeInvestigationLayer`

**Objective:** Pin the M20.1 contract with a failing test in a new file `tests/unit/test_codebase_domain_artifact_bridge.py`. The test must construct a `DomainInvestigationRequest` whose `domain == "codebase"` and whose `sources` carry three `DomainSourceRef` entries — two pointing into `runtime-boundary/codebase-analysis/` and one pointing elsewhere — and assert that the returned `InvestigationWorkProduct` exposes the two codebase-analysis refs as `codebase_artifact_refs` and the third ref as part of `evidence_refs` only.

**Files:**

- Create: `tests/unit/test_codebase_domain_artifact_bridge.py`

**Sketch (adapt to the actual `DomainInvestigationRequest`/`DomainSourceRef` constructor signatures):**

```python
"""M20.1: codebase request can reference local artifact bundle."""

from __future__ import annotations

from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.use_cases import CodeInvestigationLayer
from hisys.schemas.domain_investigation import (
    DomainInvestigationRequest,
    DomainSourceRef,
)


def _build_codebase_request(*, refs: list[tuple[str, str]]) -> DomainInvestigationRequest:
    sources = [
        DomainSourceRef(
            source_id=source_id,
            source_type="runtime_record",
            ref=ref,
            sensitivity="public",
        )
        for source_id, ref in refs
    ]
    return DomainInvestigationRequest(
        request_id="REQ-M20-1",
        domain="codebase",
        objective="codebase: artifact-bridge-acceptance",
        sources=sources,
    )


def test_code_investigation_layer_surfaces_codebase_artifact_refs(tmp_path):
    request = _build_codebase_request(
        refs=[
            ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/inventory.json"),
            ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/symbol-index.json"),
            ("SRC-EVD", "memo://REQ-M20-1/local-research-memos"),
        ],
    )

    layer = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements"))
    work_product = layer.investigate(
        request=request,
        context=DomainUseCaseContext(),
    )

    assert work_product.codebase_artifact_refs == [
        "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/inventory.json",
        "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/symbol-index.json",
    ]
    assert "memo://REQ-M20-1/local-research-memos" in work_product.evidence_refs
    for codebase_ref in work_product.codebase_artifact_refs:
        assert codebase_ref not in work_product.evidence_refs


def test_code_investigation_layer_returns_empty_artifact_refs_when_none_present(tmp_path):
    request = _build_codebase_request(
        refs=[("SRC-EVD", "memo://REQ-M20-1/local-code-and-requirements-memos")],
    )

    layer = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements"))
    work_product = layer.investigate(
        request=request,
        context=DomainUseCaseContext(),
    )

    assert work_product.codebase_artifact_refs == []
    assert "memo://REQ-M20-1/local-code-and-requirements-memos" in work_product.evidence_refs
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py -q
```

**Expected RED:** `AttributeError: 'InvestigationWorkProduct' object has no attribute 'codebase_artifact_refs'` (or `KeyError` if the work product is a `dataclass(frozen=True)` and the test path reaches a field-access guard).

---

## Task 2: GREEN — extend `InvestigationWorkProduct` and `CodeInvestigationLayer`

**Objective:** Minimal production change to make the RED test pass.

**Files:**

- Modify: `src/hisys/domain/layers.py` — add `codebase_artifact_refs: list[str] = field(default_factory=list)` to `InvestigationWorkProduct` immediately after `evidence_refs`; do not change any other field. Update `__all__` only if the dataclass is re-exported.
- Modify: `src/hisys/domain/use_cases.py` — extend `CodeInvestigationLayer.investigate` to compute a deduplicated, order-preserving list of refs from `request.sources` where `source.ref.startswith("runtime-boundary/codebase-analysis/")` and `source.ref` does not contain `".."` segments, and pass the list as `codebase_artifact_refs=...` to the `InvestigationWorkProduct(...)` construction. Refs that match the prefix must NOT be appended to `evidence_refs` to avoid double-counting. Non-matching refs continue to flow through `evidence_refs` exactly as today.

**Implementation sketch (adapt to actual code):**

```python
def _extract_codebase_artifact_refs(request: DomainInvestigationRequest) -> list[str]:
    seen: set[str] = set()
    refs: list[str] = []
    for source in request.sources:
        candidate = source.ref
        if not candidate.startswith("runtime-boundary/codebase-analysis/"):
            continue
        if ".." in candidate.split("/"):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        refs.append(candidate)
    return refs
```

Use `_extract_codebase_artifact_refs(request)` inside `CodeInvestigationLayer.investigate` and split `request.sources` between `evidence_refs` (non-matching `source_id` entries continue to be appended as today) and the new `codebase_artifact_refs` field. Preserve existing `evidence_refs` construction order for any `request.sources` entry that does not match the codebase-analysis subtree.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py -q
PYTHONPATH=src pytest tests/unit/test_domain_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py -q
```

**Expected GREEN:** the two new tests pass; existing domain use-case + structured-adapter + runtime-artifact suites continue to pass. If any existing assertion was depending on a codebase-analysis ref being inside `evidence_refs`, update the assertion to use `codebase_artifact_refs` and document the change in the Reflection entry (this is the only acceptable cross-suite assertion modification in M20.1).

---

## Task 3: Documentation and traceability update

**Objective:** Record the work-product schema field addition and validation anchors.

**Files:**

- Modify: `docs/traceability/README.md`
  - Add a new Implemented-increments row `Codebase domain artifact bundle acceptance (M20.1)` enumerating the `InvestigationWorkProduct.codebase_artifact_refs` field, the extraction rule, the unchanged `evidence_refs` semantics for non-matching refs, the gate commands, and the deferred items (loading, gating, enrichment, CLI flag, full investigation-result surfacing).
- Modify: `ralph.md`
  - Append a Reflection entry covering RED, GREEN, docs, gate result, open items, and resume checkpoint. The entry must explicitly link M20.2/M20.3/M20.4/M20.5 as the planned next increments.
- Optionally modify: an existing codebase-analysis RTM file (e.g., `docs/traceability/README.md` is the primary anchor; if a dedicated domain-adapter RTM file already enumerates `InvestigationWorkProduct` fields it should be bumped in version).

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 4: Full quality gate and local commit

**Objective:** Validate the complete M20.1 implementation and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- New codebase-domain artifact-bridge tests pass.
- Existing domain use-case + structured-adapter + runtime-artifact tests continue to pass.
- DARS critic panel focused suite stays GREEN at the post-M-CP-EXT-9 baseline.
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/domain/layers.py \
  src/hisys/domain/use_cases.py \
  tests/unit/test_codebase_domain_artifact_bridge.py \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: accept codebase artifact bundle refs"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The implementation requires reading codebase-analysis JSON files (that is M20.2/M20.3 scope, not M20.1).
- The implementation requires changing `DomainInvestigationRequest`, `DomainSourceRef`, or `SourceType` field shapes.
- The implementation requires a new CLI flag (deferred to M20.4).
- The implementation requires resolving refs against `instance_root` or creating runtime-boundary artifacts (M20.3 scope).
- Existing domain use-case / structured-adapter / runtime-artifact tests fail for a reason not directly tied to the new `codebase_artifact_refs` field.
- Existing assertions inside the structured-domain or runtime-artifact suites depend on a codebase-analysis ref being present in `evidence_refs` and the migration would change behavior beyond the M20.1 contract (in that case, stop and reduce scope or amend M20.1 controlled-document anchors first).
- Traceability validator, secret scan, or `git diff --check` fails.

## M20.2..M20.5 outlined for follow-on Prepare cycles

- **M20.2 — incomplete bundle preserves formal `needs_more_evidence`:** load `CodebaseReviewBundle` via the existing `load_codebase_review_bundle` chokepoint (with `resolve_instance_runtime_ref` safe-ref enforcement), enumerate missing-schema-id and missing-ref evidence categories, and map an incomplete bundle to formal Hisys `quality_gate="needs_more_evidence"` while keeping `requires_human_review=true`. RED test: missing ref + stale schema id both yield `needs_more_evidence`.
- **M20.3 — complete bundle enriches codebase result:** surface inventory summary, scope-map refs, risk-boundary categories, validation-plan refs, and the advisory-only source-inspection-decision synthesis into `DomainInvestigationResult.investigation_data` without changing the existing `evidence_packages` shape semantics. RED test: a complete bundle returns enriched fields and `quality_gate="passed"`.
- **M20.4 — CLI integration smoke:** add a repeatable `--codebase-artifact-ref` flag (or equivalent bundled-ref argument) to `investigate-domain`, route it into `DomainInvestigationContext` (or directly into `request.sources` if the construction site builds the request), and exercise the path with a fixture artifact bundle. RED test: CLI fixture round persists run-summary refs including the artifact bundle refs and exits 0.
- **M20.5 — docs/gate finish:** update `docs/use-cases/codebase-analysis-design-candidates.md`, public docs, and traceability; record the Hisys milestone push checkpoint per Section 10.3.

## Next increment candidates after M20.1

- M20.2 incomplete-bundle gate.
- Behavior-preserving package split of `src/hisys/agents/dars_panel.py` into adapter/runtime/record modules (deferred since M-CP-EXT-3).
- Future bounded-parallel DARS critic-panel execution activation, only after separate governance/approval and fixture scheduler harness.
