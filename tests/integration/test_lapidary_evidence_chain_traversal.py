"""End-to-end Lapidary evidence-chain traversal integration test.

Traceability: HISYS-SCHEMA-001, HISYS-FR-INV-001, HISYS-FR-INV-003,
HISYS-FR-CE-004, HISYS-DARS-CONTRACT-001, HISYS-D-015, HISYS-FR-ADM-002,
HISYS-T-024 (end-to-end traceability).

Traversal path exercised:

    investigation_data_package
      -> claim_evidence_ledger (ZettelMemo)
        -> synthesis (PerspectiveProfile)
          -> decision_packet (AlertDecisionRecord via ChiefEditorRuntime)
            -> EvidenceChainRecord (persisted sidecar + governance audit)

The persisted EvidenceChainRecord must round-trip from JSON and be traversable
from ``decision_ref`` down to ``synthesis_refs`` -> ``claim_ledger_refs`` ->
``evidence_refs`` -> ``source_refs`` (HISYS-T-024).
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.chief_editor import ChiefEditorPolicy, ChiefEditorRuntime
from hisys.config import InstanceRoot
from hisys.editor import MemoReviewReport
from hisys.schemas import (
    AlertDecisionRecord,
    EvidenceChainRecord,
    HisysMode,
    InvestigationDataPackage,
    PerspectiveProfile,
    SourceRegistryEntry,
    ZettelMemo,
)


YYYYMMDD = "20260512"
PRODUCER_ID = "lapidary-traversal-test"


def _build_source() -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id="SRC-LAPIDARY-TRAVERSAL-001",
        source_type="hardware_sensor",
        display_name="Lapidary traversal fixture source",
        owner="lab-test",
        lifecycle_state="experimental",
        reliability_class="B",
        access_method="device",
        cadence="P1H",
        rate_limit="60/min",
        usage_constraints=["test_only"],
        retention_rule="P7D",
        producer_id=PRODUCER_ID,
    )


def _build_perspective() -> PerspectiveProfile:
    return PerspectiveProfile(
        perspective_id="PERSP-LAPIDARY-TRAVERSAL-001",
        title="Lapidary traversal synthesis perspective",
        owner="research",
        lifecycle_state="active",
        intent="trace evidence from synthesis to source",
        producer_id=PRODUCER_ID,
        status="active",
    )


def _build_memo(source: SourceRegistryEntry, perspective: PerspectiveProfile) -> ZettelMemo:
    return ZettelMemo(
        memo_id="MEM-LAPIDARY-TRAVERSAL-001",
        title="Conflict detected across linked evidence",
        summary="lapidary traversal evidence conflict",
        body="Linked to signal and source; raw payload preserved upstream.",
        source_refs=[source.source_id],
        signal_refs=["SIG-LAPIDARY-TRAVERSAL-001"],
        perspective_id=perspective.perspective_id,
        confidence=0.74,
        tags=["hisys", "lapidary-traversal"],
        links=[],
        revision="1",
        review_status="flagged_conflict",
        status="flagged_conflict",
        producer_id=PRODUCER_ID,
    )


def test_evidence_chain_traverses_decision_to_synthesis_to_claim_to_source(
    tmp_path: Path,
) -> None:
    source = _build_source()
    perspective = _build_perspective()
    memo = _build_memo(source, perspective)

    # Pre-build an InvestigationDataPackage that *would* be produced upstream.
    # We will fill in the EvidenceChainRecord later (once the runtime mints the
    # decision_ref/alert_id) so InvestigationDataPackage governance validation
    # holds at the synthesis level here.
    upstream_investigation = InvestigationDataPackage(
        investigation_id="lapidary-traversal-inv-001",
        request_id="lapidary-traversal-req-001",
        domain="general",
        objective="trace evidence chain from decision back to source",
        evidence_packages=[],
        claim_evidence_ledger_refs=[memo.memo_id],
        runtime_boundary_refs=[],
        hisys_mode=HisysMode(level="none"),
    )

    review_report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id=PRODUCER_ID,
        hisys_mode=HisysMode(level="decision"),
    )

    decision_report = runtime.decide_run(
        [memo], memo_review_report=review_report, yyyymmdd=YYYYMMDD
    )

    # Decision packet was produced and exactly one evidence chain emitted.
    assert len(decision_report.alert_decision_refs) == 1
    assert len(decision_report.evidence_chain_refs) == 1
    alert_id = decision_report.alert_decision_refs[0]
    chain_id = decision_report.evidence_chain_refs[0]

    alert_decisions_dir = tmp_path / "data" / "alert-decisions" / YYYYMMDD
    decision_json = alert_decisions_dir / f"{alert_id}.json"
    sidecar_chain_json = alert_decisions_dir / f"{alert_id}.evidence_chain.json"
    audit_chain_json = (
        tmp_path
        / "data"
        / "audit"
        / YYYYMMDD
        / "lapidary-governance"
        / "evidence-chains"
        / f"{chain_id}.json"
    )
    assert decision_json.exists()
    assert sidecar_chain_json.exists()
    assert audit_chain_json.exists()

    # Round-trip the persisted EvidenceChainRecord from both sidecar and audit.
    sidecar_chain = EvidenceChainRecord.model_validate_json(
        sidecar_chain_json.read_text(encoding="utf-8")
    )
    audit_chain = EvidenceChainRecord.model_validate_json(
        audit_chain_json.read_text(encoding="utf-8")
    )
    # Both persisted copies must agree (audit mirror of sidecar chain).
    assert sidecar_chain.model_dump(mode="json", round_trip=True) == audit_chain.model_dump(
        mode="json", round_trip=True
    )
    chain = sidecar_chain

    # JSON shape preserves traversal-critical fields verbatim.
    raw_chain = json.loads(audit_chain_json.read_text(encoding="utf-8"))
    assert raw_chain["chain_id"] == chain_id
    assert raw_chain["decision_ref"] == alert_id
    assert raw_chain["structured_links_source_of_truth"] is True
    assert raw_chain["wikilinks_are_projection"] is True
    assert "path_summary" not in raw_chain

    # decision_ref -> persisted AlertDecisionRecord (decision packet).
    assert chain.decision_ref == alert_id
    decision = AlertDecisionRecord.model_validate_json(
        decision_json.read_text(encoding="utf-8")
    )
    assert decision.alert_id == chain.decision_ref
    assert decision.trigger_reason == "memo_conflict_detected"
    assert memo.memo_id in decision.memo_refs

    # synthesis_refs -> PerspectiveProfile (Gem-level synthesis).
    assert chain.synthesis_refs == [perspective.perspective_id]

    # claim_ledger_refs -> ZettelMemo claim ledger entries.
    assert chain.claim_ledger_refs == [memo.memo_id]
    assert set(chain.claim_ledger_refs).issubset(set(decision.memo_refs))

    # evidence_refs -> extracted signal refs preserved on the memo.
    assert chain.evidence_refs == list(memo.signal_refs)
    assert set(chain.evidence_refs).issubset(set(decision.signal_refs))

    # source_refs -> Stone-level source registry references.
    assert chain.source_refs == list(memo.source_refs)
    assert source.source_id in chain.source_refs

    # Attachment refs may be empty in this fixture but the schema field exists.
    assert chain.attachment_refs == []

    # Round-trip the chain into an InvestigationDataPackage at the decision
    # level: this proves the chain produced by the Chief Editor is governance-
    # valid as the investigation package's evidence_chain on close-out.
    closed_investigation = InvestigationDataPackage.model_validate(
        {
            **upstream_investigation.model_dump(mode="json", round_trip=True),
            "hisys_mode": HisysMode(level="decision").model_dump(mode="json", round_trip=True),
            "evidence_chain": chain.model_dump(mode="json", round_trip=True),
        }
    )
    assert closed_investigation.evidence_chain is not None
    closed_chain = closed_investigation.evidence_chain
    assert closed_chain.decision_ref == alert_id
    assert closed_chain.synthesis_refs == [perspective.perspective_id]
    assert closed_chain.claim_ledger_refs == [memo.memo_id]
    assert closed_chain.evidence_refs == list(memo.signal_refs)
    assert closed_chain.source_refs == [source.source_id]

    # Pydantic JSON round-trip on the wrapping investigation package preserves
    # the full traversal payload (HISYS-T-024 audit round-trip).
    investigation_json = closed_investigation.model_dump_json()
    assert "path_summary" not in json.loads(investigation_json)["evidence_chain"]
    rehydrated = InvestigationDataPackage.model_validate_json(investigation_json)
    assert rehydrated.evidence_chain is not None
    rehydrated_chain = rehydrated.evidence_chain
    assert rehydrated_chain.chain_id == chain.chain_id
    assert rehydrated_chain.decision_ref == alert_id
    assert rehydrated_chain.synthesis_refs == [perspective.perspective_id]
    assert rehydrated_chain.claim_ledger_refs == [memo.memo_id]
    assert rehydrated_chain.evidence_refs == list(memo.signal_refs)
    assert rehydrated_chain.source_refs == [source.source_id]
    assert rehydrated_chain.path_summary.startswith("decision/Jewel -> synthesis/Gem")
