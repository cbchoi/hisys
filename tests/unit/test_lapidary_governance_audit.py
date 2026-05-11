"""Lapidary governance audit writer tests.

Traceability: HISYS-SCHEMA-001, HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001,
HISYS-D-015, HISYS-FR-ADM-002, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.audit import LapidaryGovernanceAuditWriter
from hisys.chief_editor import ChiefEditorPolicy, ChiefEditorRuntime
from hisys.config import InstanceRoot
from hisys.editor import MemoReviewReport
from hisys.schemas import (
    AppraiserSeparationPolicy,
    EvidenceChainRecord,
    EvidenceOriginWeight,
    HisysMode,
    WeightedDecisionAlternative,
    ZettelMemo,
)


def test_governance_audit_writer_persists_evidence_chain_under_audit_dir(tmp_path: Path):
    writer = LapidaryGovernanceAuditWriter(InstanceRoot(tmp_path))
    chain = EvidenceChainRecord(
        chain_id="CHAIN-AUDIT-001",
        producer_id="lapidary-audit-test",
        status="active",
        decision_ref="ALERT-AUDIT-001",
        synthesis_refs=["PERSP-AUDIT-001"],
        claim_ledger_refs=["MEM-AUDIT-001"],
        evidence_refs=["SIG-AUDIT-001"],
        source_refs=["SRC-AUDIT-001"],
    )

    path = writer.append(chain, yyyymmdd="20260512")

    expected = (
        tmp_path
        / "data"
        / "audit"
        / "20260512"
        / "lapidary-governance"
        / "evidence-chains"
        / "CHAIN-AUDIT-001.json"
    )
    assert path == expected
    assert path.exists()
    roundtrip = EvidenceChainRecord.model_validate_json(path.read_text(encoding="utf-8"))
    assert roundtrip.chain_id == chain.chain_id
    assert roundtrip.decision_ref == "ALERT-AUDIT-001"
    assert roundtrip.evidence_refs == ["SIG-AUDIT-001"]
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["chain_id"] == "CHAIN-AUDIT-001"
    assert raw["structured_links_source_of_truth"] is True


def test_governance_audit_writer_persists_weighted_decision_alternative(tmp_path: Path):
    writer = LapidaryGovernanceAuditWriter(InstanceRoot(tmp_path))
    alternative = WeightedDecisionAlternative(
        alternative_id="ALT-AUDIT-001",
        producer_id="lapidary-audit-test",
        status="active",
        label="External-heavy",
        claim="External evidence outweighs internal prior.",
        origin_weights=[
            EvidenceOriginWeight(
                evidence_origin="external_source",
                ref="SRC-AUDIT-001",
                origin_weight=0.7,
                source_quality=0.9,
                verification_status=0.8,
                recency=0.7,
                independence=0.9,
                contradiction_status=0.8,
                domain_fit=0.8,
            ),
            EvidenceOriginWeight(
                evidence_origin="internal_prior",
                ref="PERSP-AUDIT-001",
                origin_weight=0.3,
                source_quality=0.5,
                verification_status=0.4,
                recency=0.6,
                independence=0.3,
                contradiction_status=0.7,
                domain_fit=0.9,
            ),
        ],
        recommended_use="hybrid",
    )

    path = writer.append(alternative, yyyymmdd="20260512")

    expected = (
        tmp_path
        / "data"
        / "audit"
        / "20260512"
        / "lapidary-governance"
        / "weighted-alternatives"
        / "ALT-AUDIT-001.json"
    )
    assert path == expected
    assert path.exists()
    roundtrip = WeightedDecisionAlternative.model_validate_json(path.read_text(encoding="utf-8"))
    assert roundtrip.alternative_id == alternative.alternative_id
    assert roundtrip.recommended_use == "hybrid"
    assert roundtrip.weighted_score == alternative.weighted_score


def test_governance_audit_writer_persists_appraiser_separation_policy(tmp_path: Path):
    writer = LapidaryGovernanceAuditWriter(InstanceRoot(tmp_path))
    policy = AppraiserSeparationPolicy(
        policy_id="APPRAISER-POLICY-AUDIT-001",
        producer_id="lapidary-audit-test",
        status="active",
        appraiser_role="DARS/Appraiser",
        separate_from_roles=["Chief Editor", "Jeweler"],
        advisory_only=True,
        may_approve_decision=False,
        may_execute_action=False,
        checks=["confirmation_bias", "stale_evidence"],
    )

    path = writer.append(policy, yyyymmdd="20260512")

    expected = (
        tmp_path
        / "data"
        / "audit"
        / "20260512"
        / "lapidary-governance"
        / "appraiser-policies"
        / "APPRAISER-POLICY-AUDIT-001.json"
    )
    assert path == expected
    assert path.exists()
    roundtrip = AppraiserSeparationPolicy.model_validate_json(path.read_text(encoding="utf-8"))
    assert roundtrip.policy_id == policy.policy_id
    assert roundtrip.advisory_only is True
    assert roundtrip.may_approve_decision is False
    assert roundtrip.checks == ["confirmation_bias", "stale_evidence"]


def test_governance_audit_writer_rejects_unsupported_record(tmp_path: Path):
    writer = LapidaryGovernanceAuditWriter(InstanceRoot(tmp_path))
    with pytest.raises(TypeError, match="unsupported"):
        writer.append({"not": "a record"}, yyyymmdd="20260512")  # type: ignore[arg-type]


def test_governance_audit_writer_exposes_stable_audit_subroot(tmp_path: Path):
    instance = InstanceRoot(tmp_path)
    writer = LapidaryGovernanceAuditWriter(instance)

    assert writer.root_dir("20260512") == instance.audit_dir("20260512") / "lapidary-governance"


def test_chief_editor_runtime_mirrors_evidence_chain_to_governance_audit(tmp_path: Path):
    memo = _memo_for_decision(
        "MEM-CE-GOV-AUDIT-001",
        review_status="flagged_conflict",
        summary="governed audit-mirrored evidence chain",
    )
    review_report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id="chief-editor-audit-test",
        hisys_mode=HisysMode(level="decision"),
    )

    decision_report = runtime.decide_run(
        [memo], memo_review_report=review_report, yyyymmdd="20260508"
    )

    alert_id = decision_report.alert_decision_refs[0]
    chain_id = decision_report.evidence_chain_refs[0]
    sidecar = (
        tmp_path
        / "data"
        / "alert-decisions"
        / "20260508"
        / f"{alert_id}.evidence_chain.json"
    )
    audit_path = (
        tmp_path
        / "data"
        / "audit"
        / "20260508"
        / "lapidary-governance"
        / "evidence-chains"
        / f"{chain_id}.json"
    )
    assert sidecar.exists(), "sidecar evidence chain must be preserved"
    assert audit_path.exists(), "evidence chain must also land under audit dir"
    roundtrip = EvidenceChainRecord.model_validate_json(audit_path.read_text(encoding="utf-8"))
    assert roundtrip.chain_id == chain_id
    assert roundtrip.decision_ref == alert_id


def test_chief_editor_runtime_default_mode_writes_no_governance_audit(tmp_path: Path):
    memo = _memo_for_decision(
        "MEM-CE-AUDIT-NONE-001",
        review_status="flagged_conflict",
        summary="default-mode skips governance audit",
    )
    review_report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id="chief-editor-audit-none-test",
    )

    decision_report = runtime.decide_run(
        [memo], memo_review_report=review_report, yyyymmdd="20260508"
    )

    assert decision_report.evidence_chain_refs == []
    governance_dir = (
        tmp_path / "data" / "audit" / "20260508" / "lapidary-governance"
    )
    assert not governance_dir.exists()


def _memo_for_decision(memo_id: str, *, review_status: str, summary: str) -> ZettelMemo:
    return ZettelMemo(
        memo_id=memo_id,
        title=summary.title(),
        summary=summary,
        body=f"# Fixture memo\n\n{summary}\n",
        source_refs=["SRC-HW-MOCK-001"],
        signal_refs=["SIG-CE-001"],
        perspective_id="PERSP-OPS-001",
        confidence=0.82,
        tags=["hisys", "zettel-draft"],
        links=["OBS-CE-001"],
        revision="1",
        review_status=review_status,
        status=review_status,
        producer_id="chief-editor-audit-test",
    )
