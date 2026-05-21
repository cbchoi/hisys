# Readiness Decision Record v0.0.21

## Decision

`RALPH_START_READY_WITH_CONTROLS` for M23 advanced codebase adapter integration.

## User authorization

On 2026-05-21 KST, 최창범 교수 authorized the previously human-gated advanced code-analysis line with: `고급 기능 LSP 외부어댑터 통합까지 모두 승인` and then requested `M23 진행`.

## Authorized scope

M23 may open governed PREP/RED/GREEN/GATE rows for:

- approved OSS comparison adapter integration for codebase analysis;
- optional local LSP adapter integration;
- local subprocess spawning only inside the governed LSP adapter boundary after a PREP row records command allowlist, timeout, workspace-root restriction, output schema, and kill policy;
- external adapter integration into advisory code-analysis evidence and the existing M22 evidence portfolio by refs, counts, schema ids, and boundary flags.

## Non-claims and remaining gates

This record does not authorize credential lookup or mutation, secret capture, arbitrary network search/clone/fetch, new or changed remote configuration, publication/deployment/release, destructive Git/history operations, force push, mutation of non-fixture user/live data, unbounded live external provider execution, or a live-provider DARS completion claim.

DARS panel completion remains bounded to `local_fixture_localhost_controlled_advisory_complete` until a separate live-provider line is planned, tested, and explicitly authorized.

## Evidence scope

- Current branch before this authorization checkpoint: `dars`.
- Current baseline before this authorization checkpoint: `cd944cc docs: close m22 codebase evidence portfolio milestone`.
- M22 evidence portfolio closed at `local_fixture_advisory_complete`.
- Remaining backlog human gates were approved for M23 only within the controlled boundaries stated above.

## Next safe task

`M23-OSS-ADAPTER-PREP`.
