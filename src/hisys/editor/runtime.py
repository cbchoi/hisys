"""I6 editorial runtime.

Traceability: HISYS-FR-PER-001..004, HISYS-FR-MEM-001..005,
HISYS-DATA-002, HISYS-D-015, HISYS-T-011, HISYS-T-012, HISYS-T-013.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
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


@dataclass(frozen=True)
class MemoReviewReport:
    """Machine-checkable I6 duplicate/conflict review report."""

    reviewed_memo_refs: list[str]
    duplicate_memo_refs: list[str] = field(default_factory=list)
    conflict_memo_refs: list[str] = field(default_factory=list)
    clean_memo_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=lambda: ["HISYS-FR-MEM-004", "HISYS-T-013"])


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


class MemoReviewRuntime:
    """Fixture duplicate/conflict reviewer for runtime-local memo drafts."""

    def __init__(self, *, instance: InstanceRoot, producer_id: str) -> None:
        self.instance = instance
        self.producer_id = producer_id

    def review_run(self, memos: list[ZettelMemo], *, yyyymmdd: str) -> MemoReviewReport:
        reviewed = [memo.memo_id for memo in memos]
        duplicate_refs = _detect_duplicate_refs(memos)
        conflict_refs = _detect_conflict_refs(memos, duplicate_refs)
        clean_refs = [
            memo.memo_id
            for memo in memos
            if memo.memo_id not in set(duplicate_refs) | set(conflict_refs)
        ]
        for memo in memos:
            if memo.memo_id in duplicate_refs:
                memo.review_status = "flagged_duplicate"
                memo.status = "flagged_duplicate"
            elif memo.memo_id in conflict_refs:
                memo.review_status = "flagged_conflict"
                memo.status = "flagged_conflict"
            self._write_reviewed_memo(memo, yyyymmdd)
        report = MemoReviewReport(
            reviewed_memo_refs=reviewed,
            duplicate_memo_refs=duplicate_refs,
            conflict_memo_refs=conflict_refs,
            clean_memo_refs=clean_refs,
        )
        self._write_report(report, yyyymmdd)
        return report

    def _write_reviewed_memo(self, memo: ZettelMemo, yyyymmdd: str) -> None:
        directory = self.instance.root / "data" / "memo-drafts" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{memo.memo_id}.json").write_text(_to_json(memo), encoding="utf-8")
        (directory / f"{memo.memo_id}.md").write_text(_to_markdown(memo), encoding="utf-8")

    def _write_report(self, report: MemoReviewReport, yyyymmdd: str) -> Path:
        directory = self.instance.root / "reports" / "run-summaries" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "memo-review-report.json"
        path.write_text(json.dumps(_dataclass_to_dict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path = directory / "memo-review-report.md"
        markdown_path.write_text(_format_review_report(report), encoding="utf-8")
        return path

def _to_json(record: BaseModel) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)


def _detect_duplicate_refs(memos: list[ZettelMemo]) -> list[str]:
    groups: dict[tuple[str, str], list[str]] = {}
    for memo in memos:
        key = (memo.perspective_id, _normalize(memo.summary))
        groups.setdefault(key, []).append(memo.memo_id)
    return sorted(ref for refs in groups.values() if len(refs) > 1 for ref in refs)


def _detect_conflict_refs(memos: list[ZettelMemo], excluded_refs: list[str]) -> list[str]:
    excluded = set(excluded_refs)
    conflicts: set[str] = set()
    for idx, left in enumerate(memos):
        if left.memo_id in excluded:
            continue
        for right in memos[idx + 1 :]:
            if right.memo_id in excluded:
                continue
            if set(left.source_refs).isdisjoint(right.source_refs):
                continue
            if _has_fixture_conflict(left.summary, right.summary):
                conflicts.update([left.memo_id, right.memo_id])
    return sorted(conflicts)


def _has_fixture_conflict(left: str, right: str) -> bool:
    left_norm = _normalize(left)
    right_norm = _normalize(right)
    high_tokens = {"high", "over_threshold", "anomaly"}
    normal_tokens = {"normal", "nominal", "within_threshold"}
    return (
        any(token in left_norm for token in high_tokens)
        and any(token in right_norm for token in normal_tokens)
    ) or (
        any(token in right_norm for token in high_tokens)
        and any(token in left_norm for token in normal_tokens)
    )


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _dataclass_to_dict(report: MemoReviewReport) -> dict[str, object]:
    return asdict(report)


def _format_review_report(report: MemoReviewReport) -> str:
    return "\n".join(
        [
            "# Hisys Memo Review Report",
            "",
            f"- reviewed_memos: {len(report.reviewed_memo_refs)}",
            f"- duplicate_memos: {len(report.duplicate_memo_refs)}",
            f"- conflict_memos: {len(report.conflict_memo_refs)}",
            f"- clean_memos: {len(report.clean_memo_refs)}",
            "",
            "## Duplicates",
            *[f"- {ref}" for ref in report.duplicate_memo_refs],
            "",
            "## Conflicts",
            *[f"- {ref}" for ref in report.conflict_memo_refs],
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


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


__all__ = ["EditorialRuntime", "MemoDrafter", "MemoDraftReport", "MemoReviewReport", "MemoReviewRuntime"]
