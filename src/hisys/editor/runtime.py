"""I6 editorial runtime.

Traceability: HISYS-FR-PER-001..004, HISYS-FR-MEM-001..005,
HISYS-DATA-002, HISYS-D-015, HISYS-T-011, HISYS-T-012.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from ..config import InstanceRoot
from ..schemas import ExtractedSignal, PerspectiveProfile, RawObservation, ZettelMemo


class MemoDrafter(Protocol):
    """Protocol for Associate Editor memo drafters."""

    def draft(
        self,
        signal: ExtractedSignal,
        *,
        perspective: PerspectiveProfile,
        observations: list[RawObservation],
    ) -> ZettelMemo:
        """Create one atomic memo draft from one signal."""


@dataclass(frozen=True)
class MemoDraftReport:
    """Machine-checkable I6 memo drafting report."""

    perspective_id: str
    perspective_state: str
    requested_signal_refs: list[str]
    draft_memo_refs: list[str] = field(default_factory=list)
    skipped_signal_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(
        default_factory=lambda: ["HISYS-FR-MEM-001", "HISYS-DATA-002"]
    )


class EditorialRuntime:
    """Persist local ZettelMemo draft artifacts under a runtime instance root."""

    def __init__(self, *, instance: InstanceRoot, drafter: MemoDrafter, producer_id: str) -> None:
        self.instance = instance
        self.drafter = drafter
        self.producer_id = producer_id

    def draft_run(
        self,
        signals: list[ExtractedSignal],
        *,
        observations: list[RawObservation],
        perspective: PerspectiveProfile,
        yyyymmdd: str,
    ) -> MemoDraftReport:
        if perspective.lifecycle_state != "active":
            return MemoDraftReport(
                perspective_id=perspective.perspective_id,
                perspective_state=perspective.lifecycle_state,
                requested_signal_refs=[signal.signal_id for signal in signals],
            )
        requested: list[str] = []
        memo_refs: list[str] = []
        skipped: list[str] = []
        for signal in signals:
            requested.append(signal.signal_id)
            matching_observations = [
                obs for obs in observations if obs.observation_id in set(signal.observation_refs)
            ]
            if not matching_observations:
                skipped.append(signal.signal_id)
                continue
            memo = self.drafter.draft(signal, perspective=perspective, observations=matching_observations)
            self._write_memo(memo, yyyymmdd)
            memo_refs.append(memo.memo_id)
        return MemoDraftReport(
            perspective_id=perspective.perspective_id,
            perspective_state=perspective.lifecycle_state,
            requested_signal_refs=requested,
            draft_memo_refs=memo_refs,
            skipped_signal_refs=skipped,
        )

    def _write_memo(self, memo: ZettelMemo, yyyymmdd: str) -> tuple[Path, Path]:
        directory = self.instance.root / "data" / "memo-drafts" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / f"{memo.memo_id}.json"
        markdown_path = directory / f"{memo.memo_id}.md"
        json_path.write_text(_to_json(memo), encoding="utf-8")
        markdown_path.write_text(_to_markdown(memo), encoding="utf-8")
        return json_path, markdown_path


def _to_json(record: BaseModel) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)


def _to_markdown(memo: ZettelMemo) -> str:
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


__all__ = ["EditorialRuntime", "MemoDrafter", "MemoDraftReport"]
