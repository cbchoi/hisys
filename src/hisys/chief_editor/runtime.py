"""Chief Editor alert decision runtime.

Traceability: HISYS-FR-CE-001..006, HISYS-CE-POLICY-001,
HISYS-D-015, HISYS-T-014, HISYS-T-015, HISYS-T-016, HISYS-T-017,
HISYS-T-018, HISYS-SCHEMA-001, HISYS-FR-INV-001, HISYS-FR-INV-003,
HISYS-T-024.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import BaseModel

from ..config import InstanceRoot
from ..core.ids import IdNamespace, make_id
from ..editor import MemoReviewReport
from ..schemas import AlertDecisionRecord, EvidenceChainRecord, HisysMode, ZettelMemo
from .policy import ChiefEditorPolicy


@dataclass(frozen=True)
class AlertDecisionRunReport:
    """Machine-checkable I7 alert decision run report."""

    reviewed_memo_refs: list[str]
    alert_decision_refs: list[str] = field(default_factory=list)
    non_escalation_decision_refs: list[str] = field(default_factory=list)
    suppressed_memo_refs: list[str] = field(default_factory=list)
    skipped_memo_refs: list[str] = field(default_factory=list)
    evidence_chain_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(
        default_factory=lambda: ["HISYS-FR-CE-004", "HISYS-CE-POLICY-001", "HISYS-T-016"]
    )


class ChiefEditorRuntime:
    """Persist fixture Chief Editor alert decisions under a runtime instance root."""

    def __init__(
        self,
        *,
        instance: InstanceRoot,
        policy: ChiefEditorPolicy,
        producer_id: str,
        hisys_mode: HisysMode | None = None,
    ) -> None:
        self.instance = instance
        self.policy = policy
        self.producer_id = producer_id
        self.hisys_mode = hisys_mode or HisysMode()

    def decide_run(
        self,
        memos: list[ZettelMemo],
        *,
        memo_review_report: MemoReviewReport,
        yyyymmdd: str,
    ) -> AlertDecisionRunReport:
        memo_by_id = {memo.memo_id: memo for memo in memos}
        alert_refs: list[str] = []
        non_escalation_refs: list[str] = []
        suppressed_refs: list[str] = []
        skipped_refs: list[str] = []
        chain_refs: list[str] = []
        existing_suppression_keys = _load_existing_suppression_keys(self.instance, yyyymmdd)
        current_suppression_keys: set[str] = set()
        for memo_id in memo_review_report.reviewed_memo_refs:
            memo = memo_by_id.get(memo_id)
            if memo is None:
                skipped_refs.append(memo_id)
                continue
            candidate = self.policy.decide(memo, producer_id=self.producer_id)
            if candidate is None:
                skipped_refs.append(memo_id)
                continue
            suppress_repeated = (
                candidate.status != "suppressed"
                and candidate.suppression_key is not None
                and candidate.suppression_key in existing_suppression_keys | current_suppression_keys
            )
            decision = self.policy.decide(
                memo,
                producer_id=self.producer_id,
                suppress_repeated_alert=suppress_repeated,
            )
            if decision is None:
                skipped_refs.append(memo_id)
                continue
            decision = decision.model_copy(update={"alert_id": make_id(IdNamespace.ALERT)})
            if decision.suppression_key is not None:
                current_suppression_keys.add(decision.suppression_key)
            self._write_decision(decision, yyyymmdd)
            if decision.status == "suppressed":
                suppressed_refs.extend(decision.memo_refs)
                non_escalation_refs.append(decision.alert_id)
            else:
                alert_refs.append(decision.alert_id)
                if self.hisys_mode.level in ("decision", "publication"):
                    chain = self._build_evidence_chain(decision=decision, memo=memo)
                    self._write_evidence_chain(decision=decision, chain=chain, yyyymmdd=yyyymmdd)
                    chain_refs.append(chain.chain_id)
        report = AlertDecisionRunReport(
            reviewed_memo_refs=list(memo_review_report.reviewed_memo_refs),
            alert_decision_refs=alert_refs,
            non_escalation_decision_refs=non_escalation_refs,
            suppressed_memo_refs=suppressed_refs,
            skipped_memo_refs=skipped_refs,
            evidence_chain_refs=chain_refs,
        )
        self._write_report(report, yyyymmdd)
        return report

    def _build_evidence_chain(
        self, *, decision: AlertDecisionRecord, memo: ZettelMemo
    ) -> EvidenceChainRecord:
        return EvidenceChainRecord(
            chain_id=make_id("CHAIN"),
            decision_ref=decision.alert_id,
            synthesis_refs=[memo.perspective_id],
            claim_ledger_refs=[memo.memo_id],
            evidence_refs=list(memo.signal_refs),
            source_refs=list(memo.source_refs),
            producer_id=self.producer_id,
            status="active",
        )

    def _write_evidence_chain(
        self,
        *,
        decision: AlertDecisionRecord,
        chain: EvidenceChainRecord,
        yyyymmdd: str,
    ) -> Path:
        directory = self.instance.root / "data" / "alert-decisions" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{decision.alert_id}.evidence_chain.json"
        path.write_text(_to_json(chain), encoding="utf-8")
        return path

    def _write_decision(self, decision: AlertDecisionRecord, yyyymmdd: str) -> tuple[Path, Path]:
        directory = self.instance.root / "data" / "alert-decisions" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / f"{decision.alert_id}.json"
        markdown_path = directory / f"{decision.alert_id}.md"
        json_path.write_text(_to_json(decision), encoding="utf-8")
        markdown_path.write_text(_decision_to_markdown(decision), encoding="utf-8")
        return json_path, markdown_path

    def _write_report(self, report: AlertDecisionRunReport, yyyymmdd: str) -> Path:
        directory = self.instance.root / "reports" / "run-summaries" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / "alert-decision-report.json"
        json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path = directory / "alert-decision-report.md"
        markdown_path.write_text(_report_to_markdown(report), encoding="utf-8")
        return json_path


def _load_existing_suppression_keys(instance: InstanceRoot, yyyymmdd: str) -> set[str]:
    directory = instance.root / "data" / "alert-decisions" / yyyymmdd
    if not directory.exists():
        return set()
    keys: set[str] = set()
    for path in sorted(directory.glob("ALERT-*.json")):
        decision = AlertDecisionRecord.model_validate_json(path.read_text(encoding="utf-8"))
        if decision.suppression_key and decision.status != "suppressed":
            keys.add(decision.suppression_key)
    return keys


def _to_json(record: BaseModel) -> str:
    return json.dumps(
        record.model_dump(mode="json", round_trip=True),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def _decision_to_markdown(decision: AlertDecisionRecord) -> str:
    return "\n".join(
        [
            "# Hisys Alert Decision",
            "",
            f"- alert_id: `{decision.alert_id}`",
            f"- trigger_reason: `{decision.trigger_reason}`",
            f"- severity: `{decision.severity}`",
            f"- status: `{decision.status}`",
            f"- action_taken: `{decision.action_taken}`",
            f"- approval_status: `{decision.approval_status}`",
            "",
            "## Memo Refs",
            *[f"- {ref}" for ref in decision.memo_refs],
            "",
            "## Signal Refs",
            *[f"- {ref}" for ref in decision.signal_refs],
            "",
            f"Follow-up: {decision.follow_up or 'none'}",
            "",
        ]
    )


def _report_to_markdown(report: AlertDecisionRunReport) -> str:
    return "\n".join(
        [
            "# Hisys Alert Decision Report",
            "",
            f"- reviewed_memos: {len(report.reviewed_memo_refs)}",
            f"- alert_decisions: {len(report.alert_decision_refs)}",
            f"- non_escalation_decisions: {len(report.non_escalation_decision_refs)}",
            f"- suppressed_memos: {len(report.suppressed_memo_refs)}",
            f"- skipped_memos: {len(report.skipped_memo_refs)}",
            "",
            "## Alert Decisions",
            *[f"- {ref}" for ref in report.alert_decision_refs],
            "",
            "## Non-escalation Decisions",
            *[f"- {ref}" for ref in report.non_escalation_decision_refs],
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


__all__ = ["AlertDecisionRunReport", "ChiefEditorRuntime"]
