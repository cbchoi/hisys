"""Lapidary governance audit writer.

Traceability: HISYS-SCHEMA-001, HISYS-FR-INV-001..006,
HISYS-DARS-CONTRACT-001, HISYS-D-015, HISYS-FR-ADM-002, HISYS-T-024.

Persists Lapidary governance records (evidence chains, weighted decision
alternatives, appraiser separation policies) under the audit instance root so
that downstream reviewers can trace governance state through the same audit
boundary as other audited artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from ..config import InstanceRoot
from ..schemas import (
    AppraiserSeparationPolicy,
    EvidenceChainRecord,
    WeightedDecisionAlternative,
)


class LapidaryGovernanceAuditWriter:
    """Append Lapidary governance records under ``data/audit/<YYYYMMDD>/lapidary-governance/``.

    Records are written as one JSON file per record, partitioned by kind so that
    governance trace traversal stays stable and the JSON round-trips through the
    originating schema.
    """

    _SUBDIRS: ClassVar[dict[type[BaseModel], str]] = {
        EvidenceChainRecord: "evidence-chains",
        WeightedDecisionAlternative: "weighted-alternatives",
        AppraiserSeparationPolicy: "appraiser-policies",
    }

    _ID_FIELDS: ClassVar[dict[type[BaseModel], str]] = {
        EvidenceChainRecord: "chain_id",
        WeightedDecisionAlternative: "alternative_id",
        AppraiserSeparationPolicy: "policy_id",
    }

    def __init__(self, instance: InstanceRoot) -> None:
        self.instance = instance

    def root_dir(self, yyyymmdd: str) -> Path:
        return self.instance.audit_dir(yyyymmdd) / "lapidary-governance"

    def append(self, record: BaseModel, *, yyyymmdd: str) -> Path:
        for kind, subdir in self._SUBDIRS.items():
            if isinstance(record, kind):
                directory = self.root_dir(yyyymmdd) / subdir
                directory.mkdir(parents=True, exist_ok=True)
                record_id = getattr(record, self._ID_FIELDS[kind])
                path = directory / f"{record_id}.json"
                payload = record.model_dump(mode="json", round_trip=True)
                path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
                return path
        raise TypeError(
            f"unsupported Lapidary governance record: {type(record).__name__}"
        )


__all__ = ["LapidaryGovernanceAuditWriter"]
