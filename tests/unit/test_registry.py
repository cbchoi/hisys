"""Source registry governance tests.

Traceability: HISYS-FR-SRC-001..005, HISYS-NFR-SEC-003,
HISYS-NFR-SEC-005, HISYS-CON-022..023, HISYS-T-001, HISYS-T-002.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from hisys.registry import SourceBlockedError, SourceRegistry, build_initial_fixture_registry
from hisys.schemas import SourceRegistryEntry, WebComplianceReview


def test_initial_fixture_registry_contains_governed_sources():
    # HISYS-T-001: initial registry validates required source governance fields.
    registry = build_initial_fixture_registry()

    expected_ids = {
        "SRC-HW-MOCK-001",
        "SRC-WEB-RSS-001",
        "SRC-AGT-DARS-001",
        "SRC-HERMES-USER-001",
        "SRC-HERMES-TOOL-001",
        "SRC-SECRET-FIXTURE-001",
    }
    assert set(registry.entries) == expected_ids

    for entry in registry.entries.values():
        assert entry.owner
        assert entry.cadence
        assert entry.rate_limit
        assert entry.retention_rule
        assert entry.usage_constraints
        assert entry.reliability_evidence

    assert registry.assert_collectable("SRC-HW-MOCK-001").source_id == "SRC-HW-MOCK-001"
    assert registry.assert_collectable("SRC-HERMES-TOOL-001").scope_policy_ref


def test_blocked_negative_source_is_not_collectable():
    registry = build_initial_fixture_registry()
    with pytest.raises(SourceBlockedError):
        registry.assert_collectable("SRC-SECRET-FIXTURE-001")


def test_approved_source_requires_reliability_evidence():
    registry = SourceRegistry()
    entry = SourceRegistryEntry(
        source_id="SRC-HW-APPROVED-001",
        source_type="hardware_sensor",
        display_name="Approved but unsupported sensor",
        owner="lab-test",
        lifecycle_state="approved",
        reliability_class="A",
        access_method="device",
        cadence="PT1H",
        rate_limit="60/min",
        usage_constraints=["test_only"],
        retention_rule="P30D",
        producer_id="test",
    )
    with pytest.raises(ValueError, match="reliability_evidence"):
        registry.register(entry)


def test_web_compliance_review_blocks_incomplete_approval():
    # HISYS-T-002: approved web collection needs checklist metadata or exception.
    with pytest.raises(ValidationError) as exc:
        WebComplianceReview(
            review_id="WEB-COMPL-BAD-001",
            source_id="SRC-WEB-BAD-001",
            approval_decision="approved",
            approved_collection_method="rss",
            reviewer="qa",
            review_date=date(2026, 5, 8),
            producer_id="test",
            status="approved",
        )
    assert "completed checks" in str(exc.value)


def test_web_source_not_collectable_without_compliance_review():
    registry = SourceRegistry()
    registry.register(
        SourceRegistryEntry(
            source_id="SRC-WEB-EXP-001",
            source_type="web_news",
            display_name="Experimental feed missing compliance",
            owner="research",
            lifecycle_state="experimental",
            reliability_class="B",
            reliability_evidence=["fixture"],
            access_method="rss",
            cadence="PT1H",
            rate_limit="6/min",
            usage_constraints=["citation_required"],
            retention_rule="P30D",
            compliance_review_ref="WEB-COMPL-MISSING",
            producer_id="test",
        )
    )
    with pytest.raises(SourceBlockedError, match="WebComplianceReview"):
        registry.assert_collectable("SRC-WEB-EXP-001")


def test_web_source_collectable_with_experimental_compliance_review():
    registry = build_initial_fixture_registry()
    web = registry.assert_collectable("SRC-WEB-RSS-001")
    review = registry.web_reviews["SRC-WEB-RSS-001"]
    assert web.source_type == "web_news"
    assert review.approved_collection_method == "rss"
    assert review.no_access_control_bypass_required is True
    assert review.citation_metadata_preserved is True
