"""Hisys CLI runtime entry points.

Traceability: HISYS-PKG-ARCH-001 Section 3, HISYS-RUNTIME-DIR-001,
HISYS-INST-INV-001, HISYS-D-015, HISYS-D-016, HISYS-T-001,
HISYS-T-007, HISYS-T-008, HISYS-T-009, HISYS-T-010, HISYS-T-011,
HISYS-T-012, HISYS-T-013, HISYS-T-014, HISYS-T-015, HISYS-T-016,
HISYS-T-017, HISYS-T-018, HISYS-T-019, HISYS-T-020, HISYS-T-021,
HISYS-T-022, HISYS-T-023, HISYS-T-024, HISYS-T-025, HISYS-T-026,
HISYS-T-030, HISYS-T-031, HISYS-T-032.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from .. import __version__
from ..adapters import AgentSystemMockSource, HardwareMockSource, HermesToolMockSource, WebNewsMockSource
from ..adapters.hermes_tool_mock import HermesCollectionInputs
from ..chief_editor import (
    AlertActionPlanRuntime,
    AlertApprovalTransitionRuntime,
    AlertConnectorRuntime,
    ChiefEditorPolicy,
    ChiefEditorRuntime,
    create_chief_editor_product,
)
from ..agents import DarsRuntime
from ..config import InstanceRoot, load_source_registry
from ..connectors import DoiMetadataConnector, FixturePublisherConnector, PdfCandidatePlanner, SourceConnectorDispatchGate, load_source_connector_registry
from ..core.ids import IdNamespace, make_id
from ..editor import EditorialRuntime, FixtureMemoDrafter, MemoDraftReport, MemoReviewReport, MemoReviewRuntime
from ..extraction import ExtractionReport, ExtractionRuntime, FixtureSignalExtractor
from ..integrations import HermesBoundaryWriter
from ..investigator import (
    CollectionReport,
    InvestigatorRuntime,
    ResearchTask,
    create_research_agent,
    merge_evidence_packages,
)
from ..investigator.agent_config import (
    AgentConnectorSafetyError,
    load_investigator_agent_config,
    select_configured_agent_plan,
)
from ..registry import SourceRegistry
from ..schemas import (
    AlternativeDecisionSet,
    CandidateRecord,
    DomainEvidencePackage,
    DomainInvestigationRequest,
    DomainInvestigationResult,
    HisysToolResult,
    InvestigationDataPackage,
    ExtractedSignal,
    PerspectiveProfile,
    RawObservation,
    SourceRegistryEntry,
    ZettelMemo,
)


@dataclass(frozen=True)
class InvestigationMemoReport:
    """Template-driven Investigator memo report.

    Traceability: HISYS-INST-INV-001, HISYS-FR-INV-001..006,
    HISYS-FR-MEM-001..005, HISYS-TPL-RESEARCH-SEARCH-001, HISYS-T-026.
    """

    topic: str
    goal: str
    template_id: str
    source_refs: list[str]
    observation_refs: list[str]
    signal_refs: list[str]
    memo_refs: list[str]
    memo_paths: list[str]
    skipped_source_ids: list[str]
    policy_refs: list[str]
    research_task_refs: list[str] | None = None
    evidence_package_refs: list[str] | None = None
    agent_ids: list[str] | None = None
    limitations: list[str] | None = None
    open_questions: list[str] | None = None
    guideline_profile_id: str = "general_investigation"
    agent_plan_source: str = "legacy"
    disabled_optional_agent_refs: list[str] | None = None
    blocked_agent_refs: list[str] | None = None


@dataclass(frozen=True)
class GuidelineProfile:
    """Purpose-specific memo guideline selected before synthesis.

    Traceability: HISYS-T-030, HISYS-INST-INV-001, HISYS-FR-MEM-001..005.
    """

    profile_id: str
    title: str
    purpose: str
    required_sections: list[str]
    decision_frame: str
    safety_note: str | None = None


def _record_json(record: object) -> str:
    if hasattr(record, "model_dump"):
        data = record.model_dump(mode="json")  # type: ignore[attr-defined]
    else:
        data = asdict(record)  # type: ignore[arg-type]
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hisys", description="Hisys runtime CLI.")
    parser.add_argument("--version", action="version", version=f"hisys {__version__}")
    sub = parser.add_subparsers(dest="command")

    validate = sub.add_parser("validate-config", help="validate a Hisys runtime instance config")
    validate.add_argument("--instance", required=True, help="runtime instance root containing config/")

    collect = sub.add_parser("collect", help="run fixture-backed Investigator collection")
    collect.add_argument("--instance", required=True, help="runtime instance root for outputs")
    collect.add_argument(
        "--config-from",
        help="optional runtime instance root to read config from; outputs still go to --instance",
    )
    collect.add_argument(
        "--source",
        dest="sources",
        action="append",
        required=True,
        help="source_id to collect; repeat for multiple sources",
    )
    collect.add_argument("--date", required=True, help="YYYYMMDD output partition")
    collect.add_argument("--collector-id", default="investigator-cli", help="collector actor id")

    investigate_memo = sub.add_parser(
        "investigate-memo",
        help="research a topic from fixture sources and write a template-based memo",
    )
    investigate_memo.add_argument("--instance", required=True, help="runtime instance root for outputs")
    investigate_memo.add_argument(
        "--config-from",
        required=True,
        help="runtime instance root containing source registry/template config",
    )
    investigate_memo.add_argument(
        "--source",
        dest="sources",
        action="append",
        required=True,
        help="source_id to investigate; repeat for multiple sources",
    )
    investigate_memo.add_argument("--date", required=True, help="YYYYMMDD output partition")
    investigate_memo.add_argument("--topic", required=True, help="research topic for the memo template")
    investigate_memo.add_argument("--goal", required=True, help="research goal for the memo template")
    investigate_memo.add_argument("--perspective", required=True, help="PerspectiveProfile id for memo framing")
    investigate_memo.add_argument(
        "--template-id",
        default="research-topic-search",
        help="memo template id; default uses examples/instance/templates/collection/research-topic-search-template.md",
    )
    investigate_memo.add_argument("--collector-id", default="investigator-cli", help="collector actor id")
    investigate_memo.add_argument(
        "--purpose",
        choices=["auto", "general_investigation", "research_idea_discovery", "investment_decision_support"],
        default="auto",
        help="purpose guideline profile; auto selects from topic and goal",
    )
    investigate_memo.add_argument(
        "--agent",
        dest="agents",
        action="append",
        default=[],
        help="research agent type to dispatch; repeat for multiple agents (fixture, fixture_contradiction)",
    )

    investigate_domain = sub.add_parser(
        "investigate-domain",
        help="run local domain-general Hisys investigation from a JSON request",
    )
    investigate_domain.add_argument("--instance", required=True, help="runtime instance root for outputs")
    investigate_domain.add_argument("--request", required=True, help="DomainInvestigationRequest JSON path")
    investigate_domain.add_argument("--date", required=True, help="YYYYMMDD output partition")

    plan_sources = sub.add_parser(
        "plan-source-connectors",
        help="dry-run plan governed source connectors for a domain investigation request",
    )
    plan_sources.add_argument("--instance", required=True, help="runtime instance root for outputs")
    plan_sources.add_argument("--request", required=True, help="DomainInvestigationRequest JSON path")
    plan_sources.add_argument("--config", required=True, help="source-connectors.yaml path")
    plan_sources.add_argument("--date", required=True, help="YYYYMMDD output partition")

    smoke_source = sub.add_parser(
        "smoke-source-connector",
        help="manual/dry-run smoke boundary for one governed source connector",
    )
    smoke_source.add_argument("--instance", required=True, help="runtime instance root for outputs")
    smoke_source.add_argument("--config", required=True, help="source-connectors.yaml path")
    smoke_source.add_argument("--date", required=True, help="YYYYMMDD output partition")
    smoke_source.add_argument("--request-id", required=True, help="request id for runtime-boundary evidence")
    smoke_source.add_argument("--connector-id", required=True, help="source connector id to smoke")
    smoke_source.add_argument("--doi", help="DOI to retrieve for DOI metadata smoke")
    smoke_source.add_argument("--source-url", help="source URL for PDF smoke gating")
    smoke_source.add_argument(
        "--license-signal",
        choices=["open_access", "closed", "unknown", "not_applicable"],
        default="unknown",
        help="license/open-access signal required for PDF smoke gating",
    )
    smoke_source.add_argument("--approval-ref", help="manual approval ref required for live smoke")
    smoke_source.add_argument("--dry-run", action="store_true", help="write blocked/dry-run evidence only; no external call")

    plan_pdf = sub.add_parser(
        "plan-pdf-candidates",
        help="derive OA PDF candidate plans from DOI metadata without fetching PDF bytes",
    )
    plan_pdf.add_argument("--instance", required=True, help="runtime instance root for outputs")
    plan_pdf.add_argument("--metadata", required=True, help="DOI metadata JSON path")
    plan_pdf.add_argument("--date", required=True, help="YYYYMMDD output partition")
    plan_pdf.add_argument("--request-id", required=True, help="request id for candidate plan")
    plan_pdf.add_argument("--metadata-access-ref", required=True, help="runtime ref to DOI metadata source access record")
    plan_pdf.add_argument(
        "--metadata-evidence-ref",
        action="append",
        default=[],
        help="runtime ref to DOI metadata evidence; repeat for multiple refs",
    )

    extract = sub.add_parser("extract", help="run fixture-backed extraction over collected observations")
    extract.add_argument("--instance", required=True, help="runtime instance root containing data/raw-observations/")
    extract.add_argument("--date", required=True, help="YYYYMMDD input/output partition")
    extract.add_argument("--producer-id", default="extractor-cli", help="extraction actor id")

    draft = sub.add_parser("draft-memo", help="draft runtime-local ZettelMemo records from extracted signals")
    draft.add_argument("--instance", required=True, help="runtime instance root containing extracted signals")
    draft.add_argument("--date", required=True, help="YYYYMMDD input/output partition")
    draft.add_argument("--perspective", required=True, help="PerspectiveProfile ID to apply")
    draft.add_argument("--producer-id", default="associate-editor-cli", help="memo drafting actor id")

    review = sub.add_parser("review-memos", help="run fixture duplicate/conflict review over memo drafts")
    review.add_argument("--instance", required=True, help="runtime instance root containing memo drafts")
    review.add_argument("--date", required=True, help="YYYYMMDD memo draft partition")
    review.add_argument("--producer-id", default="memo-review-cli", help="memo review actor id")

    decide = sub.add_parser("decide-alerts", help="run fixture Chief Editor alert decisions")
    decide.add_argument("--instance", required=True, help="runtime instance root containing memo review outputs")
    decide.add_argument("--date", required=True, help="YYYYMMDD memo review partition")
    decide.add_argument("--producer-id", default="chief-editor-cli", help="Chief Editor actor id")
    decide.add_argument(
        "--conflict-severity",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="fixture severity assigned to conflict alert candidates",
    )
    decide.add_argument(
        "--target-channel",
        help="dry-run target channel metadata; omitted means config/default selection",
    )
    decide.add_argument(
        "--product-type",
        choices=["analysis_only", "alert_delivery_dry_run"],
        help="Chief Editor product selection; defaults to config/chief-editor.yaml or alert_delivery_dry_run",
    )
    plan = sub.add_parser("plan-alert-actions", help="write fixture dry-run alert action plans")
    plan.add_argument("--instance", required=True, help="runtime instance root containing alert decisions")
    plan.add_argument("--date", required=True, help="YYYYMMDD alert decision partition")
    plan.add_argument("--producer-id", default="alert-action-plan-cli", help="action planner actor id")
    review_approval = sub.add_parser(
        "review-alert-approval",
        help="apply fixture approval/rejection transition to a local alert decision",
    )
    review_approval.add_argument("--instance", required=True, help="runtime instance root containing alert decisions")
    review_approval.add_argument("--date", required=True, help="YYYYMMDD alert decision partition")
    review_approval.add_argument("--alert-id", required=True, help="AlertDecisionRecord id to transition")
    review_approval.add_argument("--outcome", choices=["approved", "rejected"], required=True)
    review_approval.add_argument("--rationale", required=True, help="fixture human approval rationale")
    review_approval.add_argument("--reviewer-id", default="chief-editor-approval-cli", help="approval reviewer actor id")
    execute = sub.add_parser(
        "execute-alert-actions",
        help="validate dry-run alert action plans against disabled fixture connector",
    )
    execute.add_argument("--instance", required=True, help="runtime instance root containing action plans")
    execute.add_argument("--date", required=True, help="YYYYMMDD action-plan partition")
    execute.add_argument("--connector-id", default="disabled-fixture-connector", help="disabled fixture connector id")
    dars = sub.add_parser(
        "request-dars-critique",
        help="record runtime-local advisory DARS handoff loopback placeholder",
    )
    dars.add_argument("--instance", required=True, help="runtime instance root containing connector executions")
    dars.add_argument("--date", required=True, help="YYYYMMDD connector-execution partition")
    dars.add_argument("--source-execution-id", required=True, help="connector execution id used as handoff evidence")
    dars.add_argument("--critique-text", help="optional fixture critique text; omitted means loopback placeholder until DARS exists")
    dars.add_argument("--producer-id", default="dars-fixture-cli", help="DARS fixture producer id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "validate-config":
        return _cmd_validate_config(Path(args.instance))
    if args.command == "collect":
        config_root = Path(args.config_from) if args.config_from else Path(args.instance)
        return _cmd_collect(
            output_root=Path(args.instance),
            config_root=config_root,
            source_ids=args.sources,
            yyyymmdd=args.date,
            collector_id=args.collector_id,
        )
    if args.command == "investigate-memo":
        return _cmd_investigate_memo(
            output_root=Path(args.instance),
            config_root=Path(args.config_from),
            source_ids=args.sources,
            yyyymmdd=args.date,
            topic=args.topic,
            goal=args.goal,
            perspective_id=args.perspective,
            template_id=args.template_id,
            collector_id=args.collector_id,
            purpose=args.purpose,
            agent_types=args.agents,
        )
    if args.command == "investigate-domain":
        return _cmd_investigate_domain(
            instance_root=Path(args.instance),
            request_path=Path(args.request),
            yyyymmdd=args.date,
        )
    if args.command == "plan-source-connectors":
        return _cmd_plan_source_connectors(
            instance_root=Path(args.instance),
            request_path=Path(args.request),
            config_path=Path(args.config),
            yyyymmdd=args.date,
        )
    if args.command == "smoke-source-connector":
        return _cmd_smoke_source_connector(
            instance_root=Path(args.instance),
            config_path=Path(args.config),
            yyyymmdd=args.date,
            request_id=args.request_id,
            connector_id=args.connector_id,
            doi=args.doi,
            source_url=args.source_url,
            license_signal=args.license_signal,
            approval_ref=args.approval_ref,
            dry_run=args.dry_run,
        )
    if args.command == "plan-pdf-candidates":
        return _cmd_plan_pdf_candidates(
            instance_root=Path(args.instance),
            metadata_path=Path(args.metadata),
            yyyymmdd=args.date,
            request_id=args.request_id,
            metadata_access_ref=args.metadata_access_ref,
            metadata_evidence_refs=args.metadata_evidence_ref,
        )
    if args.command == "extract":
        return _cmd_extract(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            producer_id=args.producer_id,
        )
    if args.command == "draft-memo":
        return _cmd_draft_memo(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            perspective_id=args.perspective,
            producer_id=args.producer_id,
        )
    if args.command == "review-memos":
        return _cmd_review_memos(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            producer_id=args.producer_id,
        )
    if args.command == "decide-alerts":
        return _cmd_decide_alerts(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            producer_id=args.producer_id,
            conflict_severity=args.conflict_severity,
            target_channel=args.target_channel,
            product_type=args.product_type,
        )
    if args.command == "plan-alert-actions":
        return _cmd_plan_alert_actions(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            producer_id=args.producer_id,
        )
    if args.command == "review-alert-approval":
        return _cmd_review_alert_approval(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            alert_id=args.alert_id,
            outcome=args.outcome,
            rationale=args.rationale,
            reviewer_id=args.reviewer_id,
        )
    if args.command == "execute-alert-actions":
        return _cmd_execute_alert_actions(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            connector_id=args.connector_id,
        )
    if args.command == "request-dars-critique":
        return _cmd_request_dars_critique(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            source_execution_id=args.source_execution_id,
            critique_text=args.critique_text,
            producer_id=args.producer_id,
        )
    parser.error(f"unknown command: {args.command}")
    return 2


def _cmd_validate_config(instance_root: Path) -> int:
    registry = load_source_registry(InstanceRoot(instance_root))
    source_ids = sorted(registry.entries)
    print(f"config valid: {instance_root}")
    print(f"sources: {len(source_ids)}")
    for source_id in source_ids:
        entry = registry.entries[source_id]
        print(f"- {source_id} [{entry.source_type}] {entry.lifecycle_state}")
    return 0


def _cmd_plan_source_connectors(instance_root: Path, request_path: Path, config_path: Path, yyyymmdd: str) -> int:
    """Write a dry-run source connector plan without executing adapters."""

    instance = InstanceRoot(instance_root)
    request = DomainInvestigationRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
    registry = load_source_connector_registry(config_path)
    planned = _select_source_connectors_for_request(request, registry.connectors.keys())
    disabled = [connector_id for connector_id in planned if not registry.connectors[connector_id].enabled]
    blocked = [
        {
            "connector_id": connector_id,
            "reason_code": "connector_disabled",
            "reason": "Connector is planned for future evidence collection but disabled in the resolved registry.",
        }
        for connector_id in disabled
    ]
    plan = {
        "schema_id": "hisys.source_connector.plan",
        "schema_version": "0.1.0",
        "request_id": request.request_id,
        "domain": request.domain,
        "objective": request.objective,
        "planned_connectors": planned,
        "disabled_connectors": disabled,
        "blocked_connectors": blocked,
        "external_call_made": False,
        "mutation_performed": False,
        "config_ref": str(config_path),
    }
    plan_dir = instance.runtime_boundary_dir / "source-connectors" / yyyymmdd
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_artifact = plan_dir / f"connector-plan-{request.request_id}.json"
    plan_artifact.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan_md = plan_dir / f"connector-plan-{request.request_id}.md"
    plan_md.write_text(_format_source_connector_plan_markdown(plan), encoding="utf-8")

    report = {
        "schema_id": "hisys.source_connector.plan_report",
        "schema_version": "0.1.0",
        "request_id": request.request_id,
        "domain": request.domain,
        "plan_ref": str(plan_artifact.relative_to(instance.root)),
        "planned_connector_count": len(planned),
        "disabled_connector_count": len(disabled),
        "external_call_made": False,
        "mutation_performed": False,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "source-connector-plan-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "source-connector-plan-report.md"
    report_md.write_text(_format_source_connector_plan_report_markdown(report), encoding="utf-8")
    print(f"source connector plan: report={report_artifact}")
    print(f"planned_connectors: {len(planned)}")
    print("external_call_made: false")
    return 0


def _cmd_smoke_source_connector(
    *,
    instance_root: Path,
    config_path: Path,
    yyyymmdd: str,
    request_id: str,
    connector_id: str,
    doi: str | None,
    source_url: str | None,
    license_signal: str,
    approval_ref: str | None,
    dry_run: bool,
) -> int:
    """Write dry-run/manual smoke source connector evidence."""

    instance = InstanceRoot(instance_root)
    registry = load_source_connector_registry(config_path)
    gate = SourceConnectorDispatchGate(instance=instance)
    connector = registry.connectors[connector_id]
    env_name = connector.manual_smoke_env_var or "HISYS_ALLOW_LIVE_SMOKE"
    requested_domain = _source_connector_requested_domain(connector_id=connector_id, source_url=source_url)
    dispatch_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/connector-dispatch-{request_id}-{connector_id}.json"
    if connector_id == "open_access_pdf_fetch" and license_signal != "open_access":
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="dry_run" if dry_run else "manual_live",
            status="blocked",
            reason_code="pdf_license_not_open_access",
            dispatch_ref=None,
            source_evidence_refs=[],
            external_call_made=False,
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        print("source connector smoke: status=blocked reason=pdf_license_not_open_access")
        return 0 if dry_run else 2
    if dry_run:
        decision = gate.evaluate(
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            registry=registry,
            connector_id=connector_id,
            approval_ref=None,
            requested_domain=requested_domain,
            requested_actions=["read"],
        )
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="dry_run",
            status="blocked",
            reason_code=decision.reason_code,
            dispatch_ref=dispatch_ref,
            source_evidence_refs=[],
            external_call_made=False,
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        print(f"source connector smoke: status=blocked report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'source-connector-smoke-report.json'}")
        return 0
    if os.environ.get(env_name) != "1":
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="manual_live",
            status="blocked",
            reason_code="manual_smoke_env_missing",
            dispatch_ref=None,
            source_evidence_refs=[],
            external_call_made=False,
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        print("source connector smoke: status=blocked reason=manual_smoke_env_missing")
        return 2
    decision = gate.evaluate(
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        registry=registry,
        connector_id=connector_id,
        approval_ref=approval_ref,
        requested_domain=requested_domain,
        requested_actions=["read"],
    )
    if decision.decision != "allowed":
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="manual_live",
            status="blocked",
            reason_code=decision.reason_code,
            dispatch_ref=dispatch_ref,
            source_evidence_refs=[],
            external_call_made=False,
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        return 2
    if connector_id == "open_access_pdf_fetch":
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="manual_live",
            status="blocked",
            reason_code="manual_pdf_smoke_not_implemented",
            dispatch_ref=dispatch_ref,
            source_evidence_refs=[],
            external_call_made=False,
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        print("source connector smoke: status=blocked reason=manual_pdf_smoke_not_implemented")
        return 2
    if connector_id != "doi_metadata_search":
        raise ValueError("Live-C/D supports only doi_metadata_search and open_access_pdf_fetch")
    if not doi:
        raise ValueError("doi is required for doi_metadata_search")
    package = DoiMetadataConnector().collect(request_id=request_id, doi=doi, output_root=instance.root, yyyymmdd=yyyymmdd)
    report = _source_connector_smoke_report(
        request_id=request_id,
        connector_id=connector_id,
        mode="manual_live",
        status="completed",
        reason_code="manual_smoke_completed",
        dispatch_ref=dispatch_ref,
        source_evidence_refs=[package.access_ref, package.evidence_ref],
        external_call_made=True,
    )
    _write_source_connector_smoke_report(instance, yyyymmdd, report)
    print(f"source connector smoke: status=completed report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'source-connector-smoke-report.json'}")
    return 0


def _source_connector_requested_domain(*, connector_id: str, source_url: str | None) -> str:
    if connector_id == "doi_metadata_search":
        return "api.crossref.org"
    if source_url:
        return urlparse(source_url).netloc or "unknown"
    return "unknown"


def _source_connector_smoke_report(
    *,
    request_id: str,
    connector_id: str,
    mode: str,
    status: str,
    reason_code: str | None,
    dispatch_ref: str | None,
    source_evidence_refs: list[str],
    external_call_made: bool,
) -> dict[str, object]:
    return {
        "schema_id": "hisys.source_connector.smoke_report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "connector_id": connector_id,
        "mode": mode,
        "status": status,
        "reason_code": reason_code,
        "dispatch_ref": dispatch_ref,
        "source_evidence_refs": source_evidence_refs,
        "external_call_made": external_call_made,
        "mutation_performed": False,
    }


def _write_source_connector_smoke_report(instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "source-connector-smoke-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "source-connector-smoke-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Source Connector Smoke Report",
                "",
                f"- request_id: `{report['request_id']}`",
                f"- connector_id: `{report['connector_id']}`",
                f"- status: `{report['status']}`",
                f"- external_call_made: `{report['external_call_made']}`",
                f"- mutation_performed: `{report['mutation_performed']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_artifact


def _cmd_plan_pdf_candidates(
    *,
    instance_root: Path,
    metadata_path: Path,
    yyyymmdd: str,
    request_id: str,
    metadata_access_ref: str,
    metadata_evidence_refs: list[str],
) -> int:
    instance = InstanceRoot(instance_root)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    plan = PdfCandidatePlanner().plan(
        request_id=request_id,
        metadata=metadata,
        metadata_access_ref=metadata_access_ref,
        metadata_evidence_refs=metadata_evidence_refs,
        output_root=instance.root,
        yyyymmdd=yyyymmdd,
    )
    report = {
        "schema_id": "hisys.pdf_candidate.plan_report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "plan_ref": plan.plan_ref,
        "candidate_count": len(plan.candidates),
        "candidate_plan_only": True,
        "pdf_downloaded": False,
        "external_call_made": False,
        "mutation_performed": False,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "pdf-candidate-plan-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "pdf-candidate-plan-report.md"
    report_md.write_text(
        "\n".join(
            [
                f"# PDF candidate plan report {request_id}",
                "",
                f"- plan_ref: `{plan.plan_ref}`",
                f"- candidate_count: {len(plan.candidates)}",
                "- candidate_plan_only: true",
                "- pdf_downloaded: false",
                "- external_call_made: false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"pdf candidate plan: report={report_artifact}")
    print("pdf_downloaded: false")
    print("external_call_made: false")
    return 0


def _select_source_connectors_for_request(request: DomainInvestigationRequest, connector_ids: Iterable[str]) -> list[str]:
    ids = set(connector_ids)
    if request.domain == "research":
        preferred = ["publisher_web_search", "doi_metadata_search", "open_access_pdf_fetch", "arxiv_metadata_search"]
        return [connector_id for connector_id in preferred if connector_id in ids]
    return [connector_id for connector_id in ["local_pdf_reader"] if connector_id in ids]


def _format_source_connector_plan_markdown(plan: dict) -> str:
    return "\n".join(
        [
            f"# Source connector plan {plan['request_id']}",
            "",
            f"- domain: {plan['domain']}",
            f"- external_call_made: {str(plan['external_call_made']).lower()}",
            f"- mutation_performed: {str(plan['mutation_performed']).lower()}",
            "",
            "## Planned connectors",
            *[f"- {connector_id}" for connector_id in plan["planned_connectors"]],
            "",
        ]
    )


def _format_source_connector_plan_report_markdown(report: dict) -> str:
    return "\n".join(
        [
            f"# Source connector plan report {report['request_id']}",
            "",
            f"- plan_ref: `{report['plan_ref']}`",
            f"- planned_connector_count: {report['planned_connector_count']}",
            f"- external_call_made: {str(report['external_call_made']).lower()}",
            "",
        ]
    )


def _cmd_investigate_domain(instance_root: Path, request_path: Path, yyyymmdd: str) -> int:
    """Persist the local MVP boundary for a domain investigation request."""

    instance = InstanceRoot(instance_root)
    request = DomainInvestigationRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
    boundary_dir = instance.root / "runtime-boundary" / "domain-investigation" / request.domain / yyyymmdd
    boundary_dir.mkdir(parents=True, exist_ok=True)

    request_artifact = boundary_dir / f"hisys-tool-request-{request.request_id}.json"
    request_artifact.write_text(_record_json(request), encoding="utf-8")
    request_markdown = boundary_dir / f"hisys-tool-request-{request.request_id}.md"
    request_markdown.write_text(_format_domain_request_markdown(request), encoding="utf-8")

    domain_result = _build_research_domain_result(request, instance, boundary_dir, yyyymmdd)
    if domain_result is not None:
        domain_result = _write_dars_fixture_for_domain_result(
            instance=instance,
            request=request,
            domain_result=domain_result,
            boundary_dir=boundary_dir,
            yyyymmdd=yyyymmdd,
        )
        domain_result = _write_chief_editor_research_review(
            instance=instance,
            request=request,
            domain_result=domain_result,
            yyyymmdd=yyyymmdd,
        )
        data_artifact = boundary_dir / f"investigation-data-{domain_result.investigation_data.investigation_id}.json"
        data_artifact.write_text(_record_json(domain_result.investigation_data), encoding="utf-8")
        alternatives_artifact = boundary_dir / f"alternative-decision-set-{domain_result.alternative_decision_set.alternative_set_id}.json"
        alternatives_artifact.write_text(_record_json(domain_result.alternative_decision_set), encoding="utf-8")
        domain_result_artifact = boundary_dir / f"domain-investigation-result-{domain_result.result_id}.json"
        domain_result.runtime_boundary_refs.extend(
            [
                str(data_artifact.relative_to(instance.root)),
                str(alternatives_artifact.relative_to(instance.root)),
                str(domain_result_artifact.relative_to(instance.root)),
            ]
        )
        domain_result_artifact.write_text(_record_json(domain_result), encoding="utf-8")
        tool_result = HisysToolResult.from_domain_result(domain_result)
    else:
        result_ref = str((boundary_dir / f"hisys-tool-result-{request.request_id}.json").relative_to(instance.root))
        tool_result = HisysToolResult(
            status="needs_more_evidence",
            domain=request.domain,
            summary=(
                "Domain investigation request accepted and preserved; domain adapter execution "
                "is pending in the next MVP increment."
            ),
            recommended_alternative_id=None,
            requires_human_review=True,
            external_call_made=False,
            mutation_performed=False,
            runtime_boundary_refs=[
                str(request_artifact.relative_to(instance.root)),
                str(request_markdown.relative_to(instance.root)),
                result_ref,
            ],
            quality_gate="needs_more_evidence",
        )
    result_artifact = boundary_dir / f"hisys-tool-result-{request.request_id}.json"
    result_ref = str(result_artifact.relative_to(instance.root))
    if result_ref not in tool_result.runtime_boundary_refs:
        tool_result.runtime_boundary_refs.append(result_ref)
    result_artifact.write_text(_record_json(tool_result), encoding="utf-8")
    result_markdown = boundary_dir / f"hisys-tool-result-{request.request_id}.md"
    result_markdown.write_text(_format_domain_tool_result_markdown(request, tool_result), encoding="utf-8")

    report_path = _write_domain_investigation_report(
        instance=instance,
        request=request,
        tool_result=tool_result,
        tool_result_ref=str(result_artifact.relative_to(instance.root)),
        yyyymmdd=yyyymmdd,
    )
    print(f"domain investigation run: report={report_path}")
    print(f"domain: {request.domain}")
    print(f"status: {tool_result.status}")
    print(f"tool_result: {result_artifact}")
    return 0


def _build_research_domain_result(
    request: DomainInvestigationRequest,
    instance: InstanceRoot,
    boundary_dir: Path,
    yyyymmdd: str,
) -> DomainInvestigationResult | None:
    """Build the MVP deterministic research adapter result for research-gap requests."""

    objective = request.objective.lower()
    if request.domain != "research" or not {"gap", "formalism"}.issubset(set(objective.split()) | {"formalism"}):
        if request.domain == "research" and "formalism" in objective and "gap" in objective:
            pass
        else:
            return None

    source_refs = [source.source_id for source in request.sources]
    connector_package = FixturePublisherConnector().collect(
        request_id=request.request_id,
        fixture_path=Path("examples/instance/harness/fixtures/web/publisher-formalism-page.html"),
        output_root=instance.root,
        yyyymmdd=yyyymmdd,
    )
    connector_refs = [connector_package.access_ref, connector_package.evidence_ref]
    evidence = DomainEvidencePackage(
        package_id=f"DEPKG-{request.request_id}-FORMALISM-GAP",
        domain="research",
        evidence_type="research_gap_matrix",
        summary=(
            "Dynamic Structure DEVS provides executable topology-changing simulation semantics; "
            "graph rewriting provides local structural transformation rules; agent-based modeling "
            "provides decentralized interaction and emergence. The gap is a unified formalism for "
            "self-organizing structure that jointly models local interaction, feedback, topology/behavior "
            "co-evolution, executable semantics, and analyzable structural constraints."
        ),
        evidence_refs=["fixture:formalism_gap_analysis", "fixture:formalism_comparison", *connector_refs],
        source_refs=source_refs,
        claims=[
            "DSDEVS, graph rewriting, and ABM cover complementary but separated formalism capabilities.",
            "Self-organizing structure needs topology change as first-class model state plus local rewrite/adaptation rules.",
        ],
        limitations=["MVP uses fixture-local evidence only; publisher-source validation remains required."],
        open_questions=[
            "Which structural rewrite constraints preserve DEVS execution semantics?",
            "Which evaluation scenario best demonstrates topology/behavior co-evolution?",
        ],
    )
    data_package = InvestigationDataPackage(
        investigation_id=f"INV-{request.request_id}",
        request_id=request.request_id,
        domain="research",
        objective=request.objective,
        evidence_packages=[evidence],
        source_governance_refs=[
            str((boundary_dir / f"hisys-tool-request-{request.request_id}.json").relative_to(instance.root)),
            *connector_refs,
        ],
    )
    candidate_id = f"CAND-{request.request_id}-SOS-DSDEVS"
    candidate = CandidateRecord(
        candidate_id=candidate_id,
        candidate_type="research_direction",
        claim="Self-organizing Dynamic Structure DEVS with graph-rewrite structural transitions.",
        evidence_refs=[evidence.package_id],
        value="Unifies executable topology change with local structure rewrite and emergence-oriented adaptation semantics.",
        costs=["Requires formal semantics and scenario validation work."],
        risks=["Risk of overclaiming novelty before publisher-source comparison."],
        uncertainties=["Proof obligations and readability tradeoffs remain open."],
        next_increment="Validate against DSDEVS, graph transformation, and ABM literature sources.",
    )
    alternatives = AlternativeDecisionSet(
        alternative_set_id=f"ALTSET-{request.request_id}",
        request_id=request.request_id,
        candidates=[candidate],
        baseline_option="request_more_publisher_evidence",
        recommended_candidate_id=candidate_id,
    )
    return DomainInvestigationResult(
        result_id=f"DRESULT-{request.request_id}",
        request_id=request.request_id,
        domain="research",
        investigation_data=data_package,
        alternative_decision_set=alternatives,
        recommendation_summary=(
            "Recommend developing Self-organizing Dynamic Structure DEVS with graph-rewrite "
            "structural transitions as a research direction, conditioned on publisher-source validation."
        ),
        runtime_boundary_refs=[
            str((boundary_dir / f"hisys-tool-request-{request.request_id}.json").relative_to(instance.root)),
        ],
        quality_gate="passed",
        requires_human_review=True,
        external_call_made=False,
        mutation_performed=False,
    )


def _write_dars_fixture_for_domain_result(
    *,
    instance: InstanceRoot,
    request: DomainInvestigationRequest,
    domain_result: DomainInvestigationResult,
    boundary_dir: Path,
    yyyymmdd: str,
) -> DomainInvestigationResult:
    """Write local advisory-only DARS critique artifacts for the domain MVP."""

    dars_request_id = f"DARSREQ-{request.request_id}"
    dars_response_id = f"DARSRESP-{request.request_id}"
    handoff_id = f"DARSHANDOFF-{request.request_id}"
    critique_id = f"DARSCRIT-{request.request_id}"
    trace_id = f"DARSTRACE-{dars_request_id}"
    dars_dir = instance.runtime_boundary_dir / "dars" / yyyymmdd
    dars_dir.mkdir(parents=True, exist_ok=True)
    domain_result_ref = str(
        (boundary_dir / f"domain-investigation-result-{domain_result.result_id}.json").relative_to(instance.root)
    )
    evidence_ref = domain_result.investigation_data.evidence_packages[0].package_id
    connector_evidence_refs = [
        ref
        for ref in domain_result.investigation_data.evidence_packages[0].evidence_refs
        if ref.startswith("runtime-boundary/source-connectors/")
    ]
    candidate_id = domain_result.alternative_decision_set.recommended_candidate_id or "candidate-not-selected"

    dars_request = {
        "schema_id": "hisys.dars.request",
        "schema_version": "0.1.0",
        "request_id": dars_request_id,
        "handoff_id": handoff_id,
        "created_at": f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}T00:00:00Z",
        "contract": {
            "output_schema_id": "hisys.dars.critique",
            "output_schema_version": "0.1.0",
            "allowed_actions": "advisory_only",
            "external_side_effects_allowed": False,
            "mutation_allowed": False,
            "requires_structured_output": True,
        },
        "prompt_bundle_ref": {
            "prompt_bundle_id": "pb-dars-logical-conservative-devil",
            "prompt_bundle_version": "0.1.0",
            "registry_backend": "file",
            "tenant_scope": "sysailab-default",
            "status": "approved",
            "sha256": "0" * 64,
        },
        "role": {
            "role_id": "logical_conservative_devil",
            "kind": "devil_advocate",
            "profession": "research_gap_reviewer",
            "persona": "conservative_critic",
            "knowledge_scope": ["formal_methods", "self_organization", "evidence_quality"],
            "stance": "skeptical_but_constructive",
            "strictness": "high",
            "creativity": "low",
            "verbosity": "concise_structured",
            "critique_dimensions": ["unsupported_claims", "novelty_overclaim", "validation_gap"],
            "prompt": {
                "objective": "Critique the recommended research direction without executing actions.",
                "focus": request.user_focus,
            },
        },
        "sampling": {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 2000},
        "decision_process": {
            "mode": "progressive_adversarial",
            "objective": "improve_research_recommendation",
            "blocking_policy": "advisory_only",
            "round_index": 1,
            "max_rounds": request.constraints.max_rounds,
            "stop_condition": "no_critical_unresolved_findings",
        },
        "rubric_refs": [
            {
                "rubric_id": "research-gap-logical-devil",
                "rubric_version": "0.1.0",
                "artifact_ref": "harness/rubrics/research/research-gap-v0.1.0.json",
                "sha256": "1" * 64,
                "applies_to_roles": ["logical_conservative_devil"],
            }
        ],
        "critic_panel": [
            {
                "role_id": "logical_conservative_devil",
                "profession": "research_gap_reviewer",
                "persona": "conservative_critic",
                "knowledge_scope": ["formal_methods", "evidence_quality"],
            }
        ],
        "handoff": {
            "handoff_type": "evidence_gap_review",
            "requester": "hisys_domain_investigator",
            "task": "Review the formalism research-gap alternative set.",
            "context_summary": domain_result.recommendation_summary,
            "expected_output": "DarsCritiqueRecord",
            "due_condition": None,
        },
        "record_refs": {
            "sources": [source.source_id for source in request.sources],
            "observations": [],
            "signals": [],
            "memos": [domain_result_ref],
            "alerts": [],
            "handoffs": [handoff_id],
            "requirements": ["HISYS-DARS-CONTRACT-001", "HISYS-T-024"],
            "runtime_boundary": [domain_result_ref, *connector_evidence_refs],
        },
        "evidence": {
            "bundles": [
                {
                    "evidence_ref": evidence_ref,
                    "artifact_ref": f"runtime-boundary/domain-investigation/{request.domain}/{yyyymmdd}/investigation-data-{domain_result.investigation_data.investigation_id}.json",
                    "sha256": "2" * 64,
                    "summary": domain_result.investigation_data.evidence_packages[0].summary,
                    "relevance": "primary",
                }
            ],
            "limitations": domain_result.investigation_data.evidence_packages[0].limitations,
        },
        "constraints": {
            "requirement_refs": ["HISYS-DARS-CONTRACT-001", "HISYS-FR-INV-006"],
            "policy_refs": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
            "prohibited_actions": ["external_call", "file_write", "alert_send", "software_trigger"],
            "approval_state": "not_required",
            "approval_ref": None,
        },
        "user_focus": {"prompt": request.user_focus},
    }
    dars_response = {
        "schema_id": "hisys.dars.response",
        "schema_version": "0.1.0",
        "response_id": dars_response_id,
        "request_id": dars_request_id,
        "handoff_id": handoff_id,
        "created_at": f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}T00:01:00Z",
        "producer": {
            "backend_id": "loopback_fixture",
            "backend_kind": "loopback",
            "role_id": "logical_conservative_devil",
            "model": None,
            "external_call_made": False,
        },
        "critique": {
            "critique_id": critique_id,
            "status": "received",
            "critique_summary": (
                "Recommendation is useful as a research direction, but novelty and proof obligations require "
                "publisher-source validation before stronger claims."
            ),
            "confidence_assessment": "medium",
            "severity": "medium",
            "requires_human_review": True,
            "unsupported_claims": [
                {
                    "claim_ref": candidate_id,
                    "statement": "Unified novelty is not yet proven by fixture evidence alone.",
                    "reason": "Publisher-source comparison has not been collected in the MVP fixture path.",
                    "evidence_refs": [evidence_ref, *connector_evidence_refs],
                    "severity": "medium",
                }
            ],
            "counterarguments": [],
            "risk_findings": [
                {
                    "risk_id": f"RISK-{request.request_id}-NOVELTY",
                    "category": "overclaiming",
                    "statement": "The proposed formalism may overlap existing graph-transformation or DSDEVS variants.",
                    "severity": "medium",
                    "mitigation": "Collect publisher-source evidence and define evaluation scenarios before manuscript claims.",
                }
            ],
            "recommended_actions": [
                {
                    "action_id": f"RECACT-{request.request_id}-SOURCE-VALIDATION",
                    "action_type": "request_more_evidence",
                    "statement": "Validate DSDEVS, graph transformation, and ABM sources before elevating confidence.",
                    "priority": "medium",
                    "requires_approval": True,
                    "allowed_to_execute": False,
                }
            ],
            "linked_record_refs": {
                "sources": [source.source_id for source in request.sources],
                "observations": [],
                "signals": [],
                "memos": [domain_result_ref],
                "alerts": [],
                "handoffs": [handoff_id],
                "requirements": ["HISYS-DARS-CONTRACT-001", "HISYS-FR-INV-006"],
                "runtime_boundary": [domain_result_ref, *connector_evidence_refs],
            },
        },
        "decision_trace": {
            "process_mode": "progressive_adversarial",
            "round_index": 1,
            "critic_role_id": "logical_conservative_devil",
            "critic_profession": "research_gap_reviewer",
            "critic_persona": "conservative_critic",
            "prompt_bundle_ref": "pb-dars-logical-conservative-devil@0.1.0",
            "rubric_refs": ["research-gap-logical-devil@0.1.0"],
            "improvement_direction": "request_more_evidence",
            "blocks_decision": False,
            "unresolved_high_severity_findings": 0,
            "synthesis_summary": "Proceed as a human-reviewed research direction with medium confidence and source-validation conditions.",
        },
        "rubric_scores": [
            {
                "axis_id": "evidence_coverage",
                "score": 3,
                "max_score": 5,
                "severity": "medium",
                "confidence": "medium",
                "rationale": "Fixture evidence covers the gap structure but not publisher-source novelty.",
                "evidence_refs": [evidence_ref, *connector_evidence_refs],
                "improvement_recommendation": "Add publisher-source literature evidence packages.",
            }
        ],
        "validation": {"schema_valid": True, "warnings": ["fixture-local evidence only"], "rejected_fields": []},
        "boundary": {
            "allowed_actions": "advisory_only",
            "action_taken": "none",
            "mutation_requested": False,
            "mutation_performed": False,
            "external_side_effects_requested": False,
            "external_side_effects_performed": False,
        },
    }
    dars_trace = {
        "schema_id": "hisys.dars.trace_link",
        "schema_version": "0.1.0",
        "trace_id": trace_id,
        "request_id": dars_request_id,
        "response_id": dars_response_id,
        "handoff_id": handoff_id,
        "source_refs": [source.source_id for source in request.sources],
        "observation_refs": [],
        "signal_refs": [],
        "memo_refs": [domain_result_ref],
        "alert_refs": [],
        "evidence_refs": [evidence_ref, *connector_evidence_refs],
        "critique_id": critique_id,
        "recommended_action_ids": [f"RECACT-{request.request_id}-SOURCE-VALIDATION"],
        "runtime_boundary_refs": [
            f"runtime-boundary/dars/{yyyymmdd}/dars-request-{dars_request_id}.json",
            f"runtime-boundary/dars/{yyyymmdd}/dars-response-{dars_response_id}.json",
            domain_result_ref,
            *connector_evidence_refs,
        ],
        "requirement_refs": ["HISYS-DARS-CONTRACT-001", "HISYS-FR-INV-006"],
        "policy_refs": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
        "trace_complete": True,
        "gaps": [],
        "external_call_made": False,
        "mutation_performed": False,
        "action_taken": "none",
    }
    request_path = dars_dir / f"dars-request-{dars_request_id}.json"
    response_path = dars_dir / f"dars-response-{dars_response_id}.json"
    trace_path = dars_dir / f"dars-trace-{trace_id}.json"
    request_path.write_text(json.dumps(dars_request, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    response_path.write_text(json.dumps(dars_response, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trace_path.write_text(json.dumps(dars_trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trace_ref = str(trace_path.relative_to(instance.root))
    domain_result.dars_refs.extend(
        [str(request_path.relative_to(instance.root)), str(response_path.relative_to(instance.root)), trace_ref]
    )
    domain_result.runtime_boundary_refs.extend([str(request_path.relative_to(instance.root)), str(response_path.relative_to(instance.root)), trace_ref])
    return domain_result


def _write_chief_editor_research_review(
    *,
    instance: InstanceRoot,
    request: DomainInvestigationRequest,
    domain_result: DomainInvestigationResult,
    yyyymmdd: str,
) -> DomainInvestigationResult:
    """Write the Chief Editor research recommendation review product."""

    decision_id = f"CEDEC-{request.request_id}"
    decision_dir = instance.runtime_boundary_dir / "chief-editor" / "research" / yyyymmdd
    decision_dir.mkdir(parents=True, exist_ok=True)
    recommended_id = domain_result.alternative_decision_set.recommended_candidate_id
    dars_trace_refs = [ref for ref in domain_result.dars_refs if "/dars-trace-" in ref]
    source_evidence_refs = [
        ref
        for package in domain_result.investigation_data.evidence_packages
        for ref in package.evidence_refs
        if ref.startswith("runtime-boundary/source-connectors/")
    ]
    source_validation_status = "fixture_source_evidence_present" if source_evidence_refs else "source_validation_needed"
    decision = {
        "schema_id": "hisys.chief_editor.research_recommendation_review",
        "schema_version": "0.1.0",
        "decision_id": decision_id,
        "request_id": request.request_id,
        "decision_type": "research_recommendation_review",
        "status": "recommend_with_conditions",
        "domain": request.domain,
        "objective": request.objective,
        "recommended_candidate_id": recommended_id,
        "recommended_direction": domain_result.recommendation_summary,
        "source_validation_status": source_validation_status,
        "source_evidence_refs": source_evidence_refs,
        "conditions": [
            "Validate fixture source evidence against live publisher pages before publication claims.",
            "Collect publisher-source evidence for DSDEVS, graph transformation, and ABM literature.",
            "Define evaluation scenarios for topology/behavior co-evolution.",
            "Keep novelty claims conditional until DARS source-validation actions are resolved.",
        ],
        "required_next_evidence": [
            "DSDEVS source literature",
            "graph transformation/self-organization formalism sources",
            "agent-based modeling emergence/verification sources",
            "evaluation scenarios for topology/behavior co-evolution",
        ],
        "dars_trace_refs": dars_trace_refs,
        "human_approval_required": True,
        "approval_status": "not_requested",
        "action_taken": "none",
        "external_call_made": False,
        "mutation_performed": False,
        "policy_refs": ["HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
    }
    decision_path = decision_dir / f"research-recommendation-review-{decision_id}.json"
    decision_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = decision_dir / f"research-recommendation-review-{decision_id}.md"
    md_path.write_text(
        "\n".join(
            [
                "# Chief Editor Research Recommendation Review",
                "",
                f"- decision_id: `{decision_id}`",
                f"- request_id: `{request.request_id}`",
                "- decision_type: `research_recommendation_review`",
                "- status: `recommend_with_conditions`",
                f"- recommended_candidate_id: `{recommended_id}`",
                f"- source_validation_status: `{source_validation_status}`",
                "- action_taken: `none`",
                "- human_approval_required: `true`",
                "",
                "## Conditions",
                *[f"- {condition}" for condition in decision["conditions"]],
                "",
            ]
        ),
        encoding="utf-8",
    )
    ref = str(decision_path.relative_to(instance.root))
    domain_result.runtime_boundary_refs.append(ref)
    return domain_result


def _format_domain_request_markdown(request: DomainInvestigationRequest) -> str:
    return "\n".join(
        [
            "# Hisys Domain Investigation Request",
            "",
            f"- request_id: `{request.request_id}`",
            f"- domain: `{request.domain}`",
            f"- objective: {request.objective}",
            f"- external_calls_allowed: `{request.constraints.external_calls_allowed}`",
            f"- mutation_allowed: `{request.constraints.mutation_allowed}`",
            f"- credential_use_allowed: `{request.constraints.credential_use_allowed}`",
            "",
            "## Sources",
            *[f"- `{source.source_id}` ({source.source_type}) `{source.access_mode}`: {source.ref}" for source in request.sources],
            "",
        ]
    )


def _format_domain_tool_result_markdown(request: DomainInvestigationRequest, result: HisysToolResult) -> str:
    return "\n".join(
        [
            "# Hisys Domain Investigation Tool Result",
            "",
            f"- request_id: `{request.request_id}`",
            f"- domain: `{result.domain}`",
            f"- status: `{result.status}`",
            f"- quality_gate: `{result.quality_gate}`",
            f"- external_call_made: `{result.external_call_made}`",
            f"- mutation_performed: `{result.mutation_performed}`",
            "",
            "## Summary",
            result.summary,
            "",
            "## Runtime Boundary References",
            *[f"- {ref}" for ref in result.runtime_boundary_refs],
            "",
        ]
    )


def _write_domain_investigation_report(
    *,
    instance: InstanceRoot,
    request: DomainInvestigationRequest,
    tool_result: HisysToolResult,
    tool_result_ref: str,
    yyyymmdd: str,
) -> Path:
    directory = instance.root / "reports" / "run-summaries" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "domain-investigation-report.json"
    data = {
        "request_id": request.request_id,
        "domain": request.domain,
        "status": tool_result.status,
        "quality_gate": tool_result.quality_gate,
        "tool_result_ref": tool_result_ref,
        "runtime_boundary_refs": tool_result.runtime_boundary_refs,
        "policy_refs": ["HISYS-FR-INV-001", "HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
    }
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path = directory / "domain-investigation-report.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# Domain Investigation Report",
                "",
                f"- request_id: `{request.request_id}`",
                f"- domain: `{request.domain}`",
                f"- status: `{tool_result.status}`",
                f"- tool_result_ref: {tool_result_ref}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return json_path


def _cmd_collect(
    *,
    output_root: Path,
    config_root: Path,
    source_ids: list[str],
    yyyymmdd: str,
    collector_id: str,
) -> int:
    registry = load_source_registry(InstanceRoot(config_root))
    runtime = InvestigatorRuntime(
        registry=registry,
        adapters=_build_fixture_adapters(registry, source_ids),
        instance=InstanceRoot(output_root),
        collector_id=collector_id,
    )
    report = runtime.collect_run(source_ids, yyyymmdd=yyyymmdd)
    boundary_refs = _write_hermes_boundary_records(
        instance=InstanceRoot(output_root),
        report=report,
        registry=registry,
        yyyymmdd=yyyymmdd,
    )
    report_path = _write_collection_report(InstanceRoot(output_root), report, yyyymmdd, boundary_refs)
    print(f"collection run {report.collection_run_id}: report={report_path}")
    print(f"collected: {len(report.collected_observation_refs)}")
    print(f"skipped: {len(report.skipped_source_ids)}")
    print(f"boundary_records: {len(boundary_refs)}")
    if not report.collected_observation_refs:
        print("no observations collected", file=sys.stderr)
        return 1
    return 0


def _cmd_investigate_memo(
    *,
    output_root: Path,
    config_root: Path,
    source_ids: list[str],
    yyyymmdd: str,
    topic: str,
    goal: str,
    perspective_id: str,
    template_id: str,
    collector_id: str,
    purpose: str = "auto",
    agent_types: list[str] | None = None,
) -> int:
    """Run a template-driven Investigator research-to-memo path.

    Traceability: HISYS-INST-INV-001, HISYS-FR-INV-001..006,
    HISYS-FR-MEM-001..005, HISYS-TPL-RESEARCH-SEARCH-001, HISYS-T-026.
    """

    registry = load_source_registry(InstanceRoot(config_root))
    instance = InstanceRoot(output_root)
    collect_runtime = InvestigatorRuntime(
        registry=registry,
        adapters=_build_fixture_adapters(registry, source_ids),
        instance=instance,
        collector_id=collector_id,
    )
    collection = collect_runtime.collect_run(source_ids, yyyymmdd=yyyymmdd)
    observations = _load_observations(instance, yyyymmdd)
    if not observations:
        print("no observations collected for investigation memo", file=sys.stderr)
        return 1

    perspective = _fixture_perspective(perspective_id, producer_id=collector_id)
    guideline = _select_guideline_profile(topic=topic, goal=goal, purpose=purpose)
    if perspective.lifecycle_state != "active":
        print(f"perspective not active: {perspective_id}", file=sys.stderr)
        return 1

    signals = [_investigation_signal(observation, topic=topic, producer_id=collector_id) for observation in observations]
    for signal in signals:
        _write_investigation_signal(instance, signal, yyyymmdd)
    agent_config = load_investigator_agent_config(config_root / "config" / "investigator-agents.yaml")
    try:
        agent_plan = select_configured_agent_plan(
            agent_config,
            guideline_profile_id=guideline.profile_id,
            explicit_agent_types=agent_types,
        )
    except AgentConnectorSafetyError as exc:
        print(f"investigator agent connector blocked: {exc}", file=sys.stderr)
        return 1
    requested_agent_types = agent_plan.agent_types
    research_tasks = _build_research_tasks(
        requested_agent_types,
        topic=topic,
        goal=goal,
        source_ids=source_ids,
    )
    evidence_packages = []
    for task in research_tasks:
        package = create_research_agent(task.agent_type).run(task)
        evidence_packages.append(package)
        _write_research_task(instance, task, yyyymmdd)
        _write_evidence_package(instance, package, yyyymmdd)
    merged_evidence = merge_evidence_packages(evidence_packages) if evidence_packages else None
    memo = _investigation_memo(
        topic=topic,
        goal=goal,
        template_id=template_id,
        perspective=perspective,
        observations=observations,
        signals=signals,
        producer_id=collector_id,
        guideline=guideline,
        merged_evidence=merged_evidence,
    )
    memo_paths = _write_investigation_memo(instance, memo, yyyymmdd)
    report = InvestigationMemoReport(
        topic=topic,
        goal=goal,
        template_id=template_id,
        source_refs=sorted({obs.source_id for obs in observations}),
        observation_refs=[obs.observation_id for obs in observations],
        signal_refs=[signal.signal_id for signal in signals],
        memo_refs=[memo.memo_id],
        memo_paths=[str(path.relative_to(instance.root)) for path in memo_paths],
        skipped_source_ids=collection.skipped_source_ids,
        policy_refs=[
            "HISYS-INST-INV-001",
            "HISYS-D-015",
            "HISYS-DATA-002",
            "HISYS-TPL-RESEARCH-SEARCH-001",
            "HISYS-T-026",
            "HISYS-T-027",
            "HISYS-T-030",
            "HISYS-T-031",
            "HISYS-T-032",
        ],
        research_task_refs=[task.task_id for task in research_tasks],
        evidence_package_refs=[package.package_id for package in evidence_packages],
        agent_ids=merged_evidence.agent_ids if merged_evidence else [],
        limitations=merged_evidence.limitations if merged_evidence else [],
        open_questions=merged_evidence.open_questions if merged_evidence else [],
        guideline_profile_id=guideline.profile_id,
        agent_plan_source=agent_plan.source,
        disabled_optional_agent_refs=agent_plan.disabled_optional_agents,
        blocked_agent_refs=agent_plan.blocked_agents,
    )
    report_path = _write_investigation_report(instance, report, yyyymmdd)
    print(f"investigation memo run: report={report_path}")
    print(f"sources: {len(report.source_refs)}")
    print(f"observations: {len(report.observation_refs)}")
    print(f"signals: {len(report.signal_refs)}")
    print(f"agents: {len(report.agent_ids or [])}")
    print(f"memos: {len(report.memo_refs)}")
    print(f"memo: {instance.root / report.memo_paths[0]}")
    return 0


def _investigation_signal(observation: RawObservation, *, topic: str, producer_id: str) -> ExtractedSignal:
    if observation.data_quality.anomaly_flags:
        summary = "Fixture sensor indicates over-threshold temperature condition."
        signal_type = "anomaly"
        confidence = observation.data_quality.source_confidence
    else:
        summary = f"Fixture source provides accepted evidence for {topic}."
        signal_type = "fact"
        confidence = observation.data_quality.source_confidence
    return ExtractedSignal(
        signal_id=make_id(IdNamespace.SIGNAL, f"{observation.source_id}-INVESTIGATION"),
        observation_refs=[observation.observation_id],
        signal_type=signal_type,
        claim_or_event=summary,
        entities=[observation.source_id, topic],
        time_scope="runtime-local fixture investigation",
        confidence=confidence,
        uncertainty="bounded_by_fixture_source_and_template; live external research is disabled",
        contradictions=[],
        extraction_method="investigator-template-research-v0",
        producer_id=producer_id,
        status="proposed",
    )


def _investigation_memo(
    *,
    topic: str,
    goal: str,
    template_id: str,
    perspective: PerspectiveProfile,
    observations: list[RawObservation],
    signals: list[ExtractedSignal],
    producer_id: str,
    guideline: GuidelineProfile,
    merged_evidence: object | None = None,
) -> ZettelMemo:
    source_refs = sorted({obs.source_id for obs in observations})
    signal_refs = [signal.signal_id for signal in signals]
    summary = _primary_investigation_summary(signals, topic)
    body = _format_investigation_memo_body(
        topic=topic,
        goal=goal,
        template_id=template_id,
        perspective=perspective,
        observations=observations,
        signals=signals,
        guideline=guideline,
        merged_evidence=merged_evidence,
    )
    return ZettelMemo(
        memo_id=make_id(IdNamespace.MEMO),
        title=f"Investigation Memo: {topic}",
        summary=summary,
        body=body,
        source_refs=source_refs,
        signal_refs=signal_refs,
        perspective_id=perspective.perspective_id,
        confidence=min((signal.confidence for signal in signals), default=0.0),
        tags=[
            "hisys",
            "investigator-memo",
            "template:research-topic-search",
            f"guideline:{guideline.profile_id}",
            f"perspective:{perspective.perspective_id}",
            f"topic:{topic.replace(' ', '-')}",
        ],
        links=[obs.observation_id for obs in observations],
        revision="1",
        review_status="draft",
        status="draft",
        producer_id=producer_id,
    )


def _primary_investigation_summary(signals: list[ExtractedSignal], topic: str) -> str:
    if signals:
        return signals[0].claim_or_event
    return f"Investigation memo for {topic}."


def _select_guideline_profile(*, topic: str, goal: str, purpose: str = "auto") -> GuidelineProfile:
    """Select the memo guideline profile from explicit purpose or topic/goal cues."""

    profiles = _guideline_profiles()
    if purpose != "auto":
        return profiles[purpose]
    text = f"{topic} {goal}".lower()
    investment_terms = ["stock", "buy", "valuation", "company", "market trend", "investment", "financial"]
    research_terms = ["research idea", "new idea", "gap", "novelty", "formalism", "paper", "synthesis"]
    if any(term in text for term in investment_terms):
        return profiles["investment_decision_support"]
    if any(term in text for term in research_terms):
        return profiles["research_idea_discovery"]
    return profiles["general_investigation"]


def _guideline_profiles() -> dict[str, GuidelineProfile]:
    return {
        "general_investigation": GuidelineProfile(
            profile_id="general_investigation",
            title="General investigation",
            purpose="Collect bounded evidence and identify follow-up questions.",
            required_sections=[
                "Accepted source evidence",
                "Findings and limitations",
                "Open questions requiring corroboration",
            ],
            decision_frame="Decide whether additional controlled evidence is required before escalation.",
        ),
        "research_idea_discovery": GuidelineProfile(
            profile_id="research_idea_discovery",
            title="Research idea discovery",
            purpose="Find gaps, tensions, and possible new research ideas across competing concepts.",
            required_sections=[
                "Gap statements between competing ideas",
                "Novelty candidates and synthesis opportunities",
                "Evaluation scenarios for validating the new idea",
            ],
            decision_frame="Identify promising research questions rather than selecting an operational action.",
        ),
        "investment_decision_support": GuidelineProfile(
            profile_id="investment_decision_support",
            title="Investment decision support",
            purpose="Gather trend and company evidence to support a buy/hold/avoid decision frame.",
            required_sections=[
                "Company fundamentals and financial health",
                "Market trend, competitors, valuation, and risk factors",
                "Decision framing: buy, hold, avoid, or needs more evidence",
            ],
            decision_frame="Separate evidence from recommendation; require corroborated financial sources before action.",
            safety_note="This memo is not financial advice; it is a controlled evidence-gathering aid.",
        ),
    }


def _format_guideline_profile(guideline: GuidelineProfile) -> list[str]:
    lines = [
        f"- Guideline Profile: `{guideline.profile_id}` — {guideline.title}",
        f"- Purpose: {guideline.purpose}",
        "- Required evidence focus:",
        *[f"  - {section}" for section in guideline.required_sections],
        f"- Decision frame: {guideline.decision_frame}",
    ]
    if guideline.safety_note:
        lines.append(f"- Safety note: {guideline.safety_note}")
    return lines


def _format_investigation_memo_body(
    *,
    topic: str,
    goal: str,
    template_id: str,
    perspective: PerspectiveProfile,
    observations: list[RawObservation],
    signals: list[ExtractedSignal],
    guideline: GuidelineProfile,
    merged_evidence: object | None = None,
) -> str:
    query_set = [
        f"{topic} operations evidence",
        f"{topic} assessment",
        f"{topic} follow-up questions",
    ]
    accepted = [
        f"- `{obs.source_id}` via `{obs.provenance_bundle.collector_kind}`; observation `{obs.observation_id}`; payload_ref `{obs.payload_ref}`"
        for obs in observations
    ]
    findings = [f"- {signal.claim_or_event} (`{signal.signal_id}`, confidence={signal.confidence})" for signal in signals]
    evidence_trace = [
        f"- observation `{obs.observation_id}` -> source `{obs.source_id}` -> payload hash `{obs.payload_hash}`"
        for obs in observations
    ]
    signal_trace = [
        f"- signal `{signal.signal_id}` references observations: {', '.join(signal.observation_refs)}"
        for signal in signals
    ]
    agent_evidence = []
    guideline_lines = _format_guideline_profile(guideline)
    agent_limitations = []
    agent_open_questions = []
    if merged_evidence is not None:
        for claim in merged_evidence.claims:  # type: ignore[attr-defined]
            agent_evidence.append(
                f"- {claim.text} (claim `{claim.claim_id}`, evidence: {', '.join(claim.evidence_refs)})"
            )
        agent_limitations = [f"- {item}" for item in merged_evidence.limitations]  # type: ignore[attr-defined]
        agent_open_questions = [f"- {item}" for item in merged_evidence.open_questions]  # type: ignore[attr-defined]
        for evidence in merged_evidence.evidence:  # type: ignore[attr-defined]
            signal_trace.append(
                f"- research evidence `{evidence.evidence_id}` by `{evidence.agent_id}` -> `{evidence.title}`"
            )
    return "\n".join(
        [
            f"# Investigation Memo: {topic}",
            "",
            f"Template: `{template_id}` / `HISYS-TPL-RESEARCH-SEARCH-001`",
            f"Perspective: `{perspective.perspective_id}` — {perspective.title}",
            "",
            "## Research Question",
            f"- Topic: {topic}",
            f"- Goal: {goal}",
            "- Scope: runtime-local fixture investigation; live web/network research is disabled until harness rules approve it.",
            "",
            "## Query Set",
            *[f"- {query}" for query in query_set],
            "",
            "## Accepted Source Records",
            *(accepted or ["- none"]),
            "",
            "## Skipped/Rejected Source Records",
            "- none in this run; all requested fixture sources were accepted by the registry gate.",
            "",
            "## Investigation Findings",
            *(findings or ["- No extracted findings."]),
            "",
            "## Purpose Guideline",
            *guideline_lines,
            "",
            "## Research Agent Evidence",
            *(agent_evidence or ["- No research agent evidence packages were dispatched in this run."]),
            "",
            "## Evidence Trace",
            *evidence_trace,
            *signal_trace,
            "",
            "## Interpretation",
            "- The memo separates evidence from interpretation: RawObservation files keep payload references and hashes, while this memo records the Investigator's template-based judgment.",
            "- The raw payload is not copied into the memo body; downstream reviewers must follow the observation refs for evidence inspection.",
            "",
            "## Agent Limitations",
            *(agent_limitations or ["- none"]),
            "",
            "## Open Questions",
            *(agent_open_questions or [
                "- Should this finding be corroborated with an independent source before Chief Editor escalation?",
                "- Is this a one-off fixture anomaly or part of a repeated temporal pattern?",
            ]),
            "",
        ]
    )


def _write_investigation_signal(instance: InstanceRoot, signal: ExtractedSignal, yyyymmdd: str) -> Path:
    directory = instance.root / "data" / "extracted-signals" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{signal.signal_id}.json"
    path.write_text(_record_json(signal), encoding="utf-8")
    return path


def _write_research_task(instance: InstanceRoot, task: ResearchTask, yyyymmdd: str) -> Path:
    directory = instance.root / "data" / "research-tasks" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{task.task_id}.json"
    path.write_text(_record_json(task), encoding="utf-8")
    return path


def _write_evidence_package(instance: InstanceRoot, package: object, yyyymmdd: str) -> Path:
    directory = instance.root / "data" / "evidence-packages" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    package_id = package.package_id  # type: ignore[attr-defined]
    path = directory / f"{package_id}.json"
    path.write_text(_record_json(package), encoding="utf-8")
    return path


def _write_investigation_memo(instance: InstanceRoot, memo: ZettelMemo, yyyymmdd: str) -> tuple[Path, Path]:
    directory = instance.root / "data" / "investigation-memos" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{memo.memo_id}.json"
    markdown_path = directory / f"{memo.memo_id}.md"
    json_path.write_text(_record_json(memo), encoding="utf-8")
    markdown_path.write_text(_format_investigation_memo_markdown(memo), encoding="utf-8")
    return json_path, markdown_path


def _write_investigation_report(instance: InstanceRoot, report: InvestigationMemoReport, yyyymmdd: str) -> Path:
    directory = instance.root / "reports" / "run-summaries" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "investigation-memo-report.json"
    markdown_path = directory / "investigation-memo-report.md"
    json_path.write_text(_record_json(report), encoding="utf-8")
    markdown_path.write_text(_format_investigation_report_markdown(report), encoding="utf-8")
    return json_path


def _format_investigation_memo_markdown(memo: ZettelMemo) -> str:
    frontmatter = [
        "---",
        f"memo_id: {memo.memo_id}",
        f"perspective_id: {memo.perspective_id}",
        "signal_refs:",
        *[f"  - {ref}" for ref in memo.signal_refs],
        "source_refs:",
        *[f"  - {ref}" for ref in memo.source_refs],
        f"confidence: {memo.confidence}",
        f"review_status: {memo.review_status}",
        "tags:",
        *[f"  - {tag}" for tag in memo.tags],
        "---",
        "",
    ]
    return "\n".join([*frontmatter, memo.body])


def _format_investigation_report_markdown(report: InvestigationMemoReport) -> str:
    return "\n".join(
        [
            "# Hisys Investigation Memo Report",
            "",
            f"- topic: {report.topic}",
            f"- template_id: `{report.template_id}`",
            f"- sources: {len(report.source_refs)}",
            f"- observations: {len(report.observation_refs)}",
            f"- signals: {len(report.signal_refs)}",
            f"- memos: {len(report.memo_refs)}",
            "",
            "## Memos",
            *[f"- {ref}" for ref in report.memo_refs],
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


def _build_research_tasks(
    agent_types: list[str], *, topic: str, goal: str, source_ids: list[str]
) -> list[ResearchTask]:
    tasks: list[ResearchTask] = []
    for index, agent_type in enumerate(agent_types, start=1):
        tasks.append(
            ResearchTask(
                task_id=f"TASK-INV-{index:03d}",
                agent_type=agent_type,  # type: ignore[arg-type]
                question=goal,
                query=f"{topic} evidence task {index}",
                allowed_source_ids=source_ids,
            )
        )
    return tasks


def _cmd_extract(*, instance_root: Path, yyyymmdd: str, producer_id: str) -> int:
    instance = InstanceRoot(instance_root)
    observations = _load_observations(instance, yyyymmdd)
    if not observations:
        print(f"no raw observations found for date {yyyymmdd}", file=sys.stderr)
        return 1
    runtime = ExtractionRuntime(
        instance=instance,
        extractor=FixtureSignalExtractor(method="fixture-rule-v0"),
        producer_id=producer_id,
    )
    report = runtime.extract_run(observations, yyyymmdd=yyyymmdd)
    report_path = _write_extraction_report(instance, report, yyyymmdd)
    print(f"extraction run: report={report_path}")
    print(f"observations: {len(report.requested_observation_refs)}")
    print(f"signals: {len(report.extracted_signal_refs)}")
    print(f"skipped: {len(report.skipped_observation_refs)}")
    if not report.extracted_signal_refs:
        print("no signals extracted", file=sys.stderr)
        return 1
    return 0


def _load_observations(instance: InstanceRoot, yyyymmdd: str) -> list[RawObservation]:
    directory = instance.root / "data" / "raw-observations" / yyyymmdd
    if not directory.exists():
        return []
    observations: list[RawObservation] = []
    for path in sorted(directory.glob("OBS-*.json")):
        observations.append(RawObservation.model_validate_json(path.read_text(encoding="utf-8")))
    return observations


def _write_extraction_report(instance: InstanceRoot, report: ExtractionReport, yyyymmdd: str) -> Path:
    directory = instance.root / "reports" / "run-summaries" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "extraction-report.json"
    data = asdict(report)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path = directory / "extraction-report.md"
    markdown_path.write_text(_format_extraction_report_markdown(report), encoding="utf-8")
    return json_path


def _format_extraction_report_markdown(report: ExtractionReport) -> str:
    return "\n".join(
        [
            "# Hisys Extraction Report",
            "",
            f"- requested_observations: {len(report.requested_observation_refs)}",
            f"- extracted_signals: {len(report.extracted_signal_refs)}",
            f"- skipped_observations: {len(report.skipped_observation_refs)}",
            "",
            "## Extracted Signals",
            *[f"- {ref}" for ref in report.extracted_signal_refs],
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


def _cmd_draft_memo(
    *,
    instance_root: Path,
    yyyymmdd: str,
    perspective_id: str,
    producer_id: str,
) -> int:
    instance = InstanceRoot(instance_root)
    signals = _load_signals(instance, yyyymmdd)
    if not signals:
        print(f"no extracted signals found for date {yyyymmdd}", file=sys.stderr)
        return 1
    observations = _load_observations(instance, yyyymmdd)
    perspective = _fixture_perspective(perspective_id, producer_id=producer_id)
    if perspective.lifecycle_state != "active":
        print(f"perspective not active: {perspective_id}", file=sys.stderr)
        return 1
    runtime = EditorialRuntime(
        instance=instance,
        drafter=FixtureMemoDrafter(template_id="fixture-zettel-v0"),
        producer_id=producer_id,
    )
    report = runtime.draft_run(
        signals,
        observations=observations,
        perspective=perspective,
        yyyymmdd=yyyymmdd,
    )
    report_path = _write_memo_draft_report(instance, report, yyyymmdd)
    print(f"memo draft run: report={report_path}")
    print(f"signals: {len(report.requested_signal_refs)}")
    print(f"drafts: {len(report.draft_memo_refs)}")
    print(f"skipped: {len(report.skipped_signal_refs)}")
    if not report.draft_memo_refs:
        print("no memo drafts created", file=sys.stderr)
        return 1
    return 0


def _load_signals(instance: InstanceRoot, yyyymmdd: str) -> list[ExtractedSignal]:
    directory = instance.root / "data" / "extracted-signals" / yyyymmdd
    if not directory.exists():
        return []
    signals: list[ExtractedSignal] = []
    for path in sorted(directory.glob("SIG-*.json")):
        signals.append(ExtractedSignal.model_validate_json(path.read_text(encoding="utf-8")))
    return signals


def _fixture_perspective(perspective_id: str, *, producer_id: str) -> PerspectiveProfile:
    if perspective_id != "PERSP-OPS-001":
        return PerspectiveProfile(
            perspective_id=perspective_id,
            title="Unknown fixture perspective",
            owner="hisys-fixture",
            lifecycle_state="retired",
            intent="Unknown fixture perspective is inactive.",
            producer_id=producer_id,
            status="retired",
        )
    return PerspectiveProfile(
        perspective_id=perspective_id,
        title="Operations perspective",
        owner="hisys-fixture",
        lifecycle_state="active",
        intent="Surface operational anomalies for review.",
        focus_areas=["thermal anomalies"],
        bias_controls=["Keep raw evidence in linked records."],
        producer_id=producer_id,
        status="active",
    )


def _write_memo_draft_report(instance: InstanceRoot, report: MemoDraftReport, yyyymmdd: str) -> Path:
    directory = instance.root / "reports" / "run-summaries" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "memo-draft-report.json"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path = directory / "memo-draft-report.md"
    markdown_path.write_text(_format_memo_draft_report_markdown(report), encoding="utf-8")
    return json_path


def _format_memo_draft_report_markdown(report: MemoDraftReport) -> str:
    return "\n".join(
        [
            "# Hisys Memo Draft Report",
            "",
            f"- perspective_id: `{report.perspective_id}`",
            f"- perspective_state: `{report.perspective_state}`",
            f"- requested_signals: {len(report.requested_signal_refs)}",
            f"- draft_memos: {len(report.draft_memo_refs)}",
            f"- skipped_signals: {len(report.skipped_signal_refs)}",
            "",
            "## Draft Memos",
            *[f"- {ref}" for ref in report.draft_memo_refs],
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


def _cmd_review_memos(*, instance_root: Path, yyyymmdd: str, producer_id: str) -> int:
    instance = InstanceRoot(instance_root)
    memos = _load_memo_drafts(instance, yyyymmdd)
    if not memos:
        print(f"no memo drafts found for date {yyyymmdd}", file=sys.stderr)
        return 1
    runtime = MemoReviewRuntime(instance=instance, producer_id=producer_id)
    report = runtime.review_run(memos, yyyymmdd=yyyymmdd)
    report_path = instance.root / "reports" / "run-summaries" / yyyymmdd / "memo-review-report.json"
    print(f"memo review run: report={report_path}")
    print(f"reviewed: {len(report.reviewed_memo_refs)}")
    print(f"duplicates: {len(report.duplicate_memo_refs)}")
    print(f"conflicts: {len(report.conflict_memo_refs)}")
    print(f"clean: {len(report.clean_memo_refs)}")
    return 0


def _load_memo_drafts(instance: InstanceRoot, yyyymmdd: str) -> list[ZettelMemo]:
    directory = instance.root / "data" / "memo-drafts" / yyyymmdd
    if not directory.exists():
        return []
    memos: list[ZettelMemo] = []
    for path in sorted(directory.glob("MEM-*.json")):
        memos.append(ZettelMemo.model_validate_json(path.read_text(encoding="utf-8")))
    return memos


def _cmd_decide_alerts(
    *,
    instance_root: Path,
    yyyymmdd: str,
    producer_id: str,
    conflict_severity: str = "medium",
    target_channel: str | None = None,
    product_type: str | None = None,
) -> int:
    instance = InstanceRoot(instance_root)
    memos = _load_memo_drafts(instance, yyyymmdd)
    if not memos:
        print(f"no memo drafts found for date {yyyymmdd}", file=sys.stderr)
        return 1
    memo_review_report = _load_memo_review_report(instance, yyyymmdd)
    if memo_review_report is None:
        print(f"no memo review report found for date {yyyymmdd}", file=sys.stderr)
        return 1
    config = _load_chief_editor_config(instance)
    selected_product_type = product_type or str(config.get("product_type", "alert_delivery_dry_run"))
    selected_conflict_severity = str(config.get("conflict_severity", conflict_severity))
    selected_target_channel = target_channel or str(config.get("target_channel", "runtime-local"))
    product = create_chief_editor_product(
        product_type=selected_product_type,  # type: ignore[arg-type]
        instance=instance,
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id=producer_id,
        conflict_severity=selected_conflict_severity,
        target_channel=selected_target_channel,
    )
    report = product.decide_run(memos, memo_review_report=memo_review_report, yyyymmdd=yyyymmdd)
    report_path = instance.root / "reports" / "run-summaries" / yyyymmdd / "alert-decision-report.json"
    print(f"alert decision run: report={report_path}")
    print(f"product_type: {selected_product_type}")
    print(f"reviewed: {len(report.reviewed_memo_refs)}")
    print(f"alert_decisions: {len(report.alert_decision_refs)}")
    print(f"non_escalation_decisions: {len(report.non_escalation_decision_refs)}")
    print(f"suppressed_memos: {len(report.suppressed_memo_refs)}")
    print(f"skipped: {len(report.skipped_memo_refs)}")
    if not report.alert_decision_refs and not report.non_escalation_decision_refs:
        print("no alert decisions created", file=sys.stderr)
        return 1
    return 0


def _cmd_plan_alert_actions(*, instance_root: Path, yyyymmdd: str, producer_id: str) -> int:
    instance = InstanceRoot(instance_root)
    alert_dir = instance.root / "data" / "alert-decisions" / yyyymmdd
    if not alert_dir.exists() or not list(alert_dir.glob("ALERT-*.json")):
        print(f"no alert decisions found for date {yyyymmdd}", file=sys.stderr)
        return 1
    runtime = AlertActionPlanRuntime(instance=instance, producer_id=producer_id)
    report = runtime.plan_run(yyyymmdd=yyyymmdd)
    report_path = instance.root / "reports" / "run-summaries" / yyyymmdd / "alert-action-plan-report.json"
    print(f"alert action plan run: report={report_path}")
    print(f"alert_decisions: {len(report.alert_decision_refs)}")
    print(f"action_plans: {len(report.action_plan_refs)}")
    print(f"would_send: {len(report.would_send_refs)}")
    print(f"blocked: {len(report.blocked_refs)}")
    print(f"skipped_decisions: {len(report.skipped_decision_refs)}")
    if not report.action_plan_refs:
        print("no alert action plans created", file=sys.stderr)
        return 1
    return 0



def _cmd_execute_alert_actions(*, instance_root: Path, yyyymmdd: str, connector_id: str) -> int:
    instance = InstanceRoot(instance_root)
    report = AlertConnectorRuntime(instance=instance, connector_id=connector_id).execute_run(yyyymmdd=yyyymmdd)
    print(f"alert connector execution: report={instance.root / report.report_ref}")
    print(f"action_plans: {len(report.action_plan_refs)}")
    print(f"executions: {len(report.execution_refs)}")
    print(f"sent: {len(report.sent_refs)}")
    print(f"blocked: {len(report.blocked_refs)}")
    print(f"skipped_plans: {len(report.skipped_plan_refs)}")
    return 0



def _cmd_request_dars_critique(
    *,
    instance_root: Path,
    yyyymmdd: str,
    source_execution_id: str,
    critique_text: str,
    producer_id: str,
) -> int:
    instance = InstanceRoot(instance_root)
    report = (
        DarsRuntime(instance=instance).run_fixture_critique(
            yyyymmdd=yyyymmdd,
            source_execution_id=source_execution_id,
            critique_text=critique_text,
            producer_id=producer_id,
        )
        if critique_text
        else DarsRuntime(instance=instance).run_loopback_placeholder(
            yyyymmdd=yyyymmdd,
            source_execution_id=source_execution_id,
            producer_id=producer_id,
        )
    )
    print(f"dars critique: report={instance.root / report.report_ref}")
    print(f"handoffs: {len(report.handoff_refs)}")
    print(f"critiques: {len(report.critique_refs)}")
    print(f"linked_executions: {len(report.linked_execution_refs)}")
    print(f"skipped_executions: {len(report.skipped_execution_refs)}")
    print("dars_backend: loopback_placeholder")
    print("external_call_made: false")
    return 0 if report.handoff_refs else 1



def _cmd_review_alert_approval(
    *,
    instance_root: Path,
    yyyymmdd: str,
    alert_id: str,
    outcome: str,
    rationale: str,
    reviewer_id: str,
) -> int:
    instance = InstanceRoot(instance_root)
    try:
        report = AlertApprovalTransitionRuntime(
            instance=instance,
            reviewer_id=reviewer_id,
        ).transition(
            yyyymmdd=yyyymmdd,
            alert_id=alert_id,
            outcome=outcome,  # type: ignore[arg-type]
            rationale=rationale,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    report_path = instance.root / "reports" / "run-summaries" / yyyymmdd / "alert-approval-transition-report.json"
    print(f"alert approval transition: report={report_path}")
    print(f"alert_decision: {report.alert_decision_ref}")
    print(f"previous: {report.previous_approval_status}/{report.previous_status}")
    print(f"new: {report.new_approval_status}/{report.new_status}")
    print(f"action_taken: {report.action_taken}")
    return 0



def _load_chief_editor_config(instance: InstanceRoot) -> dict:
    path = instance.config_dir / "chief-editor.yaml"
    if not path.exists():
        return {}
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("config/chief-editor.yaml must contain a mapping")
    return data



def _load_memo_review_report(instance: InstanceRoot, yyyymmdd: str) -> MemoReviewReport | None:
    path = instance.root / "reports" / "run-summaries" / yyyymmdd / "memo-review-report.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return MemoReviewReport(
        reviewed_memo_refs=list(data.get("reviewed_memo_refs", [])),
        duplicate_memo_refs=list(data.get("duplicate_memo_refs", [])),
        conflict_memo_refs=list(data.get("conflict_memo_refs", [])),
        clean_memo_refs=list(data.get("clean_memo_refs", [])),
        policy_refs=list(data.get("policy_refs", ["HISYS-FR-MEM-004", "HISYS-T-013"])),
    )


def _build_fixture_adapters(
    registry: SourceRegistry,
    requested_source_ids: Iterable[str],
) -> dict[str, object]:
    adapters: dict[str, object] = {}
    for source_id in requested_source_ids:
        entry = registry.entries.get(source_id)
        if entry is None:
            continue
        adapters[source_id] = _adapter_for_entry(entry)
    return adapters


def _adapter_for_entry(entry: SourceRegistryEntry) -> object:
    if entry.source_type == "hardware_sensor":
        return HardwareMockSource(
            entry,
            payload={"temperature_c": 92.4, "unit": "C", "fixture": "cli-runtime"},
            device_identity="cli-mock-device",
        )
    if entry.source_type == "web_news":
        return WebNewsMockSource(
            entry,
            payload={"title": "Fixture RSS item", "summary": "Controlled fixture item."},
            citation_url="https://example.test/feed/item-001",
            citation_title="Fixture RSS item",
        )
    if entry.source_type == "agent_system":
        return AgentSystemMockSource(
            entry,
            payload={"critique": "Fixture advisory critique."},
            agent_identity="cli-agent-fixture",
        )
    if entry.source_type == "hermes_tool":
        return HermesToolMockSource(
            entry,
            payload={"finding": "Fixture Hermes collection output."},
            inputs=_hermes_inputs(entry),
        )
    raise ValueError(f"unsupported source_type for fixture adapter: {entry.source_type}")


def _hermes_inputs(entry: SourceRegistryEntry) -> HermesCollectionInputs:
    campaign_id = "CAMP-HERMES-CLI-001"
    prefix = f"hisys/runtime-boundary/hermes/20260508/{campaign_id}"
    return HermesCollectionInputs(
        campaign_id=campaign_id,
        hermes_parent_run_id="run-cli-parent-001",
        user_input_ref=f"{prefix}/user_input-001.md",
        prompt_or_query_ref=f"{prefix}/prompt-001.md",
        tool_output_ref=f"{prefix}/tool_output-001.md",
        boundary_record_ref=f"{prefix}/tool_output-HERMES-CLI-001.md",
        working_directory="examples/instance",
        scope_policy_ref=entry.scope_policy_ref or "HERMES-SCOPE-001",
        approval_state="preapproved",
        tool_invocation_id="tool-cli-001",
        tool_name="mock_search",
        enabled_toolsets=("read_only_search",),
        delegated_task_id="task-cli-001",
        delegated_subagent_preapproval_ref=(
            entry.delegated_subagent_preapproval_ref or "HERMES-PREAPPROVAL-001"
        ),
        source_scope="approved_fixture_sources",
    )


def _write_hermes_boundary_records(
    *,
    instance: InstanceRoot,
    report: CollectionReport,
    registry: SourceRegistry,
    yyyymmdd: str,
) -> list[str]:
    writer = HermesBoundaryWriter(instance)
    refs: list[str] = []
    for source_id in report.requested_source_ids:
        entry = registry.entries.get(source_id)
        if entry is None or entry.source_type != "hermes_tool" or source_id in report.skipped_source_ids:
            continue
        refs.append(
            writer.write_record(
                yyyymmdd=yyyymmdd,
                campaign_id="CAMP-HERMES-CLI-001",
                record_kind="tool_output",
                stable_id="HERMES-CLI-001",
                title=f"Hermes fixture collection: {source_id}",
                body=(
                    f"Source ID: `{source_id}`\n\n"
                    "Payload summary: Fixture Hermes collection output.\n\n"
                    f"Collection run: `{report.collection_run_id}`\n\n"
                    f"Observation refs: {', '.join(report.collected_observation_refs)}\n"
                ),
            )
        )
    return refs


def _write_collection_report(
    instance: InstanceRoot,
    report: CollectionReport,
    yyyymmdd: str,
    boundary_refs: list[str] | None = None,
) -> Path:
    directory = instance.root / "reports" / "run-summaries" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "collection-report.json"
    data = asdict(report)
    data["boundary_record_refs"] = list(boundary_refs or [])
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path = directory / "collection-report.md"
    markdown_path.write_text(_format_report_markdown(report, boundary_refs or []), encoding="utf-8")
    return json_path


def _format_report_markdown(report: CollectionReport, boundary_refs: list[str] | None = None) -> str:
    return "\n".join(
        [
            "# Hisys Collection Report",
            "",
            f"- collection_run_id: `{report.collection_run_id}`",
            f"- requested_source_ids: {', '.join(report.requested_source_ids)}",
            f"- collected_observations: {len(report.collected_observation_refs)}",
            f"- skipped_sources: {len(report.skipped_source_ids)}",
            "",
            "## Boundary Records",
            *[f"- {ref}" for ref in (boundary_refs or [])],
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
