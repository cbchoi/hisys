"""Fixture Investigator research agents.

Traceability: HISYS-T-027, HISYS-T-029, HISYS-INST-INV-001,
HISYS-FR-INV-001..006, HISYS-FR-MEM-001..005, HISYS-D-015,
HISYS-DATA-002.
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



class FormalismComparisonAgent:
    """Domain fixture agent for comparing self-organization formalisms."""

    agent_id = "formalism-comparison-agent"
    agent_type = "formalism_comparison"

    def run(self, task: ResearchTask) -> EvidencePackage:
        evidence = EvidenceItem(
            evidence_id=f"EV-{task.task_id}-FORMALISM-001",
            task_id=task.task_id,
            agent_id=self.agent_id,
            source_id="SRC-FORMALISM-FIXTURE-001",
            path="fixture://research/formalisms/self-organization-formalisms.json",
            title="Formalism candidates for self-organizing systems",
            quoted_text=(
                "Assessment criteria for self-organizing-system formalisms: expressiveness for "
                "structure/behavior co-evolution, explicit structural-change semantics, executable "
                "simulation semantics, compositionality, analyzability, and readability. "
                "Dynamic Structure DEVS: Expressiveness: high for topology-changing discrete-event "
                "systems; Structural change: first-class model transition; Simulation semantics: "
                "native executable semantics; Verification/readability tradeoff: precise but can "
                "be technically heavy. graph rewriting: Expressiveness: high for local network "
                "rewrites and structural invariants; Structural change: native graph transformation "
                "rules; Simulation semantics: requires an execution/control strategy; Verification/"
                "readability tradeoff: strong structural reasoning but weaker built-in temporal "
                "simulation semantics. agent-based modeling: Expressiveness: high for heterogeneous "
                "local agents and emergent macro-patterns; Structural change: usually encoded in "
                "agent/environment rules; Simulation semantics: straightforward simulation but "
                "verification is weaker. Selection heuristic: Choose Dynamic Structure DEVS when "
                "topology-changing executable model state is central; Choose graph rewriting when "
                "local structural transformation rules and invariants are central; Choose agent-based "
                "modeling when decentralized local behavior and emergence are central."
            ),
            retrieved_at="2026-05-08T00:00:00Z",
            content_hash="sha256:formalism-self-organization-fixture-v2",
        )
        claims = [
            ClaimRecord(
                claim_id=f"CLAIM-{task.task_id}-ASSESSMENT-001",
                text=(
                    "Assessment criteria for this formalism choice should include expressiveness for "
                    "structure/behavior co-evolution, explicit structural-change semantics, Simulation "
                    "semantics: native executable semantics or a declared execution strategy, compositionality, "
                    "analyzability, and Verification/readability tradeoff. Expressiveness: high for "
                    "topology-changing discrete-event systems is the Dynamic Structure DEVS strength. "
                    "Selection heuristic: Choose "
                    "Dynamic Structure DEVS for topology-changing executable model state; Choose graph "
                    "rewriting for local structural transformation rules and invariants; Choose agent-based "
                    "modeling for decentralized local behavior and emergence."
                ),
                confidence=0.86,
                evidence_refs=[evidence.evidence_id],
            ),
            ClaimRecord(
                claim_id=f"CLAIM-{task.task_id}-DSDEVS-001",
                text=(
                    "Dynamic Structure DEVS is a strong candidate when the formalism must treat "
                    "topology-changing system structure as part of executable model state; its "
                    "assessment strengths are explicit structural-change semantics and native "
                    "simulation semantics, while its main limitation is readability/verification "
                    "complexity for non-DEVS specialists."
                ),
                confidence=0.82,
                evidence_refs=[evidence.evidence_id],
            ),
            ClaimRecord(
                claim_id=f"CLAIM-{task.task_id}-GRAPH-001",
                text=(
                    "graph rewriting is a strong candidate when self-organization is expressed as "
                    "local structural transformation rules over a network or graph; its strengths "
                    "are native topology rewrites and structural invariants, while an execution "
                    "strategy is needed to obtain simulation semantics comparable to DEVS."
                ),
                confidence=0.78,
                evidence_refs=[evidence.evidence_id],
            ),
            ClaimRecord(
                claim_id=f"CLAIM-{task.task_id}-ABM-001",
                text=(
                    "agent-based modeling is a strong candidate when local agent interaction rules "
                    "and emergent macro-level behavior are the primary concern; it is readable and "
                    "simulation-oriented, but structural change and verification obligations often "
                    "need additional discipline or formal constraints."
                ),
                confidence=0.76,
                evidence_refs=[evidence.evidence_id],
            ),
        ]
        return EvidencePackage(
            package_id=f"EPKG-{task.task_id}-FORMALISM",
            task_id=task.task_id,
            agent_id=self.agent_id,
            agent_type="formalism_comparison",
            claims=claims,
            evidence=[evidence],
            limitations=[
                "Domain fixture is curated for controlled harness testing and is not a live literature review."
            ],
            open_questions=[
                "Which candidate formalism best matches the required execution semantics and proof obligations?"
            ],
            actions_taken=["formalism_fixture_comparison"],
        )


class SelfOrganizationMechanismAgent:
    """Domain fixture agent for self-organization modeling criteria."""

    agent_id = "self-organization-mechanism-agent"
    agent_type = "self_organization_mechanism"

    def run(self, task: ResearchTask) -> EvidencePackage:
        evidence = EvidenceItem(
            evidence_id=f"EV-{task.task_id}-SELFORG-001",
            task_id=task.task_id,
            agent_id=self.agent_id,
            source_id="SRC-SELF-ORG-FIXTURE-001",
            path="fixture://research/formalisms/self-organization-criteria.json",
            title="Criteria for formalizing self-organization",
            quoted_text=(
                "Self-organization formalisms should represent local interaction rules, feedback, "
                "emergent global structure, adaptation over time, and structural change as "
                "first-class state when topology co-evolves with behavior."
            ),
            retrieved_at="2026-05-08T00:00:00Z",
            content_hash="sha256:self-organization-criteria-fixture-v1",
        )
        claim = ClaimRecord(
            claim_id=f"CLAIM-{task.task_id}-CRITERIA-001",
            text=(
                "A useful formalism for self-organizing systems should capture local interaction rules, "
                "feedback loop representation, emergent global structure, adaptation over time, the "
                "boundary between component state and network topology, and structural change as "
                "first-class state."
            ),
            confidence=0.84,
            evidence_refs=[evidence.evidence_id],
        )
        return EvidencePackage(
            package_id=f"EPKG-{task.task_id}-SELFORG",
            task_id=task.task_id,
            agent_id=self.agent_id,
            agent_type="self_organization_mechanism",
            claims=[claim],
            evidence=[evidence],
            limitations=[
                "Criteria fixture identifies modeling requirements but does not rank candidates for a specific project."
            ],
            open_questions=[
                "Does the target formalism need executable simulation semantics?",
                "Does it need compositional proof or verification support?",
                "Does topology change need to be represented inside model state rather than external metadata?",
            ],
            actions_taken=["self_organization_criteria_fixture"],
        )


def create_research_agent(agent_type: str) -> ResearchAgent:
    """Create a governed fixture research agent by type."""

    if agent_type == "fixture":
        return FixtureResearchAgent()
    if agent_type == "fixture_contradiction":
        return FixtureContradictionAgent()
    if agent_type == "formalism_comparison":
        return FormalismComparisonAgent()
    if agent_type == "self_organization_mechanism":
        return SelfOrganizationMechanismAgent()
    raise ValueError(f"Unsupported research agent type: {agent_type}")
