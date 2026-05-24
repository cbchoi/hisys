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


def test_r4h_request_response_harness_validates_fixture_response_boundary(tmp_path: Path) -> None:
    """The R4H harness accepts a local fixture response without upgrading live claims."""

    from hisys.operations.dars_r4h_productization import (
        build_r4h_request_response_harness,
        validate_r4h_hermes_mediated_request,
    )

    request = {
        "schema_id": "hisys.dars.r4h_hermes_mediated_request",
        "request_id": "REQ-DARS-R4H-HARNESS-001",
        "objective": "Validate the R4H request/response contract with local fixture findings.",
        "candidate_refs": ["docs/examples/dars/hermes-mediated-r4h-productization-prep.example.json"],
        "evidence_refs": ["docs/reports/dars-r4h-hermes-mediated-productization-prep-2026-05-24.md"],
        "critic_roles": ["logical_consistency_critic", "evidence_governance_critic"],
        "human_review_ref": "human-review-required:R4H",
    }

    validated = validate_r4h_hermes_mediated_request(request)
    assert validated["valid"] is True
    assert validated["issue_codes"] == []

    packet = build_r4h_request_response_harness(
        yyyymmdd="20260524",
        request=request,
        fixture_findings={
            "logical_consistency_critic": ["R4H branch selection remains consistent with R4C deferral."],
            "evidence_governance_critic": ["Boundary flags preserve human-review and no-action constraints."],
        },
    )

    assert packet["schema_id"] == "hisys.dars.r4h_request_response_harness"
    assert packet["accepted_claim"] == "r4h_hermes_mediated_request_response_harness_closed_for_human_review"
    assert packet["request_validation"]["valid"] is True
    assert packet["response"]["schema_id"] == "hisys.dars.r4h_hermes_mediated_response"
    assert packet["response"]["status"] == "completed"
    assert packet["response"]["human_review_required_for_consequential_use"] is True
    assert set(packet["response"]["critic_findings"]) == {
        "logical_consistency_critic",
        "evidence_governance_critic",
    }

    flags = packet["boundary_flags"]
    assert flags["fixture_injected_harness"] is True
    assert flags["codex_cli_subprocess_call"] is False
    assert flags["raw_provider_api_call_by_hisys"] is False
    assert flags["credential_lookup_by_hisys"] is False
    assert flags["mutation_performed"] is False
    assert flags["publication_performed"] is False
    assert flags["release_action_performed"] is False
    assert flags["requires_human_review"] is True

    assert packet["next_safe_task"] == "DARS-LIVE-RELEASE-R7-RC-SCOPE-DECISION"
    assert "release_candidate_ready" in packet["not_accepted_upgrades"]


def test_r4h_request_response_harness_rejects_unsafe_request_fields() -> None:
    """Unsafe authority fields and unsupported critics fail closed before response synthesis."""

    from hisys.operations.dars_r4h_productization import validate_r4h_hermes_mediated_request

    request = {
        "schema_id": "hisys.dars.r4h_hermes_mediated_request",
        "request_id": "REQ-DARS-R4H-HARNESS-UNSAFE",
        "objective": "unsafe",
        "candidate_refs": ["docs/examples/dars/hermes-mediated-r4h-productization-prep.example.json"],
        "evidence_refs": ["docs/reports/dars-r4h-hermes-mediated-productization-prep-2026-05-24.md"],
        "critic_roles": ["logical_consistency_critic", "tool_enabled_critic"],
        "human_review_ref": "human-review-required:R4H",
        "credential_ref": "secret-manager://not-allowed",
        "release_authority": True,
    }

    validation = validate_r4h_hermes_mediated_request(request)

    assert validation["valid"] is False
    assert "forbidden_field:credential_ref" in validation["issue_codes"]
    assert "forbidden_field:release_authority" in validation["issue_codes"]
    assert "unsupported_critic_role:tool_enabled_critic" in validation["issue_codes"]


def test_r4h_request_response_harness_cli_writes_json_and_markdown(tmp_path: Path, capsys) -> None:
    """The CLI persists the R4H local harness packet and operator report."""

    from hisys.cli.main import main

    request = {
        "schema_id": "hisys.dars.r4h_hermes_mediated_request",
        "request_id": "REQ-DARS-R4H-HARNESS-CLI",
        "objective": "Validate R4H harness CLI with local fixture findings.",
        "candidate_refs": ["docs/examples/dars/hermes-mediated-r4h-productization-prep.example.json"],
        "evidence_refs": ["docs/reports/dars-r4h-hermes-mediated-productization-prep-2026-05-24.md"],
        "critic_roles": ["logical_consistency_critic", "evidence_governance_critic"],
        "human_review_ref": "human-review-required:R4H",
    }
    request_path = tmp_path / "r4h-request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")

    exit_code = main(
        [
            "dars-r4h-request-response-harness",
            "--instance",
            str(tmp_path),
            "--date",
            "20260524",
            "--request",
            str(request_path),
            "--write-report",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted_claim"] == "r4h_hermes_mediated_request_response_harness_closed_for_human_review"
    assert payload["report_refs"] == {
        "json_ref": "reports/run-summaries/20260524/dars-r4h-request-response-harness.json",
        "markdown_ref": "reports/run-summaries/20260524/dars-r4h-request-response-harness.md",
    }

    report = json.loads((tmp_path / payload["report_refs"]["json_ref"]).read_text(encoding="utf-8"))
    assert report["request_validation"]["valid"] is True
    assert report["boundary_flags"]["fixture_injected_harness"] is True
    assert report["boundary_flags"]["raw_provider_api_call_by_hisys"] is False

    markdown = (tmp_path / payload["report_refs"]["markdown_ref"]).read_text(encoding="utf-8")
    assert "# DARS R4H request/response harness" in markdown
    assert "fixture_injected_harness: `true`" in markdown
    assert "This is not a live model/provider or Codex subprocess execution claim." in markdown
