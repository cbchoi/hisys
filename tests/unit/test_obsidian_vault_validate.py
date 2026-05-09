"""Tests for Live-Obsidian-Config-C vault manifest validation.

Traceability: Live-Obsidian-Config-A/C, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import validate_vault_manifests


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "obsidian-live"


def test_validate_vault_manifests_accepts_scaffold_examples() -> None:
    report = validate_vault_manifests(
        registry_path=EXAMPLES / "registry.json",
        topic_manifest_path=EXAMPLES / "topic-manifest.json",
        investigation_manifest_path=EXAMPLES / "investigation-manifest.json",
        gatekeeper_decision_path=EXAMPLES / "gatekeeper-decision.json",
    )

    assert report["schema_id"] == "hisys.obsidian.vault_validation_report"
    assert report["valid"] is True
    assert report["error_count"] == 0
    assert report["checked_files"] == 4
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    assert report["vault_write_attempted"] is False


def test_validate_vault_manifests_rejects_gatekeeper_score_without_evidence_refs(tmp_path: Path) -> None:
    bad_gatekeeper = json.loads((EXAMPLES / "gatekeeper-decision.json").read_text(encoding="utf-8"))
    bad_gatekeeper["scores"]["semantic_similarity"]["evidence_refs"] = []
    bad_path = tmp_path / "bad-gatekeeper-decision.json"
    bad_path.write_text(json.dumps(bad_gatekeeper, ensure_ascii=False, indent=2), encoding="utf-8")

    report = validate_vault_manifests(
        registry_path=EXAMPLES / "registry.json",
        topic_manifest_path=EXAMPLES / "topic-manifest.json",
        investigation_manifest_path=EXAMPLES / "investigation-manifest.json",
        gatekeeper_decision_path=bad_path,
    )

    assert report["valid"] is False
    assert any(issue["code"] == "gatekeeper_score_missing_evidence_refs" for issue in report["issues"])


def test_validate_vault_manifests_rejects_merge_without_human_approval(tmp_path: Path) -> None:
    bad_gatekeeper = json.loads((EXAMPLES / "gatekeeper-decision.json").read_text(encoding="utf-8"))
    bad_gatekeeper["decision"]["action"] = "merge_with_existing_topic"
    bad_gatekeeper["decision"]["requires_human_approval"] = True
    bad_gatekeeper["decision"]["approval_ref"] = None
    bad_path = tmp_path / "bad-merge-decision.json"
    bad_path.write_text(json.dumps(bad_gatekeeper, ensure_ascii=False, indent=2), encoding="utf-8")

    report = validate_vault_manifests(
        registry_path=EXAMPLES / "registry.json",
        topic_manifest_path=EXAMPLES / "topic-manifest.json",
        investigation_manifest_path=EXAMPLES / "investigation-manifest.json",
        gatekeeper_decision_path=bad_path,
    )

    assert report["valid"] is False
    assert any(issue["code"] == "canonical_identity_mutation_missing_approval" for issue in report["issues"])


def test_vault_validate_cli_writes_report_and_returns_nonzero_for_invalid(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    bad_gatekeeper = json.loads((EXAMPLES / "gatekeeper-decision.json").read_text(encoding="utf-8"))
    bad_gatekeeper["scores"]["group_affinity"]["evidence_refs"] = []
    bad_path = tmp_path / "bad-gatekeeper.json"
    bad_path.write_text(json.dumps(bad_gatekeeper, ensure_ascii=False, indent=2), encoding="utf-8")

    result = main(
        [
            "vault-validate",
            "--instance",
            str(tmp_path),
            "--date",
            "20260509",
            "--registry",
            str(EXAMPLES / "registry.json"),
            "--topic-manifest",
            str(EXAMPLES / "topic-manifest.json"),
            "--investigation-manifest",
            str(EXAMPLES / "investigation-manifest.json"),
            "--gatekeeper-decision",
            str(bad_path),
        ]
    )

    out = capsys.readouterr().out
    assert result == 1
    assert "vault validation: invalid" in out
    report_path = tmp_path / "reports" / "run-summaries" / "20260509" / "vault-validation-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert report["vault_write_attempted"] is False
