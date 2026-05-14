# Hisys Domain Adapter Ralph Loop Plan

> **For Ralph/Hermes:** Execute this file as the active Ralph-loop control plan. Run one task at a time using strict Plan -> RED -> GREEN -> Refactor -> Quality Gate -> Commit discipline. Stop only under the stop conditions in this file.

## 0. Purpose

This Ralph loop advances the Hisys domain-refactoring line from the pre-Ralph hardening state to governed example-domain registration and migration.

Current baseline before this loop:

```text
branch: feat/domain-adaptive-requirements-analysis
baseline HEAD: 04d6b01 test: propagate src path to subprocess CLI tests
pre-Ralph gate: 528 passed, traceability OK, secret scan hit_count=0, git diff --check OK
```

The first executable milestone is Increment 5 from the master plan: register `research_spec` and `codebase_spec` as example structured domain specs while preserving the legacy research-gap adapter path.

## 1. Controlled Document Rules

Every milestone and every task shall cite the controlled document anchors below before implementation:

| Short name | Controlled document | Path |
|---|---|---|
| SRS | `HISYS-SRS-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/requirements-record.md` |
| SDD | `HISYS-SDD-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/software-design-description.md` |
| IDD | `HISYS-IDD-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/interface-design-description.md` |
| STD | `HISYS-STD-001` | `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/software-test-description.md` |
| TDD procedure | `test-driven-development` skill | `software-development/test-driven-development` |

### 1.1 Mandatory task-start checklist

Before creating or executing any task:

1. Read or search SRS, SDD, IDD, and STD for the task objective.
2. Record the relevant requirement/design/interface/test IDs in the task header.
3. Confirm the task is a single functional unit derived from SRS + SDD.
4. Confirm the test behavior is derived from STD and follows the TDD procedure.
5. If the needed requirement/design/interface/test anchor is absent:
   - perform a consistency check against existing SRS/SDD/IDD/STD constraints;
   - if consistent, update the controlled document(s) first, validate traceability, commit the document update, then resume the Ralph loop;
   - if inconsistent, stop the Ralph loop and report the inconsistency to the user.

### 1.2 Controlled-document amendment rule

A controlled-document update is allowed only when all are true:

- It strengthens or clarifies existing Hisys product goals.
- It preserves source reliability, provenance, auditability, human review, and no-live-action defaults.
- It does not authorize uncontrolled external calls, mutation, publication, credential use, order execution, or bypassing access controls.
- It can be mapped into at least one SRS requirement, one SDD design element, one IDD interface/record rule, and one STD test.

If any item fails, stop and ask the user.

### 1.3 Stop conditions

Stop the Ralph loop and report to the user if any condition occurs:

- A task lacks SRS/SDD/IDD/STD support and the proposed document amendment is inconsistent.
- The same task fails RED/GREEN validation three times.
- `scripts/validate_traceability.py` fails.
- `scripts/scan_secrets.py` reports `hit_count > 0`.
- `git diff --check` fails.
- A code path enables live external call, mutation, publication, credential use, order execution, or browser/access-control bypass without explicit controlled approval.
- Investment governance regresses from advisory-only, no autonomous execution, human approval required.
- A midpoint gate explicitly requires user confirmation.

## 2. Current Controlled-Document Alignment

The domain-adapter Ralph loop is now explicitly supported by the controlled documents:

| Controlled anchor | Summary |
|---|---|
| SRS `HISYS-FR-DOM-001..006` | DomainAdapterRegistry / StructuredDomainAdapter / DomainAdapterSpec / three-layer use cases / bridge contract / example specs / investment governance. |
| SDD `Domain Investigation Adapter Design` | Execution path from registry to structured adapter, three-layer use case, runtime writer, `DomainInvestigationResult`, and `HisysToolResult`. |
| IDD `HISYS-IF-017` and `5.7` | Domain investigation adapter contract, structured spec fields, runtime result fields, and safety validation rules. |
| STD `HISYS-T-025..028` | Spec registration/precedence, bridge, runtime artifact governance, and investment migration governance tests. |

## 3. Ralph Execution Protocol

For each task:

1. **Plan**: restate objective, controlled anchors, files, risks, and acceptance checks.
2. **RED**: write one failing test first. Run the focused test and confirm expected failure.
3. **GREEN**: implement the smallest code change to pass that test.
4. **Refactor**: clean only after tests pass; do not add behavior during refactor.
5. **Quality Gate**: run task-specific focused tests, traceability validation, secret scan if artifacts/docs changed, `git diff --check`, and any related tests.
6. **Commit**: commit exactly one coherent increment.
7. **Review**: record commit hash, validation result, and next task.

## 4. Milestones and Tasks

### Milestone M1 — Register Research and Codebase Example Specs

**Goal:** Add example `research_spec` and `codebase_spec` over `StructuredDomainAdapter` and register them behind the legacy research-gap path.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-001`, `HISYS-FR-DOM-002`, `HISYS-FR-DOM-003`, `HISYS-FR-DOM-004`, `HISYS-FR-DOM-005`, `HISYS-NFR-MNT-001`, `HISYS-DATA-003..005`
- SDD: `Domain Investigation Adapter Layer`, `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7 DomainInvestigationAdapter / DomainAdapterSpec`, Interface Validation Rules
- STD: `HISYS-T-025`, `HISYS-T-026`, `HISYS-T-027`
- TDD: RED/GREEN/REFACTOR procedure in `test-driven-development`

#### Task M1.1 — Add RED tests for registry precedence

**Objective:** Lock dispatch order before adding specs.

**Files:**

- Create/modify test: `tests/unit/test_domain_example_specs.py`
- Read/possibly modify later: `src/hisys/cli/main.py`, `src/hisys/domain/specs.py`

**Required test behaviors:**

1. `domain="research"` with formalism/research-gap objective resolves to `_ResearchGapDomainAdapter`.
2. `domain="research"` with a general research objective resolves to `StructuredDomainAdapter(research_spec)`.
3. `domain="codebase"` resolves to `StructuredDomainAdapter(codebase_spec)`.
4. `domain="codebase"` with `objective` beginning `requirements-analysis:` resolves to `codebase_spec`.
5. Structured specs do not apply research-gap DARS fixture / Chief Editor postprocessors.

**RED command:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py -q
```

**Expected RED:** missing `hisys.domain.specs` or missing registry entries.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py -q
python3 -m pytest tests/unit/test_domain_adapter_registry.py tests/unit/test_domain_postprocessing_guard.py -q
python3 scripts/validate_traceability.py
git diff --check
```

#### Task M1.2 — Implement `research_spec` and `codebase_spec`

**Objective:** Provide concrete example specs without adding new CLI branch logic.

**Files:**

- Create: `src/hisys/domain/specs.py`
- Modify: `src/hisys/domain/__init__.py`
- Test: `tests/unit/test_domain_example_specs.py`

**Implementation constraints:**

- `research_spec()` returns a `DomainAdapterSpec` using `ResearchAnalysisUseCase`, `DomainUseCaseArtifactTranslator`, `DomainRuntimeArtifactWriter`, and traceability IDs including `HISYS-FR-DOM-001..005` or local implementation IDs if already established.
- `codebase_spec()` returns a `DomainAdapterSpec` using `CodeAnalysisUseCase`.
- `codebase_spec` shall keep canonical domain `codebase`; do not add `development` to `DomainName`.
- Requirements-analysis remains an objective/subtype convention under `codebase` until controlled schema approval.

**GREEN command:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py -q
```

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_structured_domain_adapter.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M1.3 — Register example specs in the CLI default registry

**Objective:** Wire example specs into `_default_domain_adapter_registry` while preserving legacy research-gap precedence.

**Files:**

- Modify: `src/hisys/cli/main.py`
- Test: `tests/unit/test_domain_example_specs.py`, `tests/unit/test_domain_cli.py`

**Implementation constraints:**

- Registry order shall be:

```text
_ResearchGapDomainAdapter(instance)
StructuredDomainAdapter(research_spec())
StructuredDomainAdapter(codebase_spec())
```

- Do not add `if domain == ...` CLI branches for example specs.
- Existing research-gap fixture behavior shall remain unchanged.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_cli.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit message:**

```bash
git commit -m "feat: register research and codebase structured domain specs"
```

### Milestone M2 — Add Spec Collision and Developer-Guide Hardening

**Goal:** Prevent ambiguous spec registration and document how developers add new domain specs.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-001..002`, `HISYS-NFR-MNT-001`
- SDD: `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7`
- STD: `HISYS-T-025`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M2.1 — Add RED tests for duplicate domain/alias collisions

**Objective:** Ensure spec registration cannot silently create ambiguous dispatch.

**Files:**

- Modify: `tests/unit/test_domain_adapter_registry.py` or create `tests/unit/test_domain_spec_collisions.py`
- Modify later: `src/hisys/domain/adapters.py` or `src/hisys/domain/specs.py`

**Required test behaviors:**

1. Duplicate canonical domains are rejected.
2. Alias that collides with another canonical domain is rejected.
3. Alias duplicated across specs is rejected.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_spec_collisions.py tests/unit/test_domain_adapter_registry.py -q
python3 scripts/validate_traceability.py
git diff --check
```

#### Task M2.2 — Implement collision validation helper

**Objective:** Provide a small validation seam without making registry generic logic complex.

**Files:**

- Modify/create: `src/hisys/domain/specs.py` or `src/hisys/domain/domain_adapters.py`
- Test: `tests/unit/test_domain_spec_collisions.py`

**Implementation constraints:**

- Keep validation deterministic and local.
- Do not perform filesystem, network, or source access.
- Keep error messages actionable for domain developers.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_spec_collisions.py tests/unit/test_domain_example_specs.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M2.3 — Update developer guide docs

**Objective:** Document the exact steps to add a new domain spec using the example specs.

**Files:**

- Modify: `docs/use-cases/hermes-hisys-domain-tool.md`
- Optionally modify: `.hermes/plans/2026-05-14_074423-hisys-domain-refactoring-tdd-traceability.md`

**Required content:**

- Controlled doc anchors required before a new task.
- Spec fields to define.
- Three-layer use-case files to implement.
- RED tests required before code.
- Alias collision checks.
- Quality gate commands.

**Quality gate:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_spec_collisions.py -q
```

**Commit message:**

```bash
git commit -m "docs: document structured domain spec extension workflow"
```

### Milestone M3 — Prepare Investment Migration Gate

**Goal:** Prepare, but do not yet fully migrate, the investment domain into the structured-domain substrate.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-006`, `HISYS-FR-AGT-003..004`, `HISYS-NFR-SEC-001..004`
- SDD: `Domain Investigation Adapter Design`, failure handling, security/privacy/compliance design
- IDD: `HISYS-IF-017`, Interface Validation Rules
- STD: `HISYS-T-028`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M3.1 — Add RED tests for investment migration acceptance

**Objective:** Lock investment governance before migration.

**Files:**

- Create/modify: `tests/unit/test_investment_structured_domain_spec.py`
- Read existing tests: `tests/unit/test_investment_decision_packet_cli.py`, `tests/unit/test_investment_decision_packet_schema.py`

**Required test behaviors:**

1. `investment_spec` output references existing `InvestmentDecisionPacket` or dry-run report refs.
2. `execution_authorized=false` is preserved.
3. `publication_or_live_action_approved=false` is preserved.
4. Human approval is required.
5. Fixture-backed product dry-run misuse remains rejected.
6. No order execution, publication, credential use, or live external action path is introduced.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_investment_structured_domain_spec.py tests/unit/test_investment_decision_packet_cli.py tests/unit/test_investment_decision_packet_schema.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

#### Task M3.2 — Stop for midpoint confirmation before investment implementation

**Objective:** Report readiness and ask the user whether to proceed with implementation migration.

**Files:**

- Create report if useful: `.hermes/plans/<timestamp>-investment-migration-gate.md`

**Gate report shall include:**

- Completed commits since `04d6b01`.
- Test and traceability results.
- Investment acceptance tests and RED/GREEN state.
- Remaining risks.
- Specific confirmation request.

**Stop rule:** Do not implement `investment_spec` until user confirms.

### Milestone M4 — Requirements-Analysis Example Under Codebase Domain

**Goal:** Add requirements-analysis behavior as a codebase objective/subtype without changing `DomainName`.

**Controlled anchors:**

- SRS: `HISYS-FR-DOM-005`, `HISYS-FR-DOM-003..004`, `HISYS-DATA-003..005`
- SDD: `Domain Investigation Adapter Design`
- IDD: `HISYS-IF-017`, `5.7`
- STD: `HISYS-T-025..027`
- TDD: RED/GREEN/REFACTOR procedure

#### Task M4.1 — Add RED test for requirements-analysis objective routing

**Objective:** Confirm requirements-analysis remains under `codebase` until schema approval.

**Files:**

- Modify: `tests/unit/test_domain_example_specs.py`
- Possibly modify: `src/hisys/domain/specs.py`

**Required test behavior:**

```text
domain="codebase"
objective starts with "requirements-analysis:"
-> codebase_spec / CodeAnalysisUseCase path
```

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_name_strategy.py -q
python3 scripts/validate_traceability.py
git diff --check
```

#### Task M4.2 — Add requirements-analysis work-product labeling

**Objective:** Make runtime artifacts distinguish codebase evaluation from requirements-analysis without schema expansion.

**Files:**

- Modify: `src/hisys/domain/use_cases.py` or `src/hisys/domain/specs.py`
- Test: `tests/unit/test_domain_example_specs.py`, `tests/unit/test_domain_runtime_artifacts.py`

**Implementation constraints:**

- Do not add `requirements_analysis` to `DomainName` in this milestone.
- Use objective/subtype labeling only.
- Preserve no external call and no mutation defaults.

**Quality gate:**

```bash
python3 -m pytest tests/unit/test_domain_example_specs.py tests/unit/test_domain_runtime_artifacts.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## 5. Global Quality Gate

Run this before reporting any milestone complete:

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
git rev-parse --short HEAD
```

Acceptance:

- Focused tests pass.
- Full tests pass.
- Traceability script reports OK.
- Secret scan reports `hit_count=0`.
- `git diff --check` reports no whitespace errors.
- `git status --short` is clean after commit.
- Each new behavior has a RED test observed before production implementation.

## 6. Reporting Format

After each task, report:

```text
Task: <ID and title>
Controlled anchors: <SRS/SDD/IDD/STD/TDD refs>
RED: <command and expected failure>
GREEN: <command and pass result>
Quality gate: <commands and results>
Commit: <hash and message>
Next task: <ID or stop reason>
Working tree: <clean or files>
```

## 7. Initial Next Action

Start with **Task M1.1 — Add RED tests for registry precedence**.

Do not start by editing production code. The first action must be a failing test that proves the registry does not yet route general research and codebase requests through structured example specs.
