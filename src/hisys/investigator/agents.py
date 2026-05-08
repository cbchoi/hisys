"""Fixture Investigator research agents.

Traceability: HISYS-T-027, HISYS-INST-INV-001, HISYS-FR-INV-001..006,
HISYS-FR-MEM-001..005, HISYS-D-015, HISYS-DATA-002.
"""

from __future__ import annotations

from typing import Protocol

from .research import ClaimRecord, EvidenceItem, EvidencePackage, ResearchTask


class ResearchAgent(Protocol):
    """Common protocol for controlled Investigator research agents."""

    agent_id: str
    agent_type: str

    def run(self, task: ResearchTask) -> EvidencePackage:
        """Run one governed research task and return structured evidence."""


class FixtureResearchAgent:
    """Deterministic fixture agent that returns direct supporting evidence."""

    agent_id = "fixture-research-agent"
    agent_type = "fixture"

    def run(self, task: ResearchTask) -> EvidencePackage:
        source_id = task.allowed_source_ids[0] if task.allowed_source_ids else "SRC-HW-MOCK-001"
        evidence = EvidenceItem(
            evidence_id=f"EV-{task.task_id}-001",
            task_id=task.task_id,
            agent_id=self.agent_id,
            source_id=source_id,
            path=f"fixture://research/{task.task_id}.json",
            title="Fixture research evidence",
            quoted_text=f"Fixture evidence for: {task.question}",
            retrieved_at="2026-05-08T00:00:00Z",
            content_hash=f"sha256:{task.task_id.lower()}-fixture-evidence",
        )
        claim = ClaimRecord(
            claim_id=f"CLAIM-{task.task_id}-001",
            text=f"Fixture research supports investigation question: {task.question}",
            confidence=0.8,
            evidence_refs=[evidence.evidence_id],
        )
        return EvidencePackage(
            package_id=f"EPKG-{task.task_id}-FIXTURE",
            task_id=task.task_id,
            agent_id=self.agent_id,
            agent_type="fixture",
            claims=[claim],
            evidence=[evidence],
            actions_taken=["fixture_read"],
        )


class FixtureContradictionAgent:
    """Deterministic fixture agent that contributes caution/open questions."""

    agent_id = "fixture-contradiction-agent"
    agent_type = "fixture_contradiction"

    def run(self, task: ResearchTask) -> EvidencePackage:
        evidence = EvidenceItem(
            evidence_id=f"EV-{task.task_id}-CONTRA-001",
            task_id=task.task_id,
            agent_id=self.agent_id,
            source_id="SRC-FIXTURE-CONTRADICTION-001",
            path=f"fixture://research/{task.task_id}-contradiction.json",
            title="Fixture contradiction review",
            quoted_text="A single fixture observation may be insufficient to establish a repeated pattern.",
            retrieved_at="2026-05-08T00:00:00Z",
            content_hash=f"sha256:{task.task_id.lower()}-fixture-contradiction",
        )
        claim = ClaimRecord(
            claim_id=f"CLAIM-{task.task_id}-CONTRA-001",
            text="The investigation should distinguish one-off fixture evidence from repeated operational risk.",
            confidence=0.7,
            evidence_refs=[evidence.evidence_id],
            limitations=["Contradiction agent uses deterministic fixture caution, not live corroboration."],
        )
        return EvidencePackage(
            package_id=f"EPKG-{task.task_id}-CONTRADICTION",
            task_id=task.task_id,
            agent_id=self.agent_id,
            agent_type="fixture_contradiction",
            claims=[claim],
            evidence=[evidence],
            limitations=["No live corroborating source checked in fixture mode."],
            open_questions=["Is the observed condition repeated across time or independent sources?"],
            actions_taken=["fixture_contradiction_review"],
        )


def create_research_agent(agent_type: str) -> ResearchAgent:
    """Create a governed fixture research agent by type."""

    if agent_type == "fixture":
        return FixtureResearchAgent()
    if agent_type == "fixture_contradiction":
        return FixtureContradictionAgent()
    raise ValueError(f"Unsupported research agent type: {agent_type}")
