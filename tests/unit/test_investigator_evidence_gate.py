"""Tests for Investigator evidence package gates.

Traceability: HISYS-T-027, HISYS-INST-INV-001, HISYS-FR-INV-001..006,
HISYS-FR-MEM-001..005, HISYS-DATA-002.
"""

import pytest

from hisys.investigator import ClaimRecord, EvidenceItem, EvidencePackage
from hisys.investigator.evidence import EvidenceValidationError, merge_evidence_packages, validate_evidence_package


def _evidence(evidence_id: str = "EV-001") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        task_id="TASK-001",
        agent_id="fixture-research-agent",
        source_id="SRC-HW-MOCK-001",
        title="Fixture evidence",
        quoted_text="Fixture evidence quote.",
        retrieved_at="2026-05-08T00:00:00Z",
        content_hash="sha256:fixture",
    )


def _package(**overrides) -> EvidencePackage:
    evidence = overrides.pop("evidence", [_evidence()])
    claims = overrides.pop(
        "claims",
        [
            ClaimRecord(
                claim_id="CLAIM-001",
                text="Fixture claim.",
                confidence=0.8,
                evidence_refs=[evidence[0].evidence_id],
            )
        ],
    )
    return EvidencePackage(
        package_id=overrides.pop("package_id", "EPKG-001"),
        task_id=overrides.pop("task_id", "TASK-001"),
        agent_id=overrides.pop("agent_id", "fixture-research-agent"),
        agent_type=overrides.pop("agent_type", "fixture"),
        claims=claims,
        evidence=evidence,
        **overrides,
    )


def test_evidence_gate_rejects_external_side_effects():
    package = _package(external_side_effects=True)

    with pytest.raises(EvidenceValidationError, match="external side effects"):
        validate_evidence_package(package)


def test_evidence_gate_rejects_claim_without_evidence_refs():
    package = _package(
        claims=[ClaimRecord(claim_id="CLAIM-EMPTY", text="No evidence.", confidence=0.1, evidence_refs=[])]
    )

    with pytest.raises(EvidenceValidationError, match="without evidence_refs"):
        validate_evidence_package(package)


def test_evidence_gate_rejects_missing_evidence_ref():
    package = _package(
        claims=[ClaimRecord(claim_id="CLAIM-MISSING", text="Missing ref.", confidence=0.1, evidence_refs=["EV-MISSING"])]
    )

    with pytest.raises(EvidenceValidationError, match="missing evidence"):
        validate_evidence_package(package)


def test_evidence_merger_combines_packages_and_surfaces_limitations_and_open_questions():
    first = _package(limitations=["limited fixture scope"])
    second = _package(
        package_id="EPKG-002",
        task_id="TASK-002",
        agent_id="fixture-contradiction-agent",
        agent_type="fixture_contradiction",
        evidence=[_evidence("EV-002")],
        claims=[ClaimRecord(claim_id="CLAIM-002", text="Caution claim.", confidence=0.7, evidence_refs=["EV-002"])],
        open_questions=["Need corroboration?"],
    )

    merged = merge_evidence_packages([first, second])

    assert merged.package_refs == ["EPKG-001", "EPKG-002"]
    assert len(merged.claims) == 2
    assert len(merged.evidence) == 2
    assert merged.limitations == ["limited fixture scope"]
    assert merged.open_questions == ["Need corroboration?"]
