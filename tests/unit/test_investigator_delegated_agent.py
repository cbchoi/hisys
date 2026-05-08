"""Tests for disabled delegated LLM/Hermes research-agent contract.

Traceability: HISYS-T-027, HISYS-FR-AGT-001..005, HISYS-DATA-005.
"""

import pytest

from hisys.investigator import ResearchTask
from hisys.investigator.delegated import (
    DelegatedAgentConfig,
    DelegatedAgentSafetyError,
    DelegatedLLMResearchAgent,
    parse_delegated_evidence_package,
)


def test_delegated_llm_agent_refuses_to_run_when_disabled():
    agent = DelegatedLLMResearchAgent(DelegatedAgentConfig(enabled=False))
    task = ResearchTask(
        task_id="TASK-DELEGATED-001",
        agent_type="delegated_llm",
        question="Research with delegated LLM agent.",
    )

    with pytest.raises(DelegatedAgentSafetyError, match="disabled"):
        agent.run(task)


def test_delegated_agent_rejects_free_form_answer():
    with pytest.raises(DelegatedAgentSafetyError, match="EvidencePackage JSON"):
        parse_delegated_evidence_package("This is a free-form answer, not JSON.")


def test_delegated_agent_accepts_only_evidence_package_json():
    payload = """
    {
      "package_id": "EPKG-DELEGATED-001",
      "task_id": "TASK-DELEGATED-001",
      "agent_id": "delegated-llm-research-agent",
      "agent_type": "delegated_llm",
      "claims": [
        {
          "claim_id": "CLAIM-DELEGATED-001",
          "text": "Delegated result is structured.",
          "confidence": 0.6,
          "evidence_refs": ["EV-DELEGATED-001"]
        }
      ],
      "evidence": [
        {
          "evidence_id": "EV-DELEGATED-001",
          "task_id": "TASK-DELEGATED-001",
          "agent_id": "delegated-llm-research-agent",
          "source_id": "SRC-DELEGATED-FIXTURE-001",
          "title": "Delegated fixture evidence",
          "quoted_text": "Structured delegated evidence.",
          "retrieved_at": "2026-05-08T00:00:00Z",
          "content_hash": "sha256:delegated-fixture"
        }
      ],
      "external_side_effects": false,
      "actions_taken": ["delegated_fixture_parse"]
    }
    """

    package = parse_delegated_evidence_package(payload)

    assert package.package_id == "EPKG-DELEGATED-001"
    assert package.agent_type == "delegated_llm"
    assert package.external_side_effects is False
    assert package.claims[0].evidence_refs == [package.evidence[0].evidence_id]


def test_delegated_agent_rejects_external_side_effect_package():
    payload = """
    {
      "package_id": "EPKG-DELEGATED-BAD",
      "task_id": "TASK-DELEGATED-002",
      "agent_id": "delegated-llm-research-agent",
      "agent_type": "delegated_llm",
      "claims": [],
      "evidence": [],
      "external_side_effects": true
    }
    """

    with pytest.raises(DelegatedAgentSafetyError, match="external side effects"):
        parse_delegated_evidence_package(payload)
