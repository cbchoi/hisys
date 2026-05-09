"""Register controlled recommendation claims for downstream coverage gates.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RecommendationClaimRecord(BaseModel):
    """A controlled recommendation claim derived from explicit recommendation text."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    claim_text: str
    source_recommendation_text: str
    controlled_claim_id: Literal[True] = True
    source_recommendation_ref: str | None = None
    advisory_lineage_only: Literal[True] = True


class RecommendationClaimRegistryRecord(BaseModel):
    """Registry of required recommendation claims for Live-K coverage gates."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.recommendation_claim_registry"] = "hisys.source_connector.recommendation_claim_registry"
    schema_version: Literal["0.1.0"] = "0.1.0"
    registry_id: str
    request_id: str
    recommendation_text: str
    source_recommendation_ref: str | None = None
    required_claims: list[RecommendationClaimRecord]
    required_claim_ids: list[str]
    feeds_live_k_coverage_gates: Literal[True] = True
    controlled_claim_ids: Literal[True] = True
    conditional_manuscript_language_only: Literal[True] = True
    does_not_prove_novelty: Literal[True] = True
    does_not_approve_publication_ready_claims: Literal[True] = True
    external_call_made: bool = False
    mutation_performed: Literal[False] = False
    policy_refs: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class RecommendationClaimRegistryResult:
    """Result refs for recommendation claim registry construction."""

    request_id: str
    recommendation_claim_registry_refs: list[str]
    required_claim_ids: list[str]
    external_call_made: bool = False
    mutation_performed: bool = False


class RecommendationClaimRegistryBuilder:
    """Build controlled required recommendation-claim registries."""

    def __init__(self, *, root: Path) -> None:
        self.root = root

    def build(
        self,
        *,
        request_id: str,
        recommendation_text: str,
        claim_texts: list[str],
        yyyymmdd: str,
        source_recommendation_ref: str | None = None,
    ) -> RecommendationClaimRegistryResult:
        if not recommendation_text.strip():
            raise ValueError("recommendation_text is required for recommendation claim registries")
        clean_claims = [claim.strip() for claim in claim_texts if claim.strip()]
        if not clean_claims:
            raise ValueError("claim_texts are required for recommendation claim registries")
        if source_recommendation_ref is not None and not source_recommendation_ref.startswith("runtime-boundary/"):
            raise ValueError("source_recommendation_ref must point to a runtime-boundary artifact")

        claims = [
            RecommendationClaimRecord(
                claim_id=f"CLAIM-{request_id}-{index:03d}",
                claim_text=claim_text,
                source_recommendation_text=recommendation_text,
                source_recommendation_ref=source_recommendation_ref,
            )
            for index, claim_text in enumerate(clean_claims, start=1)
        ]
        registry = RecommendationClaimRegistryRecord(
            registry_id=f"REGISTRY-{request_id}-RECOMMENDATION-CLAIMS",
            request_id=request_id,
            recommendation_text=recommendation_text,
            source_recommendation_ref=source_recommendation_ref,
            required_claims=claims,
            required_claim_ids=[claim.claim_id for claim in claims],
            policy_refs=["HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
        )
        output_dir = self.root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        registry_path = output_dir / f"recommendation-claim-registry-{registry.registry_id}.json"
        registry_path.write_text(registry.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return RecommendationClaimRegistryResult(
            request_id=request_id,
            recommendation_claim_registry_refs=[str(registry_path.relative_to(self.root))],
            required_claim_ids=registry.required_claim_ids,
        )


__all__ = [
    "RecommendationClaimRegistryBuilder",
    "RecommendationClaimRegistryRecord",
    "RecommendationClaimRegistryResult",
    "RecommendationClaimRecord",
]
