# Quality Gate v0.0.7 — Current-Session Bootstrap Refresh

Pass criteria:

- Target/profile inference is recorded.
- Current Git state and baseline HEAD are recorded.
- Existing M20.3 implementation plan is referenced.
- New versioned report, tasks, testcases, gate, decision, Hisys request/result, and validation log exist.
- `profile.yaml`, tasks YAML, testcases YAML, and Hisys request JSON parse structurally.
- Domain focused regression passes.
- DARS focused regression passes.
- Traceability validator passes.
- Secret scan reports zero hits.
- `git diff --check` is clean.
- `ralph.md` is appended/merged, not overwritten.
- No tmux/background agent, remote push, live action, credentials, or production code mutation occurred.
