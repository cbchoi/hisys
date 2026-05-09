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


def test_validate_vault_manifests_rejects_unknown_structured_link_relation(tmp_path: Path) -> None:
    bad_topic = json.loads((EXAMPLES / "topic-manifest.json").read_text(encoding="utf-8"))
    bad_topic["links"] = [{"relation": "made_up_relation", "ref": "canonical/claims/CLAIM-001.md"}]
    bad_path = tmp_path / "bad-topic-manifest.json"
    bad_path.write_text(json.dumps(bad_topic, ensure_ascii=False, indent=2), encoding="utf-8")

    report = validate_vault_manifests(
        registry_path=EXAMPLES / "registry.json",
        topic_manifest_path=bad_path,
        investigation_manifest_path=EXAMPLES / "investigation-manifest.json",
        gatekeeper_decision_path=EXAMPLES / "gatekeeper-decision.json",
    )

    assert report["valid"] is False
    assert any(issue["code"] == "unknown_link_relation" for issue in report["issues"])


def test_validate_vault_manifests_rejects_invalid_group_and_investigation_ids(tmp_path: Path) -> None:
    bad_registry = json.loads((EXAMPLES / "registry.json").read_text(encoding="utf-8"))
    bad_registry["groups"][0]["group_uid"] = "GROUP-not-valid"
    bad_registry_path = tmp_path / "bad-registry.json"
    bad_registry_path.write_text(json.dumps(bad_registry, ensure_ascii=False, indent=2), encoding="utf-8")

    bad_investigation = json.loads((EXAMPLES / "investigation-manifest.json").read_text(encoding="utf-8"))
    bad_investigation["investigation_id"] = "INV-not-valid"
    bad_investigation_path = tmp_path / "bad-investigation-manifest.json"
    bad_investigation_path.write_text(json.dumps(bad_investigation, ensure_ascii=False, indent=2), encoding="utf-8")

    report = validate_vault_manifests(
        registry_path=bad_registry_path,
        topic_manifest_path=EXAMPLES / "topic-manifest.json",
        investigation_manifest_path=bad_investigation_path,
        gatekeeper_decision_path=EXAMPLES / "gatekeeper-decision.json",
    )

    codes = {issue["code"] for issue in report["issues"]}
    assert "invalid_group_uid" in codes
    assert "invalid_investigation_id" in codes


def test_validate_vault_manifests_rejects_overlong_vault_relative_ref(tmp_path: Path) -> None:
    bad_topic = json.loads((EXAMPLES / "topic-manifest.json").read_text(encoding="utf-8"))
    bad_topic["canonical_indexes"]["sources"] = "canonical/sources/" + "x" * 260 + ".json"
    bad_path = tmp_path / "bad-topic-manifest.json"
    bad_path.write_text(json.dumps(bad_topic, ensure_ascii=False, indent=2), encoding="utf-8")

    report = validate_vault_manifests(
        registry_path=EXAMPLES / "registry.json",
        topic_manifest_path=bad_path,
        investigation_manifest_path=EXAMPLES / "investigation-manifest.json",
        gatekeeper_decision_path=EXAMPLES / "gatekeeper-decision.json",
    )

    assert report["valid"] is False
    assert any(issue["code"] == "overlong_vault_relative_ref" for issue in report["issues"])
