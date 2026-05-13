"""Tests for governed Hisys evidence store and Stone promotion.

Traceability: Evidence-Store-A, HISYS-FR-INV-001..006, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.evidence_store import (
    build_stone_candidates,
    init_evidence_store,
    load_evidence_store_config,
    promote_stone_candidate,
)


def test_evidence_store_init_writes_config_registry_and_gitignore(tmp_path: Path) -> None:
    store_root = tmp_path / "hisys-evidence-store"
    config_path = tmp_path / "store.yaml"

    report = init_evidence_store(config_path=config_path, root=store_root, store_id="test-store")

    assert report["schema_id"] == "hisys.evidence_store.init_report"
    assert report["mutation_performed"] is True
    assert report["root"] == str(store_root)
    assert config_path.exists()
    assert (store_root / "README.md").exists()
    assert (store_root / "registry.json").exists()
    assert (store_root / ".gitignore").exists()
    assert "raw/" in (store_root / ".gitignore").read_text(encoding="utf-8")

    loaded = load_evidence_store_config(config_path)
    assert loaded.root == store_root
    assert loaded.allow_personal_vault_write is False
    assert loaded.require_approval_for_write is True


def test_evidence_store_status_blocks_personal_me_vault(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "store.yaml"
    config_path.write_text(
        """
schema_version: '0.1.0'
store_id: unsafe
root: /home/cbchoi/me
allow_personal_vault_write: false
require_approval_for_write: true
""".strip(),
        encoding="utf-8",
    )

    result = main(["evidence-store-status", "--config", str(config_path), "--format", "json"])

    assert result == 1
    report = json.loads(capsys.readouterr().out)
    assert report["safe_to_write"] is False
    assert "personal_vault_blocked" in report["issues"]
    assert report["mutation_performed"] is False


def test_import_investigation_requires_approval_and_copies_to_topic_layout(tmp_path: Path, capsys) -> None:
    store_root = tmp_path / "store"
    config_path = tmp_path / "store.yaml"
    init_evidence_store(config_path=config_path, root=store_root, store_id="test-store")
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    request = source_dir / "domain-request.json"
    request.write_text('{"request_id":"REQ-001"}\n', encoding="utf-8")
    report = source_dir / "idea-ranking-report.md"
    report.write_text("# Ranking\n", encoding="utf-8")

    blocked = main([
        "evidence-store-import-investigation",
        "--config", str(config_path),
        "--topic-id", "TOPIC-20260513-DAEJEON-AI-CAMP",
        "--topic-slug", "daejeon-ai-convergence-camp",
        "--investigation-id", "INV-20260513-001",
        "--date", "2026-05-13",
        "--include", str(request),
        "--include", str(report),
        "--write",
        "--format", "json",
    ])
    assert blocked == 1
    blocked_report = json.loads(capsys.readouterr().out)
    assert blocked_report["mutation_performed"] is False
    assert blocked_report["status"] == "blocked_requires_approval"

    result = main([
        "evidence-store-import-investigation",
        "--config", str(config_path),
        "--topic-id", "TOPIC-20260513-DAEJEON-AI-CAMP",
        "--topic-slug", "daejeon-ai-convergence-camp",
        "--investigation-id", "INV-20260513-001",
        "--date", "2026-05-13",
        "--include", str(request),
        "--include", str(report),
        "--approval-ref", "APPROVAL-HISYS-STORE-20260513-001",
        "--write",
        "--format", "json",
    ])

    assert result == 0
    import_report = json.loads(capsys.readouterr().out)
    assert import_report["mutation_performed"] is True
    assert import_report["copied_count"] == 2
    base = store_root / "topics" / "TOPIC-20260513-DAEJEON-AI-CAMP__daejeon-ai-convergence-camp" / "investigations" / "2026-05-13" / "INV-20260513-001"
    assert (base / "input" / "domain-request.json").exists()
    assert (base / "reports" / "idea-ranking-report.md").exists()
    assert (base / "investigation-manifest.json").exists()


def test_stone_candidates_and_promotion_are_approval_gated(tmp_path: Path) -> None:
    store_root = tmp_path / "store"
    config_path = tmp_path / "store.yaml"
    init_evidence_store(config_path=config_path, root=store_root, store_id="test-store")
    topic_id = "TOPIC-20260513-DAEJEON-AI-CAMP"
    topic_slug = "daejeon-ai-convergence-camp"
    investigation_id = "INV-20260513-001"
    base = store_root / "topics" / f"{topic_id}__{topic_slug}" / "investigations" / "2026-05-13" / investigation_id
    source_dir = base / "sources" / "extracted-text"
    source_dir.mkdir(parents=True)
    source = source_dir / "plan.txt"
    source.write_text("AI 융합 수학·과학 캠프 운영 계획\n파이썬 데이터 시각화\n", encoding="utf-8")

    candidates = build_stone_candidates(
        config_path=config_path,
        topic_id=topic_id,
        topic_slug=topic_slug,
        investigation_id=investigation_id,
    )

    assert candidates["candidate_count"] == 1
    candidate = candidates["stone_candidates"][0]
    assert candidate["recommended_stone_type"] == "program_plan_source"
    assert candidate["mutation_performed"] is False

    blocked = promote_stone_candidate(config_path=config_path, candidate=candidate, write=True, approval_ref=None)
    assert blocked["status"] == "blocked_requires_approval"
    assert blocked["mutation_performed"] is False

    promoted = promote_stone_candidate(
        config_path=config_path,
        candidate=candidate,
        write=True,
        approval_ref="APPROVAL-HISYS-STONE-20260513-001",
    )

    assert promoted["status"] == "promoted"
    assert promoted["mutation_performed"] is True
    stone_path = store_root / promoted["stone_ref"]
    assert stone_path.exists()
    text = stone_path.read_text(encoding="utf-8")
    assert "type: hisys/stone" in text
    assert "evidence_store_ref:" in text
    assert "AI 융합 수학·과학 캠프" in text
