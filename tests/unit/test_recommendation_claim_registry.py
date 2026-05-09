"""Tests for controlled recommendation claim registry construction.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.connectors.recommendation_claim_registry import RecommendationClaimRegistryBuilder


def test_recommendation_claim_registry_records_required_claims_without_approving_publication_language(tmp_path: Path) -> None:
    result = RecommendationClaimRegistryBuilder(root=tmp_path).build(
        request_id="REQ-REG-001",
        recommendation_text=(
            "Recommend developing Self-organizing Dynamic Structure DEVS with graph-rewrite structural transitions.\n"
            "Define evaluation scenarios for topology/behavior co-evolution."
        ),
        claim_texts=[
            "Self-organizing Dynamic Structure DEVS with graph-rewrite structural transitions is the recommended research direction.",
            "Evaluation scenarios should demonstrate topology/behavior co-evolution.",
        ],
        yyyymmdd="20260509",
    )

    assert result.recommendation_claim_registry_refs
    registry = json.loads((tmp_path / result.recommendation_claim_registry_refs[0]).read_text(encoding="utf-8"))
    assert registry["schema_id"] == "hisys.source_connector.recommendation_claim_registry"
    assert registry["request_id"] == "REQ-REG-001"
    assert registry["recommendation_text"]
    assert registry["required_claim_ids"] == [
        "CLAIM-REQ-REG-001-001",
        "CLAIM-REQ-REG-001-002",
    ]
    assert [claim["claim_id"] for claim in registry["required_claims"]] == registry["required_claim_ids"]
    assert registry["feeds_live_k_coverage_gates"] is True
    assert registry["controlled_claim_ids"] is True
    assert registry["does_not_prove_novelty"] is True
    assert registry["does_not_approve_publication_ready_claims"] is True
    assert registry["conditional_manuscript_language_only"] is True
    assert registry["external_call_made"] is False
    assert registry["mutation_performed"] is False
    assert registry["policy_refs"] == ["HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"]


def test_recommendation_claim_registry_rejects_empty_claims(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="claim_texts are required"):
        RecommendationClaimRegistryBuilder(root=tmp_path).build(
            request_id="REQ-REG-001",
            recommendation_text="Recommend a conditional direction.",
            claim_texts=[],
            yyyymmdd="20260509",
        )
