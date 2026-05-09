"""Fixture-only Obsidian live-research vault planning.

Traceability: Live-Obsidian-Config-A/B, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "0.1.0"
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")
_TOPIC_UID_RE = re.compile(r"^TOPIC-\d{8}-[A-Z0-9]{6}$")
_GROUP_UID_RE = re.compile(r"^GROUP-\d{8}-[A-Z0-9]{6}$")
_INVESTIGATION_ID_RE = re.compile(r"^INV-\d{8}-\d{4}-[A-Z0-9]{4}$")
_MAX_VAULT_REF_LENGTH = 240
_ALLOWED_LINK_RELATIONS = frozenset(
    {
        "belongs_to_group",
        "belongs_to_topic",
        "part_of_investigation",
        "derived_from_source",
        "has_attachment",
        "quotes_source",
        "supports_claim",
        "contradicts_claim",
        "needs_evidence_for_claim",
        "summarizes_ledgers",
        "gates_claims",
        "feeds_live_k_coverage_gate",
        "reviewed_by_dars",
        "reviewed_by_chief_editor",
        "decided_by_gatekeeper",
        "merged_into",
        "merged_from",
        "split_into",
        "split_from",
        "related_topics",
        "promoted_from_investigation",
        "tombstoned_by",
    }
)


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


def build_vault_template_plan(*, request_id: str) -> dict[str, Any]:
    """Build the controlled memo ontology/template plan without writing the vault."""

    frontmatter_fields = ["type", "schema_version", "uid", "topic_uid", "investigation_id", "phase", "governance", "links", "tags"]
    entity_types = [
        "hisys/topic-group",
        "hisys/topic",
        "hisys/investigation",
        "hisys/source",
        "hisys/attachment",
        "hisys/evidence",
        "hisys/quote",
        "hisys/claim",
        "hisys/recommendation-claim-registry",
        "hisys/claim-evidence-ledger",
        "hisys/claim-evidence-summary",
        "hisys/claim-coverage-gate",
        "hisys/synthesis",
        "hisys/decision",
        "hisys/gatekeeper-decision",
        "hisys/report",
    ]
    templates = [
        {
            "template_id": entity_type.replace("hisys/", "template-"),
            "type": entity_type,
            "phase_policy": "phase is structured metadata, not a tag",
            "frontmatter_fields": frontmatter_fields,
            "default_tags": ["hisys/live-research"],
            "link_policy": "structured_links_primary_wikilinks_projection_only",
            "planned_ref": f"_shared/templates/{entity_type.replace('hisys/', '')}.md",
        }
        for entity_type in entity_types
    ]
    return {
        "schema_id": "hisys.obsidian.vault_template_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "templates": templates,
        "allowed_relations": sorted(_ALLOWED_LINK_RELATIONS),
        "required_indexes": [
            "registry.json",
            "topics/INDEX.json",
            "groups/INDEX.json",
            "investigations/INDEX.json",
            "runtime-boundary/runtime-index.json",
            "attachments/attachment-index.json",
            "reports/report-index.json",
        ],
        "vault_write_attempted": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_vault_template_plan_artifacts(*, instance_root: Path, yyyymmdd: str, plan: dict[str, Any]) -> tuple[Path, Path]:
    plan_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"vault-template-plan-{plan['request_id']}.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_dir = instance_root / "reports" / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_id": "hisys.obsidian.vault_template_plan_report",
        "schema_version": _SCHEMA_VERSION,
        "request_id": plan["request_id"],
        "template_plan_ref": str(plan_path.relative_to(instance_root)),
        "template_count": len(plan["templates"]),
        "relation_count": len(plan["allowed_relations"]),
        "vault_write_attempted": False,
        "external_call_made": False,
        "mutation_performed": False,
    }
    report_path = report_dir / "vault-template-plan-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / "vault-template-plan-report.md").write_text(_format_vault_template_plan_report(report), encoding="utf-8")
    return plan_path, report_path


def build_topic_identity_transition_plan(
    *,
    request_id: str,
    action: str,
    source_topic_uid: str,
    target_topic_uid: str,
    approval_ref: str | None,
    rationale: str,
) -> dict[str, Any]:
    """Plan non-destructive topic merge/split identity transitions."""

    if not _TOPIC_UID_RE.fullmatch(source_topic_uid) or not _TOPIC_UID_RE.fullmatch(target_topic_uid):
        raise ValueError("invalid topic uid")
    if action not in {"merge_with_existing_topic", "split_topic_recommended"}:
        raise ValueError("unsupported topic transition action")
    base = {
        "schema_id": "hisys.obsidian.topic_identity_transition_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "action": action,
        "source_topic_uid": source_topic_uid,
        "target_topic_uid": target_topic_uid,
        "approval_required": True,
        "approval_ref": approval_ref,
        "rationale": rationale,
        "non_destructive": True,
        "delete_old_topic_folder": False,
        "vault_write_attempted": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }
    if not approval_ref:
        return {**base, "status": "blocked", "reason_code": "approval_ref_required", "planned_file_writes": [], "planned_manifest_updates": []}

    if action == "merge_with_existing_topic":
        tombstone_ref = f"topics/{source_topic_uid}/MERGED_INTO.md"
        manifest_update = {"topic_uid": source_topic_uid, "status": "merged", "merged_into": target_topic_uid}
    else:
        tombstone_ref = f"topics/{source_topic_uid}/SPLIT_INTO.md"
        manifest_update = {"topic_uid": source_topic_uid, "status": "active", "split_into": [target_topic_uid]}

    return {
        **base,
        "status": "planned",
        "reason_code": None,
        "planned_tombstone_ref": tombstone_ref,
        "planned_file_writes": [tombstone_ref, f"topics/{source_topic_uid}/topic-manifest.json"],
        "planned_manifest_updates": [manifest_update],
    }


def write_topic_identity_transition_plan(*, instance_root: Path, yyyymmdd: str, plan: dict[str, Any]) -> Path:
    plan_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / f"topic-transition-plan-{plan['request_id']}.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (plan_dir / f"topic-transition-plan-{plan['request_id']}.md").write_text(_format_topic_identity_transition_plan(plan), encoding="utf-8")
    return plan_path


def apply_vault_plan_to_fixture(
    *,
    plan: dict[str, Any],
    target_vault_root: Path,
    approval_ref: str | None,
    fixture_vault_only: bool,
) -> dict[str, Any]:
    """Apply a vault plan to an explicit fixture vault root only.

    This is a controlled local writer for harness/fixture targets. It is not a
    real `/home/cbchoi/obsidian` writer and refuses to run without approval.
    """

    request_id = str(plan.get("request_id", "unknown"))
    base_report = {
        "schema_id": "hisys.obsidian.vault_apply_report",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "approval_ref": approval_ref,
        "fixture_vault_only": fixture_vault_only,
        "target_vault_root": str(target_vault_root),
        "vault_write_attempted": False,
        "target_vault_write_performed": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
        "written_file_count": 0,
        "written_files": [],
    }
    if not approval_ref:
        return {**base_report, "status": "blocked", "reason_code": "approval_ref_required"}
    if not fixture_vault_only:
        return {**base_report, "status": "blocked", "reason_code": "fixture_vault_only_required"}
    if _is_real_obsidian_vault(target_vault_root):
        return {**base_report, "status": "blocked", "reason_code": "real_obsidian_vault_blocked"}

    planned_files = [str(ref) for ref in plan.get("planned_files", [])]
    _validate_refs(planned_files)
    written_files: list[str] = []
    for ref in planned_files:
        path = target_vault_root / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_fixture_vault_file_content(ref=ref, plan=plan, approval_ref=approval_ref), encoding="utf-8")
        written_files.append(ref)

    return {
        **base_report,
        "status": "applied",
        "reason_code": None,
        "vault_write_attempted": True,
        "target_vault_write_performed": True,
        "mutation_performed": True,
        "written_file_count": len(written_files),
        "written_files": written_files,
    }


def write_vault_apply_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"vault-apply-report-{report['request_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-apply-report-{report['request_id']}.md").write_text(_format_vault_apply_report(report), encoding="utf-8")
    return report_path


def _is_real_obsidian_vault(path: Path) -> bool:
    try:
        return path.expanduser().resolve() == Path("/home/cbchoi/obsidian").resolve()
    except OSError:
        return str(path.expanduser()) == "/home/cbchoi/obsidian"


def _fixture_vault_file_content(*, ref: str, plan: dict[str, Any], approval_ref: str) -> str:
    if ref.endswith(".json"):
        payload = {
            "schema_id": "hisys.obsidian.fixture_registry_projection" if ref == "registry.json" else "hisys.obsidian.fixture_vault_projection",
            "schema_version": _SCHEMA_VERSION,
            "source_plan_request_id": plan.get("request_id"),
            "topic_uid": plan.get("topic_uid"),
            "investigation_id": plan.get("investigation_id"),
            "vault_relative_ref": ref,
            "approval_ref": approval_ref,
            "fixture_projection_only": True,
            "real_obsidian_vault_write_performed": False,
            "external_call_made": False,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return "\n".join(
        [
            "---",
            "type: hisys/fixture-vault-projection",
            f"schema_version: \"{_SCHEMA_VERSION}\"",
            f"source_plan_request_id: {plan.get('request_id')}",
            f"topic_uid: {plan.get('topic_uid')}",
            f"investigation_id: {plan.get('investigation_id')}",
            f"approval_ref: {approval_ref}",
            "fixture_projection_only: true",
            "real_obsidian_vault_write_performed: false",
            "external_call_made: false",
            "---",
            "",
            f"# {ref}",
            "",
            "Fixture vault projection generated from a controlled Hisys vault plan.",
            "",
        ]
    )


def build_live_vault_preflight_report(*, vault_root: Path, request_id: str) -> dict[str, Any]:
    """Inspect a candidate live Obsidian vault without writing to it."""

    expanded = vault_root.expanduser()
    issues: list[dict[str, str]] = []
    vault_exists = expanded.exists() and expanded.is_dir()
    obsidian_config_detected = (expanded / ".obsidian").is_dir()
    git_repo_detected = (expanded / ".git").exists()
    gitignore_path = expanded / ".gitignore"
    gitignore_text = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    ignored_attachment_policy_detected = "attachments/pdf" in gitignore_text or "attachments/" in gitignore_text

    if not vault_exists:
        issues.append({"code": "vault_root_missing", "path": str(expanded), "message": "vault root does not exist"})
    if not obsidian_config_detected:
        issues.append({"code": "obsidian_config_missing", "path": str(expanded / ".obsidian"), "message": "Obsidian config directory is missing"})
    if not git_repo_detected:
        issues.append({"code": "git_repo_missing", "path": str(expanded / ".git"), "message": "git repository marker is missing"})
    if not ignored_attachment_policy_detected:
        issues.append({"code": "attachment_ignore_policy_missing", "path": str(gitignore_path), "message": "heavy attachment ignore policy was not detected"})

    status = "ready_for_approval_package" if not issues else "blocked"
    return {
        "schema_id": "hisys.obsidian.live_vault_preflight_report",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": status,
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "vault_root": str(expanded),
        "vault_exists": vault_exists,
        "obsidian_config_detected": obsidian_config_detected,
        "git_repo_detected": git_repo_detected,
        "ignored_attachment_policy_detected": ignored_attachment_policy_detected,
        "write_probe_performed": False,
        "write_permission_detected_without_write": bool(vault_exists),
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_live_vault_preflight_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"vault-live-preflight-{report['request_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-live-preflight-{report['request_id']}.md").write_text(_format_live_vault_preflight_report(report), encoding="utf-8")
    return report_path


def build_live_vault_approval_package(
    *,
    request_id: str,
    preflight_report: dict[str, Any],
    vault_plan: dict[str, Any],
    operator_id: str,
    rationale: str,
) -> dict[str, Any]:
    """Build a human approval package for a future live vault write without enabling it."""

    if not preflight_report.get("valid") or preflight_report.get("status") != "ready_for_approval_package":
        return {
            "schema_id": "hisys.obsidian.live_vault_approval_package",
            "schema_version": _SCHEMA_VERSION,
            "request_id": request_id,
            "status": "blocked",
            "reason_code": "preflight_not_ready",
            "approval_required": True,
            "required_approvals": [],
            "planned_write_count": 0,
            "planned_writes": [],
            "operator_id": operator_id,
            "rationale": rationale,
            "preflight_request_id": preflight_report.get("request_id"),
            "plan_request_id": vault_plan.get("request_id"),
            "rollback_plan": {},
            "final_gate_before_live_write": [],
            "live_write_enabled": False,
            "real_obsidian_vault_write_performed": False,
            "external_call_made": False,
            "mutation_performed": False,
        }

    planned_refs = [str(ref) for ref in vault_plan.get("planned_files", [])]
    _validate_refs(planned_refs)
    planned_writes = [
        {
            "vault_relative_ref": ref,
            "operation": "create_or_update_after_separate_approval",
            "source_plan_request_id": vault_plan.get("request_id"),
            "requires_human_review": True,
        }
        for ref in planned_refs
    ]
    return {
        "schema_id": "hisys.obsidian.live_vault_approval_package",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "approval_required",
        "approval_required": True,
        "required_approvals": [
            "human_live_vault_write_approval",
            "clean_git_status_confirmation",
            "rollback_plan_acknowledgement",
        ],
        "operator_id": operator_id,
        "rationale": rationale,
        "preflight_request_id": preflight_report.get("request_id"),
        "plan_request_id": vault_plan.get("request_id"),
        "vault_root": preflight_report.get("vault_root"),
        "topic_uid": vault_plan.get("topic_uid"),
        "investigation_id": vault_plan.get("investigation_id"),
        "planned_write_count": len(planned_writes),
        "planned_writes": planned_writes,
        "rollback_plan": {
            "strategy": "git_revert_or_delete_new_files_after_review",
            "requires_clean_git_before_write": True,
            "preserve_runtime_boundary_reports": True,
        },
        "final_gate_before_live_write": ["vault-live-preflight", "vault-roundtrip-validate", "git status --short"],
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_live_vault_approval_package(*, instance_root: Path, yyyymmdd: str, package: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"vault-live-approval-package-{package['request_id']}.json"
    report_path.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-live-approval-package-{package['request_id']}.md").write_text(_format_live_vault_approval_package(package), encoding="utf-8")
    return report_path


def build_live_vault_write_gate_report(
    *,
    request_id: str,
    approval_package: dict[str, Any],
    approval_ref: str | None,
    explicit_live_write_enable: bool,
    clean_git_status: bool,
) -> dict[str, Any]:
    """Evaluate final live-vault write gates without implementing or performing writes."""

    planned_writes = approval_package.get("planned_writes", [])
    required_approvals = set(approval_package.get("required_approvals", []))
    approved_for_future_live_write = bool(
        approval_ref
        and approval_package.get("status") == "approval_required"
        and "human_live_vault_write_approval" in required_approvals
        and "rollback_plan_acknowledgement" in required_approvals
    )
    if not clean_git_status:
        reason_code = "git_status_not_clean"
    elif not approved_for_future_live_write:
        reason_code = "approval_package_not_satisfied"
    elif not explicit_live_write_enable:
        reason_code = "live_write_not_enabled"
    else:
        reason_code = "live_writer_not_implemented"

    return {
        "schema_id": "hisys.obsidian.live_vault_write_gate_report",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "blocked",
        "reason_code": reason_code,
        "implementation_boundary": "gate_only_no_writer",
        "approval_package_request_id": approval_package.get("request_id"),
        "approval_ref": approval_ref,
        "approved_for_future_live_write": approved_for_future_live_write,
        "explicit_live_write_enable_requested": explicit_live_write_enable,
        "clean_git_status": clean_git_status,
        "planned_write_count": len(planned_writes),
        "planned_writes_preview": planned_writes,
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_live_vault_write_gate_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"vault-live-write-gate-{report['request_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-live-write-gate-{report['request_id']}.md").write_text(_format_live_vault_write_gate_report(report), encoding="utf-8")
    return report_path


def build_live_vault_transaction_plan(
    *,
    request_id: str,
    approval_package: dict[str, Any],
    write_gate_report: dict[str, Any],
) -> dict[str, Any]:
    """Build a live-vault transaction manifest without reading or writing the live vault."""

    gate_at_boundary = (
        write_gate_report.get("status") == "blocked"
        and write_gate_report.get("reason_code") == "live_writer_not_implemented"
        and write_gate_report.get("implementation_boundary") == "gate_only_no_writer"
    )
    if not gate_at_boundary:
        return {
            "schema_id": "hisys.obsidian.live_vault_transaction_plan",
            "schema_version": _SCHEMA_VERSION,
            "request_id": request_id,
            "status": "blocked",
            "reason_code": "write_gate_not_at_writer_boundary",
            "source_approval_package_request_id": approval_package.get("request_id"),
            "source_write_gate_request_id": write_gate_report.get("request_id"),
            "planned_operation_count": 0,
            "planned_operations": [],
            "implementation_boundary": "transaction_manifest_only_no_writer",
            "requires_followup_writer_implementation": True,
            "live_write_enabled": False,
            "real_obsidian_vault_write_performed": False,
            "external_call_made": False,
            "mutation_performed": False,
        }

    planned_writes = approval_package.get("planned_writes", [])
    refs = [str(item.get("vault_relative_ref", "")) for item in planned_writes]
    _validate_refs(refs)
    planned_operations = [
        {
            "operation_id": f"live-vault-op-{index:04d}",
            "operation": item.get("operation", "create_or_update_after_separate_approval"),
            "vault_relative_ref": ref,
            "pre_write_hash": "not_read_no_live_write",
            "post_write_hash": "not_written_no_live_write",
            "rollback_action": "restore_pre_write_hash_or_delete_created_file_after_separate_writer",
            "requires_separate_writer_implementation": True,
        }
        for index, (item, ref) in enumerate(zip(planned_writes, refs, strict=True), start=1)
    ]
    return {
        "schema_id": "hisys.obsidian.live_vault_transaction_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "planned_not_executable",
        "implementation_boundary": "transaction_manifest_only_no_writer",
        "source_approval_package_request_id": approval_package.get("request_id"),
        "source_write_gate_request_id": write_gate_report.get("request_id"),
        "vault_root": approval_package.get("vault_root"),
        "planned_operation_count": len(planned_operations),
        "planned_operations": planned_operations,
        "rollback_plan": approval_package.get("rollback_plan", {}),
        "requires_followup_writer_implementation": True,
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_live_vault_transaction_plan(*, instance_root: Path, yyyymmdd: str, plan: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"vault-live-transaction-plan-{plan['request_id']}.json"
    report_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-live-transaction-plan-{plan['request_id']}.md").write_text(_format_live_vault_transaction_plan(plan), encoding="utf-8")
    return report_path


def apply_live_vault_transaction(
    *,
    transaction_plan: dict[str, Any],
    vault_root: Path,
    approval_ref: str | None,
    explicit_live_write_enable: bool,
    allow_real_obsidian_vault: bool,
    clean_git_status: bool,
) -> dict[str, Any]:
    """Apply a transaction to an approved vault root with explicit live-write gates."""

    real_vault = _is_real_obsidian_vault(vault_root)
    base = {
        "schema_id": "hisys.obsidian.live_vault_transaction_apply",
        "schema_version": _SCHEMA_VERSION,
        "source_transaction_request_id": transaction_plan.get("request_id"),
        "vault_root": str(vault_root),
        "approval_ref": approval_ref,
        "explicit_live_write_enable": explicit_live_write_enable,
        "allow_real_obsidian_vault": allow_real_obsidian_vault,
        "clean_git_status": clean_git_status,
        "external_call_made": False,
        "real_obsidian_vault_write_performed": False,
    }
    if real_vault and not allow_real_obsidian_vault:
        return {**base, "status": "blocked", "reason_code": "real_obsidian_vault_requires_explicit_flag", "operation_count": 0, "mutation_performed": False}
    if not approval_ref or not explicit_live_write_enable or not clean_git_status or transaction_plan.get("status") != "planned_not_executable":
        return {**base, "status": "blocked", "reason_code": "live_apply_gate_not_satisfied", "operation_count": 0, "mutation_performed": False}

    operations = transaction_plan.get("planned_operations", [])
    refs = [str(operation.get("vault_relative_ref", "")) for operation in operations]
    _validate_refs(refs)
    applied: list[dict[str, str]] = []
    for operation, ref in zip(operations, refs, strict=True):
        target = vault_root / ref
        pre_hash = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else "missing"
        payload = {
            "live_transaction_projection": True,
            "source_transaction_request_id": transaction_plan.get("request_id"),
            "source_operation_id": operation.get("operation_id"),
            "vault_relative_ref": ref,
            "approval_ref": approval_ref,
            "real_obsidian_vault_write_performed": real_vault,
            "external_call_made": False,
        }
        data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
        post_hash = hashlib.sha256(data.encode("utf-8")).hexdigest()
        applied.append({"operation_id": str(operation.get("operation_id")), "vault_relative_ref": ref, "pre_write_hash": pre_hash, "post_write_hash": post_hash})

    return {
        **base,
        "status": "applied",
        "operation_count": len(applied),
        "applied_operations": applied,
        "mutation_performed": True,
        "real_obsidian_vault_write_performed": real_vault,
    }


def write_live_vault_transaction_apply_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    request_id = report.get("source_transaction_request_id", report.get("request_id", "unknown"))
    report_path = report_dir / f"vault-live-transaction-apply-{request_id}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-live-transaction-apply-{request_id}.md").write_text(_format_live_vault_transaction_apply(report), encoding="utf-8")
    return report_path


def rehearse_live_vault_transaction_in_fixture(
    *,
    transaction_plan: dict[str, Any],
    fixture_vault_root: Path,
    approval_ref: str | None,
    fixture_vault_only: bool,
) -> dict[str, Any]:
    """Rehearse a live-vault transaction manifest against a fixture root only."""

    if _is_real_obsidian_vault(fixture_vault_root):
        return {
            "schema_id": "hisys.obsidian.live_vault_transaction_rehearsal",
            "schema_version": _SCHEMA_VERSION,
            "status": "blocked",
            "reason_code": "real_obsidian_vault_blocked",
            "source_transaction_request_id": transaction_plan.get("request_id"),
            "fixture_vault_root": str(fixture_vault_root),
            "fixture_vault_only": fixture_vault_only,
            "operation_count": 0,
            "real_obsidian_vault_write_performed": False,
            "external_call_made": False,
            "mutation_performed": False,
        }
    if not approval_ref or not fixture_vault_only or transaction_plan.get("status") != "planned_not_executable":
        return {
            "schema_id": "hisys.obsidian.live_vault_transaction_rehearsal",
            "schema_version": _SCHEMA_VERSION,
            "status": "blocked",
            "reason_code": "fixture_rehearsal_gate_not_satisfied",
            "source_transaction_request_id": transaction_plan.get("request_id"),
            "fixture_vault_root": str(fixture_vault_root),
            "fixture_vault_only": fixture_vault_only,
            "operation_count": 0,
            "real_obsidian_vault_write_performed": False,
            "external_call_made": False,
            "mutation_performed": False,
        }

    operations = transaction_plan.get("planned_operations", [])
    refs = [str(operation.get("vault_relative_ref", "")) for operation in operations]
    _validate_refs(refs)
    written: list[dict[str, str]] = []
    for operation, ref in zip(operations, refs, strict=True):
        target = fixture_vault_root / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fixture_projection_only": True,
            "source_transaction_request_id": transaction_plan.get("request_id"),
            "source_operation_id": operation.get("operation_id"),
            "vault_relative_ref": ref,
            "approval_ref": approval_ref,
            "real_obsidian_vault_write_performed": False,
        }
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append({"operation_id": str(operation.get("operation_id")), "vault_relative_ref": ref})

    return {
        "schema_id": "hisys.obsidian.live_vault_transaction_rehearsal",
        "schema_version": _SCHEMA_VERSION,
        "status": "rehearsed_fixture_only",
        "source_transaction_request_id": transaction_plan.get("request_id"),
        "fixture_vault_root": str(fixture_vault_root),
        "fixture_vault_only": True,
        "approval_ref": approval_ref,
        "operation_count": len(written),
        "written_fixture_refs": written,
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_live_vault_transaction_rehearsal_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    request_id = report.get("source_transaction_request_id", report.get("request_id", "unknown"))
    report_path = report_dir / f"vault-live-transaction-rehearsal-{request_id}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-live-transaction-rehearsal-{request_id}.md").write_text(_format_live_vault_transaction_rehearsal(report), encoding="utf-8")
    return report_path


def validate_fixture_vault_roundtrip(
    *,
    plan: dict[str, Any],
    fixture_vault_root: Path,
    apply_report: dict[str, Any],
) -> dict[str, Any]:
    """Validate planned -> fixture-applied vault projections without live vault writes."""

    planned_files = [str(ref) for ref in plan.get("planned_files", [])]
    _validate_refs(planned_files)
    planned_set = set(planned_files)
    actual_files = sorted(str(path.relative_to(fixture_vault_root)) for path in fixture_vault_root.rglob("*") if path.is_file())
    actual_set = set(actual_files)
    issues: list[dict[str, str]] = []

    for ref in sorted(planned_set - actual_set):
        issues.append({"code": "missing_planned_file", "path": ref, "message": "planned file is missing from fixture vault"})
    for ref in sorted(actual_set - planned_set):
        issues.append({"code": "unexpected_fixture_file", "path": ref, "message": "file was not present in the source vault plan"})

    metadata_valid = True
    for ref in sorted(planned_set & actual_set):
        path = fixture_vault_root / ref
        text = path.read_text(encoding="utf-8")
        expected_fragments = [str(plan.get("request_id")), str(plan.get("topic_uid")), str(plan.get("investigation_id")), "real_obsidian_vault_write_performed", "external_call_made"]
        if ref.endswith(".json"):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                metadata_valid = False
                issues.append({"code": "invalid_projection_json", "path": ref, "message": "projection JSON cannot be parsed"})
                continue
            if payload.get("source_plan_request_id") != plan.get("request_id"):
                metadata_valid = False
                issues.append({"code": "projection_request_mismatch", "path": ref, "message": "source plan request id mismatch"})
            if payload.get("topic_uid") != plan.get("topic_uid") or payload.get("investigation_id") != plan.get("investigation_id"):
                metadata_valid = False
                issues.append({"code": "projection_identity_mismatch", "path": ref, "message": "topic/investigation identity mismatch"})
            if payload.get("fixture_projection_only") is not True or payload.get("real_obsidian_vault_write_performed") is not False:
                metadata_valid = False
                issues.append({"code": "projection_governance_mismatch", "path": ref, "message": "projection governance flags invalid"})
        elif not all(fragment in text for fragment in expected_fragments):
            metadata_valid = False
            issues.append({"code": "projection_metadata_missing", "path": ref, "message": "projection frontmatter is missing required governance metadata"})

    written_files = set(str(ref) for ref in apply_report.get("written_files", []))
    apply_matches = apply_report.get("status") == "applied" and written_files == planned_set and apply_report.get("real_obsidian_vault_write_performed") is False and apply_report.get("external_call_made") is False
    if not apply_matches:
        issues.append({"code": "apply_report_mismatch", "path": "apply_report", "message": "apply report does not match planned fixture files"})

    valid = not issues
    return {
        "schema_id": "hisys.obsidian.fixture_vault_roundtrip_report",
        "schema_version": _SCHEMA_VERSION,
        "request_id": plan.get("request_id"),
        "valid": valid,
        "status": "valid" if valid else "invalid",
        "issue_count": len(issues),
        "issues": issues,
        "checked_file_count": len(planned_files),
        "missing_file_count": len(planned_set - actual_set),
        "unexpected_file_count": len(actual_set - planned_set),
        "projection_metadata_valid": metadata_valid,
        "apply_report_matches_fixture": apply_matches,
        "fixture_vault_root": str(fixture_vault_root),
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_vault_roundtrip_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"vault-roundtrip-report-{report['request_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-roundtrip-report-{report['request_id']}.md").write_text(_format_vault_roundtrip_report(report), encoding="utf-8")
    return report_path


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
        for group_uid in topic.get("group_uids", []):
            _check_group_uid(group_uid, "registry.topic.group_uids", issues)
    for group in registry.get("groups", []):
        _check_group_uid(group.get("group_uid"), "registry.group_uid", issues)
        _check_slug(group.get("group_slug"), "registry.group_slug", issues)
        _check_ref(group.get("path"), "registry.group.path", issues)
        for topic_uid in group.get("topic_uids", []):
            _check_topic_uid(topic_uid, "registry.group.topic_uids", issues)

    _check_topic_uid(topic_manifest.get("topic_uid"), "topic_manifest.topic_uid", issues)
    _check_ref(topic_manifest.get("path"), "topic_manifest.path", issues)
    for ref in _flatten_refs(topic_manifest.get("canonical_indexes", {})):
        _check_ref(ref, "topic_manifest.canonical_indexes", issues)
    _check_ref(topic_manifest.get("investigations_index"), "topic_manifest.investigations_index", issues)
    for ref in topic_manifest.get("group_refs", []):
        _check_ref(ref, "topic_manifest.group_refs", issues)
    for ref in topic_manifest.get("gatekeeper_decision_refs", []):
        _check_ref(ref, "topic_manifest.gatekeeper_decision_refs", issues)
    _check_structured_links(topic_manifest.get("links", []), "topic_manifest.links", issues)

    _check_topic_uid(investigation_manifest.get("topic_uid"), "investigation_manifest.topic_uid", issues)
    _check_slug(investigation_manifest.get("topic_slug"), "investigation_manifest.topic_slug", issues)
    _check_investigation_id(investigation_manifest.get("investigation_id"), "investigation_manifest.investigation_id", issues)
    _check_investigation_id(investigation_manifest.get("run_id"), "investigation_manifest.run_id", issues)
    paths = investigation_manifest.get("paths", {})
    for ref in _flatten_refs(paths):
        _check_ref(ref, "investigation_manifest.paths", issues)
    for ref in _flatten_refs(investigation_manifest.get("indexes", {})):
        _check_ref(ref, "investigation_manifest.indexes", issues)
    _check_structured_links(investigation_manifest.get("links", []), "investigation_manifest.links", issues)
    for ref in _flatten_refs(investigation_manifest.get("artifacts", {})):
        _check_ref(ref, "investigation_manifest.artifacts", issues)

    _check_structured_links(gatekeeper.get("links", []), "gatekeeper.links", issues)
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
    if len(ref) > _MAX_VAULT_REF_LENGTH:
        issues.append({"code": "overlong_vault_relative_ref", "path": path, "message": ref})
    if ref_path.is_absolute() or ".." in ref_path.parts:
        issues.append({"code": "unsafe_vault_relative_ref", "path": path, "message": ref})


def _check_topic_uid(uid: object, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(uid, str) or not _TOPIC_UID_RE.fullmatch(uid):
        issues.append({"code": "invalid_topic_uid", "path": path, "message": str(uid)})


def _check_group_uid(uid: object, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(uid, str) or not _GROUP_UID_RE.fullmatch(uid):
        issues.append({"code": "invalid_group_uid", "path": path, "message": str(uid)})


def _check_investigation_id(investigation_id: object, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(investigation_id, str) or not _INVESTIGATION_ID_RE.fullmatch(investigation_id):
        issues.append({"code": "invalid_investigation_id", "path": path, "message": str(investigation_id)})


def _check_structured_links(links: object, path: str, issues: list[dict[str, str]]) -> None:
    if links is None:
        return
    if not isinstance(links, list):
        issues.append({"code": "invalid_links", "path": path, "message": "links must be a list"})
        return
    for index, link in enumerate(links):
        link_path = f"{path}[{index}]"
        if not isinstance(link, dict):
            issues.append({"code": "invalid_link", "path": link_path, "message": "link must be an object"})
            continue
        relation = link.get("relation")
        if relation not in _ALLOWED_LINK_RELATIONS:
            issues.append({"code": "unknown_link_relation", "path": f"{link_path}.relation", "message": str(relation)})
        _check_ref(link.get("ref"), f"{link_path}.ref", issues)


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


def _format_vault_template_plan_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Vault Template Plan Report",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Template plan ref: `{report['template_plan_ref']}`",
            f"- Template count: {report['template_count']}",
            f"- Relation count: {report['relation_count']}",
            "- vault_write_attempted: false",
            "- external_call_made: false",
            "- mutation_performed: false",
            "",
        ]
    )


def _format_live_vault_transaction_apply(report: dict[str, Any]) -> str:
    ops = "\n".join(f"- `{item['vault_relative_ref']}` pre=`{item['pre_write_hash']}` post=`{item['post_write_hash']}`" for item in report.get("applied_operations", [])) or "- none"
    return "\n".join(
        [
            "# Obsidian Live Transaction Apply Report",
            "",
            f"- Source transaction: `{report.get('source_transaction_request_id')}`",
            f"- Status: {report['status']}",
            f"- Operation count: {report['operation_count']}",
            f"- Mutation performed: {str(report.get('mutation_performed')).lower()}",
            f"- Real Obsidian vault write performed: {str(report.get('real_obsidian_vault_write_performed')).lower()}",
            "",
            "## Operations",
            ops,
            "",
        ]
    )


def _format_live_vault_transaction_rehearsal(report: dict[str, Any]) -> str:
    refs = "\n".join(f"- `{item['vault_relative_ref']}`" for item in report.get("written_fixture_refs", [])) or "- none"
    return "\n".join(
        [
            "# Obsidian Live Transaction Fixture Rehearsal",
            "",
            f"- Source transaction: `{report.get('source_transaction_request_id')}`",
            f"- Status: {report['status']}",
            f"- Operation count: {report['operation_count']}",
            "- fixture_vault_only: true",
            "- real_obsidian_vault_write_performed: false",
            "",
            "## Written fixture refs",
            refs,
            "",
        ]
    )


def _format_live_vault_transaction_plan(plan: dict[str, Any]) -> str:
    ops = "\n".join(f"- `{item['vault_relative_ref']}` ({item['operation']})" for item in plan.get("planned_operations", [])) or "- none"
    return "\n".join(
        [
            "# Obsidian Live Vault Transaction Plan",
            "",
            f"- Request: `{plan['request_id']}`",
            f"- Status: {plan['status']}",
            f"- Boundary: {plan['implementation_boundary']}",
            f"- Planned operations: {plan['planned_operation_count']}",
            "- live_write_enabled: false",
            "- real_obsidian_vault_write_performed: false",
            "",
            "## Planned operations",
            ops,
            "",
        ]
    )


def _format_live_vault_write_gate_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Live Vault Write Gate Report",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Status: {report['status']}",
            f"- Reason: {report['reason_code']}",
            f"- Approved for future live write: {str(report['approved_for_future_live_write']).lower()}",
            f"- Planned writes: {report['planned_write_count']}",
            "- live_write_enabled: false",
            "- real_obsidian_vault_write_performed: false",
            "- implementation_boundary: gate_only_no_writer",
            "",
        ]
    )


def _format_live_vault_approval_package(package: dict[str, Any]) -> str:
    planned = "\n".join(f"- `{item['vault_relative_ref']}`" for item in package.get("planned_writes", [])) or "- none"
    approvals = "\n".join(f"- {approval}" for approval in package.get("required_approvals", [])) or "- none"
    return "\n".join(
        [
            "# Obsidian Live Vault Approval Package",
            "",
            f"- Request: `{package['request_id']}`",
            f"- Status: {package['status']}",
            "- live_write_enabled: false",
            "- real_obsidian_vault_write_performed: false",
            "",
            "## Required approvals",
            approvals,
            "",
            "## Planned writes",
            planned,
            "",
        ]
    )


def _format_live_vault_preflight_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Live Vault Preflight Report",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Status: {report['status']}",
            f"- Vault exists: {str(report['vault_exists']).lower()}",
            f"- Obsidian config detected: {str(report['obsidian_config_detected']).lower()}",
            f"- Git repo detected: {str(report['git_repo_detected']).lower()}",
            f"- Attachment ignore policy detected: {str(report['ignored_attachment_policy_detected']).lower()}",
            "- write_probe_performed: false",
            "- live_write_enabled: false",
            "",
        ]
    )


def _format_vault_roundtrip_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Fixture Vault Roundtrip Report",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Status: {report['status']}",
            f"- Checked files: {report['checked_file_count']}",
            f"- Missing files: {report['missing_file_count']}",
            f"- Unexpected files: {report['unexpected_file_count']}",
            f"- Projection metadata valid: {str(report['projection_metadata_valid']).lower()}",
            f"- Apply report matches fixture: {str(report['apply_report_matches_fixture']).lower()}",
            f"- Real vault write performed: {str(report['real_obsidian_vault_write_performed']).lower()}",
            "",
        ]
    )


def _format_topic_identity_transition_plan(plan: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Topic Identity Transition Plan",
            "",
            f"- Request: `{plan['request_id']}`",
            f"- Status: {plan['status']}",
            f"- Action: `{plan['action']}`",
            f"- Source topic: `{plan['source_topic_uid']}`",
            f"- Target topic: `{plan['target_topic_uid']}`",
            f"- Approval required: {str(plan['approval_required']).lower()}",
            f"- Non-destructive: {str(plan['non_destructive']).lower()}",
            f"- Delete old topic folder: {str(plan['delete_old_topic_folder']).lower()}",
            f"- Real vault write performed: {str(plan['real_obsidian_vault_write_performed']).lower()}",
            "",
        ]
    )


def _format_vault_apply_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Vault Apply Report",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Status: {report['status']}",
            f"- Reason: {report.get('reason_code')}",
            f"- Written files: {report['written_file_count']}",
            f"- fixture_vault_only: {str(report['fixture_vault_only']).lower()}",
            f"- target_vault_write_performed: {str(report['target_vault_write_performed']).lower()}",
            f"- real_obsidian_vault_write_performed: {str(report['real_obsidian_vault_write_performed']).lower()}",
            f"- external_call_made: {str(report['external_call_made']).lower()}",
            "",
        ]
    )


__all__ = [
    "apply_live_vault_transaction",
    "apply_vault_plan_to_fixture",
    "build_live_vault_approval_package",
    "build_live_vault_preflight_report",
    "build_live_vault_transaction_plan",
    "build_live_vault_write_gate_report",
    "build_topic_identity_transition_plan",
    "build_vault_plan",
    "build_vault_template_plan",
    "rehearse_live_vault_transaction_in_fixture",
    "validate_fixture_vault_roundtrip",
    "validate_vault_manifests",
    "write_live_vault_approval_package",
    "write_vault_apply_report",
    "write_live_vault_preflight_report",
    "write_live_vault_transaction_apply_report",
    "write_live_vault_transaction_plan",
    "write_live_vault_transaction_rehearsal_report",
    "write_live_vault_write_gate_report",
    "write_vault_plan_artifacts",
    "write_vault_roundtrip_report",
    "write_vault_template_plan_artifacts",
    "write_vault_validation_report",
    "write_topic_identity_transition_plan",
]
