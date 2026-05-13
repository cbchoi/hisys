"""Governed file-backed evidence store and Stone promotion helpers.

Traceability: Evidence-Store-A, HISYS-FR-INV-001..006, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

_PERSONAL_VAULT_ROOTS = {Path("/home/cbchoi/me").resolve()}
_DEFAULT_GITIGNORE = """# Hisys evidence store: keep raw/heavy blobs out of Git by default.
raw/
blobs/
attachments/blobs/
downloads/
cache/
*.pdf
*.html
*.png
*.jpg
*.jpeg
*.webp
*.mp4
*.zip
"""


@dataclass(frozen=True)
class EvidenceStoreConfig:
    schema_version: str
    store_id: str
    root: Path
    layout: str = "topic_first"
    git_enabled: bool = True
    auto_commit: bool = False
    auto_push: bool = False
    require_clean_before_write: bool = True
    allow_personal_vault_write: bool = False
    require_approval_for_write: bool = True
    personal_vault_projection_enabled: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug or "untitled"


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("evidence store config must be a mapping")
    return data


def _config_payload(root: Path, store_id: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "store_id": store_id,
        "root": str(root),
        "layout": "topic_first",
        "git": {
            "enabled": True,
            "auto_commit": False,
            "auto_push": False,
            "require_clean_before_write": True,
        },
        "safety": {
            "allow_personal_vault_write": False,
            "require_approval_for_write": True,
        },
        "personal_vault_projection": {"enabled": False},
    }


def load_evidence_store_config(config_path: str | Path) -> EvidenceStoreConfig:
    path = Path(config_path)
    data = _read_yaml(path)
    git = data.get("git") or {}
    safety = data.get("safety") or {}
    projection = data.get("personal_vault_projection") or {}
    return EvidenceStoreConfig(
        schema_version=str(data.get("schema_version", "0.1.0")),
        store_id=str(data.get("store_id", "hisys-evidence-store")),
        root=Path(data["root"]).expanduser().resolve(),
        layout=str(data.get("layout", "topic_first")),
        git_enabled=bool(git.get("enabled", True)),
        auto_commit=bool(git.get("auto_commit", False)),
        auto_push=bool(git.get("auto_push", False)),
        require_clean_before_write=bool(git.get("require_clean_before_write", True)),
        allow_personal_vault_write=bool(
            data.get("allow_personal_vault_write", safety.get("allow_personal_vault_write", False))
        ),
        require_approval_for_write=bool(
            data.get("require_approval_for_write", safety.get("require_approval_for_write", True))
        ),
        personal_vault_projection_enabled=bool(projection.get("enabled", False)),
    )


def evidence_store_status(config_path: str | Path) -> dict[str, Any]:
    config = load_evidence_store_config(config_path)
    issues: list[str] = []
    root = config.root.resolve()
    if any(root == blocked or blocked in root.parents for blocked in _PERSONAL_VAULT_ROOTS):
        if not config.allow_personal_vault_write:
            issues.append("personal_vault_blocked")
    if config.auto_push:
        issues.append("auto_push_not_allowed")
    if config.personal_vault_projection_enabled:
        issues.append("personal_vault_projection_enabled_requires_separate_gate")
    return {
        "schema_id": "hisys.evidence_store.status_report",
        "generated_at": _now(),
        "config_path": str(Path(config_path)),
        "store_id": config.store_id,
        "root": str(root),
        "root_exists": root.exists(),
        "registry_exists": (root / "registry.json").exists(),
        "safe_to_write": not issues,
        "issues": issues,
        "mutation_performed": False,
    }


def init_evidence_store(*, config_path: str | Path, root: str | Path, store_id: str = "hisys-evidence-store") -> dict[str, Any]:
    config_file = Path(config_path)
    root_path = Path(root).expanduser().resolve()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    root_path.mkdir(parents=True, exist_ok=True)
    payload = _config_payload(root_path, store_id)
    config_file.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    registry = {
        "schema_id": "hisys.evidence_store.registry",
        "store_id": store_id,
        "created_at": _now(),
        "topics": [],
        "personal_vault_projection_enabled": False,
    }
    (root_path / "registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root_path / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")
    (root_path / "README.md").write_text(
        f"# {store_id}\n\nGoverned Hisys evidence store. Raw evidence stays here; personal vault projection is disabled by default.\n",
        encoding="utf-8",
    )
    (root_path / "topics").mkdir(exist_ok=True)
    return {
        "schema_id": "hisys.evidence_store.init_report",
        "generated_at": _now(),
        "config_path": str(config_file),
        "root": str(root_path),
        "store_id": store_id,
        "mutation_performed": True,
    }


def _topic_root(config: EvidenceStoreConfig, topic_id: str, topic_slug: str) -> Path:
    return config.root / "topics" / f"{_safe_slug(topic_id)}__{_safe_slug(topic_slug)}"


def _investigation_root(config: EvidenceStoreConfig, topic_id: str, topic_slug: str, date: str, investigation_id: str) -> Path:
    return _topic_root(config, topic_id, topic_slug) / "investigations" / date / _safe_slug(investigation_id)


def _category_for(path: Path) -> str:
    name = path.name.lower()
    if "request" in name or name.endswith("domain-request.json"):
        return "input"
    if name.endswith(".md") and ("report" in name or "ranking" in name):
        return "reports"
    if name.endswith(".txt"):
        return "sources/extracted-text"
    if name.endswith(".json") and ("result" in name or "runtime" in str(path).lower()):
        return "runtime-boundary"
    if name.endswith(".pdf"):
        return "sources/pdfs"
    return "sources"


def import_investigation_artifacts(
    *,
    config_path: str | Path,
    topic_id: str,
    topic_slug: str,
    investigation_id: str,
    date: str,
    includes: Iterable[str | Path],
    write: bool = False,
    approval_ref: str | None = None,
) -> dict[str, Any]:
    status = evidence_store_status(config_path)
    config = load_evidence_store_config(config_path)
    if not status["safe_to_write"]:
        return {**status, "schema_id": "hisys.evidence_store.import_report", "status": "blocked_unsafe_store"}
    include_paths = [Path(p).expanduser().resolve() for p in includes]
    missing = [str(p) for p in include_paths if not p.exists()]
    if missing:
        return {
            "schema_id": "hisys.evidence_store.import_report",
            "status": "blocked_missing_sources",
            "missing_sources": missing,
            "mutation_performed": False,
        }
    if config.require_approval_for_write and write and not approval_ref:
        return {
            "schema_id": "hisys.evidence_store.import_report",
            "status": "blocked_requires_approval",
            "required_approval": "approval_ref",
            "mutation_performed": False,
            "planned_copy_count": len(include_paths),
        }
    root = _investigation_root(config, topic_id, topic_slug, date, investigation_id)
    planned: list[dict[str, str]] = []
    copied: list[str] = []
    for source in include_paths:
        target = root / _category_for(source) / source.name
        planned.append({"source": str(source), "target_ref": target.relative_to(config.root).as_posix()})
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target.relative_to(config.root).as_posix())
    manifest_ref = None
    if write:
        manifest = {
            "schema_id": "hisys.evidence_store.investigation_manifest",
            "topic_id": topic_id,
            "topic_slug": topic_slug,
            "investigation_id": investigation_id,
            "date": date,
            "approval_ref": approval_ref,
            "artifact_refs": copied,
            "created_at": _now(),
        }
        manifest_path = root / "investigation-manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest_ref = manifest_path.relative_to(config.root).as_posix()
    return {
        "schema_id": "hisys.evidence_store.import_report",
        "status": "imported" if write else "planned",
        "store_root": str(config.root),
        "topic_id": topic_id,
        "investigation_id": investigation_id,
        "planned_copies": planned,
        "copied_count": len(copied),
        "copied_refs": copied,
        "manifest_ref": manifest_ref,
        "approval_ref": approval_ref,
        "mutation_performed": write,
    }


def _candidate_type(path: Path, text: str) -> tuple[str, str, str] | None:
    lower = f"{path.name}\n{text}".lower()
    if any(term in text for term in ["운영 계획", "캠프", "AI 융합", "수학·과학"]):
        return ("program_plan_source", "high", "program plan evidence reusable for proposal and curriculum design")
    if any(term in lower for term in ["doi", "arxiv", "journal", "conference", "논문", "학술"]):
        return ("academic_source", "high", "academic evidence reusable for literature-backed claims")
    if any(term in text for term in ["교육청", "정책", "공고", "지원계획"]):
        return ("policy_source", "high", "official/policy context reusable for planning claims")
    return None


def build_stone_candidates(
    *,
    config_path: str | Path,
    topic_id: str,
    topic_slug: str,
    investigation_id: str,
) -> dict[str, Any]:
    config = load_evidence_store_config(config_path)
    topic_root = _topic_root(config, topic_id, topic_slug)
    candidates: list[dict[str, Any]] = []
    for path in sorted(topic_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md"}:
            continue
        if f"/{investigation_id}/" not in path.as_posix():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        typed = _candidate_type(path, text)
        if not typed:
            continue
        stone_type, reuse_potential, reason = typed
        candidate_id = f"STONE-CAND-{len(candidates)+1:03d}"
        snippet = " ".join(line.strip() for line in text.splitlines() if line.strip())[:280]
        candidates.append(
            {
                "candidate_id": candidate_id,
                "topic_id": topic_id,
                "topic_slug": topic_slug,
                "investigation_id": investigation_id,
                "source_ref": _rel(path, config.root),
                "recommended_stone_type": stone_type,
                "reuse_potential": reuse_potential,
                "confidence": "medium",
                "reason": reason,
                "required_verification": ["source_checked", "human_promotion_approval"],
                "snippet": snippet,
                "mutation_performed": False,
            }
        )
    return {
        "schema_id": "hisys.evidence_store.stone_candidates",
        "generated_at": _now(),
        "store_root": str(config.root),
        "topic_id": topic_id,
        "investigation_id": investigation_id,
        "candidate_count": len(candidates),
        "stone_candidates": candidates,
        "mutation_performed": False,
    }


def _stone_markdown(config: EvidenceStoreConfig, candidate: dict[str, Any], approval_ref: str) -> str:
    source_ref = candidate["source_ref"]
    source_path = config.root / source_ref
    text = source_path.read_text(encoding="utf-8", errors="replace") if source_path.exists() else ""
    title = Path(source_ref).stem.replace("_", " ").replace("-", " ").strip().title()
    snippet = candidate.get("snippet") or " ".join(line.strip() for line in text.splitlines() if line.strip())[:280]
    return f"""---
type: hisys/stone
memo_type: stone
stone_id: {candidate['candidate_id'].replace('STONE-CAND', 'STONE')}
topic_uid: {candidate['topic_id']}
investigation_id: {candidate['investigation_id']}
title: "{title}"
source_type: {candidate['recommended_stone_type']}
evidence_store_ref: "{source_ref}"
source_access_date: {_now()[:10]}
reuse_potential: {candidate['reuse_potential']}
confidence: {candidate['confidence']}
verification_status: source_checked
approval_ref: {approval_ref}
personal_vault_projection: false
mutation_performed: true
tags:
  - hisys
  - stone
---

# {title}

## Source

- Evidence store ref: `{source_ref}`
- Investigation: `{candidate['investigation_id']}`
- Stone type: `{candidate['recommended_stone_type']}`

## Extracted fact

{snippet}

## Why this matters

{candidate['reason']}

## Candidate claims

- This source may support a future claim after human review and, if needed, additional corroboration.

## Limitations

- This Stone is a governed projection of evidence, not a final Gem/Jewel synthesis.
- Raw evidence remains in the Hisys evidence store; personal vault projection is disabled.
"""


def promote_stone_candidate(
    *,
    config_path: str | Path,
    candidate: dict[str, Any],
    write: bool = False,
    approval_ref: str | None = None,
) -> dict[str, Any]:
    config = load_evidence_store_config(config_path)
    if config.require_approval_for_write and write and not approval_ref:
        return {
            "schema_id": "hisys.evidence_store.stone_promotion_report",
            "status": "blocked_requires_approval",
            "required_approval": "approval_ref",
            "candidate_id": candidate.get("candidate_id"),
            "mutation_performed": False,
        }
    source_ref = candidate["source_ref"]
    base_slug = _safe_slug(Path(source_ref).stem)
    stone_id = candidate["candidate_id"].replace("STONE-CAND", "STONE")
    topic_dir = _topic_root(config, candidate["topic_id"], candidate["topic_slug"])
    stone_path = topic_dir / "canonical" / "stones" / f"{stone_id}__{base_slug}.md"
    if write:
        stone_path.parent.mkdir(parents=True, exist_ok=True)
        stone_path.write_text(_stone_markdown(config, candidate, approval_ref or ""), encoding="utf-8")
    return {
        "schema_id": "hisys.evidence_store.stone_promotion_report",
        "status": "promoted" if write else "planned",
        "candidate_id": candidate["candidate_id"],
        "stone_ref": stone_path.relative_to(config.root).as_posix(),
        "approval_ref": approval_ref,
        "mutation_performed": write,
    }


__all__ = [
    "EvidenceStoreConfig",
    "build_stone_candidates",
    "evidence_store_status",
    "import_investigation_artifacts",
    "init_evidence_store",
    "load_evidence_store_config",
    "promote_stone_candidate",
]
