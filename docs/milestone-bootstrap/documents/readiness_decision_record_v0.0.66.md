# Readiness decision record v0.0.66

## Decision

`SECTION-10-3-DARS-BRANCH-ALIGNMENT` completed as a docs/control governance housekeeping increment.

## Evidence scope

- Updated control section: `ralph.md` Section 10.3 Automatic Milestone Push Checkpoint
- Governance profile: `docs/milestone-bootstrap/profile.yaml`
- Governance current-state test: `tests/unit/test_governance_docs_current_state.py`
- Traceability summary: `docs/traceability/README.md`

## Accepted meaning

The automatic milestone push checkpoint now targets the active governed Hisys development branch:

```text
branch: dars
upstream: origin/dars
automatic command: git push origin dars
```

The controlled exception remains narrow. It applies only after local milestone completion, the Section 10.2 global gate, a clean working tree, exact `dars` / `origin/dars` alignment, and a normal non-force push that does not require credential, key, remote, branch, history, or security changes.

## Boundary retained

No new remote, credential, force-push, history rewrite, live provider/model execution, mutation, publication, release, deployment, or DARS completion-claim authority is granted. If any push precondition fails, Ralph/Hermes must stop and report the blocker instead of attempting recovery.

## Result

```text
formal_hisys_result: codex_cli_subprocess_completion_claim_review_ready_with_bounded_runtime_evidence
local_advisory_result: RALPH_START_READY_WITH_CONTROLS
```

## Next safe row

```text
operator_selection_required
```

The branch-alignment housekeeping candidate is closed. Opening live-local LSP execution, approved OSS comparison, M25, additional Codex/provider execution, or stronger DARS completion claims still requires explicit operator selection and the relevant prerequisite packet.
