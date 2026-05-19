# DARS Critic Panel M-CP-EXT-6 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the `MB-DARS-CP-EXT6-T001` document-RED/Prepare artifact. It authorizes only local RED/GREEN work for a read-only `hisys run-dars-panel` CLI wrapper over the existing fixture-local `DarsCriticPanelRuntime.run_round` surface.

**Goal:** Implement `M-CP-EXT-6` from `docs/plans/dars-critic-panel-platform-runtime-next.md`: add a read-only CLI entry point that runs the already-implemented DARS critic panel runtime from an explicit local JSON config and local candidate/evidence/rubric refs, persists the existing advisory artifacts, and prints an operator-safe summary. The command must not add live dispatch, external calls, mutation authority, publication, credential resolution, process spawning, or bounded-parallel execution.

**Architecture:** Add a small CLI handler in `src/hisys/cli/main.py` that parses an explicit panel config JSON file into `DarsCriticPanelConfig` / `DarsCriticRoleConfig`, constructs `DarsCriticPanelRuntime(instance=InstanceRoot(...))` with the default fixture policy, and calls `run_round(...)`. Keep the runtime implementation unchanged except for helper functions only if the CLI needs a pure config loader. Do not add a new service module unless the CLI handler would exceed a small parsing boundary. The CLI consumes the existing runtime and writer surfaces: critique/synthesis/round-trace artifacts remain under `data/dars-panel/<YYYYMMDD>/<REQUEST_ID>/`, and execution-boundary records remain under `runtime-boundary/dars-panel/<YYYYMMDD>/<REQUEST_ID>/`.

**Tech Stack:** Python 3.11, argparse, dataclasses, JSON, pytest. No new runtime dependency. No network/browser/CLI subprocess dependency.

**Context Packet:** Required source handles are `docs/plans/dars-critic-panel-platform-runtime-next.md`, `docs/plans/dars-critic-panel-mcp-ext-7-implementation-tasks.md`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `src/hisys/agents/dars_panel.py`, `src/hisys/agents/dars_panel_graph.py`, `src/hisys/cli/main.py`, `tests/unit/test_dars_critic_panel_runtime.py`, `tests/unit/test_dars_critic_panel_adapters.py`, `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`, and `tests/unit/test_dars_critic_panel_execution_graph_plan.py`. Validation handles are the new CLI test, the focused panel regression, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized by this plan. Live DARS dispatch, external adapter activation, browser/network calls, credential resolution, publication, destructive Git, actual bounded-parallel execution, and any operator approval of downstream decisions are out of scope. The advisory-only invariants from M-CP-EXT-1/2/3/4/5/7 remain mandatory.

---

## Accepted decisions

1. **Command name:** add `hisys run-dars-panel`. The name matches the deferred item recorded in the parent runtime-next plan and the M-CP-EXT-5/7 reflection entries.
2. **Config format:** accept a local JSON file through `--panel-config`. The file contains `panel_id`, `max_parallel_critics`, optional `failure_policy`, optional `advisory_only`, optional `default_output_contract`, and `critics[]` entries matching `DarsCriticRoleConfig` field names. YAML is deferred to avoid adding parsing ambiguity beyond the already available JSON stack.
3. **Explicit data refs:** require `--candidate-ref`, allow repeated `--evidence-ref`, and pass refs through unchanged to `run_round`. The command does not read or copy candidate/evidence/rubric payloads; runtime artifacts preserve refs only.
4. **Read-only fixture default:** construct `DarsCriticPanelRuntime(instance=InstanceRoot(instance_root))` without a caller-supplied registry. This uses the default fixture policy and preserves existing blocked behavior for `external-*` backends. Do not add CLI flags for external dispatch, adapter registry loading, credential refs, or approval overrides in this increment.
5. **Approval ref policy:** the command may consume `approval_ref` values already present in the local panel config because the runtime dataclass already has that field, but the default registry still blocks external adapters unless its own external-dispatch gate is enabled. The CLI must not introduce any flag that enables external dispatch.
6. **Output formats:** support `--format json|text` and default to `text`. JSON output should include `request_id`, `panel_id`, `execution_mode`, `task_statuses`, `critique_refs`, `synthesis_ref`, `round_trace_ref`, and `execution_boundary_refs`. Text output should print the same refs in an operator-readable bounded summary.
7. **Exit codes:** return `0` when `run_round` completes and persists the round, even if individual critic tasks are `blocked` or `failed`; those are typed advisory outcomes, not CLI infrastructure failures. Return non-zero only for invalid CLI inputs/config parsing or uncaught runtime invariant errors.
8. **No bounded-parallel activation:** if `max_parallel_critics > 1`, the runtime may continue reporting `execution_mode="bounded_parallel"` as it already does, but execution remains serial. The CLI must not spawn workers, threads, subprocesses, or async tasks.
9. **Traceability:** document the command as a read-only runtime wrapper, not as DARS enablement. The command does not approve decisions or execute recommendations.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the repository state and current GREEN baseline before writing the RED CLI test.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:**

- Branch is `dars`.
- Existing focused suites report `43 passed`.
- Working tree is clean or contains only intentional changes for this increment.

---

## Task 1: RED/GREEN — CLI runs a fixture-local panel round and prints safe JSON

**Objective:** Pin the new CLI behavior with a failing test, then add the minimal parser/handler wiring.

**Files:**

- Create: `tests/unit/test_dars_critic_panel_cli.py`
- Modify: `src/hisys/cli/main.py`

**Step 1: Write failing test**

Create `tests/unit/test_dars_critic_panel_cli.py`:

```python
"""DARS critic panel CLI tests.

Traceability:
- HISYS-FR-DARS-CP-001
- HISYS-FR-DARS-CP-003
- HISYS-FR-DARS-CP-007
- HISYS-NFR-DARS-CP-001
- M-CP-EXT-6 in docs/plans/dars-critic-panel-platform-runtime-next.md
"""

from __future__ import annotations

import json
from pathlib import Path


def _candidate_fixture(tmp_path: Path) -> tuple[str, list[str], str]:
    data_dir = tmp_path / "data" / "dars-panel-fixtures" / "20260520"
    data_dir.mkdir(parents=True)
    candidate = data_dir / "candidate-001.json"
    evidence = data_dir / "evidence-001.json"
    rubric = data_dir / "rubric-001.md"
    candidate.write_text('{"candidate_id":"candidate-001"}\n', encoding="utf-8")
    evidence.write_text('{"evidence_id":"evidence-001"}\n', encoding="utf-8")
    rubric.write_text("# Rubric\n", encoding="utf-8")
    return (
        str(candidate.relative_to(tmp_path)),
        [str(evidence.relative_to(tmp_path))],
        str(rubric.relative_to(tmp_path)),
    )


def test_run_dars_panel_cli_persists_fixture_round_and_prints_json(tmp_path: Path, capsys):
    """M-CP-EXT-6: CLI wraps the fixture-local advisory panel runtime."""

    from hisys.cli.main import main

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config_path = tmp_path / "panel-config.json"
    config_path.write_text(
        json.dumps(
            {
                "panel_id": "PANEL-DARS-CP-EXT-6",
                "max_parallel_critics": 1,
                "critics": [
                    {
                        "critic_id": "logical-devil",
                        "critic_role": "logical_devil",
                        "backend_id": "fixture-logical-cli-001",
                        "rubric_ref": rubric_ref,
                        "critique_dimensions": ["logical_validity"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-dars-panel",
            "--instance",
            str(tmp_path),
            "--date",
            "20260520",
            "--request-id",
            "REQ-DARS-CP-EXT-6",
            "--panel-config",
            str(config_path),
            "--candidate-ref",
            candidate_ref,
            "--evidence-ref",
            evidence_refs[0],
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["request_id"] == "REQ-DARS-CP-EXT-6"
    assert payload["panel_id"] == "PANEL-DARS-CP-EXT-6"
    assert payload["execution_mode"] == "serial"
    assert payload["task_statuses"] == {"TASK-REQ-DARS-CP-EXT-6-logical-devil": "completed"}
    assert len(payload["critique_refs"]) == 1
    assert payload["synthesis_ref"].endswith("synthesis.json")
    assert payload["round_trace_ref"].endswith("round-trace.json")
    assert len(payload["execution_boundary_refs"]) == 1

    for ref in payload["critique_refs"] + [payload["synthesis_ref"], payload["round_trace_ref"]] + payload["execution_boundary_refs"]:
        assert (tmp_path / ref).exists()
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py::test_run_dars_panel_cli_persists_fixture_round_and_prints_json -q
```

**Expected RED:** argparse exits because `run-dars-panel` is not a known subcommand (or the test errors with an equivalent missing-command failure). Confirm the failure is command absence, not a fixture typo.

**Step 3: Minimal GREEN implementation**

In `src/hisys/cli/main.py`:

1. Import the DARS panel runtime dataclasses near the other imports or inside the new handler:

```python
from hisys.agents.dars_panel import (
    DarsCriticPanelConfig,
    DarsCriticPanelRuntime,
    DarsCriticRoleConfig,
)
```

2. Add a small pure loader:

```python
def _load_dars_panel_config(path: Path) -> DarsCriticPanelConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    critics = [DarsCriticRoleConfig(**item) for item in payload.get("critics", [])]
    return DarsCriticPanelConfig(
        panel_id=payload["panel_id"],
        critics=critics,
        max_parallel_critics=int(payload.get("max_parallel_critics", 1)),
        failure_policy=payload.get("failure_policy", "continue_collect_errors"),
        advisory_only=bool(payload.get("advisory_only", True)),
        default_output_contract=payload.get("default_output_contract", "DarsCritiqueRecord"),
    )
```

3. Add `_cmd_run_dars_panel(...)` that constructs `DarsCriticPanelRuntime(instance=InstanceRoot(instance_root))`, calls `run_round(...)`, builds the bounded summary dictionary, prints JSON/text, and returns `0`.

4. Add the `run-dars-panel` argparse subcommand with required `--instance`, `--date`, `--request-id`, `--panel-config`, `--candidate-ref`, optional repeated `--evidence-ref`, and `--format json|text`.

5. Dispatch the parsed command in `main(...)`.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected GREEN:** new CLI test passes; existing focused panel + adapters + tool-execution + graph suites remain GREEN.

---

## Task 2: RED/GREEN — CLI blocks external-style backend without enabling live dispatch

**Objective:** Pin the safety boundary: the CLI must surface typed blocked outcomes for `external-*` backends but must not activate an external adapter or fail the whole command.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_cli.py`
- Modify: `src/hisys/cli/main.py` only if Task 1 output does not already expose the blocked status clearly.

**Step 1: Add failing or characterization test**

Add a second test that writes a panel config with `backend_id="external-cli-backend"`, runs the CLI with `--format json`, and asserts:

- exit code is `0`;
- `task_statuses` contains `"blocked"` for the critic task;
- no critique refs were produced;
- one execution-boundary ref exists;
- the boundary record has `dispatch_decision="blocked"`, `external_call_made=false`, `mutation_performed=false`, `action_authorized=false`, `advisory_only=true`, `requires_human_review=true`, and `adapter_class="unresolved"` or the resolved external adapter class only if a future explicit registry path is added.

**Step 2: Verify RED/characterization**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py::test_run_dars_panel_cli_blocks_external_backend_without_live_dispatch -q
```

If this passes immediately after Task 1 because the default fixture policy already blocks external backends and the JSON summary is complete, record it as a characterization pass in the Reflection Log. If it fails because the summary omits blocked status or boundary refs, update only `_cmd_run_dars_panel` output shaping.

**Step 3: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py -q
```

---

## Task 3: Documentation and traceability update

**Objective:** Record M-CP-EXT-6 in the DARS critic panel RTM, traceability summary README, and Ralph reflection log.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md` (bump version to `0.8.0`, dated `2026-05-20`; add the new pytest anchor to the HISYS-FR-DARS-CP-001, HISYS-FR-DARS-CP-003, HISYS-FR-DARS-CP-007, and HISYS-NFR-DARS-CP-001 rows; add a new `M-CP-EXT-6 — Read-only run-dars-panel CLI (2026-05-20)` section).
- Modify: `docs/traceability/README.md` (add an `M-CP-EXT-6` row after the DARS clock/unresolved rows, enumerating the CLI command, JSON config loader, advisory artifact refs, blocked external-style backend behavior, and gate command).
- Modify: `ralph.md` (append a new Reflection Log entry covering Prepare/RED/GREEN/Refactor/Gate, controlled anchors, RED command + observed failure, GREEN command + pass result, quality gate result, potential issues / open items, success likelihood, continue decision, and a resume checkpoint).

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 4: Full quality gate and local commit

**Objective:** Validate the complete M-CP-EXT-6 implementation and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- New CLI tests pass alongside existing focused panel + adapters + tool-execution + graph suites.
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/cli/main.py \
  tests/unit/test_dars_critic_panel_cli.py \
  docs/plans/dars-critic-panel-mcp-ext-6-implementation-tasks.md \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: add read-only DARS panel CLI"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The implementation requires adding network/browser/process-spawn dependencies, non-fixture adapter activation, credential resolution, or an external dispatch enable flag.
- The CLI would need to mutate existing candidate/evidence/rubric files instead of only persisting runtime-local artifacts under the instance root.
- The CLI must approve a DARS recommendation, publish output, execute an action, or alter `advisory_only` / `requires_human_review` invariants.
- Existing focused panel tests fail for a reason not directly tied to CLI output shaping.
- Traceability validator, secret scan, or `git diff --check` fails.

## Next increment candidates after M-CP-EXT-6

- Per-task `started_at` / `completed_at` distinct from the single round-level timestamp.
- Package split of the increasingly large `src/hisys/agents/dars_panel.py` into adapter/runtime/record modules after a behavior-preserving plan.
- Future bounded-parallel execution activation, only after a separate governance/approval increment and fixture scheduler harness.
