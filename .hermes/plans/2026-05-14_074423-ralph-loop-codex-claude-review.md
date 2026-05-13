# Ralph Loop Readiness Review — Codex + Claude

Review target:

```text
.hermes/plans/2026-05-14_074423-hisys-domain-refactoring-tdd-traceability.md
.hermes/plans/2026-05-14_074423-claude-review-domain-refactoring-plan.md
```

Reviewers:

```text
Claude Code 2.1.140, read-only, allowedTools=Read
Codex CLI 0.128.0, read-only prompt; sandbox read-only failed due bwrap/userns, retried with bypass per codex skill for trusted local read-only review
```

## Combined verdict

```text
READY_AFTER_FIXES
```

Both Claude and Codex agreed that the direction is correct but the plan should not yet be handed to a Ralph/autonomous implementation loop as-is. The plan is likely to produce partial design objects unless the schema bridge, context construction, domain-name strategy, and governance acceptance criteria are fixed first.

## Shared blocking gaps

1. `DomainUseCaseResult -> DomainUseCaseArtifactPacket -> DomainInvestigationResult -> HisysToolResult` bridge contract is not concrete enough.
2. `DomainUseCaseContext` construction from `DomainInvestigationContext` is unspecified.
3. `requirements_analysis` and `development` are not current `DomainName` values; the plan must decide schema extension versus `codebase` objective/subtype.
4. Safety and governance propagation needs explicit tests from layer to packet to result to tool result.
5. Traceability gates must validate runtime artifact `traceability_ids`, not only docstring substrings.
6. Investment migration must specify artifact-level outputs and preserve existing approval/dry-run/not-financial-advice/no-autonomous-execution controls.

## Additional Claude findings

- Add an Increment 0.5 for the domain enum/schema decision.
- Define a default `HisysMode.level`, likely `stone` or another explicit default, so `InvestigationDataPackage` evidence-chain validation does not break autonomous increments unexpectedly.
- Add Ralph stop conditions: three repeated RED failures, secret scan hit, traceability validation failure, diff check failure, live network/mutation flag true.
- Stop automatically after Increment 6 for the midpoint gate.

## Additional Codex findings

- Existing CLI post-processing such as `_write_dars_fixture_for_domain_result` and `_write_chief_editor_research_review` appears research-gap centered; generic domain results must not receive research-specific DARS/Chief Editor semantics accidentally.
- `development` alias is also blocked by current `DomainName` validation unless handled before Pydantic request construction.
- `validate_traceability.py` may not enforce new `HISYS-DOM-*` runtime traceability; tests must fill that gap.
- Investment acceptance is still too abstract unless it states whether the adapter writes or references `InvestmentDecisionPacket` / dry-run artifacts and how fixture evidence rejection remains enforced.

## Required plan amendments before Ralph loop

1. Add Increment 0.5: domain naming/schema strategy.
   - Option A: add `requirements_analysis` and `development` to `DomainName`.
   - Option B: use existing `codebase`/`investment`/`research` domain values with objective/subtype fields.
   - Record one decision before autonomous implementation.
2. Redefine Increment 2 as a full bridge-contract increment.
   - RED test must prove `DomainUseCaseResult -> DomainInvestigationResult` Pydantic validation and `HisysToolResult.from_domain_result(...)` success.
3. Add `DomainUseCaseContext` construction rule.
   - Suggested helper: `DomainUseCaseContext.from_investigation_context(...)` or `StructuredDomainAdapter._build_use_case_context(...)`.
4. Add generic-domain CLI post-processing guard.
   - Research-gap postprocessors stay behind `_ResearchGapDomainAdapter`; structured specs use domain-specific review refs.
5. Strengthen traceability tests.
   - Runtime JSON includes `traceability_ids`, `layer_trace`, artifact refs, safety flags, config/prompt refs.
6. Make investment migration artifact-level.
   - Include `InvestmentDecisionPacket` or dry-run report ref, `HumanApprovalGate`, `execution_authorized=false`, `publication_or_live_action_approved=false`, fixture evidence rejection.
7. Add Ralph loop stop conditions and midpoint stop after Increment 6.

## Suggested first Ralph loop runbook

```text
0. Pre-flight:
   git status --short
   python3 -m pytest -q
   python3 scripts/validate_traceability.py
   python3 scripts/scan_secrets.py
   git diff --check

1. Plan amendment loop only:
   Update the plan with the required amendments above.
   No production code changes.
   Commit plan-only change if accepted.

2. Increment 0.5:
   Decide and test domain naming/schema strategy.

3. Increment 1:
   Add strict traceability IDs and tests.

4. Increment 2:
   Implement bridge contract through `HisysToolResult.from_domain_result(...)`.

5. Increment 3-4:
   Runtime writer and `StructuredDomainAdapter` using fake use case first.

6. Increment 5-6:
   Register research/development and investment specs.

7. Stop after Increment 6:
   Produce midpoint gate report and request human confirmation before requirements-analysis/local search/DARS-boundary expansion.
```

## Operational conclusion

Do not start full Ralph implementation loop yet. Run one plan-amendment loop first, then start Ralph from Increment 0.5/1 with explicit stop conditions and bridge-contract tests.
