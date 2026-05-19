# DARS Critic Panel M-CP-EXT-4 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the `MB-DARS-CP-EXT4-T001` document-RED/Prepare artifact. It authorizes only local RED/GREEN work for a typed adapter-missing `LookupError` -> `status=blocked` outcome in `DarsCriticPanelRuntime.run_round`.

**Goal:** Implement `M-CP-EXT-4` from `docs/plans/dars-critic-panel-platform-runtime-next.md`: convert the currently uncaught `CriticAdapterRegistry.resolve(...)` `LookupError` path (raised when no adapter is registered for a `(critic_role, backend_id)` pair) into a typed per-task blocked outcome that mirrors the existing `PermissionError` branch. The runtime continues to write one `ExecutionBoundaryRecord` per task and preserves all M-CP-EXT-1/2/3 invariants.

**Architecture:** Modify only `DarsCriticPanelRuntime.run_round` in `src/hisys/agents/dars_panel.py` (add a sibling `except LookupError` arm to the existing `except PermissionError` adapter-resolution block). Reuse the existing `DarsTaskResult(status="blocked")` and `ExecutionBoundaryRecord(dispatch_decision="blocked")` shapes — no new dataclass, no new module, no new CLI, no clock seam. The structural `adapter_class="fixture"` default already in place for `disabled`/`PermissionError` branches applies here too.

**Tech Stack:** Python 3.11, dataclasses, pytest. No new runtime dependency. No network/browser/CLI/process-spawn dependency.

**Context Packet:** Required source handles are `docs/plans/dars-critic-panel-platform-runtime-next.md`, `docs/plans/dars-critic-panel-mcp-ext-3-implementation-tasks.md`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `src/hisys/agents/dars_panel.py`, `tests/unit/test_dars_critic_panel_adapters.py`, `tests/unit/test_dars_critic_panel_runtime.py`, `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`, and `tests/unit/test_dars_critic_panel_execution_graph_plan.py`. Validation handles are the focused panel regression, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized by this plan. Live DARS dispatch, external adapter activation, browser/network calls, credential resolution, publication, destructive Git, CLI activation, and actual bounded-parallel execution are out of scope. The advisory-only invariants from M-CP-EXT-1/2/3 remain mandatory.

---

## Accepted decisions

1. **Scope:** convert `CriticAdapterRegistry.resolve(...)` `LookupError` into a typed `DarsTaskResult(status="blocked")` plus a matching `ExecutionBoundaryRecord(dispatch_decision="blocked", dispatch_reason=<exception text>)`. Do not change `CriticAdapterRegistry.resolve` itself; it continues to raise `LookupError` so callers other than `run_round` can still treat unregistered adapters as a hard configuration error if they prefer.
2. **Exception placement:** add `except LookupError as exc:` as a sibling arm to the existing `except PermissionError as exc:` block inside `run_round`. Both arms emit the same boundary-record shape (`adapter_class="fixture"` structural default, `external_call_made=False`, `mutation_performed=False`).
3. **Reason text:** use `str(exc)` verbatim as the `dispatch_reason` so the existing `LookupError` message (`"no critic adapter registered for role=... backend_id=..."`) flows into the task result and boundary record without re-formatting.
4. **No new field:** do not introduce a `adapter_class="unresolved"` literal in this increment. The M-CP-EXT-2 open item (d) about `adapter_class="unresolved"` remains pinned for a later, separate increment. Reviewers continue to treat `adapter_class="fixture"` on a blocked `reason=no critic adapter registered ...` boundary record as a structural default, not a positive assertion that the role was bound to a fixture adapter.
5. **No CLI / clock / parallel changes:** this increment does not add a CLI, inject a deterministic clock, or activate bounded-parallel execution. M-CP-EXT-5 and M-CP-EXT-6 remain separate increments.
6. **Default fallback registry unaffected:** `_DefaultFixturePolicy` synthesizes adapters on demand and therefore never raises `LookupError`. Only explicit caller-supplied `CriticAdapterRegistry` instances with missing `(role, backend_id)` pairs trigger this branch.
7. **Compatibility:** existing tests that rely on `LookupError` propagating *outside* `run_round` do not exist (none of the current 38 focused panel tests assert that behavior). The new branch is therefore additive, not breaking.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the repository state and current GREEN baseline before writing the RED test.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:**

- Branch is `dars`.
- Existing focused suites report `38 passed`.
- Working tree is clean (or contains only intentional changes for this increment).

---

## Task 1: RED/GREEN — typed adapter-missing yields blocked task result

**Objective:** Pin the new behavior with a failing test, then add the minimal exception arm in `run_round`.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_adapters.py` (preferred home — colocated with the other registry-driven runtime tests).
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing test**

Add to `tests/unit/test_dars_critic_panel_adapters.py`:

```python
def test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role(tmp_path: Path):
    """M-CP-EXT-4: explicit registry without a matching adapter -> typed blocked task."""

    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()  # explicit, no adapters registered

    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-4",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-unregistered",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
        ],
    )

    result = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        adapter_registry=registry,
    ).run_round(
        yyyymmdd="20260520",
        request_id="REQ-DARS-CP-EXT-4",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    assert [task.status for task in result.task_results] == ["blocked"]
    assert result.task_results[0].critique_ref is None
    assert result.task_results[0].external_call_made is False
    assert "no critic adapter registered" in (result.task_results[0].error_message or "")
    assert result.critique_refs == []
    assert len(result.execution_boundary_refs) == 1

    boundary_path = tmp_path / result.execution_boundary_refs[0]
    payload = json.loads(boundary_path.read_text(encoding="utf-8"))
    assert payload["dispatch_decision"] == "blocked"
    assert "no critic adapter registered" in payload["dispatch_reason"]
    assert payload["critique_ref"] is None
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["action_authorized"] is False
    assert payload["advisory_only"] is True
    assert payload["requires_human_review"] is True
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py::test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role -q
```

**Expected RED:** `LookupError: no critic adapter registered for role=logical_devil backend_id=fixture-logical-unregistered` propagates out of `run_round` (uncaught), failing the test before any assertion runs.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`, inside `DarsCriticPanelRuntime.run_round`, locate the adapter-resolution `try`/`except PermissionError` block (around the call to `self.adapter_registry.resolve(...)`). Add a sibling `except LookupError as exc:` arm that mirrors the `PermissionError` branch:

```python
                try:
                    adapter = self.adapter_registry.resolve(
                        critic_role=critic.critic_role,
                        backend_id=critic.backend_id,
                        approval_ref=critic.approval_ref,
                    )
                except (LookupError, PermissionError) as exc:
                    dispatch_decision = "blocked"
                    dispatch_reason = str(exc)
                    task_results.append(
                        DarsTaskResult(
                            task_id=plan_task.task_id,
                            critic_id=plan_task.critic_id,
                            critic_role=plan_task.critic_role,
                            status="blocked",
                            external_call_made=False,
                            error_message=dispatch_reason,
                        )
                    )
```

The downstream boundary-record write (already inside the loop body) does not change: it picks up the same `adapter_class="fixture"` structural default when `adapter is None`, and records the merged exception's `dispatch_reason` verbatim.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected GREEN:** new test passes; existing focused panel + adapters + tool-execution + graph suites remain GREEN.

---

## Task 2: Documentation and traceability update

**Objective:** Record M-CP-EXT-4 in the DARS critic panel RTM, the traceability summary README, and the Ralph reflection log.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md` (bump version to `0.5.0`, dated `2026-05-20`; add the new pytest anchor to the HISYS-FR-DARS-CP-007 and HISYS-NFR-DARS-CP-001 rows; add a new `M-CP-EXT-4 — Typed adapter-missing blocked increment` section).
- Modify: `docs/traceability/README.md` (add an `M-CP-EXT-4` row in the Implemented-increments table after the `M-CP-EXT-3` row, enumerating the run-round exception merge, the deferred `adapter_class="unresolved"` literal, and the gate command).
- Modify: `ralph.md` (append a new Reflection Log entry for 2026-05-20 covering Prepare/RED/GREEN/Refactor/Gate, controlled anchors, RED command + observed failure, GREEN command + pass result, quality gate result, potential issues / open items, success likelihood, continue decision, and a resume checkpoint).

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 3: Full quality gate and local commit

**Objective:** Validate the complete M-CP-EXT-4 increment and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- New adapter-missing test passes alongside the existing focused panel + adapters + tool-execution + graph suites.
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_adapters.py \
  docs/plans/dars-critic-panel-mcp-ext-4-implementation-tasks.md \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: type adapter-missing as blocked task result"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The implementation would require changing the public shape of `DarsTaskResult`, `ExecutionBoundaryRecord`, or `DarsRoundResult` beyond the minimal exception merge described above.
- Existing 38 focused panel tests fail for a reason not directly tied to the intentional exception merge.
- Any implementation would require live external dispatch, process spawning, thread pools, `asyncio`, browser/network libraries, or credential access.
- Traceability validator or secret scan fails.

## Next increment candidates after M-CP-EXT-4

- M-CP-EXT-5: deterministic runtime clock seam for boundary record timestamps.
- M-CP-EXT-6: read-only `hisys run-dars-panel` CLI consuming `ExecutionGraphPlan` after a separate approval gate.
- Adapter-class literal extension: `adapter_class="unresolved"` (separate Prepare cycle; addresses the M-CP-EXT-2 open item (d) about the structural `"fixture"` default).
- Future activation: actual bounded-parallel execution, only after a separate governance/approval increment.
