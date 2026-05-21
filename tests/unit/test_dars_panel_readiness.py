"""DARS panel readiness/completion status surface tests.

Traceability:
- DARS-CLOSE-3 in docs/plans/dars-panel-completion-before-codebase-return.md
- HISYS-FR-DARS-CP-001
- HISYS-FR-DARS-CP-007
- HISYS-NFR-DARS-CP-001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_dars_panel_readiness_status_distinguishes_local_and_live_boundaries(
    tmp_path: Path, capsys
):
    """DARS-CLOSE-3: the readiness CLI distinguishes local/localhost/live modes."""

    from hisys.cli.main import main

    exit_code = main(
        [
            "dars-panel-readiness",
            "--instance",
            str(tmp_path),
            "--date",
            "20260521",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_id"] == "hisys.dars_panel.readiness_status"
    assert payload["fixture_panel_complete"] is True
    assert payload["operator_report_available"] is True
    assert payload["golden_fixture_available"] is True
    assert payload["localhost_rehearsal_available"] is True
    assert payload["localhost_rehearsal_human_gated"] is True
    assert payload["remote_subscription_policy_exists"] is True
    assert payload["remote_subscription_injected_executor_harness_available"] is True
    assert payload["live_provider_execution_smoked"] is False
    assert (
        payload["completion_claim"]
        == "local_fixture_localhost_controlled_advisory_complete"
    )
    assert payload["next_queue_after_closure"] == "MB-CODEBASE-M21-6-PREP"
    # The readiness surface is advisory-only; it never authorizes live action.
    assert payload["advisory_only"] is True
    assert payload["live_external_action_authorized"] is False


def test_dars_panel_readiness_status_text_format_lists_safety_fields(
    tmp_path: Path, capsys
):
    """DARS-CLOSE-3: text format surfaces the same boundary contract."""

    from hisys.cli.main import main

    exit_code = main(
        [
            "dars-panel-readiness",
            "--instance",
            str(tmp_path),
            "--date",
            "20260521",
            "--format",
            "text",
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "schema_id: hisys.dars_panel.readiness_status" in out
    assert "completion_claim: local_fixture_localhost_controlled_advisory_complete" in out
    assert "live_provider_execution_smoked: false" in out
    assert "next_queue_after_closure: MB-CODEBASE-M21-6-PREP" in out


def test_dars_panel_readiness_status_writes_report_when_requested(
    tmp_path: Path, capsys
):
    """DARS-CLOSE-3: optional --write-report persists the readiness snapshot."""

    from hisys.cli.main import main

    exit_code = main(
        [
            "dars-panel-readiness",
            "--instance",
            str(tmp_path),
            "--date",
            "20260521",
            "--write-report",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    expected_ref = "reports/run-summaries/20260521/dars-panel-readiness-status.json"
    assert payload["report_ref"] == expected_ref

    report = json.loads((tmp_path / expected_ref).read_text(encoding="utf-8"))
    assert report["schema_id"] == "hisys.dars_panel.readiness_status"
    assert report["completion_claim"] == "local_fixture_localhost_controlled_advisory_complete"
    assert report["live_provider_execution_smoked"] is False
