"""Release-readiness evidence summaries.

Traceability: HISYS-T-024, HISYS-FR-ADM-001..004, HISYS-DATA-001..005,
HISYS-CON-*.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

REQUIRED_QUALITY_GATES = frozenset({"pytest", "traceability", "secret_scan", "backup_restore", "health_status"})
REQUIRED_TRACE_PATH_REFS = frozenset(
    {
        "SourceRegistryEntry",
        "RawObservation",
        "ExtractedSignal",
        "ZettelMemo",
        "AlertDecisionRecord",
        "AuditEvent",
    }
)

GateStatus = Literal["pass", "fail", "blocked", "not_run"]
ReadinessStatus = Literal["ready_for_review", "not_ready"]
ReleaseDecision = Literal["human_review_ready", "continue_hardening"]


class QualityGateResult(BaseModel):
    """One release-readiness quality gate result."""

    name: str
    status: GateStatus
    evidence: str


class ReleaseReadinessReport(BaseModel):
    """Human-reviewable release-readiness evidence summary."""

    schema_id: Literal["hisys.release_readiness_report"] = "hisys.release_readiness_report"
    schema_version: Literal["0.1.0"] = "0.1.0"
    runtime_root: str
    quality_gates: list[QualityGateResult]
    trace_path_refs: list[str]
    known_gaps: list[str] = Field(default_factory=list)
    required_gate_count: int
    passed_gate_count: int
    trace_path_complete: bool
    overall_status: ReadinessStatus
    release_decision: ReleaseDecision
    external_call_made: Literal[False] = False
    mutation_performed: Literal[False] = False
    publication_or_live_action_approved: Literal[False] = False
    execution_authorized: Literal[False] = False
    requirement_refs: list[str] = Field(
        default_factory=lambda: [
            "HISYS-T-024",
            "HISYS-FR-ADM-001",
            "HISYS-FR-ADM-002",
            "HISYS-FR-ADM-003",
            "HISYS-FR-ADM-004",
            "HISYS-DATA-001",
            "HISYS-DATA-002",
            "HISYS-DATA-003",
            "HISYS-DATA-004",
            "HISYS-DATA-005",
        ]
    )

    def to_markdown(self) -> str:
        """Render a shareable release-readiness evidence memo."""

        gate_rows = "\n".join(
            f"| {gate.name} | {gate.status} | {gate.evidence} |" for gate in self.quality_gates
        )
        trace_lines = "\n".join(f"- {ref}" for ref in self.trace_path_refs)
        gaps = "\n".join(f"- {gap}" for gap in self.known_gaps) if self.known_gaps else "- none"
        return "\n".join(
            [
                "# Hisys Release Readiness Evidence Report",
                "",
                "Traceability: " + ", ".join(self.requirement_refs),
                "",
                f"Overall status: `{self.overall_status}`",
                f"Release decision: `{self.release_decision}`",
                f"Runtime root: `{self.runtime_root}`",
                "",
                "## Quality Gates",
                "",
                "| Gate | Status | Evidence |",
                "|---|---|---|",
                gate_rows,
                "",
                "## End-to-end Trace Path Evidence",
                "",
                f"Trace path complete: `{self.trace_path_complete}`",
                trace_lines,
                "",
                "## Known Gaps",
                "",
                gaps,
                "",
            ]
        )


def build_release_readiness_report(
    *,
    runtime_root: str | Path,
    quality_gates: list[QualityGateResult],
    trace_path_refs: list[str],
    known_gaps: list[str],
) -> ReleaseReadinessReport:
    """Build release-readiness status from explicit gate and trace evidence."""

    gate_by_name = {gate.name: gate for gate in quality_gates}
    passed_required = {
        name for name in REQUIRED_QUALITY_GATES if gate_by_name.get(name) and gate_by_name[name].status == "pass"
    }
    trace_complete = REQUIRED_TRACE_PATH_REFS.issubset(set(trace_path_refs))
    ready = not known_gaps and passed_required == REQUIRED_QUALITY_GATES and trace_complete
    return ReleaseReadinessReport(
        runtime_root=str(Path(runtime_root)),
        quality_gates=quality_gates,
        trace_path_refs=trace_path_refs,
        known_gaps=known_gaps,
        required_gate_count=len(REQUIRED_QUALITY_GATES),
        passed_gate_count=len(passed_required),
        trace_path_complete=trace_complete,
        overall_status="ready_for_review" if ready else "not_ready",
        release_decision="human_review_ready" if ready else "continue_hardening",
    )


__all__ = ["QualityGateResult", "ReleaseReadinessReport", "build_release_readiness_report"]
