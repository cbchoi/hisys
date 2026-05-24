"""R4H Hermes-mediated DARS productization-prep contract tests."""

from __future__ import annotations

import json
from pathlib import Path


def test_r4h_productization_prep_contract_preserves_branch_boundaries() -> None:
    """R4H prep defines a tool path without upgrading R4C/live/release claims."""

    from hisys.operations.dars_r4h_productization import build_r4h_productization_prep

    packet = build_r4h_productization_prep(yyyymmdd="20260524")

    assert packet["schema_id"] == "hisys.dars.r4h_hermes_mediated_productization_prep"
    assert packet["schema_version"] == "0.1.0"
    assert packet["accepted_claim"] == "r4h_hermes_mediated_productization_prep_ready_for_human_review"
    assert packet["active_branch"] == "R4H"
    assert packet["active_transport_kind"] == "hermes_mediated_model_advisory"
    assert packet["request_contract"]["schema_id"] == "hisys.dars.r4h_hermes_mediated_request"
    assert packet["request_contract"]["required_fields"] == [
        "request_id",
        "objective",
        "candidate_refs",
        "evidence_refs",
        "critic_roles",
        "human_review_ref",
    ]
    assert packet["response_contract"]["schema_id"] == "hisys.dars.r4h_hermes_mediated_response"
    assert "logical_consistency_critic" in packet["supported_critic_roles"]
    assert "evidence_governance_critic" in packet["supported_critic_roles"]
    assert packet["deferred_transport_relation"]["deferred_branch"] == "R4C"
    assert (
        packet["deferred_transport_relation"]["future_task"]
        == "DARS-LIVE-RELEASE-R4C-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS"
    )

    flags = packet["boundary_flags"]
    assert flags["codex_cli_subprocess_call"] is False
    assert flags["codex_cli_subprocess_completion_claim"] is False
    assert flags["raw_provider_api_call_by_hisys"] is False
    assert flags["adapter_native_readiness"] is False
    assert flags["credential_lookup_by_hisys"] is False
    assert flags["mutation_performed"] is False
    assert flags["publication_performed"] is False
    assert flags["external_notification_performed"] is False
    assert flags["release_action_performed"] is False
    assert flags["requires_human_review"] is True

    assert "codex_cli_subprocess_prompt_mode_completed" in packet["not_accepted_upgrades"]
    assert "released_for_controlled_advisory_use" in packet["not_accepted_upgrades"]


def test_r4h_productization_prep_cli_writes_json_and_markdown(tmp_path: Path, capsys) -> None:
    """The CLI produces an agent-readable prep packet and Markdown report."""

    from hisys.cli.main import main

    exit_code = main(
        [
            "dars-r4h-productization-prep",
            "--instance",
            str(tmp_path),
            "--date",
            "20260524",
            "--write-report",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_id"] == "hisys.dars.r4h_hermes_mediated_productization_prep"
    assert payload["report_refs"] == {
        "json_ref": "reports/run-summaries/20260524/dars-r4h-productization-prep.json",
        "markdown_ref": "reports/run-summaries/20260524/dars-r4h-productization-prep.md",
    }

    report = json.loads((tmp_path / payload["report_refs"]["json_ref"]).read_text(encoding="utf-8"))
    assert report["accepted_claim"] == "r4h_hermes_mediated_productization_prep_ready_for_human_review"
    assert report["boundary_flags"]["raw_provider_api_call_by_hisys"] is False

    markdown = (tmp_path / payload["report_refs"]["markdown_ref"]).read_text(encoding="utf-8")
    assert "# DARS R4H Hermes-mediated productization prep" in markdown
    assert "active_transport_kind: `hermes_mediated_model_advisory`" in markdown
    assert "This is not a Codex CLI subprocess success claim." in markdown
    assert "requires_human_review: `true`" in markdown
