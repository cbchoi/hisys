# Milestone Plan v0.0.6 — M20.3 Codebase Bundle Enrichment Prepare

## Objective
Prepare the next M20 increment: safe local loading of complete codebase-analysis bundles and bounded enrichment into `DomainInvestigationResult.investigation_data`.

## Current baseline

- HEAD: `aba9aa6 feat: gate incomplete codebase artifact bundles`
- M20.1 complete: refs-only `codebase_artifact_refs`
- M20.2 complete: role-level bundle gate `needs_more_evidence` / `candidate_complete`
- Current package is docs/bootstrap-only.

## Next safe task

`MB-M20-3-T001`: write the RED test for a complete local bundle enriching the codebase domain result.

## Boundaries

- Use existing safe loader chokepoint.
- No direct arbitrary file opens for caller refs.
- No CLI flag until M20.4.
- No live external access, raw source archival, credential use, publication, or action authorization.
- Complete bundle remains human-review-required and advisory.
