"""Chief Editor / DARS browser review chain helpers.

Traceability: HISYS-FR-INV-001..006, HISYS-FR-AGT-001..005,
HISYS-DARS-CONTRACT-001.
"""

from __future__ import annotations


def _build_browser_chief_editor_review(
    *,
    request_id: str,
    browser_investigation_report_ref: str,
    browser_report: dict[str, object],
    sufficiency: dict[str, object],
    producer_id: str,
) -> dict[str, object]:
    basis_refs = {
        "browser_investigation_report": browser_investigation_report_ref,
        "evidence_package": str(browser_report.get("evidence_package_ref") or ""),
        "source_candidates": str(browser_report.get("source_candidates_ref") or ""),
        "competitive_matrix": str(browser_report.get("competitive_matrix_ref") or ""),
        "evidence_sufficiency": str(browser_report.get("evidence_sufficiency_ref") or ""),
        "memo": str(browser_report.get("memo_ref") or ""),
    }
    return {
        "schema_id": "hisys.chief_editor.browser_investigation_review",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "browser_investigation_report_ref": browser_investigation_report_ref,
        "decision": "accept_for_devil_dars_adversarial_review",
        "basis_refs": {key: value for key, value in basis_refs.items() if value},
        "review_readiness": sufficiency.get("review_readiness"),
        "chief_editor_questions_for_devil_dars": [
            "Are high-strength competitive signals independently corroborated by patents, datasheets, filings, papers, or distributor/spec pages?",
            "Are conclusions normalized by segment before comparing vendors or technologies?",
            "Are source candidates sufficient to avoid shallow-page or vendor-marketing bias?",
        ],
        "human_approval_required": True,
        "approval_status": "not_requested",
        "action_taken": "none",
        "external_call_made": False,
        "mutation_performed": False,
        "producer_id": producer_id,
    }


def _build_browser_dars_review(
    *,
    request_id: str,
    chief_editor_review_ref: str,
    chief_review: dict[str, object],
    matrix: dict[str, object],
    producer_id: str,
) -> dict[str, object]:
    rows = [row for row in matrix.get("rows", []) if isinstance(row, dict)]
    questions = [str(item) for item in chief_review.get("chief_editor_questions_for_devil_dars", [])]
    findings: list[str] = []
    rows_text = "\n".join(
        f"{row.get('company_or_source', '')} {row.get('technology_signals', '')} {row.get('evidence_excerpt', '')}"
        for row in rows
    ).lower()
    if "dunlee" in rows_text or any("dunlee" in item.lower() for item in questions):
        findings.append("Dunlee LMB claims need explicit patent/spec cross-reference; current signal is strong but should not alone decide overall competitiveness.")
    if "varex" in rows_text or any("varex" in item.lower() for item in questions):
        findings.append("Varex breadth may reflect catalog scope rather than superior tube technology; compare product-spec rows against COMET and distributor evidence.")
    if "malvern" in rows_text or any("malvern" in item.lower() for item in questions):
        findings.append("Malvern Panalytical evidence may be instrument-integrated analytical XRF/XRD tubes, so segment scope must be separated from general x-ray tube manufacturing.")
    if "canon" in rows_text or any("canon" in item.lower() for item in questions):
        findings.append("Canon ETD signals appear medical/dental and stationary-anode focused; avoid ranking it against industrial/NDT vendors without segment normalization.")
    if not findings:
        findings.append("No company-specific adversarial finding generated; require human review of matrix rows before final acceptance.")
    revisions = [
        "Normalize conclusions by segment: CT, medical/dental, industrial/NDT, analytical XRF/XRD, and security/irradiation.",
        "Map every high-strength row to at least one corroborating evidence class: patent, datasheet/specification, distributor/spec page, filing, or paper.",
        "Downgrade any claim supported only by vendor marketing text to preliminary signal, not accepted conclusion.",
    ]
    return {
        "schema_id": "hisys.dars.browser_investigation_review",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "chief_editor_review_ref": chief_editor_review_ref,
        "decision": "requires_revision_before_final_acceptance",
        "allowed_actions": "advisory_only",
        "external_call_made": False,
        "mutation_performed": False,
        "risk_classification": "evidence_quality_adversarial_review_not_cybersecurity",
        "dars_backend": "deterministic_local_advisory",
        "adversarial_findings": findings,
        "required_revisions": revisions,
        "questions_reviewed": questions,
        "matrix_rows_reviewed": len(rows),
        "producer_id": producer_id,
    }


def _build_browser_dars_revision_resolution(
    *,
    request_id: str,
    dars_review_ref: str,
    chief_editor_review_ref: str,
    competitive_matrix_ref: str,
    dars_review: dict[str, object],
    matrix: dict[str, object],
    producer_id: str,
) -> dict[str, object]:
    rows = [row for row in matrix.get("rows", []) if isinstance(row, dict)]
    segment_rows: list[dict[str, object]] = []
    corroboration_rows: list[dict[str, object]] = []
    blockers: list[str] = []
    independent_classes = {"patent", "technical_paper", "datasheet_or_specification", "filing_or_annual_report", "distributor_or_shop_page"}
    for index, row in enumerate(rows, start=1):
        row_label = str(row.get("company_or_source") or f"row-{index}")
        segment = str(row.get("segment") or _infer_browser_segment(row)).strip()
        if segment == "unknown":
            blockers.append(f"Segment normalization missing for {row_label}.")
        signal_strength = str(row.get("competitive_signal_strength", "")).lower()
        corroborating_class = str(row.get("corroborating_evidence_class") or row.get("source_type") or "").strip()
        if signal_strength == "high" and corroborating_class not in independent_classes:
            blockers.append(f"High-strength row lacks independent corroboration class for {row_label}.")
        segment_rows.append({
            "row_index": index,
            "company_or_source": row_label,
            "normalized_segment": segment,
            "basis": "explicit_row_segment" if row.get("segment") else "heuristic_from_row_text",
        })
        corroboration_rows.append({
            "row_index": index,
            "company_or_source": row_label,
            "competitive_signal_strength": signal_strength or "unspecified",
            "corroborating_evidence_class": corroborating_class or "missing",
            "independent_corroboration_present": corroborating_class in independent_classes,
            "evidence_refs": row.get("evidence_refs", []),
        })
    segment_complete = bool(rows) and not any(item["normalized_segment"] == "unknown" for item in segment_rows)
    corroboration_complete = bool(rows) and not any(
        item["competitive_signal_strength"] == "high" and not item["independent_corroboration_present"]
        for item in corroboration_rows
    )
    ready = segment_complete and corroboration_complete and not blockers
    return {
        "schema_id": "hisys.browser_dars_revision_resolution",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "dars_review_ref": dars_review_ref,
        "chief_editor_review_ref": chief_editor_review_ref,
        "competitive_matrix_ref": competitive_matrix_ref,
        "decision": "ready_for_final_acceptance_review" if ready else "revision_required_before_final_acceptance",
        "segment_normalization_status": "complete" if segment_complete else "incomplete",
        "corroboration_mapping_status": "complete" if corroboration_complete else "incomplete",
        "segment_normalization_rows": segment_rows,
        "corroboration_mapping_rows": corroboration_rows,
        "resolved_dars_revision_items": dars_review.get("required_revisions", []),
        "remaining_blockers": blockers,
        "final_acceptance_allowed": ready,
        "allowed_actions": "advisory_only",
        "external_call_made": False,
        "mutation_performed": False,
        "producer_id": producer_id,
    }


def _infer_browser_segment(row: dict[str, object]) -> str:
    text = f"{row.get('company_or_source', '')} {row.get('technology_signals', '')} {row.get('evidence_excerpt', '')}".lower()
    if any(token in text for token in ["ct", "computed tomography"]):
        return "ct"
    if any(token in text for token in ["dental", "medical"]):
        return "medical_dental"
    if any(token in text for token in ["industrial", "ndt", "inspection"]):
        return "industrial_ndt"
    if any(token in text for token in ["xrf", "xrd", "analytical"]):
        return "analytical_xrf_xrd"
    if any(token in text for token in ["security", "irradiation"]):
        return "security_irradiation"
    return "unknown"


def _browser_revision_ready_for_final_review(revision: dict[str, object]) -> bool:
    return (
        revision.get("decision") == "ready_for_final_acceptance_review"
        and revision.get("final_acceptance_allowed") is True
        and revision.get("segment_normalization_status") == "complete"
        and revision.get("corroboration_mapping_status") == "complete"
        and not revision.get("remaining_blockers")
        and revision.get("external_call_made") is False
        and revision.get("mutation_performed") is False
    )


def _build_final_browser_acceptance_review(
    *,
    request_id: str,
    revision_resolution_ref: str,
    revision: dict[str, object],
    producer_id: str,
) -> dict[str, object]:
    return {
        "schema_id": "hisys.chief_editor.final_browser_acceptance_review",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "revision_resolution_ref": revision_resolution_ref,
        "dars_review_ref": str(revision.get("dars_review_ref", "")),
        "chief_editor_review_ref": str(revision.get("chief_editor_review_ref", "")),
        "competitive_matrix_ref": str(revision.get("competitive_matrix_ref", "")),
        "decision": "accept_for_human_reviewed_use",
        "accepted_conditions": [
            "segment_normalization_complete",
            "independent_corroboration_mapping_complete",
        ],
        "acceptance_scope": "browser_investigation_evidence_package_for_human_reviewed_use",
        "dars_role": "advisory_only_non_executable",
        "publication_or_live_action_approved": False,
        "human_approval_required_for_consequential_use": True,
        "external_call_made": False,
        "mutation_performed": False,
        "action_taken": "none",
        "producer_id": producer_id,
    }


def _primary_browser_segment(segment_signals: str) -> str:
    signal = segment_signals.lower()
    if "ct" in signal:
        return "ct"
    if "medical" in signal or "dental" in signal:
        return "medical_dental"
    if "industrial" in signal or "ndt" in signal or "inspection" in signal:
        return "industrial_ndt"
    if "xrf" in signal or "xrd" in signal or "analytical" in signal:
        return "analytical_xrf_xrd"
    if "security" in signal or "irradiation" in signal:
        return "security_irradiation"
    return "unknown"

