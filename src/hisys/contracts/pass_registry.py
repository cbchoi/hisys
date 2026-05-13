"""Pass-contract registry models and promotion helpers.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json

_ALLOWED_STATUS = {"candidate", "active", "retired"}


@dataclass(frozen=True)
class PassContractRegistryEntry:
    contract_id: str
    domain: str
    question_type: str
    status: str
    version: str
    minimum_evidence: dict[str, Any]
    blocked_if: list[str]
    promotion_gate: str
    active: bool = False
    human_approval_ref: str | None = None
    automatic_promotion_allowed: bool = False
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_or_live_action_approved: bool = False
    review_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_STATUS:
            raise ValueError(f"invalid status: {self.status}")
        if not self.contract_id.strip():
            raise ValueError("contract_id is required")
        if self.active and self.status != "active":
            raise ValueError("active entries must use status=active")
        if self.status == "active" and not self.human_approval_ref:
            raise ValueError("human_approval_ref is required for active contracts")
        if self.automatic_promotion_allowed:
            raise ValueError("automatic promotion is not allowed")
        if self.external_call_made or self.mutation_performed or self.publication_or_live_action_approved:
            raise ValueError("registry entries must not record live side effects")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_pass_contract_registry(path: Path) -> list[PassContractRegistryEntry]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        entries = data
    elif "contracts" in data:
        entries = data["contracts"]
    elif "contract_id" in data:
        entries = [data]
    else:
        entries = []
    return [PassContractRegistryEntry(**entry) for entry in entries]


def candidate_from_proposal(proposal: dict[str, Any]) -> PassContractRegistryEntry:
    candidate = proposal["candidate_contract"]
    return PassContractRegistryEntry(
        contract_id=candidate["contract_id"],
        domain=proposal["domain"],
        question_type=proposal["question_type"],
        status="candidate",
        active=False,
        version="0.1.0",
        minimum_evidence=dict(candidate.get("minimum_evidence", {})),
        blocked_if=list(candidate.get("blocked_if", [])),
        promotion_gate=candidate.get("promotion_gate", "human_reviewed_traceable_change"),
        automatic_promotion_allowed=False,
        external_call_made=False,
        mutation_performed=False,
        publication_or_live_action_approved=False,
    )


def find_contract(entries: list[PassContractRegistryEntry], *, domain: str, question_type: str, active_only: bool = True) -> PassContractRegistryEntry | None:
    for entry in entries:
        if entry.domain == domain and entry.question_type == question_type and (not active_only or entry.active):
            return entry
    return None


def promote_candidate(candidate: PassContractRegistryEntry, *, human_approval_ref: str, review_refs: list[str]) -> PassContractRegistryEntry:
    if not human_approval_ref.strip():
        raise ValueError("human_approval_ref is required")
    return PassContractRegistryEntry(
        contract_id=candidate.contract_id,
        domain=candidate.domain,
        question_type=candidate.question_type,
        status="active",
        version=candidate.version,
        minimum_evidence=dict(candidate.minimum_evidence),
        blocked_if=list(candidate.blocked_if),
        promotion_gate=candidate.promotion_gate,
        active=True,
        human_approval_ref=human_approval_ref,
        review_refs=review_refs,
        automatic_promotion_allowed=False,
        external_call_made=False,
        mutation_performed=False,
        publication_or_live_action_approved=False,
    )
