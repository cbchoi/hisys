# Hisys Live LSP RLOO Control Plan

> Active control file for `/rloo` in this repository. The previous long-form control log was moved to `ralph.history.md`. This file is intentionally short, step-by-step, and executable in one local-safe RLOO pass.

## 0. Control Metadata

| Field | Value |
|---|---|
| Plan ID | `RALPH-HISYS-LIVE-LSP-RLOO-2026-05-23` |
| Repository | `/home/cbchoi/workspaces/develop/repos/hisys` |
| Branch | `dars` |
| Baseline at plan creation | `dcf4f81` |
| Previous control file | `ralph.history.md` |
| Runtime | one coherent RLOO pass, maximum 5 hours |
| Active task | `LIVE-LSP-SMOKE-REFRESH` |
| User authorization | 최창범 교수 requested: `live lsp를 rloo돌릴 수 있도록 하자... 사용자 approval이 없고 단번에 끝낼 수 있도록 step by step ralph.md 작성.` |

## 1. Objective

Run a fresh local live LSP/lint smoke through the already-governed Hisys LSP adapter, then record bounded evidence so the result can be reviewed without further user approval.

The target outcome is not a readiness/compliance claim. The target outcome is a local advisory evidence refresh:

- `ruff` live diagnostic report for the Hisys Python tree;
- `pyright` live diagnostic report for the existing LSP adapter module;
- a concise Markdown smoke report under `docs/reports/`;
- a traceability row linking the report and runtime-boundary JSON/Markdown artifacts;
- local validation and a coherent local commit.

## 2. Continuous Local-Safe Authorization

The current user request authorizes Ralph/RLOO to complete every step in this file without asking for another approval, as long as the action stays inside this envelope:

- local file edits in this repository;
- local subprocess execution only through the existing `hisys lsp-adapter` CLI and `src/hisys/operations/lsp_adapter.py` runner;
- existing executable allowlist only: `ruff`, `pyright`;
- existing local tool locations only: `/home/cbchoi/.hermes/hermes-agent/venv/bin` and `/home/cbchoi/.hermes/hisys-lsp-tools/node_modules/.bin` may be prepended to `PATH`;
- no package installation;
- no command allowlist expansion;
- no credential lookup;
- no network fetch/clone/search;
- no remote provider/model call;
- no publication, deployment, release, PR, issue, or external API side effect;
- no raw source archival beyond normal repository files already present;
- no raw diagnostic message persistence outside the LSP adapter's bounded JSON/Markdown report shape;
- no mutation/fix/apply command such as `ruff --fix`;
- normal local git commit after gates pass.

### Approval minimization rule

Do not ask for human approval merely because the next step is PREP bookkeeping, bundle creation, local live LSP execution through the governed adapter, report generation, traceability update, validation, or a local commit. Ask only if the next required action crosses a boundary listed in Section 3.

## 3. Stop Conditions

Stop immediately and record the blocker in this file if any required next action would need:

1. installing or upgrading `ruff`, `pyright`, `eslint`, Python packages, Node packages, system packages, or language servers;
2. adding another executable such as `mypy`, `flake8`, `eslint`, `npm`, `npx`, `python -m`, `bash`, or an absolute binary path to the allowlist;
3. running a fixer, formatter with write mode, migration, destructive shell command, branch reset, force checkout, history rewrite, or force push;
4. network access, repository clone/fetch, web search, browser/tool execution, credential lookup, token/key/secret access, provider/model execution, or external API mutation;
5. pushing to a new/unclear remote or branch;
6. changing product scope, declaring DARS completion, declaring production/release readiness, or removing `requires_human_review=true`;
7. unresolved dirty working tree unrelated to this plan;
8. validation failures that cannot be fixed with local docs/control or fixture-safe code edits within this plan.

## 4. Controlled Anchors to Read First

Before action, read or inspect these anchors:

- `ralph.md` — this active file;
- `ralph.history.md` — historical context only, do not append to it during this run;
- `docs/reports/m23-live-lsp-server-smoke.md`;
- `docs/plans/m23-lsp-adapter-implementation-tasks.md`;
- `docs/plans/m23-cli-lsp-adapter-implementation-tasks.md`;
- `src/hisys/operations/lsp_adapter.py`;
- `src/hisys/cli/main.py`;
- existing runtime reports under `runtime-boundary/lsp-adapter/20260522/`;
- `docs/traceability/README.md`;
- `docs/milestone-bootstrap/profile.yaml` and `tests/unit/test_governance_docs_current_state.py` for current governance state.

## 5. Task Queue

### Task 0 — Reconstruct state

Run:

```bash
git status --short --branch
git rev-parse --short HEAD
git log --oneline -5
command -v ruff || true
PATH="/home/cbchoi/.hermes/hisys-lsp-tools/node_modules/.bin:$PATH" command -v pyright || true
PYTHONPATH=src:. pytest tests/unit/test_lsp_adapter.py tests/unit/test_domain_cli.py tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected:

- branch is `dars`;
- working tree is clean or only contains this RLOO plan/history transition if this setup commit has not yet been made;
- `ruff` and `pyright` are available through the existing paths;
- focused LSP/CLI/governance tests pass;
- traceability OK;
- secret scan `hit_count=0`;
- `git diff --check` clean.

If the only missing item is `ruff` or `pyright`, stop. Do not install or expand the allowlist.

### Task 1 — PREP: create caller-authored live LSP bundles

Create `build/live-lsp-smoke-refresh/20260523/` and write exactly two bundle JSON files.

Use this command block:

```bash
mkdir -p build/live-lsp-smoke-refresh/20260523
python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

repo = Path.cwd().resolve()
out = repo / "build" / "live-lsp-smoke-refresh" / "20260523"
out.mkdir(parents=True, exist_ok=True)
approval = "ralph.md#continuous-local-safe-authorization"

bundles = {
    "ruff-live-refresh.json": {
        "workspace_root": str(repo),
        "command": {
            "command_id": "ruff-check-live-refresh",
            "argv": [
                "ruff",
                "check",
                "--output-format=json",
                "src",
                "tests/unit/test_lsp_adapter.py",
            ],
            "timeout_seconds": 120,
            "expected_exit_codes": [0, 1],
            "output_format": "ruff_json",
        },
        "target_refs": ["src", "tests/unit/test_lsp_adapter.py"],
        "command_allowlist": ["ruff"],
        "human_approval_ref": approval,
    },
    "pyright-live-refresh.json": {
        "workspace_root": str(repo),
        "command": {
            "command_id": "pyright-check-live-refresh",
            "argv": [
                "pyright",
                "--outputjson",
                "src/hisys/operations/lsp_adapter.py",
            ],
            "timeout_seconds": 120,
            "expected_exit_codes": [0, 1],
            "output_format": "pyright_json",
        },
        "target_refs": ["src/hisys/operations/lsp_adapter.py"],
        "command_allowlist": ["pyright"],
        "human_approval_ref": approval,
    },
}

for name, payload in bundles.items():
    (out / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
python3 -m json.tool build/live-lsp-smoke-refresh/20260523/ruff-live-refresh.json >/dev/null
python3 -m json.tool build/live-lsp-smoke-refresh/20260523/pyright-live-refresh.json >/dev/null
```

Do not commit files under `build/` unless the repository policy already tracks that path. They are caller-authored runtime inputs, not durable evidence.

### Task 2 — ACTION: run governed live LSP smoke

Run the two bundles through the existing CLI. Use exactly this PATH extension and no package installation:

```bash
HEAD_SHORT="$(git rev-parse --short HEAD)"
PATH="/home/cbchoi/.hermes/hermes-agent/venv/bin:/home/cbchoi/.hermes/hisys-lsp-tools/node_modules/.bin:$PATH" \
PYTHONPATH=src:. python -m hisys.cli.main lsp-adapter \
  --instance . \
  --date 20260523 \
  --bundle build/live-lsp-smoke-refresh/20260523/ruff-live-refresh.json \
  --current-head-short "$HEAD_SHORT"
PATH="/home/cbchoi/.hermes/hermes-agent/venv/bin:/home/cbchoi/.hermes/hisys-lsp-tools/node_modules/.bin:$PATH" \
PYTHONPATH=src:. python -m hisys.cli.main lsp-adapter \
  --instance . \
  --date 20260523 \
  --bundle build/live-lsp-smoke-refresh/20260523/pyright-live-refresh.json \
  --current-head-short "$HEAD_SHORT"
```

Expected durable runtime artifacts:

- `runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.json`
- `runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.md`
- `runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.json`
- `runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.md`

Expected report flags in both JSON files:

- `advisory_only: true`
- `requires_human_review: true`
- `external_call_made: false`
- `mutation_performed: false`
- `raw_source_content_persisted: false`
- `live_external_action_authorized: false`
- `allowed_actions: advisory_only`

Do not treat a nonzero subprocess exit code as failure if it is `1`; lint/type tools may exit `1` to indicate diagnostics. The evidence refresh succeeds if the adapter emits bounded reports and validation passes.

### Task 3 — REVIEW: write bounded smoke report

Create `docs/reports/live-lsp-smoke-refresh-2026-05-23.md` by reading only the generated LSP report JSON summaries. The report must include:

- request context;
- exact command ids;
- runtime artifact refs;
- diagnostic counts and severity counts;
- subprocess exit code/time-out/truncation fields;
- boundary statement;
- statement that the result is advisory evidence only and requires human review.

Use this helper if useful:

```bash
python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

refs = [
    "runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.json",
    "runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.json",
]
rows = []
for ref in refs:
    data = json.loads(Path(ref).read_text(encoding="utf-8"))
    rows.append((ref, data))

lines = [
    "# Live LSP smoke refresh report — 2026-05-23",
    "",
    "## Request",
    "",
    "최창범 교수 requested a live LSP RLOO control plan that can run without further user approval and finish in one stepwise pass.",
    "",
    "## Runtime evidence",
    "",
    "| Tool command id | Output format | Diagnostics | Errors | Warnings | Info | Exit | Timed out | Truncated | Runtime report |",
    "|---|---|---:|---:|---:|---:|---:|---|---|---|",
]
for ref, data in rows:
    lines.append(
        "| {command_id} | {output_format} | {diagnostic_count} | {error_count} | {warning_count} | {info_count} | {subprocess_exit_code} | {subprocess_timed_out} | {output_truncated} | `{ref}` |".format(
            ref=ref,
            **data,
        )
    )
lines.extend([
    "",
    "## Boundary",
    "",
    "Execution used only the existing governed `hisys lsp-adapter` boundary with caller-authored bundles, existing `ruff` and `pyright` executables, no package installation, no credential lookup, no network fetch/clone/search, no provider/model call, no mutation/fix command, no publication/deployment/release, and no command allowlist expansion.",
    "",
    "The generated reports preserve `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `live_external_action_authorized=false`, and `allowed_actions=advisory_only`.",
    "",
    "This report is an advisory local evidence refresh only. It does not declare DARS completion, production readiness, release readiness, compliance, or removal of human review.",
    "",
])
Path("docs/reports/live-lsp-smoke-refresh-2026-05-23.md").write_text("\n".join(lines), encoding="utf-8")
PY
```

### Task 4 — TRACE: update traceability and this control file

Prepend one row to `docs/traceability/README.md`:

```markdown
| Live LSP smoke refresh (LIVE-LSP-SMOKE-REFRESH-2026-05-23) | ralph.md; docs/reports/live-lsp-smoke-refresh-2026-05-23.md; runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.json; runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.md; runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.json; runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.md | User authorized a local live LSP RLOO path without further approval. RLOO ran existing ruff/pyright executables through the governed Hisys LSP adapter, recorded bounded advisory diagnostics, and preserved no-network/no-credential/no-mutation/no-publication boundaries. |
```

Then append a short Reflection Log entry to Section 8 of this file with:

- HEAD before run;
- command ids run;
- generated artifact refs;
- validation results;
- commit message;
- next stop condition.

Do not edit `ralph.history.md` during the run.

### Task 5 — VALIDATE and COMMIT

Run:

```bash
PYTHONPATH=src:. pytest tests/unit/test_lsp_adapter.py tests/unit/test_domain_cli.py tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

If these pass, commit exactly the durable files:

```bash
git add ralph.md ralph.history.md docs/reports/live-lsp-smoke-refresh-2026-05-23.md docs/traceability/README.md runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.json runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.md runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.json runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.md
git commit -m "docs: refresh live lsp smoke evidence"
```

Do not push unless the active repository policy and current RLOO invocation explicitly call for normal synchronization. The current task only requires preparing and running the local RLOO path.

## 6. Quality Gates

A completed pass requires:

- both generated LSP JSON reports exist;
- both Markdown reports exist;
- smoke report exists under `docs/reports/`;
- traceability validator passes;
- secret scan reports `hit_count=0`;
- `git diff --check` is clean;
- focused LSP/CLI/governance tests pass;
- local commit succeeds.

## 7. Human Reporting Format

Final report to the user must state:

1. whether the live LSP RLOO pass completed;
2. generated report paths;
3. ruff/pyright diagnostic counts;
4. validation commands and results;
5. commit hash if committed;
6. any stop condition if not completed.

## 8. Reflection Log

### 2026-05-23 — LIVE-LSP-RLOO-CONTROL-PREP

- Phase completed: replaced the oversized active `ralph.md` with this single-purpose live LSP RLOO plan and moved the previous file to `ralph.history.md`.
- Boundary: docs/control setup only. No live LSP subprocess was executed in this setup edit; execution is delegated to `/rloo` following the queue above.
- Current HEAD: 00b1a9f docs: align automatic push checkpoint with dars
- Next task for `/rloo`: `LIVE-LSP-SMOKE-REFRESH`, starting at Task 0.
- Stop condition: only the Section 3 true boundary crossings require user input; ordinary local PREP/action/review/trace/validate/commit steps continue without further approval.

### 2026-05-23 — LIVE-LSP-SMOKE-REFRESH

- Phase completed: ran the bounded live LSP RLOO pass end-to-end per Tasks 0–5 of this plan, without further user approval, inside the Section 2 envelope.
- HEAD before run: 3ce9ab1 docs: prepare live lsp rloo plan.
- Command ids run: `ruff-check-live-refresh` and `pyright-check-live-refresh`, both through the governed `hisys lsp-adapter` boundary with caller-authored bundles under `build/live-lsp-smoke-refresh/20260523/` and PATH extended only to `/home/cbchoi/.hermes/hermes-agent/venv/bin` and `/home/cbchoi/.hermes/hisys-lsp-tools/node_modules/.bin`.
- Generated runtime artifacts: `runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.json`, `.../lsp-report.md`, `runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.json`, `.../lsp-report.md`. Smoke report: `docs/reports/live-lsp-smoke-refresh-2026-05-23.md`. Traceability row prepended to `docs/traceability/README.md` as `LIVE-LSP-SMOKE-REFRESH-2026-05-23`.
- Diagnostic counts: ruff `diagnostic_count=14` (errors=14, warnings=0, info=0, exit=1), pyright `diagnostic_count=2` (errors=2, warnings=0, info=0, exit=1). Both reports preserve `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `live_external_action_authorized=false`, `allowed_actions=advisory_only`. Nonzero exit `1` is the expected diagnostic-present signal for lint/type tools and is not a failure.
- Validation: focused tests `tests/unit/test_lsp_adapter.py tests/unit/test_domain_cli.py tests/unit/test_governance_docs_current_state.py -q` → `46 passed`; `scripts/validate_traceability.py` → OK; `scripts/scan_secrets.py` → `hit_count=0`; `git diff --check` clean.
- Commit message: `docs: refresh live lsp smoke evidence`.
- Boundary: no package installation, no command allowlist expansion, no `--fix`/mutation, no network/credential lookup, no provider/model call, no publication/release, no remote-setup changes, no destructive Git operation.
- Next stop condition: this RLOO pass is complete. Further work requires a fresh `/rloo` invocation or a Section 3 boundary decision; advisory diagnostics still require human review.
