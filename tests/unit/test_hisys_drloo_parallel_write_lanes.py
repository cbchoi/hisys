"""DRLOO parallel write lane discovery checks."""

from pathlib import Path

from hisys.operations.drloo_parallel_write_planner import (
    discover_parallel_write_plan,
    parse_milestone_tasks,
)


ROOT = Path(__file__).resolve().parents[2]
CONTROL_RULES = ROOT / "docs" / "plans" / "hisys-drloo-control-rules.md"
RALPH = ROOT / "ralph.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
MCP_PLAN = ROOT / "docs" / "plans" / "hisys-mcp-docker-service-implementation-tasks.md"


def test_parse_milestone_tasks_extracts_declared_write_sets() -> None:
    tasks = parse_milestone_tasks(
        """
### Task 1.1: Add alpha seam

**Files:**
- Create: `src/hisys/alpha.py`
- Test: `tests/unit/test_alpha.py`

### Task 1.2: Add beta seam

**Files:**
- Create: `src/hisys/beta.py`
- Test: `tests/unit/test_beta.py`
"""
    )

    assert [task.task_id for task in tasks] == ["task-1-1", "task-1-2"]
    assert tasks[0].write_set == ("src/hisys/alpha.py", "tests/unit/test_alpha.py")
    assert tasks[1].write_set == ("src/hisys/beta.py", "tests/unit/test_beta.py")


def test_discover_parallel_write_plan_selects_only_disjoint_lanes(tmp_path: Path) -> None:
    plan_path = tmp_path / "milestone.md"
    plan_path.write_text(
        """
### Task 1.1: Add alpha seam

**Files:**
- Create: `src/hisys/alpha.py`
- Test: `tests/unit/test_alpha.py`

### Task 1.2: Add beta seam

**Files:**
- Create: `src/hisys/beta.py`
- Test: `tests/unit/test_beta.py`

### Task 1.3: Update alpha follow-up

**Files:**
- Modify: `src/hisys/alpha.py`

### Task 1.4: Update shared governance

**Files:**
- Modify: `ralph.md`
""",
        encoding="utf-8",
    )

    result = discover_parallel_write_plan(plan_path)

    assert result.schema_id == "hisys.drloo.parallel_write_plan.v1"
    assert [lane.task_id for lane in result.lanes] == ["task-1-1", "task-1-2"]
    assert all(lane.worktree_required for lane in result.lanes)
    assert all(lane.write_capable_agent_allowed for lane in result.lanes)
    assert "parent integrates lane commits" in result.merge_strategy
    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert result.credential_lookup_performed is False
    assert result.remote_push_authorized is False
    assert any("overlaps existing lane target" in conflict for conflict in result.conflicts)
    assert any("shared governance target" in conflict for conflict in result.conflicts)


def test_current_mcp_milestone_has_parallel_write_lane_candidates() -> None:
    result = discover_parallel_write_plan(MCP_PLAN, max_lanes=3)

    assert len(result.lanes) >= 2
    lane_write_sets = [set(lane.write_set) for lane in result.lanes]
    for index, left in enumerate(lane_write_sets):
        for right in lane_write_sets[index + 1 :]:
            assert left.isdisjoint(right)
    assert result.requires_parent_integration_review is True
    assert result.remote_push_authorized is False


def test_control_docs_require_milestone_analysis_before_parallel_writers() -> None:
    control_rules = CONTROL_RULES.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    required_phrases = [
        "parallel-write lane discovery",
        "milestone dependency analysis",
        "disjoint write sets",
        "one branch/worktree per lane",
        "write-capable subagent",
        "parent integration review",
        "shared governance files remain parent-only",
        "remote push remains unauthorized",
    ]
    for phrase in required_phrases:
        assert phrase in control_rules
        assert phrase in ralph

    assert "formal_hisys_result: hisys_drloo_parallel_write_lane_planner_recorded" in profile
    assert "parallel_write_subagents_authorized: true" in profile
    assert "parallel_read_only_subagents_spawned: false" in profile
