"""Source registry and compliance gate.

Traceability:
- HISYS-FR-SRC-001..005 (source identity, lifecycle, reliability,
  cadence, rate limit, usage constraints, retention, approval).
- HISYS-NFR-SEC-003, HISYS-NFR-SEC-005 and HISYS-CON-022..023
  (web compliance and access-control non-bypass).
- HISYS-T-001 and HISYS-T-002.
- HISYS-SRC-REG-INIT-001 and HISYS-CHECK-WEB-001.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..schemas import SourceRegistryEntry, WebComplianceReview

COLLECTABLE_STATES = {"experimental", "approved"}
BLOCKED_STATES = {"blocked", "suspended", "retired"}


class SourceRegistryError(ValueError):
    """Base registry/governance error."""


class SourceNotRegisteredError(SourceRegistryError):
    """Raised when collection is attempted for an unknown source."""


class SourceBlockedError(SourceRegistryError):
    """Raised when lifecycle or compliance policy blocks collection."""


@dataclass
class SourceRegistry:
    """In-memory controlled source registry for implementation fixtures.

    This class intentionally keeps persistence out of scope for I2. It is the
    governance boundary used by later investigator/adapters before collection.
    """

    entries: dict[str, SourceRegistryEntry] = field(default_factory=dict)
    web_reviews: dict[str, WebComplianceReview] = field(default_factory=dict)

    def register(self, entry: SourceRegistryEntry) -> SourceRegistryEntry:
        if entry.source_id in self.entries:
            raise SourceRegistryError(f"duplicate source_id: {entry.source_id}")
        if entry.lifecycle_state == "approved" and not entry.reliability_evidence:
            raise SourceRegistryError(
                f"approved source requires reliability_evidence: {entry.source_id}"
            )
        self.entries[entry.source_id] = entry
        return entry

    def register_many(self, entries: Iterable[SourceRegistryEntry]) -> None:
        for entry in entries:
            self.register(entry)

    def add_web_review(self, review: WebComplianceReview) -> WebComplianceReview:
        if review.source_id not in self.entries:
            raise SourceNotRegisteredError(review.source_id)
        entry = self.entries[review.source_id]
        if entry.source_type != "web_news":
            raise SourceRegistryError(
                f"web compliance review only applies to web_news sources: {review.source_id}"
            )
        self.web_reviews[review.source_id] = review
        return review

    def get(self, source_id: str) -> SourceRegistryEntry:
        try:
            return self.entries[source_id]
        except KeyError as exc:
            raise SourceNotRegisteredError(source_id) from exc

    def assert_collectable(self, source_id: str) -> SourceRegistryEntry:
        entry = self.get(source_id)
        if entry.lifecycle_state in BLOCKED_STATES or entry.reliability_class == "X":
            raise SourceBlockedError(f"source is blocked for collection: {source_id}")
        if entry.lifecycle_state not in COLLECTABLE_STATES:
            raise SourceBlockedError(
                f"source lifecycle_state is not collectable: {source_id}={entry.lifecycle_state}"
            )
        if entry.source_type == "web_news":
            review = self.web_reviews.get(source_id)
            if review is None:
                raise SourceBlockedError(
                    f"web_news source requires WebComplianceReview before collection: {source_id}"
                )
            if review.approval_decision not in {"approved", "experimental"}:
                raise SourceBlockedError(
                    f"web_news compliance decision blocks collection: {source_id}={review.approval_decision}"
                )
            if review.no_access_control_bypass_required is not True:
                raise SourceBlockedError(
                    f"web_news collection would require access-control bypass or lacks evidence: {source_id}"
                )
        return entry


def build_initial_fixture_registry() -> SourceRegistry:
    """Build the HISYS-SRC-REG-INIT-001 non-production fixture registry."""

    registry = SourceRegistry()
    registry.register_many(
        [
            SourceRegistryEntry(
                source_id="SRC-HW-MOCK-001",
                source_type="hardware_sensor",
                display_name="Mock calibrated hardware sensor",
                owner="lab-test",
                lifecycle_state="experimental",
                reliability_class="B",
                reliability_evidence=["HISYS-SRC-REG-INIT-001", "HISYS-FIXTURE-001"],
                access_method="file",
                cadence="P1H",
                rate_limit="60/min",
                usage_constraints=["test_only", "not_production_source"],
                retention_rule="P7D",
                producer_id="hisys-initial-registry",
            ),
            SourceRegistryEntry(
                source_id="SRC-WEB-RSS-001",
                source_type="web_news",
                display_name="Permitted RSS/API-style fixture",
                owner="research",
                lifecycle_state="experimental",
                reliability_class="B",
                reliability_evidence=["HISYS-SRC-REG-INIT-001", "HISYS-CHECK-WEB-001"],
                access_method="rss",
                cadence="PT1H",
                rate_limit="6/min",
                usage_constraints=["citation_required", "no_full_text_storage", "fixture_only"],
                retention_rule="P30D",
                compliance_review_ref="WEB-COMPL-SRC-WEB-RSS-001",
                producer_id="hisys-initial-registry",
            ),
            SourceRegistryEntry(
                source_id="SRC-AGT-DARS-001",
                source_type="agent_system",
                display_name="DARS critique fixture",
                owner="qa",
                lifecycle_state="experimental",
                reliability_class="B",
                reliability_evidence=["HISYS-SRC-REG-INIT-001", "HISYS-DARS-CONTRACT-001"],
                access_method="agent_handoff",
                cadence="ad_hoc",
                rate_limit="n/a",
                usage_constraints=["advisory_only", "fixture_only"],
                retention_rule="P30D",
                producer_id="hisys-initial-registry",
            ),
            SourceRegistryEntry(
                source_id="SRC-HERMES-USER-001",
                source_type="hermes_tool",
                display_name="Hermes user-input fixture",
                owner="hermes-runtime",
                lifecycle_state="experimental",
                reliability_class="B",
                reliability_evidence=["HISYS-SRC-REG-INIT-001", "HISYS-IF-016"],
                access_method="hermes_user_input",
                cadence="ad_hoc",
                rate_limit="n/a",
                usage_constraints=["preapproved_scope_only", "boundary_record_required"],
                retention_rule="P30D",
                scope_policy_ref="HISYS-SRC-REG-INIT-001 Section 2 SRC-HERMES-USER-001",
                producer_id="hisys-initial-registry",
            ),
            SourceRegistryEntry(
                source_id="SRC-HERMES-TOOL-001",
                source_type="hermes_tool",
                display_name="Hermes tool/delegated collection fixture",
                owner="hermes-runtime",
                lifecycle_state="experimental",
                reliability_class="B",
                reliability_evidence=["HISYS-SRC-REG-INIT-001", "HISYS-IF-016"],
                access_method="hermes_tool",
                cadence="PT1H",
                rate_limit="10/min",
                usage_constraints=["preapproved_scope_only", "boundary_record_required"],
                retention_rule="P30D",
                delegated_subagent_preapproval_ref="HISYS-SRC-REG-INIT-001 Section 4 item 5",
                scope_policy_ref="HISYS-SRC-REG-INIT-001 Section 2 SRC-HERMES-TOOL-001",
                producer_id="hisys-initial-registry",
            ),
            SourceRegistryEntry(
                source_id="SRC-SECRET-FIXTURE-001",
                source_type="agent_system",
                display_name="Secret/redaction negative fixture",
                owner="security-test",
                lifecycle_state="blocked",
                reliability_class="X",
                reliability_evidence=["HISYS-SRC-REG-INIT-001", "HISYS-T-021"],
                access_method="file",
                cadence="never",
                rate_limit="blocked",
                usage_constraints=["blocked", "quarantine_only"],
                retention_rule="P0D",
                producer_id="hisys-initial-registry",
            ),
        ]
    )
    registry.add_web_review(
        WebComplianceReview(
            review_id="WEB-COMPL-SRC-WEB-RSS-001",
            source_id="SRC-WEB-RSS-001",
            official_api_or_feed_exists=True,
            robots_txt_reviewed=True,
            terms_of_service_reviewed=True,
            copyright_license_reviewed=True,
            authentication_requirement_identified=True,
            rate_limits_recorded=True,
            no_access_control_bypass_required=True,
            citation_metadata_preserved=True,
            excerpt_minimization_policy="Store citation metadata and excerpts only; no full-text payload persistence.",
            approval_decision="experimental",
            approved_collection_method="rss",
            reviewer="fixture-reviewer",
            review_date="2026-05-08",
            evidence_refs=["HISYS-CHECK-WEB-001", "HISYS-SRC-REG-INIT-001"],
            producer_id="hisys-initial-registry",
            status="experimental",
        )
    )
    return registry


__all__ = [
    "SourceRegistry",
    "SourceRegistryError",
    "SourceNotRegisteredError",
    "SourceBlockedError",
    "build_initial_fixture_registry",
]
