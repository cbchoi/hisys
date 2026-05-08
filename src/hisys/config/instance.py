"""Runtime instance root path helpers.

Traceability: HISYS-RUNTIME-DIR-001, HISYS-D-015, HISYS-D-016,
HISYS-T-023.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstanceRoot:
    """Resolved Hisys runtime instance root.

    Product code stays in the package repository. Mutable runtime state lives
    under this instance root per HISYS-RUNTIME-DIR-001.
    """

    root: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def templates_dir(self) -> Path:
        return self.root / "templates"

    @property
    def harness_dir(self) -> Path:
        return self.root / "harness"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def runtime_boundary_dir(self) -> Path:
        return self.root / "runtime-boundary"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    def raw_observations_dir(self, yyyymmdd: str) -> Path:
        return self.data_dir / "raw-observations" / yyyymmdd

    def raw_payloads_dir(self, yyyymmdd: str, source_id: str) -> Path:
        return self.data_dir / "raw-payloads" / yyyymmdd / source_id

    def hermes_traces_dir(self, yyyymmdd: str) -> Path:
        return self.data_dir / "hermes-traces" / yyyymmdd

    def audit_dir(self, yyyymmdd: str) -> Path:
        return self.data_dir / "audit" / yyyymmdd

    def audit_log_path(self, yyyymmdd: str) -> Path:
        return self.audit_dir(yyyymmdd) / f"AUDIT-{yyyymmdd}.jsonl"

    def hermes_boundary_dir(self, yyyymmdd: str, campaign_id: str) -> Path:
        return self.runtime_boundary_dir / "hermes" / yyyymmdd / campaign_id

    def run_summary_path(self, collection_run_id: str) -> Path:
        return self.reports_dir / "run-summaries" / f"collection-run-{collection_run_id}.md"


__all__ = ["InstanceRoot"]
