"""Backup/restore hardening tests for runtime-local generated knowledge outputs.

Traceability: HISYS-T-023, HISYS-FR-ADM-003, HISYS-DATA-001..004.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.operations.backup import create_backup, restore_backup_dry_run


def test_create_backup_writes_archive_and_manifest_with_hashes(tmp_path: Path) -> None:
    instance = tmp_path / "instance"
    (instance / "config").mkdir(parents=True)
    (instance / "config" / "source-registry.yaml").write_text("sources: []\n", encoding="utf-8")
    (instance / "data" / "memo-drafts" / "20260508").mkdir(parents=True)
    (instance / "data" / "memo-drafts" / "20260508" / "MEM-001.json").write_text(
        '{"memo_id":"MEM-001"}\n', encoding="utf-8"
    )
    (instance / "secrets").mkdir()
    excluded_secret = "password" + "=" + "do-not-back-up"
    (instance / "secrets" / "local-only.env").write_text(excluded_secret + "\n", encoding="utf-8")

    report = create_backup(instance, backup_dir=tmp_path / "backups", backup_id="BKP-TEST-001")

    assert report.backup_id == "BKP-TEST-001"
    assert report.archive_path.endswith("BKP-TEST-001.zip")
    assert report.manifest_path.endswith("BKP-TEST-001-manifest.json")
    assert report.file_count == 2
    assert sorted(item.relative_path for item in report.files) == [
        "config/source-registry.yaml",
        "data/memo-drafts/20260508/MEM-001.json",
    ]
    assert all(item.sha256 for item in report.files)
    manifest = json.loads(Path(report.manifest_path).read_text(encoding="utf-8"))
    assert manifest["backup_id"] == "BKP-TEST-001"
    assert "do-not-back-up" not in json.dumps(manifest)


def test_restore_backup_dry_run_verifies_manifest_without_writing_files(tmp_path: Path) -> None:
    instance = tmp_path / "instance"
    (instance / "reports" / "run-summaries" / "20260508").mkdir(parents=True)
    (instance / "reports" / "run-summaries" / "20260508" / "collection-report.json").write_text(
        '{"ok":true}\n', encoding="utf-8"
    )
    backup = create_backup(instance, backup_dir=tmp_path / "backups", backup_id="BKP-TEST-RESTORE")
    restore_target = tmp_path / "restore-target"

    dry_run = restore_backup_dry_run(backup.archive_path, restore_target)

    assert dry_run.backup_id == "BKP-TEST-RESTORE"
    assert dry_run.verified is True
    assert dry_run.would_restore_count == 1
    assert dry_run.would_restore_paths == ["reports/run-summaries/20260508/collection-report.json"]
    assert not restore_target.exists()
