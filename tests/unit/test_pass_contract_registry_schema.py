"""Pass-contract registry schema tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.contracts.pass_registry import PassContractRegistryEntry, load_pass_contract_registry


def test_registry_entry_defaults_to_inactive_candidate():
    entry = PassContractRegistryEntry(
        contract_id="product_architecture_architecture_choice_v0_1_candidate",
        domain="product_architecture",
        question_type="architecture_choice",
        status="candidate",
        version="0.1.0",
        minimum_evidence={"artifact_refs_required": True},
        blocked_if=["no_traceable_artifact_refs"],
        promotion_gate="human_reviewed_traceable_change",
    )

    assert entry.status == "candidate"
    assert entry.active is False
    assert entry.automatic_promotion_allowed is False
    assert entry.external_call_made is False
    assert entry.mutation_performed is False
    assert entry.publication_or_live_action_approved is False


def test_registry_rejects_active_without_human_approval_ref():
    with pytest.raises(ValueError, match="human_approval_ref"):
        PassContractRegistryEntry(
            contract_id="unsafe_active",
            domain="product_architecture",
            question_type="architecture_choice",
            status="active",
            active=True,
            version="0.1.0",
            minimum_evidence={"artifact_refs_required": True},
            blocked_if=["no_traceable_artifact_refs"],
            promotion_gate="human_reviewed_traceable_change",
        )


def test_load_registry_fixture_round_trips(tmp_path: Path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"contracts": [{
        "contract_id": "candidate_001",
        "domain": "product_architecture",
        "question_type": "architecture_choice",
        "status": "candidate",
        "version": "0.1.0",
        "minimum_evidence": {"artifact_refs_required": True},
        "blocked_if": ["no_traceable_artifact_refs"],
        "promotion_gate": "human_reviewed_traceable_change"
    }]}), encoding="utf-8")

    entries = load_pass_contract_registry(path)

    assert len(entries) == 1
    assert entries[0].contract_id == "candidate_001"
