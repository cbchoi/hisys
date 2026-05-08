"""Controlled Obsidian vault-write preview integration.

Traceability: HISYS-FR-MEM-001..005, HISYS-IF-007, HISYS-DATA-002,
HISYS-DATA-005, HISYS-CON-012.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..schemas import ZettelMemo

VaultWriteMode = Literal["dry_run"]


class VaultWritePreview(BaseModel):
    """Runtime-boundary record for a controlled Obsidian vault write preview."""

    memo_id: str
    mode: VaultWriteMode
    vault_root: str
    target_relative_path: str
    target_path: str
    markdown_preview: str
    report_path: str
    live_write_permitted: bool = False
    action_taken: str = "none"
    requirement_refs: list[str] = Field(
        default_factory=lambda: [
            "HISYS-FR-MEM-001",
            "HISYS-FR-MEM-002",
            "HISYS-FR-MEM-003",
            "HISYS-FR-MEM-004",
            "HISYS-FR-MEM-005",
            "HISYS-IF-007",
            "HISYS-DATA-002",
            "HISYS-DATA-005",
            "HISYS-CON-012",
        ]
    )


def build_vault_write_preview(
    *,
    memo: ZettelMemo,
    vault_root: str | Path,
    runtime_root: str | Path,
    yyyymmdd: str,
    folder: str = "Hisys/Memos",
    mode: VaultWriteMode = "dry_run",
) -> VaultWritePreview:
    """Build and persist a dry-run Obsidian vault-write preview.

    The function intentionally writes only a runtime-boundary preview report. It
    does not create or modify the target vault path.
    """

    if mode != "dry_run":
        raise ValueError("only dry_run vault-write previews are supported")
    vault_root_path = Path(vault_root)
    relative_path = _safe_relative_path(folder, _slug_filename(memo.title))
    markdown_preview = _memo_to_obsidian_markdown(memo)
    report_path = Path(runtime_root) / "runtime-boundary" / "obsidian" / yyyymmdd / f"vault-write-preview-{memo.memo_id}.md"
    preview = VaultWritePreview(
        memo_id=memo.memo_id,
        mode=mode,
        vault_root=str(vault_root_path),
        target_relative_path=relative_path,
        target_path=str(vault_root_path / relative_path),
        markdown_preview=markdown_preview,
        report_path=str(report_path),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_format_preview_report(preview), encoding="utf-8")
    return preview


def _safe_relative_path(folder: str, filename: str) -> str:
    folder_parts = [_sanitize_path_part(part) for part in folder.split("/") if part.strip()]
    return "/".join([*folder_parts, filename])


def _slug_filename(title: str) -> str:
    sanitized = re.sub(r"[^\w\s.-]+", "", title, flags=re.UNICODE)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    sanitized = sanitized.replace(":", "")
    if not sanitized:
        sanitized = "untitled-memo"
    return f"{sanitized}.md"


def _sanitize_path_part(part: str) -> str:
    cleaned = re.sub(r"[^\w\s.-]+", "", part, flags=re.UNICODE).strip(" .")
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError(f"unsafe vault path part: {part!r}")
    return cleaned


def _memo_to_obsidian_markdown(memo: ZettelMemo) -> str:
    frontmatter = [
        "---",
        f"memo_id: {memo.memo_id}",
        f"title: {memo.title}",
        f"perspective_id: {memo.perspective_id}",
        f"confidence: {memo.confidence}",
        f"review_status: {memo.review_status}",
        f"revision: {memo.revision}",
        "signal_refs:",
        *[f"  - {ref}" for ref in memo.signal_refs],
        "source_refs:",
        *[f"  - {ref}" for ref in memo.source_refs],
        "tags:",
        *[f"  - {_sanitize_tag(tag)}" for tag in memo.tags],
        "---",
        "",
    ]
    link_lines = [f"- [[{link}]]" for link in memo.links]
    return "\n".join(
        [
            *frontmatter,
            memo.body,
            "",
            "## Trace Links",
            *[f"- signal: `{ref}`" for ref in memo.signal_refs],
            *[f"- source: `{ref}`" for ref in memo.source_refs],
            "",
            "## Wikilinks",
            *link_lines,
            "",
        ]
    )


def _sanitize_tag(tag: str) -> str:
    return re.sub(r"\s+", "-", tag.strip())


def _format_preview_report(preview: VaultWritePreview) -> str:
    return "\n".join(
        [
            "# Obsidian Vault Write Preview",
            "",
            f"memo_id: `{preview.memo_id}`",
            f"mode: `{preview.mode}`",
            f"vault_root: `{preview.vault_root}`",
            f"target_relative_path: `{preview.target_relative_path}`",
            f"live_write_permitted: `{preview.live_write_permitted}`",
            f"action_taken: `{preview.action_taken}`",
            "",
            "## Requirement References",
            *[f"- {ref}" for ref in preview.requirement_refs],
            "",
            "## Markdown Preview",
            "",
            "```markdown",
            preview.markdown_preview,
            "```",
            "",
        ]
    )


__all__ = ["VaultWritePreview", "build_vault_write_preview"]
