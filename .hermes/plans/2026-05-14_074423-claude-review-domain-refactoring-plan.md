# Claude Review: Hisys Domain Refactoring Plan

Review target:

```text
.hermes/plans/2026-05-14_074423-hisys-domain-refactoring-tdd-traceability.md
```

Claude Code mode:

```text
read-only
allowed tools: Read
no file edits
```

## Verdict

```text
CONCERNS
```

Claude judged the plan direction sound, especially the shared `StructuredDomainAdapter` / `DomainAdapterSpec` model, but identified bridge-contract gaps that should be resolved before implementation proceeds beyond traceability and translation increments.

## Strong points

- The examples-as-specs framing is aligned with the intended architecture.
- The TDD rhythm is explicit: failing test, RED, minimal implementation, GREEN, commit.
- Traceability is introduced before further behavior is added.
- Investment is correctly treated as a migration domain rather than a greenfield adapter.
- Governance boundaries are preserved: advisory-only DARS, human review, external/mutation flags, no live action by default.
- Midpoint gate and validation recipe match repository scripts.

## Blocking issues

### 1. Missing bridge contract from use-case artifacts to `DomainInvestigationResult`

Current adapters must return `DomainInvestigationResult`. The plan references a future `to_domain_investigation_result(packet, refs)` function, but does not yet define the Pydantic-compatible mapping.

Required plan/test refinement:

```text
DomainUseCaseResult
  -> DomainUseCaseArtifactPacket
  -> DomainInvestigationResult
  -> HisysToolResult.from_domain_result(...)
```

The test should assert successful construction/validation of `DomainInvestigationResult`, including:

```text
alternative_decision_set
recommendation_summary
quality_gate
runtime_boundary_refs
requires_human_review
external_call_made
mutation_performed
traceability_ids
```

### 2. Missing construction rule for `DomainUseCaseContext`

`DomainInvestigationContext` and `DomainUseCaseContext` are separate records. The plan currently uses `context.use_case_context` in pseudocode, but does not define who constructs it.

Required refinement:

```text
StructuredDomainAdapter or registry factory must derive DomainUseCaseContext from:
  - instance.root
  - runtime boundary directory
  - request date / deterministic yyyymmdd
```

### 3. `DomainName` Literal does not include requirements-analysis domain

Current schema includes:

```text
"codebase", "research", "business", "investment", "iso_process", "general"
```

It does not include `requirements` or `requirements_analysis`. The plan must decide one of:

```text
A. extend DomainName with requirements-analysis value
B. model requirements analysis as domain="codebase" plus objective/subtype
```

This decision should occur before the requirements-analysis increment.

## Non-blocking improvements

- Make traceability tests stricter than checking for any `HISYS-DOM-` substring.
- Add runtime artifact assertions for `traceability_ids` arrays.
- Add OR-propagation tests for `external_call_made` and `mutation_performed`.
- Add unsupported/reserved-domain tests for `business`, `iso_process`, and `general` as applicable.
- Add `HisysToolResult.from_domain_result` acceptance to CLI/translation tests.
- Make investment layer mapping more concrete:
  - investigation: `InvestmentDecisionSupportAgent` / source evidence refs
  - aggregation: `InvestmentDecisionPacket` / weight policy / scenario refs
  - decision: existing dry-run/advisory boundary, no autonomous execution
- Test that `_ResearchGapDomainAdapter` precedence remains ahead of `StructuredDomainAdapter(research_spec)`.

## Recommended next adjustment

Proceed with Increment 1, but redefine Increment 2 as:

```text
Use-case artifact packet + DomainInvestigationResult bridge contract
```

Increment 2 RED test should prove:

```text
1. DomainUseCaseResult -> DomainUseCaseArtifactPacket
2. packet -> DomainInvestigationResult Pydantic validation
3. safety flags and human review preserved
4. HisysToolResult.from_domain_result(result) succeeds
```

This makes Increment 4 (`StructuredDomainAdapter`) implement the existing `DomainInvestigationAdapter` protocol without ambiguity.
