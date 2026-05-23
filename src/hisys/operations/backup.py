"""Runtime-local backup manifest and restore dry-run support.

Traceability: HISYS-T-023, HISYS-FR-ADM-003, HISYS-DATA-001..004.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

INCLUDED_TOP_LEVEL_DIRS = {"config", "templates", "harness", "data", "runtime-boundary", "reports"}
EXCLUDED_DIR_NAMES = {"secrets", "tmp", "cache", "logs", "backups", "__pycache__", ".pytest_cache", ".git"}
MANIFEST_NAME = "hisys-backup-manifest.json"


class BackupFileRecord(BaseModel):
    """One file included in a Hisys runtime backup."""

    relative_path: str
    size_bytes: int = Field(ge=0)
    sha256: str


class BackupReport(BaseModel):
    """Backup artifact and manifest summary."""

    backup_id: str
    archive_path: str
    manifest_path: str
    file_count: int = Field(ge=0)
    files: list[BackupFileRecord]
    excluded_dirs: list[str]


class RestoreDryRunReport(BaseModel):
    """Verification-only restore report; it does not write to the target root."""

    backup_id: str
    archive_path: str
    restore_target: str
    verified: bool
    would_restore_count: int = Field(ge=0)
    would_restore_paths: list[str]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_stream(handle) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _included_files(instance_root: Path) -> Iterable[Path]:
    for top_level in sorted(INCLUDED_TOP_LEVEL_DIRS):
        root = instance_root / top_level
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if any(part in EXCLUDED_DIR_NAMES for part in path.relative_to(instance_root).parts):
                continue
            if path.is_file():
                yield path


def create_backup(instance_root: str | Path, *, backup_dir: str | Path, backup_id: str) -> BackupReport:
    """Create a zip backup for controlled runtime files and a JSON manifest.

    Local-only secret/cache/tmp/log directories are intentionally excluded from
    this baseline backup artifact.
    """

    instance = Path(instance_root).resolve()
    destination = Path(backup_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    files = [
        BackupFileRecord(
            relative_path=str(path.relative_to(instance)),
            size_bytes=path.stat().st_size,
            sha256=_sha256_file(path),
        )
        for path in _included_files(instance)
    ]
    manifest = BackupReport(
        backup_id=backup_id,
        archive_path=str(destination / f"{backup_id}.zip"),
        manifest_path=str(destination / f"{backup_id}-manifest.json"),
        file_count=len(files),
        files=files,
        excluded_dirs=sorted(EXCLUDED_DIR_NAMES),
    )
    manifest_path = Path(manifest.manifest_path)
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    with zipfile.ZipFile(manifest.archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, manifest.model_dump_json(indent=2))
        for record in files:
            archive.write(instance / record.relative_path, arcname=record.relative_path)
    return manifest


def restore_backup_dry_run(archive_path: str | Path, restore_target: str | Path) -> RestoreDryRunReport:
    """Verify a backup archive and report what would be restored.

    This dry-run function reads and hashes archive members, but deliberately does
    not extract anything into the target root.
    """

    archive_file = Path(archive_path).resolve()
    with zipfile.ZipFile(archive_file, "r") as archive:
        manifest = BackupReport.model_validate_json(archive.read(MANIFEST_NAME).decode("utf-8"))
        member_names = set(archive.namelist())
        for record in manifest.files:
            if record.relative_path not in member_names:
                raise ValueError(f"missing backup member: {record.relative_path}")
            with archive.open(record.relative_path, "r") as member:
                digest = _sha256_stream(member)
            if digest != record.sha256:
                raise ValueError(f"hash mismatch for backup member: {record.relative_path}")
    paths = sorted(record.relative_path for record in manifest.files)
    return RestoreDryRunReport(
        backup_id=manifest.backup_id,
        archive_path=str(archive_file),
        restore_target=str(Path(restore_target).resolve()),
        verified=True,
        would_restore_count=len(paths),
        would_restore_paths=paths,
    )


__all__ = [
    "BackupFileRecord",
    "BackupReport",
    "RestoreDryRunReport",
    "create_backup",
    "restore_backup_dry_run",
]
