"""Controlled Obsidian vault-writer dry-run tests.

Traceability: HISYS-FR-MEM-001..005, HISYS-IF-007, HISYS-DATA-002,
HISYS-DATA-005, HISYS-CON-012.
"""

from __future__ import annotations

from pathlib import Path

from hisys.integrations.obsidian_vault import build_vault_write_preview
from hisys.schemas import ZettelMemo


def _memo() -> ZettelMemo:
    return ZettelMemo(
        memo_id="MEM-VAULT-001",
        title="Pump anomaly: over-threshold temperature",
        summary="Pump A temperature is over threshold.",
        body="# Pump anomaly\n\nEvidence remains linked; raw payload is not copied.",
        source_refs=["SRC-PUMP-001"],
        signal_refs=["SIG-PUMP-001"],
        perspective_id="PERSP-OPS-001",
        confidence=0.82,
        tags=["hisys", "ops review", "temperature/anomaly"],
        links=["OBS-PUMP-001", "MEM-RELATED-001"],
        revision="2",
        review_status="draft",
        status="draft",
        producer_id="test-vault-writer",
    )


def test_build_vault_write_preview_sanitizes_path_frontmatter_and_does_not_write_live_vault(tmp_path: Path) -> None:
    vault_root = tmp_path / "live-vault"
    runtime_root = tmp_path / "runtime"
    preview = build_vault_write_preview(
        memo=_memo(),
        vault_root=vault_root,
        runtime_root=runtime_root,
        yyyymmdd="20260509",
        folder="Hisys/Memos",
        mode="dry_run",
    )

    assert preview.mode == "dry_run"
    assert preview.live_write_permitted is False
    assert preview.action_taken == "none"
    assert preview.target_relative_path == "Hisys/Memos/Pump anomaly over-threshold temperature.md"
    assert preview.target_path == str(vault_root / "Hisys" / "Memos" / "Pump anomaly over-threshold temperature.md")
    assert not (vault_root / "Hisys").exists()
    assert "memo_id: MEM-VAULT-001" in preview.markdown_preview
    assert "review_status: draft" in preview.markdown_preview
    assert "signal_refs:" in preview.markdown_preview
    assert "[[MEM-RELATED-001]]" in preview.markdown_preview
    assert "temperature/anomaly" not in preview.target_relative_path


def test_vault_write_preview_persists_runtime_boundary_report_only(tmp_path: Path) -> None:
    preview = build_vault_write_preview(
        memo=_memo(),
        vault_root=tmp_path / "vault",
        runtime_root=tmp_path / "runtime",
        yyyymmdd="20260509",
        folder="Hisys/Memos",
        mode="dry_run",
    )

    report_path = Path(preview.report_path)
    assert report_path == tmp_path / "runtime" / "runtime-boundary" / "obsidian" / "20260509" / "vault-write-preview-MEM-VAULT-001.md"
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "# Obsidian Vault Write Preview" in report
    assert "live_write_permitted: `False`" in report
    assert "action_taken: `none`" in report
    assert "HISYS-IF-007" in report
