"""Tests for the M22 codebase evidence portfolio builder/writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.operations.codebase_evidence_portfolio import (
    CodebaseEvidencePortfolioRequest,
    EvidenceLineRef,
    build_codebase_evidence_portfolio_report,
    write_codebase_evidence_portfolio_report,
)


def _m21_line() -> EvidenceLineRef:
    return EvidenceLineRef(
        line_label="M21",
        artifact_refs=(
            "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
            "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
            "docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md",
        ),
        schema_ids=(
            "hisys.traceability.coverage.v1",
            "hisys.change_impact.v1",
            "hisys.architecture_candidates.v1",
        ),
        quality_gate_refs=(
            "tests/unit/test_traceability_coverage.py",
            "tests/unit/test_change_impact.py",
            "tests/unit/test_architecture_candidates.py",
        ),
        implemented_surface_count=9,
        human_gated_surface_count=2,
    )


def _dars_line() -> EvidenceLineRef:
    return EvidenceLineRef(
        line_label="DARS_PANEL_LOCAL_COMPLETION",
        artifact_refs=(
            "docs/plans/dars-panel-completion-before-codebase-return.md",
            "docs/reports/dars-panel-local-completion-audit.md",
        ),
        schema_ids=("hisys.dars_panel_readiness.v1",),
        quality_gate_refs=(
            "tests/unit/test_dars_critic_panel_runtime.py",
            "tests/unit/test_dars_critic_panel_cli.py",
        ),
        implemented_surface_count=5,
        human_gated_surface_count=0,
    )


def test_build_codebase_evidence_portfolio_aggregates_m21_and_dars(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(_m21_line(), _dars_line()),
        current_head_short="50173ba",
    )

    report = build_codebase_evidence_portfolio_report(request=request)

    assert report.schema_id == "hisys.codebase_evidence_portfolio.v1"
    assert report.date == "20260521"
    assert report.current_head_short == "50173ba"
    assert report.source_lines == ("DARS_PANEL_LOCAL_COMPLETION", "M21")
    assert "hisys.change_impact.v1" in report.schema_ids
    assert "hisys.dars_panel_readiness.v1" in report.schema_ids
    assert (
        "docs/reports/dars-panel-local-completion-audit.md"
        in report.artifact_refs
    )
    assert "tests/unit/test_change_impact.py" in report.quality_gate_refs
    assert report.implemented_surface_count == 14
    assert report.human_gated_surface_count == 2
    assert report.unsafe_refs == ()
    assert report.unsafe_line_labels == ()
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.allowed_actions == "advisory_only"


def test_write_codebase_evidence_portfolio_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(_m21_line(),),
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    refs = write_codebase_evidence_portfolio_report(
        instance_root=instance_root, date="20260521", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/codebase-evidence-portfolio/20260521/portfolio-report.json"
    )
    assert refs["markdown_ref"] == (
        "runtime-boundary/codebase-evidence-portfolio/20260521/portfolio-report.md"
    )
    assert refs["external_call_made"] is False
    assert refs["mutation_performed"] is False
    assert refs["raw_source_content_persisted"] is False
    assert refs["allowed_actions"] == "advisory_only"
    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()
    json_body = json_path.read_text(encoding="utf-8")
    assert "hisys.codebase_evidence_portfolio.v1" in json_body
    md_body = md_path.read_text(encoding="utf-8")
    assert "M21" in md_body


def test_build_portfolio_rejects_unsafe_refs_and_labels(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(
            EvidenceLineRef(
                line_label="M21",
                artifact_refs=(
                    "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
                    "/etc/passwd",
                    "../escape.md",
                ),
                schema_ids=("hisys.traceability.coverage.v1",),
                quality_gate_refs=(
                    "tests/unit/test_traceability_coverage.py",
                    "/absolute/test.py",
                ),
                implemented_surface_count=1,
                human_gated_surface_count=0,
            ),
            EvidenceLineRef(
                line_label="lowercase-not-allowed",
                artifact_refs=("docs/plans/should-not-leak.md",),
            ),
        ),
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    assert "M21" in report.source_lines
    assert "lowercase-not-allowed" not in report.source_lines
    assert "lowercase-not-allowed" in report.unsafe_line_labels
    assert "/etc/passwd" in report.unsafe_refs
    assert "../escape.md" in report.unsafe_refs
    assert "/absolute/test.py" in report.unsafe_refs
    assert "docs/plans/should-not-leak.md" not in report.artifact_refs
    assert (
        "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md"
        in report.artifact_refs
    )
    # When the only valid line has its M21 surface counts retained.
    assert report.implemented_surface_count == 1
    assert report.human_gated_surface_count == 0


def test_build_portfolio_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="2026-05-21",
        line_refs=(),
    )
    with pytest.raises(ValueError):
        build_codebase_evidence_portfolio_report(request=request)


def test_write_codebase_evidence_portfolio_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(_m21_line(),),
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    with pytest.raises(ValueError):
        write_codebase_evidence_portfolio_report(
            instance_root=instance_root, date="2026-05-21", report=report
        )


_FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "codebase-evidence-portfolio"
)


def _load_golden_bundle() -> dict[str, object]:
    return json.loads(
        (_FIXTURE_DIR / "m21_dars_bundle.json").read_text(encoding="utf-8")
    )


def _expected_golden_json() -> str:
    return (_FIXTURE_DIR / "expected" / "portfolio-report.json").read_text(
        encoding="utf-8"
    )


def _expected_golden_markdown() -> str:
    return (_FIXTURE_DIR / "expected" / "portfolio-report.md").read_text(
        encoding="utf-8"
    )


def _load_m23_golden_bundle() -> dict[str, object]:
    return json.loads(
        (_FIXTURE_DIR / "m21_dars_m23_bundle.json").read_text(encoding="utf-8")
    )


def _expected_m23_golden_json() -> str:
    return (
        _FIXTURE_DIR / "expected-m21-dars-m23" / "portfolio-report.json"
    ).read_text(encoding="utf-8")


def _expected_m23_golden_markdown() -> str:
    return (
        _FIXTURE_DIR / "expected-m21-dars-m23" / "portfolio-report.md"
    ).read_text(encoding="utf-8")


def test_codebase_evidence_portfolio_golden_round_trip(tmp_path: Path) -> None:
    bundle = _load_golden_bundle()
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    line_refs = tuple(
        EvidenceLineRef(**raw) for raw in bundle["line_refs"]
    )
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date=bundle["date"],
        line_refs=line_refs,
        current_head_short=bundle["current_head_short"],
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    write_codebase_evidence_portfolio_report(
        instance_root=instance_root, date=bundle["date"], report=report
    )

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle["date"]
        / "portfolio-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle["date"]
        / "portfolio-report.md"
    )
    assert json_path.read_text(encoding="utf-8") == _expected_golden_json()
    assert md_path.read_text(encoding="utf-8") == _expected_golden_markdown()


def test_codebase_evidence_portfolio_accepts_m23_adapter_lines(
    tmp_path: Path,
) -> None:
    bundle = _load_m23_golden_bundle()
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    line_refs = tuple(EvidenceLineRef(**raw) for raw in bundle["line_refs"])
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date=bundle["date"],
        line_refs=line_refs,
        current_head_short=bundle["current_head_short"],
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    write_codebase_evidence_portfolio_report(
        instance_root=instance_root, date=bundle["date"], report=report
    )

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle["date"]
        / "portfolio-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle["date"]
        / "portfolio-report.md"
    )
    assert json_path.read_text(encoding="utf-8") == _expected_m23_golden_json()
    assert md_path.read_text(encoding="utf-8") == _expected_m23_golden_markdown()
    assert "M23_LSP_ADAPTER" in report.source_lines
    assert "M23_OSS_ADAPTER" in report.source_lines
    assert "hisys.lsp_adapter.v1" in report.schema_ids
    assert "hisys.oss_comparison_adapter.v1" in report.schema_ids
    assert (
        "runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.json"
        in report.artifact_refs
    )
    assert (
        "runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.json"
        in report.artifact_refs
    )
    assert "tests/unit/test_lsp_adapter.py" in report.quality_gate_refs
    assert "tests/unit/test_oss_comparison_adapter.py" in report.quality_gate_refs
    assert report.unsafe_refs == ()
    assert report.unsafe_line_labels == ()
    assert report.raw_source_content_persisted is False
    assert report.external_call_made is False
