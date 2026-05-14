"""Persist structured domain runtime artifacts.

Traceability: HISYS-DOM-003, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.translation import DomainUseCaseArtifactPacket


@dataclass(frozen=True)
class DomainRuntimeArtifactRefs:
    """Relative refs for persisted structured-domain runtime artifacts."""

    json_ref: Path
    markdown_ref: Path


class DomainRuntimeArtifactWriter:
    """Write a structured domain packet under the governed runtime boundary."""

    def write(self, packet: DomainUseCaseArtifactPacket, context: DomainUseCaseContext) -> DomainRuntimeArtifactRefs:
        artifact_dir = context.boundary_dir / packet.domain / context.yyyymmdd
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_path = artifact_dir / f"domain-use-case-result-{packet.request_id}.json"
        markdown_path = artifact_dir / f"domain-use-case-result-{packet.request_id}.md"

        json_path.write_text(
            json.dumps(packet.to_runtime_record(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(self._format_markdown(packet), encoding="utf-8")
        return DomainRuntimeArtifactRefs(
            json_ref=json_path.relative_to(context.instance_root),
            markdown_ref=markdown_path.relative_to(context.instance_root),
        )

    def _format_markdown(self, packet: DomainUseCaseArtifactPacket) -> str:
        trace = ", ".join(step.layer for step in packet.layer_trace)
        return "\n".join(
            [
                f"# Structured Domain Result: {packet.request_id}",
                "",
                f"Domain: {packet.domain}",
                f"Quality gate: {packet.quality_gate}",
                f"Human review required: {str(packet.requires_human_review).lower()}",
                f"External call made: {str(packet.external_call_made).lower()}",
                f"Mutation performed: {str(packet.mutation_performed).lower()}",
                f"Layer trace: {trace}",
                "",
                packet.recommendation_summary,
                "",
            ]
        )


__all__ = ["DomainRuntimeArtifactRefs", "DomainRuntimeArtifactWriter"]
