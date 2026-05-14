# Hisys Domain Refactor Supplement Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task after the user approves execution.

**Goal:** Close the remaining implementation-readiness gaps before running the full Ralph loop for `DomainAdapterRegistry -> StructuredDomainAdapter -> DomainUseCase -> three layers`.

**Architecture:** Keep the existing committed plan as the master plan and add this supplement as the execution guardrail for the first implementation phase. The supplement narrows early increments to schema naming, bridge compatibility, runtime artifact acceptance, and CLI postprocessing separation so later example specs can be added without guessing.

**Tech Stack:** Python 3.11, pytest, Pydantic schemas in `src/hisys/schemas/domain_investigation.py`, dataclass/Protocol domain layer model in `src/hisys/domain/*`, existing CLI command implementation in `src/hisys/cli/main.py`.

---

## 1. Current Verified Baseline

Current repository state at planning time:

```text
branch: feat/domain-adaptive-requirements-analysis
HEAD: 6e3d2ea docs: amend domain refactoring ralph readiness plan
working tree: clean
```

Recently verified gates:

```text
focused domain/investment tests: 19 passed
traceability validation: OK
secret scan: hit_count=0
full pytest: 516 passed
```

Relevant current code facts:

- `DomainName = Literal["codebase", "research", "business", "investment", "iso_process", "general"]`.
- `DomainInvestigationRequest` has `domain`, `objective`, `sources`, `constraints`, `output_contract`, `user_focus`, `config_snapshot_refs`, `prompt_bundle_refs`.
- `DomainInvestigationResult` already bridges to `HisysToolResult.from_domain_result(...)`.
- `DomainUseCaseResult.domain` is currently `str`, while schema domain fields are `DomainName`.
- `DomainUseCaseResult` does not yet carry `requires_human_review`, `quality_gate`, `traceability_ids`, or runtime refs directly.
- `_handle_investigate_domain` currently applies `_write_dars_fixture_for_domain_result(...)` and `_write_chief_editor_research_review(...)` to any `domain_result`, so structured generic domains need a guard before they are introduced.

---

## 2. Supplement Objective Function

Optimize for:

1. Ralph can start implementation without inventing missing contract details.
2. Existing research-gap and investment workflows do not regress.
3. Example specs remain specs over a shared adapter, not architecture forks.
4. All new behavior is introduced through RED -> GREEN -> validation -> commit.
5. No live network, mutation, publication, order execution, or credential use is introduced.

Constraints:

```text
- No production code before a failing test.
- No live external action.
- No mutation outside governed runtime-boundary writes.
- Existing DomainInvestigationResult / HisysToolResult compatibility must be preserved.
- Investment governance controls must not weaken.
- Stop after investment example spec migration for midpoint confirmation.
```

---

## 3. Recommended補完 Strategy

Use a short **pre-Ralph hardening phase** before running the main loop.

Recommended option:

```text
Supplement-A: Contract-first hardening
```

Why:

- It uses the current Pydantic schemas instead of replacing them.
- It fixes naming, bridge, artifact, and postprocessing ambiguity before example specs.
- It keeps `research`, `codebase`, and `investment` implementable within current schema constraints.
- It defers first-class `requirements_analysis` until after the midpoint gate unless the user explicitly chooses schema extension.

Rejected for now:

```text
Supplement-B: Add all example specs immediately
```

Reason: would force Ralph to solve bridge, runtime, and CLI postprocessing problems during feature implementation.

```text
Supplement-C: Replace DomainInvestigationResult with a new universal schema
```

Reason: unnecessary migration risk before the shared adapter seam is proven.

---

## 4. Concrete补완 Decisions to Lock Before Code

### Decision D1 — Domain naming

Default decision for first implementation loop:

```text
- `research` remains canonical.
- `investment` remains canonical.
- `development/codebase` uses canonical `domain="codebase"`.
- `development` is not accepted as a direct Pydantic `DomainName` unless a pre-validation normalization seam is intentionally added.
- `requirements-analysis` is deferred past midpoint; if implemented before schema extension, represent it as `domain="codebase"` plus explicit objective convention.
```

Rationale: avoids expanding schema before the bridge and adapter seams are stable.

### Decision D2 — Bridge default

Default bridge behavior:

```text
DomainUseCaseResult
  -> DomainUseCaseArtifactPacket
  -> DomainInvestigationResult
  -> HisysToolResult.from_domain_result(...)
```

Mapping defaults:

```text
hisys_mode.level: stone
quality_gate: needs_more_evidence unless decision layer explicitly marks passed
requires_human_review: decision.requires_human_review
external_call_made: OR of layer flags
mutation_performed: OR of layer flags
traceability_ids: from DomainAdapterSpec, persisted in runtime JSON
```

### Decision D3 — Postprocessing separation

Before adding structured specs, split the current domain-result postprocessing path conceptually:

```text
ResearchGapDomainAdapter result:
  -> existing DARS fixture writer
  -> existing Chief Editor research review writer

StructuredDomainAdapter result:
  -> generic structured runtime writer
  -> no research-specific Chief Editor review unless spec opts in
```

---

## 5. Supplement Task Queue

### Task S0: Record supplement plan and verify baseline

**Objective:** Preserve this supplement and verify it starts from a clean baseline.

**Files:**
- Create: `.hermes/plans/2026-05-14_135745-hisys-domain-refactor-supplement-plan.md`

**Steps:**

1. Save this plan.
2. Run:

```bash
git status --short
git rev-parse --short HEAD
python3 -m pytest tests/unit/test_domain_adapter_registry.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_domain_cli.py tests/unit/test_investment_decision_packet_cli.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected:

```text
working tree clean except this plan before commit
focused tests pass
traceability OK
secret_scan hit_count=0
git diff --check OK
```

Optional commit:

```bash
git add .hermes/plans/2026-05-14_135745-hisys-domain-refactor-supplement-plan.md
git commit -m "docs: add domain refactor supplement plan"
```

---

### Task S1: Lock domain naming strategy with tests

**Objective:** Prevent Ralph from using unsupported `development` or `requirements_analysis` domain values by accident.

**Files:**
- Create: `tests/unit/test_domain_name_strategy.py`
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`
- Modify: `src/hisys/schemas/domain_investigation.py` only if schema extension is explicitly chosen.

**Step 1: Write failing tests**

Test cases:

```python
def test_codebase_is_canonical_development_domain() -> None:
    request = DomainInvestigationRequest(
        request_id="REQ-domain-name-codebase",
        domain="codebase",
        objective="development/codebase evaluation",
        sources=[],
    )
    assert request.domain == "codebase"


def test_development_is_not_direct_domain_without_prevalidation_alias() -> None:
    with pytest.raises(ValidationError):
        DomainInvestigationRequest(
            request_id="REQ-domain-name-development",
            domain="development",
            objective="development/codebase evaluation",
            sources=[],
        )


def test_requirements_analysis_strategy_is_documented_as_codebase_objective_for_first_loop() -> None:
    request = DomainInvestigationRequest(
        request_id="REQ-domain-name-requirements",
        domain="codebase",
        objective="requirements-analysis: identify ambiguity conflict gap unverifiable statements",
        sources=[],
    )
    assert request.domain == "codebase"
    assert "requirements-analysis" in request.objective
```

Traceability: `HISYS-DOM-005`, `HISYS-DOM-006`, `HISYS-DOM-012`.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_name_strategy.py -q
```

Expected: FAIL because the test file does not exist or docs do not yet carry the strategy reference.

**Step 3: Implement minimal docs/test support**

Do not add a schema value unless the user explicitly chooses first-class requirements-analysis. For the default path, only document and test the current schema behavior.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_name_strategy.py -q
python3 scripts/validate_traceability.py
```

**Step 5: Commit**

```bash
git add tests/unit/test_domain_name_strategy.py docs/use-cases/hermes-hisys-domain-tool.md
git commit -m "test: lock domain naming strategy"
```

---

### Task S2: Extend use-case result contract before bridge implementation

**Objective:** Make the three-layer result carry enough information for deterministic schema bridging.

**Files:**
- Modify: `src/hisys/domain/layers.py`
- Modify: `tests/unit/test_domain_three_layer_use_cases.py`

**Step 1: Write failing tests**

Add tests that assert a `DomainUseCaseResult` exposes:

```text
requires_human_review
quality_gate
recommendation_summary
```

and that these are derived from the decision work product without changing layer execution order.

Suggested expected defaults:

```text
requires_human_review=True
quality_gate="needs_more_evidence"
recommendation_summary=decision.recommendation
```

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_three_layer_use_cases.py -q
```

Expected: FAIL because fields are not present.

**Step 3: Implement minimal dataclass fields**

Add fields to `DomainUseCaseResult`; optionally add `quality_gate` to `DecisionWorkProduct` if the test requires decision-layer ownership. Keep default safe and advisory.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_three_layer_use_cases.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/layers.py tests/unit/test_domain_three_layer_use_cases.py
git commit -m "refactor: enrich domain use case result contract"
```

---

### Task S3: Implement bridge contract tests and translator

**Objective:** Prove the central bridge path before structured adapters exist.

**Files:**
- Create: `src/hisys/domain/translation.py`
- Modify: `src/hisys/domain/__init__.py`
- Create: `tests/unit/test_domain_bridge_contract.py`

**Step 1: Write failing tests**

Test behavior:

```text
DomainUseCaseResult -> DomainUseCaseArtifactPacket
DomainUseCaseArtifactPacket -> DomainInvestigationResult
HisysToolResult.from_domain_result(result) succeeds
```

Assertions:

```text
result.investigation_data.hisys_mode.level == "stone"
result.requires_human_review is True
result.external_call_made == packet.external_call_made
result.mutation_performed == packet.mutation_performed
tool_result.runtime_boundary_refs includes generated result ref
tool_result.quality_gate == result.quality_gate
```

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_bridge_contract.py -q
```

Expected: FAIL because `hisys.domain.translation` does not exist.

**Step 3: Implement minimal translator and bridge**

Create:

```text
DomainUseCaseArtifactPacket
DomainUseCaseArtifactTranslator
build_domain_investigation_result(...)
```

The bridge should construct existing Pydantic models:

```text
DomainEvidencePackage
InvestigationDataPackage
CandidateRecord
AlternativeDecisionSet
DomainInvestigationResult
```

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_bridge_contract.py tests/unit/test_domain_three_layer_use_cases.py -q
python3 scripts/validate_traceability.py
```

**Step 5: Commit**

```bash
git add src/hisys/domain/translation.py src/hisys/domain/__init__.py tests/unit/test_domain_bridge_contract.py
git commit -m "refactor: bridge domain use cases to investigation results"
```

---

### Task S4: Add runtime artifact writer acceptance

**Objective:** Make runtime artifact JSON the acceptance boundary for traceability and governance.

**Files:**
- Create: `src/hisys/domain/runtime.py`
- Modify: `src/hisys/domain/__init__.py`
- Create: `tests/unit/test_domain_runtime_artifacts.py`

**Step 1: Write failing tests**

Test with `tmp_path` and deterministic date:

```text
runtime-boundary/domain-investigation/<domain>/<yyyymmdd>/domain-use-case-result-<request_id>.json
runtime-boundary/domain-investigation/<domain>/<yyyymmdd>/domain-use-case-result-<request_id>.md
```

JSON must include:

```text
request_id
domain
layer_trace
artifact_refs
config_snapshot_refs
prompt_bundle_refs
traceability_ids
requires_human_review
external_call_made
mutation_performed
quality_gate
```

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_runtime_artifacts.py -q
```

**Step 3: Implement minimal writer**

Local filesystem only. Write only under `DomainUseCaseContext.boundary_dir` or a child thereof.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_bridge_contract.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/runtime.py src/hisys/domain/__init__.py tests/unit/test_domain_runtime_artifacts.py
git commit -m "feat: persist structured domain runtime artifacts"
```

---

### Task S5: Guard CLI research-specific postprocessing

**Objective:** Prevent structured generic domain results from receiving research-gap-only postprocessing.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Modify/create: `tests/unit/test_domain_cli.py` or `tests/unit/test_domain_postprocessing_guard.py`

**Step 1: Write failing tests**

Test behavior:

```text
- Research-gap objective still invokes existing DARS fixture/Chief Editor research review path.
- A fake structured codebase/investment domain result is persisted without Chief Editor research-review refs.
```

If a fake adapter is easier, inject a test registry or isolate a helper:

```text
_apply_domain_result_postprocessors(adapter_kind="research_gap" | "structured")
```

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_postprocessing_guard.py -q
```

Expected: FAIL because current CLI applies both postprocessors to all `domain_result` values.

**Step 3: Implement minimal separation**

Introduce a small wrapper result or adapter metadata flag only if needed:

```text
DomainInvestigationExecutionResult(kind="research_gap" | "structured", result=DomainInvestigationResult)
```

or a CLI helper that checks the resolved adapter type before applying postprocessors.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_postprocessing_guard.py tests/unit/test_domain_cli.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/cli/main.py tests/unit/test_domain_postprocessing_guard.py tests/unit/test_domain_cli.py
git commit -m "fix: guard research-specific domain postprocessing"
```

---

### Task S6: Add `StructuredDomainAdapter` with fake spec only

**Objective:** Introduce the shared adapter/spec seam without domain-specific implementation complexity.

**Files:**
- Create: `src/hisys/domain/domain_adapters.py`
- Modify: `src/hisys/domain/__init__.py`
- Create: `tests/unit/test_structured_domain_adapter.py`

**Step 1: Write failing tests**

Test behavior:

```text
DomainAdapterSpec contains domain_id, aliases, use_case_factory, translator, writer, traceability_ids, safety_policy.
StructuredDomainAdapter.supports(request) matches canonical domain_id.
StructuredDomainAdapter.investigate(...) builds DomainUseCaseContext from DomainInvestigationContext.
StructuredDomainAdapter returns valid DomainInvestigationResult through the bridge.
Runtime artifact refs are recorded.
```

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_structured_domain_adapter.py -q
```

**Step 3: Implement minimal fake-spec adapter**

No real research/code/investment spec yet. Use fake deterministic use case in the test.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_adapter_registry.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/domain_adapters.py src/hisys/domain/__init__.py tests/unit/test_structured_domain_adapter.py
git commit -m "refactor: add structured domain adapter seam"
```

---

## 6. Gate After Supplement Tasks

After S1-S6 complete, run:

```bash
python3 -m pytest \
  tests/unit/test_domain_name_strategy.py \
  tests/unit/test_domain_three_layer_use_cases.py \
  tests/unit/test_domain_bridge_contract.py \
  tests/unit/test_domain_runtime_artifacts.py \
  tests/unit/test_domain_postprocessing_guard.py \
  tests/unit/test_structured_domain_adapter.py \
  tests/unit/test_domain_adapter_registry.py \
  tests/unit/test_domain_cli.py \
  tests/unit/test_investment_decision_packet_cli.py \
  -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest -q
git status --short
```

Expected:

```text
all focused tests pass
traceability OK
secret_scan hit_count=0
git diff --check OK
full pytest pass
working tree clean after commits
```

If this gate passes, start the master plan at example-spec registration:

```text
Master Increment 5: research + development/codebase example specs
Master Increment 6: investment example spec migration
Then stop for midpoint user confirmation.
```

---

## 7. Ralph Stop Conditions for Supplement Phase

Stop and report if any condition occurs:

```text
- same supplement task fails RED/GREEN cycle three times;
- bridge cannot create a valid DomainInvestigationResult without schema migration;
- HisysToolResult.from_domain_result(...) cannot preserve safety fields;
- CLI postprocessing guard requires broad CLI rewrite;
- secret scan hit_count > 0;
- traceability validation fails and cannot be fixed in the same small increment;
- git diff --check fails;
- any live network, mutation, publication, order execution, or credential path appears;
- investment governance defaults change.
```

---

## 8. Open Questions for User Gate

These do not block S1-S6 if the default choices above are accepted:

1. Should `requirements_analysis` become a first-class `DomainName`, or remain `domain="codebase"` with an objective/subtype convention until after midpoint?
2. Should `development` be a user-facing pre-validation alias, or should users always send `domain="codebase"`?
3. Should structured domain runtime artifacts live under the current CLI `boundary_dir` or under `boundary_dir/domain-investigation/<domain>/<yyyymmdd>/`? The supplement recommends the latter for structured adapter artifacts while preserving existing CLI result artifacts.

Recommended defaults for first implementation loop:

```text
requirements-analysis: defer first-class schema value
development: use codebase canonical domain
structured artifacts: write under boundary_dir/domain-investigation/<domain>/<yyyymmdd>/ and reference from existing HisysToolResult refs
```
