"""Governance docs current-state consistency tests."""

import subprocess
from pathlib import Path

from hisys.operations.governance_docs import build_governance_current_state_report


ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def test_governance_profile_and_ralph_checkpoint_match_current_head() -> None:
    report = build_governance_current_state_report(ROOT)
    current_head_short = _git("rev-parse", "--short", "HEAD")
    current_head_subject = _git("log", "-1", "--pretty=%s")

    assert report.schema_id == "hisys.governance.current_state.v1"
    assert report.repository == "/home/cbchoi/workspaces/develop/repos/hisys"
    assert report.branch == "dars"
    assert report.profile_version == "v0.0.78"
    assert report.next_safe_task == "DARS-LIVE-RELEASE-R4-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS"
    assert report.current_head_short == current_head_short
    assert report.current_head_subject == current_head_subject
    assert report.ralph_checkpoint_head == report.current_head_at_plan_creation
    assert report.v0012_validation_status == "completed"
    assert report.remote_push_authorized is False
    assert report.live_model_call_authorized is False
    assert report.live_external_action_authorized is False
    assert report.issues == ()
