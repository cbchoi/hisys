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
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

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
from ..agents.dars_panel import (
    DarsCriticPanelConfig,
    DarsCriticPanelRuntime,
    DarsCriticRoleConfig,
)
from ..agents.dars_panel_live_adapter import LocalModelCriticRequest, LocalModelPanelAdapter
from ..agents.dars_panel_live_config import LiveDarsPanelActivationPacket
from ..audit import LapidaryGovernanceAuditWriter
from ..browser.public_profile import load_public_browser_profile
from ..browser.public_summary import write_public_browser_run_summary
from ..browser.reports import (
    _browser_investigation_report,
    _render_browser_chief_editor_review_md,
    _render_browser_dars_handoff_md,
    _render_browser_dars_revision_report_md,
    _render_browser_dars_revision_resolution_md,
    _render_browser_dars_review_md,
    _render_final_browser_acceptance_report_md,
    _render_final_browser_acceptance_review_md,
    _write_browser_investigation_report,
)
from ..browser.workflow import BrowserInvestigationRunConfig, run_browser_investigation
from ..hermes_deploy import (
    DEFAULT_HERMES_TOOL_ROOT,
    build_hermes_deploy_report,
    deploy_hisys_to_hermes,
    get_hermes_deployment_status,
    rollback_hisys_hermes_tool,
)
from ..browser.review_chain import (
    _build_browser_chief_editor_review,
    _build_browser_dars_review,
    _build_browser_dars_revision_resolution,
    _build_final_browser_acceptance_review,
    _browser_revision_ready_for_final_review,
    _primary_browser_segment,
)
from ..config import InstanceRoot, apply_live_vault_transaction, apply_vault_plan_to_fixture, build_live_obsidian_config_status_report, build_live_vault_approval_package, build_live_vault_preflight_report, build_live_vault_transaction_plan, build_live_vault_write_gate_report, build_obsidian_evidence_promotion_plan, build_obsidian_git_sync_plan, build_obsidian_milestone_status_report, build_topic_gatekeeper_decision, build_topic_identity_transition_plan, build_vault_plan, build_vault_template_plan, execute_obsidian_git_initialization_in_fixture, execute_obsidian_git_sync_in_fixture, execute_obsidian_git_sync_live, load_source_registry, rehearse_live_vault_transaction_in_fixture, validate_fixture_vault_roundtrip, validate_vault_manifests, write_live_obsidian_config_status_report, write_live_vault_approval_package, write_live_vault_preflight_report, write_live_vault_transaction_apply_report, write_live_vault_transaction_plan, write_live_vault_transaction_rehearsal_report, write_live_vault_write_gate_report, write_obsidian_evidence_promotion_plan, write_obsidian_git_fixture_execution_report, write_obsidian_git_live_execution_report, write_obsidian_milestone_status_report, write_topic_gatekeeper_decision, write_topic_identity_transition_plan, write_vault_apply_report, write_vault_plan_artifacts, write_vault_roundtrip_report, write_vault_template_plan_artifacts, write_vault_validation_report
from ..connectors import ClaimCoverageGateBuilder, ClaimEvidenceLedgerBuilder, ClaimEvidenceSummaryBuilder, DoiMetadataConnector, FixturePublisherConnector, GeneralWebSearchConnector, OpenAccessPdfConnector, PdfCandidatePlanner, PdfEvidencePromotionLoader, PdfQuoteExtractor, PlaywrightBrowserConnector, PlaywrightUnavailableError, RecommendationClaimRegistryBuilder, SourceConnectorDispatchGate, load_source_connector_registry
from ..connectors.live_source_evidence import SourceAccessRecord, SourceEvidenceItem
from ..core.ids import IdNamespace, make_id
from ..contracts.evidence_reasons import reason_codes
from ..contracts.evaluator import EvidenceSummary, evaluate_pass_contract
from ..contracts.pass_registry import PassContractRegistryEntry, candidate_from_proposal, find_contract, load_pass_contract_registry, promote_candidate
from ..contracts.review_package import build_review_package
from ..domain import (
    DomainAdapterRegistry,
    DomainInvestigationContext,
    StructuredDomainAdapter,
    codebase_spec,
    investment_spec,
    research_spec,
)
from ..domain.specs import validate_spec_collisions
from ..editor import EditorialRuntime, FixtureMemoDrafter, MemoDraftReport, MemoReviewReport, MemoReviewRuntime
from ..evidence_store import (
    build_stone_candidates,
    evidence_store_status,
    import_investigation_artifacts,
    init_evidence_store,
    promote_stone_candidate,
)
from ..environment_config import DEFAULT_ENVIRONMENT_CONFIG, environment_config_status, init_environment_config
from ..extraction import ExtractionReport, ExtractionRuntime, FixtureSignalExtractor
from ..integrations import HermesBoundaryWriter
from ..operations.lapidary_flow import build_weighted_alternative
from ..operations.agent_workflow import (
    build_finish_packet,
    build_spec_first_run_packet,
    write_finish_packet,
    write_spec_first_run_packet,
)
from ..operations.codebase_analysis import (
    CodebaseInventory,
    PythonSymbolIndex,
    build_codebase_inventory,
    build_codebase_scope_map,
    build_codebase_validation_plan,
    build_python_symbol_index,
    load_codebase_review_bundle,
    resolve_instance_runtime_ref,
    review_codebase_source_inspection,
    scan_codebase_risk_boundaries,
    write_codebase_inventory,
    write_codebase_risk_scan,
    write_codebase_scope_map,
    write_codebase_source_inspection_decision,
    write_python_symbol_index,
)
from ..operations.backup import create_backup, restore_backup_dry_run
from ..operations.health import collect_health_status
from ..operations.release_readiness import QualityGateResult, build_release_readiness_report
from ..operations.codebase_map_freshness import (
    build_codebase_map_freshness_report,
    write_codebase_map_freshness_report,
)
from ..operations.runtime_boundary_consistency import (
    build_runtime_boundary_consistency_report,
    write_runtime_boundary_consistency_report,
)
from ..operations.runtime_status_surface import (
    build_runtime_status_packet,
    render_runtime_status_text,
    write_runtime_status_surface,
)
from ..operations.traceability_coverage import (
    build_traceability_coverage_report,
    load_repo_traceability_anchors,
    write_traceability_coverage_report,
)
from ..operations.change_impact import (
    ChangeImpactRequest,
    build_change_impact_report,
    write_change_impact_report,
)
from ..operations.architecture_candidates import (
    ArchitectureCandidateInputs,
    build_architecture_candidate_report,
    write_architecture_candidate_report,
)
from ..operations.codebase_evidence_portfolio import (
    CodebaseEvidencePortfolioRequest,
    EvidenceLineRef,
    build_codebase_evidence_portfolio_report,
    write_codebase_evidence_portfolio_report,
)
from ..operations.oss_comparison_adapter import (
    ApprovedOssSource,
    LocalCodebaseLine,
    OssComparisonRequest,
    build_oss_comparison_report,
    write_oss_comparison_report,
)
from ..operations.code_analysis_pass_contract import (
    _SUPPORTED_QUESTION_TYPES as CODE_ANALYSIS_SUPPORTED_QUESTION_TYPES,
    build_code_analysis_evidence_summary,
    write_code_analysis_pass_contract_evaluation,
)
from ..contracts.subagent_evidence_collector import (
    validate_subagent_evidence_result_packet,
    validate_subagent_evidence_task_packet,
)
from ..investigator import (
    ClaimRecord,
    CollectionReport,
    EvidenceItem,
    EvidencePackage,
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
    BrowserDarsRevisionResolution,
    BrowserDarsRevisionResolutionReport,
    CandidateRecord,
    DomainEvidencePackage,
    DomainInvestigationRequest,
    DomainInvestigationResult,
    FinalBrowserAcceptanceReview,
    FinalBrowserAcceptanceReviewReport,
    HisysToolResult,
    InvestigationDataPackage,
    InvestmentDecisionPacket,
    InvestmentSignal,
    InvestmentWeightPolicy,
    ExtractedSignal,
    HumanApprovalGate,
    ScenarioAssessment,
    EvidenceChainRecord,
    HisysMode,
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
    orchestrator_harness_ref: str | None = None
    harness_source_refs: list[str] | None = None
    user_opinion: str | None = None


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


def _load_orchestrator_harness(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("orchestrator harness must be a JSON object")
    if data.get("schema_id") not in {None, "hisys.investigator.orchestrator_harness"}:
        raise ValueError("orchestrator harness schema_id is not supported")
    return data


def _string_list_from_harness(data: dict[str, object], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"orchestrator harness {key} must be a list of non-empty strings")
    return [item.strip() for item in value]


def _optional_string_from_harness(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"orchestrator harness {key} must be a string when present")
    return value.strip() or None


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique


def _record_json(record: object) -> str:
    if hasattr(record, "model_dump"):
        data = record.model_dump(mode="json")  # type: ignore[attr-defined]
    else:
        data = asdict(record)  # type: ignore[arg-type]
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def _round_trip_record_json(record: object) -> str:
    if hasattr(record, "model_dump"):
        data = record.model_dump(mode="json", round_trip=True)  # type: ignore[attr-defined]
    else:
        data = asdict(record)  # type: ignore[arg-type]
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _safe_relative_ref(instance_root: Path, path: Path) -> str:
    return path.relative_to(instance_root).as_posix()


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "unspecified"


def _contract_fixture_name(domain: str, question_type: str) -> str:
    return f"{_slug(domain).replace('-', '_')}_{_slug(question_type).replace('-', '_')}.yaml"


def _build_pass_contract_proposal(
    *,
    yyyymmdd: str,
    domain: str,
    question_type: str,
    failure_mode: str,
    example_request_ids: list[str],
) -> dict[str, object]:
    fixture_name = _contract_fixture_name(domain, question_type)
    proposal_id = f"CONTRACT-PROP-{_slug(domain).upper()}-{_slug(question_type).upper()}-{_slug(failure_mode).upper()}"
    return {
        "schema_id": "hisys.pass_contract.proposal",
        "schema_version": "0.1.0",
        "proposal_id": proposal_id,
        "created_date": yyyymmdd,
        "status": "proposed_for_human_review",
        "domain": domain,
        "question_type": question_type,
        "dominant_failure_mode": failure_mode,
        "example_request_ids": example_request_ids,
        "self_improvement_boundary": (
            "Hisys does not self-authorize lower standards; it proposes bounded pass criteria, "
            "fixtures, tests, and review artifacts for human-reviewed promotion."
        ),
        "needs_more_evidence_reason_taxonomy": reason_codes(),
        "candidate_contract": {
            "contract_id": f"{_slug(domain).replace('-', '_')}_{_slug(question_type).replace('-', '_')}_v0_1_candidate",
            "principle": "expand coverage by adding domain-specific evidence criteria, not by weakening evidence gates",
            "minimum_evidence": {
                "artifact_refs_required": True,
                "alternative_set_required": True,
                "claim_coverage_required": True,
                "contradiction_check_required": True,
                "dars_critique_required": True,
            },
            "blocked_if": [
                "only_user_opinion",
                "only_fixture_evidence_for_live_claims",
                "no_traceable_artifact_refs",
                "boundary_violation_detected",
            ],
            "promotion_gate": "human_reviewed_traceable_change",
        },
        "suggested_artifacts": [
            f"tests/fixtures/pass-contracts/{fixture_name}",
            f"tests/unit/test_pass_contract_{_slug(domain).replace('-', '_')}_{_slug(question_type).replace('-', '_')}.py",
            "docs/contracts/pass-contract-self-improvement.md",
            "docs/traceability/README.md",
        ],
        "required_validation": [
            "focused pytest for generated contract fixture",
            "domain adapter regression tests",
            "traceability validation",
            "secret scan",
            "human approval before promotion to active registry",
        ],
        "automatic_promotion_allowed": False,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }


def _render_pass_contract_proposal_md(proposal: dict[str, object]) -> str:
    candidate = proposal["candidate_contract"]
    assert isinstance(candidate, dict)
    lines = [
        f"# Pass Contract Proposal: {proposal['proposal_id']}",
        "",
        "## Self-improvement boundary",
        "",
        "Hisys does not self-authorize lower standards. It proposes bounded pass criteria, fixture scenarios, tests, and review artifacts; promotion requires human-reviewed traceable change.",
        "",
        "## Scope",
        "",
        f"- Domain: {proposal['domain']}",
        f"- Question type: {proposal['question_type']}",
        f"- Dominant failure mode: {proposal['dominant_failure_mode']}",
        f"- Status: {proposal['status']}",
        f"- Automatic promotion allowed: {_bool_text(bool(proposal['automatic_promotion_allowed']))}",
        "",
        "## Candidate contract principle",
        "",
        str(candidate["principle"]),
        "",
        "## Required validation before promotion",
        "",
        *[f"- {item}" for item in proposal["required_validation"]],
        "",
        "## Boundary flags",
        "",
        f"- External call made: {_bool_text(bool(proposal['external_call_made']))}",
        f"- Mutation performed: {_bool_text(bool(proposal['mutation_performed']))}",
        f"- Publication/live action approved: {_bool_text(bool(proposal['publication_or_live_action_approved']))}",
        "",
    ]
    return "\n".join(lines)


def _cmd_propose_pass_contract(
    *,
    instance_root: Path,
    yyyymmdd: str,
    domain: str,
    question_type: str,
    failure_mode: str,
    example_request_ids: list[str],
    output_format: str,
) -> int:
    instance = InstanceRoot(instance_root)
    proposal = _build_pass_contract_proposal(
        yyyymmdd=yyyymmdd,
        domain=domain,
        question_type=question_type,
        failure_mode=failure_mode,
        example_request_ids=example_request_ids,
    )
    proposal_dir = instance.root / "runtime-boundary" / "pass-contract-proposals" / yyyymmdd
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_path = proposal_dir / f"{proposal['proposal_id']}.json"
    proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    proposal_path.with_suffix(".md").write_text(_render_pass_contract_proposal_md(proposal), encoding="utf-8")

    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_id": "hisys.pass_contract.proposal_report",
        "schema_version": "0.1.0",
        "message": "pass contract proposal created",
        "proposal_id": proposal["proposal_id"],
        "proposal_ref": _safe_relative_ref(instance.root, proposal_path),
        "proposal_markdown_ref": _safe_relative_ref(instance.root, proposal_path.with_suffix(".md")),
        "status": proposal["status"],
        "automatic_promotion_allowed": False,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    report_path = report_dir / "pass-contract-proposal-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pass contract proposal: {proposal_path}")
    return 0


def _load_contract_json_ref(instance_root: Path, ref: str) -> dict[str, Any]:
    path = Path(ref)
    if not path.is_absolute():
        path = instance_root / ref
    resolved = path.resolve()
    root = instance_root.resolve()
    if root not in resolved.parents and resolved != root:
        raise ValueError(f"ref escapes instance root: {ref}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _cmd_evaluate_pass_contract(*, instance_root: Path, yyyymmdd: str, contract_ref: str, evidence_summary: str, output_format: str) -> int:
    instance = InstanceRoot(instance_root)
    contract_path = Path(contract_ref)
    entries = load_pass_contract_registry(contract_path if contract_path.is_absolute() else instance.root / contract_ref)
    if not entries:
        raise ValueError("contract registry is empty")
    summary_data = _load_contract_json_ref(instance.root, evidence_summary)
    evaluation = evaluate_pass_contract(entries[0], EvidenceSummary.from_dict(summary_data))
    eval_dir = instance.root / "runtime-boundary" / "pass-contract-evaluations" / yyyymmdd
    eval_path = eval_dir / f"EVAL-{entries[0].contract_id}.json"
    payload = evaluation.to_dict()
    _write_json(eval_path, payload)
    report = {
        "schema_id": "hisys.pass_contract.evaluation_report",
        "schema_version": "0.1.0",
        "evaluation_ref": _safe_relative_ref(instance.root, eval_path),
        **payload,
    }
    report_path = instance.reports_dir / "run-summaries" / yyyymmdd / "pass-contract-evaluation-report.json"
    _write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if output_format == "json" else f"pass contract evaluation: {eval_path}")
    return 0


def _cmd_convert_pass_contract_proposal(*, instance_root: Path, yyyymmdd: str, proposal_ref: str, output_format: str) -> int:
    instance = InstanceRoot(instance_root)
    proposal = _load_contract_json_ref(instance.root, proposal_ref)
    candidate = candidate_from_proposal(proposal)
    candidate_dir = instance.root / "runtime-boundary" / "pass-contract-candidates" / yyyymmdd
    candidate_path = candidate_dir / f"{candidate.contract_id}.json"
    _write_json(candidate_path, candidate.to_dict())
    report = {
        "schema_id": "hisys.pass_contract.candidate_report",
        "schema_version": "0.1.0",
        "candidate_ref": _safe_relative_ref(instance.root, candidate_path),
        "status": candidate.status,
        "automatic_promotion_allowed": False,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    report_path = instance.reports_dir / "run-summaries" / yyyymmdd / "pass-contract-candidate-report.json"
    _write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if output_format == "json" else f"pass contract candidate: {candidate_path}")
    return 0


def _cmd_request_pass_contract_review(*, instance_root: Path, yyyymmdd: str, candidate_ref: str, reviewers: list[str], output_format: str) -> int:
    instance = InstanceRoot(instance_root)
    _load_contract_json_ref(instance.root, candidate_ref)
    review = build_review_package(candidate_ref=candidate_ref, reviewers=reviewers)
    review_dir = instance.root / "runtime-boundary" / "pass-contract-reviews" / yyyymmdd
    review_path = review_dir / f"REVIEW-{_slug(Path(candidate_ref).stem)}.json"
    _write_json(review_path, review)
    report = {
        "schema_id": "hisys.pass_contract.review_report",
        "schema_version": "0.1.0",
        "review_ref": _safe_relative_ref(instance.root, review_path),
        **review,
    }
    report_path = instance.reports_dir / "run-summaries" / yyyymmdd / "pass-contract-review-report.json"
    _write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if output_format == "json" else f"pass contract review: {review_path}")
    return 0


def _cmd_promote_pass_contract(*, instance_root: Path, yyyymmdd: str, candidate_ref: str, review_ref: str, validation_ref: str, human_approval_ref: str | None, output_format: str) -> int:
    if not human_approval_ref:
        print("human_approval_ref is required", file=sys.stderr)
        return 2
    instance = InstanceRoot(instance_root)
    candidate_data = _load_contract_json_ref(instance.root, candidate_ref)
    _load_contract_json_ref(instance.root, review_ref)
    _load_contract_json_ref(instance.root, validation_ref)
    candidate = PassContractRegistryEntry(**candidate_data)
    active = promote_candidate(candidate, human_approval_ref=human_approval_ref, review_refs=[review_ref])
    active_path = instance.root / "config" / "pass-contract-registry" / "active" / f"{active.contract_id}.json"
    _write_json(active_path, active.to_dict())
    promotion_path = instance.root / "runtime-boundary" / "pass-contract-promotions" / yyyymmdd / f"PROMOTION-{active.contract_id}.json"
    promotion = {
        "schema_id": "hisys.pass_contract.promotion",
        "schema_version": "0.1.0",
        "active_registry_ref": _safe_relative_ref(instance.root, active_path),
        "human_approval_ref": human_approval_ref,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    _write_json(promotion_path, promotion)
    report = {"schema_id": "hisys.pass_contract.promotion_report", "schema_version": "0.1.0", "promotion_ref": _safe_relative_ref(instance.root, promotion_path), **promotion}
    report_path = instance.reports_dir / "run-summaries" / yyyymmdd / "pass-contract-promotion-report.json"
    _write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if output_format == "json" else f"pass contract promotion: {promotion_path}")
    return 0


def _cmd_audit_needs_more_evidence(*, instance_root: Path, yyyymmdd: str, output_format: str) -> int:
    instance = InstanceRoot(instance_root)
    proposal_dir = instance.root / "runtime-boundary" / "pass-contract-proposals" / yyyymmdd
    counts: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    for path in sorted(proposal_dir.glob("*.json")) if proposal_dir.exists() else []:
        data = json.loads(path.read_text(encoding="utf-8"))
        reason = data.get("dominant_failure_mode", "unknown")
        counts[reason] = counts.get(reason, 0) + 1
        scope = f"{data.get('domain', 'unknown')}::{data.get('question_type', 'unknown')}"
        by_scope[scope] = by_scope.get(scope, 0) + 1
    report = {
        "schema_id": "hisys.needs_more_evidence.audit_report",
        "schema_version": "0.1.0",
        "dominant_reasons": [{"reason": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))],
        "scopes": [{"scope": key, "count": value} for key, value in sorted(by_scope.items())],
        "recommended_next_actions": ["propose_pass_contract"] if counts else [],
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    report_path = instance.reports_dir / "run-summaries" / yyyymmdd / "needs-more-evidence-audit-report.json"
    _write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if output_format == "json" else f"needs-more-evidence audit: {report_path}")
    return 0


def _render_investment_decision_packet_md(packet: InvestmentDecisionPacket) -> str:
    """Render a compact operator-facing investment packet boundary summary."""

    lines = [
        f"# Investment Decision Packet: {packet.packet_id}",
        "",
        f"- Asset: {packet.asset}",
        f"- Instruments: {', '.join(packet.instrument_refs) if packet.instrument_refs else 'n/a'}",
        f"- Time horizon: {packet.time_horizon}",
        f"- Proposed action: {packet.proposed_action}",
        f"- Hisys mode: {packet.hisys_mode.level}",
        f"- Chief Editor status: {packet.chief_editor_status}",
        f"- Devil review status: {packet.devil_review_status}",
        f"- DARS review status: {packet.dars_review_status}",
        f"- Human approval: {packet.human_approval.status}",
        f"- Requested approval scopes: {', '.join(packet.human_approval.requested_scopes) if packet.human_approval.requested_scopes else 'none'}",
        f"- Approved approval scopes: {', '.join(packet.human_approval.approved_scopes) if packet.human_approval.approved_scopes else 'none'}",
        f"- Execution authorized: {_bool_text(packet.execution_authorized)}",
        f"- Publication/live action approved: {_bool_text(packet.publication_or_live_action_approved)}",
        "",
        "## Recommendation summary",
        "",
        packet.recommendation_summary,
        "",
        "## Scores",
        "",
        f"- Confidence: {packet.confidence:.2f}",
        f"- Evidence score: {packet.evidence_score:.2f}",
        f"- Risk score: {packet.risk_score:.2f}",
        f"- Contradiction score: {packet.contradiction_score:.2f}",
        "",
        "## Boundary",
        "",
        "- Not financial advice.",
        "- No autonomous execution.",
        "- Consequential use requires explicit approved human approval.",
    ]
    return "\n".join(lines) + "\n"


def _persist_investment_decision_packet(
    *,
    instance: InstanceRoot,
    packet: InvestmentDecisionPacket,
    yyyymmdd: str,
    weight_policy_path: Path | None = None,
    workflow: str = "investment_decision_packet_build",
    input_evidence_package_refs: list[str] | None = None,
    fixture_backend_used: bool | None = None,
) -> tuple[dict, Path, Path, str | None]:
    output_dir = instance.runtime_boundary_dir / "investment-decisions" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_json_path = output_dir / f"{packet.packet_id}.json"
    packet_md_path = packet_json_path.with_suffix(".md")
    weight_policy_ref: str | None = None
    if weight_policy_path is not None:
        weight_policy = InvestmentWeightPolicy.model_validate_json(weight_policy_path.read_text(encoding="utf-8"))
        if packet.weight_policy_ref is not None and weight_policy.policy_id != packet.weight_policy_ref:
            raise ValueError("weight policy id does not match packet.weight_policy_ref")
        weight_policy_json_path = output_dir / f"{weight_policy.policy_id}.json"
        weight_policy_json_path.write_text(_round_trip_record_json(weight_policy) + "\n", encoding="utf-8")
        weight_policy_ref = _safe_relative_ref(instance.root, weight_policy_json_path)
    packet_json_path.write_text(_round_trip_record_json(packet) + "\n", encoding="utf-8")
    packet_md_path.write_text(_render_investment_decision_packet_md(packet), encoding="utf-8")

    audit_writer = LapidaryGovernanceAuditWriter(instance)
    audit_refs: list[str] = []
    if packet.evidence_chain is not None:
        audit_refs.append(_safe_relative_ref(instance.root, audit_writer.append(packet.evidence_chain, yyyymmdd=yyyymmdd)))
    for alternative in packet.weighted_alternatives:
        audit_refs.append(_safe_relative_ref(instance.root, audit_writer.append(alternative, yyyymmdd=yyyymmdd)))

    report = {
        "schema_id": "hisys.investment_decision_packet_report",
        "workflow": workflow,
        "packet_id": packet.packet_id,
        "asset": packet.asset,
        "packet_ref": _safe_relative_ref(instance.root, packet_json_path),
        "packet_markdown_ref": _safe_relative_ref(instance.root, packet_md_path),
        "packet_weight_policy_ref": packet.weight_policy_ref,
        "weight_policy_ref": weight_policy_ref,
        "input_evidence_package_refs": input_evidence_package_refs or [],
        "fixture_backend_used": fixture_backend_used,
        "lapidary_audit_refs": audit_refs,
        "hisys_mode_level": packet.hisys_mode.level,
        "chief_editor_status": packet.chief_editor_status,
        "devil_review_status": packet.devil_review_status,
        "dars_review_status": packet.dars_review_status,
        "human_approval_status": packet.human_approval.status,
        "human_approval_required_for_consequential_use": packet.human_approval.required,
        "requested_approval_scopes": list(packet.human_approval.requested_scopes),
        "approved_approval_scopes": list(packet.human_approval.approved_scopes),
        "execution_authorized": packet.execution_authorized,
        "publication_or_live_action_approved": packet.publication_or_live_action_approved,
        "action_taken": "none",
        "external_call_made": False,
        "mutation_performed": False,
        "disclaimers": list(packet.disclaimers),
    }
    report_path = output_dir / "investment-decision-packet-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, report_path, packet_json_path, weight_policy_ref


def _cmd_build_investment_decision_packet(
    *,
    instance_root: Path,
    packet_path: Path,
    yyyymmdd: str,
    weight_policy_path: Path | None = None,
) -> int:
    """Validate and persist a human-gated investment packet product boundary."""

    instance = InstanceRoot(instance_root)
    packet = InvestmentDecisionPacket.model_validate_json(packet_path.read_text(encoding="utf-8"))
    report, report_path, _packet_json_path, weight_policy_ref = _persist_investment_decision_packet(
        instance=instance,
        packet=packet,
        yyyymmdd=yyyymmdd,
        weight_policy_path=weight_policy_path,
    )

    print(f"investment decision packet: written packet_id={packet.packet_id}")
    print(f"packet_ref={report['packet_ref']}")
    print(f"report_ref={_safe_relative_ref(instance.root, report_path)}")
    if weight_policy_ref is not None:
        print(f"weight_policy_ref={weight_policy_ref}")
    print(f"execution_authorized={_bool_text(packet.execution_authorized)}")
    print(f"publication_or_live_action_approved={_bool_text(packet.publication_or_live_action_approved)}")
    print(f"human_approval_status={packet.human_approval.status}")
    print("action_taken=none")
    return 0


def _investment_id_suffix(asset: str) -> str:
    id_part = "".join(ch for ch in asset.upper() if ch.isalnum())
    if not id_part:
        id_part = "ASSET"
    return id_part[:24]


def _evidence_package_uses_fixture_backend(package: EvidencePackage) -> bool:
    markers = [package.agent_id, package.agent_type, *package.actions_taken]
    markers.extend(item.agent_id for item in package.evidence)
    return any("fixture" in marker.lower() or "mock" in marker.lower() for marker in markers)


def _source_evidence_confidence_score(confidence: str) -> float:
    return {
        "high": 0.75,
        "medium": 0.6,
        "low": 0.4,
        "unknown": 0.5,
    }.get(confidence, 0.5)


def _cmd_build_investment_evidence_package(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    asset: str,
    source_access_path: Path,
    source_evidence_path: Path,
) -> int:
    """Promote source connector artifacts into an investment EvidencePackage."""

    instance = InstanceRoot(instance_root)
    source_access = SourceAccessRecord.model_validate_json(source_access_path.read_text(encoding="utf-8"))
    source_evidence = SourceEvidenceItem.model_validate_json(source_evidence_path.read_text(encoding="utf-8"))
    if Path(source_evidence.access_ref).name != source_access_path.name and source_evidence.access_ref != _safe_relative_ref(
        instance.root, source_access_path
    ):
        raise ValueError("source evidence access_ref does not match supplied source access artifact")
    if source_access.mutation_performed:
        raise ValueError("investment evidence package requires non-mutating source access")

    suffix = _investment_id_suffix(asset)
    package_id = f"PKG-INV-SOURCE-{suffix}-001"
    evidence_id = f"EV-INV-SOURCE-{suffix}-001"
    claim_id = f"CLAIM-INV-SOURCE-{suffix}-001"
    confidence = _source_evidence_confidence_score(source_evidence.confidence)
    source_ref = source_access.access_id
    package = EvidencePackage(
        package_id=package_id,
        task_id=f"TASK-INV-SOURCE-{suffix}-001",
        agent_id="source-connector-investment-evidence-adapter",
        agent_type="investment_decision_support",
        claims=[
            ClaimRecord(
                claim_id=claim_id,
                text=f"{asset} investment decision support signal: {source_evidence.interpretation}",
                confidence=confidence,
                evidence_refs=[evidence_id],
                limitations=[
                    "Source connector evidence was promoted for dry-run decision support only.",
                    "Human review is required before consequential use.",
                ],
            )
        ],
        evidence=[
            EvidenceItem(
                evidence_id=evidence_id,
                task_id=f"TASK-INV-SOURCE-{suffix}-001",
                agent_id="source-connector-investment-evidence-adapter",
                source_id=source_ref,
                url=source_access.source_url,
                title=source_access.title or f"{asset} source connector evidence",
                quoted_text=source_evidence.quoted_text,
                retrieved_at=source_access.accessed_at,
                content_hash=f"sha256:{source_access.sha256}",
            )
        ],
        limitations=[
            "EvidencePackage is assembled from persisted read-only source connector artifacts.",
            "No autonomous execution, publication, or live action is authorized.",
        ],
        open_questions=[source_evidence.uncertainty] if source_evidence.uncertainty else [],
        external_side_effects=False,
        actions_taken=["source_connector_evidence_promoted"],
    )
    output_dir = instance.data_dir / "evidence-packages" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    package_path = output_dir / f"{package.package_id}.json"
    package_path.write_text(_record_json(package) + "\n", encoding="utf-8")
    report = {
        "schema_id": "hisys.investment_evidence_package_report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "asset": asset,
        "package_id": package.package_id,
        "package_ref": _safe_relative_ref(instance.root, package_path),
        "source_access_ref": _safe_relative_ref(instance.root, source_access_path),
        "source_evidence_ref": _safe_relative_ref(instance.root, source_evidence_path),
        "source_external_call_made": source_access.external_call_made,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
        "execution_authorized": False,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "investment-evidence-package-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"investment evidence package: package_id={package.package_id}")
    print(f"package_ref={report['package_ref']}")
    print(f"source_external_call_made={_bool_text(source_access.external_call_made)}")
    print("external_call_made=false")
    print("mutation_performed=false")
    return 0


def _cmd_run_investment_decision_dry_run(
    *,
    instance_root: Path,
    yyyymmdd: str,
    asset: str,
    instruments: list[str],
    time_horizon: str,
    evidence_package_paths: list[Path],
    weight_policy_path: Path,
) -> int:
    """Assemble a human-gated investment packet from read-only evidence artifacts."""

    if not evidence_package_paths:
        raise ValueError("run-investment-decision-dry-run requires at least one evidence package")
    instance = InstanceRoot(instance_root)
    packages = [EvidencePackage.model_validate_json(path.read_text(encoding="utf-8")) for path in evidence_package_paths]
    if any(package.external_side_effects for package in packages):
        raise ValueError("investment dry-run evidence packages must not report external_side_effects")
    if any(_evidence_package_uses_fixture_backend(package) for package in packages):
        raise ValueError("fixture backend evidence packages are not accepted for investment dry-run")
    first_package = packages[0]
    if not first_package.claims:
        raise ValueError("investment dry-run requires at least one claim")
    if not first_package.evidence:
        raise ValueError("investment dry-run requires at least one evidence item")
    claim = first_package.claims[0]
    evidence_item = first_package.evidence[0]
    source_ref = evidence_item.source_id or evidence_item.url or evidence_item.path
    if not source_ref:
        raise ValueError("investment dry-run evidence items require source_id, url, or path")

    suffix = _investment_id_suffix(asset)
    policy = InvestmentWeightPolicy.model_validate_json(weight_policy_path.read_text(encoding="utf-8"))
    evidence_score = min(1.0, max(0.0, claim.confidence))
    contradiction_score = 0.5 if first_package.open_questions else 0.35
    risk_score = max(0.35, contradiction_score)
    confidence = round((evidence_score + max(0.0, 1.0 - contradiction_score)) / 2, 2)
    chain = EvidenceChainRecord(
        chain_id=f"CHAIN-INVDRY-{suffix}-001",
        producer_id="hisys-investment-decision-dry-run",
        status="active",
        decision_ref=f"ALERT-INVDRY-{suffix}-001",
        synthesis_refs=[first_package.package_id],
        claim_ledger_refs=[claim.claim_id],
        evidence_refs=[evidence_item.evidence_id],
        source_refs=[source_ref],
    )
    alternative = build_weighted_alternative(
        alternative_id=f"ALT-INVDRY-{suffix}-001",
        label=f"Dry-run human-reviewed {asset} decision support",
        claim=claim.text,
        evidence_chain=chain,
        producer_id="hisys-investment-decision-dry-run",
        recommended_use="hybrid",
    )
    packet = InvestmentDecisionPacket(
        packet_id=f"IDP-INVDRY-{suffix}-001",
        producer_id="hisys-investment-decision-dry-run",
        status="draft",
        asset=asset,
        instrument_refs=instruments,
        time_horizon=time_horizon,
        proposed_action="staged_buy",
        weight_policy_ref=policy.policy_id,
        recommendation_summary=f"Dry-run decision-support packet assembled from read-only evidence artifact {first_package.package_id}.",
        confidence=confidence,
        evidence_score=evidence_score,
        risk_score=risk_score,
        contradiction_score=contradiction_score,
        signals=[
            InvestmentSignal(
                signal_id=f"SIG-INVDRY-{suffix}-001",
                name=f"{asset} read-only evidence signal",
                direction="mixed" if first_package.open_questions else "bullish",
                strength=evidence_score,
                evidence_refs=[evidence_item.evidence_id],
                interpretation=claim.text,
                limitations=list(claim.limitations) + list(first_package.limitations),
            )
        ],
        bull_case=ScenarioAssessment(
            case_id=f"CASE-INVDRY-{suffix}-BULL-001",
            summary="Evidence improves enough to support human-reviewed staged exposure.",
            probability=0.34,
            evidence_refs=[evidence_item.evidence_id],
        ),
        base_case=ScenarioAssessment(
            case_id=f"CASE-INVDRY-{suffix}-BASE-001",
            summary="Evidence remains mixed; retain guarded human-reviewed decision support.",
            probability=0.46,
            evidence_refs=[evidence_item.evidence_id],
        ),
        bear_case=ScenarioAssessment(
            case_id=f"CASE-INVDRY-{suffix}-BEAR-001",
            summary="Open questions or contradiction risk block stronger consequential use.",
            probability=0.20,
            evidence_refs=[evidence_item.evidence_id],
        ),
        decision_boundary=["Dry run only; no publication, execution, order placement, or live connector action."],
        risk_register=list(first_package.limitations) + list(first_package.open_questions),
        contradicting_evidence_refs=[evidence_item.evidence_id] if first_package.open_questions else [],
        chief_editor_status="accepted_for_human_reviewed_use",
        devil_review_status="completed",
        dars_review_status="not_started",
        human_insight_refs=[],
        human_approval=HumanApprovalGate(
            required=True,
            status="pending",
            approver_ref="human:operator",
            responsibility_statement="Human accepts responsibility before any consequential use.",
        ),
        disclaimers=["not financial advice", "no autonomous execution"],
        hisys_mode=HisysMode(
            level="decision",
            routing_policy_ref="lapidary-routing-policy/operational-governance-v1",
            upgrade_triggers=["decision_requested", "artifact_backed_dry_run"],
        ),
        evidence_chain=chain,
        weighted_alternatives=[alternative],
    )
    report, report_path, _packet_json_path, weight_policy_ref = _persist_investment_decision_packet(
        instance=instance,
        packet=packet,
        yyyymmdd=yyyymmdd,
        weight_policy_path=weight_policy_path,
        workflow="investment_decision_dry_run",
        input_evidence_package_refs=[str(path) for path in evidence_package_paths],
        fixture_backend_used=False,
    )

    print(f"investment decision dry run: assembled packet_id={packet.packet_id}")
    print(f"packet_ref={report['packet_ref']}")
    print(f"report_ref={_safe_relative_ref(instance.root, report_path)}")
    if weight_policy_ref is not None:
        print(f"weight_policy_ref={weight_policy_ref}")
    print("fixture_backend_used=false")
    print("external_call_made=false")
    print("mutation_performed=false")
    print("action_taken=none")
    return 0


def _cmd_review_investment_decision_packet(
    *,
    instance_root: Path,
    packet_id: str,
    yyyymmdd: str,
    output_format: str,
) -> int:
    """Print an operator-facing summary for a persisted investment packet."""

    instance = InstanceRoot(instance_root)
    output_dir = instance.runtime_boundary_dir / "investment-decisions" / yyyymmdd
    packet_json_path = output_dir / f"{packet_id}.json"
    report_path = output_dir / "investment-decision-packet-report.json"

    packet = InvestmentDecisionPacket.model_validate_json(packet_json_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = {
        "schema_id": "hisys.investment_decision_packet_operator_summary",
        "packet_id": packet.packet_id,
        "asset": packet.asset,
        "instrument_refs": list(packet.instrument_refs),
        "time_horizon": packet.time_horizon,
        "proposed_action": packet.proposed_action,
        "chief_editor_status": packet.chief_editor_status,
        "devil_review_status": packet.devil_review_status,
        "dars_review_status": packet.dars_review_status,
        "human_approval_status": packet.human_approval.status,
        "requested_approval_scopes": list(packet.human_approval.requested_scopes),
        "approved_approval_scopes": list(packet.human_approval.approved_scopes),
        "scores": {
            "confidence": packet.confidence,
            "evidence_score": packet.evidence_score,
            "risk_score": packet.risk_score,
            "contradiction_score": packet.contradiction_score,
        },
        "boundary": {
            "execution_authorized": packet.execution_authorized,
            "publication_or_live_action_approved": packet.publication_or_live_action_approved,
            "action_taken": report.get("action_taken", "unknown"),
            "external_call_made": report.get("external_call_made", "unknown"),
            "mutation_performed": report.get("mutation_performed", "unknown"),
        },
        "artifact_refs": {
            "packet_ref": report.get("packet_ref"),
            "packet_markdown_ref": report.get("packet_markdown_ref"),
            "packet_weight_policy_ref": report.get("packet_weight_policy_ref"),
            "weight_policy_ref": report.get("weight_policy_ref"),
            "report_ref": _safe_relative_ref(instance.root, report_path),
            "lapidary_audit_refs": report.get("lapidary_audit_refs", []),
        },
        "disclaimers": list(packet.disclaimers),
    }

    if output_format == "markdown":
        print(f"# Investment Decision Packet Review: {packet.packet_id}")
        print()
        print(f"- Asset: {packet.asset}")
        print(f"- Proposed action: {packet.proposed_action}")
        print(f"- Human approval: {packet.human_approval.status}")
        print(f"- Requested scopes: {', '.join(packet.human_approval.requested_scopes)}")
        print(f"- Approved scopes: {', '.join(packet.human_approval.approved_scopes) if packet.human_approval.approved_scopes else 'none'}")
        print(f"- Action taken: {summary['boundary']['action_taken']}")
        print(f"- External call made: {_bool_text(bool(summary['boundary']['external_call_made']))}")
        print(f"- Mutation performed: {_bool_text(bool(summary['boundary']['mutation_performed']))}")
        return 0

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _parse_validation_status(items: list[str]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError("validation entries must use name=status")
        name, status = item.split("=", 1)
        statuses[name.strip()] = status.strip()
    return statuses


def _component_status(*, component_id: str, title: str, complete: bool, evidence_refs: list[str], gated: bool = False) -> dict[str, object]:
    return {
        "component_id": component_id,
        "title": title,
        "status": "gated" if gated else ("complete" if complete else "missing"),
        "evidence_refs": evidence_refs,
    }


def _cmd_health_status(*, instance_root: Path, yyyymmdd: str, output_format: str) -> int:
    """Write local health status evidence without external probes."""

    instance = InstanceRoot(instance_root)
    report = collect_health_status(instance.root)
    payload = report.model_dump(mode="json")
    payload.update(
        {
            "schema_id": "hisys.health_status_report",
            "schema_version": "0.1.0",
            "external_call_made": False,
            "mutation_performed": False,
            "publication_or_live_action_approved": False,
            "execution_authorized": False,
        }
    )
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "hisys-health-status.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = report_dir / "hisys-health-status.md"
    md_path.write_text(
        "\n".join(
            [
                "# Hisys Health Status",
                "",
                f"- overall_status: `{payload['overall_status']}`",
                f"- external_call_made: `{str(payload['external_call_made']).lower()}`",
                f"- mutation_performed: `{str(payload['mutation_performed']).lower()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"health status: status={payload['overall_status']} report={json_path}")
    return 0 if payload["overall_status"] == "ok" else 2


def _cmd_backup_runtime(*, instance_root: Path, yyyymmdd: str, backup_id: str, output_format: str) -> int:
    """Create a controlled runtime backup evidence artifact."""

    instance = InstanceRoot(instance_root)
    backup_dir = instance.root / "backups" / yyyymmdd
    report = create_backup(instance.root, backup_dir=backup_dir, backup_id=backup_id)
    payload = report.model_dump(mode="json")
    payload.update(
        {
            "schema_id": "hisys.backup_report",
            "schema_version": "0.1.0",
            "external_call_made": False,
            "mutation_performed": False,
            "publication_or_live_action_approved": False,
            "execution_authorized": False,
        }
    )
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "hisys-backup-report.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"backup runtime: file_count={payload['file_count']} archive={payload['archive_path']}")
    return 0


def _cmd_restore_backup_dry_run(
    *, archive_path: Path, restore_target: Path, report_root: Path, yyyymmdd: str, output_format: str
) -> int:
    """Verify a backup archive without restoring files."""

    instance = InstanceRoot(report_root)
    report = restore_backup_dry_run(archive_path, restore_target)
    payload = report.model_dump(mode="json")
    payload.update(
        {
            "schema_id": "hisys.restore_dry_run_report",
            "schema_version": "0.1.0",
            "external_call_made": False,
            "mutation_performed": False,
            "publication_or_live_action_approved": False,
            "execution_authorized": False,
        }
    )
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "hisys-restore-dry-run.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"restore dry-run: verified={payload['verified']} would_restore={payload['would_restore_count']} report={json_path}")
    return 0 if payload["verified"] else 2


def _parse_quality_gate_result(item: str) -> QualityGateResult:
    parts = item.split(":", 2)
    if len(parts) != 3:
        raise ValueError("quality gate entries must be NAME:STATUS:EVIDENCE")
    name, status, evidence = parts
    return QualityGateResult(name=name, status=status, evidence=evidence)


def _cmd_build_spec_first_packet(
    *,
    instance_root: Path,
    yyyymmdd: str,
    packet_id: str,
    objective: str,
    scope: list[str],
    non_goals: list[str],
    allowed_actions: list[str],
    evidence_contract: list[str],
    expected_artifacts: list[str],
    gate_criteria: list[str],
    human_approval_boundary: str,
    output_format: str,
) -> int:
    """Write a spec-first run packet before governed agent work."""

    packet = build_spec_first_run_packet(
        packet_id=packet_id,
        objective=objective,
        scope=scope,
        non_goals=non_goals,
        allowed_actions=allowed_actions,
        evidence_contract=evidence_contract,
        expected_artifacts=expected_artifacts,
        gate_criteria=gate_criteria,
        human_approval_boundary=human_approval_boundary,
    )
    result = write_spec_first_run_packet(instance_root, yyyymmdd, packet)
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"spec-first packet: packet_id={result['packet_id']} json={result['json_ref']} markdown={result['markdown_ref']}")
    return 0


def _cmd_build_codebase_inventory(
    *,
    repo_root: Path,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    analysis_scope: str | None,
    output_format: str,
) -> int:
    """Build a deterministic local codebase inventory and persist artifacts."""

    inventory = build_codebase_inventory(
        repo_root=repo_root,
        analysis_scope=analysis_scope,
    )
    result = write_codebase_inventory(
        instance_root=instance_root,
        date=yyyymmdd,
        request_id=request_id,
        inventory=inventory,
    )
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "codebase inventory: "
            f"schema={result['schema_id']} json={result['json_ref']} "
            f"markdown={result['markdown_ref']}"
        )
    return 0


def _cmd_build_code_symbol_index(
    *,
    repo_root: Path,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    analysis_scope: str | None,
    output_format: str,
) -> int:
    """Build a deterministic Python AST symbol index and persist artifacts."""

    symbol_index = build_python_symbol_index(
        repo_root=repo_root,
        analysis_scope=analysis_scope,
    )
    result = write_python_symbol_index(
        instance_root=instance_root,
        date=yyyymmdd,
        request_id=request_id,
        symbol_index=symbol_index,
    )
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "codebase symbol index: "
            f"schema={result['schema_id']} json={result['json_ref']} "
            f"markdown={result['markdown_ref']}"
        )
    return 0


def _cmd_scan_codebase_boundaries(
    *,
    repo_root: Path,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    analysis_scope: str | None,
    output_format: str,
) -> int:
    """Run the conservative codebase risk-boundary scanner and persist artifacts."""

    scan = scan_codebase_risk_boundaries(
        repo_root=repo_root,
        analysis_scope=analysis_scope,
    )
    result = write_codebase_risk_scan(
        instance_root=instance_root,
        date=yyyymmdd,
        request_id=request_id,
        scan=scan,
    )
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "codebase risk-boundary scan: "
            f"schema={result['schema_id']} json={result['json_ref']} "
            f"markdown={result['markdown_ref']}"
        )
    return 0


def _cmd_build_codebase_map(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    inventory_ref: str,
    symbol_index_ref: str,
    output_format: str,
) -> int:
    """Assemble a codebase scope map + validation plan from local artifact refs."""

    inventory_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=inventory_ref
    )
    symbol_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=symbol_index_ref
    )

    inventory_payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    symbol_payload = json.loads(symbol_path.read_text(encoding="utf-8"))

    inventory = CodebaseInventory.model_validate(inventory_payload)
    symbol_index = PythonSymbolIndex.model_validate(symbol_payload)

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index
    )
    validation_plan = build_codebase_validation_plan(scope_map)
    result = write_codebase_scope_map(
        instance_root=instance_root,
        date=yyyymmdd,
        request_id=request_id,
        scope_map=scope_map,
        validation_plan=validation_plan,
    )
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "codebase scope map: "
            f"schema={result['schema_id']} json={result['json_ref']} "
            f"markdown={result['markdown_ref']}"
        )
    return 0


def _cmd_review_codebase_analysis(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    inventory_ref: str,
    symbol_index_ref: str,
    scope_map_ref: str,
    risk_scan_ref: str,
    unresolved_blockers: list[str],
    output_format: str,
) -> int:
    """Load a codebase-analysis bundle and persist the review decision packet.

    Returns 0 when the decision is `complete_for_human_review` and 2 when
    the decision is `blocked_needs_more_evidence` so automation can branch
    on the decision without re-parsing the JSON. The CLI never grants
    `approved`, `safe_to_deploy`, or `ready_for_live_action` — those values
    are structurally rejected by the Pydantic decision record.
    """

    bundle = load_codebase_review_bundle(
        instance_root=instance_root,
        inventory_ref=inventory_ref,
        symbol_index_ref=symbol_index_ref,
        scope_map_ref=scope_map_ref,
        risk_scan_ref=risk_scan_ref,
    )
    decision = review_codebase_source_inspection(
        inventory=bundle.inventory,
        symbol_index=bundle.symbol_index,
        scope_map=bundle.scope_map,
        validation_plan=bundle.validation_plan,
        risk_scan=bundle.risk_scan,
        unresolved_blockers=unresolved_blockers,
    )
    result = write_codebase_source_inspection_decision(
        instance_root=instance_root,
        date=yyyymmdd,
        request_id=request_id,
        decision=decision,
    )

    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "codebase source-inspection decision: "
            f"schema={result['schema_id']} decision={result['decision']} "
            f"json={result['json_ref']} markdown={result['markdown_ref']}"
        )

    return 0 if decision.decision == "complete_for_human_review" else 2


def _cmd_build_finish_packet(
    *,
    instance_root: Path,
    yyyymmdd: str,
    packet_id: str,
    spec_packet_ref: str,
    completed_tasks: list[str],
    validation_results: list[str],
    review_findings: list[str],
    unresolved_blockers: list[str],
    next_actions: list[str],
    human_gate_state: str,
    decision: str,
    output_format: str,
) -> int:
    """Write a finish packet that separates completion from live approval."""

    packet = build_finish_packet(
        packet_id=packet_id,
        spec_packet_ref=spec_packet_ref,
        decision=decision,  # type: ignore[arg-type]
        completed_tasks=completed_tasks,
        validation_results=validation_results,
        review_findings=review_findings,
        unresolved_blockers=unresolved_blockers,
        next_actions=next_actions,
        human_gate_state=human_gate_state,
    )
    result = write_finish_packet(instance_root, yyyymmdd, packet)
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"finish packet: packet_id={result['packet_id']} json={result['json_ref']} markdown={result['markdown_ref']}")
    return 0


def _cmd_release_readiness(
    *,
    instance_root: Path,
    yyyymmdd: str,
    quality_gate_items: list[str],
    trace_refs: list[str],
    known_gaps: list[str],
    output_format: str,
) -> int:
    """Write release-readiness evidence report for human review."""

    instance = InstanceRoot(instance_root)
    gates = [_parse_quality_gate_result(item) for item in quality_gate_items]
    report = build_release_readiness_report(
        runtime_root=instance.root,
        quality_gates=gates,
        trace_path_refs=trace_refs,
        known_gaps=known_gaps,
    )
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "hisys-release-readiness.json"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    md_path = report_dir / "hisys-release-readiness.md"
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    if output_format == "json":
        print(report.model_dump_json(indent=2))
    else:
        print(f"release readiness: status={report.overall_status} decision={report.release_decision} report={json_path}")
    return 0 if report.overall_status == "ready_for_review" else 2


def _cmd_traceability_coverage(*, instance_root: Path, yyyymmdd: str, repo_root: Path) -> int:
    """Write a local advisory traceability coverage report via the Hisys CLI."""

    anchors = load_repo_traceability_anchors(repo_root)
    report = build_traceability_coverage_report(anchors)
    refs = write_traceability_coverage_report(
        instance_root=instance_root,
        date=yyyymmdd,
        report=report,
    )
    print(f"traceability coverage report: json={refs['json_ref']}")
    print(f"markdown: {refs['markdown_ref']}")
    print(f"coverage_ratio: {report.coverage_ratio}")
    print(f"unreferenced_requirements: {len(report.unreferenced_requirements)}")
    print(f"orphan_test_ids: {len(report.orphan_test_ids)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0


def _cmd_change_impact(
    *,
    instance_root: Path,
    yyyymmdd: str,
    repo_root: Path,
    changed_refs: tuple[str, ...],
    current_head_short: str | None,
) -> int:
    """Write a local advisory change-impact report via the CLI."""

    anchors = load_repo_traceability_anchors(repo_root)
    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=changed_refs,
        current_head_short=current_head_short,
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    written = write_change_impact_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"change-impact report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"changed_ref_count: {report.changed_ref_count}")
    print(f"impacted_requirements: {len(report.impacted_requirement_ids)}")
    print(f"impacted_tests: {len(report.impacted_test_id_or_refs)}")
    print(
        "impacted_design_or_interface_refs: "
        f"{len(report.impacted_design_or_interface_refs)}"
    )
    print(
        "impacted_runtime_boundary_refs: "
        f"{len(report.impacted_runtime_boundary_refs)}"
    )
    print(f"unmapped_changed_refs: {len(report.unmapped_changed_refs)}")
    print(f"unsafe_changed_refs: {len(report.unsafe_changed_refs)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0


def _load_json_report(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object report at {path}")
    return payload


def _cmd_architecture_candidates(
    *,
    instance_root: Path,
    yyyymmdd: str,
    coverage_report_path: Path | None,
    freshness_report_path: Path | None,
    change_impact_report_path: Path | None,
    current_head_short: str | None,
) -> int:
    """Write a local advisory architecture-candidate report via the CLI."""

    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_load_json_report(coverage_report_path),
        freshness_report=_load_json_report(freshness_report_path),
        change_impact_report=_load_json_report(change_impact_report_path),
        current_head_short=current_head_short,
    )
    report = build_architecture_candidate_report(inputs=inputs)
    written = write_architecture_candidate_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"architecture-candidates report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"candidate_count: {report.candidate_count}")
    print("advisory_only: true")
    print("requires_human_review: true")
    print("external_call_made: false")
    print("mutation_performed: false")
    print("raw_source_content_persisted: false")
    print("allowed_actions: advisory_only")
    return 0


def _load_portfolio_line_bundle(path: Path) -> tuple[EvidenceLineRef, ...]:
    """Load a caller-supplied portfolio bundle JSON into EvidenceLineRef tuples."""

    payload = _load_json_report(path)
    if payload is None:
        raise ValueError(f"portfolio bundle is required at {path}")
    refs = payload.get("line_refs")
    if not isinstance(refs, list):
        raise ValueError(
            "portfolio bundle must contain a 'line_refs' list"
        )
    line_refs: list[EvidenceLineRef] = []
    for raw in refs:
        if not isinstance(raw, dict):
            raise ValueError("each portfolio bundle line_ref must be an object")
        line_refs.append(EvidenceLineRef(**raw))
    return tuple(line_refs)


def _cmd_codebase_evidence_portfolio(
    *,
    instance_root: Path,
    yyyymmdd: str,
    line_bundle_path: Path,
    current_head_short: str | None,
) -> int:
    """Write a local advisory codebase evidence portfolio report via the CLI."""

    line_refs = _load_portfolio_line_bundle(line_bundle_path)
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date=yyyymmdd,
        line_refs=line_refs,
        current_head_short=current_head_short,
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    written = write_codebase_evidence_portfolio_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"codebase-evidence-portfolio report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"source_line_count: {len(report.source_lines)}")
    print(f"artifact_ref_count: {len(report.artifact_refs)}")
    print(f"schema_id_count: {len(report.schema_ids)}")
    print(f"quality_gate_ref_count: {len(report.quality_gate_refs)}")
    print(f"implemented_surface_count: {report.implemented_surface_count}")
    print(f"human_gated_surface_count: {report.human_gated_surface_count}")
    print(f"unsafe_ref_count: {len(report.unsafe_refs)}")
    print(f"unsafe_line_label_count: {len(report.unsafe_line_labels)}")
    print("advisory_only: true")
    print("requires_human_review: true")
    print("external_call_made: false")
    print("mutation_performed: false")
    print("raw_source_content_persisted: false")
    print("allowed_actions: advisory_only")
    return 0


def _load_oss_comparison_bundle(
    path: Path,
) -> tuple[LocalCodebaseLine, tuple[ApprovedOssSource, ...]]:
    """Load a caller-supplied OSS comparison bundle JSON."""

    payload = _load_json_report(path)
    if payload is None:
        raise ValueError(f"oss comparison bundle is required at {path}")
    local_line_raw = payload.get("local_line")
    if not isinstance(local_line_raw, dict):
        raise ValueError(
            "oss comparison bundle must contain a 'local_line' object"
        )
    sources_raw = payload.get("approved_sources", [])
    if not isinstance(sources_raw, list):
        raise ValueError(
            "oss comparison bundle 'approved_sources' must be a list"
        )
    sources: list[ApprovedOssSource] = []
    for raw in sources_raw:
        if not isinstance(raw, dict):
            raise ValueError(
                "each oss comparison bundle approved source must be an object"
            )
        sources.append(ApprovedOssSource(**raw))
    return LocalCodebaseLine(**local_line_raw), tuple(sources)


def _cmd_oss_comparison_adapter(
    *,
    instance_root: Path,
    yyyymmdd: str,
    bundle_path: Path,
    current_head_short: str | None,
) -> int:
    """Write a local advisory OSS comparison adapter report via the CLI."""

    local_line, approved_sources = _load_oss_comparison_bundle(bundle_path)
    request = OssComparisonRequest(
        instance_root=instance_root,
        date=yyyymmdd,
        local_line=local_line,
        approved_sources=approved_sources,
        current_head_short=current_head_short,
    )
    report = build_oss_comparison_report(request=request)
    written = write_oss_comparison_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"oss-comparison-adapter report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"compared_source_count: {report.compared_source_count}")
    print(f"union_category_count: {report.union_category_count}")
    print(
        f"intersection_category_count: {report.intersection_category_count}"
    )
    print(
        f"local_only_category_count: {report.local_only_category_count}"
    )
    print(f"oss_only_category_count: {report.oss_only_category_count}")
    print(f"unsafe_ref_count: {len(report.unsafe_refs)}")
    print(f"unsafe_source_id_count: {len(report.unsafe_source_ids)}")
    print(f"unsafe_line_label_count: {len(report.unsafe_line_labels)}")
    print("advisory_only: true")
    print("requires_human_review: true")
    print("external_call_made: false")
    print("mutation_performed: false")
    print("raw_source_content_persisted: false")
    print("live_external_action_authorized: false")
    print("allowed_actions: advisory_only")
    return 0


def _cmd_evaluate_code_analysis_contract(
    *,
    instance_root: Path,
    yyyymmdd: str,
    contract_ref: Path,
    question_type: str,
    coverage_report_path: Path | None,
    boundary_report_path: Path | None,
    freshness_report_path: Path | None,
    benchmark_report_path: Path | None,
    change_impact_report_path: Path | None,
    architecture_candidates_report_path: Path | None,
    human_approval_ref: str | None,
) -> int:
    """Evaluate a code-analysis pass-contract via the CLI."""

    entries = load_pass_contract_registry(contract_ref)
    if not entries:
        raise ValueError("contract registry is empty")
    entry = entries[0]
    summary = build_code_analysis_evidence_summary(
        question_type=question_type,
        coverage_report=_load_json_report(coverage_report_path),
        boundary_report=_load_json_report(boundary_report_path),
        freshness_report=_load_json_report(freshness_report_path),
        benchmark_report=_load_json_report(benchmark_report_path),
        change_impact_report=_load_json_report(change_impact_report_path),
        architecture_candidates_report=_load_json_report(
            architecture_candidates_report_path
        ),
    )
    result = evaluate_pass_contract(entry, summary)
    written = write_code_analysis_pass_contract_evaluation(
        instance_root=instance_root,
        date=yyyymmdd,
        contract_id=entry.contract_id,
        result=result,
        human_approval_ref=human_approval_ref,
    )
    print(
        f"evaluate-code-analysis-contract evaluation: json={written['json_ref']}"
    )
    print(f"markdown: {written['markdown_ref']}")
    print(f"contract_id: {entry.contract_id}")
    print(f"question_type: {question_type}")
    print(f"quality_gate: {result.quality_gate}")
    blockers_text = ",".join(result.blockers) if result.blockers else "none"
    print(f"blockers: {blockers_text}")
    print("advisory_only: true")
    print("requires_human_review: true")
    print("external_call_made: false")
    print("mutation_performed: false")
    print("raw_source_content_persisted: false")
    print("allowed_actions: advisory_only")
    return 0


def _cmd_validate_subagent_evidence_packet(
    *,
    task_path: Path,
    result_path: Path | None,
) -> int:
    """Validate caller-supplied subagent evidence task and optional result packet."""

    task_payload = _load_json_report(task_path)
    if task_payload is None:
        raise ValueError(f"expected JSON object task packet at {task_path}")
    task = validate_subagent_evidence_task_packet(task_payload)

    result = None
    if result_path is not None:
        result_payload = _load_json_report(result_path)
        if result_payload is None:
            raise ValueError(f"expected JSON object result packet at {result_path}")
        result = validate_subagent_evidence_result_packet(result_payload, task=task)

    artifact_ref_count = len(result.artifact_refs) if result is not None else 0
    source_ref_count = len(result.source_refs) if result is not None else 0
    print("validate-subagent-evidence-packet: ok")
    print(f"task_id: {task.task_id}")
    print(f"result_supplied: {'true' if result is not None else 'false'}")
    print(f"artifact_ref_count: {artifact_ref_count}")
    print(f"source_ref_count: {source_ref_count}")
    print("advisory_only: true")
    print("requires_human_review: true")
    print("external_call_made: false")
    print("mutation_performed: false")
    print("raw_source_content_persisted: false")
    print("allowed_actions: advisory_only")
    return 0


def _cmd_codebase_map_freshness_review(
    *,
    instance_root: Path,
    yyyymmdd: str,
    current_date_iso: str,
    max_age_days: int,
    current_head_short: str | None,
) -> int:
    """Write a local advisory codebase map freshness report via the CLI."""

    from datetime import date as _date

    parsed_current = _date.fromisoformat(current_date_iso)
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=parsed_current,
        max_age_days=max_age_days,
        current_head_short=current_head_short,
    )
    written = write_codebase_map_freshness_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"codebase map freshness report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"fresh_partitions: {len(report.fresh_partitions)}")
    print(f"stale_partitions: {len(report.stale_partitions)}")
    print(f"incomplete_partitions: {len(report.incomplete_partitions)}")
    print(f"unsafe_partitions: {len(report.unsafe_partitions)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0


def _cmd_runtime_boundary_check(
    *,
    instance_root: Path,
    yyyymmdd: str,
    refs: tuple[str, ...],
) -> int:
    """Write a local advisory runtime-boundary consistency report via the CLI."""

    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root, candidate_refs=refs
    )
    written = write_runtime_boundary_consistency_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"runtime-boundary consistency report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"ok_ref_count: {report.ok_ref_count}")
    print(f"unsafe_refs: {len(report.unsafe_refs)}")
    print(f"missing_files: {len(report.missing_files)}")
    print(f"malformed_json_refs: {len(report.malformed_json_refs)}")
    print(f"missing_markdown_pair_refs: {len(report.missing_markdown_pair_refs)}")
    print(f"missing_advisory_flag_refs: {len(report.missing_advisory_flag_refs)}")
    print(f"outside_runtime_boundary_refs: {len(report.outside_runtime_boundary_refs)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0


def _cmd_runtime_status_surface(
    *,
    instance_root: Path,
    yyyymmdd: str,
    workdir: Path | None,
    model: str | None,
    session: str | None,
    approval_state: str,
    context_budget: str,
    output_format: str,
) -> int:
    """Write a local/read-only runtime status surface packet."""

    instance = InstanceRoot(instance_root)
    packet = build_runtime_status_packet(
        instance_root=instance.root,
        yyyymmdd=yyyymmdd,
        workdir=workdir,
        model=model,
        session=session,
        approval_state=approval_state,
        context_budget=context_budget,
    )
    artifacts = write_runtime_status_surface(instance_root=instance.root, yyyymmdd=yyyymmdd, packet=packet)
    if output_format == "json":
        print(json.dumps({"packet": packet, "artifacts": artifacts}, ensure_ascii=False, indent=2, sort_keys=True))
    elif output_format == "markdown":
        print((instance.root / artifacts["markdown_ref"]).read_text(encoding="utf-8"), end="")
    else:
        print(render_runtime_status_text(packet, json_ref=artifacts["json_ref"]))
    return 0


def _load_dars_panel_config(path: Path) -> DarsCriticPanelConfig:
    """Parse a local DARS panel config JSON file into the runtime dataclass.

    M-CP-EXT-6: the loader is intentionally schema-strict on critic entries;
    unknown keys raise ``TypeError`` from ``DarsCriticRoleConfig(**item)`` so
    operators see a clear failure rather than a silent drop.
    """

    payload = json.loads(path.read_text(encoding="utf-8"))
    critics = [DarsCriticRoleConfig(**item) for item in payload.get("critics", [])]
    return DarsCriticPanelConfig(
        panel_id=payload["panel_id"],
        critics=critics,
        max_parallel_critics=int(payload.get("max_parallel_critics", 1)),
        failure_policy=payload.get("failure_policy", "continue_collect_errors"),
        advisory_only=bool(payload.get("advisory_only", True)),
        default_output_contract=payload.get("default_output_contract", "DarsCritiqueRecord"),
    )


def _load_live_dars_activation_packet(path: Path) -> LiveDarsPanelActivationPacket:
    """Load a local M-CP-LIVE-1 activation packet without credential lookup."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return LiveDarsPanelActivationPacket.model_validate(payload)


def _run_dars_panel_local_model_rehearsal(
    *,
    instance: InstanceRoot,
    yyyymmdd: str,
    request_id: str,
    panel_config: DarsCriticPanelConfig,
    candidate_ref: str,
    evidence_refs: list[str],
    local_model_endpoint: str,
    local_model: str,
    activation_packet_path: Path | None,
) -> dict[str, object]:
    """Run local-model panel rehearsal through the localhost-only adapter bridge."""

    if activation_packet_path is None:
        print("error: --activation-packet is required for --local-model-endpoint", file=sys.stderr)
        raise SystemExit(2)
    activation_packet = _load_live_dars_activation_packet(activation_packet_path)
    adapter = LocalModelPanelAdapter(instance=instance)
    task_statuses: dict[str, str] = {}
    local_model_boundary_refs: list[str] = []
    model_boundary_crossed = False
    local_model_call_made = False
    for index, critic in enumerate(panel_config.critics):
        task_id = f"TASK-{request_id}-{index:02d}-{critic.critic_id}"
        result = adapter.run_critic(
            activation_packet=activation_packet,
            critic_request=LocalModelCriticRequest(
                yyyymmdd=yyyymmdd,
                request_id=request_id,
                task_id=task_id,
                critic_id=critic.critic_id,
                critic_role=critic.critic_role,
                backend_id=critic.backend_id,
                model=local_model,
                endpoint=local_model_endpoint,
                candidate_ref=candidate_ref,
                evidence_refs=list(evidence_refs),
                rubric_ref=critic.rubric_ref,
                critique_dimensions=list(critic.critique_dimensions),
            ),
        )
        task_statuses[task_id] = result.status
        local_model_boundary_refs.append(result.boundary_ref)
        model_boundary_crossed = model_boundary_crossed or result.model_boundary_crossed
        local_model_call_made = local_model_call_made or result.local_model_call_made
    return {
        "request_id": request_id,
        "panel_id": panel_config.panel_id,
        "execution_mode": "local_model_rehearsal",
        "task_statuses": task_statuses,
        "local_model_boundary_refs": local_model_boundary_refs,
        "model_boundary_crossed": model_boundary_crossed,
        "local_model_call_made": local_model_call_made,
        "endpoint_scope": "localhost_only",
        "external_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "allowed_actions": "advisory_only",
    }


def _render_dars_panel_round_report_md(report: dict[str, object]) -> str:
    lines = [
        "# DARS panel round report",
        "",
        f"request_id: {report['request_id']}",
        f"panel_id: {report['panel_id']}",
        f"execution_mode: {report['execution_mode']}",
        f"advisory_only: {_bool_text(bool(report['advisory_only']))}",
        f"requires_human_review: {_bool_text(bool(report['requires_human_review']))}",
        f"external_call_made: {_bool_text(bool(report['external_call_made']))}",
        f"mutation_performed: {_bool_text(bool(report['mutation_performed']))}",
        f"publication_performed: {_bool_text(bool(report['publication_performed']))}",
        f"live_external_action_authorized: {_bool_text(bool(report['live_external_action_authorized']))}",
        "",
        "## Task statuses",
    ]
    task_statuses = report.get("task_statuses", {})
    if isinstance(task_statuses, dict):
        for task_id, status in task_statuses.items():
            lines.append(f"- {task_id}: {status}")
    lines.extend(["", "## Artifact refs"])
    for key in (
        "critique_refs",
        "local_model_boundary_refs",
        "execution_boundary_refs",
    ):
        refs = report.get(key, [])
        if refs:
            lines.append(f"- {key}:")
            if isinstance(refs, list):
                for ref in refs:
                    lines.append(f"  - {ref}")
    for key in ("synthesis_ref", "round_trace_ref"):
        if report.get(key):
            lines.append(f"- {key}: {report[key]}")
    return "\n".join(lines) + "\n"


def _write_dars_panel_round_report(
    *,
    instance: InstanceRoot,
    yyyymmdd: str,
    summary: dict[str, object],
) -> str:
    report = {
        "schema_id": "hisys.dars_panel.round_report",
        "schema_version": "0.1.0",
        **summary,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": bool(summary.get("external_call_made", False)),
        "mutation_performed": bool(summary.get("mutation_performed", False)),
        "publication_performed": bool(summary.get("publication_performed", False)),
        "live_external_action_authorized": False,
    }
    report_path = instance.reports_dir / "run-summaries" / yyyymmdd / "dars-panel-round-report.json"
    _write_json(report_path, report)
    report_path.with_suffix(".md").write_text(_render_dars_panel_round_report_md(report), encoding="utf-8")
    return _safe_relative_ref(Path(instance.root), report_path)


def _cmd_run_dars_panel(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    panel_config_path: Path,
    candidate_ref: str,
    evidence_refs: list[str],
    output_format: str,
    local_model_endpoint: str | None = None,
    local_model: str = "local-dars-panel",
    activation_packet_path: Path | None = None,
    write_report: bool = False,
) -> int:
    """Run the fixture-local DARS critic panel and print a bounded summary.

    M-CP-EXT-6: read-only wrapper over ``DarsCriticPanelRuntime.run_round`` with
    the default fixture policy. The command never enables external dispatch,
    never spawns workers, and never approves downstream decisions. Typed
    blocked/failed outcomes from individual critic tasks are surfaced in the
    summary but do not change the CLI exit code.
    """

    panel_config = _load_dars_panel_config(panel_config_path)
    instance = InstanceRoot(instance_root)
    if local_model_endpoint is not None:
        summary = _run_dars_panel_local_model_rehearsal(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            panel_config=panel_config,
            candidate_ref=candidate_ref,
            evidence_refs=list(evidence_refs),
            local_model_endpoint=local_model_endpoint,
            local_model=local_model,
            activation_packet_path=activation_packet_path,
        )
        if write_report:
            summary["report_ref"] = _write_dars_panel_round_report(
                instance=instance,
                yyyymmdd=yyyymmdd,
                summary=summary,
            )
        if output_format == "json":
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            lines = [
                f"request_id: {request_id}",
                f"panel_id: {panel_config.panel_id}",
                "execution_mode: local_model_rehearsal",
                f"model_boundary_crossed: {summary['model_boundary_crossed']}",
                f"local_model_call_made: {summary['local_model_call_made']}",
                "local_model_boundary_refs:",
            ]
            for ref in summary["local_model_boundary_refs"]:
                lines.append(f"  - {ref}")
            print("\n".join(lines))
        return 0
    runtime = DarsCriticPanelRuntime(instance=instance)
    result = runtime.run_round(
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        candidate_ref=candidate_ref,
        evidence_refs=list(evidence_refs),
        panel_config=panel_config,
    )
    execution_mode = "bounded_parallel" if panel_config.max_parallel_critics > 1 else "serial"
    task_statuses = {task.task_id: task.status for task in result.task_results}
    summary = {
        "request_id": request_id,
        "panel_id": panel_config.panel_id,
        "execution_mode": execution_mode,
        "task_statuses": task_statuses,
        "critique_refs": list(result.critique_refs),
        "synthesis_ref": result.synthesis_ref,
        "round_trace_ref": result.round_trace_ref,
        "execution_boundary_refs": list(result.execution_boundary_refs),
    }
    if write_report:
        summary["report_ref"] = _write_dars_panel_round_report(
            instance=instance,
            yyyymmdd=yyyymmdd,
            summary=summary,
        )
    if output_format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        lines = [
            f"request_id: {request_id}",
            f"panel_id: {panel_config.panel_id}",
            f"execution_mode: {execution_mode}",
            "task_statuses:",
        ]
        for task_id, status in task_statuses.items():
            lines.append(f"  - {task_id}: {status}")
        lines.append(f"synthesis_ref: {result.synthesis_ref}")
        lines.append(f"round_trace_ref: {result.round_trace_ref}")
        lines.append("critique_refs:")
        for ref in result.critique_refs:
            lines.append(f"  - {ref}")
        lines.append("execution_boundary_refs:")
        for ref in result.execution_boundary_refs:
            lines.append(f"  - {ref}")
        print("\n".join(lines))
    return 0


# DARS-CLOSE-2: Repo-relative location of the checked-in golden fixture for
# the fixture-local DARS panel productization demo path. The wrapper command
# ``run-dars-panel-golden`` resolves these files at runtime; the corresponding
# golden-contract test is ``test_run_dars_panel_cli_golden_fixture_writes_
# stable_operator_report``.
_DARS_PANEL_GOLDEN_BASIC_DIR = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "dars_panel"
    / "golden_basic"
)


def _cmd_run_dars_panel_golden(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    output_format: str,
) -> int:
    """Run the DARS critic panel against the checked-in golden fixture.

    Operator-facing wrapper that copies the locked golden fixture into the
    selected Hisys instance, rewrites instance-relative refs, and delegates to
    ``_cmd_run_dars_panel`` with ``write_report=True``. The wrapper never
    exposes the live-model rehearsal or activation-packet arguments; live
    external action remains outside this productization path.
    """

    if not _DARS_PANEL_GOLDEN_BASIC_DIR.is_dir():
        raise SystemExit(
            "run-dars-panel-golden: missing checked-in golden fixture at "
            f"{_DARS_PANEL_GOLDEN_BASIC_DIR}"
        )

    data_dir = instance_root / "data" / "dars-panel-fixtures" / yyyymmdd
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("candidate-001.json", "evidence-001.json", "rubric-001.md"):
        shutil.copy(_DARS_PANEL_GOLDEN_BASIC_DIR / filename, data_dir / filename)

    config_blueprint = json.loads(
        (_DARS_PANEL_GOLDEN_BASIC_DIR / "panel-config.json").read_text(encoding="utf-8")
    )
    rubric_ref = f"data/dars-panel-fixtures/{yyyymmdd}/rubric-001.md"
    for critic in config_blueprint["critics"]:
        critic["rubric_ref"] = rubric_ref
    config_path = instance_root / "panel-config.json"
    config_path.write_text(json.dumps(config_blueprint), encoding="utf-8")

    return _cmd_run_dars_panel(
        instance_root=instance_root,
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        panel_config_path=config_path,
        candidate_ref=f"data/dars-panel-fixtures/{yyyymmdd}/candidate-001.json",
        evidence_refs=[f"data/dars-panel-fixtures/{yyyymmdd}/evidence-001.json"],
        output_format=output_format,
        write_report=True,
    )


def _cmd_dars_panel_readiness(
    *,
    instance_root: Path,
    yyyymmdd: str,
    output_format: str,
    write_report: bool,
) -> int:
    """Print the locked DARS panel readiness/completion status.

    DARS-CLOSE-3: advisory-only surface that records which panel modes are
    fixture-complete, which are localhost-rehearsal-available but
    human-gated, and which remain unproven. No live action, credential
    lookup, mutation, publication, or remote push is introduced.
    """

    from hisys.operations.dars_panel_readiness import (
        build_dars_panel_readiness_status,
        format_text_status,
        write_dars_panel_readiness_report,
    )

    status = build_dars_panel_readiness_status()
    if write_report:
        status["report_ref"] = write_dars_panel_readiness_report(
            instance_root=instance_root,
            yyyymmdd=yyyymmdd,
            status=status,
        )

    if output_format == "json":
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_text_status(status))
    return 0


def _cmd_completion_status(
    *,
    instance_root: Path,
    yyyymmdd: str,
    validation_items: list[str],
    output_format: str,
) -> int:
    """Write a product completion/gate status report from runtime artifacts."""

    instance = InstanceRoot(instance_root)
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    investment_report = instance.runtime_boundary_dir / "investment-decisions" / yyyymmdd / "investment-decision-packet-report.json"
    evidence_report = report_dir / "investment-evidence-package-report.json"
    source_e2e_complete = evidence_report.exists() and investment_report.exists()
    dry_run_boundary_complete = False
    if investment_report.exists():
        payload = json.loads(investment_report.read_text(encoding="utf-8"))
        dry_run_boundary_complete = (
            payload.get("workflow") == "investment_decision_dry_run"
            and payload.get("fixture_backend_used") is False
            and payload.get("external_call_made") is False
            and payload.get("mutation_performed") is False
            and payload.get("execution_authorized") is False
            and payload.get("publication_or_live_action_approved") is False
        )
    components = [
        _component_status(
            component_id="investment_source_e2e",
            title="Source connector evidence to investment dry-run E2E",
            complete=source_e2e_complete,
            evidence_refs=[
                _safe_relative_ref(instance.root, evidence_report),
                _safe_relative_ref(instance.root, investment_report),
            ]
            if source_e2e_complete
            else [],
        ),
        _component_status(
            component_id="investment_dry_run_boundary",
            title="Investment dry-run no-action boundary",
            complete=dry_run_boundary_complete,
            evidence_refs=[_safe_relative_ref(instance.root, investment_report)] if investment_report.exists() else [],
        ),
        _component_status(
            component_id="live_external_action",
            title="Live external action remains gated",
            complete=False,
            evidence_refs=["High-impact Confirm Gate", "No Live External Action Until Harness Passes"],
            gated=True,
        ),
    ]
    missing = [component["component_id"] for component in components if component["status"] == "missing"]
    gates = [
        {
            "gate_id": "high_impact_confirm_gate",
            "status": "closed",
            "reason": "Live connectors, publication, execution, schema/security/governance changes require explicit confirmation.",
        },
        {
            "gate_id": "no_live_external_action_until_harness_passes",
            "status": "closed",
            "reason": "Current completion report records no live external action as executed.",
        },
    ]
    validation = _parse_validation_status(validation_items)
    validations_passed = bool(validation) and all(status == "passed" for status in validation.values())
    overall_status = "gated_release_candidate" if not missing and validations_passed else "incomplete"
    report = {
        "schema_id": "hisys.completion_status_report",
        "schema_version": "0.1.0",
        "date": yyyymmdd,
        "overall_status": overall_status,
        "components": components,
        "gaps": missing,
        "gates": gates,
        "validation": validation,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
        "execution_authorized": False,
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "hisys-completion-status.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = report_dir / "hisys-completion-status.md"
    md_path.write_text(
        "\n".join(
            [
                "# Hisys Completion Status",
                "",
                f"- overall_status: `{overall_status}`",
                f"- gaps: `{', '.join(missing) if missing else 'none'}`",
                "- live_external_action: `gated`",
                "- external_call_made: `false`",
                "- mutation_performed: `false`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if output_format == "markdown":
        print(md_path.read_text(encoding="utf-8"), end="")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hisys", description="Hisys runtime CLI.")
    parser.add_argument("--version", action="version", version=f"hisys {__version__}")
    sub = parser.add_subparsers(dest="command")

    validate = sub.add_parser("validate-config", help="validate a Hisys runtime instance config")
    validate.add_argument("--instance", required=True, help="runtime instance root containing config/")

    deploy_hermes = sub.add_parser(
        "deploy-hermes-tool",
        help="deploy a controlled Hisys wrapper/manifest under a Hermes tools directory",
    )
    deploy_hermes.add_argument("--source-root", type=Path, default=Path.cwd(), help="Hisys source repo root; defaults to current directory")
    deploy_hermes.add_argument("--target", type=Path, default=DEFAULT_HERMES_TOOL_ROOT, help="Hermes Hisys tool deployment directory")
    deploy_hermes.add_argument("--channel-id", help="optional Discord channel/thread id for generated config snippet")
    deploy_hermes.add_argument("--channel-name", help="optional human-readable channel/thread name for generated prompt")
    deploy_hermes.add_argument("--force", action="store_true", help="replace an existing Hisys Hermes tool deployment")

    deployment_status = sub.add_parser("deployment-status", help="inspect a Hermes Hisys tool snapshot deployment")
    deployment_status.add_argument("--target", type=Path, default=DEFAULT_HERMES_TOOL_ROOT, help="Hermes Hisys tool deployment directory")
    deployment_status.add_argument("--format", choices=["json", "text"], default="text")

    rollback_hermes = sub.add_parser("rollback-hermes-tool", help="move releases/current back to a previous Hisys Hermes tool snapshot")
    rollback_hermes.add_argument("--target", type=Path, default=DEFAULT_HERMES_TOOL_ROOT, help="Hermes Hisys tool deployment directory")
    rollback_choice = rollback_hermes.add_mutually_exclusive_group(required=True)
    rollback_choice.add_argument("--to-release", help="release id to promote to releases/current")
    rollback_choice.add_argument("--previous", action="store_true", help="rollback to the most recent non-current release")
    rollback_hermes.add_argument("--format", choices=["json", "text"], default="text")

    deploy_report = sub.add_parser("build-hermes-deploy-report", help="write a governed Hermes tool deployment report")
    deploy_report.add_argument("--target", type=Path, default=DEFAULT_HERMES_TOOL_ROOT, help="Hermes Hisys tool deployment directory")
    deploy_report.add_argument("--validation", action="append", default=[], help="validation status as name=status; repeatable")
    deploy_report.add_argument("--output", type=Path, help="optional JSON report output path")
    deploy_report.add_argument("--format", choices=["json", "text"], default="text")

    environment_init = sub.add_parser("environment-init", help="write host-local Hisys environment/vault registry config")
    environment_init.add_argument("--config", type=Path, default=DEFAULT_ENVIRONMENT_CONFIG, help="environment YAML config path")
    environment_init.add_argument("--host-id", required=True)
    environment_init.add_argument("--hisys-tool-root", type=Path, required=True)
    environment_init.add_argument("--hisys-source-repo", type=Path, required=True)
    environment_init.add_argument("--evidence-store-root", type=Path, required=True)
    environment_init.add_argument("--evidence-store-config", type=Path, required=True)
    environment_init.add_argument("--personal-vault-root", type=Path, required=True)
    environment_init.add_argument("--lab-vault-root", type=Path, required=True)
    environment_init.add_argument("--format", choices=["json", "text"], default="text")

    environment_status = sub.add_parser("environment-status", help="inspect Hisys host-local environment/vault registry config")
    environment_status.add_argument("--config", type=Path, default=DEFAULT_ENVIRONMENT_CONFIG, help="environment YAML config path")
    environment_status.add_argument("--format", choices=["json", "text"], default="text")

    store_init = sub.add_parser("evidence-store-init", help="initialize a governed Hisys evidence store config and layout")
    store_init.add_argument("--config", type=Path, required=True, help="store YAML config path")
    store_init.add_argument("--root", type=Path, required=True, help="evidence store root directory")
    store_init.add_argument("--store-id", default="hisys-evidence-store", help="logical store id")
    store_init.add_argument("--format", choices=["json", "text"], default="text")

    store_status = sub.add_parser("evidence-store-status", help="inspect Hisys evidence store safety/config status")
    store_status.add_argument("--config", type=Path, required=True, help="store YAML config path")
    store_status.add_argument("--format", choices=["json", "text"], default="text")

    store_import = sub.add_parser("evidence-store-import-investigation", help="copy investigation artifacts into governed evidence store layout")
    store_import.add_argument("--config", type=Path, required=True, help="store YAML config path")
    store_import.add_argument("--topic-id", required=True)
    store_import.add_argument("--topic-slug", required=True)
    store_import.add_argument("--investigation-id", required=True)
    store_import.add_argument("--date", required=True, help="YYYY-MM-DD investigation partition")
    store_import.add_argument("--include", action="append", required=True, help="file to copy; repeatable")
    store_import.add_argument("--approval-ref", help="human approval ref for store mutation")
    store_import.add_argument("--write", action="store_true", help="perform copy; without this only plans")
    store_import.add_argument("--format", choices=["json", "text"], default="text")

    stone_candidates = sub.add_parser("evidence-stone-candidates", help="propose Stone candidates from stored investigation evidence")
    stone_candidates.add_argument("--config", type=Path, required=True, help="store YAML config path")
    stone_candidates.add_argument("--topic-id", required=True)
    stone_candidates.add_argument("--topic-slug", required=True)
    stone_candidates.add_argument("--investigation-id", required=True)
    stone_candidates.add_argument("--output", type=Path, help="optional JSON candidates output path")
    stone_candidates.add_argument("--format", choices=["json", "text"], default="text")

    promote_stone = sub.add_parser("evidence-promote-stone", help="approval-gated promotion of a Stone candidate into canonical stones")
    promote_stone.add_argument("--config", type=Path, required=True, help="store YAML config path")
    promote_stone.add_argument("--candidate", type=Path, required=True, help="candidate JSON file or report containing stone_candidates")
    promote_stone.add_argument("--candidate-id", required=True, help="candidate id to promote")
    promote_stone.add_argument("--approval-ref", help="human approval ref for Stone write")
    promote_stone.add_argument("--write", action="store_true", help="perform Stone write; without this only plans")
    promote_stone.add_argument("--format", choices=["json", "text"], default="text")

    public_profile = sub.add_parser(
        "validate-public-browser-profile",
        help="validate a governed public browser launch profile",
    )
    public_profile.add_argument("--profile", type=Path, required=True, help="public browser profile YAML path")

    public_browser_run = sub.add_parser(
        "public-browser-run",
        help="run the governed public browser beta chain and write a public operator summary",
    )
    public_browser_run.add_argument("--instance", required=True, help="runtime instance root for outputs")
    public_browser_run.add_argument("--config", required=True, help="source-connectors.yaml path")
    public_browser_run.add_argument("--profile", type=Path, required=True, help="validated public browser profile YAML path")
    public_browser_run.add_argument("--date", required=True, help="YYYYMMDD output partition")
    public_browser_run.add_argument("--request-id", required=True, help="request id for public browser run")
    public_browser_run.add_argument("--topic", required=True, help="topic/question being investigated")
    public_browser_run.add_argument("--user-opinion", default="", help="operator context to carry into memo")
    public_browser_run.add_argument("--approval-ref", required=True, help="approval ref for read-only browser source access")
    public_browser_run.add_argument("--source-url", action="append", required=True, help="approved URL to visit; repeat for multiple pages")
    public_browser_run.add_argument("--follow-links", action="store_true", help="follow bounded same-domain technology/product detail links discovered from source pages")
    public_browser_run.add_argument("--max-follow-links-per-source", type=int, help="override public profile follow-link bound")
    public_browser_run.add_argument(
        "--orchestrator-corroborating-url",
        action="append",
        default=[],
        help="orchestrator-provided candidate URL for independent corroboration; recorded but not fetched unless promoted as a source URL",
    )

    public_readiness = sub.add_parser(
        "public-browser-readiness",
        help="check public browser beta profile/config/import readiness without live network access",
    )
    public_readiness.add_argument("--instance", required=True, help="runtime instance root for readiness report")
    public_readiness.add_argument("--config", required=True, help="source-connectors.yaml path")
    public_readiness.add_argument("--profile", type=Path, required=True, help="public browser profile YAML path")
    public_readiness.add_argument("--date", required=True, help="YYYYMMDD output partition")

    get_run_summary = sub.add_parser(
        "get-run-summary",
        help="print a public browser run summary artifact for agent consumption",
    )
    get_run_summary.add_argument("--instance", required=True, help="runtime instance root containing reports/")
    get_run_summary.add_argument("--date", required=True, help="YYYYMMDD run partition")
    get_run_summary.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="summary format to print",
    )

    list_run_artifacts = sub.add_parser(
        "list-run-artifacts",
        help="list safe relative artifact refs for a date/request id",
    )
    list_run_artifacts.add_argument("--instance", required=True, help="runtime instance root containing artifacts")
    list_run_artifacts.add_argument("--date", required=True, help="YYYYMMDD run partition")
    list_run_artifacts.add_argument("--request-id", help="optional request id filter")

    show_artifact = sub.add_parser(
        "show-artifact",
        help="print a safe relative JSON/Markdown artifact under the runtime instance",
    )
    show_artifact.add_argument("--instance", required=True, help="runtime instance root")
    show_artifact.add_argument("--ref", required=True, help="safe relative artifact ref to print")

    investment_packet = sub.add_parser(
        "build-investment-decision-packet",
        help="validate and persist a human-gated investment decision packet product artifact",
    )
    investment_packet.add_argument("--instance", required=True, help="runtime instance root for outputs")
    investment_packet.add_argument("--date", required=True, help="YYYYMMDD output partition")
    investment_packet.add_argument("--packet", required=True, help="InvestmentDecisionPacket JSON input path")
    investment_packet.add_argument("--weight-policy", help="optional InvestmentWeightPolicy JSON path to persist with the packet")

    investment_evidence = sub.add_parser(
        "build-investment-evidence-package",
        help="promote source connector evidence artifacts into an investment EvidencePackage for dry-run use",
    )
    investment_evidence.add_argument("--instance", required=True, help="runtime instance root for outputs")
    investment_evidence.add_argument("--date", required=True, help="YYYYMMDD output partition")
    investment_evidence.add_argument("--request-id", required=True, help="request id for the promotion run")
    investment_evidence.add_argument("--asset", required=True, help="asset name the evidence package supports")
    investment_evidence.add_argument("--source-access", required=True, help="SourceAccessRecord JSON artifact path")
    investment_evidence.add_argument("--source-evidence", required=True, help="SourceEvidenceItem JSON artifact path")

    completion_status = sub.add_parser("completion-status", help="write Hisys completion/gate status from runtime artifacts")
    completion_status.add_argument("--instance", required=True, help="Hisys instance root")
    completion_status.add_argument("--date", required=True, help="YYYYMMDD")
    completion_status.add_argument(
        "--validation",
        action="append",
        default=[],
        help="validation status as name=status, e.g. focused=passed; repeatable",
    )
    completion_status.add_argument("--format", choices=["json", "markdown"], default="json")

    traceability_coverage = sub.add_parser(
        "traceability-coverage",
        help="write local advisory traceability coverage report artifacts",
    )
    traceability_coverage.add_argument("--instance", required=True, help="Hisys instance root")
    traceability_coverage.add_argument("--date", required=True, help="YYYYMMDD report partition")
    traceability_coverage.add_argument("--repo", type=Path, default=Path.cwd(), help="repo root to scan; defaults to cwd")

    change_impact = sub.add_parser(
        "change-impact",
        help="write local advisory change-impact report artifacts",
    )
    change_impact.add_argument("--instance", required=True, help="Hisys instance root")
    change_impact.add_argument("--date", required=True, help="YYYYMMDD report partition")
    change_impact.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="repo root for traceability anchor loading; defaults to cwd",
    )
    change_impact.add_argument(
        "--changed-ref",
        action="append",
        default=[],
        help="repeatable relative changed file ref (caller-supplied)",
    )
    change_impact.add_argument(
        "--current-head-short",
        default=None,
        help="optional caller-supplied git HEAD short hash recorded verbatim",
    )

    architecture_candidates = sub.add_parser(
        "architecture-candidates",
        help="write local advisory architecture-candidate report artifacts",
    )
    architecture_candidates.add_argument(
        "--instance", required=True, help="Hisys instance root"
    )
    architecture_candidates.add_argument(
        "--date", required=True, help="YYYYMMDD report partition"
    )
    architecture_candidates.add_argument(
        "--coverage-report",
        default=None,
        help="optional explicit hisys.traceability.coverage.v1 JSON report path",
    )
    architecture_candidates.add_argument(
        "--freshness-report",
        default=None,
        help="optional explicit hisys.codebase_map.freshness.v1 JSON report path",
    )
    architecture_candidates.add_argument(
        "--change-impact-report",
        default=None,
        help="optional explicit hisys.change_impact.v1 JSON report path",
    )
    architecture_candidates.add_argument(
        "--current-head-short",
        default=None,
        help="optional caller-supplied git HEAD short hash recorded verbatim",
    )

    codebase_portfolio = sub.add_parser(
        "codebase-evidence-portfolio",
        help="write local advisory codebase evidence portfolio report artifacts",
    )
    codebase_portfolio.add_argument(
        "--instance", required=True, help="Hisys instance root"
    )
    codebase_portfolio.add_argument(
        "--date", required=True, help="YYYYMMDD report partition"
    )
    codebase_portfolio.add_argument(
        "--line-bundle",
        required=True,
        help="explicit caller-supplied JSON bundle path with a 'line_refs' list",
    )
    codebase_portfolio.add_argument(
        "--current-head-short",
        default=None,
        help="optional caller-supplied git HEAD short hash recorded verbatim",
    )

    oss_comparison_adapter = sub.add_parser(
        "oss-comparison-adapter",
        help="write local advisory approved-OSS comparison adapter report artifacts",
    )
    oss_comparison_adapter.add_argument(
        "--instance", required=True, help="Hisys instance root"
    )
    oss_comparison_adapter.add_argument(
        "--date", required=True, help="YYYYMMDD report partition"
    )
    oss_comparison_adapter.add_argument(
        "--bundle",
        required=True,
        help="explicit caller-supplied JSON bundle path with 'local_line' and 'approved_sources'",
    )
    oss_comparison_adapter.add_argument(
        "--current-head-short",
        default=None,
        help="optional caller-supplied git HEAD short hash recorded verbatim",
    )

    evaluate_code_analysis = sub.add_parser(
        "evaluate-code-analysis-contract",
        help="evaluate a code-analysis pass-contract against M21.1..M21.7 reports",
    )
    evaluate_code_analysis.add_argument(
        "--instance", required=True, help="Hisys instance root"
    )
    evaluate_code_analysis.add_argument(
        "--date", required=True, help="YYYYMMDD evaluation partition"
    )
    evaluate_code_analysis.add_argument(
        "--contract-ref",
        required=True,
        help="explicit caller-supplied pass-contract registry JSON path (first contract wins)",
    )
    evaluate_code_analysis.add_argument(
        "--question-type",
        required=True,
        choices=sorted(CODE_ANALYSIS_SUPPORTED_QUESTION_TYPES),
        help="code-analysis question type",
    )
    evaluate_code_analysis.add_argument(
        "--coverage-report",
        default=None,
        help="optional explicit hisys.traceability.coverage.v1 JSON report path",
    )
    evaluate_code_analysis.add_argument(
        "--boundary-report",
        default=None,
        help="optional explicit hisys.runtime_boundary.consistency.v1 JSON report path",
    )
    evaluate_code_analysis.add_argument(
        "--freshness-report",
        default=None,
        help="optional explicit hisys.codebase_map.freshness.v1 JSON report path",
    )
    evaluate_code_analysis.add_argument(
        "--benchmark-report",
        default=None,
        help="optional explicit hisys.codebase_regression.benchmark.v1 JSON report path",
    )
    evaluate_code_analysis.add_argument(
        "--change-impact-report",
        default=None,
        help="optional explicit hisys.change_impact.v1 JSON report path",
    )
    evaluate_code_analysis.add_argument(
        "--architecture-candidates-report",
        default=None,
        help="optional explicit hisys.architecture_candidates.v1 JSON report path",
    )
    evaluate_code_analysis.add_argument(
        "--human-approval-ref",
        default=None,
        help="optional caller-supplied human-approval token recorded verbatim",
    )

    validate_subagent_evidence_packet = sub.add_parser(
        "validate-subagent-evidence-packet",
        help="validate caller-supplied subagent evidence task and optional result packet",
    )
    validate_subagent_evidence_packet.add_argument(
        "--task",
        required=True,
        help="explicit caller-supplied subagent task packet JSON path",
    )
    validate_subagent_evidence_packet.add_argument(
        "--result",
        default=None,
        help="optional explicit caller-supplied subagent result packet JSON path",
    )

    codebase_map_freshness_review = sub.add_parser(
        "codebase-map-freshness-review",
        help="write local advisory codebase map freshness/drift report artifacts",
    )
    codebase_map_freshness_review.add_argument("--instance", required=True, help="Hisys instance root")
    codebase_map_freshness_review.add_argument("--date", required=True, help="YYYYMMDD report partition")
    codebase_map_freshness_review.add_argument(
        "--current-date",
        required=True,
        help="YYYY-MM-DD caller date used for freshness comparison",
    )
    codebase_map_freshness_review.add_argument(
        "--max-age-days",
        required=True,
        type=int,
        help="freshness threshold in days; partitions older than this are stale",
    )
    codebase_map_freshness_review.add_argument(
        "--current-head-short",
        default=None,
        help="optional caller-supplied git HEAD short hash recorded verbatim",
    )

    runtime_boundary_check = sub.add_parser(
        "runtime-boundary-check",
        help="write local advisory runtime-boundary consistency report artifacts",
    )
    runtime_boundary_check.add_argument("--instance", required=True, help="Hisys instance root")
    runtime_boundary_check.add_argument("--date", required=True, help="YYYYMMDD report partition")
    runtime_boundary_check.add_argument(
        "--ref",
        action="append",
        default=[],
        help="relative runtime-boundary ref under <instance>/runtime-boundary/; repeatable",
    )

    runtime_status_surface = sub.add_parser(
        "runtime-status-surface",
        help="write local redacted runtime status surface artifacts without external calls",
    )
    runtime_status_surface.add_argument("--instance", required=True, help="Hisys instance root")
    runtime_status_surface.add_argument("--date", required=True, help="YYYYMMDD")
    runtime_status_surface.add_argument("--workdir", type=Path, default=None, help="local workdir/repository to inspect; defaults to cwd")
    runtime_status_surface.add_argument("--model", default=None, help="optional current model label; credential-like values are redacted")
    runtime_status_surface.add_argument("--session", default=None, help="optional session label; credential-like values are redacted")
    runtime_status_surface.add_argument("--approval-state", default="unknown", help="current approval/gate state")
    runtime_status_surface.add_argument("--context-budget", default="unknown", help="current context/cost budget summary")
    runtime_status_surface.add_argument("--format", choices=["text", "json", "markdown"], default="text")

    run_dars_panel = sub.add_parser(
        "run-dars-panel",
        help="run the fixture-local DARS critic panel and persist advisory artifacts (read-only)",
    )
    run_dars_panel.add_argument("--instance", required=True, help="Hisys runtime instance root")
    run_dars_panel.add_argument("--date", required=True, help="YYYYMMDD run partition")
    run_dars_panel.add_argument("--request-id", required=True, help="request id slug for the round")
    run_dars_panel.add_argument("--panel-config", type=Path, required=True, help="local DARS panel config JSON path")
    run_dars_panel.add_argument("--candidate-ref", required=True, help="instance-relative candidate artifact ref")
    run_dars_panel.add_argument(
        "--evidence-ref",
        action="append",
        default=[],
        help="instance-relative evidence artifact ref; repeatable",
    )
    run_dars_panel.add_argument("--format", choices=["json", "text"], default="text")
    run_dars_panel.add_argument(
        "--local-model-endpoint",
        default=None,
        help="localhost-only OpenAI-compatible endpoint for controlled local model rehearsal",
    )
    run_dars_panel.add_argument(
        "--local-model",
        default="local-dars-panel",
        help="local model name sent to the localhost-only rehearsal endpoint",
    )
    run_dars_panel.add_argument(
        "--activation-packet",
        type=Path,
        default=None,
        help="M-CP-LIVE-1 activation packet JSON required for local model rehearsal",
    )
    run_dars_panel.add_argument(
        "--write-report",
        action="store_true",
        help="write an operator-facing advisory round report under reports/run-summaries/<date>",
    )

    run_dars_panel_golden = sub.add_parser(
        "run-dars-panel-golden",
        help=(
            "run the fixture-local DARS critic panel against the checked-in "
            "golden fixture and write the operator report (no live action)"
        ),
    )
    run_dars_panel_golden.add_argument(
        "--instance", required=True, help="Hisys runtime instance root"
    )
    run_dars_panel_golden.add_argument(
        "--date", required=True, help="YYYYMMDD run partition"
    )
    run_dars_panel_golden.add_argument(
        "--request-id", required=True, help="request id slug for the round"
    )
    run_dars_panel_golden.add_argument(
        "--format", choices=["json", "text"], default="text"
    )

    dars_panel_readiness = sub.add_parser(
        "dars-panel-readiness",
        help=(
            "report which DARS panel modes are fixture-complete, human-gated, "
            "or unproven; advisory-only, no live action"
        ),
    )
    dars_panel_readiness.add_argument(
        "--instance", required=True, help="Hisys runtime instance root"
    )
    dars_panel_readiness.add_argument(
        "--date", required=True, help="YYYYMMDD run partition"
    )
    dars_panel_readiness.add_argument(
        "--format", choices=["json", "text"], default="text"
    )
    dars_panel_readiness.add_argument(
        "--write-report",
        action="store_true",
        help="persist the readiness snapshot under reports/run-summaries/<date>",
    )

    spec_packet = sub.add_parser("build-spec-first-packet", help="write a spec-first run packet before governed agent work")
    spec_packet.add_argument("--instance", required=True, help="Hisys instance root")
    spec_packet.add_argument("--date", required=True, help="YYYYMMDD")
    spec_packet.add_argument("--packet-id", required=True, help="spec packet id")
    spec_packet.add_argument("--objective", required=True, help="bounded objective")
    spec_packet.add_argument("--scope", action="append", default=[], help="in-scope item; repeatable")
    spec_packet.add_argument("--non-goal", action="append", default=[], help="out-of-scope item; repeatable")
    spec_packet.add_argument("--allowed-action", action="append", default=[], help="allowed action category; repeatable")
    spec_packet.add_argument("--evidence-contract", action="append", default=[], help="evidence/traceability requirement; repeatable")
    spec_packet.add_argument("--expected-artifact", action="append", default=[], help="expected artifact ref; repeatable")
    spec_packet.add_argument("--gate-criterion", action="append", default=[], help="quality gate criterion; repeatable")
    spec_packet.add_argument("--human-approval-boundary", required=True, help="human gate boundary for consequential use")
    spec_packet.add_argument("--format", choices=["text", "json"], default="text")

    codebase_inventory = sub.add_parser(
        "build-codebase-inventory",
        help="build a deterministic local codebase inventory and persist JSON/Markdown artifacts",
    )
    codebase_inventory.add_argument("--repo", required=True, help="local repository root to inventory")
    codebase_inventory.add_argument("--instance", required=True, help="Hisys instance root for artifact output")
    codebase_inventory.add_argument("--date", required=True, help="YYYYMMDD")
    codebase_inventory.add_argument("--request-id", required=True, help="inventory request id slug, e.g. REQ-CODEBASE-001")
    codebase_inventory.add_argument("--scope", default=None, help="optional repo-relative subdirectory to restrict the walk")
    codebase_inventory.add_argument("--format", choices=["text", "json"], default="text")

    symbol_index_parser = sub.add_parser(
        "build-code-symbol-index",
        help="build a deterministic Python AST symbol index and persist JSON/Markdown artifacts",
    )
    symbol_index_parser.add_argument("--repo", required=True, help="local repository root to index")
    symbol_index_parser.add_argument("--instance", required=True, help="Hisys instance root for artifact output")
    symbol_index_parser.add_argument("--date", required=True, help="YYYYMMDD")
    symbol_index_parser.add_argument("--request-id", required=True, help="symbol index request id slug, e.g. REQ-CODEBASE-001")
    symbol_index_parser.add_argument("--scope", default=None, help="optional repo-relative subdirectory to restrict the walk")
    symbol_index_parser.add_argument("--format", choices=["text", "json"], default="text")

    risk_scan_parser = sub.add_parser(
        "scan-codebase-boundaries",
        help="scan a local repository for boundary-crossing call sites; findings are review evidence, not vulnerability verdicts",
    )
    risk_scan_parser.add_argument("--repo", required=True, help="local repository root to scan")
    risk_scan_parser.add_argument("--instance", required=True, help="Hisys instance root for artifact output")
    risk_scan_parser.add_argument("--date", required=True, help="YYYYMMDD")
    risk_scan_parser.add_argument("--request-id", required=True, help="risk-scan request id slug, e.g. REQ-CODEBASE-RISK-001")
    risk_scan_parser.add_argument("--scope", default=None, help="optional repo-relative subdirectory to restrict the walk")
    risk_scan_parser.add_argument("--format", choices=["text", "json"], default="text")

    scope_map_parser = sub.add_parser(
        "build-codebase-map",
        help="assemble a scope map and validation plan from local inventory and symbol-index refs",
    )
    scope_map_parser.add_argument("--instance", required=True, help="Hisys instance root for artifact output")
    scope_map_parser.add_argument("--date", required=True, help="YYYYMMDD")
    scope_map_parser.add_argument("--request-id", required=True, help="scope-map request id slug, e.g. REQ-CODEBASE-001")
    scope_map_parser.add_argument(
        "--inventory-ref",
        required=True,
        help="instance-relative path to an inventory JSON artifact previously written by build-codebase-inventory",
    )
    scope_map_parser.add_argument(
        "--symbol-index-ref",
        required=True,
        help="instance-relative path to a symbol-index JSON artifact previously written by build-code-symbol-index",
    )
    scope_map_parser.add_argument("--format", choices=["text", "json"], default="text")

    review_codebase = sub.add_parser(
        "review-codebase-analysis",
        help=(
            "review a codebase-analysis four-file bundle and persist the "
            "source-inspection decision packet; allowed decision values are "
            "only complete_for_human_review and blocked_needs_more_evidence"
        ),
    )
    review_codebase.add_argument("--instance", required=True, help="Hisys instance root for artifact output")
    review_codebase.add_argument("--date", required=True, help="YYYYMMDD")
    review_codebase.add_argument(
        "--request-id",
        required=True,
        help="decision request id slug, e.g. REQ-CODEBASE-DECISION-001",
    )
    review_codebase.add_argument(
        "--inventory-ref",
        required=True,
        help="instance-relative path to an inventory JSON artifact",
    )
    review_codebase.add_argument(
        "--symbol-index-ref",
        required=True,
        help="instance-relative path to a symbol-index JSON artifact",
    )
    review_codebase.add_argument(
        "--scope-map-ref",
        required=True,
        help="instance-relative path to a scope-map JSON artifact (with embedded validation plan)",
    )
    review_codebase.add_argument(
        "--risk-scan-ref",
        required=True,
        help="instance-relative path to a risk-scan JSON artifact",
    )
    review_codebase.add_argument(
        "--unresolved-blocker",
        action="append",
        default=[],
        help="unresolved blocker that gates the decision; repeatable",
    )
    review_codebase.add_argument("--format", choices=["text", "json"], default="text")

    finish_packet = sub.add_parser("build-finish-packet", help="write a finish packet separating completion from live approval")
    finish_packet.add_argument("--instance", required=True, help="Hisys instance root")
    finish_packet.add_argument("--date", required=True, help="YYYYMMDD")
    finish_packet.add_argument("--packet-id", required=True, help="finish packet id")
    finish_packet.add_argument("--spec-packet-ref", required=True, help="spec-first packet relative ref")
    finish_packet.add_argument("--completed-task", action="append", default=[], help="completed task; repeatable")
    finish_packet.add_argument("--validation-result", action="append", default=[], help="validation command/result; repeatable")
    finish_packet.add_argument("--review-finding", action="append", default=[], help="review finding; repeatable")
    finish_packet.add_argument("--unresolved-blocker", action="append", default=[], help="remaining blocker; repeatable")
    finish_packet.add_argument("--next-action", action="append", default=[], help="next action; repeatable")
    finish_packet.add_argument("--human-gate-state", required=True, help="current human gate state")
    finish_packet.add_argument("--decision", choices=["complete_for_human_review", "blocked_needs_more_evidence"], default="complete_for_human_review")
    finish_packet.add_argument("--format", choices=["text", "json"], default="text")

    release_readiness = sub.add_parser("release-readiness", help="write release-readiness evidence report")
    release_readiness.add_argument("--instance", required=True, help="Hisys instance root")
    release_readiness.add_argument("--date", required=True, help="YYYYMMDD")
    release_readiness.add_argument("--quality-gate", action="append", default=[], help="quality gate as NAME:pass|fail|blocked|not_run:EVIDENCE")
    release_readiness.add_argument("--trace-ref", action="append", default=[], help="HISYS-T-024 trace path reference")
    release_readiness.add_argument("--known-gap", action="append", default=[], help="known release gap")
    release_readiness.add_argument("--format", choices=["text", "json"], default="text")

    health_status = sub.add_parser("health-status", help="write local health status gate evidence")
    health_status.add_argument("--instance", required=True, help="Hisys instance root")
    health_status.add_argument("--date", required=True, help="YYYYMMDD")
    health_status.add_argument("--format", choices=["text", "json"], default="text")

    backup_runtime = sub.add_parser("backup-runtime", help="create controlled runtime backup gate evidence")
    backup_runtime.add_argument("--instance", required=True, help="Hisys instance root")
    backup_runtime.add_argument("--date", required=True, help="YYYYMMDD")
    backup_runtime.add_argument("--backup-id", required=True, help="backup artifact id")
    backup_runtime.add_argument("--format", choices=["text", "json"], default="text")

    restore_dry_run = sub.add_parser("restore-backup-dry-run", help="verify a backup archive without restore writes")
    restore_dry_run.add_argument("--archive", required=True, help="backup archive path")
    restore_dry_run.add_argument("--restore-target", required=True, help="target root to verify without writing")
    restore_dry_run.add_argument("--report-root", required=True, help="Hisys instance root for writing the dry-run report")
    restore_dry_run.add_argument("--date", required=True, help="YYYYMMDD")
    restore_dry_run.add_argument("--format", choices=["text", "json"], default="text")

    review_investment_packet = sub.add_parser(
        "review-investment-decision-packet",
        help="print a persisted investment decision packet operator summary",
    )
    review_investment_packet.add_argument("--instance", required=True, help="runtime instance root containing outputs")
    review_investment_packet.add_argument("--date", required=True, help="YYYYMMDD output partition")
    review_investment_packet.add_argument("--packet-id", required=True, help="InvestmentDecisionPacket packet_id")
    review_investment_packet.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="operator summary format to print",
    )

    investment_dry_run = sub.add_parser(
        "run-investment-decision-dry-run",
        help="assemble an investment decision packet from read-only evidence artifacts without a fixture backend",
    )
    investment_dry_run.add_argument("--instance", required=True, help="runtime instance root for outputs")
    investment_dry_run.add_argument("--date", required=True, help="YYYYMMDD output partition")
    investment_dry_run.add_argument("--asset", required=True, help="asset under review")
    investment_dry_run.add_argument("--instrument", action="append", required=True, help="instrument ref; repeat for multiple instruments")
    investment_dry_run.add_argument("--time-horizon", required=True, help="human-readable time horizon")
    investment_dry_run.add_argument("--evidence-package", action="append", required=True, help="read-only EvidencePackage artifact path; repeat for multiple packages")
    investment_dry_run.add_argument("--weight-policy", required=True, help="InvestmentWeightPolicy JSON path")

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
        required=False,
        default=[],
        help="source_id to investigate; repeat for multiple sources; optional when --orchestrator-harness supplies source_ids",
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
    investigate_memo.add_argument(
        "--orchestrator-harness",
        help="optional governed orchestrator-authored JSON harness with source_ids, agent_types, user_opinion, and rationale for Investigator",
    )

    investigate_domain = sub.add_parser(
        "investigate-domain",
        help="run local domain-general Hisys investigation from a JSON request",
    )
    investigate_domain.add_argument("--instance", required=True, help="runtime instance root for outputs")
    investigate_domain.add_argument("--request", required=True, help="DomainInvestigationRequest JSON path")
    investigate_domain.add_argument("--date", required=True, help="YYYYMMDD output partition")
    investigate_domain.add_argument("--pass-contract-registry", help="optional pass-contract registry JSON for domain/question evaluation")
    investigate_domain.add_argument("--question-type", help="question type for pass-contract lookup")
    investigate_domain.add_argument("--evidence-summary", help="optional evidence summary JSON for pass-contract evaluation")
    investigate_domain.add_argument(
        "--promote-pdf-source-access-ref",
        dest="promote_pdf_source_access_refs",
        action="append",
        default=[],
        help="explicit source-access ref for approved OA PDF evidence promotion; repeatable",
    )
    investigate_domain.add_argument(
        "--promote-pdf-source-evidence-ref",
        dest="promote_pdf_source_evidence_refs",
        action="append",
        default=[],
        help="explicit source-evidence ref for approved OA PDF evidence promotion; repeatable",
    )
    investigate_domain.add_argument(
        "--source-quote-ref",
        dest="source_quote_refs",
        action="append",
        default=[],
        help="explicit source-quote ref from promoted OA PDF quote extraction; repeatable",
    )
    investigate_domain.add_argument(
        "--claim-evidence-ledger-ref",
        dest="claim_evidence_ledger_refs",
        action="append",
        default=[],
        help="explicit claim-evidence ledger ref from quote-to-claim mapping; repeatable",
    )
    investigate_domain.add_argument(
        "--claim-evidence-summary-ref",
        dest="claim_evidence_summary_refs",
        action="append",
        default=[],
        help="explicit claim-evidence summary ref from advisory ledger aggregation; repeatable",
    )
    investigate_domain.add_argument(
        "--claim-coverage-gate-ref",
        dest="claim_coverage_gate_refs",
        action="append",
        default=[],
        help="explicit claim coverage gate ref for conditional manuscript-language gating; repeatable",
    )
    investigate_domain.add_argument(
        "--recommendation-claim-registry-ref",
        dest="recommendation_claim_registry_refs",
        action="append",
        default=[],
        help="explicit recommendation claim registry ref for conditional required-claim lineage; repeatable",
    )
    investigate_domain.add_argument(
        "--source-access-ref",
        dest="live_source_access_refs",
        action="append",
        default=[],
        help="explicit live source-access ref from an approved source connector; repeatable",
    )
    investigate_domain.add_argument(
        "--source-evidence-ref",
        dest="live_source_evidence_refs",
        action="append",
        default=[],
        help="explicit live source-evidence ref from an approved source connector; repeatable",
    )

    live_ideation = sub.add_parser(
        "live-ideation-run",
        help="run approved live-source ideation evidence through DARS and Chief Editor",
    )
    live_ideation.add_argument("--instance", required=True, help="runtime instance root for outputs")
    live_ideation.add_argument("--request", required=True, help="DomainInvestigationRequest JSON path")
    live_ideation.add_argument("--config", required=True, help="source-connectors.yaml path")
    live_ideation.add_argument("--date", required=True, help="YYYYMMDD output partition")
    live_ideation.add_argument("--doi", required=True, help="approved DOI for read-only metadata retrieval")
    live_ideation.add_argument("--approval-ref", required=True, help="approval ref authorizing live ideation source access")
    live_ideation.add_argument("--explicit-live-source-enable", action="store_true", help="operator live-source opt-in")
    live_ideation.add_argument("--metadata-fixture", help="local Crossref-style JSON fixture for tests/harnesses")

    live_pipeline = sub.add_parser(
        "live-ideation-persist",
        help="run approved live ideation, write approved Obsidian evidence, and Git-sync it",
    )
    live_pipeline.add_argument("--instance", required=True, help="runtime instance root for outputs")
    live_pipeline.add_argument("--request", required=True, help="DomainInvestigationRequest JSON path")
    live_pipeline.add_argument("--config", required=True, help="source-connectors.yaml path")
    live_pipeline.add_argument("--date", required=True, help="YYYYMMDD output partition")
    live_pipeline.add_argument("--doi", required=True, help="approved DOI for read-only metadata retrieval")
    live_pipeline.add_argument("--approval-ref", help="approval ref authorizing all pipeline stages; optional when a standing approval policy supplies it")
    live_pipeline.add_argument("--vault-root", required=True, help="target Obsidian vault root")
    live_pipeline.add_argument("--remote-name", default="origin", help="Git remote name for vault sync")
    live_pipeline.add_argument("--branch", default="main", help="Git branch for vault sync")
    live_pipeline.add_argument("--credential-ref", required=True, help="credential reference only; raw credentials are rejected")
    live_pipeline.add_argument("--commit-message", help="Git commit message for the approved ideation persistence")
    live_pipeline.add_argument("--explicit-live-source-enable", action="store_true", help="operator live-source opt-in")
    live_pipeline.add_argument("--explicit-live-write-enable", action="store_true", help="operator live-vault-write opt-in")
    live_pipeline.add_argument("--explicit-live-git-enable", action="store_true", help="operator live-Git-sync opt-in")
    live_pipeline.add_argument("--allow-real-obsidian-vault", action="store_true", help="allow /home/cbchoi/obsidian as target vault")
    live_pipeline.add_argument("--clean-git-status", action="store_true", help="operator confirms target vault Git status is clean except approved refs")
    live_pipeline.add_argument("--metadata-fixture", help="local Crossref-style JSON fixture for tests/harnesses")
    live_pipeline.add_argument("--standing-approval-policy", help="approved standing autonomous operating-envelope policy JSON")

    live_autonomy = sub.add_parser(
        "live-autonomy-run",
        help="run a standing-approved queue of live ideation persistence jobs",
    )
    live_autonomy.add_argument("--instance", required=True, help="runtime instance root for batch outputs")
    live_autonomy.add_argument("--queue", required=True, help="JSON queue with approved live ideation persistence entries")
    live_autonomy.add_argument("--config", required=True, help="source-connectors.yaml path")
    live_autonomy.add_argument("--date", required=True, help="YYYYMMDD output partition")
    live_autonomy.add_argument("--vault-root", required=True, help="target Obsidian vault root")
    live_autonomy.add_argument("--credential-ref", required=True, help="credential reference only; raw credentials are rejected")
    live_autonomy.add_argument("--standing-approval-policy", required=True, help="approved standing autonomous operating-envelope policy JSON")
    live_autonomy.add_argument("--remote-name", default="origin", help="Git remote name for vault sync")
    live_autonomy.add_argument("--branch", default="main", help="Git branch for vault sync")
    live_autonomy.add_argument("--allow-real-obsidian-vault", action="store_true", help="allow /home/cbchoi/obsidian as target vault if policy allows it")
    live_autonomy.add_argument("--clean-git-status", action="store_true", help="operator confirms target vault Git status is clean before batch execution")
    live_autonomy.add_argument("--max-items", type=int, help="optional maximum queue entries to execute")
    live_autonomy.add_argument("--ledger", help="optional queue idempotency/retry ledger JSON path; defaults under data/live-autonomy-ledgers")
    live_autonomy.add_argument("--max-retries", type=int, default=3, help="maximum retry attempts for retryable blocked entries")

    live_scheduler = sub.add_parser(
        "live-autonomy-tick",
        help="cron-ready scheduler tick that discovers and runs standing-approved live autonomy queues",
    )
    live_scheduler.add_argument("--instance", required=True, help="runtime instance root for scheduler outputs")
    live_scheduler.add_argument("--queue-dir", required=True, help="directory containing queue JSON files")
    live_scheduler.add_argument("--queue-glob", default="*.json", help="glob for queue JSON files; default: *.json")
    live_scheduler.add_argument("--config", required=True, help="source-connectors.yaml path")
    live_scheduler.add_argument("--date", required=True, help="YYYYMMDD output partition")
    live_scheduler.add_argument("--vault-root", required=True, help="target Obsidian vault root")
    live_scheduler.add_argument("--credential-ref", required=True, help="credential reference only; raw credentials are rejected")
    live_scheduler.add_argument("--standing-approval-policy", required=True, help="approved standing autonomous operating-envelope policy JSON")
    live_scheduler.add_argument("--remote-name", default="origin", help="Git remote name for vault sync")
    live_scheduler.add_argument("--branch", default="main", help="Git branch for vault sync")
    live_scheduler.add_argument("--allow-real-obsidian-vault", action="store_true", help="allow /home/cbchoi/obsidian as target vault if policy allows it")
    live_scheduler.add_argument("--clean-git-status", action="store_true", help="operator confirms target vault Git status is clean before queue execution")
    live_scheduler.add_argument("--max-queues", type=int, default=1, help="maximum queue files to process in this scheduler tick")
    live_scheduler.add_argument("--max-items", type=int, help="optional maximum queue entries to execute per queue")
    live_scheduler.add_argument("--ledger-dir", help="optional directory for per-queue ledgers; defaults under instance data")
    live_scheduler.add_argument("--max-retries", type=int, default=3, help="maximum retry attempts for retryable blocked entries")
    live_scheduler.add_argument("--queue-lifecycle", action="store_true", help="move queue files through incoming/active/done/attention/rejected handoff directories")
    live_scheduler.add_argument("--active-dir", help="queue lifecycle active directory; defaults to sibling active directory")
    live_scheduler.add_argument("--done-dir", help="queue lifecycle done directory; defaults to sibling done directory")
    live_scheduler.add_argument("--attention-dir", help="queue lifecycle attention directory; defaults to sibling attention directory")
    live_scheduler.add_argument("--rejected-dir", help="queue lifecycle rejected directory; defaults to sibling rejected directory")

    live_admission = sub.add_parser(
        "live-autonomy-admit",
        help="deterministically validate candidate live-autonomy queues into incoming or rejected handoff dirs",
    )
    live_admission.add_argument("--instance", required=True, help="runtime instance root for admission reports")
    live_admission.add_argument("--candidate-dir", required=True, help="directory containing candidate queue JSON files")
    live_admission.add_argument("--candidate-glob", default="*.json", help="glob for candidate queue JSON files; default: *.json")
    live_admission.add_argument("--incoming-dir", required=True, help="accepted incoming queue handoff directory")
    live_admission.add_argument("--rejected-dir", required=True, help="rejected queue handoff directory")
    live_admission.add_argument("--date", required=True, help="YYYYMMDD output partition")
    live_admission.add_argument("--max-candidates", type=int, default=10, help="maximum candidate queue files to validate in this admission tick")

    live_status = sub.add_parser(
        "live-autonomy-status",
        help="write a compact operator dashboard from existing live-autonomy reports and ledgers",
    )
    live_status.add_argument("--instance", required=True, help="runtime instance root containing reports and ledgers")
    live_status.add_argument("--date", required=True, help="YYYYMMDD output partition")
    live_status.add_argument("--ledger-dir", help="optional ledger directory; defaults to data/live-autonomy-ledgers/<date>")

    plan_sources = sub.add_parser(
        "plan-source-connectors",
        help="dry-run plan governed source connectors for a domain investigation request",
    )
    plan_sources.add_argument("--instance", required=True, help="runtime instance root for outputs")
    plan_sources.add_argument("--request", required=True, help="DomainInvestigationRequest JSON path")
    plan_sources.add_argument("--config", required=True, help="source-connectors.yaml path")
    plan_sources.add_argument("--date", required=True, help="YYYYMMDD output partition")

    source_preflight = sub.add_parser(
        "source-connector-preflight",
        help="evaluate approved read-only source connector readiness without executing the connector",
    )
    source_preflight.add_argument("--instance", required=True, help="runtime instance root for outputs")
    source_preflight.add_argument("--config", required=True, help="source-connectors.yaml path")
    source_preflight.add_argument("--date", required=True, help="YYYYMMDD output partition")
    source_preflight.add_argument("--request-id", required=True, help="request id for the preflight")
    source_preflight.add_argument("--connector-id", required=True, help="connector id to preflight")
    source_preflight.add_argument("--approval-ref", help="approval ref for planned read-only external access")
    source_preflight.add_argument("--requested-domain", help="domain that a later run would access")
    source_preflight.add_argument("--requested-action", action="append", default=None, help="requested action; defaults to read")
    source_preflight.add_argument("--provider-url-ref", help="provider endpoint ref to preserve without resolving")
    source_preflight.add_argument("--preflight-only", action="store_true", help="required marker that this command performs no connector execution")

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
    smoke_source.add_argument("--query", help="topic/search query for governed general web search smoke")
    smoke_source.add_argument("--transport-fixture-search", help="local JSON fixture used as injected transport for tested search smoke")
    smoke_source.add_argument(
        "--license-signal",
        choices=["open_access", "closed", "unknown", "not_applicable"],
        default="unknown",
        help="license/open-access signal required for PDF smoke gating",
    )
    smoke_source.add_argument("--approval-ref", help="manual approval ref required for live smoke")
    smoke_source.add_argument("--transport-fixture-pdf", help="local PDF fixture used as injected transport for tested manual PDF smoke")
    smoke_source.add_argument("--browser-fixture-html", help="local HTML fixture used as injected page for tested Playwright browser smoke")
    smoke_source.add_argument("--dry-run", action="store_true", help="write blocked/dry-run evidence only; no external call")

    browser_investigate = sub.add_parser(
        "browser-investigate-topic",
        help="collect approved company/publisher pages with governed Playwright and write actual-data evidence/memo",
    )
    browser_investigate.add_argument("--instance", required=True, help="runtime instance root for outputs")
    browser_investigate.add_argument("--config", required=True, help="source-connectors.yaml path")
    browser_investigate.add_argument("--date", required=True, help="YYYYMMDD output partition")
    browser_investigate.add_argument("--request-id", required=True, help="request id for browser investigation")
    browser_investigate.add_argument("--topic", required=True, help="topic/question being investigated")
    browser_investigate.add_argument("--user-opinion", default="", help="operator context to carry into memo")
    browser_investigate.add_argument("--approval-ref", required=True, help="approval ref for read-only browser source access")
    browser_investigate.add_argument("--source-url", action="append", required=True, help="approved URL to visit; repeat for multiple pages")
    browser_investigate.add_argument(
        "--orchestrator-decide-domains",
        action="store_true",
        help="derive a scoped browser domain allowlist from the orchestrator-selected source URLs and persist the decision",
    )
    browser_investigate.add_argument("--browser-fixture-html", action="append", default=[], help="local HTML fixture paired by order with --source-url for deterministic tests")
    browser_investigate.add_argument("--follow-links", action="store_true", help="follow bounded same-domain technology/product detail links discovered from source pages")
    browser_investigate.add_argument("--max-follow-links-per-source", type=int, default=0, help="maximum discovered links to follow per source URL when --follow-links is set")
    browser_investigate.add_argument(
        "--orchestrator-corroborating-url",
        action="append",
        default=[],
        help="orchestrator-provided candidate URL for independent corroboration; recorded but not fetched unless separately promoted as a source URL",
    )
    browser_review = sub.add_parser(
        "review-browser-investigation",
        help="run Chief Editor readiness review over a browser investigation report",
    )
    browser_review.add_argument("--instance", required=True, help="runtime instance root containing browser investigation outputs")
    browser_review.add_argument("--date", required=True, help="YYYYMMDD review partition")
    browser_review.add_argument("--browser-investigation-report-ref", required=True, help="relative ref to browser-investigation-report.json")
    browser_review.add_argument("--producer-id", default="chief-editor-browser-review-cli", help="Chief Editor browser review producer id")

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

    extract_pdf_quotes = sub.add_parser(
        "extract-pdf-quotes",
        help="extract quote-only records from explicit promoted OA PDF evidence refs",
    )
    extract_pdf_quotes.add_argument("--instance", required=True, help="runtime instance root for outputs")
    extract_pdf_quotes.add_argument("--date", required=True, help="YYYYMMDD output partition")
    extract_pdf_quotes.add_argument("--request-id", required=True, help="request id for quote extraction")
    extract_pdf_quotes.add_argument(
        "--promoted-pdf-evidence-ref",
        action="append",
        required=True,
        help="explicit promoted PDF source-evidence ref; repeat for multiple refs",
    )

    claim_ledger = sub.add_parser(
        "build-claim-evidence-ledger",
        help="map explicit source quote refs to advisory claim evidence ledger records",
    )
    claim_ledger.add_argument("--instance", required=True, help="runtime instance root for outputs")
    claim_ledger.add_argument("--date", required=True, help="YYYYMMDD output partition")
    claim_ledger.add_argument("--request-id", required=True, help="request id for claim evidence ledger")
    claim_ledger.add_argument("--claim-id", required=True, help="claim id being mapped")
    claim_ledger.add_argument("--claim-text", required=True, help="claim text being mapped")
    claim_ledger.add_argument("--relation", required=True, choices=["support", "contradict", "needs_evidence"])
    claim_ledger.add_argument("--rationale", required=True, help="advisory mapping rationale")
    claim_ledger.add_argument(
        "--source-quote-ref",
        action="append",
        required=True,
        help="explicit source quote ref; repeat for multiple refs",
    )

    claim_summary = sub.add_parser(
        "build-claim-evidence-summary",
        help="aggregate explicit claim evidence ledger refs into advisory evidence balance summaries",
    )
    claim_summary.add_argument("--instance", required=True, help="runtime instance root for outputs")
    claim_summary.add_argument("--date", required=True, help="YYYYMMDD output partition")
    claim_summary.add_argument("--request-id", required=True, help="request id for claim evidence summary")
    claim_summary.add_argument("--claim-id", required=True, help="claim id being summarized")
    claim_summary.add_argument(
        "--claim-evidence-ledger-ref",
        action="append",
        required=True,
        help="explicit claim evidence ledger ref; repeat for multiple refs",
    )

    coverage_gate = sub.add_parser(
        "build-claim-coverage-gate",
        help="gate manuscript-facing claim language on explicit claim evidence summaries",
    )
    coverage_gate.add_argument("--instance", required=True, help="runtime instance root for outputs")
    coverage_gate.add_argument("--date", required=True, help="YYYYMMDD output partition")
    coverage_gate.add_argument("--request-id", required=True, help="request id for claim coverage gate")
    coverage_gate.add_argument(
        "--required-claim-id",
        action="append",
        required=True,
        help="required recommendation claim id; repeat for multiple required claims",
    )
    coverage_gate.add_argument(
        "--claim-evidence-summary-ref",
        action="append",
        required=True,
        help="explicit claim evidence summary ref; repeat for multiple refs",
    )

    recommendation_registry = sub.add_parser(
        "build-recommendation-claim-registry",
        help="register controlled required recommendation claims for Live-K coverage gates",
    )
    recommendation_registry.add_argument("--instance", required=True, help="runtime instance root for outputs")
    recommendation_registry.add_argument("--date", required=True, help="YYYYMMDD output partition")
    recommendation_registry.add_argument("--request-id", required=True, help="request id for recommendation claim registry")
    recommendation_registry.add_argument("--recommendation-text", required=True, help="explicit recommendation text being registered")
    recommendation_registry.add_argument(
        "--claim-text",
        action="append",
        required=True,
        help="required recommendation claim text; repeat for multiple claims",
    )
    recommendation_registry.add_argument(
        "--source-recommendation-ref",
        help="optional runtime-boundary recommendation artifact ref",
    )

    search_topic = sub.add_parser(
        "search-topic",
        help="approved governed topic search that writes source evidence and an Investigator harness",
    )
    search_topic.add_argument("--instance", required=True, help="runtime instance root for outputs")
    search_topic.add_argument("--config", required=True, help="source connector config YAML")
    search_topic.add_argument("--date", required=True, help="YYYYMMDD source connector partition")
    search_topic.add_argument("--request-id", required=True, help="stable request id")
    search_topic.add_argument("--topic", required=True, help="topic/search query")
    search_topic.add_argument("--user-opinion", default="", help="optional user opinion to preserve in the Investigator harness")
    search_topic.add_argument("--approval-ref", help="manual/standing approval reference")
    search_topic.add_argument("--transport-fixture-search", help="local JSON fixture used as injected search transport for tests/smoke")
    search_topic.add_argument("--provider", default="generic_json", help="approved search provider adapter name")
    search_topic.add_argument("--provider-url-ref", help="credential-style ref to provider endpoint URL, e.g. env:HISYS_SEARCH_PROVIDER_URL")
    search_topic.add_argument("--credential-ref", help="optional credential ref for provider API token; never persisted as a value")
    search_topic.add_argument("--provider-response-fixture", help="local provider JSON response fixture for deterministic adapter tests")

    vault_plan = sub.add_parser(
        "vault-plan",
        help="plan an Obsidian live-research topic/investigation layout without writing the vault",
    )
    vault_plan.add_argument("--instance", required=True, help="runtime instance root for dry-run planner artifacts")
    vault_plan.add_argument("--registry", required=True, help="Obsidian live-research registry JSON path")
    vault_plan.add_argument("--date", required=True, help="YYYYMMDD output partition")
    vault_plan.add_argument("--time", required=True, help="HHMM investigation timestamp component")
    vault_plan.add_argument("--request-id", required=True, help="request id for vault planning")
    vault_plan.add_argument("--topic-title", required=True, help="submitted topic title")
    vault_plan.add_argument("--domain", required=True, help="submitted topic domain")
    vault_plan.add_argument("--objective", required=True, help="submitted investigation objective")
    vault_plan.add_argument("--dry-run", action="store_true", required=True, help="required; compute plan only and write no vault files")

    vault_validate = sub.add_parser(
        "vault-validate",
        help="validate Obsidian live-research manifests without writing the vault",
    )
    vault_validate.add_argument("--instance", required=True, help="runtime instance root for validation reports")
    vault_validate.add_argument("--date", required=True, help="YYYYMMDD report partition")
    vault_validate.add_argument("--registry", required=True, help="registry.json path")
    vault_validate.add_argument("--topic-manifest", required=True, help="topic-manifest.json path")
    vault_validate.add_argument("--investigation-manifest", required=True, help="investigation-manifest.json path")
    vault_validate.add_argument("--gatekeeper-decision", required=True, help="gatekeeper decision JSON path")

    vault_template_plan = sub.add_parser(
        "vault-template-plan",
        help="plan Obsidian memo ontology templates and indexes without writing the vault",
    )
    vault_template_plan.add_argument("--instance", required=True, help="runtime instance root for template plan reports")
    vault_template_plan.add_argument("--date", required=True, help="YYYYMMDD report partition")
    vault_template_plan.add_argument("--request-id", required=True, help="request id for template planning")

    vault_apply = sub.add_parser(
        "vault-apply",
        help="apply an Obsidian vault plan to an explicit fixture vault root only",
    )
    vault_apply.add_argument("--instance", required=True, help="runtime instance root for apply reports")
    vault_apply.add_argument("--date", required=True, help="YYYYMMDD report partition")
    vault_apply.add_argument("--plan", required=True, help="vault-plan JSON path")
    vault_apply.add_argument("--target-vault-root", required=True, help="explicit fixture vault root to write")
    vault_apply.add_argument("--approval-ref", help="required human approval ref for fixture writes")
    vault_apply.add_argument("--fixture-vault-only", action="store_true", help="required; refuses real Obsidian vault writes")

    vault_roundtrip = sub.add_parser(
        "vault-roundtrip-validate",
        help="validate plan -> fixture vault apply roundtrip without live vault writes",
    )
    vault_roundtrip.add_argument("--instance", required=True, help="runtime instance root for roundtrip reports")
    vault_roundtrip.add_argument("--date", required=True, help="YYYYMMDD report partition")
    vault_roundtrip.add_argument("--plan", required=True, help="vault-plan JSON path")
    vault_roundtrip.add_argument("--fixture-vault-root", required=True, help="fixture vault root to validate")
    vault_roundtrip.add_argument("--apply-report", required=True, help="vault-apply report JSON path")

    live_preflight = sub.add_parser(
        "vault-live-preflight",
        help="inspect a candidate live Obsidian vault without writing to it",
    )
    live_preflight.add_argument("--instance", required=True, help="runtime instance root for preflight reports")
    live_preflight.add_argument("--date", required=True, help="YYYYMMDD report partition")
    live_preflight.add_argument("--request-id", required=True, help="request id for preflight")
    live_preflight.add_argument("--vault-root", required=True, help="candidate Obsidian vault root")

    live_approval = sub.add_parser(
        "vault-live-approval-package",
        help="prepare a human approval package for a future live vault write without enabling it",
    )
    live_approval.add_argument("--instance", required=True, help="runtime instance root for approval package artifacts")
    live_approval.add_argument("--date", required=True, help="YYYYMMDD report partition")
    live_approval.add_argument("--request-id", required=True, help="request id for approval package")
    live_approval.add_argument("--preflight-report", required=True, help="vault-live-preflight JSON report path")
    live_approval.add_argument("--plan", required=True, help="vault-plan JSON path")
    live_approval.add_argument("--operator-id", required=True, help="operator requesting approval package")
    live_approval.add_argument("--rationale", required=True, help="human-readable rationale")

    live_write_gate = sub.add_parser(
        "vault-live-write-gate",
        help="evaluate final live vault write gates without implementing or performing writes",
    )
    live_write_gate.add_argument("--instance", required=True, help="runtime instance root for gate reports")
    live_write_gate.add_argument("--date", required=True, help="YYYYMMDD report partition")
    live_write_gate.add_argument("--request-id", required=True, help="request id for write gate")
    live_write_gate.add_argument("--approval-package", required=True, help="vault-live-approval-package JSON path")
    live_write_gate.add_argument("--approval-ref", help="human approval reference outside prompt text")
    live_write_gate.add_argument("--explicit-live-write-enable", action="store_true", help="still blocked until a writer is explicitly implemented")
    live_write_gate.add_argument("--clean-git-status", action="store_true", help="operator/git precondition signal")

    live_transaction = sub.add_parser(
        "vault-live-transaction-plan",
        help="plan a non-executable live vault transaction manifest without writing",
    )
    live_transaction.add_argument("--instance", required=True, help="runtime instance root for transaction plan artifacts")
    live_transaction.add_argument("--date", required=True, help="YYYYMMDD report partition")
    live_transaction.add_argument("--request-id", required=True, help="request id for transaction plan")
    live_transaction.add_argument("--approval-package", required=True, help="vault-live-approval-package JSON path")
    live_transaction.add_argument("--write-gate-report", required=True, help="vault-live-write-gate JSON report path")

    live_rehearsal = sub.add_parser(
        "vault-live-transaction-rehearse",
        help="rehearse a live transaction manifest against a fixture vault only",
    )
    live_rehearsal.add_argument("--instance", required=True, help="runtime instance root for rehearsal reports")
    live_rehearsal.add_argument("--date", required=True, help="YYYYMMDD report partition")
    live_rehearsal.add_argument("--transaction-plan", required=True, help="vault-live-transaction-plan JSON path")
    live_rehearsal.add_argument("--fixture-vault-root", required=True, help="fixture vault root to write")
    live_rehearsal.add_argument("--approval-ref", help="required rehearsal approval ref")
    live_rehearsal.add_argument("--fixture-vault-only", action="store_true", help="required; refuses real Obsidian vault")

    live_apply = sub.add_parser(
        "vault-live-transaction-apply",
        help="apply an approved transaction to a vault root with explicit live-write gates",
    )
    live_apply.add_argument("--instance", required=True, help="runtime instance root for apply reports")
    live_apply.add_argument("--date", required=True, help="YYYYMMDD report partition")
    live_apply.add_argument("--transaction-plan", required=True, help="vault-live-transaction-plan JSON path")
    live_apply.add_argument("--vault-root", required=True, help="approved vault root to mutate")
    live_apply.add_argument("--approval-ref", help="required live-apply approval ref")
    live_apply.add_argument("--explicit-live-write-enable", action="store_true", help="required explicit write enable switch")
    live_apply.add_argument("--allow-real-obsidian-vault", action="store_true", help="required only for /home/cbchoi/obsidian")
    live_apply.add_argument("--clean-git-status", action="store_true", help="operator-confirmed clean git status signal")

    live_status = sub.add_parser(
        "vault-live-config-status",
        help="write the Live-Obsidian-Config completion status report",
    )
    live_status.add_argument("--instance", required=True, help="runtime instance root for status report")
    live_status.add_argument("--date", required=True, help="YYYYMMDD report partition")
    live_status.add_argument("--request-id", required=True, help="request id for status report")

    topic_gatekeeper = sub.add_parser(
        "vault-topic-gatekeeper",
        help="write a read-only evidence-citing topic routing decision",
    )
    topic_gatekeeper.add_argument("--instance", required=True, help="runtime instance root for decision report")
    topic_gatekeeper.add_argument("--date", required=True, help="YYYYMMDD report partition")
    topic_gatekeeper.add_argument("--request-id", required=True, help="request id for topic gatekeeper decision")
    topic_gatekeeper.add_argument("--registry", required=True, help="topic registry JSON path")
    topic_gatekeeper.add_argument("--proposed-topic", required=True, help="proposed topic JSON path")

    evidence_promotion = sub.add_parser(
        "vault-evidence-promotion-plan",
        help="plan promotion of evidence refs into topic canonical indexes without writing the vault",
    )
    evidence_promotion.add_argument("--instance", required=True, help="runtime instance root for promotion plan")
    evidence_promotion.add_argument("--date", required=True, help="YYYYMMDD report partition")
    evidence_promotion.add_argument("--request", required=True, help="evidence promotion request JSON path")

    obsidian_status = sub.add_parser(
        "vault-obsidian-milestone-status",
        help="write the completed Obsidian milestone status report",
    )
    obsidian_status.add_argument("--instance", required=True, help="runtime instance root for milestone report")
    obsidian_status.add_argument("--date", required=True, help="YYYYMMDD report partition")
    obsidian_status.add_argument("--request-id", required=True, help="request id for milestone status report")

    git_fixture_init = sub.add_parser(
        "vault-git-fixture-init",
        help="execute an Obsidian Git initialization plan against fixture Git repos only",
    )
    git_fixture_init.add_argument("--instance", required=True, help="runtime instance root for Git fixture execution report")
    git_fixture_init.add_argument("--date", required=True, help="YYYYMMDD report partition")
    git_fixture_init.add_argument("--plan", required=True, help="obsidian git initialization plan JSON path")
    git_fixture_init.add_argument("--fixture-vault-root", required=True, help="fixture vault root to initialize")
    git_fixture_init.add_argument("--fixture-remote-root", required=True, help="local bare fixture Git remote path")
    git_fixture_init.add_argument("--fixture-git-only", action="store_true", help="required; refuses live/non-fixture Git execution")

    git_fixture_sync = sub.add_parser(
        "vault-git-fixture-sync",
        help="execute an Obsidian Git sync plan against fixture Git repos only",
    )
    git_fixture_sync.add_argument("--instance", required=True, help="runtime instance root for Git fixture execution report")
    git_fixture_sync.add_argument("--date", required=True, help="YYYYMMDD report partition")
    git_fixture_sync.add_argument("--plan", required=True, help="obsidian git sync plan JSON path")
    git_fixture_sync.add_argument("--fixture-vault-root", required=True, help="fixture vault root to sync")
    git_fixture_sync.add_argument("--fixture-remote-root", required=True, help="local bare fixture Git remote path")
    git_fixture_sync.add_argument("--fixture-git-only", action="store_true", help="required; refuses live/non-fixture Git execution")

    git_live_sync = sub.add_parser(
        "vault-git-live-sync",
        help="execute an approved Obsidian Git sync plan against the configured vault remote",
    )
    git_live_sync.add_argument("--instance", required=True, help="runtime instance root for Git live execution report")
    git_live_sync.add_argument("--date", required=True, help="YYYYMMDD report partition")
    git_live_sync.add_argument("--plan", required=True, help="obsidian git sync plan JSON path")
    git_live_sync.add_argument("--vault-root", required=True, help="approved vault root to mutate and push")
    git_live_sync.add_argument("--approval-ref", help="required approval ref; must match the sync plan push approval")
    git_live_sync.add_argument("--explicit-live-git-enable", action="store_true", help="required explicit live Git mutation/push switch")
    git_live_sync.add_argument("--allow-real-obsidian-vault", action="store_true", help="required only for /home/cbchoi/obsidian")
    git_live_sync.add_argument("--clean-git-status", action="store_true", help="operator-confirmed clean/scoped git status signal")

    topic_transition = sub.add_parser(
        "vault-topic-transition-plan",
        help="plan non-destructive topic merge/split transitions without writing the vault",
    )
    topic_transition.add_argument("--instance", required=True, help="runtime instance root for transition plan artifacts")
    topic_transition.add_argument("--date", required=True, help="YYYYMMDD report partition")
    topic_transition.add_argument("--request-id", required=True, help="request id for transition planning")
    topic_transition.add_argument("--action", required=True, choices=["merge_with_existing_topic", "split_topic_recommended"], help="topic identity transition action")
    topic_transition.add_argument("--source-topic-uid", required=True, help="source topic uid")
    topic_transition.add_argument("--target-topic-uid", required=True, help="target topic uid")
    topic_transition.add_argument("--approval-ref", help="required human approval ref")
    topic_transition.add_argument("--rationale", required=True, help="transition rationale")

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
    dars.add_argument("--backend", choices=["loopback", "configured"], default="loopback", help="DARS backend selection mode")
    dars.add_argument("--approval-ref", help="explicit approval ref required for external DARS backends")
    dars.add_argument(
        "--backend-activation-packet",
        help=(
            "JSON path to a DARS backend activation packet; required for"
            " openai_compatible backends. The runtime is the enforcement"
            " boundary and the CLI only passes the ref through."
        ),
    )
    browser_dars = sub.add_parser(
        "request-browser-dars-review",
        help="run advisory DARS/Devil review over a Chief Editor browser-investigation review artifact",
    )
    browser_dars.add_argument("--instance", required=True, help="runtime instance root containing Chief Editor browser review")
    browser_dars.add_argument("--date", required=True, help="YYYYMMDD review partition")
    browser_dars.add_argument("--chief-editor-review-ref", required=True, help="relative ref to CHIEF-REVIEW-*-BROWSER.json")
    browser_dars.add_argument("--producer-id", default="dars-browser-cli", help="DARS browser review producer id")
    browser_revision = sub.add_parser(
        "resolve-browser-dars-revisions",
        help="convert advisory browser DARS findings into deterministic segment/corroboration resolution evidence",
    )
    browser_revision.add_argument("--instance", required=True, help="runtime instance root containing the browser DARS review")
    browser_revision.add_argument("--date", required=True, help="YYYYMMDD review partition")
    browser_revision.add_argument("--dars-review-ref", required=True, help="relative ref to DARS-REVIEW-*-BROWSER.json")
    browser_revision.add_argument("--producer-id", default="browser-revision-cli", help="revision resolver producer id")
    browser_final = sub.add_parser(
        "final-review-browser-investigation",
        help="run Chief Editor final acceptance review over resolved browser DARS revisions",
    )
    browser_final.add_argument("--instance", required=True, help="runtime instance root containing the revision resolution")
    browser_final.add_argument("--date", required=True, help="YYYYMMDD review partition")
    browser_final.add_argument("--revision-resolution-ref", required=True, help="relative ref to REVISION-*-BROWSER.json")
    browser_final.add_argument("--producer-id", default="chief-editor-browser-final-cli", help="Chief Editor final-review producer id")
    pass_contract = sub.add_parser(
        "propose-pass-contract",
        help="write a governed self-improvement proposal for a missing/insufficient pass contract",
    )
    pass_contract.add_argument("--instance", required=True, help="Hisys instance root")
    pass_contract.add_argument("--date", required=True, help="YYYYMMDD proposal partition")
    pass_contract.add_argument("--domain", required=True, help="domain needing a pass-contract proposal")
    pass_contract.add_argument("--question-type", required=True, help="question type needing a pass-contract proposal")
    pass_contract.add_argument(
        "--failure-mode",
        required=True,
        choices=[
            "adapter_missing",
            "domain_contract_missing",
            "source_count_insufficient",
            "independent_corroboration_missing",
            "contradiction_unchecked",
            "claim_coverage_incomplete",
            "confidence_below_threshold",
            "human_approval_required",
        ],
        help="dominant needs_more_evidence reason driving the proposal",
    )
    pass_contract.add_argument("--example-request-id", action="append", default=[], help="example request id behind the proposal")
    pass_contract.add_argument("--format", choices=["text", "json"], default="text")

    eval_contract = sub.add_parser("evaluate-pass-contract", help="evaluate a pass contract against a local evidence summary")
    eval_contract.add_argument("--instance", required=True)
    eval_contract.add_argument("--date", required=True)
    eval_contract.add_argument("--contract-ref", required=True)
    eval_contract.add_argument("--evidence-summary", required=True)
    eval_contract.add_argument("--format", choices=["text", "json"], default="text")

    convert_contract = sub.add_parser("convert-pass-contract-proposal", help="convert a proposal into an inactive candidate registry entry")
    convert_contract.add_argument("--instance", required=True)
    convert_contract.add_argument("--date", required=True)
    convert_contract.add_argument("--proposal-ref", required=True)
    convert_contract.add_argument("--format", choices=["text", "json"], default="text")

    review_contract = sub.add_parser("request-pass-contract-review", help="write an advisory pass-contract review package")
    review_contract.add_argument("--instance", required=True)
    review_contract.add_argument("--date", required=True)
    review_contract.add_argument("--candidate-ref", required=True)
    review_contract.add_argument("--reviewer", action="append", default=[])
    review_contract.add_argument("--format", choices=["text", "json"], default="text")

    promote_contract = sub.add_parser("promote-pass-contract", help="promote a candidate contract after human approval")
    promote_contract.add_argument("--instance", required=True)
    promote_contract.add_argument("--date", required=True)
    promote_contract.add_argument("--candidate-ref", required=True)
    promote_contract.add_argument("--review-ref", required=True)
    promote_contract.add_argument("--validation-ref", required=True)
    promote_contract.add_argument("--human-approval-ref")
    promote_contract.add_argument("--format", choices=["text", "json"], default="text")

    audit_nme = sub.add_parser("audit-needs-more-evidence", help="summarize needs_more_evidence proposal patterns")
    audit_nme.add_argument("--instance", required=True)
    audit_nme.add_argument("--date", required=True)
    audit_nme.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "propose-pass-contract":
        return _cmd_propose_pass_contract(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            domain=args.domain,
            question_type=args.question_type,
            failure_mode=args.failure_mode,
            example_request_ids=args.example_request_id,
            output_format=args.format,
        )
    if args.command == "evaluate-pass-contract":
        return _cmd_evaluate_pass_contract(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            contract_ref=args.contract_ref,
            evidence_summary=args.evidence_summary,
            output_format=args.format,
        )
    if args.command == "convert-pass-contract-proposal":
        return _cmd_convert_pass_contract_proposal(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            proposal_ref=args.proposal_ref,
            output_format=args.format,
        )
    if args.command == "request-pass-contract-review":
        return _cmd_request_pass_contract_review(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            candidate_ref=args.candidate_ref,
            reviewers=args.reviewer,
            output_format=args.format,
        )
    if args.command == "promote-pass-contract":
        return _cmd_promote_pass_contract(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            candidate_ref=args.candidate_ref,
            review_ref=args.review_ref,
            validation_ref=args.validation_ref,
            human_approval_ref=args.human_approval_ref,
            output_format=args.format,
        )
    if args.command == "audit-needs-more-evidence":
        return _cmd_audit_needs_more_evidence(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            output_format=args.format,
        )
    if args.command == "validate-config":
        return _cmd_validate_config(Path(args.instance))
    if args.command == "deploy-hermes-tool":
        return _cmd_deploy_hermes_tool(
            source_root=args.source_root,
            target_root=args.target,
            channel_id=args.channel_id,
            channel_name=args.channel_name,
            force=args.force,
        )
    if args.command == "deployment-status":
        return _cmd_deployment_status(target_root=args.target, output_format=args.format)
    if args.command == "rollback-hermes-tool":
        return _cmd_rollback_hermes_tool(
            target_root=args.target,
            to_release=args.to_release,
            previous=args.previous,
            output_format=args.format,
        )
    if args.command == "build-hermes-deploy-report":
        return _cmd_build_hermes_deploy_report(
            target_root=args.target,
            validation_items=args.validation,
            output=args.output,
            output_format=args.format,
        )
    if args.command == "environment-init":
        return _cmd_environment_init(
            config_path=args.config,
            host_id=args.host_id,
            hisys_tool_root=args.hisys_tool_root,
            hisys_source_repo=args.hisys_source_repo,
            evidence_store_root=args.evidence_store_root,
            evidence_store_config=args.evidence_store_config,
            personal_vault_root=args.personal_vault_root,
            lab_vault_root=args.lab_vault_root,
            output_format=args.format,
        )
    if args.command == "environment-status":
        return _cmd_environment_status(config_path=args.config, output_format=args.format)
    if args.command == "evidence-store-init":
        return _cmd_evidence_store_init(config_path=args.config, root=args.root, store_id=args.store_id, output_format=args.format)
    if args.command == "evidence-store-status":
        return _cmd_evidence_store_status(config_path=args.config, output_format=args.format)
    if args.command == "evidence-store-import-investigation":
        return _cmd_evidence_store_import_investigation(
            config_path=args.config,
            topic_id=args.topic_id,
            topic_slug=args.topic_slug,
            investigation_id=args.investigation_id,
            date=args.date,
            includes=args.include,
            approval_ref=args.approval_ref,
            write=args.write,
            output_format=args.format,
        )
    if args.command == "evidence-stone-candidates":
        return _cmd_evidence_stone_candidates(
            config_path=args.config,
            topic_id=args.topic_id,
            topic_slug=args.topic_slug,
            investigation_id=args.investigation_id,
            output=args.output,
            output_format=args.format,
        )
    if args.command == "evidence-promote-stone":
        return _cmd_evidence_promote_stone(
            config_path=args.config,
            candidate_path=args.candidate,
            candidate_id=args.candidate_id,
            approval_ref=args.approval_ref,
            write=args.write,
            output_format=args.format,
        )
    if args.command == "validate-public-browser-profile":
        try:
            profile = load_public_browser_profile(args.profile)
        except Exception as exc:
            print(f"public browser profile: invalid reason={exc}", file=sys.stderr)
            return 2
        print(
            "public browser profile: valid "
            f"profile_id={profile.profile_id} connector_id={profile.connector_id} transport_kind={profile.transport_kind}"
        )
        return 0
    if args.command == "public-browser-run":
        return _cmd_public_browser_run(
            instance_root=Path(args.instance),
            config_path=Path(args.config),
            profile_path=args.profile,
            yyyymmdd=args.date,
            request_id=args.request_id,
            topic=args.topic,
            user_opinion=args.user_opinion,
            approval_ref=args.approval_ref,
            source_urls=args.source_url,
            follow_links=args.follow_links,
            max_follow_links_per_source=args.max_follow_links_per_source,
            orchestrator_corroborating_urls=args.orchestrator_corroborating_url,
        )
    if args.command == "public-browser-readiness":
        return _cmd_public_browser_readiness(
            instance_root=Path(args.instance),
            config_path=Path(args.config),
            profile_path=args.profile,
            yyyymmdd=args.date,
        )
    if args.command == "get-run-summary":
        return _cmd_get_run_summary(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            output_format=args.format,
        )
    if args.command == "list-run-artifacts":
        return _cmd_list_run_artifacts(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
        )
    if args.command == "show-artifact":
        return _cmd_show_artifact(instance_root=Path(args.instance), ref=args.ref)
    if args.command == "build-investment-decision-packet":
        return _cmd_build_investment_decision_packet(
            instance_root=Path(args.instance),
            packet_path=Path(args.packet),
            yyyymmdd=args.date,
            weight_policy_path=Path(args.weight_policy) if args.weight_policy else None,
        )
    if args.command == "build-investment-evidence-package":
        return _cmd_build_investment_evidence_package(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            asset=args.asset,
            source_access_path=Path(args.source_access),
            source_evidence_path=Path(args.source_evidence),
        )
    if args.command == "completion-status":
        return _cmd_completion_status(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            validation_items=args.validation,
            output_format=args.format,
        )
    if args.command == "traceability-coverage":
        return _cmd_traceability_coverage(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            repo_root=args.repo,
        )
    if args.command == "change-impact":
        return _cmd_change_impact(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            repo_root=args.repo,
            changed_refs=tuple(args.changed_ref),
            current_head_short=args.current_head_short,
        )
    if args.command == "architecture-candidates":
        return _cmd_architecture_candidates(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            coverage_report_path=(
                Path(args.coverage_report) if args.coverage_report else None
            ),
            freshness_report_path=(
                Path(args.freshness_report) if args.freshness_report else None
            ),
            change_impact_report_path=(
                Path(args.change_impact_report)
                if args.change_impact_report
                else None
            ),
            current_head_short=args.current_head_short,
        )
    if args.command == "codebase-evidence-portfolio":
        return _cmd_codebase_evidence_portfolio(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            line_bundle_path=Path(args.line_bundle),
            current_head_short=args.current_head_short,
        )
    if args.command == "oss-comparison-adapter":
        return _cmd_oss_comparison_adapter(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            bundle_path=Path(args.bundle),
            current_head_short=args.current_head_short,
        )
    if args.command == "evaluate-code-analysis-contract":
        return _cmd_evaluate_code_analysis_contract(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            contract_ref=Path(args.contract_ref),
            question_type=args.question_type,
            coverage_report_path=(
                Path(args.coverage_report) if args.coverage_report else None
            ),
            boundary_report_path=(
                Path(args.boundary_report) if args.boundary_report else None
            ),
            freshness_report_path=(
                Path(args.freshness_report) if args.freshness_report else None
            ),
            benchmark_report_path=(
                Path(args.benchmark_report) if args.benchmark_report else None
            ),
            change_impact_report_path=(
                Path(args.change_impact_report)
                if args.change_impact_report
                else None
            ),
            architecture_candidates_report_path=(
                Path(args.architecture_candidates_report)
                if args.architecture_candidates_report
                else None
            ),
            human_approval_ref=args.human_approval_ref,
        )
    if args.command == "validate-subagent-evidence-packet":
        return _cmd_validate_subagent_evidence_packet(
            task_path=Path(args.task),
            result_path=Path(args.result) if args.result else None,
        )
    if args.command == "codebase-map-freshness-review":
        return _cmd_codebase_map_freshness_review(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            current_date_iso=args.current_date,
            max_age_days=args.max_age_days,
            current_head_short=args.current_head_short,
        )
    if args.command == "runtime-boundary-check":
        return _cmd_runtime_boundary_check(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            refs=tuple(args.ref),
        )
    if args.command == "runtime-status-surface":
        return _cmd_runtime_status_surface(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            workdir=args.workdir,
            model=args.model,
            session=args.session,
            approval_state=args.approval_state,
            context_budget=args.context_budget,
            output_format=args.format,
        )
    if args.command == "run-dars-panel":
        return _cmd_run_dars_panel(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            panel_config_path=args.panel_config,
            candidate_ref=args.candidate_ref,
            evidence_refs=args.evidence_ref,
            output_format=args.format,
            local_model_endpoint=args.local_model_endpoint,
            local_model=args.local_model,
            activation_packet_path=args.activation_packet,
            write_report=args.write_report,
        )
    if args.command == "run-dars-panel-golden":
        return _cmd_run_dars_panel_golden(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            output_format=args.format,
        )
    if args.command == "dars-panel-readiness":
        return _cmd_dars_panel_readiness(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            output_format=args.format,
            write_report=args.write_report,
        )
    if args.command == "build-spec-first-packet":
        return _cmd_build_spec_first_packet(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            packet_id=args.packet_id,
            objective=args.objective,
            scope=args.scope,
            non_goals=args.non_goal,
            allowed_actions=args.allowed_action,
            evidence_contract=args.evidence_contract,
            expected_artifacts=args.expected_artifact,
            gate_criteria=args.gate_criterion,
            human_approval_boundary=args.human_approval_boundary,
            output_format=args.format,
        )
    if args.command == "build-codebase-inventory":
        return _cmd_build_codebase_inventory(
            repo_root=Path(args.repo),
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            analysis_scope=args.scope,
            output_format=args.format,
        )
    if args.command == "build-code-symbol-index":
        return _cmd_build_code_symbol_index(
            repo_root=Path(args.repo),
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            analysis_scope=args.scope,
            output_format=args.format,
        )
    if args.command == "scan-codebase-boundaries":
        return _cmd_scan_codebase_boundaries(
            repo_root=Path(args.repo),
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            analysis_scope=args.scope,
            output_format=args.format,
        )
    if args.command == "build-codebase-map":
        return _cmd_build_codebase_map(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            inventory_ref=args.inventory_ref,
            symbol_index_ref=args.symbol_index_ref,
            output_format=args.format,
        )
    if args.command == "review-codebase-analysis":
        return _cmd_review_codebase_analysis(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            inventory_ref=args.inventory_ref,
            symbol_index_ref=args.symbol_index_ref,
            scope_map_ref=args.scope_map_ref,
            risk_scan_ref=args.risk_scan_ref,
            unresolved_blockers=args.unresolved_blocker,
            output_format=args.format,
        )
    if args.command == "build-finish-packet":
        return _cmd_build_finish_packet(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            packet_id=args.packet_id,
            spec_packet_ref=args.spec_packet_ref,
            completed_tasks=args.completed_task,
            validation_results=args.validation_result,
            review_findings=args.review_finding,
            unresolved_blockers=args.unresolved_blocker,
            next_actions=args.next_action,
            human_gate_state=args.human_gate_state,
            decision=args.decision,
            output_format=args.format,
        )
    if args.command == "release-readiness":
        return _cmd_release_readiness(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            quality_gate_items=args.quality_gate,
            trace_refs=args.trace_ref,
            known_gaps=args.known_gap,
            output_format=args.format,
        )
    if args.command == "health-status":
        return _cmd_health_status(instance_root=Path(args.instance), yyyymmdd=args.date, output_format=args.format)
    if args.command == "backup-runtime":
        return _cmd_backup_runtime(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            backup_id=args.backup_id,
            output_format=args.format,
        )
    if args.command == "restore-backup-dry-run":
        return _cmd_restore_backup_dry_run(
            archive_path=Path(args.archive),
            restore_target=Path(args.restore_target),
            report_root=Path(args.report_root),
            yyyymmdd=args.date,
            output_format=args.format,
        )
    if args.command == "review-investment-decision-packet":
        return _cmd_review_investment_decision_packet(
            instance_root=Path(args.instance),
            packet_id=args.packet_id,
            yyyymmdd=args.date,
            output_format=args.format,
        )
    if args.command == "run-investment-decision-dry-run":
        return _cmd_run_investment_decision_dry_run(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            asset=args.asset,
            instruments=args.instrument,
            time_horizon=args.time_horizon,
            evidence_package_paths=[Path(path) for path in args.evidence_package],
            weight_policy_path=Path(args.weight_policy),
        )
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
            orchestrator_harness_path=Path(args.orchestrator_harness) if args.orchestrator_harness else None,
        )
    if args.command == "investigate-domain":
        return _cmd_investigate_domain(
            instance_root=Path(args.instance),
            request_path=Path(args.request),
            yyyymmdd=args.date,
            pass_contract_registry=Path(args.pass_contract_registry) if args.pass_contract_registry else None,
            question_type=args.question_type,
            evidence_summary=Path(args.evidence_summary) if args.evidence_summary else None,
            promote_pdf_source_access_refs=args.promote_pdf_source_access_refs,
            promote_pdf_source_evidence_refs=args.promote_pdf_source_evidence_refs,
            source_quote_refs=args.source_quote_refs,
            claim_evidence_ledger_refs=args.claim_evidence_ledger_refs,
            claim_evidence_summary_refs=args.claim_evidence_summary_refs,
            claim_coverage_gate_refs=args.claim_coverage_gate_refs,
            recommendation_claim_registry_refs=args.recommendation_claim_registry_refs,
            live_source_access_refs=args.live_source_access_refs,
            live_source_evidence_refs=args.live_source_evidence_refs,
        )
    if args.command == "live-ideation-run":
        return _cmd_live_ideation_run(
            instance_root=Path(args.instance),
            request_path=Path(args.request),
            config_path=Path(args.config),
            yyyymmdd=args.date,
            doi=args.doi,
            approval_ref=args.approval_ref,
            explicit_live_source_enable=args.explicit_live_source_enable,
            metadata_fixture=Path(args.metadata_fixture) if args.metadata_fixture else None,
        )
    if args.command == "live-ideation-persist":
        return _cmd_live_ideation_persist(
            instance_root=Path(args.instance),
            request_path=Path(args.request),
            config_path=Path(args.config),
            yyyymmdd=args.date,
            doi=args.doi,
            approval_ref=args.approval_ref,
            vault_root=Path(args.vault_root),
            remote_name=args.remote_name,
            branch=args.branch,
            credential_ref=args.credential_ref,
            commit_message=args.commit_message,
            explicit_live_source_enable=args.explicit_live_source_enable,
            explicit_live_write_enable=args.explicit_live_write_enable,
            explicit_live_git_enable=args.explicit_live_git_enable,
            allow_real_obsidian_vault=args.allow_real_obsidian_vault,
            clean_git_status=args.clean_git_status,
            metadata_fixture=Path(args.metadata_fixture) if args.metadata_fixture else None,
            standing_approval_policy=Path(args.standing_approval_policy) if args.standing_approval_policy else None,
        )
    if args.command == "live-autonomy-run":
        return _cmd_live_autonomy_run(
            instance_root=Path(args.instance),
            queue_path=Path(args.queue),
            config_path=Path(args.config),
            yyyymmdd=args.date,
            vault_root=Path(args.vault_root),
            credential_ref=args.credential_ref,
            standing_approval_policy=Path(args.standing_approval_policy),
            remote_name=args.remote_name,
            branch=args.branch,
            allow_real_obsidian_vault=args.allow_real_obsidian_vault,
            clean_git_status=args.clean_git_status,
            max_items=args.max_items,
            ledger_path=Path(args.ledger) if args.ledger else None,
            max_retries=args.max_retries,
            report_subdir=None,
        )
    if args.command == "live-autonomy-tick":
        return _cmd_live_autonomy_tick(
            instance_root=Path(args.instance),
            queue_dir=Path(args.queue_dir),
            queue_glob=args.queue_glob,
            config_path=Path(args.config),
            yyyymmdd=args.date,
            vault_root=Path(args.vault_root),
            credential_ref=args.credential_ref,
            standing_approval_policy=Path(args.standing_approval_policy),
            remote_name=args.remote_name,
            branch=args.branch,
            allow_real_obsidian_vault=args.allow_real_obsidian_vault,
            clean_git_status=args.clean_git_status,
            max_queues=args.max_queues,
            max_items=args.max_items,
            ledger_dir=Path(args.ledger_dir) if args.ledger_dir else None,
            max_retries=args.max_retries,
            queue_lifecycle=args.queue_lifecycle,
            active_dir=Path(args.active_dir) if args.active_dir else None,
            done_dir=Path(args.done_dir) if args.done_dir else None,
            attention_dir=Path(args.attention_dir) if args.attention_dir else None,
            rejected_dir=Path(args.rejected_dir) if args.rejected_dir else None,
        )
    if args.command == "live-autonomy-admit":
        return _cmd_live_autonomy_admit(
            instance_root=Path(args.instance),
            candidate_dir=Path(args.candidate_dir),
            candidate_glob=args.candidate_glob,
            incoming_dir=Path(args.incoming_dir),
            rejected_dir=Path(args.rejected_dir),
            yyyymmdd=args.date,
            max_candidates=args.max_candidates,
        )
    if args.command == "live-autonomy-status":
        return _cmd_live_autonomy_status(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            ledger_dir=Path(args.ledger_dir) if args.ledger_dir else None,
        )
    if args.command == "plan-source-connectors":
        return _cmd_plan_source_connectors(
            instance_root=Path(args.instance),
            request_path=Path(args.request),
            config_path=Path(args.config),
            yyyymmdd=args.date,
        )
    if args.command == "source-connector-preflight":
        return _cmd_source_connector_preflight(
            instance_root=Path(args.instance),
            config_path=Path(args.config),
            yyyymmdd=args.date,
            request_id=args.request_id,
            connector_id=args.connector_id,
            approval_ref=args.approval_ref,
            requested_domain=args.requested_domain,
            requested_actions=args.requested_action or ["read"],
            provider_url_ref=args.provider_url_ref,
            preflight_only=args.preflight_only,
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
            query=args.query,
            transport_fixture_search=Path(args.transport_fixture_search) if args.transport_fixture_search else None,
            license_signal=args.license_signal,
            approval_ref=args.approval_ref,
            transport_fixture_pdf=Path(args.transport_fixture_pdf) if args.transport_fixture_pdf else None,
            browser_fixture_html=Path(args.browser_fixture_html) if args.browser_fixture_html else None,
            dry_run=args.dry_run,
        )
    if args.command == "browser-investigate-topic":
        return _cmd_browser_investigate_topic(
            instance_root=Path(args.instance),
            config_path=Path(args.config),
            yyyymmdd=args.date,
            request_id=args.request_id,
            topic=args.topic,
            user_opinion=args.user_opinion,
            approval_ref=args.approval_ref,
            source_urls=args.source_url,
            orchestrator_decide_domains=args.orchestrator_decide_domains,
            browser_fixture_html=[Path(item) for item in args.browser_fixture_html],
            follow_links=args.follow_links,
            max_follow_links_per_source=args.max_follow_links_per_source,
            orchestrator_corroborating_urls=args.orchestrator_corroborating_url,
        )
    if args.command == "review-browser-investigation":
        return _cmd_review_browser_investigation(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            browser_investigation_report_ref=args.browser_investigation_report_ref,
            producer_id=args.producer_id,
        )
    if args.command == "search-topic":
        return _cmd_search_topic(
            instance_root=Path(args.instance),
            config_path=Path(args.config),
            yyyymmdd=args.date,
            request_id=args.request_id,
            topic=args.topic,
            user_opinion=args.user_opinion,
            approval_ref=args.approval_ref,
            transport_fixture_search=Path(args.transport_fixture_search) if args.transport_fixture_search else None,
            provider=args.provider,
            provider_url_ref=args.provider_url_ref,
            credential_ref=args.credential_ref,
            provider_response_fixture=Path(args.provider_response_fixture) if args.provider_response_fixture else None,
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
    if args.command == "extract-pdf-quotes":
        return _cmd_extract_pdf_quotes(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            promoted_pdf_evidence_refs=args.promoted_pdf_evidence_ref,
        )
    if args.command == "build-claim-evidence-ledger":
        return _cmd_build_claim_evidence_ledger(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            claim_id=args.claim_id,
            claim_text=args.claim_text,
            relation=args.relation,
            rationale=args.rationale,
            source_quote_refs=args.source_quote_ref,
        )
    if args.command == "build-claim-evidence-summary":
        return _cmd_build_claim_evidence_summary(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            claim_id=args.claim_id,
            claim_evidence_ledger_refs=args.claim_evidence_ledger_ref,
        )
    if args.command == "build-claim-coverage-gate":
        return _cmd_build_claim_coverage_gate(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            required_claim_ids=args.required_claim_id,
            claim_evidence_summary_refs=args.claim_evidence_summary_ref,
        )
    if args.command == "build-recommendation-claim-registry":
        return _cmd_build_recommendation_claim_registry(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            recommendation_text=args.recommendation_text,
            claim_texts=args.claim_text,
            source_recommendation_ref=args.source_recommendation_ref,
        )
    if args.command == "vault-plan":
        return _cmd_vault_plan(
            instance_root=Path(args.instance),
            registry_path=Path(args.registry),
            yyyymmdd=args.date,
            hhmm=args.time,
            request_id=args.request_id,
            submitted_title=args.topic_title,
            domain=args.domain,
            objective=args.objective,
            dry_run=args.dry_run,
        )
    if args.command == "vault-validate":
        return _cmd_vault_validate(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            registry_path=Path(args.registry),
            topic_manifest_path=Path(args.topic_manifest),
            investigation_manifest_path=Path(args.investigation_manifest),
            gatekeeper_decision_path=Path(args.gatekeeper_decision),
        )
    if args.command == "vault-template-plan":
        return _cmd_vault_template_plan(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
        )
    if args.command == "vault-apply":
        return _cmd_vault_apply(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            plan_path=Path(args.plan),
            target_vault_root=Path(args.target_vault_root),
            approval_ref=args.approval_ref,
            fixture_vault_only=args.fixture_vault_only,
        )
    if args.command == "vault-roundtrip-validate":
        return _cmd_vault_roundtrip_validate(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            plan_path=Path(args.plan),
            fixture_vault_root=Path(args.fixture_vault_root),
            apply_report_path=Path(args.apply_report),
        )
    if args.command == "vault-live-preflight":
        return _cmd_vault_live_preflight(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            vault_root=Path(args.vault_root),
        )
    if args.command == "vault-live-approval-package":
        return _cmd_vault_live_approval_package(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            preflight_report_path=Path(args.preflight_report),
            plan_path=Path(args.plan),
            operator_id=args.operator_id,
            rationale=args.rationale,
        )
    if args.command == "vault-live-write-gate":
        return _cmd_vault_live_write_gate(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            approval_package_path=Path(args.approval_package),
            approval_ref=args.approval_ref,
            explicit_live_write_enable=args.explicit_live_write_enable,
            clean_git_status=args.clean_git_status,
        )
    if args.command == "vault-live-transaction-plan":
        return _cmd_vault_live_transaction_plan(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            approval_package_path=Path(args.approval_package),
            write_gate_report_path=Path(args.write_gate_report),
        )
    if args.command == "vault-live-transaction-rehearse":
        return _cmd_vault_live_transaction_rehearse(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            transaction_plan_path=Path(args.transaction_plan),
            fixture_vault_root=Path(args.fixture_vault_root),
            approval_ref=args.approval_ref,
            fixture_vault_only=args.fixture_vault_only,
        )
    if args.command == "vault-live-transaction-apply":
        return _cmd_vault_live_transaction_apply(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            transaction_plan_path=Path(args.transaction_plan),
            vault_root=Path(args.vault_root),
            approval_ref=args.approval_ref,
            explicit_live_write_enable=args.explicit_live_write_enable,
            allow_real_obsidian_vault=args.allow_real_obsidian_vault,
            clean_git_status=args.clean_git_status,
        )
    if args.command == "vault-live-config-status":
        return _cmd_vault_live_config_status(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
        )
    if args.command == "vault-topic-gatekeeper":
        return _cmd_vault_topic_gatekeeper(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            registry_path=Path(args.registry),
            proposed_topic_path=Path(args.proposed_topic),
        )
    if args.command == "vault-evidence-promotion-plan":
        return _cmd_vault_evidence_promotion_plan(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_path=Path(args.request),
        )
    if args.command == "vault-obsidian-milestone-status":
        return _cmd_vault_obsidian_milestone_status(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
        )
    if args.command == "vault-git-fixture-init":
        return _cmd_vault_git_fixture_init(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            plan_path=Path(args.plan),
            fixture_vault_root=Path(args.fixture_vault_root),
            fixture_remote_root=Path(args.fixture_remote_root),
            fixture_git_only=args.fixture_git_only,
        )
    if args.command == "vault-git-fixture-sync":
        return _cmd_vault_git_fixture_sync(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            plan_path=Path(args.plan),
            fixture_vault_root=Path(args.fixture_vault_root),
            fixture_remote_root=Path(args.fixture_remote_root),
            fixture_git_only=args.fixture_git_only,
        )
    if args.command == "vault-git-live-sync":
        return _cmd_vault_git_live_sync(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            plan_path=Path(args.plan),
            vault_root=Path(args.vault_root),
            approval_ref=args.approval_ref,
            explicit_live_git_enable=args.explicit_live_git_enable,
            allow_real_obsidian_vault=args.allow_real_obsidian_vault,
            clean_git_status=args.clean_git_status,
        )
    if args.command == "vault-topic-transition-plan":
        return _cmd_vault_topic_transition_plan(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            request_id=args.request_id,
            action=args.action,
            source_topic_uid=args.source_topic_uid,
            target_topic_uid=args.target_topic_uid,
            approval_ref=args.approval_ref,
            rationale=args.rationale,
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
            backend=args.backend,
            approval_ref=args.approval_ref,
            backend_activation_packet_ref=args.backend_activation_packet,
        )
    if args.command == "request-browser-dars-review":
        return _cmd_request_browser_dars_review(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            chief_editor_review_ref=args.chief_editor_review_ref,
            producer_id=args.producer_id,
        )
    if args.command == "resolve-browser-dars-revisions":
        return _cmd_resolve_browser_dars_revisions(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            dars_review_ref=args.dars_review_ref,
            producer_id=args.producer_id,
        )
    if args.command == "final-review-browser-investigation":
        return _cmd_final_review_browser_investigation(
            instance_root=Path(args.instance),
            yyyymmdd=args.date,
            revision_resolution_ref=args.revision_resolution_ref,
            producer_id=args.producer_id,
        )
    parser.error(f"unknown command: {args.command}")
    return 2


def _cmd_deploy_hermes_tool(
    *,
    source_root: Path,
    target_root: Path,
    channel_id: str | None,
    channel_name: str | None,
    force: bool,
) -> int:
    result = deploy_hisys_to_hermes(
        source_root=source_root,
        target_root=target_root,
        channel_id=channel_id,
        channel_name=channel_name,
        force=force,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "deployed" else 2


def _cmd_deployment_status(*, target_root: Path, output_format: str) -> int:
    status = get_hermes_deployment_status(target_root=target_root)
    if output_format == "json":
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status: {status['status']}")
        print(f"current_release_id: {status.get('current_release_id')}")
        print(f"source_commit: {status.get('source_commit')}")
        print(f"wrapper_points_to_snapshot: {str(status['wrapper_points_to_snapshot']).lower()}")
        print(f"wrapper_references_live_source: {str(status['wrapper_references_live_source']).lower()}")
        print(f"rollback_available: {str(status['rollback_available']).lower()}")
        print(f"safe_to_use: {str(status['safe_to_use']).lower()}")
    return 0 if status.get("safe_to_use") else 2


def _cmd_rollback_hermes_tool(*, target_root: Path, to_release: str | None, previous: bool, output_format: str) -> int:
    result = rollback_hisys_hermes_tool(target_root=target_root, to_release=to_release, previous=previous)
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        if result.get("status") == "rolled_back":
            print(f"previous_release_id: {result['previous_release_id']}")
            print(f"current_release_id: {result['current_release_id']}")
        else:
            print(f"reason: {result.get('reason')}")
    return 0 if result.get("status") == "rolled_back" else 2


def _cmd_build_hermes_deploy_report(*, target_root: Path, validation_items: list[str], output: Path | None, output_format: str) -> int:
    try:
        validations = _parse_validation_status(validation_items)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    report = build_hermes_deploy_report(target_root=target_root, validations=validations, output=output)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if output:
            print(f"deploy_report: {output}")
        print(f"status: {report['deployment_status']['status']}")
        print(f"release_id: {report.get('release_id')}")
        print("promotion_allowed: false")
        print("human_approval_required_for_host_install: true")
    return 0 if report["deployment_status"].get("safe_to_use") else 2


def _print_json_or_text(report: dict[str, Any], *, output_format: str, text_lines: list[str] | None = None) -> None:
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for line in text_lines or []:
            print(line)


def _cmd_environment_init(
    *,
    config_path: Path,
    host_id: str,
    hisys_tool_root: Path,
    hisys_source_repo: Path,
    evidence_store_root: Path,
    evidence_store_config: Path,
    personal_vault_root: Path,
    lab_vault_root: Path,
    output_format: str,
) -> int:
    report = init_environment_config(
        config_path=config_path,
        host_id=host_id,
        hisys_tool_root=hisys_tool_root,
        hisys_source_repo=hisys_source_repo,
        evidence_store_root=evidence_store_root,
        evidence_store_config=evidence_store_config,
        personal_vault_root=personal_vault_root,
        lab_vault_root=lab_vault_root,
    )
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"environment config initialized: {report['config_path']}")
    return 0


def _cmd_environment_status(*, config_path: Path, output_format: str) -> int:
    report = environment_config_status(config_path)
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"environment config: {'safe' if report['safe_to_use'] else 'unsafe'}")
        if report.get("issues"):
            print("issues: " + ", ".join(report["issues"]))
    return 0 if report["safe_to_use"] else 1


def _cmd_evidence_store_init(*, config_path: Path, root: Path, store_id: str, output_format: str) -> int:
    report = init_evidence_store(config_path=config_path, root=root, store_id=store_id)
    _print_json_or_text(
        report,
        output_format=output_format,
        text_lines=[f"evidence_store: initialized", f"root: {report['root']}", f"config: {report['config_path']}"],
    )
    return 0


def _cmd_evidence_store_status(*, config_path: Path, output_format: str) -> int:
    report = evidence_store_status(config_path)
    _print_json_or_text(
        report,
        output_format=output_format,
        text_lines=[
            f"evidence_store: {'safe' if report['safe_to_write'] else 'blocked'}",
            f"root: {report['root']}",
            f"issues: {','.join(report['issues']) if report['issues'] else 'none'}",
        ],
    )
    return 0 if report.get("safe_to_write") else 1


def _cmd_evidence_store_import_investigation(
    *,
    config_path: Path,
    topic_id: str,
    topic_slug: str,
    investigation_id: str,
    date: str,
    includes: list[str],
    approval_ref: str | None,
    write: bool,
    output_format: str,
) -> int:
    report = import_investigation_artifacts(
        config_path=config_path,
        topic_id=topic_id,
        topic_slug=topic_slug,
        investigation_id=investigation_id,
        date=date,
        includes=includes,
        approval_ref=approval_ref,
        write=write,
    )
    _print_json_or_text(
        report,
        output_format=output_format,
        text_lines=[
            f"evidence_store_import: {report['status']}",
            f"topic_id: {report.get('topic_id')}",
            f"investigation_id: {report.get('investigation_id')}",
            f"copied_count: {report.get('copied_count', 0)}",
        ],
    )
    return 0 if report.get("status") in {"planned", "imported"} else 1


def _cmd_evidence_stone_candidates(
    *,
    config_path: Path,
    topic_id: str,
    topic_slug: str,
    investigation_id: str,
    output: Path | None,
    output_format: str,
) -> int:
    report = build_stone_candidates(
        config_path=config_path,
        topic_id=topic_id,
        topic_slug=topic_slug,
        investigation_id=investigation_id,
    )
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _print_json_or_text(
        report,
        output_format=output_format,
        text_lines=[
            f"stone_candidates: {report['candidate_count']}",
            *(f"- {candidate['candidate_id']} {candidate['recommended_stone_type']} {candidate['source_ref']}" for candidate in report["stone_candidates"]),
        ],
    )
    return 0


def _load_candidate(candidate_path: Path, candidate_id: str) -> dict[str, Any]:
    data = json.loads(candidate_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and data.get("candidate_id") == candidate_id:
        return data
    for candidate in data.get("stone_candidates", []):
        if candidate.get("candidate_id") == candidate_id:
            return candidate
    raise ValueError(f"candidate not found: {candidate_id}")


def _cmd_evidence_promote_stone(
    *,
    config_path: Path,
    candidate_path: Path,
    candidate_id: str,
    approval_ref: str | None,
    write: bool,
    output_format: str,
) -> int:
    try:
        candidate = _load_candidate(candidate_path, candidate_id)
    except Exception as exc:
        print(f"error: {exc}")
        return 2
    report = promote_stone_candidate(config_path=config_path, candidate=candidate, write=write, approval_ref=approval_ref)
    _print_json_or_text(
        report,
        output_format=output_format,
        text_lines=[f"stone_promotion: {report['status']}", f"stone_ref: {report.get('stone_ref')}", f"approval_ref: {report.get('approval_ref')}"]
    )
    return 0 if report.get("status") in {"planned", "promoted"} else 1


def _cmd_validate_config(instance_root: Path) -> int:
    registry = load_source_registry(InstanceRoot(instance_root))
    source_ids = sorted(registry.entries)
    print(f"config valid: {instance_root}")
    print(f"sources: {len(source_ids)}")
    for source_id in source_ids:
        entry = registry.entries[source_id]
        print(f"- {source_id} [{entry.source_type}] {entry.lifecycle_state}")
    return 0


def _cmd_vault_plan(
    *,
    instance_root: Path,
    registry_path: Path,
    yyyymmdd: str,
    hhmm: str,
    request_id: str,
    submitted_title: str,
    domain: str,
    objective: str,
    dry_run: bool,
) -> int:
    """Write a fixture-only Obsidian vault plan without writing the vault."""

    plan = build_vault_plan(
        registry_path=registry_path,
        request_id=request_id,
        submitted_title=submitted_title,
        domain=domain,
        objective=objective,
        yyyymmdd=yyyymmdd,
        hhmm=hhmm,
        dry_run=dry_run,
    )
    plan_path, report_path = write_vault_plan_artifacts(instance_root=instance_root, yyyymmdd=yyyymmdd, plan=plan)
    print(f"vault plan: report={report_path}")
    print(f"plan_ref: {plan_path.relative_to(instance_root)}")
    print("vault_write_attempted: false")
    print("external_call_made: false")
    return 0


def _cmd_vault_validate(
    *,
    instance_root: Path,
    yyyymmdd: str,
    registry_path: Path,
    topic_manifest_path: Path,
    investigation_manifest_path: Path,
    gatekeeper_decision_path: Path,
) -> int:
    """Validate Obsidian live-research manifests without writing the vault."""

    report = validate_vault_manifests(
        registry_path=registry_path,
        topic_manifest_path=topic_manifest_path,
        investigation_manifest_path=investigation_manifest_path,
        gatekeeper_decision_path=gatekeeper_decision_path,
    )
    report_path = write_vault_validation_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    status = "valid" if report["valid"] else "invalid"
    print(f"vault validation: {status}")
    print(f"report={report_path}")
    print("vault_write_attempted: false")
    return 0 if report["valid"] else 1


def _cmd_vault_template_plan(*, instance_root: Path, yyyymmdd: str, request_id: str) -> int:
    """Plan Obsidian memo ontology templates without writing the vault."""

    plan = build_vault_template_plan(request_id=request_id)
    plan_path, report_path = write_vault_template_plan_artifacts(instance_root=instance_root, yyyymmdd=yyyymmdd, plan=plan)
    print(f"vault template plan: report={report_path}")
    print(f"template_plan_ref: {plan_path.relative_to(instance_root)}")
    print("vault_write_attempted: false")
    return 0


def _cmd_vault_apply(
    *,
    instance_root: Path,
    yyyymmdd: str,
    plan_path: Path,
    target_vault_root: Path,
    approval_ref: str | None,
    fixture_vault_only: bool,
) -> int:
    """Apply a vault plan to an explicit fixture vault root only."""

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    report = apply_vault_plan_to_fixture(
        plan=plan,
        target_vault_root=target_vault_root,
        approval_ref=approval_ref,
        fixture_vault_only=fixture_vault_only,
    )
    report_path = write_vault_apply_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"vault apply: {report['status']}")
    print(f"report={report_path}")
    print(f"real_obsidian_vault_write_performed: {str(report['real_obsidian_vault_write_performed']).lower()}")
    return 0 if report["status"] == "applied" else 2


def _cmd_vault_roundtrip_validate(
    *,
    instance_root: Path,
    yyyymmdd: str,
    plan_path: Path,
    fixture_vault_root: Path,
    apply_report_path: Path,
) -> int:
    """Validate a fixture vault apply against its source plan."""

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    apply_report = json.loads(apply_report_path.read_text(encoding="utf-8"))
    report = validate_fixture_vault_roundtrip(plan=plan, fixture_vault_root=fixture_vault_root, apply_report=apply_report)
    report_path = write_vault_roundtrip_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"vault roundtrip validation: {report['status']}")
    print(f"report={report_path}")
    print("real_obsidian_vault_write_performed: false")
    return 0 if report["valid"] else 1


def _cmd_vault_live_preflight(*, instance_root: Path, yyyymmdd: str, request_id: str, vault_root: Path) -> int:
    """Inspect a candidate live vault without writing to it."""

    report = build_live_vault_preflight_report(vault_root=vault_root, request_id=request_id)
    report_path = write_live_vault_preflight_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"vault live preflight: {report['status']}")
    print(f"report={report_path}")
    print("write_probe_performed: false")
    print("live_write_enabled: false")
    return 0 if report["valid"] else 1


def _cmd_vault_live_approval_package(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    preflight_report_path: Path,
    plan_path: Path,
    operator_id: str,
    rationale: str,
) -> int:
    """Prepare a human approval package for a future live vault write."""

    preflight_report = json.loads(preflight_report_path.read_text(encoding="utf-8"))
    vault_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    package = build_live_vault_approval_package(
        request_id=request_id,
        preflight_report=preflight_report,
        vault_plan=vault_plan,
        operator_id=operator_id,
        rationale=rationale,
    )
    package_path = write_live_vault_approval_package(instance_root=instance_root, yyyymmdd=yyyymmdd, package=package)
    print(f"vault live approval package: {package['status']}")
    print(f"package={package_path}")
    print("live_write_enabled: false")
    print("real_obsidian_vault_write_performed: false")
    return 0 if package["status"] == "approval_required" else 1


def _cmd_vault_live_write_gate(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    approval_package_path: Path,
    approval_ref: str | None,
    explicit_live_write_enable: bool,
    clean_git_status: bool,
) -> int:
    """Evaluate final live-write gates without live vault mutation."""

    approval_package = json.loads(approval_package_path.read_text(encoding="utf-8"))
    report = build_live_vault_write_gate_report(
        request_id=request_id,
        approval_package=approval_package,
        approval_ref=approval_ref,
        explicit_live_write_enable=explicit_live_write_enable,
        clean_git_status=clean_git_status,
    )
    report_path = write_live_vault_write_gate_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"vault live write gate: {report['status']}")
    print(f"reason={report['reason_code']}")
    print(f"report={report_path}")
    print("live_write_enabled: false")
    print("real_obsidian_vault_write_performed: false")
    return 1


def _cmd_vault_live_transaction_plan(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    approval_package_path: Path,
    write_gate_report_path: Path,
) -> int:
    """Plan a non-executable live-vault transaction manifest."""

    approval_package = json.loads(approval_package_path.read_text(encoding="utf-8"))
    write_gate_report = json.loads(write_gate_report_path.read_text(encoding="utf-8"))
    plan = build_live_vault_transaction_plan(
        request_id=request_id,
        approval_package=approval_package,
        write_gate_report=write_gate_report,
    )
    report_path = write_live_vault_transaction_plan(instance_root=instance_root, yyyymmdd=yyyymmdd, plan=plan)
    print(f"vault live transaction plan: {plan['status']}")
    print(f"report={report_path}")
    print("live_write_enabled: false")
    print("real_obsidian_vault_write_performed: false")
    return 0 if plan["status"] == "planned_not_executable" else 1


def _cmd_vault_live_transaction_rehearse(
    *,
    instance_root: Path,
    yyyymmdd: str,
    transaction_plan_path: Path,
    fixture_vault_root: Path,
    approval_ref: str | None,
    fixture_vault_only: bool,
) -> int:
    """Rehearse a live-vault transaction manifest against a fixture vault only."""

    transaction_plan = json.loads(transaction_plan_path.read_text(encoding="utf-8"))
    report = rehearse_live_vault_transaction_in_fixture(
        transaction_plan=transaction_plan,
        fixture_vault_root=fixture_vault_root,
        approval_ref=approval_ref,
        fixture_vault_only=fixture_vault_only,
    )
    report_path = write_live_vault_transaction_rehearsal_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"vault live transaction rehearsal: {report['status']}")
    print(f"report={report_path}")
    print("real_obsidian_vault_write_performed: false")
    return 0 if report["status"] == "rehearsed_fixture_only" else 1


def _cmd_vault_live_transaction_apply(
    *,
    instance_root: Path,
    yyyymmdd: str,
    transaction_plan_path: Path,
    vault_root: Path,
    approval_ref: str | None,
    explicit_live_write_enable: bool,
    allow_real_obsidian_vault: bool,
    clean_git_status: bool,
) -> int:
    """Apply an approved live-vault transaction to a configured vault root."""

    transaction_plan = json.loads(transaction_plan_path.read_text(encoding="utf-8"))
    report = apply_live_vault_transaction(
        transaction_plan=transaction_plan,
        vault_root=vault_root,
        approval_ref=approval_ref,
        explicit_live_write_enable=explicit_live_write_enable,
        allow_real_obsidian_vault=allow_real_obsidian_vault,
        clean_git_status=clean_git_status,
    )
    report_path = write_live_vault_transaction_apply_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"vault live transaction apply: {report['status']}")
    print(f"report={report_path}")
    print(f"real_obsidian_vault_write_performed: {str(report['real_obsidian_vault_write_performed']).lower()}")
    return 0 if report["status"] == "applied" else 1


def _cmd_vault_live_config_status(*, instance_root: Path, yyyymmdd: str, request_id: str) -> int:
    """Write the Live-Obsidian-Config completion status report."""

    report = build_live_obsidian_config_status_report(request_id=request_id)
    report_path = write_live_obsidian_config_status_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"vault live config status: {report['status']}")
    print(f"report={report_path}")
    print(f"open_stage_count: {report['open_stage_count']}")
    print("real_obsidian_vault_write_performed: false")
    return 0 if report["status"] == "complete" and report["open_stage_count"] == 0 else 1


def _cmd_vault_topic_gatekeeper(*, instance_root: Path, yyyymmdd: str, request_id: str, registry_path: Path, proposed_topic_path: Path) -> int:
    """Write a read-only evidence-citing topic gatekeeper decision."""

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    proposed_topic = json.loads(proposed_topic_path.read_text(encoding="utf-8"))
    decision = build_topic_gatekeeper_decision(request_id=request_id, proposed_topic=proposed_topic, registry=registry)
    report_path = write_topic_gatekeeper_decision(instance_root=instance_root, yyyymmdd=yyyymmdd, decision=decision)
    action = decision["decision"]["action"]
    print(f"topic gatekeeper: {action}")
    print(f"report={report_path}")
    print("real_obsidian_vault_write_performed: false")
    return 0


def _cmd_vault_evidence_promotion_plan(*, instance_root: Path, yyyymmdd: str, request_path: Path) -> int:
    """Write a no-vault-write evidence promotion plan."""

    request = json.loads(request_path.read_text(encoding="utf-8"))
    plan = build_obsidian_evidence_promotion_plan(request=request)
    report_path = write_obsidian_evidence_promotion_plan(instance_root=instance_root, yyyymmdd=yyyymmdd, plan=plan)
    print(f"obsidian evidence promotion plan: {plan['status']}")
    print(f"planned_operation_count: {plan['planned_operation_count']}")
    print(f"report={report_path}")
    print("real_obsidian_vault_write_performed: false")
    return 0


def _cmd_vault_obsidian_milestone_status(*, instance_root: Path, yyyymmdd: str, request_id: str) -> int:
    """Write the completed Obsidian milestone status report."""

    report = build_obsidian_milestone_status_report(request_id=request_id)
    report_path = write_obsidian_milestone_status_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"obsidian milestone: {report['status']}")
    print(f"completed_milestone_count: {report['completed_milestone_count']}")
    print(f"open_milestone_count: {report['open_milestone_count']}")
    print(f"report={report_path}")
    print("real_obsidian_vault_write_performed: false")
    return 0 if report["obsidian_milestone_complete"] else 1


def _cmd_vault_git_fixture_init(
    *,
    instance_root: Path,
    yyyymmdd: str,
    plan_path: Path,
    fixture_vault_root: Path,
    fixture_remote_root: Path,
    fixture_git_only: bool,
) -> int:
    """Execute a Git initialization plan against fixture Git repos only."""

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    report = execute_obsidian_git_initialization_in_fixture(
        plan=plan,
        fixture_vault_root=fixture_vault_root,
        fixture_remote_root=fixture_remote_root,
        fixture_git_only=fixture_git_only,
    )
    report_path = write_obsidian_git_fixture_execution_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"obsidian git fixture init: {report['status']}")
    print(f"fixture_remote_push_performed: {str(report['fixture_remote_push_performed']).lower()}")
    print(f"external_call_made: {str(report['external_call_made']).lower()}")
    print(f"report={report_path}")
    return 0 if report["status"] == "applied" else 1


def _cmd_vault_git_fixture_sync(
    *,
    instance_root: Path,
    yyyymmdd: str,
    plan_path: Path,
    fixture_vault_root: Path,
    fixture_remote_root: Path,
    fixture_git_only: bool,
) -> int:
    """Execute a Git sync plan against fixture Git repos only."""

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    report = execute_obsidian_git_sync_in_fixture(
        plan=plan,
        fixture_vault_root=fixture_vault_root,
        fixture_remote_root=fixture_remote_root,
        fixture_git_only=fixture_git_only,
    )
    report_path = write_obsidian_git_fixture_execution_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"obsidian git fixture sync: {report['status']}")
    print(f"fixture_remote_push_performed: {str(report['fixture_remote_push_performed']).lower()}")
    print(f"external_call_made: {str(report['external_call_made']).lower()}")
    print(f"report={report_path}")
    return 0 if report["status"] == "applied" else 1


def _cmd_vault_git_live_sync(
    *,
    instance_root: Path,
    yyyymmdd: str,
    plan_path: Path,
    vault_root: Path,
    approval_ref: str | None,
    explicit_live_git_enable: bool,
    allow_real_obsidian_vault: bool,
    clean_git_status: bool,
) -> int:
    """Execute a Git sync plan against a live vault and configured remote."""

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    report = execute_obsidian_git_sync_live(
        plan=plan,
        vault_root=vault_root,
        approval_ref=approval_ref,
        explicit_live_git_enable=explicit_live_git_enable,
        allow_real_obsidian_vault=allow_real_obsidian_vault,
        clean_git_status=clean_git_status,
    )
    report_path = write_obsidian_git_live_execution_report(instance_root=instance_root, yyyymmdd=yyyymmdd, report=report)
    print(f"obsidian git live sync: {report['status']}")
    print(f"target_vault_git_mutation_performed: {str(report['target_vault_git_mutation_performed']).lower()}")
    print(f"network_push_performed: {str(report['network_push_performed']).lower()}")
    print(f"external_call_made: {str(report['external_call_made']).lower()}")
    print(f"report={report_path}")
    return 0 if report["status"] == "applied" else 1


def _cmd_vault_topic_transition_plan(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    action: str,
    source_topic_uid: str,
    target_topic_uid: str,
    approval_ref: str | None,
    rationale: str,
) -> int:
    """Plan non-destructive Obsidian topic identity transitions."""

    plan = build_topic_identity_transition_plan(
        request_id=request_id,
        action=action,
        source_topic_uid=source_topic_uid,
        target_topic_uid=target_topic_uid,
        approval_ref=approval_ref,
        rationale=rationale,
    )
    plan_path = write_topic_identity_transition_plan(instance_root=instance_root, yyyymmdd=yyyymmdd, plan=plan)
    print(f"topic transition plan: {plan['status']}")
    print(f"plan_ref: {plan_path.relative_to(instance_root)}")
    print("real_obsidian_vault_write_performed: false")
    return 0 if plan["status"] == "planned" else 2


def _cmd_live_ideation_run(
    *,
    instance_root: Path,
    request_path: Path,
    config_path: Path,
    yyyymmdd: str,
    doi: str,
    approval_ref: str,
    explicit_live_source_enable: bool,
    metadata_fixture: Path | None,
) -> int:
    """Run approved live-source ideation evidence through DARS and Chief Editor.

    This is the first autonomous live ideation increment: one command gates a
    read-only DOI metadata source access, records provenance, and feeds the
    resulting source refs into the existing domain/DARS/Chief Editor pipeline.
    """

    instance = InstanceRoot(instance_root)
    request = DomainInvestigationRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
    registry = load_source_connector_registry(config_path)
    if not explicit_live_source_enable:
        return _write_live_ideation_blocked_report(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request.request_id,
            reason_code="explicit_live_source_enable_required",
        )
    if os.environ.get("HISYS_ALLOW_LIVE_IDEATION") != "1":
        return _write_live_ideation_blocked_report(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request.request_id,
            reason_code="live_ideation_env_missing",
        )
    gate = SourceConnectorDispatchGate(instance=instance)
    decision = gate.evaluate(
        yyyymmdd=yyyymmdd,
        request_id=request.request_id,
        registry=registry,
        connector_id="doi_metadata_search",
        approval_ref=approval_ref,
        requested_domain="api.crossref.org",
        requested_actions=["read"],
    )
    dispatch_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/connector-dispatch-{request.request_id}-doi_metadata_search.json"
    if decision.decision != "allowed":
        return _write_live_ideation_blocked_report(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request.request_id,
            reason_code=decision.reason_code,
            dispatch_ref=dispatch_ref,
        )

    fetch = None
    transport_kind = "live_network"
    if metadata_fixture is not None:
        transport_kind = "fixture_injected"

        def fetch(url: str) -> tuple[int, str, str]:
            return 200, "application/json", metadata_fixture.read_text(encoding="utf-8")

    package = DoiMetadataConnector(fetch=fetch).collect(
        request_id=request.request_id,
        doi=doi,
        output_root=instance.root,
        yyyymmdd=yyyymmdd,
    )
    domain_status = _cmd_investigate_domain(
        instance_root=instance.root,
        request_path=request_path,
        yyyymmdd=yyyymmdd,
        live_source_access_refs=[package.access_ref],
        live_source_evidence_refs=[package.evidence_ref],
    )
    report = {
        "schema_id": "hisys.live_ideation.run_report",
        "schema_version": "0.1.0",
        "request_id": request.request_id,
        "status": "completed" if domain_status == 0 else "domain_investigation_failed",
        "mode": "approved_live_source_ideation",
        "approval_ref": approval_ref,
        "dispatch_ref": dispatch_ref,
        "source_access_refs": [package.access_ref],
        "source_evidence_refs": [package.evidence_ref],
        "transport_kind": transport_kind,
        "external_call_made": True,
        "mutation_performed": False,
        "dars_chief_editor_pipeline_invoked": domain_status == 0,
        "human_review_required": True,
    }
    report_path = _write_live_ideation_report(instance=instance, yyyymmdd=yyyymmdd, report=report)
    print(f"live ideation run: status={report['status']} report={report_path}")
    print("external_call_made: true")
    print("mutation_performed: false")
    return 0 if domain_status == 0 else 1


def _write_live_ideation_blocked_report(
    *,
    instance: InstanceRoot,
    yyyymmdd: str,
    request_id: str,
    reason_code: str | None,
    dispatch_ref: str | None = None,
) -> int:
    report = {
        "schema_id": "hisys.live_ideation.run_report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": "blocked",
        "mode": "approved_live_source_ideation",
        "reason_code": reason_code,
        "dispatch_ref": dispatch_ref,
        "source_access_refs": [],
        "source_evidence_refs": [],
        "external_call_made": False,
        "mutation_performed": False,
        "dars_chief_editor_pipeline_invoked": False,
        "human_review_required": True,
    }
    report_path = _write_live_ideation_report(instance=instance, yyyymmdd=yyyymmdd, report=report)
    print(f"live ideation run: status=blocked reason={reason_code} report={report_path}")
    return 2


def _write_live_ideation_report(*, instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live-ideation-run-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "live-ideation-run-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Live Ideation Run Report",
                "",
                f"- request_id: `{report['request_id']}`",
                f"- status: `{report['status']}`",
                f"- external_call_made: `{str(report['external_call_made']).lower()}`",
                f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
                f"- dars_chief_editor_pipeline_invoked: `{str(report['dars_chief_editor_pipeline_invoked']).lower()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def _cmd_live_ideation_persist(
    *,
    instance_root: Path,
    request_path: Path,
    config_path: Path,
    yyyymmdd: str,
    doi: str,
    approval_ref: str | None,
    vault_root: Path,
    remote_name: str,
    branch: str,
    credential_ref: str,
    commit_message: str | None,
    explicit_live_source_enable: bool,
    explicit_live_write_enable: bool,
    explicit_live_git_enable: bool,
    allow_real_obsidian_vault: bool,
    clean_git_status: bool,
    metadata_fixture: Path | None,
    standing_approval_policy: Path | None = None,
) -> int:
    """Run approved live ideation through vault persistence and Git sync."""

    instance = InstanceRoot(instance_root)
    request = DomainInvestigationRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
    policy = _resolve_live_ideation_standing_approval(
        policy_path=standing_approval_policy,
        request=request,
        yyyymmdd=yyyymmdd,
        vault_root=vault_root,
        remote_name=remote_name,
        branch=branch,
        credential_ref=credential_ref,
        explicit_approval_ref=approval_ref,
    )
    if policy["status"] != "approved":
        pipeline_report = _live_ideation_persist_report(
            request_id=request.request_id,
            approval_ref=str(approval_ref or policy.get("approval_ref") or ""),
            status="blocked",
            reason_code=str(policy["reason_code"]),
            standing_approval_policy_ref=str(standing_approval_policy) if standing_approval_policy else None,
            standing_approval_applied=False,
        )
        report_path = _write_live_ideation_persist_report(instance=instance, yyyymmdd=yyyymmdd, report=pipeline_report)
        print(f"live ideation persist: status=blocked report={report_path}")
        return 2
    approval_ref = str(policy["approval_ref"])
    standing_approval_applied = bool(policy["standing_approval_applied"])
    explicit_live_source_enable = explicit_live_source_enable or standing_approval_applied
    explicit_live_write_enable = explicit_live_write_enable or standing_approval_applied
    explicit_live_git_enable = explicit_live_git_enable or standing_approval_applied
    allow_real_obsidian_vault = allow_real_obsidian_vault or bool(policy["allow_real_obsidian_vault"])
    clean_git_status = clean_git_status or bool(policy["clean_git_status_required"])
    run_status = _cmd_live_ideation_run(
        instance_root=instance.root,
        request_path=request_path,
        config_path=config_path,
        yyyymmdd=yyyymmdd,
        doi=doi,
        approval_ref=approval_ref,
        explicit_live_source_enable=explicit_live_source_enable,
        metadata_fixture=metadata_fixture,
    )
    ideation_report_path = instance.reports_dir / "run-summaries" / yyyymmdd / "live-ideation-run-report.json"
    ideation_report = json.loads(ideation_report_path.read_text(encoding="utf-8")) if ideation_report_path.exists() else {}
    if run_status != 0:
        pipeline_report = _live_ideation_persist_report(
            request_id=request.request_id,
            approval_ref=approval_ref,
            status="blocked",
            reason_code="live_ideation_stage_failed",
            ideation_report_ref=str(ideation_report_path.relative_to(instance.root)) if ideation_report_path.exists() else None,
            standing_approval_policy_ref=str(standing_approval_policy) if standing_approval_policy else None,
            standing_approval_applied=standing_approval_applied,
        )
        report_path = _write_live_ideation_persist_report(instance=instance, yyyymmdd=yyyymmdd, report=pipeline_report)
        print(f"live ideation persist: status=blocked report={report_path}")
        return 2

    vault_ref = f"91 Hisys/Live Research/approved-ideation/live-ideation-{request.request_id}.json"
    transaction_plan = {
        "schema_id": "hisys.obsidian.live_vault_transaction_plan",
        "schema_version": "0.1.0",
        "request_id": f"{request.request_id}-PERSIST",
        "status": "planned_not_executable",
        "vault_root": str(vault_root),
        "planned_operation_count": 1,
        "planned_operations": [
            {
                "operation_id": "live-ideation-persist-op-0001",
                "operation": "write_live_ideation_review_projection",
                "vault_relative_ref": vault_ref,
                "approval_ref": approval_ref,
                "source_refs": ideation_report.get("source_access_refs", []),
                "evidence_refs": ideation_report.get("source_evidence_refs", []),
            }
        ],
        "live_write_enabled": explicit_live_write_enable,
        "external_call_made": False,
        "mutation_performed": False,
    }
    apply_report = apply_live_vault_transaction(
        transaction_plan=transaction_plan,
        vault_root=vault_root,
        approval_ref=approval_ref,
        explicit_live_write_enable=explicit_live_write_enable,
        allow_real_obsidian_vault=allow_real_obsidian_vault,
        clean_git_status=clean_git_status,
    )
    apply_report_path = write_live_vault_transaction_apply_report(instance_root=instance.root, yyyymmdd=yyyymmdd, report=apply_report)
    if apply_report.get("status") != "applied":
        pipeline_report = _live_ideation_persist_report(
            request_id=request.request_id,
            approval_ref=approval_ref,
            status="blocked",
            reason_code=str(apply_report.get("reason_code") or "vault_apply_failed"),
            ideation_report_ref=str(ideation_report_path.relative_to(instance.root)),
            vault_apply_report_ref=str(apply_report_path.relative_to(instance.root)),
            vault_refs=[vault_ref],
            standing_approval_policy_ref=str(standing_approval_policy) if standing_approval_policy else None,
            standing_approval_applied=standing_approval_applied,
        )
        report_path = _write_live_ideation_persist_report(instance=instance, yyyymmdd=yyyymmdd, report=pipeline_report)
        print(f"live ideation persist: status=blocked report={report_path}")
        return 2

    git_plan = build_obsidian_git_sync_plan(
        request_id=f"{request.request_id}-GIT-SYNC",
        vault_root=vault_root,
        memo_refs=[vault_ref],
        runtime_boundary_refs=[],
        commit_message=commit_message or f"chore(obsidian): persist live ideation {request.request_id}",
        remote_name=remote_name,
        branch=branch,
        credential_ref=credential_ref,
        approval_ref=approval_ref,
    )
    git_report = execute_obsidian_git_sync_live(
        plan=git_plan,
        vault_root=vault_root,
        approval_ref=approval_ref,
        explicit_live_git_enable=explicit_live_git_enable,
        allow_real_obsidian_vault=allow_real_obsidian_vault,
        clean_git_status=clean_git_status,
    )
    git_report_path = write_obsidian_git_live_execution_report(instance_root=instance.root, yyyymmdd=yyyymmdd, report=git_report)
    status = "completed" if git_report.get("status") == "applied" else "blocked"
    pipeline_report = _live_ideation_persist_report(
        request_id=request.request_id,
        approval_ref=approval_ref,
        status=status,
        reason_code=None if status == "completed" else str(git_report.get("reason_code") or "git_sync_failed"),
        ideation_report_ref=str(ideation_report_path.relative_to(instance.root)),
        vault_apply_report_ref=str(apply_report_path.relative_to(instance.root)),
        git_sync_report_ref=str(git_report_path.relative_to(instance.root)),
        vault_refs=[vault_ref],
        source_access_refs=list(ideation_report.get("source_access_refs", [])),
        source_evidence_refs=list(ideation_report.get("source_evidence_refs", [])),
        external_call_made=bool(ideation_report.get("external_call_made")) or bool(git_report.get("external_call_made")),
        real_obsidian_vault_write_performed=bool(apply_report.get("real_obsidian_vault_write_performed")),
        network_push_performed=bool(git_report.get("network_push_performed")),
        mutation_performed=bool(apply_report.get("mutation_performed")) or bool(git_report.get("mutation_performed")),
        standing_approval_policy_ref=str(standing_approval_policy) if standing_approval_policy else None,
        standing_approval_applied=standing_approval_applied,
    )
    report_path = _write_live_ideation_persist_report(instance=instance, yyyymmdd=yyyymmdd, report=pipeline_report)
    print(f"live ideation persist: status={status} report={report_path}")
    print(f"real_obsidian_vault_write_performed: {str(pipeline_report['real_obsidian_vault_write_performed']).lower()}")
    print(f"network_push_performed: {str(pipeline_report['network_push_performed']).lower()}")
    return 0 if status == "completed" else 2


def _resolve_live_ideation_standing_approval(
    *,
    policy_path: Path | None,
    request: DomainInvestigationRequest,
    yyyymmdd: str,
    vault_root: Path,
    remote_name: str,
    branch: str,
    credential_ref: str,
    explicit_approval_ref: str | None,
) -> dict[str, object]:
    if policy_path is None:
        if not explicit_approval_ref:
            return {"status": "blocked", "reason_code": "approval_ref_required", "approval_ref": None}
        return {
            "status": "approved",
            "approval_ref": explicit_approval_ref,
            "standing_approval_applied": False,
            "allow_real_obsidian_vault": False,
            "clean_git_status_required": False,
        }
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    approval_ref = policy.get("approval_ref")
    if not isinstance(approval_ref, str) or not approval_ref.strip():
        return {"status": "blocked", "reason_code": "standing_approval_ref_required", "approval_ref": approval_ref}
    if explicit_approval_ref and explicit_approval_ref != approval_ref:
        return {"status": "blocked", "reason_code": "standing_approval_ref_mismatch", "approval_ref": approval_ref}
    if policy.get("status") != "approved":
        return {"status": "blocked", "reason_code": "standing_approval_not_approved", "approval_ref": approval_ref}
    capabilities = set(policy.get("capabilities") or [])
    required = {"live_source_access", "live_vault_write", "obsidian_git_push"}
    if not required.issubset(capabilities):
        return {"status": "blocked", "reason_code": "standing_approval_missing_capability", "approval_ref": approval_ref}
    expires_on = policy.get("expires_on")
    if expires_on is not None and (not isinstance(expires_on, str) or len(expires_on) != 8 or not expires_on.isdigit()):
        return {"status": "blocked", "reason_code": "standing_approval_expiry_invalid", "approval_ref": approval_ref}
    if isinstance(expires_on, str) and expires_on and expires_on < yyyymmdd:
        return {"status": "blocked", "reason_code": "standing_approval_expired", "approval_ref": approval_ref}
    allowed_domains = policy.get("allowed_domains") or []
    if allowed_domains and request.domain not in allowed_domains:
        return {"status": "blocked", "reason_code": "standing_approval_domain_not_allowed", "approval_ref": approval_ref}
    allowed_vault_roots = {str(Path(root)) for root in policy.get("allowed_vault_roots") or []}
    if allowed_vault_roots and str(vault_root) not in allowed_vault_roots:
        return {"status": "blocked", "reason_code": "standing_approval_vault_root_not_allowed", "approval_ref": approval_ref}
    allowed_remote_names = set(policy.get("allowed_remote_names") or [])
    if allowed_remote_names and remote_name not in allowed_remote_names:
        return {"status": "blocked", "reason_code": "standing_approval_remote_not_allowed", "approval_ref": approval_ref}
    allowed_branches = set(policy.get("allowed_branches") or [])
    if allowed_branches and branch not in allowed_branches:
        return {"status": "blocked", "reason_code": "standing_approval_branch_not_allowed", "approval_ref": approval_ref}
    allowed_credential_refs = set(policy.get("allowed_credential_refs") or [])
    if allowed_credential_refs and credential_ref not in allowed_credential_refs:
        return {"status": "blocked", "reason_code": "standing_approval_credential_ref_not_allowed", "approval_ref": approval_ref}
    return {
        "status": "approved",
        "approval_ref": approval_ref,
        "standing_approval_applied": True,
        "allow_real_obsidian_vault": bool(policy.get("allow_real_obsidian_vault", False)),
        "clean_git_status_required": bool(policy.get("clean_git_status_required", True)),
    }


def _live_ideation_persist_report(
    *,
    request_id: str,
    approval_ref: str,
    status: str,
    reason_code: str | None = None,
    ideation_report_ref: str | None = None,
    vault_apply_report_ref: str | None = None,
    git_sync_report_ref: str | None = None,
    vault_refs: list[str] | None = None,
    source_access_refs: list[str] | None = None,
    source_evidence_refs: list[str] | None = None,
    external_call_made: bool = False,
    real_obsidian_vault_write_performed: bool = False,
    network_push_performed: bool = False,
    mutation_performed: bool = False,
    standing_approval_policy_ref: str | None = None,
    standing_approval_applied: bool = False,
) -> dict[str, object]:
    return {
        "schema_id": "hisys.live_ideation.persist_report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": status,
        "reason_code": reason_code,
        "approval_ref": approval_ref,
        "ideation_report_ref": ideation_report_ref,
        "vault_apply_report_ref": vault_apply_report_ref,
        "git_sync_report_ref": git_sync_report_ref,
        "vault_refs": vault_refs or [],
        "source_access_refs": source_access_refs or [],
        "source_evidence_refs": source_evidence_refs or [],
        "external_call_made": external_call_made,
        "real_obsidian_vault_write_performed": real_obsidian_vault_write_performed,
        "network_push_performed": network_push_performed,
        "mutation_performed": mutation_performed,
        "standing_approval_policy_ref": standing_approval_policy_ref,
        "standing_approval_applied": standing_approval_applied,
        "dars_chief_editor_pipeline_invoked": status == "completed",
        "human_review_required": True,
    }


def _write_live_ideation_persist_report(*, instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live-ideation-persist-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "live-ideation-persist-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Live Ideation Persist Report",
                "",
                f"- request_id: `{report['request_id']}`",
                f"- status: `{report['status']}`",
                f"- real_obsidian_vault_write_performed: `{str(report['real_obsidian_vault_write_performed']).lower()}`",
                f"- network_push_performed: `{str(report['network_push_performed']).lower()}`",
                f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
                f"- standing_approval_applied: `{str(report['standing_approval_applied']).lower()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def _write_live_autonomy_scheduler_tick_report(*, instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live-autonomy-scheduler-tick-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "live-autonomy-scheduler-tick-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Live Autonomy Scheduler Tick Report",
                "",
                f"- status: `{report['status']}`",
                f"- scheduler_ready: `{str(report['scheduler_ready']).lower()}`",
                f"- discovered_queue_count: `{report['discovered_queue_count']}`",
                f"- processed_queue_count: `{report['processed_queue_count']}`",
                f"- attention_count: `{report['attention_count']}`",
                f"- next_scheduler_action: `{report['next_scheduler_action']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def _live_autonomy_safe_report_segment(queue_id: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in queue_id).strip("._/")
    return cleaned or "queue"


def _live_autonomy_lifecycle_dirs(
    *,
    queue_dir: Path,
    active_dir: Path | None,
    done_dir: Path | None,
    attention_dir: Path | None,
    rejected_dir: Path | None,
) -> dict[str, Path]:
    parent = queue_dir.parent
    return {
        "incoming": queue_dir,
        "active": active_dir or (parent / "active"),
        "done": done_dir or (parent / "done"),
        "attention": attention_dir or (parent / "attention"),
        "rejected": rejected_dir or (parent / "rejected"),
    }


def _live_autonomy_unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(1, 10000):
        candidate = directory / f"{stem}-{index:04d}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("unable to allocate unique queue lifecycle path")


def _live_autonomy_copy_queue_to_active(*, queue_path: Path, active_dir: Path) -> str:
    active_path = _live_autonomy_unique_path(active_dir, queue_path.name)
    shutil.copy2(queue_path, active_path)
    return str(active_path)


def _live_autonomy_finalize_queue_file(*, queue_path: Path, active_copy: Path | None, destination_dir: Path) -> str:
    final_path = _live_autonomy_unique_path(destination_dir, queue_path.name)
    if queue_path.exists():
        shutil.move(str(queue_path), str(final_path))
    elif active_copy is not None and active_copy.exists():
        shutil.copy2(active_copy, final_path)
    else:
        final_path.write_text("", encoding="utf-8")
    if active_copy is not None and active_copy.exists():
        active_copy.unlink()
    return str(final_path)


LIVE_AUTONOMY_REPLAY_CLASSIFICATIONS = ["new", "same_hash_replay", "changed_same_entry_id", "duplicate_queue_content"]


def _live_autonomy_content_hash(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _live_autonomy_file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _live_autonomy_entry_hashes(queue: object) -> dict[str, str]:
    if not isinstance(queue, dict) or not isinstance(queue.get("entries"), list):
        return {}
    hashes: dict[str, str] = {}
    for index, entry in enumerate(queue["entries"], start=1):
        if isinstance(entry, dict):
            entry_id = str(entry.get("entry_id") or f"entry-{index:04d}").strip()
            if entry_id:
                hashes[entry_id] = _live_autonomy_content_hash(entry)
    return hashes


def _live_autonomy_queue_hash_index(paths: Iterable[Path]) -> dict[str, object]:
    queue_hashes: dict[str, set[str]] = {}
    entry_hashes: dict[str, set[str]] = {}
    for path in paths:
        if not path.is_file():
            continue
        try:
            queue = json.loads(path.read_text(encoding="utf-8"))
            queue_hash = _live_autonomy_content_hash(queue)
            queue_id = str(queue.get("queue_id") or path.stem) if isinstance(queue, dict) else path.stem
            current_entry_hashes = _live_autonomy_entry_hashes(queue)
        except json.JSONDecodeError:
            queue_hash = _live_autonomy_file_hash(path)
            queue_id = path.stem
            current_entry_hashes = {}
        queue_hashes.setdefault(queue_hash, set()).add(queue_id)
        for entry_id, entry_hash in current_entry_hashes.items():
            entry_hashes.setdefault(entry_id, set()).add(entry_hash)
    return {"queue_hashes": queue_hashes, "entry_hashes": entry_hashes}


def _live_autonomy_replay_classification(
    *,
    queue_id: str | None,
    queue_hash: str,
    entry_hashes: dict[str, str],
    prior_index: dict[str, object],
) -> str:
    prior_queue_hashes = prior_index.get("queue_hashes", {})
    prior_entry_hashes = prior_index.get("entry_hashes", {})
    matching_queue_ids = prior_queue_hashes.get(queue_hash, set()) if isinstance(prior_queue_hashes, dict) else set()
    if isinstance(matching_queue_ids, set) and queue_id and queue_id in matching_queue_ids:
        return "same_hash_replay"
    if isinstance(matching_queue_ids, set) and matching_queue_ids:
        return "duplicate_queue_content"
    if isinstance(prior_entry_hashes, dict):
        for entry_id, entry_hash in entry_hashes.items():
            prior_hashes = prior_entry_hashes.get(entry_id, set())
            if isinstance(prior_hashes, set) and prior_hashes and entry_hash not in prior_hashes:
                return "changed_same_entry_id"
    return "new"


def _validate_live_autonomy_candidate_queue(queue: object) -> tuple[bool, str | None, str | None]:
    if not isinstance(queue, dict):
        return False, "queue_not_object", None
    queue_id_raw = queue.get("queue_id")
    queue_id = str(queue_id_raw).strip() if queue_id_raw is not None else None
    if queue_id_raw is not None and (not queue_id or _live_autonomy_safe_report_segment(queue_id) != queue_id):
        return False, "queue_id_invalid", queue_id
    entries = queue.get("entries")
    if not isinstance(entries, list) or not entries:
        return False, "queue_entries_missing", queue_id
    entry_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            return False, "queue_entry_not_object", queue_id
        entry_id = str(entry.get("entry_id") or f"entry-{index:04d}").strip()
        if not entry_id:
            return False, "queue_entry_id_invalid", queue_id
        if entry_id in entry_ids:
            return False, "queue_entry_id_duplicate", queue_id
        entry_ids.add(entry_id)
        if not isinstance(entry.get("doi"), str) or not entry["doi"].strip():
            return False, "queue_entry_missing_doi", queue_id
        request_path = entry.get("request_path")
        if not isinstance(request_path, str) or not request_path.strip():
            return False, "queue_entry_missing_request", queue_id
        request_ref = Path(request_path)
        if request_ref.is_absolute() or ".." in request_ref.parts:
            return False, "queue_entry_request_path_unsafe", queue_id
    return True, None, queue_id


def _write_live_autonomy_admission_report(*, instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live-autonomy-admission-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (report_dir / "live-autonomy-admission-report.md").write_text(
        "\n".join(
            [
                "# Live Autonomy Admission Report",
                "",
                f"- status: `{report['status']}`",
                f"- admitted_count: `{report['admitted_count']}`",
                f"- rejected_count: `{report['rejected_count']}`",
                f"- processed_candidate_count: `{report['processed_candidate_count']}`",
                f"- external_call_made: `{str(report['external_call_made']).lower()}`",
                f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def _live_autonomy_read_json_if_present(path: Path) -> dict[str, object] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _live_autonomy_compact_counts(report: dict[str, object] | None, keys: list[str]) -> dict[str, int]:
    if report is None:
        return {key: 0 for key in keys}
    counts: dict[str, int] = {}
    for key in keys:
        value = report.get(key, 0)
        counts[key] = int(value) if isinstance(value, int) else 0
    return counts


def _write_live_autonomy_status_report(*, instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live-autonomy-status-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (report_dir / "live-autonomy-status-report.md").write_text(
        "\n".join(
            [
                "# Live Autonomy Status Dashboard",
                "",
                f"- status: `{report['status']}`",
                f"- health_status: `{report['health_status']}`",
                f"- next_operator_action: `{report['next_operator_action']}`",
                f"- admission_rejected_count: `{report['admission_summary']['rejected_count']}`",
                f"- scheduler_attention_count: `{report['scheduler_summary']['attention_count']}`",
                f"- watchdog_attention_count: `{report['watchdog_summary']['attention_count']}`",
                f"- ledger_completed_count: `{report['ledger_summary']['completed_count']}`",
                f"- ledger_attention_count: `{report['ledger_summary']['attention_count']}`",
                f"- hash_algorithm: `{report['hash_algorithm']}`",
                f"- ledger_entry_hash_count: `{report['hash_summary']['ledger_entry_hash_count']}`",
                f"- external_call_made: `{str(report['external_call_made']).lower()}`",
                f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
                f"- network_push_performed: `{str(report['network_push_performed']).lower()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def _cmd_live_autonomy_status(*, instance_root: Path, yyyymmdd: str, ledger_dir: Path | None) -> int:
    """Write a compact operator status dashboard from existing reports and ledgers."""

    instance = InstanceRoot(instance_root)
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    ledger_root = ledger_dir or (instance.data_dir / "live-autonomy-ledgers" / yyyymmdd)
    admission_path = report_dir / "live-autonomy-admission-report.json"
    scheduler_path = report_dir / "live-autonomy-scheduler-tick-report.json"
    admission = _live_autonomy_read_json_if_present(admission_path)
    scheduler = _live_autonomy_read_json_if_present(scheduler_path)

    watchdog_reports: list[dict[str, object]] = []
    watchdog_refs: list[str] = []
    if report_dir.exists():
        for watchdog_path in sorted(report_dir.rglob("live-autonomy-watchdog-report.json")):
            watchdog = _live_autonomy_read_json_if_present(watchdog_path)
            if watchdog is not None:
                watchdog_reports.append(watchdog)
                watchdog_refs.append(str(watchdog_path))

    ledger_files = sorted(ledger_root.glob("*.json")) if ledger_root.exists() else []
    ledger_entries: list[dict[str, object]] = []
    ledger_queue_hashes: list[str] = []
    ledger_entry_hashes: dict[str, str] = {}
    for ledger_path in ledger_files:
        ledger = _live_autonomy_read_json_if_present(ledger_path)
        entries = ledger.get("entries", {}) if ledger else {}
        if ledger and isinstance(ledger.get("queue_hash"), str):
            ledger_queue_hashes.append(str(ledger["queue_hash"]))
        entry_hash_map = ledger.get("entry_hashes", {}) if ledger else {}
        if isinstance(entry_hash_map, dict):
            for entry_id, entry_hash in entry_hash_map.items():
                if isinstance(entry_id, str) and isinstance(entry_hash, str):
                    ledger_entry_hashes[entry_id] = entry_hash
        if isinstance(entries, dict):
            for entry in entries.values():
                if isinstance(entry, dict):
                    ledger_entries.append(entry)

    admission_counts = _live_autonomy_compact_counts(
        admission,
        ["discovered_candidate_count", "processed_candidate_count", "admitted_count", "rejected_count"],
    )
    scheduler_counts = _live_autonomy_compact_counts(
        scheduler,
        ["discovered_queue_count", "processed_queue_count", "attention_count"],
    )
    watchdog_attention_count = sum(1 for item in watchdog_reports if item.get("health_status") == "attention_required")
    retry_eligible_count = sum(int(item.get("retry_eligible_count", 0)) for item in watchdog_reports if isinstance(item.get("retry_eligible_count", 0), int))
    ledger_completed_count = sum(1 for entry in ledger_entries if entry.get("status") in {"completed", "skipped_completed"})
    ledger_attention_count = sum(
        1
        for entry in ledger_entries
        if entry.get("status") in {"blocked", "skipped_retry_exhausted", "skipped_non_retryable"}
    )
    missing_sources = [
        name
        for name, present in {
            "admission_report": admission is not None,
            "scheduler_tick_report": scheduler is not None,
        }.items()
        if not present
    ]
    attention_count = admission_counts["rejected_count"] + scheduler_counts["attention_count"] + watchdog_attention_count + ledger_attention_count
    admission_hashes = admission.get("queue_hashes", []) if admission else []
    scheduler_hashes = scheduler.get("queue_hashes", []) if scheduler else []
    status = "idle" if not admission and not scheduler and not watchdog_reports and not ledger_entries else ("attention_required" if attention_count else "ok")
    health_status = "attention_required" if attention_count else "ok"
    report = {
        "schema_id": "hisys.live_autonomy.status_dashboard",
        "schema_version": "0.1.0",
        "status": status,
        "health_status": health_status,
        "scheduler_ready": True,
        "date": yyyymmdd,
        "next_operator_action": "review_attention_artifacts" if attention_count else "sleep",
        "missing_source_reports": missing_sources,
        "hash_algorithm": "sha256",
        "hash_summary": {
            "admission_queue_hashes": admission_hashes if isinstance(admission_hashes, list) else [],
            "scheduler_queue_hashes": scheduler_hashes if isinstance(scheduler_hashes, list) else [],
            "ledger_queue_hashes": ledger_queue_hashes,
            "ledger_entry_hash_count": len(ledger_entry_hashes),
        },
        "admission_summary": {
            **admission_counts,
            "report_ref": str(admission_path) if admission is not None else None,
            "status": admission.get("status") if admission else "missing",
        },
        "scheduler_summary": {
            **scheduler_counts,
            "report_ref": str(scheduler_path) if scheduler is not None else None,
            "status": scheduler.get("status") if scheduler else "missing",
            "next_scheduler_action": scheduler.get("next_scheduler_action") if scheduler else None,
        },
        "watchdog_summary": {
            "report_count": len(watchdog_reports),
            "attention_count": watchdog_attention_count,
            "retry_eligible_count": retry_eligible_count,
            "report_refs": watchdog_refs,
        },
        "ledger_summary": {
            "ledger_dir": str(ledger_root),
            "ledger_file_count": len(ledger_files),
            "entry_count": len(ledger_entries),
            "completed_count": ledger_completed_count,
            "attention_count": ledger_attention_count,
        },
        "external_call_made": False,
        "mutation_performed": False,
        "network_push_performed": False,
    }
    report_path = _write_live_autonomy_status_report(instance=instance, yyyymmdd=yyyymmdd, report=report)
    print(f"live autonomy status: status={status} health={health_status} attention={attention_count} report={report_path}")
    return 0


def _cmd_live_autonomy_admit(
    *,
    instance_root: Path,
    candidate_dir: Path,
    candidate_glob: str,
    incoming_dir: Path,
    rejected_dir: Path,
    yyyymmdd: str,
    max_candidates: int,
) -> int:
    """Validate candidate queue files before admitting them to incoming."""

    instance = InstanceRoot(instance_root)
    prior_paths = []
    for existing_dir in (incoming_dir, rejected_dir):
        if existing_dir.exists():
            prior_paths.extend(path for path in existing_dir.glob(candidate_glob) if path.is_file())
    prior_index = _live_autonomy_queue_hash_index(prior_paths)
    discovered = sorted(path for path in candidate_dir.glob(candidate_glob) if path.is_file()) if candidate_dir.exists() else []
    selected = discovered[: max(0, max_candidates)]
    results: list[dict[str, object]] = []
    for candidate_path in selected:
        status = "rejected"
        reason_code: str | None = None
        queue_id: str | None = candidate_path.stem
        queue_hash = _live_autonomy_file_hash(candidate_path)
        entry_hashes: dict[str, str] = {}
        try:
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            queue_hash = _live_autonomy_content_hash(candidate)
            entry_hashes = _live_autonomy_entry_hashes(candidate)
            accepted, reason_code, validated_queue_id = _validate_live_autonomy_candidate_queue(candidate)
            queue_id = validated_queue_id or candidate_path.stem
        except json.JSONDecodeError:
            accepted = False
            reason_code = "queue_json_invalid"
        replay_classification = _live_autonomy_replay_classification(
            queue_id=queue_id,
            queue_hash=queue_hash,
            entry_hashes=entry_hashes,
            prior_index=prior_index,
        )
        destination = incoming_dir if accepted else rejected_dir
        try:
            final_ref = _live_autonomy_unique_path(destination, candidate_path.name)
            shutil.move(str(candidate_path), str(final_ref))
        except RuntimeError:
            accepted = False
            status = "rejected"
            reason_code = "lifecycle_path_exhausted"
            final_ref = None
        if accepted:
            status = "admitted"
        results.append(
            {
                "candidate_path": str(candidate_path),
                "queue_id": queue_id,
                "hash_algorithm": "sha256",
                "queue_hash": queue_hash,
                "entry_hashes": entry_hashes,
                "replay_classification": replay_classification,
                "status": status,
                "reason_code": reason_code,
                "final_ref": str(final_ref) if final_ref is not None else None,
                "external_call_made": False,
                "mutation_performed": False,
                "network_push_performed": False,
            }
        )
    rejected_count = sum(1 for result in results if result["status"] == "rejected")
    admitted_count = sum(1 for result in results if result["status"] == "admitted")
    replay_counts = {classification: sum(1 for result in results if result.get("replay_classification") == classification) for classification in LIVE_AUTONOMY_REPLAY_CLASSIFICATIONS}
    report = {
        "schema_id": "hisys.live_autonomy.admission_report",
        "schema_version": "0.1.0",
        "status": "idle" if not selected else ("completed" if rejected_count == 0 else "attention_required"),
        "candidate_dir": str(candidate_dir),
        "candidate_glob": candidate_glob,
        "incoming_dir": str(incoming_dir),
        "rejected_dir": str(rejected_dir),
        "discovered_candidate_count": len(discovered),
        "processed_candidate_count": len(selected),
        "admitted_count": admitted_count,
        "rejected_count": rejected_count,
        "hash_algorithm": "sha256",
        "queue_hashes": [result["queue_hash"] for result in results if result.get("queue_hash")],
        "replay_classification_counts": replay_counts,
        "external_call_made": False,
        "mutation_performed": False,
        "network_push_performed": False,
        "results": results,
    }
    report_path = _write_live_autonomy_admission_report(instance=instance, yyyymmdd=yyyymmdd, report=report)
    print(f"live autonomy admit: status={report['status']} admitted={admitted_count} rejected={rejected_count} report={report_path}")
    return 0


def _cmd_live_autonomy_tick(
    *,
    instance_root: Path,
    queue_dir: Path,
    queue_glob: str,
    config_path: Path,
    yyyymmdd: str,
    vault_root: Path,
    credential_ref: str,
    standing_approval_policy: Path,
    remote_name: str,
    branch: str,
    allow_real_obsidian_vault: bool,
    clean_git_status: bool,
    max_queues: int,
    max_items: int | None,
    ledger_dir: Path | None,
    max_retries: int,
    queue_lifecycle: bool,
    active_dir: Path | None,
    done_dir: Path | None,
    attention_dir: Path | None,
    rejected_dir: Path | None,
) -> int:
    """Run one cron-ready scheduler tick over discovered live autonomy queues."""

    instance = InstanceRoot(instance_root)
    lifecycle_dirs = _live_autonomy_lifecycle_dirs(
        queue_dir=queue_dir,
        active_dir=active_dir,
        done_dir=done_dir,
        attention_dir=attention_dir,
        rejected_dir=rejected_dir,
    )
    discovered = sorted(path for path in queue_dir.glob(queue_glob) if path.is_file()) if queue_dir.exists() else []
    selected = discovered[: max(0, max_queues)]
    queue_results: list[dict[str, object]] = []
    for queue_path in selected:
        queue_id = queue_path.stem
        lifecycle_active_ref = None
        lifecycle_final_ref = None
        queue_hash = _live_autonomy_file_hash(queue_path)
        entry_hashes: dict[str, str] = {}
        if queue_lifecycle:
            lifecycle_active_ref = _live_autonomy_copy_queue_to_active(queue_path=queue_path, active_dir=lifecycle_dirs["active"])
        try:
            queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
            queue_hash = _live_autonomy_content_hash(queue_data)
            entry_hashes = _live_autonomy_entry_hashes(queue_data)
            queue_id = str(queue_data.get("queue_id") or queue_path.stem)
        except json.JSONDecodeError:
            if queue_lifecycle:
                lifecycle_final_ref = _live_autonomy_finalize_queue_file(
                    queue_path=queue_path,
                    active_copy=Path(lifecycle_active_ref) if lifecycle_active_ref else None,
                    destination_dir=lifecycle_dirs["rejected"],
                )
            queue_results.append(
                {
                    "queue_path": str(queue_path),
                    "queue_id": queue_id,
                    "hash_algorithm": "sha256",
                    "queue_hash": queue_hash,
                    "entry_hashes": entry_hashes,
                    "status": "blocked",
                    "reason_code": "queue_json_invalid",
                    "queue_run_report_ref": None,
                    "watchdog_report_ref": None,
                    "lifecycle_active_ref": lifecycle_active_ref,
                    "lifecycle_final_ref": lifecycle_final_ref,
                    "lifecycle_state": "rejected" if queue_lifecycle else None,
                }
            )
            continue
        ledger_path = (ledger_dir / f"{queue_id}.json") if ledger_dir else None
        report_subdir = _live_autonomy_safe_report_segment(queue_id)
        status_code = _cmd_live_autonomy_run(
            instance_root=instance.root,
            queue_path=queue_path,
            config_path=config_path,
            yyyymmdd=yyyymmdd,
            vault_root=vault_root,
            credential_ref=credential_ref,
            standing_approval_policy=standing_approval_policy,
            remote_name=remote_name,
            branch=branch,
            allow_real_obsidian_vault=allow_real_obsidian_vault,
            clean_git_status=clean_git_status,
            max_items=max_items,
            ledger_path=ledger_path,
            max_retries=max_retries,
            report_subdir=report_subdir,
        )
        run_report_path = instance.reports_dir / "run-summaries" / yyyymmdd / report_subdir / "live-autonomy-run-report.json"
        run_report = json.loads(run_report_path.read_text(encoding="utf-8")) if run_report_path.exists() else {}
        lifecycle_state = None
        if queue_lifecycle:
            lifecycle_state = "done" if status_code == 0 else "attention"
            lifecycle_final_ref = _live_autonomy_finalize_queue_file(
                queue_path=queue_path,
                active_copy=Path(lifecycle_active_ref) if lifecycle_active_ref else None,
                destination_dir=lifecycle_dirs[lifecycle_state],
            )
        queue_results.append(
            {
                "queue_path": str(queue_path),
                "queue_id": queue_id,
                "hash_algorithm": "sha256",
                "queue_hash": queue_hash,
                "entry_hashes": entry_hashes,
                "status": "completed" if status_code == 0 else "attention_required",
                "reason_code": None if status_code == 0 else "queue_run_attention_required",
                "queue_run_report_ref": str(run_report_path.relative_to(instance.root)) if run_report_path.exists() else None,
                "watchdog_report_ref": run_report.get("watchdog_report_ref"),
                "completed_count": run_report.get("completed_count", 0),
                "blocked_count": run_report.get("blocked_count", 0),
                "retry_eligible_count": run_report.get("retry_eligible_count", 0),
                "lifecycle_active_ref": lifecycle_active_ref,
                "lifecycle_final_ref": lifecycle_final_ref,
                "lifecycle_state": lifecycle_state,
            }
        )
    attention_count = sum(1 for result in queue_results if result["status"] != "completed")
    tick_report = {
        "schema_id": "hisys.live_autonomy.scheduler_tick_report",
        "schema_version": "0.1.0",
        "status": "idle" if not selected and attention_count == 0 else ("completed" if attention_count == 0 else "attention_required"),
        "scheduler_ready": True,
        "queue_dir": str(queue_dir),
        "queue_glob": queue_glob,
        "queue_lifecycle_enabled": queue_lifecycle,
        "queue_lifecycle_dirs": {key: str(value) for key, value in lifecycle_dirs.items()} if queue_lifecycle else {},
        "discovered_queue_count": len(discovered),
        "processed_queue_count": len(selected),
        "hash_algorithm": "sha256",
        "queue_hashes": [result["queue_hash"] for result in queue_results if result.get("queue_hash")],
        "attention_count": attention_count,
        "next_scheduler_action": "sleep" if attention_count == 0 else "review_queue_results",
        "queue_results": queue_results,
    }
    report_path = _write_live_autonomy_scheduler_tick_report(instance=instance, yyyymmdd=yyyymmdd, report=tick_report)
    print(f"live autonomy tick: status={tick_report['status']} processed={len(selected)} attention={attention_count} report={report_path}")
    return 0 if attention_count == 0 else 2


def _cmd_live_autonomy_run(
    *,
    instance_root: Path,
    queue_path: Path,
    config_path: Path,
    yyyymmdd: str,
    vault_root: Path,
    credential_ref: str,
    standing_approval_policy: Path,
    remote_name: str,
    branch: str,
    allow_real_obsidian_vault: bool,
    clean_git_status: bool,
    max_items: int | None,
    ledger_path: Path | None,
    max_retries: int,
    report_subdir: str | None,
) -> int:
    """Run a standing-approved queue of autonomous live ideation persistence jobs."""

    instance = InstanceRoot(instance_root)
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue_hash = _live_autonomy_content_hash(queue)
    entry_hashes = _live_autonomy_entry_hashes(queue)
    queue_id = str(queue.get("queue_id") or queue_path.stem)
    ledger_path = ledger_path or (instance.data_dir / "live-autonomy-ledgers" / yyyymmdd / f"{queue_id}.json")
    report_subdir = report_subdir or ""
    ledger = _load_live_autonomy_ledger(ledger_path=ledger_path, queue_id=queue_id, yyyymmdd=yyyymmdd)
    entries = list(queue.get("entries") or [])
    if max_items is not None:
        entries = entries[:max(0, max_items)]
    results: list[dict[str, object]] = []
    queue_dir = queue_path.parent
    for index, entry in enumerate(entries, start=1):
        entry_id = str(entry.get("entry_id") or f"entry-{index:04d}")
        entry_hash = entry_hashes.get(entry_id)
        ledger_entry = ledger["entries"].get(entry_id, {})
        ledger_entry = _live_autonomy_mark_transition(ledger_entry, state="queued", yyyymmdd=yyyymmdd, reason_code=None)
        if ledger_entry.get("status") == "completed":
            ledger_entry = _live_autonomy_mark_transition(ledger_entry, state="skipped_completed", yyyymmdd=yyyymmdd, reason_code="ledger_completed")
            results.append(
                {
                    "entry_id": entry_id,
                    "entry_hash": entry_hash,
                    "request_id": ledger_entry.get("request_id"),
                    "status": "skipped_completed",
                    "reason_code": "ledger_completed",
                    "pipeline_report_ref": ledger_entry.get("pipeline_report_ref"),
                    "vault_refs": ledger_entry.get("vault_refs", []),
                    "attempt_count": int(ledger_entry.get("attempt_count", 0)),
                    "retry_eligible": False,
                    "external_call_made": False,
                    "mutation_performed": False,
                    "network_push_performed": False,
                }
            )
            ledger["entries"][entry_id] = ledger_entry
            continue
        if ledger_entry.get("status") == "blocked" and ledger_entry.get("retry_eligible") is False:
            ledger_entry = _live_autonomy_mark_transition(ledger_entry, state="skipped_non_retryable", yyyymmdd=yyyymmdd, reason_code="non_retryable_blocked")
            results.append(
                {
                    "entry_id": entry_id,
                    "entry_hash": entry_hash,
                    "request_id": ledger_entry.get("request_id"),
                    "status": "skipped_non_retryable",
                    "reason_code": "non_retryable_blocked",
                    "pipeline_report_ref": ledger_entry.get("pipeline_report_ref"),
                    "vault_refs": ledger_entry.get("vault_refs", []),
                    "attempt_count": int(ledger_entry.get("attempt_count", 0)),
                    "retry_eligible": False,
                    "external_call_made": False,
                    "mutation_performed": False,
                    "network_push_performed": False,
                }
            )
            ledger["entries"][entry_id] = ledger_entry
            continue
        if int(ledger_entry.get("attempt_count", 0)) >= max_retries and ledger_entry.get("status") == "blocked":
            ledger_entry = _live_autonomy_mark_transition(ledger_entry, state="skipped_retry_exhausted", yyyymmdd=yyyymmdd, reason_code="retry_limit_exhausted")
            results.append(
                {
                    "entry_id": entry_id,
                    "entry_hash": entry_hash,
                    "request_id": ledger_entry.get("request_id"),
                    "status": "skipped_retry_exhausted",
                    "reason_code": "retry_limit_exhausted",
                    "pipeline_report_ref": ledger_entry.get("pipeline_report_ref"),
                    "vault_refs": ledger_entry.get("vault_refs", []),
                    "attempt_count": int(ledger_entry.get("attempt_count", 0)),
                    "retry_eligible": False,
                    "external_call_made": False,
                    "mutation_performed": False,
                    "network_push_performed": False,
                }
            )
            ledger["entries"][entry_id] = ledger_entry
            continue
        request_ref = entry.get("request_path")
        doi = entry.get("doi")
        if not isinstance(request_ref, str) or not isinstance(doi, str) or not doi.strip():
            result = {
                "entry_id": entry_id,
                "entry_hash": entry_hash,
                "status": "blocked",
                "reason_code": "queue_entry_missing_request_or_doi",
                "pipeline_report_ref": None,
                "attempt_count": int(ledger_entry.get("attempt_count", 0)) + 1,
                "retry_eligible": False,
                "external_call_made": False,
                "mutation_performed": False,
                "network_push_performed": False,
            }
            results.append(result)
            ledger_entry = _live_autonomy_mark_transition(ledger_entry, state="blocked", yyyymmdd=yyyymmdd, reason_code="queue_entry_missing_request_or_doi")
            ledger["entries"][entry_id] = _live_autonomy_ledger_entry_from_result(previous=ledger_entry, result=result)
            continue
        request_path = Path(request_ref)
        if not request_path.is_absolute():
            request_path = queue_dir / request_path
        metadata_fixture = entry.get("metadata_fixture")
        metadata_fixture_path = Path(metadata_fixture) if isinstance(metadata_fixture, str) and metadata_fixture else None
        if metadata_fixture_path is not None and not metadata_fixture_path.is_absolute():
            metadata_fixture_path = queue_dir / metadata_fixture_path
        entry_instance_root = instance.data_dir / "autonomy-runs" / yyyymmdd / entry_id
        ledger_entry = _live_autonomy_mark_transition(ledger_entry, state="running", yyyymmdd=yyyymmdd, reason_code=None)
        status_code = _cmd_live_ideation_persist(
            instance_root=entry_instance_root,
            request_path=request_path,
            config_path=config_path,
            yyyymmdd=yyyymmdd,
            doi=doi,
            approval_ref=None,
            vault_root=vault_root,
            remote_name=remote_name,
            branch=branch,
            credential_ref=credential_ref,
            commit_message=entry.get("commit_message") if isinstance(entry.get("commit_message"), str) else None,
            explicit_live_source_enable=False,
            explicit_live_write_enable=False,
            explicit_live_git_enable=False,
            allow_real_obsidian_vault=allow_real_obsidian_vault,
            clean_git_status=clean_git_status,
            metadata_fixture=metadata_fixture_path,
            standing_approval_policy=standing_approval_policy,
        )
        report_path = entry_instance_root / "reports" / "run-summaries" / yyyymmdd / "live-ideation-persist-report.json"
        entry_report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
        attempt_count = int(ledger_entry.get("attempt_count", 0)) + 1
        result = {
            "entry_id": entry_id,
            "entry_hash": entry_hash,
            "request_id": entry_report.get("request_id"),
            "status": "completed" if status_code == 0 else "blocked",
            "reason_code": entry_report.get("reason_code"),
            "pipeline_report_ref": str(report_path.relative_to(instance.root)) if report_path.exists() else None,
            "vault_refs": entry_report.get("vault_refs", []),
            "attempt_count": attempt_count,
            "retry_eligible": status_code != 0 and attempt_count < max_retries and _live_autonomy_reason_retryable(entry_report.get("reason_code")),
            "external_call_made": bool(entry_report.get("external_call_made")),
            "mutation_performed": bool(entry_report.get("mutation_performed")),
            "network_push_performed": bool(entry_report.get("network_push_performed")),
        }
        ledger_entry = _live_autonomy_mark_transition(
            ledger_entry,
            state="completed" if status_code == 0 else "blocked",
            yyyymmdd=yyyymmdd,
            reason_code=result.get("reason_code"),
        )
        results.append(result)
        ledger["entries"][entry_id] = _live_autonomy_ledger_entry_from_result(previous=ledger_entry, result=result)
    completed_count = sum(1 for result in results if result["status"] == "completed")
    skipped_completed_count = sum(1 for result in results if result["status"] == "skipped_completed")
    skipped_retry_exhausted_count = sum(1 for result in results if result["status"] == "skipped_retry_exhausted")
    skipped_non_retryable_count = sum(1 for result in results if result["status"] == "skipped_non_retryable")
    blocked_count = sum(1 for result in results if result["status"] == "blocked")
    retry_eligible_count = sum(1 for result in results if result.get("retry_eligible"))
    ledger["hash_algorithm"] = "sha256"
    ledger["queue_hash"] = queue_hash
    ledger["entry_hashes"] = entry_hashes
    ledger["summary"] = {
        "entry_count": len(results),
        "completed_count": completed_count,
        "blocked_count": blocked_count,
        "skipped_completed_count": skipped_completed_count,
        "skipped_retry_exhausted_count": skipped_retry_exhausted_count,
        "skipped_non_retryable_count": skipped_non_retryable_count,
        "retry_eligible_count": retry_eligible_count,
    }
    _write_live_autonomy_ledger(ledger_path=ledger_path, ledger=ledger)
    watchdog_report = {
        "schema_id": "hisys.live_autonomy.watchdog_report",
        "schema_version": "0.1.0",
        "queue_id": queue_id,
        "hash_algorithm": "sha256",
        "queue_hash": queue_hash,
        "entry_hashes": entry_hashes,
        "scheduler_ready": True,
        "health_status": "ok" if blocked_count == 0 and retry_eligible_count == 0 else "attention_required",
        "entry_count": len(results),
        "completed_count": completed_count,
        "blocked_count": blocked_count,
        "skipped_completed_count": skipped_completed_count,
        "skipped_retry_exhausted_count": skipped_retry_exhausted_count,
        "skipped_non_retryable_count": skipped_non_retryable_count,
        "retry_eligible_count": retry_eligible_count,
        "ledger_ref": str(ledger_path.relative_to(instance.root)) if ledger_path.is_relative_to(instance.root) else str(ledger_path),
        "next_scheduler_action": "sleep" if blocked_count == 0 and retry_eligible_count == 0 else "review_or_retry_eligible_entries",
    }
    watchdog_report_path = _write_live_autonomy_watchdog_report(instance=instance, yyyymmdd=yyyymmdd, report=watchdog_report, report_subdir=report_subdir)
    batch_report = {
        "schema_id": "hisys.live_autonomy.queue_run_report",
        "schema_version": "0.1.0",
        "queue_id": queue.get("queue_id"),
        "hash_algorithm": "sha256",
        "queue_hash": queue_hash,
        "entry_hashes": entry_hashes,
        "status": "completed" if blocked_count == 0 else "completed_with_blocks",
        "ledger_ref": str(ledger_path.relative_to(instance.root)) if ledger_path.is_relative_to(instance.root) else str(ledger_path),
        "watchdog_report_ref": str(watchdog_report_path.relative_to(instance.root)),
        "entry_count": len(results),
        "completed_count": completed_count,
        "blocked_count": blocked_count,
        "skipped_completed_count": skipped_completed_count,
        "skipped_retry_exhausted_count": skipped_retry_exhausted_count,
        "skipped_non_retryable_count": skipped_non_retryable_count,
        "retry_eligible_count": retry_eligible_count,
        "max_retries": max_retries,
        "standing_approval_policy_ref": str(standing_approval_policy),
        "external_call_made": any(result["external_call_made"] for result in results),
        "mutation_performed": any(result["mutation_performed"] for result in results),
        "network_push_performed": any(result["network_push_performed"] for result in results),
        "results": results,
    }
    report_path = _write_live_autonomy_run_report(instance=instance, yyyymmdd=yyyymmdd, report=batch_report, report_subdir=report_subdir)
    print(f"live autonomy run: status={batch_report['status']} completed={completed_count} blocked={blocked_count} report={report_path}")
    return 0 if blocked_count == 0 else 2


def _load_live_autonomy_ledger(*, ledger_path: Path, queue_id: str, yyyymmdd: str) -> dict[str, object]:
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        entries = ledger.get("entries")
        if not isinstance(entries, dict):
            ledger["entries"] = {}
        return ledger
    return {
        "schema_id": "hisys.live_autonomy.queue_retry_ledger",
        "schema_version": "0.1.0",
        "queue_id": queue_id,
        "date": yyyymmdd,
        "entries": {},
        "summary": {},
    }


def _write_live_autonomy_ledger(*, ledger_path: Path, ledger: dict[str, object]) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _live_autonomy_reason_retryable(reason_code: object) -> bool:
    if not isinstance(reason_code, str):
        return False
    non_retryable = {
        "queue_entry_missing_request_or_doi",
        "standing_approval_ref_required",
        "standing_approval_ref_mismatch",
        "standing_approval_not_approved",
        "standing_approval_missing_capability",
        "standing_approval_expiry_invalid",
        "standing_approval_expired",
        "standing_approval_domain_not_allowed",
        "standing_approval_vault_root_not_allowed",
        "standing_approval_remote_not_allowed",
        "standing_approval_branch_not_allowed",
        "standing_approval_credential_ref_not_allowed",
    }
    return reason_code not in non_retryable


def _live_autonomy_mark_transition(entry: dict[str, object], *, state: str, yyyymmdd: str, reason_code: object) -> dict[str, object]:
    updated = dict(entry)
    history = list(updated.get("state_history") or [])
    if not history or history[-1].get("state") != state:
        transition: dict[str, object] = {"state": state, "run_date": yyyymmdd}
        if reason_code:
            transition["reason_code"] = reason_code
        history.append(transition)
    updated["current_state"] = state
    updated["state_history"] = history
    return updated


def _live_autonomy_ledger_entry_from_result(*, previous: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    attempt_count = int(result.get("attempt_count") or previous.get("attempt_count") or 0)
    return {
        "entry_id": result.get("entry_id"),
        "entry_hash": result.get("entry_hash") or previous.get("entry_hash"),
        "request_id": result.get("request_id") or previous.get("request_id"),
        "status": result.get("status"),
        "current_state": previous.get("current_state") or result.get("status"),
        "state_history": previous.get("state_history", []),
        "reason_code": result.get("reason_code"),
        "pipeline_report_ref": result.get("pipeline_report_ref"),
        "vault_refs": result.get("vault_refs", []),
        "attempt_count": attempt_count,
        "retry_eligible": bool(result.get("retry_eligible")),
        "external_call_made": bool(result.get("external_call_made")),
        "mutation_performed": bool(result.get("mutation_performed")),
        "network_push_performed": bool(result.get("network_push_performed")),
    }


def _write_live_autonomy_watchdog_report(*, instance: InstanceRoot, yyyymmdd: str, report: dict[str, object], report_subdir: str = "") -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    if report_subdir:
        report_dir = report_dir / report_subdir
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live-autonomy-watchdog-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "live-autonomy-watchdog-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Live Autonomy Watchdog Report",
                "",
                f"- queue_id: `{report['queue_id']}`",
                f"- scheduler_ready: `{str(report['scheduler_ready']).lower()}`",
                f"- health_status: `{report['health_status']}`",
                f"- next_scheduler_action: `{report['next_scheduler_action']}`",
                f"- retry_eligible_count: `{report['retry_eligible_count']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def _write_live_autonomy_run_report(*, instance: InstanceRoot, yyyymmdd: str, report: dict[str, object], report_subdir: str = "") -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    if report_subdir:
        report_dir = report_dir / report_subdir
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live-autonomy-run-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "live-autonomy-run-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Live Autonomy Queue Run Report",
                "",
                f"- queue_id: `{report['queue_id']}`",
                f"- status: `{report['status']}`",
                f"- entry_count: `{report['entry_count']}`",
                f"- completed_count: `{report['completed_count']}`",
                f"- blocked_count: `{report['blocked_count']}`",
                f"- skipped_completed_count: `{report['skipped_completed_count']}`",
                f"- skipped_retry_exhausted_count: `{report['skipped_retry_exhausted_count']}`",
                f"- skipped_non_retryable_count: `{report.get('skipped_non_retryable_count', 0)}`",
                f"- retry_eligible_count: `{report['retry_eligible_count']}`",
                f"- ledger_ref: `{report['ledger_ref']}`",
                f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
                f"- network_push_performed: `{str(report['network_push_performed']).lower()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_path


def _cmd_plan_source_connectors(instance_root: Path, request_path: Path, config_path: Path, yyyymmdd: str) -> int:
    """Write a dry-run source connector plan without executing adapters."""

    instance = InstanceRoot(instance_root)
    request = DomainInvestigationRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
    registry = load_source_connector_registry(config_path)
    planned = _select_source_connectors_for_request(request, registry.connectors.keys())
    planned_handoffs = _source_connector_planned_handoffs(planned)
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
        "planned_handoffs": planned_handoffs,
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
        "planned_handoff_count": len(planned_handoffs),
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


def _cmd_source_connector_preflight(
    *,
    instance_root: Path,
    config_path: Path,
    yyyymmdd: str,
    request_id: str,
    connector_id: str,
    approval_ref: str | None,
    requested_domain: str | None,
    requested_actions: list[str],
    provider_url_ref: str | None,
    preflight_only: bool,
) -> int:
    """Evaluate approved read-only source connector readiness without executing it."""

    instance = InstanceRoot(instance_root)
    registry = load_source_connector_registry(config_path)
    decision = SourceConnectorDispatchGate(instance=instance).evaluate(
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        registry=registry,
        connector_id=connector_id,
        approval_ref=approval_ref,
        requested_domain=requested_domain,
        requested_actions=requested_actions,
    )
    dispatch_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/connector-dispatch-{request_id}-{connector_id}.json"
    connector = registry.connectors.get(connector_id)
    allowed_read_only = (
        preflight_only
        and decision.decision == "allowed"
        and requested_actions == ["read"]
        and decision.mutation_requested is False
        and decision.external_call_made is False
    )
    status = "ready_for_manual_smoke" if allowed_read_only else "blocked"
    report = {
        "schema_id": "hisys.source_connector.preflight_report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "connector_id": connector_id,
        "connector_type": connector.connector_type if connector else None,
        "status": status,
        "reason_code": decision.reason_code,
        "approval_ref": approval_ref,
        "requested_domain": requested_domain,
        "requested_actions": requested_actions,
        "provider_url_ref": provider_url_ref,
        "preflight_only": preflight_only,
        "dispatch_ref": dispatch_ref,
        "external_call_requested": decision.external_call_requested,
        "external_call_permitted": decision.external_call_permitted,
        "external_call_made": False,
        "mutation_requested": decision.mutation_requested,
        "mutation_performed": False,
        "live_execution_ready": False,
        "requires_high_impact_confirm_gate": True,
        "forbidden_actions_preserved": connector.forbidden_actions if connector else [],
        "policy_refs": [
            "docs/use-cases/live-research-connectors.md",
            "examples/instance/config/source-connectors.yaml",
            "High-impact Confirm Gate",
            "No Live External Action Until Harness Passes",
        ],
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "source-connector-preflight-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "source-connector-preflight-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Source Connector Preflight Report",
                "",
                f"- connector_id: `{connector_id}`",
                f"- status: `{status}`",
                f"- preflight_only: `{str(preflight_only).lower()}`",
                "- live_execution_ready: `false`",
                "- external_call_made: `false`",
                "- mutation_performed: `false`",
                "- requires_high_impact_confirm_gate: `true`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"source connector preflight: status={status} report={report_path}")
    return 0 if status == "ready_for_manual_smoke" else 2


def _cmd_search_topic(
    *,
    instance_root: Path,
    config_path: Path,
    yyyymmdd: str,
    request_id: str,
    topic: str,
    user_opinion: str,
    approval_ref: str | None,
    transport_fixture_search: Path | None,
    provider: str,
    provider_url_ref: str | None,
    credential_ref: str | None,
    provider_response_fixture: Path | None,
) -> int:
    """Run governed topic search and emit an Investigator harness."""

    instance = InstanceRoot(instance_root)
    registry = load_source_connector_registry(config_path)
    connector_id = "general_web_search"
    connector = registry.connectors[connector_id]
    env_name = connector.manual_smoke_env_var or "HISYS_ALLOW_LIVE_SEARCH_SMOKE"
    dispatch_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/connector-dispatch-{request_id}-{connector_id}.json"
    if os.environ.get(env_name) != "1":
        report = _search_topic_report(
            request_id=request_id,
            topic=topic,
            status="blocked",
            reason_code="manual_smoke_env_missing",
            dispatch_ref=None,
            source_access_refs=[],
            source_evidence_refs=[],
            investigator_harness_ref=None,
            external_call_made=False,
        )
        _write_search_topic_report(instance, yyyymmdd, report)
        print("search topic: status=blocked reason=manual_smoke_env_missing")
        return 2
    provider_endpoint = None
    requested_domain = "search.local.fixture"
    if transport_fixture_search is None:
        if provider_url_ref is None:
            report = _search_topic_report(
                request_id=request_id,
                topic=topic,
                status="blocked",
                reason_code="search_provider_ref_required",
                dispatch_ref=None,
                source_access_refs=[],
                source_evidence_refs=[],
                investigator_harness_ref=None,
                external_call_made=False,
            )
            _write_search_topic_report(instance, yyyymmdd, report)
            return 2
        provider_endpoint = _resolve_env_ref(provider_url_ref, "provider-url-ref")
        requested_domain = urlparse(provider_endpoint).hostname or ""
    if credential_ref is not None:
        _validate_runtime_secret_ref(credential_ref, "credential-ref")
    decision = SourceConnectorDispatchGate(instance=instance).evaluate(
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        registry=registry,
        connector_id=connector_id,
        approval_ref=approval_ref,
        requested_domain=requested_domain,
        requested_actions=["read"],
    )
    if decision.decision != "allowed":
        report = _search_topic_report(
            request_id=request_id,
            topic=topic,
            status="blocked",
            reason_code=decision.reason_code,
            dispatch_ref=dispatch_ref,
            source_access_refs=[],
            source_evidence_refs=[],
            investigator_harness_ref=None,
            external_call_made=False,
        )
        _write_search_topic_report(instance, yyyymmdd, report)
        return 2
    transport_kind = "fixture_injected"
    if transport_fixture_search is not None:
        package = GeneralWebSearchConnector().collect_fixture(
            request_id=request_id,
            query=topic,
            fixture_path=transport_fixture_search,
            output_root=instance.root,
            yyyymmdd=yyyymmdd,
        )
    else:
        if provider_response_fixture is not None:
            provider_payload = json.loads(provider_response_fixture.read_text(encoding="utf-8"))
            transport_kind = "provider_fixture"
            provider_external_call_made = False
        else:
            provider_payload = _fetch_search_provider_json(
                endpoint_url=provider_endpoint or "",
                query=topic,
                credential_ref=credential_ref,
            )
            transport_kind = "provider_http"
            provider_external_call_made = True
        package = GeneralWebSearchConnector().collect_provider_results(
            request_id=request_id,
            query=topic,
            provider_name=provider,
            provider_url_ref=provider_url_ref or "[none]",
            provider_payload=provider_payload,
            external_call_made=provider_external_call_made,
            output_root=instance.root,
            yyyymmdd=yyyymmdd,
        )
    external_call_made = package.access_record.external_call_made
    harness_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/orchestrator-harness-{request_id}.json"
    harness = {
        "schema_id": "hisys.investigator.orchestrator_harness",
        "schema_version": "0.1.0",
        "harness_id": f"ORCH-HARNESS-{request_id}",
        "source_ids": ["SRC-GENERAL-WEB-SEARCH-001"],
        "agent_types": ["fixture"],
        "topic": topic,
        "user_opinion": user_opinion,
        "rationale": "Governed general web search produced bounded source evidence for Investigator follow-up.",
        "source_access_refs": [package.access_ref],
        "source_evidence_refs": [package.evidence_ref],
        "transport_kind": transport_kind,
        "provider": provider,
        "provider_url_ref": provider_url_ref,
        "credential_ref": credential_ref,
        "external_call_made": external_call_made,
        "mutation_performed": False,
    }
    harness_path = instance.root / harness_ref
    harness_path.parent.mkdir(parents=True, exist_ok=True)
    harness_path.write_text(json.dumps(harness, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = _search_topic_report(
        request_id=request_id,
        topic=topic,
        status="completed",
        reason_code="search_topic_completed",
        dispatch_ref=dispatch_ref,
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
        investigator_harness_ref=harness_ref,
        external_call_made=external_call_made,
        transport_kind=transport_kind,
        provider=provider,
        provider_url_ref=provider_url_ref,
        credential_ref=credential_ref,
    )
    _write_search_topic_report(instance, yyyymmdd, report)
    print(f"search topic: status=completed report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'search-topic-report.json'}")
    return 0


def _search_topic_report(
    *,
    request_id: str,
    topic: str,
    status: str,
    reason_code: str | None,
    dispatch_ref: str | None,
    source_access_refs: list[str],
    source_evidence_refs: list[str],
    investigator_harness_ref: str | None,
    external_call_made: bool,
    transport_kind: str | None = None,
    provider: str | None = None,
    provider_url_ref: str | None = None,
    credential_ref: str | None = None,
) -> dict[str, object]:
    return {
        "schema_id": "hisys.search_topic.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "topic": topic,
        "connector_id": "general_web_search",
        "status": status,
        "reason_code": reason_code,
        "dispatch_ref": dispatch_ref,
        "source_access_refs": source_access_refs,
        "source_evidence_refs": source_evidence_refs,
        "investigator_harness_ref": investigator_harness_ref,
        "transport_kind": transport_kind,
        "provider": provider,
        "provider_url_ref": provider_url_ref,
        "credential_ref": credential_ref,
        "external_call_made": external_call_made,
        "mutation_performed": False,
    }


def _resolve_env_ref(ref: str, label: str) -> str:
    if not ref.startswith("env:"):
        raise ValueError(f"{label} must be an env: reference")
    name = ref.split(":", 1)[1]
    if not name:
        raise ValueError(f"{label} env ref is empty")
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{label} environment value is missing")
    return value


def _validate_runtime_secret_ref(ref: str, label: str) -> None:
    allowed = ("env:", "keyring:", "file:", "ssh-agent:", "secretstore:", "op:", "aws-sm:")
    if not ref.startswith(allowed):
        raise ValueError(f"{label} must be a credential reference, not a raw value")


def _resolve_optional_env_token(ref: str | None) -> str | None:
    if ref is None:
        return None
    _validate_runtime_secret_ref(ref, "credential-ref")
    if not ref.startswith("env:"):
        return None
    return os.environ.get(ref.split(":", 1)[1])


def _fetch_search_provider_json(*, endpoint_url: str, query: str, credential_ref: str | None) -> dict[str, Any]:
    parsed = urlparse(endpoint_url)
    if parsed.scheme != "https":
        raise ValueError("search provider endpoint must use https")
    separator = "&" if parsed.query else "?"
    url = f"{endpoint_url}{separator}{urlencode({'q': query})}"
    headers = {"Accept": "application/json", "User-Agent": "hisys-search/0.1"}
    credential_value = _resolve_optional_env_token(credential_ref)
    if credential_value:
        headers["Authorization"] = f"Bearer {credential_value}"
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=20) as response:  # noqa: S310 - gated read-only approved endpoint
        body = response.read().decode("utf-8")
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("search provider response must be a JSON object")
    return payload


def _write_search_topic_report(instance: InstanceRoot, yyyymmdd: str, report: dict[str, object]) -> Path:
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "search-topic-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "search-topic-report.md"
    report_md.write_text(
        "\n".join(
            [
                "# Search Topic Report",
                "",
                f"- request_id: `{report['request_id']}`",
                f"- topic: `{report['topic']}`",
                f"- status: `{report['status']}`",
                f"- connector_id: `{report['connector_id']}`",
                f"- investigator_harness_ref: `{report.get('investigator_harness_ref')}`",
                f"- external_call_made: `{report['external_call_made']}`",
                f"- mutation_performed: `{report['mutation_performed']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report_artifact


def _safe_artifact_path(instance: InstanceRoot, ref: str) -> Path | None:
    candidate = (instance.root / ref).resolve()
    root = instance.root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.suffix not in {".json", ".md"}:
        return None
    return candidate


def _safe_artifact_ref(instance: InstanceRoot, path: Path) -> str:
    return path.resolve().relative_to(instance.root.resolve()).as_posix()


def _cmd_get_run_summary(*, instance_root: Path, yyyymmdd: str, output_format: str) -> int:
    instance = InstanceRoot(instance_root)
    suffix = "md" if output_format == "markdown" else "json"
    ref = f"reports/run-summaries/{yyyymmdd}/public-browser-run-summary.{suffix}"
    path = _safe_artifact_path(instance, ref)
    if path is None or not path.exists():
        print(f"run summary not found: {ref}", file=sys.stderr)
        return 1
    print(path.read_text(encoding="utf-8"), end="")
    return 0


def _artifact_kind(ref: str) -> str:
    if ref.startswith("reports/run-summaries/"):
        return "run_summary"
    if ref.startswith("data/chief-editor-final-browser-reviews/"):
        return "final_chief_editor_review"
    if ref.startswith("data/browser-dars-revision-resolutions/"):
        return "browser_dars_revision_resolution"
    if ref.startswith("data/dars-browser-reviews/"):
        return "dars_browser_review"
    if ref.startswith("data/chief-editor-reviews/"):
        return "chief_editor_review"
    if ref.startswith("data/evidence-packages/"):
        return "evidence_package"
    if ref.startswith("data/source-access/"):
        return "source_access"
    if ref.startswith("data/investigation-memos/"):
        return "investigation_memo"
    return "artifact"


def _cmd_list_run_artifacts(*, instance_root: Path, yyyymmdd: str, request_id: str | None) -> int:
    instance = InstanceRoot(instance_root)
    roots = [
        instance.root / "reports" / "run-summaries" / yyyymmdd,
        instance.root / "data" / "source-access" / yyyymmdd,
        instance.root / "data" / "evidence-packages" / yyyymmdd,
        instance.root / "data" / "investigation-memos" / yyyymmdd,
        instance.root / "data" / "chief-editor-reviews" / yyyymmdd,
        instance.root / "data" / "dars-browser-reviews" / yyyymmdd,
        instance.root / "data" / "browser-dars-revision-resolutions" / yyyymmdd,
        instance.root / "data" / "chief-editor-final-browser-reviews" / yyyymmdd,
    ]
    artifacts: list[dict[str, object]] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted([*root.glob("*.json"), *root.glob("*.md")]):
            ref = _safe_artifact_ref(instance, path)
            if request_id and request_id not in path.name and "public-browser" not in path.name:
                continue
            artifacts.append(
                {
                    "ref": ref,
                    "kind": _artifact_kind(ref),
                    "format": path.suffix.lstrip("."),
                    "bytes": path.stat().st_size,
                }
            )
    payload = {
        "schema_id": "hisys.run_artifact_index",
        "date": yyyymmdd,
        "request_id": request_id,
        "artifacts": artifacts,
        "external_call_made": False,
        "mutation_performed": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _cmd_show_artifact(*, instance_root: Path, ref: str) -> int:
    instance = InstanceRoot(instance_root)
    path = _safe_artifact_path(instance, ref)
    if path is None:
        print(f"unsafe artifact ref: {ref}", file=sys.stderr)
        return 2
    if not path.exists() or not path.is_file():
        print(f"artifact not found: {ref}", file=sys.stderr)
        return 1
    print(path.read_text(encoding="utf-8"), end="")
    return 0


def _cmd_public_browser_readiness(
    *,
    instance_root: Path,
    config_path: Path,
    profile_path: Path,
    yyyymmdd: str,
) -> int:
    instance = InstanceRoot(instance_root)
    blockers: list[str] = []
    profile_valid = False
    connector_ready = False
    profile_id = ""
    connector_id = ""
    transport_kind = ""
    try:
        profile = load_public_browser_profile(profile_path)
        profile_valid = True
        profile_id = profile.profile_id
        connector_id = profile.connector_id
        transport_kind = profile.transport_kind
    except Exception as exc:
        profile = None
        blockers.append(f"profile_invalid:{exc}")

    if profile is not None:
        try:
            registry = load_source_connector_registry(config_path)
            connector = registry.connectors.get(profile.connector_id)
            if not registry.policy.live_network_enabled:
                blockers.append("live_network_not_enabled")
            if connector is None:
                blockers.append("connector_missing")
            else:
                if not connector.enabled:
                    blockers.append("connector_not_enabled")
                if connector.mode != "read_only":
                    blockers.append("connector_not_read_only")
                if not connector.external_call_allowed:
                    blockers.append("connector_external_call_not_allowed")
                if connector.domain_decision_policy != profile.domain_decision_policy:
                    blockers.append("domain_decision_policy_mismatch")
                forbidden = set(connector.forbidden_actions)
                missing_forbidden = set(profile.forbidden_actions) - forbidden
                if missing_forbidden:
                    blockers.append("connector_missing_forbidden_actions")
            connector_ready = not any(
                item
                in {
                    "live_network_not_enabled",
                    "connector_missing",
                    "connector_not_enabled",
                    "connector_not_read_only",
                    "connector_external_call_not_allowed",
                    "domain_decision_policy_mismatch",
                    "connector_missing_forbidden_actions",
                }
                for item in blockers
            )
        except Exception as exc:
            blockers.append(f"config_invalid:{exc}")

    playwright_importable = importlib.util.find_spec("playwright") is not None
    status = "ready" if profile_valid and connector_ready and not blockers else "blocked"
    report = {
        "schema_id": "hisys.public_browser_readiness.report",
        "schema_version": "0.1.0",
        "status": status,
        "profile_id": profile_id,
        "connector_id": connector_id,
        "transport_kind": transport_kind,
        "profile_valid": profile_valid,
        "connector_ready": connector_ready,
        "playwright_importable": playwright_importable,
        "blockers": blockers,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    report_ref = f"reports/run-summaries/{yyyymmdd}/public-browser-readiness-report.json"
    report_path = instance.root / report_ref
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.with_suffix(".md").write_text(_render_public_browser_readiness_report_md(report), encoding="utf-8")
    print(f"public browser readiness: status={status} report={report_path}")
    print("external_call_made: false")
    return 0 if status == "ready" else 2


def _render_public_browser_readiness_report_md(report: dict[str, object]) -> str:
    blockers = [f"- {item}" for item in report.get("blockers", [])]
    if not blockers:
        blockers = ["- none"]
    return "\n".join(
        [
            "# Public Browser Readiness Report",
            "",
            f"- status: `{report['status']}`",
            f"- profile_id: `{report.get('profile_id', '')}`",
            f"- connector_id: `{report.get('connector_id', '')}`",
            f"- transport_kind: `{report.get('transport_kind', '')}`",
            f"- profile_valid: `{str(report['profile_valid']).lower()}`",
            f"- connector_ready: `{str(report['connector_ready']).lower()}`",
            f"- playwright_importable: `{str(report['playwright_importable']).lower()}`",
            f"- external_call_made: `{str(report['external_call_made']).lower()}`",
            f"- mutation_performed: `{str(report['mutation_performed']).lower()}`",
            "",
            "## Blockers",
            "",
            *blockers,
            "",
        ]
    )


def _cmd_public_browser_run(
    *,
    instance_root: Path,
    config_path: Path,
    profile_path: Path,
    yyyymmdd: str,
    request_id: str,
    topic: str,
    user_opinion: str,
    approval_ref: str,
    source_urls: list[str],
    follow_links: bool,
    max_follow_links_per_source: int | None,
    orchestrator_corroborating_urls: list[str],
) -> int:
    profile = load_public_browser_profile(profile_path)
    if profile.connector_id != "playwright_read_only":
        print("public browser run: blocked reason=unsupported_public_browser_connector", file=sys.stderr)
        return 2
    if len(source_urls) > profile.max_source_urls:
        print("public browser run: blocked reason=too_many_source_urls", file=sys.stderr)
        return 2
    follow_bound = profile.max_follow_links_per_source if max_follow_links_per_source is None else max_follow_links_per_source
    if follow_bound > profile.max_follow_links_per_source:
        print("public browser run: blocked reason=max_follow_links_exceeds_profile", file=sys.stderr)
        return 2

    instance = InstanceRoot(instance_root)
    investigation_code = _cmd_browser_investigate_topic(
        instance_root=instance_root,
        config_path=config_path,
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        topic=topic,
        user_opinion=user_opinion,
        approval_ref=approval_ref,
        source_urls=source_urls,
        orchestrator_decide_domains=True,
        browser_fixture_html=[],
        follow_links=follow_links,
        max_follow_links_per_source=follow_bound,
        orchestrator_corroborating_urls=orchestrator_corroborating_urls,
    )
    browser_report_ref = f"reports/run-summaries/{yyyymmdd}/browser-investigation-report.json"
    if investigation_code != 0:
        _write_blocked_public_browser_summary(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            topic=topic,
            source_urls=source_urls,
            reason=f"browser_investigation_failed:{investigation_code}",
            refs={"browser_investigation_report_ref": browser_report_ref},
        )
        return investigation_code

    chief_code = _cmd_review_browser_investigation(
        instance_root=instance_root,
        yyyymmdd=yyyymmdd,
        browser_investigation_report_ref=browser_report_ref,
        producer_id="public-browser-run-chief-editor",
    )
    chief_ref = f"data/chief-editor-reviews/{yyyymmdd}/CHIEF-REVIEW-{request_id}-BROWSER.json"
    if chief_code != 0:
        _write_blocked_public_browser_summary(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            topic=topic,
            source_urls=source_urls,
            reason=f"chief_editor_review_failed:{chief_code}",
            refs={"browser_investigation_report_ref": browser_report_ref, "chief_editor_review_ref": chief_ref},
        )
        return chief_code

    dars_code = _cmd_request_browser_dars_review(
        instance_root=instance_root,
        yyyymmdd=yyyymmdd,
        chief_editor_review_ref=chief_ref,
        producer_id="public-browser-run-dars",
    )
    dars_ref = f"data/dars-browser-reviews/{yyyymmdd}/DARS-REVIEW-{request_id}-BROWSER.json"
    if dars_code != 0:
        _write_blocked_public_browser_summary(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            topic=topic,
            source_urls=source_urls,
            reason=f"dars_review_failed:{dars_code}",
            refs={"browser_investigation_report_ref": browser_report_ref, "chief_editor_review_ref": chief_ref, "dars_review_ref": dars_ref},
        )
        return dars_code

    revision_code = _cmd_resolve_browser_dars_revisions(
        instance_root=instance_root,
        yyyymmdd=yyyymmdd,
        dars_review_ref=dars_ref,
        producer_id="public-browser-run-revision",
    )
    revision_ref = f"data/browser-dars-revision-resolutions/{yyyymmdd}/REVISION-{request_id}-BROWSER.json"
    if revision_code != 0:
        _write_blocked_public_browser_summary(
            instance=instance,
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            topic=topic,
            source_urls=source_urls,
            reason=f"revision_resolution_failed:{revision_code}",
            refs={
                "browser_investigation_report_ref": browser_report_ref,
                "chief_editor_review_ref": chief_ref,
                "dars_review_ref": dars_ref,
                "revision_resolution_ref": revision_ref,
            },
        )
        return revision_code

    final_code = _cmd_final_review_browser_investigation(
        instance_root=instance_root,
        yyyymmdd=yyyymmdd,
        revision_resolution_ref=revision_ref,
        producer_id="public-browser-run-final-chief-editor",
    )
    final_ref = f"data/chief-editor-final-browser-reviews/{yyyymmdd}/FINAL-CHIEF-REVIEW-{request_id}-BROWSER.json"
    refs = {
        "browser_investigation_report_ref": browser_report_ref,
        "chief_editor_review_ref": chief_ref,
        "dars_review_ref": dars_ref,
        "revision_resolution_ref": revision_ref,
        "final_review_ref": final_ref,
    }
    browser_report = _load_json_ref(instance, browser_report_ref)
    final_review = _load_json_ref(instance, final_ref)
    revision = _load_json_ref(instance, revision_ref)
    summary_ref = write_public_browser_run_summary(
        instance=instance,
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        topic=topic,
        source_urls=source_urls,
        transport_kinds=[str(item) for item in browser_report.get("transport_kinds", [])],
        final_decision=str(final_review.get("decision", "blocked")),
        remaining_blockers=[str(item) for item in revision.get("remaining_blockers", [])],
        refs=refs,
        external_call_made=bool(browser_report.get("external_call_made")),
        mutation_performed=False,
    )
    print(f"public browser run: summary={instance.root / summary_ref}")
    print(f"decision: {final_review.get('decision', 'blocked')}")
    print("publication_or_live_action_approved: false")
    return final_code


def _write_blocked_public_browser_summary(
    *,
    instance: InstanceRoot,
    yyyymmdd: str,
    request_id: str,
    topic: str,
    source_urls: list[str],
    reason: str,
    refs: dict[str, str],
) -> str:
    transport_kinds: list[str] = []
    external_call_made = False
    blocker_classification: str | None = None
    operator_interpretation: str | None = None
    browser_report_ref = refs.get("browser_investigation_report_ref")
    if browser_report_ref:
        try:
            browser_report = _load_json_ref(instance, browser_report_ref)
        except FileNotFoundError:
            browser_report = {}
        transport_kinds = [str(item) for item in browser_report.get("transport_kinds", [])]
        external_call_made = bool(browser_report.get("external_call_made"))
        sufficiency_ref = str(browser_report.get("evidence_sufficiency_ref") or "")
        if sufficiency_ref:
            try:
                sufficiency = _load_json_ref(instance, sufficiency_ref)
            except FileNotFoundError:
                sufficiency = {}
            blocker_classification = str(sufficiency.get("risk_classification") or "") or None
            if blocker_classification == "evidence_quality_decision_fairness_not_cybersecurity":
                operator_interpretation = (
                    "Blocked for source-access/evidence-quality limitation, not a cybersecurity violation. "
                    "Some pages may have returned Access Denied, empty visible text, or shallow company-only evidence. "
                    "No login, credential use, access-control bypass, mutation, publication, or live consequential action is approved."
                )
    return write_public_browser_run_summary(
        instance=instance,
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        topic=topic,
        source_urls=source_urls,
        transport_kinds=transport_kinds,
        final_decision="blocked",
        remaining_blockers=[reason],
        refs=refs,
        external_call_made=external_call_made,
        mutation_performed=False,
        blocker_classification=blocker_classification,
        operator_interpretation=operator_interpretation,
    )


def _cmd_browser_investigate_topic(
    *,
    instance_root: Path,
    config_path: Path,
    yyyymmdd: str,
    request_id: str,
    topic: str,
    user_opinion: str,
    approval_ref: str,
    source_urls: list[str],
    orchestrator_decide_domains: bool,
    browser_fixture_html: list[Path],
    follow_links: bool,
    max_follow_links_per_source: int,
    orchestrator_corroborating_urls: list[str],
) -> int:
    return run_browser_investigation(
        BrowserInvestigationRunConfig(
            instance_root=instance_root,
            config_path=config_path,
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            topic=topic,
            user_opinion=user_opinion,
            approval_ref=approval_ref,
            source_urls=source_urls,
            orchestrator_decide_domains=orchestrator_decide_domains,
            browser_fixture_html=browser_fixture_html,
            follow_links=follow_links,
            max_follow_links_per_source=max_follow_links_per_source,
            orchestrator_corroborating_urls=orchestrator_corroborating_urls,
        )
    )












def _cmd_review_browser_investigation(
    *,
    instance_root: Path,
    yyyymmdd: str,
    browser_investigation_report_ref: str,
    producer_id: str,
) -> int:
    instance = InstanceRoot(instance_root)
    report_path = instance.root / browser_investigation_report_ref
    if not report_path.exists():
        print(f"browser investigation report not found: {browser_investigation_report_ref}", file=sys.stderr)
        return 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "completed":
        print("browser chief editor review: blocked reason=browser_investigation_not_completed")
        return 2
    sufficiency_ref = str(report.get("evidence_sufficiency_ref") or "")
    sufficiency = _load_json_ref(instance, sufficiency_ref) if sufficiency_ref else {}
    if sufficiency.get("chief_editor_decision_allowed") is not True:
        print("browser chief editor review: blocked reason=evidence_sufficiency_gate_not_ready")
        return 2
    request_id = str(report.get("request_id") or _browser_request_id_from_ref(browser_investigation_report_ref))
    review = _build_browser_chief_editor_review(
        request_id=request_id,
        browser_investigation_report_ref=browser_investigation_report_ref,
        browser_report=report,
        sufficiency=sufficiency,
        producer_id=producer_id,
    )
    review_ref = f"data/chief-editor-reviews/{yyyymmdd}/CHIEF-REVIEW-{request_id}-BROWSER.json"
    review_path = instance.root / review_ref
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    review_path.with_suffix(".md").write_text(_render_browser_chief_editor_review_md(review), encoding="utf-8")
    run_report_ref = f"reports/run-summaries/{yyyymmdd}/browser-chief-editor-review-report.json"
    run_report = {
        "schema_id": "hisys.chief_editor.browser_investigation_review.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "browser_investigation_report_ref": browser_investigation_report_ref,
        "chief_editor_review_ref": review_ref,
        "decision": review["decision"],
        "external_call_made": False,
        "mutation_performed": False,
    }
    run_report_path = instance.root / run_report_ref
    run_report_path.parent.mkdir(parents=True, exist_ok=True)
    run_report_path.write_text(json.dumps(run_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"browser chief editor review: report={run_report_path}")
    print(f"decision: {review['decision']}")
    print("external_call_made: false")
    print("mutation_performed: false")
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
    query: str | None,
    transport_fixture_search: Path | None,
    license_signal: str,
    approval_ref: str | None,
    transport_fixture_pdf: Path | None,
    browser_fixture_html: Path | None,
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
    if connector_id == "general_web_search":
        if not query:
            raise ValueError("query is required for general_web_search")
        if transport_fixture_search is None:
            report = _source_connector_smoke_report(
                request_id=request_id,
                connector_id=connector_id,
                mode="manual_live",
                status="blocked",
                reason_code="search_fixture_transport_required",
                dispatch_ref=dispatch_ref,
                source_evidence_refs=[],
                external_call_made=False,
            )
            _write_source_connector_smoke_report(instance, yyyymmdd, report)
            return 2
        package = GeneralWebSearchConnector().collect_fixture(
            request_id=request_id,
            query=query,
            fixture_path=transport_fixture_search,
            output_root=instance.root,
            yyyymmdd=yyyymmdd,
        )
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="manual_live",
            status="completed",
            reason_code="manual_search_smoke_completed",
            dispatch_ref=dispatch_ref,
            source_access_refs=[package.access_ref],
            source_evidence_refs=[package.evidence_ref],
            external_call_made=package.access_record.external_call_made,
            transport_kind="fixture_injected",
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        print(f"source connector smoke: status=completed report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'source-connector-smoke-report.json'}")
        return 0
    if connector_id == "playwright_read_only":
        if not source_url:
            raise ValueError("source-url is required for playwright_read_only")
        try:
            if browser_fixture_html is not None:
                package = PlaywrightBrowserConnector().collect_fixture(
                    request_id=request_id,
                    source_url=source_url,
                    fixture_html=browser_fixture_html,
                    output_root=instance.root,
                    yyyymmdd=yyyymmdd,
                )
                transport_kind = "playwright_fixture"
            else:
                package = PlaywrightBrowserConnector().collect_live(
                    request_id=request_id,
                    source_url=source_url,
                    output_root=instance.root,
                    yyyymmdd=yyyymmdd,
                )
                transport_kind = "playwright_live"
        except PlaywrightUnavailableError:
            report = _source_connector_smoke_report(
                request_id=request_id,
                connector_id=connector_id,
                mode="manual_live",
                status="blocked",
                reason_code="browser_fixture_or_playwright_required",
                dispatch_ref=dispatch_ref,
                source_evidence_refs=[],
                external_call_made=False,
            )
            _write_source_connector_smoke_report(instance, yyyymmdd, report)
            return 2
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="manual_live",
            status="completed",
            reason_code="manual_browser_smoke_completed",
            dispatch_ref=dispatch_ref,
            source_access_refs=[package.access_ref],
            source_evidence_refs=[package.evidence_ref],
            external_call_made=package.access_record.external_call_made,
            transport_kind=transport_kind,
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        print(f"source connector smoke: status=completed report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'source-connector-smoke-report.json'}")
        return 0
    if connector_id == "open_access_pdf_fetch":
        if not source_url:
            raise ValueError("source-url is required for open_access_pdf_fetch")
        transport = None
        if transport_fixture_pdf is not None:
            def transport(url: str) -> dict[str, object]:
                return {
                    "status_code": 200,
                    "content_type": "application/pdf",
                    "content": transport_fixture_pdf.read_bytes(),
                }
        package = OpenAccessPdfConnector(transport=transport).collect_manual_smoke(
            request_id=request_id,
            source_url=source_url,
            license_signal="open_access",
            output_root=instance.root,
            yyyymmdd=yyyymmdd,
        )
        report = _source_connector_smoke_report(
            request_id=request_id,
            connector_id=connector_id,
            mode="manual_live",
            status="completed",
            reason_code="manual_pdf_smoke_completed",
            dispatch_ref=dispatch_ref,
            source_access_refs=[package.access_ref],
            source_evidence_refs=[package.evidence_ref],
            external_call_made=package.access_record.external_call_made,
            pdf_downloaded=True,
            transport_kind="fixture_injected" if transport_fixture_pdf is not None else "live_network",
        )
        _write_source_connector_smoke_report(instance, yyyymmdd, report)
        print(f"source connector smoke: status=completed report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'source-connector-smoke-report.json'}")
        return 0
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
        external_call_made=package.access_record.external_call_made,
    )
    _write_source_connector_smoke_report(instance, yyyymmdd, report)
    print(f"source connector smoke: status=completed report={instance.reports_dir / 'run-summaries' / yyyymmdd / 'source-connector-smoke-report.json'}")
    return 0


def _source_connector_requested_domain(*, connector_id: str, source_url: str | None) -> str:
    if connector_id == "doi_metadata_search":
        return "api.crossref.org"
    if connector_id == "general_web_search":
        return "search.local.fixture"
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
    source_access_refs: list[str] | None = None,
    pdf_downloaded: bool = False,
    transport_kind: str | None = None,
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
        "source_access_refs": source_access_refs or [],
        "source_evidence_refs": source_evidence_refs,
        "pdf_downloaded": pdf_downloaded,
        "transport_kind": transport_kind,
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
                f"- pdf_downloaded: `{report.get('pdf_downloaded', False)}`",
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


def _cmd_extract_pdf_quotes(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    promoted_pdf_evidence_refs: list[str],
) -> int:
    instance = InstanceRoot(instance_root)
    result = PdfQuoteExtractor(root=instance.root).extract(
        request_id=request_id,
        promoted_pdf_evidence_refs=promoted_pdf_evidence_refs,
        yyyymmdd=yyyymmdd,
    )
    report = {
        "schema_id": "hisys.pdf_quote.extraction_report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": "completed",
        "source_quote_refs": result.source_quote_refs,
        "quote_count": len(result.source_quote_refs),
        "external_call_made": result.external_call_made,
        "mutation_performed": result.mutation_performed,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "pdf-quote-extraction-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "pdf-quote-extraction-report.md"
    report_md.write_text(
        "\n".join(
            [
                f"# PDF quote extraction report {request_id}",
                "",
                "- status: `completed`",
                f"- quote_count: {len(result.source_quote_refs)}",
                "- external_call_made: false",
                "- mutation_performed: false",
                "",
                "## Source quote refs",
                *[f"- {ref}" for ref in result.source_quote_refs],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"pdf quote extraction: report={report_artifact}")
    print("external_call_made: false")
    return 0


def _cmd_build_claim_evidence_ledger(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    claim_id: str,
    claim_text: str,
    relation: str,
    rationale: str,
    source_quote_refs: list[str],
) -> int:
    instance = InstanceRoot(instance_root)
    result = ClaimEvidenceLedgerBuilder(root=instance.root).build(
        request_id=request_id,
        claim_id=claim_id,
        claim_text=claim_text,
        relation=relation,
        rationale=rationale,
        source_quote_refs=source_quote_refs,
        yyyymmdd=yyyymmdd,
    )
    report = {
        "schema_id": "hisys.claim_evidence_ledger.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": "completed",
        "claim_id": claim_id,
        "relation": relation,
        "claim_evidence_ledger_refs": result.claim_evidence_ledger_refs,
        "ledger_count": len(result.claim_evidence_ledger_refs),
        "external_call_made": result.external_call_made,
        "mutation_performed": result.mutation_performed,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "claim-evidence-ledger-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "claim-evidence-ledger-report.md"
    report_md.write_text(
        "\n".join(
            [
                f"# Claim evidence ledger report {request_id}",
                "",
                "- status: `completed`",
                f"- claim_id: `{claim_id}`",
                f"- relation: `{relation}`",
                f"- ledger_count: {len(result.claim_evidence_ledger_refs)}",
                "- external_call_made: false",
                "- mutation_performed: false",
                "",
                "## Claim evidence ledger refs",
                *[f"- {ref}" for ref in result.claim_evidence_ledger_refs],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"claim evidence ledger: report={report_artifact}")
    print("external_call_made: false")
    return 0


def _cmd_build_claim_evidence_summary(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    claim_id: str,
    claim_evidence_ledger_refs: list[str],
) -> int:
    instance = InstanceRoot(instance_root)
    result = ClaimEvidenceSummaryBuilder(root=instance.root).build(
        request_id=request_id,
        claim_id=claim_id,
        claim_evidence_ledger_refs=claim_evidence_ledger_refs,
        yyyymmdd=yyyymmdd,
    )
    report = {
        "schema_id": "hisys.claim_evidence_summary.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": "completed",
        "claim_id": claim_id,
        "claim_evidence_summary_refs": result.claim_evidence_summary_refs,
        "summary_count": len(result.claim_evidence_summary_refs),
        "external_call_made": result.external_call_made,
        "mutation_performed": result.mutation_performed,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "claim-evidence-summary-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "claim-evidence-summary-report.md"
    report_md.write_text(
        "\n".join(
            [
                f"# Claim evidence summary report {request_id}",
                "",
                "- status: `completed`",
                f"- claim_id: `{claim_id}`",
                f"- summary_count: {len(result.claim_evidence_summary_refs)}",
                "- advisory_confidence_only: true",
                "- does_not_prove_novelty: true",
                "- external_call_made: false",
                "- mutation_performed: false",
                "",
                "## Claim evidence summary refs",
                *[f"- {ref}" for ref in result.claim_evidence_summary_refs],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"claim evidence summary: report={report_artifact}")
    print("external_call_made: false")
    return 0


def _cmd_build_claim_coverage_gate(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    required_claim_ids: list[str],
    claim_evidence_summary_refs: list[str],
) -> int:
    instance = InstanceRoot(instance_root)
    result = ClaimCoverageGateBuilder(root=instance.root).build(
        request_id=request_id,
        required_claim_ids=required_claim_ids,
        claim_evidence_summary_refs=claim_evidence_summary_refs,
        yyyymmdd=yyyymmdd,
    )
    gate = json.loads((instance.root / result.claim_coverage_gate_refs[0]).read_text(encoding="utf-8"))
    report = {
        "schema_id": "hisys.claim_coverage_gate.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": "completed",
        "coverage_status": gate["coverage_status"],
        "claim_coverage_gate_refs": result.claim_coverage_gate_refs,
        "gate_count": len(result.claim_coverage_gate_refs),
        "external_call_made": result.external_call_made,
        "mutation_performed": result.mutation_performed,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "claim-coverage-gate-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "claim-coverage-gate-report.md"
    report_md.write_text(
        "\n".join(
            [
                f"# Claim coverage gate report {request_id}",
                "",
                "- status: `completed`",
                f"- coverage_status: `{gate['coverage_status']}`",
                "- manuscript_language_gate: `conditional_only`",
                "- conditional_manuscript_language_only: true",
                "- does_not_approve_publication_ready_claims: true",
                "- external_call_made: false",
                "- mutation_performed: false",
                "",
                "## Claim coverage gate refs",
                *[f"- {ref}" for ref in result.claim_coverage_gate_refs],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"claim coverage gate: report={report_artifact}")
    print("external_call_made: false")
    return 0


def _cmd_build_recommendation_claim_registry(
    *,
    instance_root: Path,
    yyyymmdd: str,
    request_id: str,
    recommendation_text: str,
    claim_texts: list[str],
    source_recommendation_ref: str | None = None,
) -> int:
    instance = InstanceRoot(instance_root)
    result = RecommendationClaimRegistryBuilder(root=instance.root).build(
        request_id=request_id,
        recommendation_text=recommendation_text,
        claim_texts=claim_texts,
        yyyymmdd=yyyymmdd,
        source_recommendation_ref=source_recommendation_ref,
    )
    report = {
        "schema_id": "hisys.recommendation_claim_registry.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": "completed",
        "recommendation_claim_registry_refs": result.recommendation_claim_registry_refs,
        "required_claim_ids": result.required_claim_ids,
        "feeds_live_k_coverage_gates": True,
        "conditional_manuscript_language_only": True,
        "external_call_made": result.external_call_made,
        "mutation_performed": result.mutation_performed,
    }
    report_dir = instance.reports_dir / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_artifact = report_dir / "recommendation-claim-registry-report.json"
    report_artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = report_dir / "recommendation-claim-registry-report.md"
    report_md.write_text(
        "\n".join(
            [
                f"# Recommendation claim registry report {request_id}",
                "",
                "- status: `completed`",
                "- feeds_live_k_coverage_gates: true",
                "- conditional_manuscript_language_only: true",
                "- does_not_approve_publication_ready_claims: true",
                "- external_call_made: false",
                "- mutation_performed: false",
                "",
                "## Recommendation claim registry refs",
                *[f"- {ref}" for ref in result.recommendation_claim_registry_refs],
                "",
                "## Required claim ids for Live-K",
                *[f"- {claim_id}" for claim_id in result.required_claim_ids],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"recommendation claim registry: report={report_artifact}")
    print("external_call_made: false")
    return 0


def _select_source_connectors_for_request(request: DomainInvestigationRequest, connector_ids: Iterable[str]) -> list[str]:
    ids = set(connector_ids)
    if request.domain == "research":
        preferred = ["general_web_search", "publisher_web_search", "doi_metadata_search", "open_access_pdf_fetch", "arxiv_metadata_search"]
        return [connector_id for connector_id in preferred if connector_id in ids]
    return [connector_id for connector_id in ["local_pdf_reader"] if connector_id in ids]


def _source_connector_planned_handoffs(planned_connectors: list[str]) -> list[dict[str, object]]:
    if "doi_metadata_search" not in planned_connectors or "open_access_pdf_fetch" not in planned_connectors:
        return []
    return [
        {
            "from_connector_id": "doi_metadata_search",
            "to_connector_id": "open_access_pdf_fetch",
            "handoff_type": "pdf_candidate_plan_only",
            "artifact_kind": "pdf-candidate-plan",
            "pdf_downloaded": False,
            "external_call_made": False,
        }
    ]


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
            "## Planned handoffs",
            *[f"- {handoff['from_connector_id']} -> {handoff['to_connector_id']} ({handoff['handoff_type']})" for handoff in plan.get("planned_handoffs", [])],
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
            f"- planned_handoff_count: {report.get('planned_handoff_count', 0)}",
            f"- external_call_made: {str(report['external_call_made']).lower()}",
            "",
        ]
    )


def _cmd_investigate_domain(
    instance_root: Path,
    request_path: Path,
    yyyymmdd: str,
    pass_contract_registry: Path | None = None,
    question_type: str | None = None,
    evidence_summary: Path | None = None,
    promote_pdf_source_access_refs: list[str] | None = None,
    promote_pdf_source_evidence_refs: list[str] | None = None,
    source_quote_refs: list[str] | None = None,
    claim_evidence_ledger_refs: list[str] | None = None,
    claim_evidence_summary_refs: list[str] | None = None,
    claim_coverage_gate_refs: list[str] | None = None,
    recommendation_claim_registry_refs: list[str] | None = None,
    live_source_access_refs: list[str] | None = None,
    live_source_evidence_refs: list[str] | None = None,
) -> int:
    """Persist the local MVP boundary for a domain investigation request."""

    instance = InstanceRoot(instance_root)
    request = DomainInvestigationRequest.model_validate_json(request_path.read_text(encoding="utf-8"))
    boundary_dir = instance.root / "runtime-boundary" / "domain-investigation" / request.domain / yyyymmdd
    boundary_dir.mkdir(parents=True, exist_ok=True)

    request_artifact = boundary_dir / f"hisys-tool-request-{request.request_id}.json"
    request_artifact.write_text(_record_json(request), encoding="utf-8")
    request_markdown = boundary_dir / f"hisys-tool-request-{request.request_id}.md"
    request_markdown.write_text(_format_domain_request_markdown(request), encoding="utf-8")

    promoted_pdf_evidence = None
    if promote_pdf_source_access_refs or promote_pdf_source_evidence_refs:
        promoted_pdf_evidence = PdfEvidencePromotionLoader(root=instance.root).promote(
            source_access_refs=promote_pdf_source_access_refs or [],
            source_evidence_refs=promote_pdf_source_evidence_refs or [],
        )

    pass_contract_tool_result: HisysToolResult | None = None
    if pass_contract_registry and question_type and evidence_summary:
        registry_entries = load_pass_contract_registry(pass_contract_registry)
        contract = find_contract(registry_entries, domain=request.domain, question_type=question_type, active_only=True)
        result_ref = str((boundary_dir / f"hisys-tool-result-{request.request_id}.json").relative_to(instance.root))
        if contract is None:
            pass_contract_tool_result = HisysToolResult(
                status="needs_more_evidence",
                domain=request.domain,
                summary="No active pass contract found for domain/question type.",
                recommended_alternative_id=None,
                requires_human_review=True,
                external_call_made=False,
                mutation_performed=False,
                runtime_boundary_refs=[str(request_artifact.relative_to(instance.root)), str(request_markdown.relative_to(instance.root)), result_ref],
                quality_gate="needs_more_evidence",
            )
        else:
            summary_data = json.loads(evidence_summary.read_text(encoding="utf-8"))
            evaluation = evaluate_pass_contract(contract, EvidenceSummary.from_dict(summary_data))
            eval_dir = instance.root / "runtime-boundary" / "pass-contract-evaluations" / yyyymmdd
            eval_path = eval_dir / f"EVAL-{contract.contract_id}.json"
            _write_json(eval_path, evaluation.to_dict())
            status = "completed" if evaluation.quality_gate == "passed" else evaluation.quality_gate
            pass_contract_tool_result = HisysToolResult(
                status=status,
                domain=request.domain,
                summary=f"Pass-contract evaluation for {contract.contract_id}: {evaluation.quality_gate}",
                recommended_alternative_id=None,
                requires_human_review=True,
                external_call_made=False,
                mutation_performed=False,
                runtime_boundary_refs=[
                    str(request_artifact.relative_to(instance.root)),
                    str(request_markdown.relative_to(instance.root)),
                    _safe_relative_ref(instance.root, eval_path),
                    result_ref,
                ],
                quality_gate=evaluation.quality_gate,
            )

    domain_context = DomainInvestigationContext(
        instance_root=instance.root,
        boundary_dir=boundary_dir,
        yyyymmdd=yyyymmdd,
        promoted_pdf_evidence=promoted_pdf_evidence,
        source_quote_refs=source_quote_refs or [],
        claim_evidence_ledger_refs=claim_evidence_ledger_refs or [],
        claim_evidence_summary_refs=claim_evidence_summary_refs or [],
        claim_coverage_gate_refs=claim_coverage_gate_refs or [],
        recommendation_claim_registry_refs=recommendation_claim_registry_refs or [],
        live_source_access_refs=live_source_access_refs or [],
        live_source_evidence_refs=live_source_evidence_refs or [],
    )
    domain_adapter = None
    domain_result = None
    if pass_contract_tool_result is None:
        domain_registry = _default_domain_adapter_registry(instance=instance)
        domain_adapter = domain_registry.resolve(request)
        if domain_adapter is not None:
            domain_result = domain_adapter.investigate(request, domain_context)
    if domain_result is not None:
        if _should_apply_research_gap_postprocessors(domain_adapter):
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
    elif pass_contract_tool_result is not None:
        tool_result = pass_contract_tool_result
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


class _ResearchGapDomainAdapter:
    """Research-gap adapter kept behind the domain adapter registry."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self._instance = instance

    def supports(self, request: DomainInvestigationRequest) -> bool:
        objective = request.objective.lower()
        return request.domain == "research" and "formalism" in objective and "gap" in objective

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainInvestigationContext,
    ) -> DomainInvestigationResult:
        result = _build_research_domain_result(
            request,
            self._instance,
            context.boundary_dir,
            context.yyyymmdd,
            promoted_pdf_evidence=context.promoted_pdf_evidence,
            source_quote_refs=context.source_quote_refs,
            claim_evidence_ledger_refs=context.claim_evidence_ledger_refs,
            claim_evidence_summary_refs=context.claim_evidence_summary_refs,
            claim_coverage_gate_refs=context.claim_coverage_gate_refs,
            recommendation_claim_registry_refs=context.recommendation_claim_registry_refs,
            live_source_access_refs=context.live_source_access_refs,
            live_source_evidence_refs=context.live_source_evidence_refs,
        )
        if result is None:
            raise ValueError("ResearchGapDomainAdapter received an unsupported request")
        return result


def _should_apply_research_gap_postprocessors(adapter: object | None) -> bool:
    """Return true only for the legacy research-gap adapter path."""

    return isinstance(adapter, _ResearchGapDomainAdapter)


def _default_domain_adapter_registry(*, instance: InstanceRoot) -> DomainAdapterRegistry[DomainInvestigationResult]:
    """Build the ordered registry for domain-specific investigation adapters."""

    structured_specs = [research_spec(), codebase_spec(), investment_spec()]
    # Reject duplicate canonical domains or aliases at registry construction
    # so example specs cannot silently shadow each other.
    validate_spec_collisions(structured_specs)
    # Keep the legacy research-gap adapter ahead of the generic research spec so
    # existing DARS fixture and Chief Editor postprocessors remain the first
    # match for formalism-gap objectives.
    return DomainAdapterRegistry(
        [
            _ResearchGapDomainAdapter(instance=instance),
            *(StructuredDomainAdapter(spec) for spec in structured_specs),
        ]
    )


def _build_research_domain_result(
    request: DomainInvestigationRequest,
    instance: InstanceRoot,
    boundary_dir: Path,
    yyyymmdd: str,
    promoted_pdf_evidence=None,
    source_quote_refs: list[str] | None = None,
    claim_evidence_ledger_refs: list[str] | None = None,
    claim_evidence_summary_refs: list[str] | None = None,
    claim_coverage_gate_refs: list[str] | None = None,
    recommendation_claim_registry_refs: list[str] | None = None,
    live_source_access_refs: list[str] | None = None,
    live_source_evidence_refs: list[str] | None = None,
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
    promoted_source_refs = []
    promoted_evidence_refs = []
    if promoted_pdf_evidence is not None:
        promoted_source_refs = [*promoted_pdf_evidence.source_access_refs, *promoted_pdf_evidence.source_evidence_refs]
        promoted_evidence_refs = promoted_pdf_evidence.promoted_pdf_evidence_refs
    quote_refs = source_quote_refs or []
    for quote_ref in quote_refs:
        if not quote_ref.startswith("runtime-boundary/source-connectors/") or "/source-quote-" not in quote_ref:
            raise ValueError("source_quote_refs must point to runtime-boundary/source-connectors source-quote artifacts")
    ledger_refs = claim_evidence_ledger_refs or []
    for ledger_ref in ledger_refs:
        if not ledger_ref.startswith("runtime-boundary/source-connectors/") or "/claim-evidence-ledger-" not in ledger_ref:
            raise ValueError("claim_evidence_ledger_refs must point to runtime-boundary/source-connectors claim-evidence-ledger artifacts")
    summary_refs = claim_evidence_summary_refs or []
    for summary_ref in summary_refs:
        if not summary_ref.startswith("runtime-boundary/source-connectors/") or "/claim-evidence-summary-" not in summary_ref:
            raise ValueError("claim_evidence_summary_refs must point to runtime-boundary/source-connectors claim-evidence-summary artifacts")
    gate_refs = claim_coverage_gate_refs or []
    for gate_ref in gate_refs:
        if not gate_ref.startswith("runtime-boundary/source-connectors/") or "/claim-coverage-gate-" not in gate_ref:
            raise ValueError("claim_coverage_gate_refs must point to runtime-boundary/source-connectors claim-coverage-gate artifacts")
    registry_refs = recommendation_claim_registry_refs or []
    for registry_ref in registry_refs:
        if not registry_ref.startswith("runtime-boundary/source-connectors/") or "/recommendation-claim-registry-" not in registry_ref:
            raise ValueError("recommendation_claim_registry_refs must point to runtime-boundary/source-connectors recommendation-claim-registry artifacts")
    live_access_refs = live_source_access_refs or []
    for access_ref in live_access_refs:
        if not access_ref.startswith("runtime-boundary/source-connectors/") or "/source-access-" not in access_ref:
            raise ValueError("live_source_access_refs must point to runtime-boundary/source-connectors source-access artifacts")
    live_evidence_refs = live_source_evidence_refs or []
    for evidence_ref in live_evidence_refs:
        if not evidence_ref.startswith("runtime-boundary/source-connectors/") or "/source-evidence-" not in evidence_ref:
            raise ValueError("live_source_evidence_refs must point to runtime-boundary/source-connectors source-evidence artifacts")
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
        evidence_refs=["fixture:formalism_gap_analysis", "fixture:formalism_comparison", *connector_refs, *live_evidence_refs, *promoted_evidence_refs, *quote_refs, *ledger_refs, *summary_refs, *gate_refs, *registry_refs],
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
            *live_access_refs,
            *live_evidence_refs,
            *promoted_source_refs,
        ],
        promoted_pdf_evidence_refs=promoted_evidence_refs,
        source_quote_refs=quote_refs,
        claim_evidence_ledger_refs=ledger_refs,
        claim_evidence_summary_refs=summary_refs,
        claim_coverage_gate_refs=gate_refs,
        recommendation_claim_registry_refs=registry_refs,
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
        external_call_made=bool(live_access_refs or live_evidence_refs),
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
        "promoted_pdf_evidence_refs": domain_result.investigation_data.promoted_pdf_evidence_refs,
        "source_quote_refs": domain_result.investigation_data.source_quote_refs,
        "claim_evidence_ledger_refs": domain_result.investigation_data.claim_evidence_ledger_refs,
        "claim_evidence_summary_refs": domain_result.investigation_data.claim_evidence_summary_refs,
        "claim_coverage_gate_refs": domain_result.investigation_data.claim_coverage_gate_refs,
        "recommendation_claim_registry_refs": domain_result.investigation_data.recommendation_claim_registry_refs,
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
    if domain_result.investigation_data.claim_coverage_gate_refs:
        source_validation_status = "claim_coverage_gate_present"
    elif domain_result.investigation_data.recommendation_claim_registry_refs:
        source_validation_status = "recommendation_claim_registry_present"
    elif domain_result.investigation_data.claim_evidence_summary_refs:
        source_validation_status = "claim_evidence_summary_present"
    elif domain_result.investigation_data.claim_evidence_ledger_refs:
        source_validation_status = "claim_evidence_ledger_present"
    elif domain_result.investigation_data.source_quote_refs:
        source_validation_status = "manual_pdf_quotes_present"
    elif domain_result.investigation_data.promoted_pdf_evidence_refs:
        source_validation_status = "manual_pdf_evidence_promoted"
    else:
        source_validation_status = "fixture_source_evidence_present" if source_evidence_refs else "source_validation_needed"
    dars_acceptance = _decide_dars_acceptance(instance=instance, dars_refs=domain_result.dars_refs)
    conditions = [
        "Validate fixture source evidence against live publisher pages before publication claims.",
        "Collect publisher-source evidence for DSDEVS, graph transformation, and ABM literature.",
        "Define evaluation scenarios for topology/behavior co-evolution.",
        "Keep novelty claims conditional until DARS source-validation actions are resolved.",
        "Keep novelty claims conditional after quote extraction.",
        "Keep novelty claims conditional after claim-evidence ledger mapping.",
        "Keep confidence advisory after claim-evidence summary aggregation.",
        "Keep manuscript-facing claims conditional after claim coverage gating.",
        "Run Live-K claim coverage gates before stronger manuscript-facing claims.",
    ]
    if dars_acceptance["dars_accepted"]:
        conditions.append("Chief Editor accepted DARS advisory actions as non-executable conditions.")
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
        "promoted_pdf_evidence_refs": domain_result.investigation_data.promoted_pdf_evidence_refs,
        "source_quote_refs": domain_result.investigation_data.source_quote_refs,
        "claim_evidence_ledger_refs": domain_result.investigation_data.claim_evidence_ledger_refs,
        "claim_evidence_summary_refs": domain_result.investigation_data.claim_evidence_summary_refs,
        "claim_coverage_gate_refs": domain_result.investigation_data.claim_coverage_gate_refs,
        "recommendation_claim_registry_refs": domain_result.investigation_data.recommendation_claim_registry_refs,
        "advisory_confidence_only": bool(domain_result.investigation_data.claim_evidence_summary_refs),
        "feeds_live_k_coverage_gates": bool(domain_result.investigation_data.recommendation_claim_registry_refs),
        "recommendation_claim_registry_conditional": bool(domain_result.investigation_data.recommendation_claim_registry_refs),
        "manuscript_language_gate": "conditional_only" if domain_result.investigation_data.claim_coverage_gate_refs else "source_validation_required",
        "conditional_manuscript_language_only": bool(domain_result.investigation_data.claim_coverage_gate_refs),
        "conditions": conditions,
        "required_next_evidence": [
            "DSDEVS source literature",
            "graph transformation/self-organization formalism sources",
            "agent-based modeling emergence/verification sources",
            "evaluation scenarios for topology/behavior co-evolution",
        ],
        "dars_trace_refs": dars_trace_refs,
        **dars_acceptance,
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
                f"- dars_acceptance_decision: `{decision['dars_acceptance_decision']}`",
                f"- dars_accepted: `{str(decision['dars_accepted']).lower()}`",
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


def _decide_dars_acceptance(*, instance: InstanceRoot, dars_refs: list[str]) -> dict[str, Any]:
    """Chief Editor's controlled decision on whether to accept DARS advice.

    DARS remains advisory-only: accepting DARS means importing its recommended
    action IDs as non-executable review conditions, never executing them.
    """

    response = _load_latest_dars_response(instance=instance, dars_refs=dars_refs)
    if response is None:
        return {
            "dars_acceptance_decision": "not_available",
            "dars_accepted": False,
            "accepted_dars_action_ids": [],
            "dars_blocks_decision": False,
            "dars_unresolved_high_severity_findings": 0,
            "dars_acceptance_rationale": "No DARS response artifact was available for Chief Editor review.",
        }

    boundary = response.get("boundary", {})
    decision_trace = response.get("decision_trace", {})
    critique = response.get("critique", {})
    recommended_actions = critique.get("recommended_actions", [])
    unsafe_boundary = (
        boundary.get("action_taken") != "none"
        or boundary.get("mutation_performed") is True
        or boundary.get("external_side_effects_performed") is True
    )
    blocks_decision = bool(decision_trace.get("blocks_decision", False))
    unresolved_high = int(decision_trace.get("unresolved_high_severity_findings", 0) or 0)
    accepted_action_ids = [
        action.get("action_id")
        for action in recommended_actions
        if isinstance(action, dict)
        and action.get("action_id")
        and action.get("allowed_to_execute") is False
    ]
    if unsafe_boundary or blocks_decision:
        return {
            "dars_acceptance_decision": "rejected_boundary_violation",
            "dars_accepted": False,
            "accepted_dars_action_ids": [],
            "dars_blocks_decision": blocks_decision,
            "dars_unresolved_high_severity_findings": unresolved_high,
            "dars_acceptance_rationale": "DARS advice was not accepted because it violated the advisory-only boundary or attempted to block the decision.",
        }
    if accepted_action_ids:
        return {
            "dars_acceptance_decision": "accepted_as_conditions",
            "dars_accepted": True,
            "accepted_dars_action_ids": accepted_action_ids,
            "dars_blocks_decision": blocks_decision,
            "dars_unresolved_high_severity_findings": unresolved_high,
            "dars_acceptance_rationale": "Chief Editor accepted DARS advisory recommendations as non-executable conditions requiring human-reviewed follow-up.",
        }
    return {
        "dars_acceptance_decision": "reviewed_no_advisory_actions",
        "dars_accepted": False,
        "accepted_dars_action_ids": [],
        "dars_blocks_decision": blocks_decision,
        "dars_unresolved_high_severity_findings": unresolved_high,
        "dars_acceptance_rationale": "DARS response was reviewed but contained no non-executable advisory action IDs to accept.",
    }


def _load_latest_dars_response(*, instance: InstanceRoot, dars_refs: list[str]) -> dict[str, Any] | None:
    response_refs = [ref for ref in dars_refs if "/dars-response-" in ref and ref.endswith(".json")]
    for ref in reversed(response_refs):
        path = instance.root / ref
        if path.exists() and path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


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
    orchestrator_harness_path: Path | None = None,
) -> int:
    """Run a template-driven Investigator research-to-memo path.

    Traceability: HISYS-INST-INV-001, HISYS-FR-INV-001..006,
    HISYS-FR-MEM-001..005, HISYS-TPL-RESEARCH-SEARCH-001, HISYS-T-026.
    """

    registry = load_source_registry(InstanceRoot(config_root))
    harness_data: dict[str, object] | None = None
    harness_source_ids: list[str] = []
    harness_agent_types: list[str] = []
    user_opinion: str | None = None
    if orchestrator_harness_path is not None:
        try:
            harness_data = _load_orchestrator_harness(orchestrator_harness_path)
            harness_source_ids = _string_list_from_harness(harness_data, "source_ids")
            harness_agent_types = _string_list_from_harness(harness_data, "agent_types")
            user_opinion = _optional_string_from_harness(harness_data, "user_opinion")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"orchestrator harness invalid: {exc}", file=sys.stderr)
            return 1
    source_ids = _ordered_unique([*harness_source_ids, *source_ids])
    if not source_ids:
        print("no sources supplied; use --source or --orchestrator-harness source_ids", file=sys.stderr)
        return 1
    missing_sources = [source_id for source_id in source_ids if source_id not in registry.entries]
    if missing_sources:
        print(f"orchestrator/requested sources not in registry: {', '.join(missing_sources)}", file=sys.stderr)
        return 1
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
    effective_agent_types = agent_types or harness_agent_types or None
    agent_plan_source_override = "orchestrator_harness" if orchestrator_harness_path is not None and not agent_types else None
    try:
        agent_plan = select_configured_agent_plan(
            agent_config,
            guideline_profile_id=guideline.profile_id,
            explicit_agent_types=effective_agent_types,
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
        harness_source_refs=harness_source_ids,
        user_opinion=user_opinion,
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
        agent_plan_source=agent_plan_source_override or agent_plan.source,
        disabled_optional_agent_refs=agent_plan.disabled_optional_agents,
        blocked_agent_refs=agent_plan.blocked_agents,
        orchestrator_harness_ref=str(orchestrator_harness_path) if orchestrator_harness_path else None,
        harness_source_refs=harness_source_ids or None,
        user_opinion=user_opinion,
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
    harness_source_refs: list[str] | None = None,
    user_opinion: str | None = None,
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
        harness_source_refs=harness_source_refs,
        user_opinion=user_opinion,
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
    harness_source_refs: list[str] | None = None,
    user_opinion: str | None = None,
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
    harness_lines = [f"- `{source_ref}`" for source_ref in (harness_source_refs or [])]
    user_opinion_lines = [f"- {user_opinion}"] if user_opinion else ["- none supplied"]
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
            "## Orchestrator Harness",
            *(harness_lines or ["- no orchestrator harness supplied; CLI/default source selection used"]),
            "",
            "## User Opinion",
            *user_opinion_lines,
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



def _cmd_request_browser_dars_review(
    *,
    instance_root: Path,
    yyyymmdd: str,
    chief_editor_review_ref: str,
    producer_id: str,
) -> int:
    instance = InstanceRoot(instance_root)
    chief_path = instance.root / chief_editor_review_ref
    if not chief_path.exists():
        print(f"chief editor review not found: {chief_editor_review_ref}", file=sys.stderr)
        return 1
    chief_review = json.loads(chief_path.read_text(encoding="utf-8"))
    request_id = str(chief_review.get("request_id") or _browser_request_id_from_ref(chief_editor_review_ref))
    if chief_review.get("decision") != "accept_for_devil_dars_adversarial_review":
        print("browser dars review: blocked reason=chief_editor_not_accepted_for_dars")
        return 2
    basis_refs = chief_review.get("basis_refs", {}) if isinstance(chief_review.get("basis_refs"), dict) else {}
    sufficiency_ref = str(basis_refs.get("evidence_sufficiency", ""))
    if sufficiency_ref:
        sufficiency_path = instance.root / sufficiency_ref
        if sufficiency_path.exists():
            sufficiency = json.loads(sufficiency_path.read_text(encoding="utf-8"))
            if not sufficiency.get("devil_review_allowed"):
                print("browser dars review: blocked reason=evidence_sufficiency_gate_not_ready")
                return 2
    matrix_ref = str(basis_refs.get("competitive_matrix", ""))
    matrix = {}
    if matrix_ref and (instance.root / matrix_ref).exists():
        matrix = json.loads((instance.root / matrix_ref).read_text(encoding="utf-8"))
    review = _build_browser_dars_review(
        request_id=request_id,
        chief_editor_review_ref=chief_editor_review_ref,
        chief_review=chief_review,
        matrix=matrix,
        producer_id=producer_id,
    )
    handoff_ref = f"data/agent-handoffs/{yyyymmdd}/HANDOFF-DARS-{request_id}-BROWSER.json"
    handoff = {
        "schema_id": "hisys.agent_handoff_package",
        "schema_version": "0.1.0",
        "handoff_id": f"HANDOFF-DARS-{request_id}-BROWSER",
        "target_agent_system": "DARS",
        "task": "adversarial_browser_investigation_review",
        "context": "Challenge Chief Editor browser-investigation readiness and preliminary competitive technology signals.",
        "evidence_bundle": [chief_editor_review_ref, *[str(v) for v in basis_refs.values() if v]],
        "constraints": [
            "advisory_only",
            "no live external action",
            "external_call_made=false",
            "do not mutate evidence, Chief Editor review, or final decision",
        ],
        "expected_output": "adversarial findings, rebuttal targets, required revisions, and final-review recommendation",
        "allowed_actions": "advisory_only",
        "approval_state": "not_required",
        "result_refs": [f"data/dars-browser-reviews/{yyyymmdd}/DARS-REVIEW-{request_id}-BROWSER.json"],
        "status": "linked",
        "producer_id": producer_id,
    }
    handoff_path = instance.root / handoff_ref
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (handoff_path.with_suffix(".md")).write_text(_render_browser_dars_handoff_md(handoff), encoding="utf-8")
    review_ref = f"data/dars-browser-reviews/{yyyymmdd}/DARS-REVIEW-{request_id}-BROWSER.json"
    review["handoff_ref"] = handoff_ref
    review_path = instance.root / review_ref
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    review_path.with_suffix(".md").write_text(_render_browser_dars_review_md(review), encoding="utf-8")
    report_ref = f"reports/run-summaries/{yyyymmdd}/browser-dars-review-report.json"
    report = {
        "schema_id": "hisys.browser_dars_review.report",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "chief_editor_review_ref": chief_editor_review_ref,
        "handoff_ref": handoff_ref,
        "dars_review_ref": review_ref,
        "decision": review["decision"],
        "external_call_made": False,
        "mutation_performed": False,
    }
    report_path = instance.root / report_ref
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"browser dars review: report={report_path}")
    print(f"decision: {review['decision']}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0








def _browser_request_id_from_ref(ref: str) -> str:
    name = Path(ref).stem
    return name.removeprefix("CHIEF-REVIEW-").removesuffix("-BROWSER")



def _cmd_resolve_browser_dars_revisions(
    *,
    instance_root: Path,
    yyyymmdd: str,
    dars_review_ref: str,
    producer_id: str,
) -> int:
    instance = InstanceRoot(instance_root)
    dars_path = instance.root / dars_review_ref
    if not dars_path.exists():
        print(f"browser dars review not found: {dars_review_ref}", file=sys.stderr)
        return 1
    dars_review = json.loads(dars_path.read_text(encoding="utf-8"))
    if dars_review.get("decision") != "requires_revision_before_final_acceptance":
        print("browser dars revision resolution: blocked reason=dars_review_not_revision_required")
        return 2
    chief_ref = str(dars_review.get("chief_editor_review_ref", ""))
    chief_review = _load_json_ref(instance, chief_ref) if chief_ref else {}
    basis_refs = chief_review.get("basis_refs", {}) if isinstance(chief_review.get("basis_refs"), dict) else {}
    matrix_ref = str(basis_refs.get("competitive_matrix", ""))
    matrix = _load_json_ref(instance, matrix_ref) if matrix_ref else {}
    resolution = BrowserDarsRevisionResolution.model_validate(_build_browser_dars_revision_resolution(
        request_id=str(dars_review.get("request_id") or _browser_request_id_from_ref(dars_review_ref)),
        dars_review_ref=dars_review_ref,
        chief_editor_review_ref=chief_ref,
        competitive_matrix_ref=matrix_ref,
        dars_review=dars_review,
        matrix=matrix,
        producer_id=producer_id,
    )).model_dump(mode="json")
    resolution_ref = f"data/browser-dars-revision-resolutions/{yyyymmdd}/REVISION-{resolution['request_id']}-BROWSER.json"
    resolution_path = instance.root / resolution_ref
    resolution_path.parent.mkdir(parents=True, exist_ok=True)
    resolution_path.write_text(json.dumps(resolution, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    resolution_path.with_suffix(".md").write_text(_render_browser_dars_revision_resolution_md(resolution), encoding="utf-8")
    report_ref = f"reports/run-summaries/{yyyymmdd}/browser-dars-revision-resolution-report.json"
    report = BrowserDarsRevisionResolutionReport.model_validate({
        "schema_id": "hisys.browser_dars_revision_resolution.report",
        "schema_version": "0.1.0",
        "request_id": resolution["request_id"],
        "dars_review_ref": dars_review_ref,
        "revision_resolution_ref": resolution_ref,
        "decision": resolution["decision"],
        "segment_normalization_status": resolution["segment_normalization_status"],
        "corroboration_mapping_status": resolution["corroboration_mapping_status"],
        "external_call_made": False,
        "mutation_performed": False,
    }).model_dump(mode="json")
    report_path = instance.root / report_ref
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.with_suffix(".md").write_text(_render_browser_dars_revision_report_md(report), encoding="utf-8")
    print(f"browser dars revision resolution: report={report_path}")
    print(f"decision: {resolution['decision']}")
    print(f"segment_normalization_status: {resolution['segment_normalization_status']}")
    print(f"corroboration_mapping_status: {resolution['corroboration_mapping_status']}")
    print("external_call_made: false")
    return 0



def _load_json_ref(instance: InstanceRoot, ref: str) -> dict[str, object]:
    path = instance.root / ref
    if path.exists() and path.is_file():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            return loaded
    return {}















def _cmd_final_review_browser_investigation(
    *,
    instance_root: Path,
    yyyymmdd: str,
    revision_resolution_ref: str,
    producer_id: str,
) -> int:
    instance = InstanceRoot(instance_root)
    revision_path = instance.root / revision_resolution_ref
    if not revision_path.exists():
        print(f"browser revision resolution not found: {revision_resolution_ref}", file=sys.stderr)
        return 1
    revision = json.loads(revision_path.read_text(encoding="utf-8"))
    if not _browser_revision_ready_for_final_review(revision):
        print("final browser review: blocked reason=revision_resolution_not_ready")
        return 2
    final_review = FinalBrowserAcceptanceReview.model_validate(_build_final_browser_acceptance_review(
        request_id=str(revision.get("request_id") or _browser_request_id_from_ref(revision_resolution_ref)),
        revision_resolution_ref=revision_resolution_ref,
        revision=revision,
        producer_id=producer_id,
    )).model_dump(mode="json")
    final_ref = f"data/chief-editor-final-browser-reviews/{yyyymmdd}/FINAL-CHIEF-REVIEW-{final_review['request_id']}-BROWSER.json"
    final_path = instance.root / final_ref
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(json.dumps(final_review, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    final_path.with_suffix(".md").write_text(_render_final_browser_acceptance_review_md(final_review), encoding="utf-8")
    report_ref = f"reports/run-summaries/{yyyymmdd}/final-browser-acceptance-review-report.json"
    report = FinalBrowserAcceptanceReviewReport.model_validate({
        "schema_id": "hisys.chief_editor.final_browser_acceptance_review.report",
        "schema_version": "0.1.0",
        "request_id": final_review["request_id"],
        "revision_resolution_ref": revision_resolution_ref,
        "final_review_ref": final_ref,
        "decision": final_review["decision"],
        "publication_or_live_action_approved": False,
        "external_call_made": False,
        "mutation_performed": False,
    }).model_dump(mode="json")
    report_path = instance.root / report_ref
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.with_suffix(".md").write_text(_render_final_browser_acceptance_report_md(report), encoding="utf-8")
    print(f"final browser review: report={report_path}")
    print(f"decision: {final_review['decision']}")
    print("publication_or_live_action_approved: false")
    print("action_taken: none")
    print("external_call_made: false")
    return 0















def _cmd_request_dars_critique(
    *,
    instance_root: Path,
    yyyymmdd: str,
    source_execution_id: str,
    critique_text: str,
    producer_id: str,
    backend: str,
    approval_ref: str | None,
    backend_activation_packet_ref: str | None = None,
) -> int:
    instance = InstanceRoot(instance_root)
    runtime = DarsRuntime(instance=instance)
    if critique_text:
        report = runtime.run_fixture_critique(
            yyyymmdd=yyyymmdd,
            source_execution_id=source_execution_id,
            critique_text=critique_text,
            producer_id=producer_id,
        )
        backend_label = "fixture_text"
        external_call_made = False
    elif backend == "loopback":
        report = runtime.run_loopback_placeholder(
            yyyymmdd=yyyymmdd,
            source_execution_id=source_execution_id,
            producer_id=producer_id,
        )
        backend_label = "loopback_placeholder"
        external_call_made = False
    else:
        report = runtime.run_configured_critique(
            yyyymmdd=yyyymmdd,
            source_execution_id=source_execution_id,
            producer_id=producer_id,
            approval_ref=approval_ref,
            backend_activation_packet_ref=backend_activation_packet_ref,
        )
        config_path = instance.config_dir / "dars.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        backend_label = config_data["spec"]["default_backend"]
        external_call_made = bool(config_data["spec"]["backends"][backend_label].get("external_call_allowed"))
    print(f"dars critique: report={instance.root / report.report_ref}")
    print(f"handoffs: {len(report.handoff_refs)}")
    print(f"critiques: {len(report.critique_refs)}")
    print(f"linked_executions: {len(report.linked_execution_refs)}")
    print(f"skipped_executions: {len(report.skipped_execution_refs)}")
    print(f"dars_backend: {backend_label}")
    print(f"external_call_made: {str(external_call_made).lower()}")
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
