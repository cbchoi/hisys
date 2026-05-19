# DARS Critic Panel M-CP-EXT-7 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the `MB-DARS-CP-EXT7-T001` document-RED/Prepare artifact. It authorizes only local RED/GREEN work for the non-structural `adapter_class="unresolved"` literal on `ExecutionBoundaryRecord`.

**Goal:** Implement the deferred `adapter_class="unresolved"` literal pinned by the M-CP-EXT-2 reflection open item (d) and the M-CP-EXT-4 reflection open item (a). When `DarsCriticPanelRuntime.run_round` reaches the boundary-record write with `adapter is None` (the `disabled` critic, `PermissionError` from the registry, or `LookupError` from the registry branches), the persisted `ExecutionBoundaryRecord.adapter_class` becomes `"unresolved"` instead of the previous structural `"fixture"` default. Reviewers can now distinguish "the role was bound to a fixture adapter and the adapter chose this outcome" from "no adapter resolution attempt yielded an adapter for this role".

**Architecture:** Modify only `src/hisys/agents/dars_panel.py`. Widen the `AdapterClass` type alias to include `"unresolved"`, replace the inline `adapter.adapter_class if adapter is not None else "fixture"` expression in `run_round` with `... else "unresolved"`. The existing `FixtureCriticAdapter.__post_init__` continues to reject `"unresolved"` for adapter registration (the literal is reserved for boundary-record reporting; it never describes a real adapter binding). No new module, no new CLI, no clock change, no schema field added or removed.

**Tech Stack:** Python 3.11, `Literal`, pytest. No new runtime dependency.

**Context Packet:** Required source handles are `docs/plans/dars-critic-panel-platform-runtime-next.md`, `docs/plans/dars-critic-panel-mcp-ext-4-implementation-tasks.md`, `docs/plans/dars-critic-panel-mcp-ext-5-implementation-tasks.md`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `src/hisys/agents/dars_panel.py`, `tests/unit/test_dars_critic_panel_adapters.py`, `tests/unit/test_dars_critic_panel_runtime.py`, `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`, and `tests/unit/test_dars_critic_panel_execution_graph_plan.py`. Validation handles are the focused panel regression, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized by this plan. Live DARS dispatch, external adapter activation, browser/network calls, credential resolution, publication, destructive Git, CLI activation, and actual bounded-parallel execution are out of scope. The advisory-only invariants from M-CP-EXT-1/2/3/4/5 remain mandatory.

---

## Accepted decisions

1. **Single union, runtime guard:** widen `AdapterClass = Literal["fixture", "loopback", "external"]` to include `"unresolved"`. `FixtureCriticAdapter.__post_init__` already rejects any `adapter_class` outside `{"fixture", "loopback", "external"}`; the existing check is sufficient to keep `"unresolved"` out of real adapter registrations.
2. **Record-level marker only:** `"unresolved"` is reserved for the `ExecutionBoundaryRecord.adapter_class` field when `run_round` reaches the boundary write with no resolved adapter. It is never returned by `CriticAdapterRegistry.resolve(...)` and is never accepted as a `FixtureCriticAdapter.adapter_class` value.
3. **Substitution site:** the only production code change is the boundary-record construction inside `DarsCriticPanelRuntime.run_round`: `adapter_class=adapter.adapter_class if adapter is not None else "unresolved"`.
4. **Backwards-compatibility:** no existing test asserts `adapter_class == "fixture"` on a blocked-no-adapter-resolved boundary record JSON payload (confirmed via grep). The only places that pass `adapter_class="fixture"` literally to `ExecutionBoundaryRecord(...)` are the M-CP-EXT-2 unit-test fixtures that construct records directly with a real fixture adapter context; those tests are unaffected.
5. **No schema versioning:** the persisted JSON payload still has an `adapter_class` field; only the value space expands. Readers tolerating Pydantic-style `Literal` validation against the wider union will accept the new value; readers strict-matching the older three-value set will need to update. Within this repository, only the runtime writes the field, so there is no other reader to coordinate with.
6. **No documentation rewording of M-CP-EXT-2:** the M-CP-EXT-2 RTM section already notes the `"fixture"` structural default explicitly. This increment adds a forward-pointing note ("M-CP-EXT-7 replaces the structural `"fixture"` default with `"unresolved"`") in the new RTM section rather than retroactively editing the M-CP-EXT-2 audit trail.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the repository state and current GREEN baseline before writing the RED test.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:**

- Branch is `dars`.
- Existing focused suites report `41 passed` (post-M-CP-EXT-5).
- Working tree is clean (or contains only intentional changes for this increment).

---

## Task 1: RED/GREEN — disabled critic boundary record uses `adapter_class="unresolved"`

**Objective:** Pin the new behavior with a failing test, then change the structural default in `run_round`.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing test**

Add to `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`:

```python
def test_panel_runtime_marks_unresolved_adapter_class_for_disabled_critic(tmp_path: Path):
    """M-CP-EXT-7: when no adapter is resolved, the boundary record marks `adapter_class="unresolved"`."""

    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )
    from hisys.config.instance import InstanceRoot

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()  # empty
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-7",
        critics=[
            DarsCriticRoleConfig(
                critic_id="disabled-devil",
                critic_role="logical_devil",
                backend_id="fixture-disabled",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
                enabled=False,
            ),
            DarsCriticRoleConfig(
                critic_id="missing-devil",
                critic_role="standards_reviewer",
                backend_id="fixture-missing",
                rubric_ref=rubric_ref,
                critique_dimensions=["standards_alignment"],
            ),
        ],
    )

    result = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        adapter_registry=registry,
    ).run_round(
        yyyymmdd="20260520",
        request_id="REQ-DARS-CP-EXT-7",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    boundary_payloads = [
        json.loads((tmp_path / ref).read_text(encoding="utf-8"))
        for ref in result.execution_boundary_refs
    ]
    assert [payload["adapter_class"] for payload in boundary_payloads] == [
        "unresolved",
        "unresolved",
    ]
    # Safety envelope still locked
    for payload in boundary_payloads:
        assert payload["dispatch_decision"] == "blocked"
        assert payload["external_call_made"] is False
        assert payload["mutation_performed"] is False
        assert payload["action_authorized"] is False
        assert payload["advisory_only"] is True
        assert payload["requires_human_review"] is True
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_marks_unresolved_adapter_class_for_disabled_critic -q
```

**Expected RED:** `AssertionError` comparing `["fixture", "fixture"]` to `["unresolved", "unresolved"]`.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`:

1. Widen the `AdapterClass` type alias:

```python
AdapterClass = Literal["fixture", "loopback", "external", "unresolved"]
```

2. Inside `DarsCriticPanelRuntime.run_round`, find the boundary-record construction and change the `adapter_class` argument:

```python
            boundary_record = ExecutionBoundaryRecord(
                task_id=plan_task.task_id,
                critic_id=plan_task.critic_id,
                critic_role=plan_task.critic_role,
                adapter_class=adapter.adapter_class if adapter is not None else "unresolved",
                backend_id=plan_task.backend_id,
                ...
            )
```

(The existing `FixtureCriticAdapter.__post_init__` continues to reject `"unresolved"` for adapter registration; no change there.)

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected GREEN:** new test passes; existing focused panel + adapters + tool-execution + graph suites remain GREEN.

---

## Task 2: Documentation and traceability update

**Objective:** Record M-CP-EXT-7 in the DARS critic panel RTM, the traceability summary README, and the Ralph reflection log.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md` (bump version to `0.7.0`, dated `2026-05-20`; add the new pytest anchor to the HISYS-FR-DARS-CP-007 row; add a new `M-CP-EXT-7 — Unresolved adapter class literal (2026-05-20)` section).
- Modify: `docs/traceability/README.md` (add an `M-CP-EXT-7` row in the Implemented-increments table after the `M-CP-EXT-5` row, enumerating the widened `AdapterClass` literal, the substitution site in `run_round`, the unchanged `FixtureCriticAdapter` rejection, and the gate command).
- Modify: `ralph.md` (append a new Reflection Log entry for 2026-05-20 covering Prepare/RED/GREEN/Refactor/Gate, controlled anchors, RED command + observed failure, GREEN command + pass result, quality gate result, potential issues / open items, success likelihood, continue decision, and a resume checkpoint).

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 3: Full quality gate and local commit

**Objective:** Validate the complete M-CP-EXT-7 increment and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- New unresolved-adapter test passes alongside the existing focused panel + adapters + tool-execution + graph suites (42 passed).
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_tool_execution_runtime.py \
  docs/plans/dars-critic-panel-mcp-ext-7-implementation-tasks.md \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: mark unresolved adapter class on DARS boundary records"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The implementation would require changing the public shape of `DarsTaskResult`, `ExecutionBoundaryRecord` (beyond the `adapter_class` literal value space), or `DarsRoundResult`.
- Existing 41 focused panel tests fail for a reason not directly tied to the intentional literal extension.
- Any implementation would require live external dispatch, process spawning, thread pools, `asyncio`, browser/network libraries, or credential access.
- Traceability validator or secret scan fails.

## Next increment candidates after M-CP-EXT-7

- M-CP-EXT-6: read-only `hisys run-dars-panel` CLI consuming `ExecutionGraphPlan` after a separate approval gate.
- Per-task `started_at` / `completed_at` distinct from a single round-level clock tick.
- Future activation: actual bounded-parallel execution, only after a separate governance/approval increment.
