"""CLI tests for domain-general Hisys MVP boundary.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024,
HISYS-CON-010..012.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.connectors.claim_evidence_ledger import ClaimEvidenceLedgerBuilder
from hisys.connectors.claim_evidence_summary import ClaimEvidenceSummaryBuilder
from hisys.connectors.open_access_pdf import OpenAccessPdfConnector
from hisys.connectors.pdf_evidence_promotion import PdfEvidencePromotionLoader
from hisys.connectors.pdf_quote_extractor import PdfQuoteExtractor


def _write_domain_request(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": "HISYS-REQ-RESEARCH-GAP-001",
                "domain": "research",
                "objective": "find research gap among formalisms for self-organizing structure",
                "sources": [
                    {
                        "source_id": "SRC-FORMALISM-FIXTURE-001",
                        "source_type": "fixture",
                        "ref": "fixture://formalism-gap",
                        "access_mode": "read_only",
                    }
                ],
                "user_focus": "Separate source evidence from interpreted gap statements.",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_investigate_domain_writes_request_and_tool_result_boundary(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "domain investigation run" in captured.out
    assert "domain: research" in captured.out
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    request_artifact = boundary_dir / "hisys-tool-request-HISYS-REQ-RESEARCH-GAP-001.json"
    result_artifact = boundary_dir / "hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.json"
    assert request_artifact.exists()
    assert result_artifact.exists()

    request_data = json.loads(request_artifact.read_text(encoding="utf-8"))
    tool_result = json.loads(result_artifact.read_text(encoding="utf-8"))
    assert request_data["constraints"] == {
        "credential_use_allowed": False,
        "external_calls_allowed": False,
        "max_rounds": 3,
        "mutation_allowed": False,
    }
    assert tool_result["status"] == "completed"
    assert tool_result["domain"] == "research"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False
    assert tool_result["quality_gate"] == "passed"
    assert str(result_artifact.relative_to(tmp_path)) in tool_result["runtime_boundary_refs"]

    report = json.loads(
        (tmp_path / "reports" / "run-summaries" / "20260509" / "domain-investigation-report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["request_id"] == "HISYS-REQ-RESEARCH-GAP-001"
    assert report["domain"] == "research"
    assert report["tool_result_ref"] == str(result_artifact.relative_to(tmp_path))


def test_investigate_domain_research_gap_fixture_generates_alternatives(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "status: completed" in captured.out
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data_artifact = boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json"
    alternatives_artifact = boundary_dir / "alternative-decision-set-ALTSET-HISYS-REQ-RESEARCH-GAP-001.json"
    domain_result_artifact = boundary_dir / "domain-investigation-result-DRESULT-HISYS-REQ-RESEARCH-GAP-001.json"
    tool_result_artifact = boundary_dir / "hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.json"
    assert data_artifact.exists()
    assert alternatives_artifact.exists()
    assert domain_result_artifact.exists()

    data = json.loads(data_artifact.read_text(encoding="utf-8"))
    alternatives = json.loads(alternatives_artifact.read_text(encoding="utf-8"))
    domain_result = json.loads(domain_result_artifact.read_text(encoding="utf-8"))
    tool_result = json.loads(tool_result_artifact.read_text(encoding="utf-8"))

    assert data["evidence_packages"][0]["evidence_type"] == "research_gap_matrix"
    assert "Dynamic Structure DEVS" in data["evidence_packages"][0]["summary"]
    assert any("source-access-ACCESS-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in data["evidence_packages"][0]["evidence_refs"])
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in data["evidence_packages"][0]["evidence_refs"])
    assert alternatives["recommended_candidate_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert alternatives["candidates"][0]["candidate_type"] == "research_direction"
    assert "Self-organizing Dynamic Structure DEVS" in alternatives["candidates"][0]["claim"]
    assert domain_result["quality_gate"] == "passed"
    assert domain_result["recommended_alternative_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert tool_result["status"] == "completed"
    assert tool_result["recommended_alternative_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False

    dars_dir = tmp_path / "runtime-boundary" / "dars" / "20260509"
    dars_request = dars_dir / "dars-request-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json"
    dars_response = dars_dir / "dars-response-DARSRESP-HISYS-REQ-RESEARCH-GAP-001.json"
    dars_trace = dars_dir / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json"
    assert dars_request.exists()
    assert dars_response.exists()
    assert dars_trace.exists()
    assert str(dars_trace.relative_to(tmp_path)) in domain_result["dars_refs"]
    response = json.loads(dars_response.read_text(encoding="utf-8"))
    dars_request_payload = json.loads(dars_request.read_text(encoding="utf-8"))
    dars_trace_payload = json.loads(dars_trace.read_text(encoding="utf-8"))
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in dars_request_payload["record_refs"]["runtime_boundary"])
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in dars_trace_payload["evidence_refs"])
    assert response["producer"]["backend_kind"] == "loopback"
    assert response["producer"]["external_call_made"] is False
    assert response["boundary"]["action_taken"] == "none"
    assert response["boundary"]["external_side_effects_performed"] is False
    assert response["boundary"]["mutation_performed"] is False
    assert response["critique"]["recommended_actions"][0]["allowed_to_execute"] is False
    assert response["decision_trace"]["blocks_decision"] is False

    chief_dir = tmp_path / "runtime-boundary" / "chief-editor" / "research" / "20260509"
    chief_decision = chief_dir / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
    assert chief_decision.exists()
    decision = json.loads(chief_decision.read_text(encoding="utf-8"))
    assert decision["decision_type"] == "research_recommendation_review"
    assert decision["status"] == "recommend_with_conditions"
    assert decision["recommended_candidate_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert decision["source_validation_status"] == "fixture_source_evidence_present"
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in decision["source_evidence_refs"])
    assert "Validate fixture source evidence against live publisher pages before publication claims." in decision["conditions"]
    assert decision["action_taken"] == "none"
    assert decision["human_approval_required"] is True
    assert decision["external_call_made"] is False
    assert decision["mutation_performed"] is False


def test_investigate_domain_promotes_explicit_manual_pdf_evidence_refs(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-smoke.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual smoke bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-smoke.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data_artifact = boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json"
    data = json.loads(data_artifact.read_text(encoding="utf-8"))
    assert data["promoted_pdf_evidence_refs"] == [package.evidence_ref]
    assert package.access_ref in data["source_governance_refs"]
    assert package.evidence_ref in data["source_governance_refs"]
    assert package.evidence_ref in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert package.evidence_ref in dars_trace["evidence_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["source_validation_status"] == "manual_pdf_evidence_promoted"
    assert chief_decision["promoted_pdf_evidence_refs"] == [package.evidence_ref]


def test_investigate_domain_preserves_explicit_pdf_quote_refs_without_strengthening_claims(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-smoke.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual quote bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-quote.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    quote_result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
            "--source-quote-ref",
            quote_result.source_quote_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["source_quote_refs"] == quote_result.source_quote_refs
    assert quote_result.source_quote_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert quote_result.source_quote_refs[0] in dars_trace["source_quote_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["source_quote_refs"] == quote_result.source_quote_refs
    assert chief_decision["source_validation_status"] == "manual_pdf_quotes_present"
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep novelty claims conditional after quote extraction." in chief_decision["conditions"]


def test_investigate_domain_preserves_claim_evidence_ledger_refs_without_strengthening_claims(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-ledger.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual ledger bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-ledger.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    quote_result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )
    ledger_result = ClaimEvidenceLedgerBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id="CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS",
        claim_text="Dynamic Structure DEVS is relevant to topology-changing simulation.",
        relation="support",
        rationale="The quote records structural change evidence but does not prove novelty.",
        source_quote_refs=quote_result.source_quote_refs,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
            "--source-quote-ref",
            quote_result.source_quote_refs[0],
            "--claim-evidence-ledger-ref",
            ledger_result.claim_evidence_ledger_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["claim_evidence_ledger_refs"] == ledger_result.claim_evidence_ledger_refs
    assert ledger_result.claim_evidence_ledger_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger_result.claim_evidence_ledger_refs[0] in dars_trace["claim_evidence_ledger_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["claim_evidence_ledger_refs"] == ledger_result.claim_evidence_ledger_refs
    assert chief_decision["source_validation_status"] == "claim_evidence_ledger_present"
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep novelty claims conditional after claim-evidence ledger mapping." in chief_decision["conditions"]


def test_investigate_domain_preserves_claim_evidence_summary_refs_as_advisory_confidence(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-summary.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual summary bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-summary.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    quote_result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )
    ledger_result = ClaimEvidenceLedgerBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id="CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS",
        claim_text="Dynamic Structure DEVS is relevant to topology-changing simulation.",
        relation="support",
        rationale="The quote supports relevance, not novelty proof.",
        source_quote_refs=quote_result.source_quote_refs,
        yyyymmdd="20260509",
    )
    summary_result = ClaimEvidenceSummaryBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id="CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS",
        claim_evidence_ledger_refs=ledger_result.claim_evidence_ledger_refs,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
            "--source-quote-ref",
            quote_result.source_quote_refs[0],
            "--claim-evidence-ledger-ref",
            ledger_result.claim_evidence_ledger_refs[0],
            "--claim-evidence-summary-ref",
            summary_result.claim_evidence_summary_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["claim_evidence_summary_refs"] == summary_result.claim_evidence_summary_refs
    assert summary_result.claim_evidence_summary_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary_result.claim_evidence_summary_refs[0] in dars_trace["claim_evidence_summary_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["claim_evidence_summary_refs"] == summary_result.claim_evidence_summary_refs
    assert chief_decision["source_validation_status"] == "claim_evidence_summary_present"
    assert chief_decision["advisory_confidence_only"] is True
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep confidence advisory after claim-evidence summary aggregation." in chief_decision["conditions"]
