"""Common configuration envelope validation tests.

Traceability: HISYS-FR-AGT-001..005, HISYS-T-019, HISYS-T-020,
HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.
"""

from __future__ import annotations

from hisys.config.validation import validate_config_document


def test_common_config_envelope_rejects_unknown_schema_with_path_issue():
    report = validate_config_document(
        {
            "schema_id": "hisys.unknown.config",
            "schema_version": "0.1.0",
            "config_id": "unknown-default",
            "config_version": "0.1.0",
            "owner": "sysailab",
            "status": "draft",
            "classification": "runtime_config",
            "traceability": {
                "requirements": ["HISYS-T-019"],
                "constraints": ["HISYS-CON-010"],
            },
            "spec": {},
        },
        config_ref="inline://unknown",
    )

    assert report.valid is False
    assert report.schema_id == "hisys.unknown.config"
    assert any(issue.path == "schema_id" and issue.code == "unknown_schema_id" for issue in report.issues)


def test_common_config_envelope_reports_missing_traceability_paths():
    report = validate_config_document(
        {
            "schema_id": "hisys.dars.config",
            "schema_version": "0.1.0",
            "config_id": "dars-default",
            "config_version": "0.1.0",
            "owner": "sysailab",
            "status": "draft",
            "classification": "runtime_config",
            "spec": {},
        },
        config_ref="inline://dars-missing-traceability",
    )

    assert report.valid is False
    issue_paths = {issue.path for issue in report.issues}
    assert "traceability.requirements" in issue_paths
    assert "traceability.constraints" in issue_paths
