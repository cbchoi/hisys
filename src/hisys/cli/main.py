"""Hisys CLI runtime entry points.

Traceability: HISYS-PKG-ARCH-001 Section 3, HISYS-RUNTIME-DIR-001,
HISYS-INST-INV-001, HISYS-D-015, HISYS-D-016, HISYS-T-001,
HISYS-T-007, HISYS-T-008, HISYS-T-009, HISYS-T-010, HISYS-T-011,
HISYS-T-012, HISYS-T-013, HISYS-T-014, HISYS-T-015, HISYS-T-016,
HISYS-T-017, HISYS-T-018, HISYS-T-019, HISYS-T-020, HISYS-T-021,
HISYS-T-022, HISYS-T-023, HISYS-T-024, HISYS-T-025.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

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
from ..editor import EditorialRuntime, FixtureMemoDrafter, MemoDraftReport, MemoReviewReport, MemoReviewRuntime
from ..extraction import ExtractionReport, ExtractionRuntime, FixtureSignalExtractor
from ..integrations import HermesBoundaryWriter
from ..investigator import CollectionReport, InvestigatorRuntime
from ..registry import SourceRegistry
from ..schemas import ExtractedSignal, PerspectiveProfile, RawObservation, SourceRegistryEntry, ZettelMemo


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
