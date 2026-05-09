"""Fixture-only Obsidian live-research vault planning.

Traceability: Live-Obsidian-Config-A/B, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "0.1.0"
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")
_TOPIC_UID_RE = re.compile(r"^TOPIC-\d{8}-[A-Z0-9]{6}$")


def build_vault_plan(
    *,
    registry_path: Path,
    request_id: str,
    submitted_title: str,
    domain: str,
    objective: str,
    yyyymmdd: str,
    hhmm: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Build a dry-run vault plan from a registry without writing the vault."""

    if not dry_run:
        raise ValueError("Live-Obsidian-Config-B only supports dry_run=True")
    if ".." in submitted_title or "/" in submitted_title or "\\" in submitted_title:
        raise ValueError("unsafe topic title")
    if not re.fullmatch(r"\d{8}", yyyymmdd):
        raise ValueError("yyyymmdd must match YYYYMMDD")
    if not re.fullmatch(r"\d{4}", hhmm):
        raise ValueError("hhmm must match HHMM")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    existing = _find_existing_topic(registry, submitted_title, domain)
    date = f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"

    if existing:
        topic_uid = existing["topic_uid"]
        topic_slug = existing["topic_slug"]
        topic_path = existing["path"]
        action = "same_as_existing_topic"
        score_refs = ["registry.json#/topics/0", existing.get("manifest", "")]
        requires_human_approval = False
    else:
        topic_slug = _slugify(submitted_title)
        if not topic_slug:
            raise ValueError("unsafe topic title")
        topic_uid = f"TOPIC-{yyyymmdd}-VAULT1"
        topic_path = f"topics/{topic_uid}__{topic_slug}"
        action = "new_topic"
        score_refs = ["registry.json"]
        requires_human_approval = False

    if not _TOPIC_UID_RE.fullmatch(topic_uid):
        raise ValueError("invalid topic uid")
    investigation_id = f"INV-{yyyymmdd}-{hhmm}-VAULT"
    investigation_path = f"{topic_path}/investigations/{date}/{investigation_id}"

    planned_files = [
        "registry.json",
        "topics/INDEX.json",
        f"{topic_path}/index.md",
        f"{topic_path}/topic-config.yaml",
        f"{topic_path}/topic-manifest.json",
        f"{topic_path}/investigations/INDEX.json",
        f"{investigation_path}/index.md",
        f"{investigation_path}/investigation-config.yaml",
        f"{investigation_path}/investigation-manifest.json",
        f"{investigation_path}/input/request.md",
        f"{investigation_path}/input/request.json",
        f"{investigation_path}/runtime-boundary/runtime-index.json",
        f"{investigation_path}/attachments/attachment-index.json",
        f"{investigation_path}/reports/report-index.json",
    ]
    _validate_refs(planned_files)

    return {
        "schema_id": "hisys.obsidian.vault_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "submitted_topic": {
            "title": submitted_title,
            "domain": domain,
            "objective": objective,
        },
        "topic_uid": topic_uid,
        "topic_slug": topic_slug,
        "topic_path": topic_path,
        "investigation_id": investigation_id,
        "investigation_path": investigation_path,
        "planned_files": planned_files,
        "decision": {
            "action": action,
            "target_topic_uid": topic_uid if existing else None,
            "new_topic_uid": None if existing else topic_uid,
            "requires_human_approval": requires_human_approval,
            "scores": {
                "semantic_similarity": {
                    "value": 1.0 if existing else 0.0,
                    "evidence_refs": [ref for ref in score_refs if ref],
                },
                "governance_compatibility": {
                    "value": 1.0,
                    "evidence_refs": ["registry.json"],
                },
            },
        },
        "dry_run": True,
        "vault_write_attempted": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_vault_plan_artifacts(*, instance_root: Path, yyyymmdd: str, plan: dict[str, Any]) -> tuple[Path, Path]:
    """Persist a dry-run plan and summary under runtime-boundary/reports only."""

    plan_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"vault-plan-{plan['request_id']}.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_dir = instance_root / "reports" / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_id": "hisys.obsidian.vault_plan_report",
        "schema_version": _SCHEMA_VERSION,
        "request_id": plan["request_id"],
        "vault_plan_ref": str(plan_path.relative_to(instance_root)),
        "decision_action": plan["decision"]["action"],
        "planned_file_count": len(plan["planned_files"]),
        "dry_run": True,
        "vault_write_attempted": False,
        "external_call_made": False,
        "mutation_performed": False,
    }
    report_path = report_dir / "vault-plan-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / "vault-plan-report.md").write_text(_format_vault_plan_report(report), encoding="utf-8")
    return plan_path, report_path


def _find_existing_topic(registry: dict[str, Any], submitted_title: str, domain: str) -> dict[str, Any] | None:
    normalized = submitted_title.casefold().strip()
    for topic in registry.get("topics", []):
        candidates = [topic.get("title", ""), *topic.get("aliases", [])]
        if topic.get("domain") == domain and any(str(candidate).casefold().strip() == normalized for candidate in candidates):
            return topic
    return None


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    if not slug or not _SAFE_SLUG_RE.fullmatch(slug):
        return ""
    return slug[:80]


def _validate_refs(refs: list[str]) -> None:
    for ref in refs:
        path = Path(ref)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe vault-relative ref: {ref}")


def validate_vault_manifests(
    *,
    registry_path: Path,
    topic_manifest_path: Path,
    investigation_manifest_path: Path,
    gatekeeper_decision_path: Path,
) -> dict[str, Any]:
    """Validate Live-Obsidian fixture manifests without touching the vault."""

    files = [registry_path, topic_manifest_path, investigation_manifest_path, gatekeeper_decision_path]
    docs = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    registry, topic_manifest, investigation_manifest, gatekeeper = docs
    issues: list[dict[str, str]] = []

    for path, doc in zip(files, docs):
        if doc.get("schema_version") != _SCHEMA_VERSION:
            issues.append({"code": "unsupported_schema_version", "path": str(path), "message": "schema_version must be 0.1.0"})

    _check_ref(registry.get("topics_index_ref"), "registry.topics_index_ref", issues)
    _check_ref(registry.get("groups_index_ref"), "registry.groups_index_ref", issues)
    for topic in registry.get("topics", []):
        _check_topic_uid(topic.get("topic_uid"), "registry.topic_uid", issues)
        _check_slug(topic.get("topic_slug"), "registry.topic_slug", issues)
        _check_ref(topic.get("path"), "registry.topic.path", issues)
        _check_ref(topic.get("manifest"), "registry.topic.manifest", issues)

    _check_topic_uid(topic_manifest.get("topic_uid"), "topic_manifest.topic_uid", issues)
    _check_ref(topic_manifest.get("path"), "topic_manifest.path", issues)
    for ref in _flatten_refs(topic_manifest.get("canonical_indexes", {})):
        _check_ref(ref, "topic_manifest.canonical_indexes", issues)
    _check_ref(topic_manifest.get("investigations_index"), "topic_manifest.investigations_index", issues)

    paths = investigation_manifest.get("paths", {})
    for ref in _flatten_refs(paths):
        _check_ref(ref, "investigation_manifest.paths", issues)
    for ref in _flatten_refs(investigation_manifest.get("indexes", {})):
        _check_ref(ref, "investigation_manifest.indexes", issues)

    for score_name, score in gatekeeper.get("scores", {}).items():
        if score.get("value") is None:
            issues.append({"code": "gatekeeper_score_missing_value", "path": score_name, "message": "score requires value"})
        evidence_refs = score.get("evidence_refs") or []
        if not evidence_refs:
            issues.append({"code": "gatekeeper_score_missing_evidence_refs", "path": score_name, "message": "score requires evidence_refs"})
        for ref in evidence_refs:
            _check_ref(ref.split("#", 1)[0] or "registry.json", f"gatekeeper.scores.{score_name}.evidence_refs", issues)

    decision = gatekeeper.get("decision", {})
    action = decision.get("action")
    if action in {"merge_with_existing_topic", "split_topic_recommended"} and not decision.get("approval_ref"):
        issues.append(
            {
                "code": "canonical_identity_mutation_missing_approval",
                "path": "gatekeeper.decision.approval_ref",
                "message": f"{action} requires a human approval ref",
            }
        )

    return {
        "schema_id": "hisys.obsidian.vault_validation_report",
        "schema_version": _SCHEMA_VERSION,
        "valid": not issues,
        "error_count": len(issues),
        "issues": issues,
        "checked_files": len(files),
        "vault_write_attempted": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_vault_validation_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "reports" / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "vault-validation-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / "vault-validation-report.md").write_text(_format_vault_validation_report(report), encoding="utf-8")
    return report_path


def _check_ref(ref: object, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(ref, str) or not ref:
        issues.append({"code": "missing_ref", "path": path, "message": "ref is required"})
        return
    ref_path = Path(ref)
    if ref_path.is_absolute() or ".." in ref_path.parts:
        issues.append({"code": "unsafe_vault_relative_ref", "path": path, "message": ref})


def _check_topic_uid(uid: object, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(uid, str) or not _TOPIC_UID_RE.fullmatch(uid):
        issues.append({"code": "invalid_topic_uid", "path": path, "message": str(uid)})


def _check_slug(slug: object, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(slug, str) or not _SAFE_SLUG_RE.fullmatch(slug):
        issues.append({"code": "invalid_slug", "path": path, "message": str(slug)})


def _flatten_refs(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        refs: list[str] = []
        for child in value.values():
            refs.extend(_flatten_refs(child))
        return refs
    if isinstance(value, list):
        refs = []
        for child in value:
            refs.extend(_flatten_refs(child))
        return refs
    return []


def _format_vault_plan_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Vault Plan Report",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Plan ref: `{report['vault_plan_ref']}`",
            f"- Decision: `{report['decision_action']}`",
            f"- Planned files: {report['planned_file_count']}",
            "- dry_run: true",
            "- vault_write_attempted: false",
            "- external_call_made: false",
            "- mutation_performed: false",
            "",
        ]
    )


def _format_vault_validation_report(report: dict[str, Any]) -> str:
    status = "valid" if report["valid"] else "invalid"
    lines = [
        "# Obsidian Vault Validation Report",
        "",
        f"- Status: {status}",
        f"- Error count: {report['error_count']}",
        "- vault_write_attempted: false",
        "- external_call_made: false",
        "- mutation_performed: false",
        "",
    ]
    for issue in report.get("issues", []):
        lines.append(f"- {issue['code']} at `{issue['path']}`: {issue['message']}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "build_vault_plan",
    "validate_vault_manifests",
    "write_vault_plan_artifacts",
    "write_vault_validation_report",
]
