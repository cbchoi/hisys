# Milestone Plan v0.0.5 — M20.2 incomplete codebase artifact bundle gate

## Scope

Prepare the M20.2 implementation increment after M20.1 accepted refs-only codebase artifact bundle references. This package is a document-RED checkpoint; it does not modify production behavior.

## Baseline evidence

- Branch: `dars`
- Baseline HEAD: `d87bc96 feat: accept codebase artifact bundle refs`
- Domain gate before planning: `15 passed`
- DARS focused gate before planning: `48 passed`

## Next safe milestone

`M20.2`: classify codebase artifact bundle completeness and preserve advisory `needs_more_evidence` semantics for incomplete bundles.

## Non-goals

- No CLI flag.
- No live external calls.
- No repository clone.
- No raw source archival.
- No publication or action authorization.
- No final `DomainInvestigationResult` enrichment; that remains M20.3.
