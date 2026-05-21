# Milestone M21.9-CLI — Subagent Evidence Packet Validator CLI Wrapper Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. This plan is the document-RED/Prepare artifact for a thin CLI wrapper around the M21.9.1 pure validator. The wrapper validates caller-supplied JSON packet files only. It does not execute subagents.

**Goal:** Add a thin `hisys validate-subagent-evidence-packet --task <json> [--result <json>]` CLI subcommand that loads explicit JSON object files, validates them through `validate_subagent_evidence_task_packet(...)` and optionally `validate_subagent_evidence_result_packet(..., task=task)`, prints bounded advisory summary lines, and returns `0` when supplied packets validate.

**Architecture:** Reuse existing surfaces:

- Pure validator: `src/hisys/contracts/subagent_evidence_collector.py`.
- CLI dispatcher/parser: `src/hisys/cli/main.py`.
- CLI tests: `tests/unit/test_domain_cli.py`.

The CLI must not change packet semantics, must not execute a subagent, must not verify artifact existence, must not auto-discover packet files, must not call `delegate_task`, must not call `subprocess`, must not read `.git/`, must not access network/browser/model tools, must not mutate files except normal test temp files and validation output, and must not add approval/promotion authority.

---

## Boundary decisions

1. **Explicit JSON paths only.** `--task` is required. `--result` is optional. No directory crawling or latest-packet discovery.
2. **Validation only.** The CLI validates packet shape and boundary flags. It does not execute or simulate a subagent and does not verify that `artifact_refs` exist.
3. **Exit code.** A successfully validated packet set returns `0`. Validation errors may propagate as non-zero exceptions; adding a structured error-report writer is deferred.
4. **Summary lines.** On success print `validate-subagent-evidence-packet: ok`, `task_id: <id>`, `result_supplied: true|false`, `artifact_ref_count: <n>`, `source_ref_count: <n>`, `advisory_only: true`, `requires_human_review: true`, `external_call_made: false`, `mutation_performed: false`, `raw_source_content_persisted: false`, and `allowed_actions: advisory_only`.
5. **No writer in first wrapper.** The wrapper prints only; it does not persist runtime-boundary artifacts. A future report writer requires a separate Prepare/RED.

---

## Task M21.9-CLI-PREP: Prepare/document-RED wrapper

**Files:**

- Create: `docs/plans/m21-9-cli-subagent-evidence-packet-validator-implementation-tasks.md`
- Update: `ralph.md`

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:** `docs: prepare subagent evidence packet validator cli`

---

## Task M21.9-CLI: Thin CLI wrapper (RED -> GREEN)

**Files:**

- Modify: `tests/unit/test_domain_cli.py`
- Modify: `src/hisys/cli/main.py`
- Update: `docs/traceability/README.md`
- Update: `ralph.md`

**First RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_validate_subagent_evidence_packet_cli_accepts_task_and_result -q
```

Expected failure: argparse rejects the missing `validate-subagent-evidence-packet` subcommand with `SystemExit: 2`.

**Minimum behavior:**

- Load `--task` and optional `--result` as JSON objects using the existing `_load_json_report` helper or an equivalent object-only loader.
- Validate task packet through `validate_subagent_evidence_task_packet`.
- If result is supplied, validate through `validate_subagent_evidence_result_packet(..., task=task)`.
- Print bounded summary lines and return `0` on successful validation.
- Preserve the no-execution/no-live/no-mutation boundary.

**Focused validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_validate_subagent_evidence_packet_cli_accepts_task_and_result tests/unit/test_subagent_evidence_collector_protocol.py -q
PYTHONPATH=src pytest tests/unit/test_domain_cli.py tests/unit/test_subagent_evidence_collector_protocol.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Stop / continue rule

Stop after this Prepare package is committed if continuing into the CLI wrapper is not authorized. If continuing is authorized, proceed with the RED test above. Stop immediately if the wrapper would need to execute a subagent, verify filesystem artifacts, call external tools, mutate repositories, or add approval/promotion semantics.
