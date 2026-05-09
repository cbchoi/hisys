"""Tests for Topic-Gatekeeper completion sequence.

Traceability: Topic-Gatekeeper-A/B/C/D/E, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import (
    build_topic_gatekeeper_approval_package,
    build_topic_gatekeeper_decision,
    build_topic_gatekeeper_status_report,
    build_topic_gatekeeper_transaction_plan,
    rehearse_topic_gatekeeper_transaction_in_fixture,
)


def _registry() -> dict:
    return {
        "topics": [
            {
                "topic_uid": "TOPIC-20260509-AAAAAA",
                "topic_slug": "devs-structural-change-formalism",
                "title": "DEVS Structural Change Formalism",
                "aliases": ["DSDEVS", "structural DEVS"],
                "claim_ids": ["CLAIM-001"],
                "source_ids": ["doi:10.1000/example"],
                "groups": ["GROUP-20260509-BBBBBB"],
                "vault_relative_ref": "91 Hisys/Live Research/topics/TOPIC-20260509-AAAAAA__devs-structural-change-formalism/topic-manifest.json",
            }
        ]
    }


def test_topic_gatekeeper_decision_is_evidence_citing_and_no_mutation() -> None:
    decision = build_topic_gatekeeper_decision(
        request_id="REQ-TG-A",
        proposed_topic={
            "title": "Structural DEVS formalism",
            "topic_slug": "structural-devs-formalism",
            "claim_ids": ["CLAIM-001"],
            "source_ids": ["doi:10.1000/example"],
            "groups": ["GROUP-20260509-BBBBBB"],
        },
        registry=_registry(),
    )

    assert decision["decision"]["action"] == "same_as_existing_topic"
    assert decision["decision"]["target_topic_uid"] == "TOPIC-20260509-AAAAAA"
    assert decision["scores"]["semantic_similarity"]["evidence_refs"]
    assert decision["scores"]["source_overlap"]["evidence_refs"]
    assert decision["external_call_made"] is False
    assert decision["mutation_performed"] is False
    assert decision["real_obsidian_vault_write_performed"] is False


def test_topic_gatekeeper_approval_and_transaction_are_no_write() -> None:
    decision = build_topic_gatekeeper_decision(request_id="REQ-TG-A", proposed_topic={"title": "New Topic", "topic_slug": "new-topic"}, registry={"topics": []})
    package = build_topic_gatekeeper_approval_package(request_id="REQ-TG-B", decision=decision, approval_ref="APPROVAL-TG")
    plan = build_topic_gatekeeper_transaction_plan(request_id="REQ-TG-C", approval_package=package)

    assert package["status"] == "approval_packaged"
    assert package["requires_human_approval"] is True
    assert plan["status"] == "planned_not_executed"
    assert plan["planned_operation_count"] >= 2
    assert plan["real_obsidian_vault_write_performed"] is False
    assert all(op["vault_relative_ref"].startswith("91 Hisys/Live Research/") for op in plan["planned_operations"])


def test_topic_gatekeeper_fixture_rehearsal_writes_only_fixture(tmp_path: Path) -> None:
    decision = build_topic_gatekeeper_decision(request_id="REQ-TG-A", proposed_topic={"title": "New Topic", "topic_slug": "new-topic"}, registry={"topics": []})
    package = build_topic_gatekeeper_approval_package(request_id="REQ-TG-B", decision=decision, approval_ref="APPROVAL-TG")
    plan = build_topic_gatekeeper_transaction_plan(request_id="REQ-TG-C", approval_package=package)
    report = rehearse_topic_gatekeeper_transaction_in_fixture(transaction_plan=plan, fixture_vault_root=tmp_path, approval_ref="APPROVAL-TG", fixture_vault_only=True)

    assert report["status"] == "rehearsed_fixture_only"
    assert report["operation_count"] == plan["planned_operation_count"]
    assert report["real_obsidian_vault_write_performed"] is False
    first = tmp_path / report["written_fixture_refs"][0]["vault_relative_ref"]
    assert first.exists()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["topic_gatekeeper_projection_only"] is True


def test_topic_gatekeeper_status_marks_complete() -> None:
    report = build_topic_gatekeeper_status_report(request_id="REQ-TG-STATUS")

    assert report["status"] == "complete"
    assert report["topic_gatekeeper_complete"] is True
    assert report["completed_stage_count"] == 5
    assert report["open_stage_count"] == 0
    assert report["real_obsidian_vault_write_performed"] is False


def test_topic_gatekeeper_cli_writes_decision_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    registry_path = tmp_path / "registry.json"
    proposed_path = tmp_path / "proposed-topic.json"
    registry_path.write_text(json.dumps(_registry()), encoding="utf-8")
    proposed_path.write_text(json.dumps({"title": "Structural DEVS formalism", "topic_slug": "structural-devs-formalism"}), encoding="utf-8")

    exit_code = main([
        "vault-topic-gatekeeper",
        "--instance", str(instance),
        "--date", "20260510",
        "--request-id", "REQ-TG-A",
        "--registry", str(registry_path),
        "--proposed-topic", str(proposed_path),
    ])

    assert exit_code == 0
    assert "topic gatekeeper: same_as_existing_topic" in capsys.readouterr().out
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260510" / "topic-gatekeeper-decision-REQ-TG-A.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["decision"]["action"] == "same_as_existing_topic"
