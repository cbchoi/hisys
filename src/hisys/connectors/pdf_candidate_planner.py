"""Plan OA PDF candidates from DOI metadata without fetching PDF bytes.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PdfCandidatePlan:
    request_id: str
    plan_id: str
    connector_id: str
    doi: str
    metadata_access_ref: str
    metadata_evidence_refs: list[str]
    candidates: list[dict[str, str]]
    reason_codes: list[str]
    candidate_plan_only: bool
    pdf_downloaded: bool
    external_call_made: bool
    mutation_performed: bool
    plan_ref: str


class PdfCandidatePlanner:
    """Derive candidate OA PDF URLs from DOI metadata artifacts only."""

    connector_id = "pdf_candidate_planner"
    target_connector_id = "open_access_pdf_fetch"

    def plan(
        self,
        *,
        request_id: str,
        metadata: dict[str, Any],
        metadata_access_ref: str,
        metadata_evidence_refs: list[str],
        output_root: Path,
        yyyymmdd: str,
    ) -> PdfCandidatePlan:
        message = metadata.get("message", {}) if isinstance(metadata, dict) else {}
        doi = str(message.get("DOI") or request_id)
        license_signal = _license_signal(message)
        pdf_urls = _pdf_urls(message)
        candidates: list[dict[str, str]] = []
        reason_codes: list[str] = []
        if license_signal != "open_access":
            reason_codes.append("license_not_open_access")
        if not pdf_urls:
            reason_codes.append("metadata_pdf_link_missing")
        if license_signal == "open_access":
            for url in pdf_urls:
                candidates.append(
                    {
                        "candidate_id": f"PDF-CAND-{request_id}-{len(candidates) + 1:02d}",
                        "connector_id": self.target_connector_id,
                        "doi": doi,
                        "candidate_url": url,
                        "license_signal": license_signal,
                        "reason_code": "doi_metadata_open_access_pdf_hint",
                    }
                )
        plan_id = f"PDF-CANDIDATE-PLAN-{request_id}"
        plan_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/pdf-candidate-plan-{request_id}.json"
        plan = PdfCandidatePlan(
            request_id=request_id,
            plan_id=plan_id,
            connector_id=self.connector_id,
            doi=doi,
            metadata_access_ref=metadata_access_ref,
            metadata_evidence_refs=metadata_evidence_refs,
            candidates=candidates,
            reason_codes=reason_codes,
            candidate_plan_only=True,
            pdf_downloaded=False,
            external_call_made=False,
            mutation_performed=False,
            plan_ref=plan_ref,
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_root / plan_ref).write_text(json.dumps(asdict(plan), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return plan


def _license_signal(message: dict[str, Any]) -> str:
    for item in message.get("license", []) or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("URL") or item.get("url") or "").lower()
        if "creativecommons.org" in url or "open-access" in url or "open_access" in url:
            return "open_access"
    return "unknown"


def _pdf_urls(message: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for item in message.get("link", []) or []:
        if not isinstance(item, dict):
            continue
        content_type = str(item.get("content-type") or item.get("content_type") or "").lower()
        url = str(item.get("URL") or item.get("url") or "")
        if url and (content_type == "application/pdf" or url.lower().endswith(".pdf")):
            urls.append(url)
    return urls


__all__ = ["PdfCandidatePlan", "PdfCandidatePlanner"]
