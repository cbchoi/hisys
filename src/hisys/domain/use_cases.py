"""Concrete three-layer domain use cases.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001,
HISYS-CON-010..012.
"""

from __future__ import annotations

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
        return InvestigationWorkProduct(
            work_product_id=f"INVEST-{request.request_id}-CODE",
            scope="codebase",
            local_search_targets=[self._me_vault_root, self._requirements_root],
            data_source_targets=["local_requirements_folder"],
            memo_refs=[f"memo://{request.request_id}/local-code-and-requirements-memos"],
            evidence_refs=[
                *[source.source_id for source in request.sources],
                f"requirements-folder://{self._requirements_root}",
            ],
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
        return AggregationWorkProduct(
            work_product_id=f"AGG-{request.request_id}",
            report_type="memo_aggregation_report",
            input_memo_refs=investigation.memo_refs,
            input_evidence_refs=investigation.evidence_refs,
            report_ref=report_ref,
            summary=f"Aggregated {investigation.scope} memos and evidence for {request.request_id}.",
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
        return DecisionWorkProduct(
            work_product_id=f"DEC-{request.request_id}",
            decision_engine="DARS",
            decision_type=self._decision_type,
            input_report_ref=aggregation.report_ref,
            decision_ref=decision_ref,
            recommendation="human_review_required",
            requires_human_review=True,
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


__all__ = [
    "CodeAnalysisUseCase",
    "CodeInvestigationLayer",
    "DarsDecisionLayer",
    "MemoReportAggregationLayer",
    "ResearchAnalysisUseCase",
    "ResearchInvestigationLayer",
]
