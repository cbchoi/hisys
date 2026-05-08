"""Investigator multi-agent research evidence contracts.

Traceability: HISYS-T-027, HISYS-T-029, HISYS-INST-INV-001,
HISYS-FR-INV-001..006, HISYS-FR-MEM-001..005, HISYS-D-015,
HISYS-DATA-002, HISYS-TPL-RESEARCH-SEARCH-001.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AgentType = Literal[
    "fixture",
    "fixture_contradiction",
    "formalism_comparison",
    "self_organization_mechanism",
    "local_pdf",
    "selenium_read_only",
    "delegated_llm",
]


class ResearchTask(BaseModel):
    """A governed unit of work for an Investigator research agent."""

    task_id: str
    agent_type: AgentType
    question: str
    query: str | None = None
    allowed_source_ids: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    disallowed_actions: list[str] = Field(
        default_factory=lambda: [
            "login",
            "post",
            "form_submit",
            "upload",
            "purchase",
            "credential_use",
        ]
    )
    expected_output_schema: str = "EvidencePackage"


class EvidenceItem(BaseModel):
    """Traceable evidence collected by a research agent."""

    evidence_id: str
    task_id: str
    agent_id: str
    source_id: str | None = None
    url: str | None = None
    path: str | None = None
    title: str
    quoted_text: str | None = None
    excerpt_ref: str | None = None
    retrieved_at: str
    content_hash: str | None = None


class ClaimRecord(BaseModel):
    """A claim that must cite one or more evidence references."""

    claim_id: str
    text: str
    confidence: float
    evidence_refs: list[str]
    limitations: list[str] = Field(default_factory=list)


class EvidencePackage(BaseModel):
    """Standard output contract for every Investigator research agent."""

    package_id: str
    task_id: str
    agent_id: str
    agent_type: AgentType
    claims: list[ClaimRecord]
    evidence: list[EvidenceItem]
    limitations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    external_side_effects: bool = False
    actions_taken: list[str] = Field(default_factory=list)
