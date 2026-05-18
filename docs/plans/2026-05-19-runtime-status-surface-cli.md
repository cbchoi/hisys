# Runtime Status Surface CLI Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add a governed Hisys CLI status-surface capability that can produce a compact, redacted operator view of runtime context, Git state, model/session boundaries, cost/context usage inputs, and approval boundaries without performing live external action.

**Architecture:** Implement this as a read-only local CLI/reporting increment. Start with a pure builder module that accepts explicit inputs and local repository/runtime paths, redacts sensitive fields, and returns a deterministic status-surface packet. Then add a CLI command that writes JSON/Markdown artifacts under the Hisys instance runtime boundary and optionally prints a compact text line. Keep actual terminal statusline integration, tmux integration, Hermes TUI integration, and Claude Code statusline scripting as later adapters that consume the packet.

**Tech Stack:** Python 3.11, argparse CLI in `src/hisys/cli/main.py`, dataclasses/Pydantic-compatible dictionaries, pytest, local Git subprocess calls with timeouts, Hisys runtime artifacts.

**Context Packet:**
- Source Stone: `/home/cbchoi/me/10 Mine/Links/202605190801-claude-code-statusline.md`
- Source URL: `https://code.claude.com/docs/en/statusline`
- Approval: user approved applying the cherrypick direction in Discord on 2026-05-19.
- Existing CLI surface: `src/hisys/cli/main.py`, especially parser registration around `health-status` and existing report-writing commands.
- Existing local-status patterns: `src/hisys/operations/health.py`, `src/hisys/hermes_deploy.py`, `tests/unit/test_release_ops_cli.py`, `tests/unit/test_completion_status_cli.py`.
- Omitted context: raw Claude docs HTML, broad Hermes runtime internals, and live gateway state. Retrieve those only if implementing downstream Hermes/TUI adapters.
- Validation handles: focused pytest tests listed per milestone, `python3 scripts/validate_traceability.py`, `python3 scripts/scan_secrets.py`, `git diff --check`.

**Boundary Record:**
- This plan authorizes documentation/planning only.
- Future implementation must remain local/read-only by default: no browser/network calls, no publication, no external action, no credential access, no runtime restart.
- A generated status packet may write only under the requested Hisys instance root.
- Any adapter that reads live Hermes runtime config, invokes Claude Code, modifies shell/tmux statuslines, or changes Hermes gateway/TUI behavior requires a separate approval gate.

---

## Accepted Requirements

1. **Status-surface packet**
   - Define a machine-readable packet with `schema_id`, `schema_version`, `status_surface_id`, `created_at`, `request_id`, `producer_id`, `working_directory`, `git`, `runtime`, `model_context`, `cost_context`, `approval_boundary`, `health`, `display`, `redaction`, and `boundary_flags` sections.
   - Preserve `external_call_made=false`, `mutation_performed=false`, and `action_taken=none` for the core command.
   - Packet fields must be deterministic and safe to render in a one-line or multi-line status surface.

2. **Redaction-first design**
   - Never expose tokens, API keys, env values, credential refs, full private home paths, connection strings, or raw command arguments containing secrets.
   - Shorten home paths to `~/...` or `<repo>/...` where possible.
   - Provide `redaction.applied=true|false`, `redaction.rules`, and `redaction.hidden_fields`.
   - Fail closed if explicit input contains a credential-looking value and no redaction rule handles it.

3. **Local Git/runtime inspection only**
   - Git status may inspect a local worktree only.
   - Do not call remote Git, GitHub, network APIs, Hermes gateway, Claude services, or browser connectors.
   - If `--repo-root` is absent, derive Git info from `--working-directory` only when it is inside a Git worktree; otherwise record `git.available=false`.

4. **CLI command**
   - Add a command such as `runtime-status-surface`.
   - Required flags: `--instance`, `--date`, `--request-id`.
   - Optional flags: `--working-directory`, `--repo-root`, `--model`, `--provider`, `--session-id`, `--context-used`, `--context-limit`, `--cost-usd`, `--approval-state`, `--approval-ref`, `--format text|json`.
   - Output artifacts:
     - `runtime-boundary/status-surfaces/<YYYYMMDD>/<request_id>-status-surface.json`
     - `runtime-boundary/status-surfaces/<YYYYMMDD>/<request_id>-status-surface.md`
   - Text output should be concise and safe for terminal display.

5. **Future adapter seam**
   - The first implementation should not implement a live statusline.
   - It should expose a renderer function that later Claude Code, Hermes TUI, or tmux adapters can reuse.
   - Keep the display renderer separate from artifact writing.

---

## Milestone 0: Schema and redaction policy baseline

**Objective:** Define the packet contract and redaction rules before reading runtime state.

**Files:**
- Create: `src/hisys/operations/runtime_status_surface.py`
- Create: `tests/unit/test_runtime_status_surface.py`
- Modify: `docs/traceability/README.md` if new trace IDs are added.

**Step 1: Write failing tests**

Add tests for:
- `test_status_surface_packet_defaults_to_no_external_action()`
- `test_status_surface_redacts_home_paths_and_secret_like_values()`
- `test_status_surface_rejects_unredacted_secret_like_value()`
- `test_status_surface_renders_compact_display_line()`

**Step 2: Run tests to verify RED**

```bash
python3 -m pytest tests/unit/test_runtime_status_surface.py -q
```

Expected: FAIL because the module does not exist.

**Step 3: Implement minimal packet builder**

Create pure functions:
- `redact_status_value(value: str) -> tuple[str, bool, list[str]]`
- `build_runtime_status_surface(...) -> dict[str, object]`
- `render_status_surface_line(packet: dict[str, object]) -> str`
- `render_status_surface_markdown(packet: dict[str, object]) -> str`

Minimum packet fields:
```json
{
  "schema_id": "hisys.runtime_status_surface",
  "schema_version": "0.1.0",
  "external_call_made": false,
  "mutation_performed": false,
  "action_taken": "none"
}
```

**Step 4: Run tests to verify GREEN**

```bash
python3 -m pytest tests/unit/test_runtime_status_surface.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/hisys/operations/runtime_status_surface.py tests/unit/test_runtime_status_surface.py docs/traceability/README.md
git commit -m "feat: add runtime status surface packet"
```

---

## Milestone 1: Local Git and workdir context collection

**Objective:** Add safe local Git/workdir fields without remote calls.

**Files:**
- Modify: `src/hisys/operations/runtime_status_surface.py`
- Modify: `tests/unit/test_runtime_status_surface.py`

**Step 1: Write failing tests**

Add tests for:
- `test_collect_git_status_reports_branch_and_dirty_flag_for_local_repo()`
- `test_collect_git_status_marks_unavailable_outside_git_repo()`
- `test_collect_git_status_does_not_call_remote_commands()`
- `test_working_directory_is_redacted_to_home_relative_path()`

**Step 2: Run tests to verify RED**

```bash
python3 -m pytest tests/unit/test_runtime_status_surface.py -q
```

Expected: FAIL for missing Git collector behavior.

**Step 3: Implement local Git collector**

Add `collect_local_git_context(repo_root: Path | None, working_directory: Path | None) -> dict[str, object]`.

Allowed commands:
```bash
git -C <repo> rev-parse --abbrev-ref HEAD
git -C <repo> status --porcelain
git -C <repo> rev-parse --short HEAD
```

Disallowed commands:
- `git fetch`
- `git pull`
- `git push`
- any command that contacts a remote.

**Step 4: Run tests to verify GREEN**

```bash
python3 -m pytest tests/unit/test_runtime_status_surface.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/hisys/operations/runtime_status_surface.py tests/unit/test_runtime_status_surface.py
git commit -m "feat: collect local git context for status surfaces"
```

---

## Milestone 2: CLI command and artifact writing

**Objective:** Add the `runtime-status-surface` CLI command that writes JSON/Markdown artifacts under the instance root.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Modify/Create: `tests/unit/test_runtime_status_surface_cli.py`
- Modify: `docs/public/agent-tool-manual.md` or `docs/public/public-beta-manual.md` with the new read-only command.

**Step 1: Write failing CLI tests**

Add subprocess tests for:
- `test_runtime_status_surface_cli_writes_json_and_markdown()`
- `test_runtime_status_surface_cli_json_output_contains_safe_boundary_flags()`
- `test_runtime_status_surface_cli_text_output_is_redacted()`
- `test_runtime_status_surface_cli_rejects_unredacted_secret_like_input()`

Use `PYTHONPATH=src` in subprocess tests if needed, matching the known Hisys subprocess test pitfall.

**Step 2: Run tests to verify RED**

```bash
python3 -m pytest tests/unit/test_runtime_status_surface_cli.py -q
```

Expected: FAIL because the CLI command is not registered.

**Step 3: Register CLI parser**

Add parser near `health-status` / `completion-status` style commands:
```text
runtime-status-surface
```

Recommended flags:
```bash
--instance <path>
--date YYYYMMDD
--request-id REQ-...
--working-directory <path>
--repo-root <path>
--model <model-name>
--provider <provider-name>
--session-id <safe-session-id>
--context-used <int>
--context-limit <int>
--cost-usd <decimal>
--approval-state <state>
--approval-ref <ref>
--format text|json
```

Add `_cmd_runtime_status_surface(...) -> int` that:
1. builds the packet;
2. writes JSON and Markdown artifacts;
3. prints either compact text or JSON summary;
4. returns nonzero on redaction failure.

**Step 4: Run tests to verify GREEN**

```bash
python3 -m pytest tests/unit/test_runtime_status_surface_cli.py tests/unit/test_runtime_status_surface.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/hisys/cli/main.py src/hisys/operations/runtime_status_surface.py tests/unit/test_runtime_status_surface_cli.py docs/public/agent-tool-manual.md
git commit -m "feat: add runtime status surface CLI"
```

---

## Milestone 3: Documentation and operator examples

**Objective:** Document how Hisys status packets relate to Claude Code statusline and Hermes runtime visibility without implementing live adapters.

**Files:**
- Create: `docs/public/runtime-status-surface.md`
- Modify: `docs/public/agent-tool-manual.md`
- Optionally modify: `docs/traceability/README.md`

**Step 1: Write the public operator doc**

Include:
- command purpose;
- example command;
- example compact output;
- artifact paths;
- redaction rules;
- boundary statement: no external calls, no runtime mutation;
- future adapter note for Claude Code/Hermes/tmux.

Example command:
```bash
hisys runtime-status-surface \
  --instance /tmp/hisys-status-demo \
  --date 20260519 \
  --request-id REQ-STATUS-DEMO-001 \
  --working-directory /home/cbchoi/workspaces/develop/repos/hisys \
  --repo-root /home/cbchoi/workspaces/develop/repos/hisys \
  --provider openai-codex \
  --model gpt-5.5 \
  --approval-state human_approved_plan_only \
  --approval-ref DISCORD-20260519-STATUS-SURFACE \
  --format text
```

**Step 2: Run doc and command checks**

```bash
python3 -m pytest tests/unit/test_runtime_status_surface.py tests/unit/test_runtime_status_surface_cli.py -q
python3 -m hisys.cli.main runtime-status-surface --instance /tmp/hisys-status-demo --date 20260519 --request-id REQ-STATUS-DEMO-001 --working-directory /home/cbchoi/workspaces/develop/repos/hisys --repo-root /home/cbchoi/workspaces/develop/repos/hisys --approval-state human_approved_plan_only --approval-ref DISCORD-20260519-STATUS-SURFACE --format text
```

Expected: tests pass; CLI writes JSON/Markdown and prints a redacted compact line.

**Step 3: Commit**

```bash
git add docs/public/runtime-status-surface.md docs/public/agent-tool-manual.md docs/traceability/README.md
git commit -m "docs: document runtime status surface CLI"
```

---

## Milestone 4: Release gates

**Objective:** Validate the complete local/read-only implementation before any runtime deployment or Hermes integration.

**Focused validation:**
```bash
python3 -m pytest tests/unit/test_runtime_status_surface.py tests/unit/test_runtime_status_surface_cli.py -q
```

**Relevant CLI regression validation:**
```bash
python3 -m pytest tests/unit/test_release_ops_cli.py tests/unit/test_completion_status_cli.py tests/unit/test_cli_runtime.py -q
```

**Project gates:**
```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short
```

**Full validation before merge/release:**
```bash
python3 -m pytest
```

**Acceptance criteria:**
- `runtime-status-surface` writes JSON and Markdown artifacts under the instance root.
- JSON contains `external_call_made=false`, `mutation_performed=false`, and `action_taken=none`.
- Text output contains no raw secrets or unredacted private paths.
- Local Git status collection never invokes remote commands.
- Documentation clearly states this is a status packet/reporting surface, not a live statusline adapter.

---

## Deferred Work

1. **Claude Code statusline adapter**
   - Build a separate script/template that renders Hisys packet fields in Claude Code's statusline mechanism.
   - Requires separate local operator approval because it mutates local Claude Code settings or shell config.

2. **Hermes TUI/footer integration**
   - Consume the same packet shape or field policy in Hermes UI surfaces.
   - Requires ai.persona/Hermes repo changes and runtime restart approval.

3. **tmux/Ralph loop status integration**
   - Add a status provider for long-running Ralph/agent loops.
   - Must preserve approval state and avoid leaking private workspace paths.

4. **Cost/context auto-collection**
   - Initial implementation should accept cost/context values as explicit inputs.
   - Auto-reading provider/gateway telemetry requires a separate boundary review.
