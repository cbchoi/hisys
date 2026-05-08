"""Web source compliance review schema.

Traceability:
- HISYS-NFR-SEC-003, HISYS-NFR-SEC-005 (approved source qualification,
  web access-control non-bypass, citation and minimization metadata).
- HISYS-CON-022, HISYS-CON-023 (no unauthorized scraping or access bypass).
- HISYS-T-002 (web source compliance gate).
- HISYS-CHECK-WEB-001.
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Literal

from pydantic import Field, model_validator

from .base import BaseRecord

ComplianceDecision = Literal["approved", "experimental", "blocked", "requires_legal_human_review"]
CollectionMethod = Literal["api", "rss", "permitted_scraping", "manual", "blocked"]


class WebComplianceReview(BaseRecord):
    """Controlled checklist result for autonomous web/news collection."""

    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-NFR-SEC-003",
        "HISYS-NFR-SEC-005",
        "HISYS-CON-022",
        "HISYS-CON-023",
        "HISYS-T-002",
    )

    review_id: str
    source_id: str
    official_api_or_feed_exists: bool | None = None
    robots_txt_reviewed: bool | None = None
    terms_of_service_reviewed: bool | None = None
    copyright_license_reviewed: bool | None = None
    authentication_requirement_identified: bool | None = None
    rate_limits_recorded: bool | None = None
    no_access_control_bypass_required: bool | None = None
    citation_metadata_preserved: bool | None = None
    excerpt_minimization_policy: str | None = None
    exception_approval_ref: str | None = None
    approval_decision: ComplianceDecision
    approved_collection_method: CollectionMethod
    reviewer: str
    review_date: date
    next_review_date: date | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    notes: str = ""

    status: ComplianceDecision = "experimental"

    @model_validator(mode="after")
    def _approved_requires_complete_gate(self) -> "WebComplianceReview":
        if self.approval_decision != "approved":
            return self

        missing = [
            field
            for field in (
                "official_api_or_feed_exists",
                "robots_txt_reviewed",
                "terms_of_service_reviewed",
                "copyright_license_reviewed",
                "authentication_requirement_identified",
                "rate_limits_recorded",
                "no_access_control_bypass_required",
                "citation_metadata_preserved",
            )
            if getattr(self, field) is not True
        ]
        if missing and not self.exception_approval_ref:
            raise ValueError(
                "approved web compliance review requires completed checks or exception_approval_ref: "
                + ", ".join(missing)
            )
        if self.approved_collection_method == "blocked":
            raise ValueError("approved web compliance review cannot use blocked collection method")
        if not self.excerpt_minimization_policy and not self.exception_approval_ref:
            raise ValueError(
                "approved web compliance review requires excerpt_minimization_policy or exception_approval_ref"
            )
        return self
