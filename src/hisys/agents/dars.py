"""Runtime-local DARS advisory critique handoff foundation.

Traceability: HISYS-FR-AGT-001..005, HISYS-DARS-CONTRACT-001,
HISYS-D-015, HISYS-T-023.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..config.instance import InstanceRoot
from ..schemas import AgentHandoffPackage


class DarsCritiqueRecord(BaseModel):
    critique_id: str
    handoff_ref: str
    source_execution_ref: str
    target_agent_system: str = "DARS"
    critique_text: str
    allowed_actions: Literal["advisory_only"] = "advisory_only"
    action_taken: Literal["none"] = "none"
    status: Literal["received"] = "received"
    producer_id: str
    policy_refs: list[str] = Field(default_factory=lambda: ["HISYS-FR-AGT-001", "HISYS-FR-AGT-002", "HISYS-FR-AGT-003", "HISYS-T-023"])


@dataclass(frozen=True)
class DarsCritiqueReport:
    report_ref: str
    handoff_refs: list[str] = field(default_factory=list)
    critique_refs: list[str] = field(default_factory=list)
    linked_execution_refs: list[str] = field(default_factory=list)
    skipped_execution_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=lambda: ["HISYS-FR-AGT-001", "HISYS-FR-AGT-002", "HISYS-FR-AGT-003", "HISYS-T-023"])


class DarsRuntime:
    """Prepare advisory DARS handoffs and ingest fixture critiques locally."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def run_fixture_critique(
        self,
        *,
        yyyymmdd: str,
        source_execution_id: str,
        critique_text: str,
        producer_id: str,
    ) -> DarsCritiqueReport:
        execution = _load_connector_execution(self.instance, yyyymmdd, source_execution_id)
        report = DarsCritiqueReport(report_ref=str(_report_json_path(self.instance, yyyymmdd).relative_to(self.instance.root)))
        if not execution:
            report.skipped_execution_refs.append(source_execution_id)
            _write_report(self.instance, yyyymmdd, report)
            return report

        suffix = _suffix(source_execution_id)
        handoff_id = f"HANDOFF-DARS-{suffix}"
        critique_id = f"CRITIQUE-DARS-{suffix}"
        handoff = AgentHandoffPackage(
            handoff_id=handoff_id,
            target_agent_system="DARS",
            task="critique_alert_connector_execution",
            context=(
                "Runtime-local disabled connector execution requires advisory critique; "
                f"execution={source_execution_id}; alert_decision={execution.get('alert_decision_ref', '')}."
            ),
            evidence_bundle=[source_execution_id],
            constraints=[
                "advisory_only",
                "no live external action",
                "do not mutate alert decisions or connector executions",
            ],
            expected_output="advisory critique text and optional improvement notes",
            allowed_actions="advisory_only",
            approval_state="not_required",
            result_refs=[critique_id],
            status="linked",
            producer_id=producer_id,
        )
        critique = DarsCritiqueRecord(
            critique_id=critique_id,
            handoff_ref=handoff_id,
            source_execution_ref=source_execution_id,
            critique_text=critique_text,
            producer_id=producer_id,
        )
        _write_handoff(self.instance, yyyymmdd, handoff)
        _write_critique(self.instance, yyyymmdd, critique)
        report.handoff_refs.append(handoff_id)
        report.critique_refs.append(critique_id)
        report.linked_execution_refs.append(source_execution_id)
        _write_report(self.instance, yyyymmdd, report)
        return report


def _load_connector_execution(instance: InstanceRoot, yyyymmdd: str, execution_id: str) -> dict | None:
    path = instance.data_dir / "alert-connector-executions" / yyyymmdd / f"{execution_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_handoff(instance: InstanceRoot, yyyymmdd: str, handoff: AgentHandoffPackage) -> None:
    output_dir = instance.data_dir / "agent-handoffs" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = handoff.model_dump(mode="json")
    (output_dir / f"{handoff.handoff_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / f"{handoff.handoff_id}.md").write_text(
        "\n".join([
            f"# DARS handoff {handoff.handoff_id}",
            "",
            f"- target_agent_system: {handoff.target_agent_system}",
            f"- task: {handoff.task}",
            f"- allowed_actions: {handoff.allowed_actions}",
            f"- approval_state: {handoff.approval_state}",
            f"- status: {handoff.status}",
            f"- evidence_bundle: {', '.join(handoff.evidence_bundle)}",
            "",
        ]),
        encoding="utf-8",
    )


def _write_critique(instance: InstanceRoot, yyyymmdd: str, critique: DarsCritiqueRecord) -> None:
    output_dir = instance.data_dir / "agent-critiques" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = critique.model_dump(mode="json")
    (output_dir / f"{critique.critique_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / f"{critique.critique_id}.md").write_text(
        "\n".join([
            f"# DARS critique {critique.critique_id}",
            "",
            f"- handoff_ref: {critique.handoff_ref}",
            f"- source_execution_ref: {critique.source_execution_ref}",
            f"- allowed_actions: {critique.allowed_actions}",
            f"- action_taken: {critique.action_taken}",
            "",
            critique.critique_text,
            "",
        ]),
        encoding="utf-8",
    )


def _write_report(instance: InstanceRoot, yyyymmdd: str, report: DarsCritiqueReport) -> None:
    report_path = _report_json_path(instance, yyyymmdd)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _report_md_path(instance, yyyymmdd).write_text(
        "\n".join([
            "# DARS Critique Report",
            "",
            f"- handoffs: {len(report.handoff_refs)}",
            f"- critiques: {len(report.critique_refs)}",
            f"- linked_executions: {len(report.linked_execution_refs)}",
            f"- skipped_executions: {len(report.skipped_execution_refs)}",
            "",
        ]),
        encoding="utf-8",
    )


def _report_json_path(instance: InstanceRoot, yyyymmdd: str) -> Path:
    return instance.reports_dir / "run-summaries" / yyyymmdd / "dars-critique-report.json"


def _report_md_path(instance: InstanceRoot, yyyymmdd: str) -> Path:
    return instance.reports_dir / "run-summaries" / yyyymmdd / "dars-critique-report.md"


def _suffix(source_execution_id: str) -> str:
    raw = source_execution_id.removeprefix("EXEC-")
    if raw.startswith("DARS-"):
        return raw.removeprefix("DARS-")
    return raw


__all__ = ["DarsCritiqueRecord", "DarsCritiqueReport", "DarsRuntime"]
