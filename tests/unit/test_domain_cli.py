"""CLI tests for domain-general Hisys MVP boundary.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024,
HISYS-CON-010..012.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.connectors.claim_coverage_gate import ClaimCoverageGateBuilder
from hisys.connectors.claim_evidence_ledger import ClaimEvidenceLedgerBuilder
from hisys.connectors.claim_evidence_summary import ClaimEvidenceSummaryBuilder
from hisys.connectors.open_access_pdf import OpenAccessPdfConnector
from hisys.connectors.recommendation_claim_registry import RecommendationClaimRegistryBuilder
from hisys.connectors.pdf_evidence_promotion import PdfEvidencePromotionLoader
from hisys.connectors.pdf_quote_extractor import PdfQuoteExtractor
from hisys.operations.codebase_analysis import (
    build_codebase_inventory,
    build_codebase_scope_map,
    build_codebase_validation_plan,
    build_python_symbol_index,
    scan_codebase_risk_boundaries,
    write_codebase_inventory,
    write_codebase_risk_scan,
    write_codebase_scope_map,
    write_python_symbol_index,
)


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


def test_runtime_boundary_check_cli_writes_consistency_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    safe_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.json"
    safe_md = "runtime-boundary/traceability-coverage/20260520/coverage-report.md"
    safe_json_path = instance_root / safe_ref
    safe_md_path = instance_root / safe_md
    safe_json_path.parent.mkdir(parents=True, exist_ok=True)
    safe_json_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.traceability.coverage.v1",
                "advisory_only": True,
                "requires_human_review": True,
                "external_call_made": False,
                "mutation_performed": False,
                "raw_source_content_persisted": False,
                "requirement_count": 0,
                "covered_requirement_count": 0,
                "coverage_ratio": 1.0,
                "unreferenced_requirements": [],
                "orphan_test_ids": [],
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    safe_md_path.write_text("# coverage\n- advisory_only: true\n", encoding="utf-8")

    result = main(
        [
            "runtime-boundary-check",
            "--instance",
            str(instance_root),
            "--date",
            "20260520",
            "--ref",
            safe_ref,
            "--ref",
            safe_md,
            "--ref",
            "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json",
            "--ref",
            "runtime-boundary/../escape.txt",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "runtime-boundary consistency report" in captured.out
    assert "external_call_made: false" in captured.out
    json_path = (
        instance_root
        / "runtime-boundary"
        / "runtime-boundary-consistency"
        / "20260520"
        / "consistency-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "runtime-boundary-consistency"
        / "20260520"
        / "consistency-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.runtime_boundary.consistency.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["ok_ref_count"] == 2
    assert data["unsafe_refs"] == ["runtime-boundary/../escape.txt"]
    assert data["missing_files"] == [
        "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json"
    ]


def test_traceability_coverage_cli_writes_runtime_boundary_report(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "traceability-coverage",
            "--instance",
            str(tmp_path),
            "--date",
            "20260520",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "traceability coverage report" in captured.out
    assert "external_call_made: false" in captured.out
    json_path = tmp_path / "runtime-boundary" / "traceability-coverage" / "20260520" / "coverage-report.json"
    md_path = tmp_path / "runtime-boundary" / "traceability-coverage" / "20260520" / "coverage-report.md"
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.traceability.coverage.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False


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
    assert decision["dars_acceptance_decision"] == "accepted_as_conditions"
    assert decision["dars_accepted"] is True
    assert decision["accepted_dars_action_ids"] == ["RECACT-HISYS-REQ-RESEARCH-GAP-001-SOURCE-VALIDATION"]
    assert decision["dars_blocks_decision"] is False
    assert "Chief Editor accepted DARS advisory actions as non-executable conditions." in decision["conditions"]
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


def test_investigate_domain_preserves_claim_coverage_gate_refs_as_conditional_manuscript_gate(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-coverage.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual coverage bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-coverage.pdf",
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
    claim_id = "CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS"
    ledger_result = ClaimEvidenceLedgerBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id=claim_id,
        claim_text="Dynamic Structure DEVS is relevant to topology-changing simulation.",
        relation="support",
        rationale="The quote supports relevance, not novelty proof.",
        source_quote_refs=quote_result.source_quote_refs,
        yyyymmdd="20260509",
    )
    summary_result = ClaimEvidenceSummaryBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id=claim_id,
        claim_evidence_ledger_refs=ledger_result.claim_evidence_ledger_refs,
        yyyymmdd="20260509",
    )
    gate_result = ClaimCoverageGateBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        required_claim_ids=[claim_id, "CLAIM-HISYS-REQ-RESEARCH-GAP-001-TOPOLOGY-BEHAVIOR"],
        claim_evidence_summary_refs=summary_result.claim_evidence_summary_refs,
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
            "--claim-coverage-gate-ref",
            gate_result.claim_coverage_gate_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["claim_coverage_gate_refs"] == gate_result.claim_coverage_gate_refs
    assert gate_result.claim_coverage_gate_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate_result.claim_coverage_gate_refs[0] in dars_trace["claim_coverage_gate_refs"]
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
    assert chief_decision["claim_coverage_gate_refs"] == gate_result.claim_coverage_gate_refs
    assert chief_decision["source_validation_status"] == "claim_coverage_gate_present"
    assert chief_decision["manuscript_language_gate"] == "conditional_only"
    assert chief_decision["conditional_manuscript_language_only"] is True
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep manuscript-facing claims conditional after claim coverage gating." in chief_decision["conditions"]


def test_investigate_domain_preserves_recommendation_claim_registry_refs_as_conditional_lineage(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    registry_result = RecommendationClaimRegistryBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        recommendation_text="Recommend DSDEVS and topology/behavior co-evolution evaluation scenarios.",
        claim_texts=[
            "Self-organizing Dynamic Structure DEVS is the recommended research direction.",
            "Evaluation scenarios should demonstrate topology/behavior co-evolution.",
        ],
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
            "--recommendation-claim-registry-ref",
            registry_result.recommendation_claim_registry_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["recommendation_claim_registry_refs"] == registry_result.recommendation_claim_registry_refs
    assert registry_result.recommendation_claim_registry_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry_result.recommendation_claim_registry_refs[0] in dars_trace["recommendation_claim_registry_refs"]
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
    assert chief_decision["recommendation_claim_registry_refs"] == registry_result.recommendation_claim_registry_refs
    assert chief_decision["source_validation_status"] == "recommendation_claim_registry_present"
    assert chief_decision["recommendation_claim_registry_conditional"] is True
    assert chief_decision["feeds_live_k_coverage_gates"] is True
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Run Live-K claim coverage gates before stronger manuscript-facing claims." in chief_decision["conditions"]


# ---------------------------------------------------------------------------
# M20.4 — investigate-domain --domain codebase fixture smoke.
# ---------------------------------------------------------------------------


def _seed_codebase_smoke_repo(repo: Path) -> None:
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pkg" / "mod.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )


def _materialize_complete_codebase_bundle_for_cli(
    *, instance_root: Path, repo: Path, date: str, request_id: str
) -> dict[str, str]:
    inventory = build_codebase_inventory(repo_root=repo)
    inv_ref = write_codebase_inventory(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        inventory=inventory,
    )["json_ref"]

    symbol_index = build_python_symbol_index(repo_root=repo)
    sym_ref = write_python_symbol_index(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        symbol_index=symbol_index,
    )["json_ref"]

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index
    )
    validation_plan = build_codebase_validation_plan(scope_map)
    scope_ref = write_codebase_scope_map(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        scope_map=scope_map,
        validation_plan=validation_plan,
    )["json_ref"]

    risk_scan = scan_codebase_risk_boundaries(repo_root=repo)
    risk_ref = write_codebase_risk_scan(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        scan=risk_scan,
    )["json_ref"]

    return {
        "inventory": inv_ref,
        "symbol_index": sym_ref,
        "scope_map": scope_ref,
        "validation_plan": (
            f"runtime-boundary/codebase-analysis/{date}/{request_id}/validation-plan.json"
        ),
        "risk_scan": risk_ref,
    }


def _write_codebase_smoke_request(
    path: Path, *, request_id: str, refs: dict[str, str]
) -> None:
    sources = [
        {
            "source_id": "SRC-INV",
            "source_type": "runtime_record",
            "ref": refs["inventory"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-SYM",
            "source_type": "runtime_record",
            "ref": refs["symbol_index"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-SCOPE",
            "source_type": "runtime_record",
            "ref": refs["scope_map"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-VALID",
            "source_type": "runtime_record",
            "ref": refs["validation_plan"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-RISK",
            "source_type": "runtime_record",
            "ref": refs["risk_scan"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
    ]
    path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": request_id,
                "domain": "codebase",
                "objective": "codebase: investigate-domain artifact-bridge smoke",
                "sources": sources,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_investigate_domain_codebase_smokes_local_bundle(
    tmp_path: Path, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_codebase_smoke_repo(repo)
    refs = _materialize_complete_codebase_bundle_for_cli(
        instance_root=instance_root,
        repo=repo,
        date="20260520",
        request_id="m20_4_smoke",
    )

    request_path = instance_root / "codebase-request.json"
    _write_codebase_smoke_request(
        request_path, request_id="HISYS-REQ-M20-4-SMOKE", refs=refs
    )

    exit_code = main(
        [
            "investigate-domain",
            "--instance",
            str(instance_root),
            "--request",
            str(request_path),
            "--date",
            "20260520",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "domain: codebase" in captured.out

    boundary_dir = (
        instance_root
        / "runtime-boundary"
        / "domain-investigation"
        / "codebase"
        / "20260520"
    )
    result_artifact = boundary_dir / "hisys-tool-result-HISYS-REQ-M20-4-SMOKE.json"
    assert result_artifact.exists()

    tool_result = json.loads(result_artifact.read_text(encoding="utf-8"))
    assert tool_result["domain"] == "codebase"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False
    assert tool_result["requires_human_review"] is True
    assert tool_result["quality_gate"] == "passed"
    assert tool_result["status"] == "completed"

    domain_result_artifacts = list(boundary_dir.glob("domain-investigation-result-*.json"))
    assert len(domain_result_artifacts) == 1
    domain_payload = json.loads(domain_result_artifacts[0].read_text(encoding="utf-8"))
    codebase_packages = [
        pkg
        for pkg in domain_payload["investigation_data"]["evidence_packages"]
        if pkg["evidence_type"] == "codebase_analysis_bundle"
    ]
    assert len(codebase_packages) == 1
    package = codebase_packages[0]
    assert package["evidence_refs"] == [
        refs["inventory"],
        refs["symbol_index"],
        refs["scope_map"],
        refs["risk_scan"],
    ]
    assert package["external_call_made"] is False
    assert package["mutation_performed"] is False

    report_path = (
        instance_root
        / "reports"
        / "run-summaries"
        / "20260520"
        / "domain-investigation-report.json"
    )
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["request_id"] == "HISYS-REQ-M20-4-SMOKE"
    assert report["domain"] == "codebase"
    assert report["tool_result_ref"] == str(result_artifact.relative_to(instance_root))
