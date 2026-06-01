"""Judge subsystem readiness text rendering tests.

These tests pin a Judge-only, human-readable rendering of the existing
subsystem readiness packet. The renderer must reuse the packet content, stay
side-effect free, and preserve the advisory-only / human-review-required
boundary.
"""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
JUDGE_RALPH = ROOT / "src" / "hisys" / "judge" / "ralph.md"


def _run_judge_rloo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "hisys.judge.rloo", *args],
        cwd=str(ROOT),
        env={
            "PYTHONPATH": f"{SRC}:{ROOT}",
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_render_judge_subsystem_readiness_text_surfaces_status_and_task() -> None:
    from hisys.judge.rloo import (
        build_judge_subsystem_readiness_packet,
        render_judge_subsystem_readiness_text,
    )

    packet = build_judge_subsystem_readiness_packet()
    rendered = render_judge_subsystem_readiness_text(packet)

    assert rendered.startswith("Judge Subsystem Readiness: READY")
    assert "Subsystem: judge" in rendered
    assert "Scope: Judge only" in rendered
    assert (
        "Next safe task: JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION"
        in rendered
    )
    assert "Controller: src/hisys/judge/ralph.md" in rendered


def test_render_judge_subsystem_readiness_text_preserves_authority_boundary() -> None:
    from hisys.judge.rloo import (
        build_judge_subsystem_readiness_packet,
        render_judge_subsystem_readiness_text,
    )

    rendered = render_judge_subsystem_readiness_text(
        build_judge_subsystem_readiness_packet()
    )

    assert "Advisory only: yes" in rendered
    assert "Requires human review: yes" in rendered
    assert "Live external action authorized: no" in rendered
    assert "Mutation authorized: no" in rendered
    assert "Publication authorized: no" in rendered
    assert "Remote push authorized: no" in rendered
    assert "Human-review removal authorized: no" in rendered
    assert "Note: This readiness text grants no execution authority" in rendered


def test_render_judge_subsystem_readiness_text_records_independence_and_no_side_effects() -> None:
    from hisys.judge.rloo import (
        build_judge_subsystem_readiness_packet,
        render_judge_subsystem_readiness_text,
    )

    rendered = render_judge_subsystem_readiness_text(
        build_judge_subsystem_readiness_packet()
    )

    assert "Depends on root RLOO: no" in rendered
    assert "Depends on Altas: no" in rendered
    assert "Depends on DARS: no" in rendered
    assert "Subsystem locally invocable: yes" in rendered
    assert "Performed live provider call: no" in rendered
    assert "Performed credential lookup: no" in rendered
    assert "Performed network call: no" in rendered
    assert "Performed remote push: no" in rendered
    assert "Performed cross-subsystem call: no" in rendered


def test_render_judge_subsystem_readiness_text_is_pure_and_does_not_mutate_packet() -> None:
    from hisys.judge.rloo import (
        build_judge_subsystem_readiness_packet,
        render_judge_subsystem_readiness_text,
    )

    packet = build_judge_subsystem_readiness_packet()
    before = copy.deepcopy(packet)

    first = render_judge_subsystem_readiness_text(packet)
    second = render_judge_subsystem_readiness_text(packet)

    assert packet == before
    assert first == second
    assert isinstance(first, str)


def test_judge_rloo_text_cli_outputs_human_readable_readiness_without_json() -> None:
    before = JUDGE_RALPH.read_text(encoding="utf-8")
    completed = _run_judge_rloo("--check", "--format", "text")
    after = JUDGE_RALPH.read_text(encoding="utf-8")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.startswith("Judge Subsystem Readiness: READY")
    assert "Advisory only: yes" in completed.stdout
    assert completed.stdout.lstrip()[0] != "{"
    assert before == after


def test_judge_rloo_help_lists_text_format_choice() -> None:
    completed = _run_judge_rloo("--help")

    assert completed.returncode == 0, completed.stderr
    assert "json" in completed.stdout
    assert "text" in completed.stdout
