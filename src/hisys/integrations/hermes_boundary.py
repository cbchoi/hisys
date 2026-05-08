"""Hermes Markdown boundary record writer.

Traceability: HISYS-D-016, HISYS-FR-DS-006, HISYS-FR-INV-006,
HISYS-DATA-005, HISYS-T-005A.
"""

from __future__ import annotations

from ..config import InstanceRoot


class HermesBoundaryWriter:
    """Write human-reviewable Hermes runtime boundary Markdown records."""

    def __init__(self, instance: InstanceRoot) -> None:
        self.instance = instance

    def write_record(
        self,
        *,
        yyyymmdd: str,
        campaign_id: str,
        record_kind: str,
        stable_id: str,
        title: str,
        body: str,
    ) -> str:
        directory = self.instance.hermes_boundary_dir(yyyymmdd, campaign_id)
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{record_kind}-{stable_id}.md"
        path = directory / filename
        path.write_text(f"---\nrecord_kind: {record_kind}\ncampaign_id: {campaign_id}\n---\n\n# {title}\n\n{body}\n", encoding="utf-8")
        return f"hisys/runtime-boundary/hermes/{yyyymmdd}/{campaign_id}/{filename}"


__all__ = ["HermesBoundaryWriter"]
