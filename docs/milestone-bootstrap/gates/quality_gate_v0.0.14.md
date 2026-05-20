# Quality Gate v0.0.14 — M21.6 Prepare Bootstrap Refresh

## Required checks

1. Structural YAML/JSON parse over profile, task YAML, testcase YAML, Hisys request, and benchmark manifest.
2. Governance current-state test.
3. M21.5 benchmark fixture focused test.
4. Focused codebase-analysis regression cohort.
5. Traceability validator.
6. Secret scan.
7. `git diff --check`.

## Pass criteria

- All generated YAML/JSON parses.
- `next_safe_task` is `MB-CODEBASE-M21-6-PREP`.
- `selected_profile` is `develop`.
- `formal_hisys_result` is `not_run_in_this_bootstrap`.
- `local_advisory_result` is `RALPH_START_READY_WITH_CONTROLS`.
- No production code or tests are created by this refresh.
- No tmux/background agent, live external action, credential lookup, remote push, publication, deployment, or destructive Git action occurs.
