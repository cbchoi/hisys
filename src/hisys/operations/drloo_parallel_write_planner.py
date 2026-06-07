"""Local DRLOO parallel-write lane discovery for milestone plans.

This module is a repository-local planning helper. It parses a Markdown
milestone plan, extracts task write sets, and proposes write-capable lanes only
when tasks have disjoint file targets. It performs no mutation, no process
launch, no network access, no credential lookup, and no external action.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_TASK_HEADING_RE = re.compile(r"^###\s+(?P<title>Task\s+[^\n]+)$", re.MULTILINE)
_FILE_LINE_RE = re.compile(r"^-\s+(?:Create|Modify|Test|Files?)\s*:\s*(?P<path>`[^`]+`|[^\n]+)", re.IGNORECASE)
_INLINE_PATH_RE = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class DrlooMilestoneTask:
    """A local milestone task extracted from Markdown."""

    task_id: str
    title: str
    write_set: tuple[str, ...]
    block: str


@dataclass(frozen=True)
class DrlooParallelLaneCandidate:
    """A candidate lane that may be delegated to one writer worktree."""

    lane_id: str
    task_id: str
    title: str
    write_set: tuple[str, ...]
    worktree_required: bool = True
    write_capable_agent_allowed: bool = True


@dataclass(frozen=True)
class DrlooParallelWritePlan:
    """A bounded, local-only DRLOO parallel-write plan."""

    schema_id: str
    source_plan: str
    lanes: tuple[DrlooParallelLaneCandidate, ...]
    conflicts: tuple[str, ...]
    merge_strategy: str
    external_call_made: bool = False
    mutation_performed: bool = False
    credential_lookup_performed: bool = False
    remote_push_authorized: bool = False
    requires_parent_integration_review: bool = True


_ALWAYS_SHARED_TARGETS = {
    "ralph.md",
    "docs/milestone-bootstrap/profile.yaml",
    "docs/traceability/README.md",
}


def _normalize_task_id(title: str) -> str:
    prefix = title.split(":", 1)[0]
    return re.sub(r"[^A-Za-z0-9]+", "-", prefix).strip("-").lower()


def _extract_paths(line: str) -> tuple[str, ...]:
    quoted = _INLINE_PATH_RE.findall(line)
    if quoted:
        return tuple(path.strip() for path in quoted if path.strip())
    match = _FILE_LINE_RE.match(line.strip())
    if not match:
        return ()
    return (match.group("path").strip().strip("`"),)


def parse_milestone_tasks(markdown: str) -> tuple[DrlooMilestoneTask, ...]:
    """Extract task headings and declared file targets from a Markdown plan."""

    matches = list(_TASK_HEADING_RE.finditer(markdown))
    tasks: list[DrlooMilestoneTask] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        block = markdown[start:end]
        title = match.group("title").strip()
        paths: list[str] = []
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("-"):
                continue
            if not re.match(r"^-\s+(Create|Modify|Test|File|Files?)\s*:", stripped, flags=re.IGNORECASE):
                continue
            paths.extend(_extract_paths(stripped))
        write_set = tuple(dict.fromkeys(path for path in paths if path))
        tasks.append(
            DrlooMilestoneTask(
                task_id=_normalize_task_id(title),
                title=title,
                write_set=write_set,
                block=block.strip(),
            )
        )
    return tuple(tasks)


def discover_parallel_write_plan(plan_path: Path, *, max_lanes: int = 3) -> DrlooParallelWritePlan:
    """Build a disjoint-write-set lane plan from a milestone Markdown file.

    The planner is conservative: tasks with no declared write set or tasks that
    mention always-shared governance files are reported as conflicts instead of
    lane candidates. Parent integration remains required even when lanes are
    disjoint.
    """

    source = plan_path.resolve()
    tasks = parse_milestone_tasks(source.read_text(encoding="utf-8"))
    lanes: list[DrlooParallelLaneCandidate] = []
    claimed_paths: set[str] = set()
    conflicts: list[str] = []

    for task in tasks:
        write_set = set(task.write_set)
        if not write_set:
            conflicts.append(f"{task.task_id}: no declared write set")
            continue
        shared = write_set & _ALWAYS_SHARED_TARGETS
        if shared:
            conflicts.append(f"{task.task_id}: shared governance target(s): {', '.join(sorted(shared))}")
            continue
        overlap = write_set & claimed_paths
        if overlap:
            conflicts.append(f"{task.task_id}: overlaps existing lane target(s): {', '.join(sorted(overlap))}")
            continue
        if len(lanes) >= max_lanes:
            conflicts.append(f"{task.task_id}: max lane count reached")
            continue
        lane_id = f"lane-{len(lanes) + 1}-{task.task_id}"
        lanes.append(
            DrlooParallelLaneCandidate(
                lane_id=lane_id,
                task_id=task.task_id,
                title=task.title,
                write_set=tuple(sorted(write_set)),
            )
        )
        claimed_paths.update(write_set)

    return DrlooParallelWritePlan(
        schema_id="hisys.drloo.parallel_write_plan.v1",
        source_plan=source.as_posix(),
        lanes=tuple(lanes),
        conflicts=tuple(conflicts),
        merge_strategy=(
            "one branch/worktree per lane; no shared-file writes in lane agents; "
            "parent integrates lane commits, resolves governance docs, runs focused "
            "and full validation, then makes the integration commit"
        ),
    )


__all__ = [
    "DrlooMilestoneTask",
    "DrlooParallelLaneCandidate",
    "DrlooParallelWritePlan",
    "discover_parallel_write_plan",
    "parse_milestone_tasks",
]
