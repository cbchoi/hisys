"""Tests for Investigator multi-agent research contracts.

Traceability: HISYS-T-027, HISYS-INST-INV-001, HISYS-FR-INV-001..006,
HISYS-FR-MEM-001..005, HISYS-TPL-RESEARCH-SEARCH-001.
"""

import pytest
from pydantic import ValidationError

from hisys.investigator import (
    ClaimRecord,
    EvidenceItem,
    EvidencePackage,
    FixtureContradictionAgent,
    FixtureResearchAgent,
    FormalismComparisonAgent,
    SelfOrganizationMechanismAgent,
    ResearchTask,
    create_research_agent,
)


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



def test_research_agent_factory_returns_fixture_agents():
    fixture_agent = create_research_agent("fixture")
    contradiction_agent = create_research_agent("fixture_contradiction")

    assert isinstance(fixture_agent, FixtureResearchAgent)
    assert isinstance(contradiction_agent, FixtureContradictionAgent)


def test_research_agent_factory_rejects_unknown_agent_type():
    with pytest.raises(ValueError, match="Unsupported research agent type"):
        create_research_agent("unbounded_browser")


def test_fixture_research_agent_returns_claim_and_evidence_package():
    task = ResearchTask(
        task_id="TASK-FIXTURE-001",
        agent_type="fixture",
        question="Assess fixture overheating evidence.",
        query="hardware overheating risk",
        allowed_source_ids=["SRC-HW-MOCK-001"],
    )

    package = create_research_agent("fixture").run(task)

    assert package.agent_id == "fixture-research-agent"
    assert package.agent_type == "fixture"
    assert package.task_id == task.task_id
    assert package.external_side_effects is False
    assert package.claims
    assert package.evidence
    assert package.claims[0].evidence_refs == [package.evidence[0].evidence_id]
    assert package.evidence[0].source_id == "SRC-HW-MOCK-001"


def test_fixture_contradiction_agent_returns_limitation_or_open_question():
    task = ResearchTask(
        task_id="TASK-CONTRADICTION-001",
        agent_type="fixture_contradiction",
        question="Look for contradictory fixture interpretation.",
    )

    package = create_research_agent("fixture_contradiction").run(task)

    assert package.agent_id == "fixture-contradiction-agent"
    assert package.agent_type == "fixture_contradiction"
    assert package.external_side_effects is False
    assert package.open_questions or package.limitations



def test_formalism_domain_agent_returns_self_organization_formalism_candidates():
    task = ResearchTask(
        task_id="TASK-FORMALISM-001",
        agent_type="formalism_comparison",
        question="Assess formalisms that can express self-organizing systems.",
        query="formalism that can express self-organizing systems",
        allowed_source_ids=["SRC-FORMALISM-FIXTURE-001"],
    )

    package = create_research_agent("formalism_comparison").run(task)

    assert isinstance(create_research_agent("formalism_comparison"), FormalismComparisonAgent)
    assert package.agent_id == "formalism-comparison-agent"
    assert package.agent_type == "formalism_comparison"
    assert package.external_side_effects is False
    claim_text = "\n".join(claim.text for claim in package.claims)
    evidence_text = "\n".join(item.quoted_text or "" for item in package.evidence)
    assert "Dynamic Structure DEVS" in claim_text
    assert "graph rewriting" in claim_text
    assert "agent-based" in claim_text
    assert "topology-changing" in evidence_text
    assert "Assessment criteria" in evidence_text
    assert "Expressiveness: high for topology-changing discrete-event systems" in evidence_text
    assert "Simulation semantics: native executable semantics" in evidence_text
    assert "Verification/readability tradeoff" in evidence_text
    assert "Selection heuristic" in evidence_text
    assert "Choose Dynamic Structure DEVS" in evidence_text
    assert "Choose graph rewriting" in evidence_text
    assert "Choose agent-based modeling" in evidence_text
    assert all(claim.evidence_refs for claim in package.claims)


def test_self_organization_mechanism_agent_returns_modeling_criteria_and_open_questions():
    task = ResearchTask(
        task_id="TASK-MECHANISM-001",
        agent_type="self_organization_mechanism",
        question="Identify criteria for self-organization formalisms.",
        query="self-organizing systems formalism criteria",
        allowed_source_ids=["SRC-SELF-ORG-FIXTURE-001"],
    )

    package = create_research_agent("self_organization_mechanism").run(task)

    assert isinstance(create_research_agent("self_organization_mechanism"), SelfOrganizationMechanismAgent)
    assert package.agent_id == "self-organization-mechanism-agent"
    assert package.agent_type == "self_organization_mechanism"
    assert package.external_side_effects is False
    claim_text = "\n".join(claim.text for claim in package.claims)
    assert "local interaction rules" in claim_text
    assert "emergent global structure" in claim_text
    assert "feedback loop representation" in claim_text
    assert "boundary between component state and network topology" in claim_text
    assert "structural change as first-class state" in claim_text
    assert "Does the target formalism need executable simulation semantics?" in package.open_questions
    assert "Does it need compositional proof or verification support?" in package.open_questions
