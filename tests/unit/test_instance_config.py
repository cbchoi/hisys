"""Runtime instance and YAML config loader tests.

Traceability: HISYS-D-015, HISYS-D-016, HISYS-RUNTIME-DIR-001,
HISYS-FR-SRC-001..005, HISYS-T-001, HISYS-T-002, HISYS-T-023.
"""

from __future__ import annotations

from pathlib import Path

from hisys.config import InstanceRoot, load_source_registry


def test_instance_root_resolves_i4_runtime_directories(tmp_path: Path):
    # HISYS-RUNTIME-DIR-001: code repo and runtime instance data are separate.
    instance = InstanceRoot(tmp_path)

    assert instance.config_dir == tmp_path / "config"
    assert instance.templates_dir == tmp_path / "templates"
    assert instance.harness_dir == tmp_path / "harness"
    assert instance.raw_observations_dir("20260508") == tmp_path / "data" / "raw-observations" / "20260508"
    assert instance.audit_log_path("20260508") == tmp_path / "data" / "audit" / "20260508" / "AUDIT-20260508.jsonl"
    assert (
        instance.hermes_boundary_dir("20260508", "CAMP-HERMES-001")
        == tmp_path / "runtime-boundary" / "hermes" / "20260508" / "CAMP-HERMES-001"
    )


def test_source_registry_loader_reads_yaml_and_web_compliance(tmp_path: Path):
    config = tmp_path / "config"
    (config / "web-compliance").mkdir(parents=True)
    (config / "source-registry.yaml").write_text(
        """
sources:
  - source_id: SRC-HW-MOCK-001
    source_type: hardware_sensor
    display_name: Mock calibrated hardware sensor
    owner: lab-test
    lifecycle_state: experimental
    reliability_class: B
    reliability_evidence: [HISYS-FIXTURE-001]
    access_method: file
    cadence: P1H
    rate_limit: 60/min
    usage_constraints: [test_only]
    retention_rule: P7D
    producer_id: fixture-config
  - source_id: SRC-WEB-RSS-001
    source_type: web_news
    display_name: Permitted RSS fixture
    owner: research
    lifecycle_state: experimental
    reliability_class: B
    reliability_evidence: [HISYS-CHECK-WEB-001]
    access_method: rss
    cadence: PT1H
    rate_limit: 6/min
    usage_constraints: [citation_required, no_full_text_storage]
    retention_rule: P30D
    compliance_review_ref: WEB-COMPL-SRC-WEB-RSS-001
    producer_id: fixture-config
""".strip(),
        encoding="utf-8",
    )
    (config / "web-compliance" / "SRC-WEB-RSS-001.yaml").write_text(
        """
review_id: WEB-COMPL-SRC-WEB-RSS-001
source_id: SRC-WEB-RSS-001
official_api_or_feed_exists: true
robots_txt_reviewed: true
terms_of_service_reviewed: true
copyright_license_reviewed: true
authentication_requirement_identified: true
rate_limits_recorded: true
no_access_control_bypass_required: true
citation_metadata_preserved: true
excerpt_minimization_policy: Store citation metadata only.
approval_decision: experimental
approved_collection_method: rss
reviewer: fixture-reviewer
review_date: 2026-05-08
evidence_refs: [HISYS-CHECK-WEB-001]
producer_id: fixture-config
status: experimental
""".strip(),
        encoding="utf-8",
    )

    registry = load_source_registry(InstanceRoot(tmp_path))

    assert registry.assert_collectable("SRC-HW-MOCK-001").source_type == "hardware_sensor"
    assert registry.assert_collectable("SRC-WEB-RSS-001").source_type == "web_news"
    assert "SRC-WEB-RSS-001" in registry.web_reviews
