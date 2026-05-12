"""Release-readiness evidence report tests.

Traceability: HISYS-T-024, HISYS-FR-ADM-001..004, HISYS-DATA-001..005,
HISYS-CON-*.
"""

from __future__ import annotations

from pathlib import Path

import json

from hisys.cli.main import main
from hisys.operations.release_readiness import QualityGateResult, build_release_readiness_report


def test_release_readiness_cli_writes_evidence_report(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "release-readiness",
            "--instance",
            str(tmp_path),
            "--date",
            "20260512",
            "--quality-gate",
            "pytest:pass:469 passed",
            "--quality-gate",
            "traceability:pass:OK",
            "--quality-gate",
            "secret_scan:pass:hit_count=0",
            "--quality-gate",
            "backup_restore:pass:dry-run verified",
            "--quality-gate",
            "health_status:pass:overall_status=ok",
            "--trace-ref",
            "SourceRegistryEntry",
            "--trace-ref",
            "RawObservation",
            "--trace-ref",
            "ExtractedSignal",
            "--trace-ref",
            "ZettelMemo",
            "--trace-ref",
            "AlertDecisionRecord",
            "--trace-ref",
            "AuditEvent",
            "--format",
            "json",
        ]
    )

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["schema_id"] == "hisys.release_readiness_report"
    assert report["overall_status"] == "ready_for_review"
    assert report["release_decision"] == "human_review_ready"
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    report_dir = tmp_path / "reports" / "run-summaries" / "20260512"
    assert (report_dir / "hisys-release-readiness.json").exists()
    assert (report_dir / "hisys-release-readiness.md").exists()


def test_release_readiness_report_marks_ready_when_required_gates_pass(tmp_path: Path) -> None:
    report = build_release_readiness_report(
        runtime_root=tmp_path / "instance",
        quality_gates=[
            QualityGateResult(name="pytest", status="pass", evidence="121 passed"),
            QualityGateResult(name="traceability", status="pass", evidence="OK"),
            QualityGateResult(name="secret_scan", status="pass", evidence="hit_count=0"),
            QualityGateResult(name="backup_restore", status="pass", evidence="dry-run verified"),
            QualityGateResult(name="health_status", status="pass", evidence="overall_status=ok"),
        ],
        trace_path_refs=[
            "SourceRegistryEntry",
            "RawObservation",
            "ExtractedSignal",
            "ZettelMemo",
            "AlertDecisionRecord",
            "AuditEvent",
        ],
        known_gaps=[],
    )

    assert report.overall_status == "ready_for_review"
    assert report.required_gate_count == 5
    assert report.passed_gate_count == 5
    assert report.trace_path_complete is True
    assert report.release_decision == "human_review_ready"


def test_release_readiness_markdown_records_gaps_and_traceability_refs(tmp_path: Path) -> None:
    report = build_release_readiness_report(
        runtime_root=tmp_path / "instance",
        quality_gates=[QualityGateResult(name="pytest", status="pass", evidence="121 passed")],
        trace_path_refs=["SourceRegistryEntry", "RawObservation"],
        known_gaps=["DARS adapter remains loopback-only", "live connectors disabled"],
    )

    markdown = report.to_markdown()

    assert report.overall_status == "not_ready"
    assert report.trace_path_complete is False
    assert "Traceability: HISYS-T-024" in markdown
    assert "DARS adapter remains loopback-only" in markdown
    assert "live connectors disabled" in markdown
    assert "SourceRegistryEntry" in markdown
    assert "RawObservation" in markdown
