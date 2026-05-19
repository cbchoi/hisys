"""Concrete three-layer domain use cases.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001,
HISYS-CON-010..012.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.schemas.domain_investigation import DomainInvestigationRequest

from .layers import (
    AggregationWorkProduct,
    DecisionWorkProduct,
    DomainUseCase,
    DomainUseCaseContext,
    InvestigationWorkProduct,
)


class ResearchInvestigationLayer:
    """Investigate research evidence from local memos and publisher sources."""

    def __init__(self, *, me_vault_root: str = "/home/cbchoi/me") -> None:
        self._me_vault_root = me_vault_root

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
    ) -> InvestigationWorkProduct:
        return InvestigationWorkProduct(
            work_product_id=f"INVEST-{request.request_id}-RESEARCH",
            scope="research",
            local_search_targets=[self._me_vault_root],
            data_source_targets=["publisher_source"],
            memo_refs=[f"memo://{request.request_id}/local-research-memos"],
            evidence_refs=[
                *[source.source_id for source in request.sources],
                f"publisher-source-plan://{request.request_id}",
            ],
        )


REQUIREMENTS_ANALYSIS_OBJECTIVE_PREFIX = "requirements-analysis:"
REQUIREMENTS_ANALYSIS_OBJECTIVE_MARKER = "[requirements-analysis]"


def _is_requirements_analysis_objective(objective: str) -> bool:
    """Detect the requirements-analysis subtype convention under `codebase`."""

    normalized = objective.strip().lower()
    return normalized.startswith(REQUIREMENTS_ANALYSIS_OBJECTIVE_PREFIX) or normalized.startswith(
        REQUIREMENTS_ANALYSIS_OBJECTIVE_MARKER
    )


CODEBASE_ARTIFACT_REF_PREFIX = "runtime-boundary/codebase-analysis/"


def _is_codebase_artifact_ref(ref: str) -> bool:
    """Return true for safe local codebase-analysis runtime-boundary refs."""

    parts = ref.split("/")
    return ref.startswith(CODEBASE_ARTIFACT_REF_PREFIX) and ".." not in parts


def _extract_codebase_artifact_refs(request: DomainInvestigationRequest) -> list[str]:
    """Extract ordered, deduplicated local codebase-analysis artifact refs."""

    seen: set[str] = set()
    refs: list[str] = []
    for source in request.sources:
        if source.source_type != "runtime_record":
            continue
        if not _is_codebase_artifact_ref(source.ref):
            continue
        if source.ref in seen:
            continue
        seen.add(source.ref)
        refs.append(source.ref)
    return refs


class CodeInvestigationLayer:
    """Investigate code evidence from local memos and requirements folders."""

    def __init__(self, *, me_vault_root: str = "/home/cbchoi/me", requirements_root: str) -> None:
        self._me_vault_root = me_vault_root
        self._requirements_root = requirements_root

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
    ) -> InvestigationWorkProduct:
        # Requirements-analysis remains a codebase subtype via objective
        # labeling so audit reviewers can distinguish it from generic codebase
        # evaluation without expanding `DomainName`.
        is_requirements_analysis = _is_requirements_analysis_objective(request.objective)
        suffix = "REQUIREMENTS-ANALYSIS" if is_requirements_analysis else "CODE"
        scope = "codebase:requirements-analysis" if is_requirements_analysis else "codebase"
        memo_kind = (
            "local-requirements-analysis-memos"
            if is_requirements_analysis
            else "local-code-and-requirements-memos"
        )
        codebase_artifact_refs = _extract_codebase_artifact_refs(request)
        codebase_artifact_ref_set = set(codebase_artifact_refs)
        return InvestigationWorkProduct(
            work_product_id=f"INVEST-{request.request_id}-{suffix}",
            scope=scope,
            local_search_targets=[self._me_vault_root, self._requirements_root],
            data_source_targets=["local_requirements_folder"],
            memo_refs=[f"memo://{request.request_id}/{memo_kind}"],
            evidence_refs=[
                *[
                    source.source_id
                    for source in request.sources
                    if source.ref not in codebase_artifact_ref_set
                ],
                f"requirements-folder://{self._requirements_root}",
            ],
            codebase_artifact_refs=codebase_artifact_refs,
            domain_subtype="requirements-analysis" if is_requirements_analysis else None,
        )


class MemoReportAggregationLayer:
    """Aggregate investigation memos into one report work product."""

    def aggregate(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
        investigation: InvestigationWorkProduct,
    ) -> AggregationWorkProduct:
        report_ref = f"runtime-boundary/domain-investigation/{request.domain}/{context.yyyymmdd}/aggregation-report-{request.request_id}.md"
        summary = f"Aggregated {investigation.scope} memos and evidence for {request.request_id}."
        _write_aggregation_report(
            instance_root=context.instance_root,
            report_ref=report_ref,
            request=request,
            investigation=investigation,
            summary=summary,
        )
        return AggregationWorkProduct(
            work_product_id=f"AGG-{request.request_id}",
            report_type="memo_aggregation_report",
            input_memo_refs=investigation.memo_refs,
            input_evidence_refs=investigation.evidence_refs,
            report_ref=report_ref,
            summary=summary,
        )


class DarsDecisionLayer:
    """Run the DARS decision-review boundary over an aggregation report."""

    def __init__(self, *, decision_type: str) -> None:
        self._decision_type = decision_type

    def decide(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
        aggregation: AggregationWorkProduct,
    ) -> DecisionWorkProduct:
        decision_ref = f"runtime-boundary/dars/{context.yyyymmdd}/dars-decision-{request.request_id}.json"
        # Persist a structured advisory placeholder so the recorded ref always
        # resolves to a real artifact; downstream auditors can tell the
        # placeholder apart from a completed DARS decision via the `status`
        # field. Missing DARS output must be explicit, not a dangling path.
        _write_dars_decision_placeholder(
            instance_root=context.instance_root,
            decision_ref=decision_ref,
            request=request,
            aggregation=aggregation,
            decision_type=self._decision_type,
        )
        return DecisionWorkProduct(
            work_product_id=f"DEC-{request.request_id}",
            decision_engine="DARS",
            decision_type=self._decision_type,
            input_report_ref=aggregation.report_ref,
            decision_ref=decision_ref,
            recommendation="human_review_required",
            requires_human_review=True,
        )


def _write_aggregation_report(
    *,
    instance_root: Path,
    report_ref: str,
    request: DomainInvestigationRequest,
    investigation: InvestigationWorkProduct,
    summary: str,
) -> None:
    output_path = instance_root / report_ref
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                f"# Aggregation Report {request.request_id}",
                "",
                f"- domain: {request.domain}",
                f"- scope: {investigation.scope}",
                f"- input memo refs: {len(investigation.memo_refs)}",
                f"- input evidence refs: {len(investigation.evidence_refs)}",
                f"- external call made: {str(investigation.external_call_made).lower()}",
                f"- mutation performed: {str(investigation.mutation_performed).lower()}",
                "",
                summary,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_dars_decision_placeholder(
    *,
    instance_root: Path,
    decision_ref: str,
    request: DomainInvestigationRequest,
    aggregation: AggregationWorkProduct,
    decision_type: str,
) -> None:
    output_path = instance_root / decision_ref
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_id": "hisys.domain.dars_decision_placeholder",
        "schema_version": "0.1.0",
        "request_id": request.request_id,
        "decision_engine": "DARS",
        "decision_type": decision_type,
        "input_report_ref": aggregation.report_ref,
        "recommendation": "human_review_required",
        "requires_human_review": True,
        "advisory_only": True,
        "external_call_made": False,
        "mutation_performed": False,
        "status": "pending_human_review",
        "policy_refs": [
            "HISYS-FR-AGT-001",
            "HISYS-FR-AGT-003",
            "HISYS-CON-010",
            "HISYS-CON-012",
        ],
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class ResearchAnalysisUseCase(DomainUseCase):
    """Research use case: local me-vault + publisher investigation, memo report, DARS."""

    def __init__(self, *, me_vault_root: str = "/home/cbchoi/me") -> None:
        super().__init__(
            investigation_layer=ResearchInvestigationLayer(me_vault_root=me_vault_root),
            aggregation_layer=MemoReportAggregationLayer(),
            decision_layer=DarsDecisionLayer(decision_type="research_review"),
        )


class CodeAnalysisUseCase(DomainUseCase):
    """Code use case: local me-vault + requirements-folder investigation, memo report, DARS."""

    def __init__(self, *, me_vault_root: str = "/home/cbchoi/me", requirements_root: str) -> None:
        super().__init__(
            investigation_layer=CodeInvestigationLayer(
                me_vault_root=me_vault_root,
                requirements_root=requirements_root,
            ),
            aggregation_layer=MemoReportAggregationLayer(),
            decision_layer=DarsDecisionLayer(decision_type="code_evaluation_review"),
        )


class InvestmentInvestigationLayer:
    """Read-only investigation over local investment evidence artifacts.

    Traceability: HISYS-FR-DOM-006, HISYS-NFR-SEC-001..004.
    """

    def __init__(self, *, me_vault_root: str = "/home/cbchoi/me") -> None:
        self._me_vault_root = me_vault_root

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
    ) -> InvestigationWorkProduct:
        return InvestigationWorkProduct(
            work_product_id=f"INVEST-{request.request_id}-INVESTMENT",
            scope="investment",
            local_search_targets=[
                self._me_vault_root,
                "runtime-boundary/investment-decisions",
            ],
            data_source_targets=["investment_decision_packet_artifact"],
            memo_refs=[f"memo://{request.request_id}/investment-advisory-memos"],
            evidence_refs=[
                *[source.source_id for source in request.sources],
                f"investment-packet-plan://{request.request_id}",
            ],
        )


class InvestmentAdvisoryDecisionLayer:
    """Investment decision layer: always advisory, never autonomous.

    The recommendation summary embeds the advisory-only governance flags
    so audit reviewers can confirm `execution_authorized=false` and
    `publication_or_live_action_approved=false` directly from the runtime
    artifact without re-resolving the underlying investment packet.

    Traceability: HISYS-FR-DOM-006, HISYS-NFR-SEC-004, HISYS-T-028.
    """

    def decide(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
        aggregation: AggregationWorkProduct,
    ) -> DecisionWorkProduct:
        decision_ref = (
            f"runtime-boundary/dars/{context.yyyymmdd}/"
            f"investment-advisory-decision-{request.request_id}.json"
        )
        recommendation = (
            "Investment advisory result: not financial advice; no autonomous execution; "
            "execution_authorized=false; publication_or_live_action_approved=false; "
            "human review required before any consequential use."
        )
        return DecisionWorkProduct(
            work_product_id=f"DEC-{request.request_id}",
            decision_engine="DARS",
            decision_type="investment_advisory_review",
            input_report_ref=aggregation.report_ref,
            decision_ref=decision_ref,
            recommendation=recommendation,
            requires_human_review=True,
            governance_flags={
                "execution_authorized": False,
                "publication_or_live_action_approved": False,
                "autonomous_execution_allowed": False,
                "credential_use_allowed": False,
                "live_external_action_allowed": False,
            },
        )


class InvestmentAnalysisUseCase(DomainUseCase):
    """Investment use case: read-only local artifacts, advisory-only DARS review.

    This use case migrates the investment domain into the structured-domain
    substrate while reusing the existing investment packet/dry-run/operator-
    review CLI as the system of record. It never authorizes live execution,
    publication, credential use, or external mutation.
    """

    def __init__(self, *, me_vault_root: str = "/home/cbchoi/me") -> None:
        super().__init__(
            investigation_layer=InvestmentInvestigationLayer(me_vault_root=me_vault_root),
            aggregation_layer=MemoReportAggregationLayer(),
            decision_layer=InvestmentAdvisoryDecisionLayer(),
        )


__all__ = [
    "CodeAnalysisUseCase",
    "CodeInvestigationLayer",
    "DarsDecisionLayer",
    "InvestmentAdvisoryDecisionLayer",
    "InvestmentAnalysisUseCase",
    "InvestmentInvestigationLayer",
    "MemoReportAggregationLayer",
    "ResearchAnalysisUseCase",
    "ResearchInvestigationLayer",
]
