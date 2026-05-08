"""Tests for Investigator multi-agent research contracts.

Traceability: HISYS-T-027, HISYS-INST-INV-001, HISYS-FR-INV-001..006,
HISYS-FR-MEM-001..005, HISYS-TPL-RESEARCH-SEARCH-001.
"""

import pytest
from pydantic import ValidationError

from hisys.investigator import ClaimRecord, EvidenceItem, EvidencePackage, ResearchTask


def test_research_task_defaults_disallow_live_side_effect_actions():
    task = ResearchTask(
        task_id="TASK-INV-001",
        agent_type="fixture",
        question="Assess whether fixture overheating evidence requires attention.",
    )

    assert task.expected_output_schema == "EvidencePackage"
    assert task.allowed_source_ids == []
    assert task.allowed_domains == []
    assert "login" in task.disallowed_actions
    assert "form_submit" in task.disallowed_actions
    assert "credential_use" in task.disallowed_actions


def test_evidence_package_defaults_to_no_external_side_effects_and_links_claims_to_evidence():
    evidence = EvidenceItem(
        evidence_id="EV-001",
        task_id="TASK-INV-001",
        agent_id="fixture-research-agent",
        source_id="SRC-HW-MOCK-001",
        title="Fixture hardware observation",
        quoted_text="Temperature threshold exceeded in fixture record.",
        retrieved_at="2026-05-08T00:00:00Z",
        content_hash="sha256:fixture-hash",
    )
    claim = ClaimRecord(
        claim_id="CLAIM-001",
        text="Fixture hardware evidence indicates an overheating risk.",
        confidence=0.9,
        evidence_refs=[evidence.evidence_id],
    )

    package = EvidencePackage(
        package_id="EPKG-001",
        task_id="TASK-INV-001",
        agent_id="fixture-research-agent",
        agent_type="fixture",
        claims=[claim],
        evidence=[evidence],
    )

    assert package.external_side_effects is False
    assert package.actions_taken == []
    assert package.open_questions == []
    assert package.claims[0].evidence_refs == ["EV-001"]


def test_research_task_rejects_unknown_agent_type():
    with pytest.raises(ValidationError):
        ResearchTask(
            task_id="TASK-INV-UNKNOWN",
            agent_type="unbounded_browser",  # type: ignore[arg-type]
            question="This agent type is not in the governed HISYS-T-027 contract.",
        )
