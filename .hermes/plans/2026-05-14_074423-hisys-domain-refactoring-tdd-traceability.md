# Hisys Domain Refactoring Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task if execution is approved. Use strict TDD and keep each increment committed separately.

**Goal:** Refactor Hisys into a traceable, governed, domain-adaptive decision-support substrate where research, development/codebase, investment, and requirements-analysis are example domain adapters/specs that all run through the same investigation, aggregation, and decision layer structure.

**Architecture:** Keep `DomainAdapterRegistry` as the CLI dispatch seam. Keep `DomainUseCase` as the internal use-case seam composed of `InvestigationLayer -> AggregationLayer -> DecisionLayer`. Add a generic example/domain adapter composition mechanism so research, development/codebase, investment, and requirements-analysis register as specs over the same adapter/use-case pipeline. Domain-specific products such as investment packets remain concrete work products owned by their layers, not separate CLI special cases.

**Tech Stack:** Python 3.11, dataclasses, Protocol interfaces, Pydantic schemas, pytest, local runtime-boundary artifacts, Hisys traceability/secret-scan scripts.

---

## 1. Current Context

Current branch:

```text
feat/domain-adaptive-requirements-analysis
```

Current recent commits:

```text
46d565a refactor: define three-layer domain use cases
fe12eed refactor: add domain investigation adapter registry
```

Current implementation anchors:

- `src/hisys/domain/adapters.py`
  - `DomainInvestigationContext`
  - `DomainInvestigationAdapter`
  - `DomainAdapterRegistry`
- `src/hisys/domain/layers.py`
  - `DomainUseCaseContext`
  - `InvestigationLayer`
  - `AggregationLayer`
  - `DecisionLayer`
  - `DomainUseCase`
  - work-product records
- `src/hisys/domain/use_cases.py`
  - `ResearchAnalysisUseCase`
  - `CodeAnalysisUseCase`
  - `ResearchInvestigationLayer`
  - `CodeInvestigationLayer`
  - `MemoReportAggregationLayer`
  - `DarsDecisionLayer`
- `src/hisys/cli/main.py`
  - `_handle_investigate_domain(...)`
  - `_ResearchGapDomainAdapter`
  - `_default_domain_adapter_registry(...)`
- `docs/use-cases/hermes-hisys-domain-tool.md`
  - documents the three-layer model and registry implications.

Existing investment anchors that must be treated as migration inputs, not new
greenfield work:

- `src/hisys/schemas/investment.py`
  - `InvestmentDecisionPacket`
  - `InvestmentSignal`
  - `InvestmentWeightPolicy`
  - `HumanApprovalGate`
  - `ScenarioAssessment`
  - `OrderTicketDraft`
- `src/hisys/investigator/agents.py`
  - `InvestmentDecisionSupportAgent`
- `src/hisys/cli/main.py`
  - `build-investment-decision-packet`
  - `build-investment-evidence-package`
  - `run-investment-decision-dry-run`
- `tests/unit/test_investment_decision_packet_schema.py`
- `tests/unit/test_investment_decision_packet_cli.py`

Investment is therefore a **migration domain** for this refactor. The existing
product workflow already covers human approval, weight policy, dry-run packet
assembly, source-evidence ingestion, and no-autonomous-execution boundaries. The
refactor should wrap/reuse those products through `InvestmentAnalysisUseCase`
and `investment_spec` registered behind the shared `StructuredDomainAdapter` rather than rebuilding them.

Current validation baseline from the prior increment:

```text
python3 -m pytest -q
# 516 passed

python3 scripts/validate_traceability.py
# OK

python3 scripts/scan_secrets.py
# hit_count=0
```

## 2. Refactoring Principles

1. **TDD-first:** No production behavior without a failing test first.
2. **Traceability-first:** Every increment must cite requirement/design IDs or introduce controlled IDs in tests, docstrings, and docs.
3. **Governed boundaries:** External calls and mutations stay disabled unless a later approved connector policy and human approval gate exist.
4. **Small increments:** One coherent behavior per commit.
5. **Adapter/use-case separation:**
   - Adapter answers: which domain owns this CLI request and how does it translate into Hisys artifacts?
   - Use case answers: how do investigation, aggregation, and decision layers execute for that domain?
6. **Evidence before decision:** Decision layer must consume aggregation output; it must not collect evidence directly.
7. **DARS advisory-only:** DARS output may recommend, request evidence, or critique; it must not execute, publish, mutate, or approve final actions.
8. **Runtime boundary records:** Every CLI-visible domain workflow must preserve request, layer trace, artifact refs, config/policy refs, and safety flags.
9. **Example adapters are specs, not architecture forks:** research, development/codebase, investment, and requirements-analysis should be registered through a common adapter/use-case structure. Domain-specific classes may do the work inside layers, but dispatch, trace, translation, artifact writing, and safety gates should be shared.

## 3. DOE-Informed Design Alternatives

### Alternative A — Continue adding special cases in `src/hisys/cli/main.py`

- **Pros:** fastest local change.
- **Cons:** poor maintainability; weak OOP boundary; traceability scattered in CLI; domain growth will increase branching.
- **Verdict:** reject except for temporary compatibility shims.

### Alternative B — Each domain gets a bespoke adapter class that calls a concrete `DomainUseCase`

- **Pros:** preserves current CLI contract; keeps adapter dispatch and domain execution separate; easy to implement one domain at a time.
- **Cons:** can still duplicate routing, translation, artifact writing, and safety checks across research/development/investment/requirements.
- **Verdict:** acceptable as a transitional step only; not the final structure.

### Alternative C — Replace current schemas with a new universal domain result schema immediately

- **Pros:** cleaner long-term schema.
- **Cons:** larger migration; high regression risk; may disrupt existing research-gap fixtures and CLI tests.
- **Verdict:** defer until adapter/use-case integration is stable.

### Alternative D — Build live source connectors immediately

- **Pros:** demonstrates full workflow sooner.
- **Cons:** violates fixture-first/no-live-action discipline; increases governance and secret risk.
- **Verdict:** defer until local/fake connector harnesses and traceability pass.

### Alternative E — Generic structured domain adapter with example domain specs

- **Pros:** treats research, development/codebase, investment, and requirements-analysis as example adapters/specs over one common structure; centralizes dispatch, translation, artifact writing, traceability, and safety gates; preserves domain-specific layer implementations and existing product schemas.
- **Cons:** requires a small spec/factory seam before wiring all examples.
- **Verdict:** recommended next path. Use bespoke adapters only for legacy compatibility shims such as the existing research-gap fixture path.

Recommended architecture for the next refactoring sequence: **Alternative E**, with schema generalization and live connectors deferred.

## 4. Traceability Model to Add

Introduce or document controlled IDs for this refactor. If the repo already has a controlled requirements register, add these there; otherwise document them first in `docs/use-cases/hermes-hisys-domain-tool.md` and tests/docstrings.

Suggested IDs:

| ID | Requirement / Decision | Acceptance evidence |
|---|---|---|
| `HISYS-DOM-001` | Domain CLI dispatch resolves an ordered adapter registry. | `tests/unit/test_domain_adapter_registry.py` |
| `HISYS-DOM-002` | Domain use cases execute `investigation -> aggregation -> decision` in order. | `tests/unit/test_domain_three_layer_use_cases.py` |
| `HISYS-DOM-003` | Domain adapters translate use-case work products into Hisys runtime artifacts. | New adapter integration tests |
| `HISYS-DOM-004` | Research workflow searches local memos plus approved/planned publisher evidence. | Research adapter tests and artifact refs |
| `HISYS-DOM-005` | Codebase workflow searches local memos plus local requirements/code evidence. | Codebase adapter tests and artifact refs |
| `HISYS-DOM-006` | Requirements-analysis workflow creates requirement-candidate, ambiguity/conflict/gap/verifiability evidence. | Requirements adapter tests |
| `HISYS-DOM-007` | Aggregation layer produces a memo/report artifact with source memo/evidence refs. | Artifact persistence tests |
| `HISYS-DOM-008` | Decision layer runs DARS as advisory-only with human review required. | DARS boundary tests |
| `HISYS-DOM-009` | External calls and mutations are disabled by default and recorded as false. | Safety flag tests and secret scan |
| `HISYS-DOM-010` | Runtime boundary records include request ID, layer trace, artifact refs, config refs, and traceability IDs. | Runtime artifact JSON/MD tests |
| `HISYS-DOM-011` | Existing investment decision-support products are migrated into the three-layer domain adapter model without weakening human approval, dry-run, not-financial-advice, no-autonomous-execution, or source-evidence controls. | Investment migration adapter tests plus existing `test_investment_decision_packet_*` tests |
| `HISYS-DOM-012` | Research, development/codebase, investment, and requirements-analysis are example domain specs/adapters registered through a shared adapter/use-case pipeline rather than independent architecture forks. | Generic adapter/spec tests plus CLI acceptance tests for each example domain |

Each new test file should include a docstring like:

```python
"""Tests for <feature>.

Traceability: HISYS-DOM-003, HISYS-DOM-007, HISYS-DOM-010.
"""
```

Each production module touched for this refactor should include or preserve a `Traceability:` docstring line.


## 5. Developer Guide: Adding a New Domain Adapter from the Examples

The examples are intended to be copied as **domain specs**, not as new architecture
branches. A developer adding a new domain should follow this path:

```text
1. Define the domain's three concrete layers.
   - <Domain>InvestigationLayer
   - <Domain>AggregationLayer
   - <Domain>DecisionLayer

2. Compose them as a DomainUseCase.
   - <Domain>AnalysisUseCase

3. Register the use case through DomainAdapterSpec.
   - domain_id
   - aliases
   - use_case_factory
   - translator
   - runtime artifact writer
   - traceability_ids
   - safety policy

4. Let StructuredDomainAdapter handle common behavior.
   - supports(request)
   - run use case
   - translate result
   - persist runtime-boundary artifacts
   - preserve layer trace
   - preserve safety flags

5. Add tests before implementation.
   - use-case test: layer order and domain-specific work products
   - spec test: domain/alias resolution and shared adapter routing
   - CLI acceptance test: artifact output and traceability IDs
   - governance test: no unapproved external call or mutation
```

A new domain should not add a new CLI branch unless it is a compatibility shim for
an existing product workflow. The common extension point is the spec registration,
not `if domain == ...` logic in the CLI.

Minimal intended shape:

```python
@dataclass(frozen=True)
class DomainAdapterSpec:
    domain_id: str
    aliases: tuple[str, ...]
    use_case_factory: Callable[[], DomainUseCase]
    translator: DomainUseCaseArtifactTranslator
    artifact_writer: DomainRuntimeArtifactWriter
    traceability_ids: tuple[str, ...]
    safety_policy: DomainSafetyPolicy

class StructuredDomainAdapter(DomainInvestigationAdapter):
    def supports(self, request: DomainInvestigationRequest) -> bool:
        return request.domain in {self.spec.domain_id, *self.spec.aliases}

    def investigate(self, context: DomainInvestigationContext) -> DomainInvestigationResult:
        result = self.spec.use_case_factory().run(context.request, context.use_case_context)
        packet = self.spec.translator.translate(result, traceability_ids=self.spec.traceability_ids)
        refs = self.spec.artifact_writer.write(packet, context.use_case_context)
        return to_domain_investigation_result(packet, refs)
```

Example domains should document what changes and what stays common:

| Domain spec | Domain-specific parts | Common parts |
|---|---|---|
| `research_spec` | research local memo/publisher evidence layers; `research_review` decision type | dispatch, translation, artifact writing, trace IDs, safety flags |
| `development_or_codebase_spec` | requirements/code evidence layers; `code_evaluation_review` decision type | dispatch, translation, artifact writing, trace IDs, safety flags |
| `investment_spec` | existing `InvestmentDecisionPacket`, weight policy, dry-run, human approval refs | dispatch, translation, artifact writing, trace IDs, safety flags |
| `requirements_analysis_spec` | requirement candidate/ambiguity/conflict/gap/verifiability layers | dispatch, translation, artifact writing, trace IDs, safety flags |

Checklist for a new third-party/custom domain:

```text
[ ] Add <Domain>InvestigationLayer, <Domain>AggregationLayer, <Domain>DecisionLayer.
[ ] Add <Domain>AnalysisUseCase that preserves investigation -> aggregation -> decision order.
[ ] Add <domain>_spec using DomainAdapterSpec.
[ ] Register the spec in the default domain adapter registry factory.
[ ] Add tests with a Traceability: HISYS-DOM-* docstring.
[ ] Assert safety defaults: no external call, no mutation, human review required when decision is advisory.
[ ] Assert runtime artifact JSON includes request ID, domain, layer trace, artifact refs, safety flags, and traceability IDs.
[ ] Run focused tests, traceability validation, secret scan, diff check, and full pytest.
```


## 6. Layer Customization Matrix for Currently Identified Domains

The shared adapter/spec mechanism should make only the layer internals and domain
metadata customizable. The adapter pipeline itself should remain common.

Common across all domains:

```text
DomainAdapterRegistry
StructuredDomainAdapter.supports()
StructuredDomainAdapter.investigate()
DomainUseCase.run() order: investigation -> aggregation -> decision
DomainUseCaseArtifactTranslator
DomainRuntimeArtifactWriter
traceability ID injection
safety flag propagation
runtime-boundary artifact schema
no-live-action defaults
```

Customizable per domain:

```text
domain_id / aliases
source policies and allowed local roots
InvestigationLayer implementation
AggregationLayer implementation
DecisionLayer implementation or decision_type
extra domain work-product refs
human-review and approval policy labels
traceability IDs
```

| Domain spec | Investigation customization | Aggregation customization | Decision customization | Must remain common / governed |
|---|---|---|---|---|
| `research_spec` | Search local research/memo roots such as `/home/cbchoi/me`; select publisher/source refs; preserve source IDs from `DomainInvestigationRequest.sources`; no live publisher query unless approved. | Produce a research memo aggregation report; group evidence by question, paper/source, gap, and claim; preserve citation/source refs. | DARS advisory review with `decision_type="research_review"`; evaluate evidence gap, paper/report readiness, source sufficiency; human review required. | Same structured adapter, translator, artifact writer, layer trace, safety flags. |
| `development_or_codebase_spec` | Search local memo roots plus requirements/code roots; collect requirement refs, code inventory refs, test/static-analysis refs when available; no repo mutation. | Produce codebase/development evaluation report; aggregate requirements-to-code evidence, risk findings, test evidence, and traceability gaps. | DARS advisory review with `decision_type="code_evaluation_review"`; evaluate change risk, evidence sufficiency, requirements coverage, and recommended human next action. | Same structured adapter, translator, artifact writer, layer trace, safety flags; no code modification by investigation/evaluation workflow. |
| `investment_spec` | Reuse existing `InvestmentDecisionSupportAgent`/source-evidence package refs; collect thesis/risk/scenario evidence; reject fixture-backed product dry-runs where existing policy requires source evidence. | Reuse or reference existing investment packet/report products: `InvestmentDecisionPacket`, signal set, weight policy, scenario assessment, evidence chain. | Reuse existing investment dry-run/advisory boundary; preserve not-financial-advice, no-autonomous-execution, `execution_authorized=false`, `publication_or_live_action_approved=false`, human approval gate. | Same structured adapter, translator, artifact writer, layer trace, safety flags; existing investment schema/CLI tests remain authoritative. |
| `requirements_analysis_spec` | Search stakeholder statements, requirements folders, local memos, and controlled requirement docs; extract candidate requirement refs and issue refs for ambiguity/conflict/gap/unverifiable statements. | Produce requirements analysis report; group candidates by requirement, source, ambiguity/conflict/gap/verifiability issue, and needed clarification. | DARS advisory review with `decision_type="requirements_review"`; evaluate requirement quality and request human clarification/approval. | Same structured adapter, translator, artifact writer, layer trace, safety flags. |

Reserved schema domains currently visible in `DomainName` but not yet first-class
example specs:

| Domain | Current treatment |
|---|---|
| `business` | Reserved. Add a `business_spec` later by following the same three-layer/spec checklist. |
| `iso_process` | Reserved. Add an `iso_process_spec` later; likely investigation over process docs/audit evidence, aggregation into compliance report, decision into advisory process review. |
| `general` | Compatibility/fallback only. Avoid making it a catch-all that bypasses traceability; prefer explicit domain specs. |

Acceptance tests should verify that domain-specific customization appears only in
layer work products and spec metadata, while the adapter pipeline and runtime
artifact shape remain unchanged across examples.

## 7. Ralph-Loop Readiness Amendments from Codex/Claude Review

Codex and Claude both classified the plan as `READY_AFTER_FIXES` for a Ralph/autonomous implementation loop. The following amendments are mandatory before production-code implementation starts. They convert the design plan into an executable loop contract.

### 7.1 Domain naming and schema strategy

Current `DomainName` accepts only:

```text
codebase, research, business, investment, iso_process, general
```

Therefore `development`, `requirements`, or `requirements_analysis` cannot be passed directly in a `DomainInvestigationRequest` unless schema is extended before request construction. The recommended Ralph-loop decision is:

```text
- Keep `development_or_codebase_spec` registered under canonical domain_id=`codebase`.
- Treat `development` as a pre-Pydantic CLI/user alias only if an input-normalization seam exists before `DomainInvestigationRequest` validation.
- Add `requirements_analysis` to `DomainName` only if the requirements-analysis workflow must be first-class at the schema level. Otherwise represent it as domain=`codebase` plus objective/subtype metadata.
```

The first executable increment after the plan commit must resolve this choice with tests. Do not let Ralph infer the naming strategy from prose.

### 7.2 Bridge contract required before structured adapters

The structured adapter must return the existing Pydantic result type. The required bridge is:

```text
DomainUseCaseResult
  -> DomainUseCaseArtifactPacket
  -> DomainInvestigationResult
  -> HisysToolResult.from_domain_result(...)
```

The bridge contract must define deterministic mappings for:

```text
investigation_data.investigation_id
investigation_data.evidence_packages
investigation_data.runtime_boundary_refs
investigation_data.hisys_mode.level
alternative_decision_set
recommendation_summary
dars_refs
runtime_boundary_refs
quality_gate
requires_human_review
external_call_made
mutation_performed
traceability_ids in persisted runtime artifact JSON
```

Default `HisysMode.level` must be explicit. Use `stone` unless a later governed increment creates a complete `EvidenceChainRecord`; this avoids unexpected validation failures for `claim`, `synthesis`, `decision`, or `publication` levels.

### 7.3 Context construction rule

`DomainInvestigationContext` is the adapter-facing context and `DomainUseCaseContext` is the layer-facing context. The structured adapter must own a deterministic conversion, for example:

```python
def build_use_case_context(context: DomainInvestigationContext) -> DomainUseCaseContext:
    return DomainUseCaseContext(
        instance_root=context.instance_root,
        boundary_dir=context.boundary_dir,
        yyyymmdd=context.yyyymmdd,
    )
```

The current `DomainInvestigationContext` already exposes `instance_root`, `boundary_dir`, and `yyyymmdd`; the context-builder test should lock this mapping so future adapter changes do not recreate ad-hoc runtime paths. Tests should use `tmp_path` and deterministic dates only.

### 7.4 CLI post-processing guard

Legacy research-gap behavior may keep research-specific postprocessors such as DARS fixture or Chief Editor research review writers. Structured example specs must not accidentally receive research-gap-only semantics. The plan requires a guard:

```text
_ResearchGapDomainAdapter path -> existing research-gap postprocessors
StructuredDomainAdapter path -> generic/domain-specific runtime refs only
```

Add tests proving investment/codebase/requirements structured results do not get research-only review refs unless their spec explicitly requests an equivalent domain-specific review artifact.

### 7.5 Runtime traceability and governance propagation

Runtime artifact JSON is the acceptance boundary for the Ralph loop. Each structured-domain runtime JSON must include:

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

Tests must prove safety/governance flags propagate from layer work products through packet, persisted artifact, `DomainInvestigationResult`, and `HisysToolResult`.

### 7.6 Investment migration acceptance

Investment is not greenfield. The migration acceptance must require artifact-level evidence that existing controls are preserved:

```text
- output refs include `InvestmentDecisionPacket` or an existing dry-run report artifact ref;
- output refs include `InvestmentWeightPolicy` and `HumanApprovalGate` where applicable;
- `execution_authorized=false`;
- `publication_or_live_action_approved=false`;
- not-financial-advice/no-autonomous-execution wording remains present;
- fixture-backed product dry-run rejection remains covered by existing investment tests;
- no order execution, publication, network call, or credential use is introduced.
```

### 7.7 Ralph stop conditions

An autonomous Ralph loop must stop and report instead of continuing when any condition occurs:

```text
- the same increment reaches RED or non-green validation three times;
- `python3 scripts/scan_secrets.py` reports hit_count > 0;
- `python3 scripts/validate_traceability.py` fails;
- `git diff --check` fails;
- any live network, publication, order execution, or mutation path is enabled;
- any layer/result/tool artifact reports `mutation_performed=true` or unapproved `external_call_made=true`;
- investment governance regresses: execution_authorized or publication_or_live_action_approved becomes true by default;
- the next step crosses the Increment 6 midpoint gate without user confirmation.
```

## 8. Increment Plan

### Increment 0: Baseline verification and plan commit

**Objective:** Establish a clean baseline and save this plan.

**Files:**
- Create: `.hermes/plans/2026-05-14_074423-hisys-domain-refactoring-tdd-traceability.md`

**Commands:**

```bash
git branch --show-current
git status --short
python3 -m pytest tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_domain_adapter_registry.py tests/unit/test_domain_cli.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** focused tests pass; traceability OK; secret scan hit_count=0; no whitespace errors.

**Commit:** optional plan-only commit if desired:

```bash
git add .hermes/plans/2026-05-14_074423-hisys-domain-refactoring-tdd-traceability.md
git commit -m "docs: plan domain refactoring traceability"
```

---

### Increment 0.5: Decide and test domain naming/schema strategy

**Objective:** Remove schema ambiguity before Ralph creates example specs. Decide whether requirements-analysis and development are first-class `DomainName` values or aliases/objective subtypes under existing schema values.

**Recommended decision for the first Ralph loop:**

```text
- Canonical development/codebase domain: `codebase`.
- Optional user-facing alias: `development`, normalized before `DomainInvestigationRequest` validation.
- Requirements-analysis: choose one explicitly before implementation:
  A. add `requirements_analysis` to `DomainName`; or
  B. represent it as domain=`codebase` plus an explicit objective/subtype field or objective convention.
```

**Files:**
- Modify: `src/hisys/schemas/domain_investigation.py` only if Option A is chosen.
- Modify: `src/hisys/cli/main.py` or adapter input-normalization seam only if aliases are supported before Pydantic validation.
- Create: `tests/unit/test_domain_name_strategy.py`.
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`.

**Step 1: Write failing schema/alias strategy test**

Test behavior:

- A request with canonical `domain="codebase"` is valid and routes to the development/codebase spec later.
- `development` is either rejected by schema or normalized before request construction; the chosen behavior is explicit.
- Requirements-analysis strategy is explicit:
  - Option A: `domain="requirements_analysis"` validates; or
  - Option B: `domain="codebase"` plus objective/subtype convention validates and is documented.

Traceability: `HISYS-DOM-005`, `HISYS-DOM-006`, `HISYS-DOM-012`.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_name_strategy.py -q
```

Expected: FAIL until the chosen schema/alias behavior is implemented or documented in a testable way.

**Step 3: Implement minimal schema/alias decision**

Do not add broad schema migration. Make only the smallest change needed for the chosen strategy.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_name_strategy.py tests/unit/test_domain_adapter_registry.py -q
python3 scripts/validate_traceability.py
```

**Step 5: Commit**

```bash
git add src/hisys/schemas/domain_investigation.py src/hisys/cli/main.py tests/unit/test_domain_name_strategy.py docs/use-cases/hermes-hisys-domain-tool.md
git commit -m "refactor: define domain naming strategy"
```

---

### Increment 1: Add explicit traceability IDs for the domain refactor

**Objective:** Make the domain refactor traceable through controlled IDs before adding more behavior.

**Files:**
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`
- Modify: `src/hisys/domain/adapters.py`
- Modify: `src/hisys/domain/layers.py`
- Modify: `src/hisys/domain/use_cases.py`
- Modify: `tests/unit/test_domain_adapter_registry.py`
- Modify: `tests/unit/test_domain_three_layer_use_cases.py`

**Step 1: Write failing traceability test**

Create or extend a unit test that asserts all domain modules/tests contain the new `HISYS-DOM-*` traceability IDs. Prefer a lightweight repository-content test if existing traceability script does not enforce this.

Suggested file:

```text
tests/unit/test_domain_traceability_ids.py
```

Test intent:

```python
def test_domain_refactor_modules_carry_traceability_ids() -> None:
    paths = [
        Path("src/hisys/domain/adapters.py"),
        Path("src/hisys/domain/layers.py"),
        Path("src/hisys/domain/use_cases.py"),
        Path("tests/unit/test_domain_adapter_registry.py"),
        Path("tests/unit/test_domain_three_layer_use_cases.py"),
    ]
    for path in paths:
        text = path.read_text()
        assert "Traceability:" in text
        assert "HISYS-DOM-" in text
```

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_traceability_ids.py -q
```

Expected: FAIL because current files cite existing IDs but not the new `HISYS-DOM-*` IDs.

**Step 3: Implement minimal docs/docstring changes**

- Add the traceability table in `docs/use-cases/hermes-hisys-domain-tool.md`.
- Add relevant `HISYS-DOM-*` IDs to module/test docstrings.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_traceability_ids.py -q
python3 scripts/validate_traceability.py
```

**Step 5: Commit**

```bash
git add docs/use-cases/hermes-hisys-domain-tool.md src/hisys/domain/adapters.py src/hisys/domain/layers.py src/hisys/domain/use_cases.py tests/unit/test_domain_traceability_ids.py tests/unit/test_domain_adapter_registry.py tests/unit/test_domain_three_layer_use_cases.py
git commit -m "docs: add domain refactor traceability ids"
```

---

### Increment 2: Add use-case artifact packet and `DomainInvestigationResult` bridge contract

**Objective:** Define and test the complete bridge from three-layer use-case work products into existing Hisys result schemas, ending at `HisysToolResult.from_domain_result(...)`. This increment must close the schema contract before `StructuredDomainAdapter` exists.

**Files:**
- Create: `src/hisys/domain/translation.py`
- Modify: `src/hisys/domain/__init__.py`
- Create: `tests/unit/test_domain_use_case_translation.py`
- Create or modify: `tests/unit/test_domain_bridge_contract.py`

**Step 1: Write failing bridge tests**

Test behavior:

- Given a deterministic `DomainUseCaseResult`, translator returns `DomainUseCaseArtifactPacket`.
- Packet includes request ID, domain, layer trace, investigation refs, aggregation report ref, decision ref, memo/evidence refs, safety flags, human-review flag, quality gate, and traceability IDs.
- `to_domain_investigation_result(packet, request, runtime_refs)` returns a valid `DomainInvestigationResult`.
- `HisysToolResult.from_domain_result(result)` succeeds.
- `InvestigationDataPackage.hisys_mode.level` is explicitly `stone` unless a complete evidence chain is provided.
- `external_call_made`, `mutation_performed`, and `requires_human_review` are preserved from layer result -> packet -> result -> tool result.
- Runtime traceability IDs are available for the artifact writer even though the writer is implemented in the next increment.

Suggested test names:

```python
def test_use_case_result_bridges_to_domain_investigation_result() -> None:
    ...

def test_bridge_preserves_governance_flags_and_human_review() -> None:
    ...
```

Traceability: `HISYS-DOM-003`, `HISYS-DOM-009`, `HISYS-DOM-010`, `HISYS-DOM-012`.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_use_case_translation.py tests/unit/test_domain_bridge_contract.py -q
```

Expected: FAIL because `hisys.domain.translation`, `DomainUseCaseArtifactPacket`, and the result bridge do not exist.

**Step 3: Implement minimal bridge**

Suggested shape:

```python
@dataclass(frozen=True)
class DomainUseCaseArtifactPacket:
    request_id: str
    domain: str
    layer_trace: list[LayerTraceStep]
    investigation_ref: str
    aggregation_report_ref: str
    decision_ref: str
    memo_refs: list[str]
    evidence_refs: list[str]
    runtime_boundary_refs: list[str]
    traceability_ids: tuple[str, ...]
    recommendation_summary: str
    quality_gate: Literal["passed", "needs_more_evidence", "failed"]
    requires_human_review: bool
    external_call_made: bool
    mutation_performed: bool

class DomainUseCaseArtifactTranslator:
    def translate(
        self,
        result: DomainUseCaseResult,
        *,
        traceability_ids: tuple[str, ...],
    ) -> DomainUseCaseArtifactPacket:
        ...

def to_domain_investigation_result(
    packet: DomainUseCaseArtifactPacket,
    request: DomainInvestigationRequest,
    *,
    runtime_boundary_refs: list[str],
) -> DomainInvestigationResult:
    ...
```

Do not introduce a new universal result schema in this increment. The bridge must satisfy the existing Pydantic models in `src/hisys/schemas/domain_investigation.py`.

**Step 4: Verify GREEN**

```bash
python3 -m pytest \
  tests/unit/test_domain_use_case_translation.py \
  tests/unit/test_domain_bridge_contract.py \
  tests/unit/test_domain_three_layer_use_cases.py \
  -q
python3 scripts/validate_traceability.py
```

**Step 5: Commit**

```bash
git add src/hisys/domain/translation.py src/hisys/domain/__init__.py tests/unit/test_domain_use_case_translation.py tests/unit/test_domain_bridge_contract.py
git commit -m "refactor: bridge domain use cases to investigation results"
```

---

### Increment 3: Add file-backed runtime artifact writer for three-layer use cases

**Objective:** Persist the translated domain use-case packet under `runtime-boundary/domain-investigation/<domain>/<YYYYMMDD>/`.

**Files:**
- Create: `src/hisys/domain/runtime.py`
- Modify: `src/hisys/domain/__init__.py`
- Create: `tests/unit/test_domain_runtime_artifacts.py`

**Step 1: Write failing test**

Test behavior:

- Writer receives a packet and `DomainUseCaseContext`.
- Writer creates JSON and Markdown artifacts.
- JSON includes request ID, domain, layer trace, artifact refs, config snapshot refs, prompt bundle refs, external/mutation flags, human-review flag, quality gate, and traceability IDs.
- Markdown includes a human-readable summary and “human review required” decision status.

Expected files:

```text
runtime-boundary/domain-investigation/<domain>/<YYYYMMDD>/domain-use-case-result-<request_id>.json
runtime-boundary/domain-investigation/<domain>/<YYYYMMDD>/domain-use-case-result-<request_id>.md
```

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_runtime_artifacts.py -q
```

Expected: FAIL because runtime writer does not exist.

**Step 3: Implement minimal writer**

Keep it local-only. Do not perform external calls. Do not mutate outside the runtime boundary passed in context. Tests must use `tmp_path` and deterministic `yyyymmdd`. The writer must persist the packet fields used by the Increment 2 bridge, not a separate ad-hoc shape.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_use_case_translation.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/runtime.py src/hisys/domain/__init__.py tests/unit/test_domain_runtime_artifacts.py
git commit -m "feat: persist domain use case runtime artifacts"
```

---

### Increment 4: Add generic structured domain adapter/spec seam behind `DomainAdapterRegistry`

**Objective:** Add a shared adapter/spec seam so example domains can be registered without duplicating dispatch, translation, artifact writing, traceability, and safety checks.

**Files:**
- Create: `src/hisys/domain/domain_adapters.py`
- Modify: `src/hisys/domain/__init__.py`
- Modify: `src/hisys/cli/main.py`
- Create: `tests/unit/test_structured_domain_adapter.py`
- Modify: `tests/unit/test_domain_cli.py` only if CLI behavior needs a fixture assertion.

**Step 1: Write failing adapter/spec test**

Test behavior:

- A `DomainAdapterSpec` binds a domain id, aliases, use-case factory, translator, artifact writer, traceability IDs, and safety policy.
- A `StructuredDomainAdapter` supports requests whose domain matches the spec.
- `investigate(...)` builds `DomainUseCaseContext` deterministically from `DomainInvestigationContext`, calls the spec's `DomainUseCase`, translates/persists the result, bridges to `DomainInvestigationResult`, and returns the existing schema type.
- Safety flags remain false unless a layer explicitly reports otherwise.
- Layer trace order is preserved.
- Test uses a small fake use case first; research/development/investment specs are wired in later increments.
- Legacy `_ResearchGapDomainAdapter` remains first in registry precedence for existing research-gap objective patterns.
- Structured generic-domain results do not invoke research-gap-only postprocessors such as Chief Editor research review unless explicitly requested by the spec.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_structured_domain_adapter.py -q
```

Expected: FAIL because `DomainAdapterSpec` / `StructuredDomainAdapter` does not exist.

**Step 3: Implement minimal structured adapter seam**

Suggested classes/helpers:

```text
DomainAdapterSpec
StructuredDomainAdapter
DomainAdapterSpecRegistryFactory
build_use_case_context(context: DomainInvestigationContext) -> DomainUseCaseContext
```

Recommended order in default registry after example specs are wired:

```text
1. _ResearchGapDomainAdapter       # preserve existing specific fixture path
2. StructuredDomainAdapter(research_spec)
3. StructuredDomainAdapter(development_or_codebase_spec)
4. StructuredDomainAdapter(investment_spec)
5. StructuredDomainAdapter(requirements_analysis_spec)
```

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_adapter_registry.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/domain_adapters.py src/hisys/domain/__init__.py tests/unit/test_structured_domain_adapter.py
git commit -m "refactor: add structured domain adapter spec seam"
```

---

### Increment 5: Register research and development/codebase example specs

**Objective:** Register research and development/codebase as example domain specs that use the shared structured adapter seam.

**Files:**
- Modify: `src/hisys/domain/domain_adapters.py`
- Modify: `src/hisys/cli/main.py`
- Create: `tests/unit/test_example_domain_specs.py`
- Add/modify CLI fixture under `tests/fixtures/` only if the repo already uses CLI JSON fixtures for domain requests.

**Step 1: Write failing test**

Test behavior:

- Request with `domain="research"` resolves to `StructuredDomainAdapter(research_spec)` except for legacy research-gap fixture requests.
- Request with canonical `domain="codebase"` resolves to `StructuredDomainAdapter(development_or_codebase_spec)`. If Increment 0.5 chose a `development` alias, test that alias normalization happens before Pydantic request validation; otherwise test that direct `domain="development"` is rejected with a controlled error.
- Development/codebase investigation records local `/home/cbchoi/me` and local requirements/code targets.
- Research decision type remains `research_review`; development/codebase decision type remains `code_evaluation_review`.
- No external calls/mutations.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_example_domain_specs.py -q
```

Expected: FAIL because example specs are missing or registry factory does not include them.

**Step 3: Implement minimal adapter**

Do not perform actual source-code analysis yet. Use deterministic refs and the shared artifact writer first. Treat development/codebase as an example spec, not a special CLI branch.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_example_domain_specs.py tests/unit/test_domain_three_layer_use_cases.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/domain_adapters.py src/hisys/cli/main.py tests/unit/test_example_domain_specs.py
git commit -m "feat: register research and development example domain specs"
```

---

### Increment 6: Register investment example spec by migrating the existing investment workflow

**Objective:** Register investment as an example domain spec through the shared structured adapter seam while reusing the existing investment decision-support product workflow.

**Files:**
- Modify: `src/hisys/domain/use_cases.py`
- Modify: `src/hisys/domain/domain_adapters.py`
- Modify: `src/hisys/domain/__init__.py`
- Create: `tests/unit/test_investment_example_domain_spec.py`
- Preserve: `src/hisys/schemas/investment.py`
- Preserve: `tests/unit/test_investment_decision_packet_schema.py`
- Preserve: `tests/unit/test_investment_decision_packet_cli.py`
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`

**Step 1: Write failing investment spec test**

Test behavior:

- `domain="investment"` resolves to `StructuredDomainAdapter(investment_spec)`.
- The spec calls `InvestmentAnalysisUseCase` or equivalent concrete investment layers.
- Investigation references existing `investment_decision_support` evidence concepts.
- Aggregation references existing investment evidence/package/report boundaries.
- Decision references `InvestmentDecisionPacket` or existing investment dry-run report artifacts rather than creating a separate ungoverned recommendation.
- Existing boundaries remain true:
  - `not financial advice`;
  - `no autonomous execution`;
  - `execution_authorized=false` by default;
  - `publication_or_live_action_approved=false`;
  - human approval required;
  - `InvestmentWeightPolicy` and `HumanApprovalGate` refs are preserved where applicable;
  - fixture-backed product dry-run rejection remains covered by existing tests;
  - no order execution, publication, network call, or credential use is introduced.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_investment_example_domain_spec.py -q
```

Expected: FAIL because investment is not yet registered through the structured domain adapter seam.

**Step 3: Implement minimal investment spec migration**

Do not duplicate `InvestmentDecisionPacket` validation. Reuse existing schema/product concepts and record refs to existing product artifact families. The minimal migration may reference existing dry-run/packet artifacts, but it must make those refs explicit in the structured runtime artifact and bridge result.

**Step 4: Verify GREEN**

```bash
python3 -m pytest   tests/unit/test_investment_example_domain_spec.py   tests/unit/test_investment_decision_packet_schema.py   tests/unit/test_investment_decision_packet_cli.py   -q
```

**Step 5: Commit**

```bash
git add   src/hisys/domain/use_cases.py   src/hisys/domain/domain_adapters.py   src/hisys/domain/__init__.py   tests/unit/test_investment_example_domain_spec.py   docs/use-cases/hermes-hisys-domain-tool.md
git commit -m "feat: register investment example domain spec"
```

---

### Increment 7: Add requirements-analysis example spec, use case, and adapter

**Objective:** Support requirements-analysis-stage work as an example domain workflow using the same structured adapter seam and the domain naming strategy chosen in Increment 0.5.

**Files:**
- Modify: `src/hisys/domain/use_cases.py`
- Modify: `src/hisys/domain/domain_adapters.py`
- Modify: `src/hisys/domain/__init__.py`
- Create: `tests/unit/test_requirements_analysis_use_case.py`
- Create: `tests/unit/test_requirements_analysis_adapter.py`
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`

**Step 1: Write failing use-case test**

Test behavior:

- `RequirementsAnalysisUseCase` runs investigation, aggregation, decision in order.
- The request uses the canonical domain strategy chosen in Increment 0.5 (`requirements_analysis` if schema was extended, otherwise `codebase` with explicit objective/subtype convention).
- Investigation targets stakeholder statements and local requirements folder.
- Work product includes candidate requirement refs and issue categories:
  - ambiguity
  - conflict
  - gap
  - unverifiable statement
- Aggregation report type is `requirements_analysis_report`.
- DARS decision type is `requirements_review`.
- Human review is required.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_requirements_analysis_use_case.py -q
```

Expected: FAIL because use case does not exist.

**Step 3: Implement minimal concrete classes**

Suggested classes:

```text
RequirementsInvestigationLayer
RequirementsAnalysisAggregationLayer
RequirementsAnalysisUseCase
RequirementsAnalysisAdapter
```

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_requirements_analysis_use_case.py tests/unit/test_requirements_analysis_adapter.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/use_cases.py src/hisys/domain/domain_adapters.py src/hisys/domain/__init__.py tests/unit/test_requirements_analysis_use_case.py tests/unit/test_requirements_analysis_adapter.py docs/use-cases/hermes-hisys-domain-tool.md
git commit -m "feat: add requirements analysis domain use case"
```

---

### Increment 8: Introduce fixture-backed local search providers

**Objective:** Replace pure planned refs with deterministic, read-only local discovery for memos and requirements.

**Files:**
- Create: `src/hisys/domain/search.py`
- Modify: `src/hisys/domain/use_cases.py`
- Create: `tests/unit/test_domain_local_search.py`
- Modify existing use-case tests to assert discovered fixture refs.

**Step 1: Write failing search-provider test**

Test behavior:

- Search provider walks only configured root paths.
- It returns deterministic refs for `.md`, `.txt`, `.json`, or controlled requirement docs.
- It refuses missing roots or roots outside allowed scope according to policy.
- It records no external calls and no mutations.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_local_search.py -q
```

Expected: FAIL because search provider does not exist.

**Step 3: Implement minimal read-only provider**

Keep implementation deterministic and fixture-backed. Do not scan arbitrary large directories in tests.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_local_search.py tests/unit/test_domain_three_layer_use_cases.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/search.py src/hisys/domain/use_cases.py tests/unit/test_domain_local_search.py tests/unit/test_domain_three_layer_use_cases.py
git commit -m "feat: add read-only domain local search provider"
```

---

### Increment 9: Add DARS boundary adapter for domain decisions

**Objective:** Replace the placeholder `DarsDecisionLayer` with a controlled adapter seam that can run the existing local DARS loopback/fixture path.

**Files:**
- Create: `src/hisys/domain/decision.py`
- Modify: `src/hisys/domain/use_cases.py`
- Create: `tests/unit/test_domain_dars_decision_boundary.py`
- Modify docs.

**Step 1: Write failing DARS-boundary test**

Test behavior:

- Decision layer produces DARS request/response/trace refs.
- Advisory-only fields are enforced.
- `requires_human_review=True`.
- Mutation/publication/external-call flags remain false in fixture mode.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_dars_decision_boundary.py -q
```

Expected: FAIL because domain DARS boundary adapter does not exist.

**Step 3: Implement minimal boundary seam**

Keep fixture/local loopback only. Do not call a live external DARS system.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_dars_decision_boundary.py tests/unit/test_domain_three_layer_use_cases.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/domain/decision.py src/hisys/domain/use_cases.py tests/unit/test_domain_dars_decision_boundary.py docs/use-cases/hermes-hisys-domain-tool.md
git commit -m "feat: add domain DARS decision boundary"
```

---

### Increment 10: Add end-to-end CLI acceptance tests for research/development/investment/requirements

**Objective:** Prove `hisys investigate-domain --request <json>` uses the new adapter/use-case chain and writes expected artifacts.

**Files:**
- Modify: `tests/unit/test_domain_cli.py` or create `tests/integration/test_domain_cli_three_layer.py` depending on existing project convention.
- Add fixtures under existing fixture directory if needed.

**Step 1: Write failing CLI tests**

Test cases:

1. Research general request writes three-layer result artifacts.
2. Development/codebase request writes three-layer result artifacts.
3. Investment request writes or references three-layer investment result artifacts while preserving existing `InvestmentDecisionPacket` boundaries.
4. Requirements-analysis request writes three-layer result artifacts.
5. Legacy research-gap/formalism request still uses existing deterministic fixture behavior.

Assertions:

- CLI exit code success.
- Runtime artifact JSON exists.
- JSON has layer trace in order.
- Safety flags false.
- DARS decision requires human review.
- Traceability IDs present.
- `HisysToolResult.from_domain_result(...)` projection succeeds.
- Research-gap-only DARS/Chief Editor postprocessing is not applied to structured investment/codebase/requirements results unless explicitly requested by their spec.

**Step 2: Verify RED**

```bash
python3 -m pytest tests/unit/test_domain_cli.py -q
```

Expected: FAIL on new cases before CLI routing is complete.

**Step 3: Implement minimal CLI registration/routing adjustments**

Keep `_ResearchGapDomainAdapter` precedence for legacy objective patterns.

**Step 4: Verify GREEN**

```bash
python3 -m pytest tests/unit/test_domain_cli.py tests/unit/test_domain_adapter_registry.py tests/unit/test_domain_three_layer_use_cases.py -q
```

**Step 5: Commit**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py src/hisys/domain/domain_adapters.py
git commit -m "feat: add CLI acceptance for three-layer domain workflows"
```

---

### Increment 11: Documentation, traceability matrix, and validation gate

**Objective:** Document the final refactored design and prove repository-level quality gates.

**Files:**
- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`
- Optionally create: `docs/traceability/domain-refactor-traceability.md` if repo convention supports it.

**Step 1: Write/extend documentation test if applicable**

If project has docs validation, add a controlled check that the main domain doc references:

- adapter registry
- three-layer use case model
- research/code/research/development/investment/requirements workflows
- DARS advisory-only boundary
- safety flags
- traceability IDs

**Step 2: Run full validation**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest -q
```

Expected:

```text
traceability OK
secret_scan hit_count=0
no diff whitespace errors
all tests pass
```

**Step 3: Commit**

```bash
git add docs/use-cases/hermes-hisys-domain-tool.md docs/traceability/domain-refactor-traceability.md
# include only files that exist/changed
git commit -m "docs: record three-layer domain refactor traceability"
```

---

## 9. Midpoint and High-Impact Gates

Pause for user confirmation after **Increment 6** before requirements-analysis and local search provider work.

Reason:

- Research, development/codebase, and investment example specs will be connected through the shared structured adapter seam.
- The next phase introduces broader requirements-analysis semantics and local file discovery.
- This crosses the 50% point of the refactor and may affect domain contract shape.

Gate report should include:

```text
Completed increments: 0.5-6
Commits: <hash list>
Focused tests: <results>
Full validation: <results>
Working tree: clean/dirty
Open design choices:
  A. confirm requirements-analysis naming strategy chosen in Increment 0.5 remains acceptable
  B. local search provider allowed roots and file extensions
  C. artifact schema compatibility vs new universal schema
Recommended next choice: <one option>
Confirmation requested: proceed to increments 7-11?
```

Also pause before any future work that enables:

- live publisher search;
- browser/network connector use;
- mutation or code modification by Hisys;
- publication/external messaging;
- schema migration that breaks existing artifacts.

## 10. Full Validation Recipe

Run after each coherent increment, with focused tests first. Ralph must stop instead of continuing if any command fails, if the same increment reaches RED/non-green validation three times, or if a live network/mutation/publication/order-execution path becomes enabled:

```bash
# Focused test for the increment
python3 -m pytest <focused-test-file> -q

# Related domain tests
python3 -m pytest \
  tests/unit/test_domain_adapter_registry.py \
  tests/unit/test_domain_three_layer_use_cases.py \
  tests/unit/test_domain_cli.py \
  tests/unit/test_example_domain_specs.py \
  tests/unit/test_investment_decision_packet_cli.py \
  -q

# Project quality gates
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest -q
```

Post-commit smoke:

```bash
python3 -m pytest \
  tests/unit/test_domain_adapter_registry.py \
  tests/unit/test_domain_three_layer_use_cases.py \
  tests/unit/test_domain_cli.py \
  tests/unit/test_example_domain_specs.py \
  tests/unit/test_investment_decision_packet_cli.py \
  -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short
git rev-parse --short HEAD
```

## 11. Risks and Controls

| Risk | Control |
|---|---|
| CLI grows more branching | Move new domain logic to `src/hisys/domain/domain_adapters.py`; keep CLI registry construction thin. |
| Tests verify implementation details only | Assert observable artifacts, layer order, refs, safety flags, and decision boundaries. |
| Existing research-gap behavior regresses | Preserve `_ResearchGapDomainAdapter` precedence and keep existing `test_domain_cli.py` cases green. |
| Traceability IDs become decorative | Enforce IDs in test/docstrings and include IDs in runtime artifact JSON. |
| Premature live external calls | Keep connector work fixture-backed; require explicit user gate before live providers. |
| Runtime artifacts lose boundary clarity | Writer must accept `DomainUseCaseContext.boundary_dir` and write only inside it. |
| Requirements-analysis scope expands too far | First implement candidate/ambiguity/conflict/gap/verifiability refs only; defer full NLP extraction. |
| Existing investment workflow is rebuilt instead of migrated | Treat `InvestmentDecisionPacket`, dry-run, weight policy, and human approval gate as authoritative existing products; adapter spec wraps/references them. |
| `DomainUseCaseResult` cannot satisfy existing Pydantic schemas | Close the Increment 2 bridge contract before adding `StructuredDomainAdapter`; require `HisysToolResult.from_domain_result(...)` acceptance. |
| `development` or `requirements_analysis` fails request validation | Resolve domain naming/schema strategy in Increment 0.5 before example specs. |
| Research-specific CLI postprocessing leaks into generic domains | Add structured-domain postprocessing guard and tests in Increment 4/10. |
| Ralph loop continues past a high-impact gate | Encode stop conditions and require user confirmation after Increment 6. |

## 12. Definition of Done

The full refactor is done when:

1. Research, development/codebase, investment, and requirements-analysis workflows are registered as example domain specs/adapters that call concrete three-layer use cases through the shared structured adapter seam.
2. CLI acceptance tests prove artifact creation or governed artifact references for all supported example workflows.
3. Runtime artifacts include request ID, domain, layer trace, evidence refs, aggregation refs, DARS decision refs, config/prompt refs, safety flags, quality gate, human-review flag, and traceability IDs.
4. `DomainUseCaseResult -> DomainInvestigationResult -> HisysToolResult.from_domain_result(...)` is tested for every example spec.
5. DARS remains advisory-only and human-review-required.
6. Existing research-gap/formalism fixture path still passes.
7. Existing investment packet schema/CLI tests still pass without weakened approval or dry-run boundaries.
8. Ralph stop conditions and Increment 6 midpoint stop are documented and followed.
9. Full validation passes:

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest -q
```

10. Working tree is clean and each increment is committed.

## 13. Recommended Execution Order

Recommended immediate sequence:

```text
Increment 0.5: domain naming/schema strategy
Increment 1: traceability IDs
Increment 2: use-case artifact packet + DomainInvestigationResult bridge
Increment 3: runtime artifact writer
Increment 4: structured domain adapter/spec seam + context builder + postprocessing guard
Increment 5: research + development/codebase example specs
Increment 6: investment example spec migration
Gate: stop, report, and confirm
Increment 7: requirements-analysis example spec/use case using chosen naming strategy
Increment 8: fixture-backed local search provider
Increment 9: DARS boundary adapter
Increment 10: CLI acceptance tests for examples
Increment 11: docs + traceability matrix + full validation
```

This order keeps the system testable and traceable before expanding behavior. It closes the schema bridge before structured adapters, avoids live connectors, and prevents Ralph from crossing the Increment 6 gate without human confirmation.
