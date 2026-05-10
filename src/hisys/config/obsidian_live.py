"""Fixture-only Obsidian live-research vault planning.

Traceability: Live-Obsidian-Config-A/B, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "0.1.0"
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")
_TOPIC_UID_RE = re.compile(r"^TOPIC-\d{8}-[A-Z0-9]{6}$")
_GROUP_UID_RE = re.compile(r"^GROUP-\d{8}-[A-Z0-9]{6}$")
_INVESTIGATION_ID_RE = re.compile(r"^INV-\d{8}-\d{4}-[A-Z0-9]{4}$")
_MAX_VAULT_REF_LENGTH = 240
_ALLOWED_GIT_CREDENTIAL_REF_SCHEMES = frozenset({"env", "keyring", "file", "ssh-agent", "secretstore", "op", "aws-sm"})
_GIT_CREDENTIAL_REF_RE = re.compile(
    rf"(?:{'|'.join(re.escape(scheme) for scheme in sorted(_ALLOWED_GIT_CREDENTIAL_REF_SCHEMES, key=len, reverse=True))}):[A-Za-z0-9_./:@+-]+"
)
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
    vault_relative_root = str(registry.get("vault_relative_root", "91 Hisys/Live Research")).strip("/")
    if not vault_relative_root:
        raise ValueError("vault_relative_root is required")
    _validate_refs([vault_relative_root])
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
        f"{vault_relative_root}/registry.json",
        f"{vault_relative_root}/topics/INDEX.json",
        f"{vault_relative_root}/{topic_path}/index.md",
        f"{vault_relative_root}/{topic_path}/topic-config.yaml",
        f"{vault_relative_root}/{topic_path}/topic-manifest.json",
        f"{vault_relative_root}/{topic_path}/investigations/INDEX.json",
        f"{vault_relative_root}/{investigation_path}/index.md",
        f"{vault_relative_root}/{investigation_path}/investigation-config.yaml",
        f"{vault_relative_root}/{investigation_path}/investigation-manifest.json",
        f"{vault_relative_root}/{investigation_path}/input/request.md",
        f"{vault_relative_root}/{investigation_path}/input/request.json",
        f"{vault_relative_root}/{investigation_path}/runtime-boundary/runtime-index.json",
        f"{vault_relative_root}/{investigation_path}/attachments/attachment-index.json",
        f"{vault_relative_root}/{investigation_path}/reports/report-index.json",
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
        "vault_relative_root": vault_relative_root,
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


def build_obsidian_git_initialization_plan(
    *,
    request_id: str,
    vault_root: Path,
    remote_url: str,
    default_branch: str,
    credential_ref: str,
    operator_id: str,
    approval_ref: str | None = None,
) -> dict[str, Any]:
    """Plan initialization of an Obsidian vault as a Hisys-managed Git repository.

    This is a controlled plan, not an executor: it records that the operator must
    provide credentials by reference. Raw credential material is never persisted.
    """

    credential_issue = _git_credential_issue(credential_ref)
    if credential_issue:
        return _blocked_obsidian_git_plan(
            schema_id="hisys.obsidian.git_initialization_plan",
            request_id=request_id,
            reason_code=credential_issue,
            vault_root=vault_root,
            credential_ref=credential_ref,
        )
    if not remote_url.strip():
        return _blocked_obsidian_git_plan(
            schema_id="hisys.obsidian.git_initialization_plan",
            request_id=request_id,
            reason_code="remote_url_required",
            vault_root=vault_root,
            credential_ref=credential_ref,
        )
    if not default_branch.strip():
        return _blocked_obsidian_git_plan(
            schema_id="hisys.obsidian.git_initialization_plan",
            request_id=request_id,
            reason_code="default_branch_required",
            vault_root=vault_root,
            credential_ref=credential_ref,
        )
    if not approval_ref:
        return _blocked_obsidian_git_plan(
            schema_id="hisys.obsidian.git_initialization_plan",
            request_id=request_id,
            reason_code="approval_ref_required",
            vault_root=vault_root,
            credential_ref=credential_ref,
        )

    operations = [
        {"operation_id": "obsidian-git-init-op-0001", "operation": "verify_or_create_vault_root", "vault_root": str(vault_root), "requires_approval": False},
        {"operation_id": "obsidian-git-init-op-0002", "operation": "git_init_if_missing", "default_branch": default_branch, "requires_approval": False},
        {"operation_id": "obsidian-git-init-op-0003", "operation": "configure_remote_origin", "remote_url": remote_url, "requires_approval": False},
        {"operation_id": "obsidian-git-init-op-0004", "operation": "install_lightweight_gitignore_policy", "policy": "notes_and_small_governance_json_only", "requires_approval": False},
        {"operation_id": "obsidian-git-init-op-0005", "operation": "credential_ref_binding", "credential_ref": credential_ref, "requires_approval": False},
        {"operation_id": "obsidian-git-init-op-0006", "operation": "initial_commit_and_push", "remote_name": "origin", "branch": default_branch, "approval_ref": approval_ref, "requires_approval": True},
    ]
    return {
        "schema_id": "hisys.obsidian.git_initialization_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "planned_requires_operator_credentials",
        "vault_root": str(vault_root),
        "remote_url": remote_url,
        "default_branch": default_branch,
        "operator_id": operator_id,
        "approval_ref": approval_ref,
        "credential_ref": credential_ref,
        "raw_credential_stored": False,
        "gitignore_policy": [
            "track_markdown_notes",
            "track_small_governance_json",
            "attachments_ignored_by_default",
            "secrets_ignored_always",
            "runtime_cache_logs_tmp_ignored",
        ],
        "required_gates": [
            "credential_ref_resolves_outside_repository",
            "remote_write_access_verified_by_operator",
            "no_raw_secret_in_config_or_runtime_boundary",
            "initial_push_requires_explicit_approval",
        ],
        "planned_operation_count": len(operations),
        "planned_operations": operations,
        "mutation_performed": False,
        "external_call_made": False,
    }


def build_obsidian_git_sync_plan(
    *,
    request_id: str,
    vault_root: Path,
    memo_refs: list[str],
    runtime_boundary_refs: list[str],
    commit_message: str,
    remote_name: str,
    branch: str,
    credential_ref: str,
    approval_ref: str | None,
) -> dict[str, Any]:
    """Plan Git sync after an approved vault write with at least one scoped ref."""

    refs = [*memo_refs, *runtime_boundary_refs]
    try:
        _validate_refs(refs)
    except ValueError:
        return _blocked_obsidian_git_plan(
            schema_id="hisys.obsidian.git_sync_plan",
            request_id=request_id,
            reason_code="unsafe_vault_ref",
            vault_root=vault_root,
            credential_ref=credential_ref,
        )
    credential_issue = _git_credential_issue(credential_ref)
    if credential_issue:
        return _blocked_obsidian_git_plan(
            schema_id="hisys.obsidian.git_sync_plan",
            request_id=request_id,
            reason_code=credential_issue,
            vault_root=vault_root,
            credential_ref=credential_ref,
        )
    missing = _missing_git_sync_field(refs, commit_message, remote_name, branch, approval_ref)
    if missing:
        return _blocked_obsidian_git_plan(
            schema_id="hisys.obsidian.git_sync_plan",
            request_id=request_id,
            reason_code=missing,
            vault_root=vault_root,
            credential_ref=credential_ref,
        )

    operations = [
        {"operation_id": "obsidian-git-sync-op-0001", "operation": "pre_sync_git_status", "must_be_clean_except_approved_refs": True, "requires_approval": False},
        {"operation_id": "obsidian-git-sync-op-0002", "operation": "stage_approved_memo_and_runtime_boundary_refs", "refs": refs, "requires_approval": False},
        {"operation_id": "obsidian-git-sync-op-0003", "operation": "commit_memo_projection", "commit_message": commit_message, "requires_approval": False},
        {"operation_id": "obsidian-git-sync-op-0004", "operation": "push_commit_to_remote", "remote_name": remote_name, "branch": branch, "credential_ref": credential_ref, "approval_ref": approval_ref, "requires_approval": True},
        {"operation_id": "obsidian-git-sync-op-0005", "operation": "record_post_push_status", "runtime_boundary_required": True, "requires_approval": False},
    ]
    return {
        "schema_id": "hisys.obsidian.git_sync_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "planned_after_vault_write",
        "vault_root": str(vault_root),
        "memo_refs": memo_refs,
        "runtime_boundary_refs": runtime_boundary_refs,
        "commit_message": commit_message,
        "remote_name": remote_name,
        "branch": branch,
        "credential_ref": credential_ref,
        "approval_ref": approval_ref,
        "raw_credential_stored": False,
        "required_gates": [
            "approved_vault_write_report_exists",
            "git_status_scoped_to_approved_refs",
            "credential_ref_resolves_outside_repository",
            "push_result_recorded_in_runtime_boundary",
        ],
        "planned_operation_count": len(operations),
        "planned_operations": operations,
        "mutation_performed": False,
        "external_call_made": False,
    }


def execute_obsidian_git_initialization_in_fixture(
    *,
    plan: dict[str, Any],
    fixture_vault_root: Path,
    fixture_remote_root: Path,
    fixture_git_only: bool,
) -> dict[str, Any]:
    """Execute an Obsidian Git initialization plan against local fixture Git repos only."""

    report = _base_obsidian_git_fixture_execution_report(
        plan=plan,
        operation="initialization",
        fixture_vault_root=fixture_vault_root,
        fixture_remote_root=fixture_remote_root,
        fixture_git_only=fixture_git_only,
    )
    blocked = _obsidian_git_fixture_execution_blocker(plan=plan, fixture_vault_root=fixture_vault_root, fixture_remote_root=fixture_remote_root, fixture_git_only=fixture_git_only)
    if blocked:
        return {**report, "status": "blocked", "reason_code": blocked}
    if plan.get("schema_id") != "hisys.obsidian.git_initialization_plan" or plan.get("status") != "planned_requires_operator_credentials":
        return {**report, "status": "blocked", "reason_code": "initialization_plan_required"}
    push_op = _push_operation(plan)
    if not push_op.get("approval_ref"):
        return {**report, "status": "blocked", "reason_code": "approval_ref_required"}

    branch = str(plan.get("default_branch") or push_op.get("branch") or "main")
    fixture_remote_root.parent.mkdir(parents=True, exist_ok=True)
    if not fixture_remote_root.exists():
        _run_git(["init", "--bare", str(fixture_remote_root)])
    fixture_vault_root.mkdir(parents=True, exist_ok=True)
    _ensure_git_repo(fixture_vault_root=fixture_vault_root, branch=branch)
    _run_git(["config", "user.email", "hisys-fixture@example.invalid"], cwd=fixture_vault_root)
    _run_git(["config", "user.name", "Hisys Fixture Executor"], cwd=fixture_vault_root)
    _ensure_origin(fixture_vault_root=fixture_vault_root, fixture_remote_root=fixture_remote_root)
    (fixture_vault_root / ".gitignore").write_text(_lightweight_obsidian_gitignore(), encoding="utf-8")
    _run_git(["add", ".gitignore"], cwd=fixture_vault_root)
    _commit_if_needed(fixture_vault_root=fixture_vault_root, message="chore(obsidian): initialize fixture vault git policy")
    _run_git(["push", "-u", "origin", branch], cwd=fixture_vault_root)
    pushed_commit = _run_git(["rev-parse", "HEAD"], cwd=fixture_vault_root).stdout.strip()
    return {
        **report,
        "status": "applied",
        "reason_code": None,
        "branch": branch,
        "approved_refs": [".gitignore"],
        "pushed_commit": pushed_commit,
        "operation_count": int(plan.get("planned_operation_count", 0)),
        "target_vault_git_mutation_performed": True,
        "fixture_remote_push_performed": True,
        "mutation_performed": True,
    }


def execute_obsidian_git_sync_in_fixture(
    *,
    plan: dict[str, Any],
    fixture_vault_root: Path,
    fixture_remote_root: Path,
    fixture_git_only: bool,
) -> dict[str, Any]:
    """Execute an Obsidian Git sync plan against local fixture Git repos only."""

    report = _base_obsidian_git_fixture_execution_report(
        plan=plan,
        operation="sync",
        fixture_vault_root=fixture_vault_root,
        fixture_remote_root=fixture_remote_root,
        fixture_git_only=fixture_git_only,
    )
    blocked = _obsidian_git_fixture_execution_blocker(plan=plan, fixture_vault_root=fixture_vault_root, fixture_remote_root=fixture_remote_root, fixture_git_only=fixture_git_only)
    if blocked:
        return {**report, "status": "blocked", "reason_code": blocked}
    if plan.get("schema_id") != "hisys.obsidian.git_sync_plan" or plan.get("status") != "planned_after_vault_write":
        return {**report, "status": "blocked", "reason_code": "sync_plan_required"}
    push_op = _push_operation(plan)
    if not push_op.get("approval_ref"):
        return {**report, "status": "blocked", "reason_code": "approval_ref_required"}
    if not (fixture_vault_root / ".git").exists():
        return {**report, "status": "blocked", "reason_code": "fixture_git_repo_required"}
    if not fixture_remote_root.exists():
        return {**report, "status": "blocked", "reason_code": "fixture_remote_required"}

    refs = [str(ref) for ref in [*plan.get("memo_refs", []), *plan.get("runtime_boundary_refs", [])]]
    try:
        _validate_refs(refs)
    except ValueError:
        return {**report, "status": "blocked", "reason_code": "unsafe_vault_ref"}
    missing_refs = [ref for ref in refs if not (fixture_vault_root / ref).exists()]
    if missing_refs:
        return {**report, "status": "blocked", "reason_code": "approved_ref_missing_from_fixture_vault", "missing_refs": missing_refs}

    _run_git(["config", "user.email", "hisys-fixture@example.invalid"], cwd=fixture_vault_root)
    _run_git(["config", "user.name", "Hisys Fixture Executor"], cwd=fixture_vault_root)
    _ensure_origin(fixture_vault_root=fixture_vault_root, fixture_remote_root=fixture_remote_root)
    _run_git(["add", *refs], cwd=fixture_vault_root)
    commit_created = _commit_if_needed(fixture_vault_root=fixture_vault_root, message=str(plan.get("commit_message") or "chore(obsidian): sync fixture vault"))
    branch = str(plan.get("branch") or push_op.get("branch") or "main")
    _run_git(["push", "origin", branch], cwd=fixture_vault_root)
    pushed_commit = _run_git(["rev-parse", "HEAD"], cwd=fixture_vault_root).stdout.strip()
    return {
        **report,
        "status": "applied",
        "reason_code": None,
        "branch": branch,
        "approved_refs": refs,
        "commit_created": commit_created,
        "pushed_commit": pushed_commit,
        "operation_count": int(plan.get("planned_operation_count", 0)),
        "target_vault_git_mutation_performed": True,
        "fixture_remote_push_performed": True,
        "mutation_performed": True,
    }


def write_obsidian_git_fixture_execution_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"obsidian-git-fixture-execution-{report['operation']}-{report['request_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"obsidian-git-fixture-execution-{report['operation']}-{report['request_id']}.md").write_text(_format_obsidian_git_fixture_execution_report(report), encoding="utf-8")
    return report_path


def _base_obsidian_git_fixture_execution_report(
    *,
    plan: dict[str, Any],
    operation: str,
    fixture_vault_root: Path,
    fixture_remote_root: Path,
    fixture_git_only: bool,
) -> dict[str, Any]:
    return {
        "schema_id": "hisys.obsidian.git_fixture_execution_report",
        "schema_version": _SCHEMA_VERSION,
        "request_id": str(plan.get("request_id", "unknown")),
        "operation": operation,
        "fixture_git_only": fixture_git_only,
        "fixture_vault_root": str(fixture_vault_root),
        "fixture_remote_root": str(fixture_remote_root),
        "credential_ref": plan.get("credential_ref"),
        "credential_ref_resolved": False,
        "target_vault_git_mutation_performed": False,
        "fixture_remote_push_performed": False,
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def _obsidian_git_fixture_execution_blocker(*, plan: dict[str, Any], fixture_vault_root: Path, fixture_remote_root: Path, fixture_git_only: bool) -> str | None:
    if not fixture_git_only:
        return "fixture_git_only_required"
    if _is_real_obsidian_vault(fixture_vault_root) or _is_real_obsidian_vault(fixture_remote_root):
        return "real_obsidian_vault_blocked"
    if plan.get("status") == "blocked":
        return str(plan.get("reason_code") or "plan_blocked")
    for operation in plan.get("planned_operations", []):
        if operation.get("requires_approval") and not operation.get("approval_ref"):
            return "approval_ref_required"
    return None


def _push_operation(plan: dict[str, Any]) -> dict[str, Any]:
    for operation in plan.get("planned_operations", []):
        if operation.get("operation") in {"initial_commit_and_push", "push_commit_to_remote"}:
            return operation
    return {}


def _ensure_git_repo(*, fixture_vault_root: Path, branch: str) -> None:
    if not (fixture_vault_root / ".git").exists():
        _run_git(["init", "-b", branch], cwd=fixture_vault_root)


def _ensure_origin(*, fixture_vault_root: Path, fixture_remote_root: Path) -> None:
    remote_url = str(fixture_remote_root)
    remotes = _run_git(["remote"], cwd=fixture_vault_root).stdout.splitlines()
    if "origin" not in remotes:
        _run_git(["remote", "add", "origin", remote_url], cwd=fixture_vault_root)
    else:
        _run_git(["remote", "set-url", "origin", remote_url], cwd=fixture_vault_root)


def _commit_if_needed(*, fixture_vault_root: Path, message: str) -> bool:
    staged = _run_git(["diff", "--cached", "--quiet"], cwd=fixture_vault_root, check=False)
    if staged.returncode == 0:
        return False
    _run_git(["commit", "-m", message], cwd=fixture_vault_root)
    return True


def _run_git(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def _lightweight_obsidian_gitignore() -> str:
    return "\n".join(
        [
            "# Hisys lightweight Obsidian vault policy",
            ".obsidian/workspace*",
            "attachments/",
            "*.pdf",
            "*.zip",
            "*.tmp",
            ".DS_Store",
            "",
        ]
    )


def _format_obsidian_git_fixture_execution_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Obsidian Git Fixture Execution Report",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Operation: `{report['operation']}`",
            f"- Status: {report['status']}",
            f"- Reason: {report.get('reason_code')}",
            f"- fixture_git_only: {str(report['fixture_git_only']).lower()}",
            f"- target_vault_git_mutation_performed: {str(report['target_vault_git_mutation_performed']).lower()}",
            f"- fixture_remote_push_performed: {str(report['fixture_remote_push_performed']).lower()}",
            f"- real_obsidian_vault_write_performed: {str(report['real_obsidian_vault_write_performed']).lower()}",
            f"- external_call_made: {str(report['external_call_made']).lower()}",
            "",
        ]
    )


def _git_credential_issue(credential_ref: str) -> str | None:
    stripped = credential_ref.strip()
    if not stripped:
        return "credential_ref_required"
    if re.search(r"\b(?:ghp|github_pat|sk|xox[baprs]|hf)_[A-Za-z0-9][A-Za-z0-9_-]{8,}\b|\bsk-[A-Za-z0-9][A-Za-z0-9_-]{8,}\b", stripped):
        return "raw_credential_value_not_allowed"
    if not _GIT_CREDENTIAL_REF_RE.fullmatch(stripped):
        return "credential_ref_scheme_not_allowed"
    return None


def _missing_git_sync_field(
    refs: list[str],
    commit_message: str,
    remote_name: str,
    branch: str,
    approval_ref: str | None,
) -> str | None:
    if not refs:
        return "refs_required"
    if not commit_message.strip():
        return "commit_message_required"
    if not remote_name.strip():
        return "remote_name_required"
    if not branch.strip():
        return "branch_required"
    if not approval_ref:
        return "approval_ref_required"
    return None


def _blocked_obsidian_git_plan(
    *,
    schema_id: str,
    request_id: str,
    reason_code: str,
    vault_root: Path,
    credential_ref: str,
) -> dict[str, Any]:
    return {
        "schema_id": schema_id,
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "blocked",
        "reason_code": reason_code,
        "vault_root": str(vault_root),
        "credential_ref": credential_ref if reason_code != "raw_credential_value_not_allowed" else "redacted_raw_credential_ref_rejected",
        "raw_credential_stored": False,
        "planned_operation_count": 0,
        "planned_operations": [],
        "mutation_performed": False,
        "external_call_made": False,
    }


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


def build_obsidian_evidence_promotion_plan(*, request: dict[str, Any]) -> dict[str, Any]:
    """Plan promotion of investigation evidence refs into topic canonical indexes."""

    request_id = str(request["request_id"])
    topic_uid = str(request["topic_uid"])
    topic_slug = str(request["topic_slug"])
    approval_ref = request.get("approval_ref")
    topic_root = f"91 Hisys/Live Research/topics/{topic_uid}__{topic_slug}"
    promotion_refs = {
        "source_refs": list(request.get("source_refs", [])),
        "evidence_refs": list(request.get("evidence_refs", [])),
        "claim_refs": list(request.get("claim_refs", [])),
        "decision_refs": list(request.get("decision_refs", [])),
    }
    _validate_refs([ref for refs in promotion_refs.values() for ref in refs])
    operations = [
        {"operation_id": "evidence-promotion-op-0001", "operation": "update_source_index", "vault_relative_ref": f"{topic_root}/canonical/sources/source-index.json", "source_refs": promotion_refs["source_refs"]},
        {"operation_id": "evidence-promotion-op-0002", "operation": "update_evidence_index", "vault_relative_ref": f"{topic_root}/canonical/evidence/evidence-index.json", "evidence_refs": promotion_refs["evidence_refs"]},
        {"operation_id": "evidence-promotion-op-0003", "operation": "update_claim_index", "vault_relative_ref": f"{topic_root}/canonical/claims/claim-index.json", "claim_refs": promotion_refs["claim_refs"]},
        {"operation_id": "evidence-promotion-op-0004", "operation": "update_decision_index", "vault_relative_ref": f"{topic_root}/canonical/decisions/decision-index.json", "decision_refs": promotion_refs["decision_refs"]},
        {"operation_id": "evidence-promotion-op-0005", "operation": "write_promotion_manifest", "vault_relative_ref": f"{topic_root}/canonical/evidence/evidence-promotion-{request_id}.json", "promotion_request_id": request_id},
    ]
    return {
        "schema_id": "hisys.obsidian.evidence_promotion_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "planned_not_executed",
        "topic_uid": topic_uid,
        "topic_slug": topic_slug,
        "investigation_id": request.get("investigation_id"),
        "approval_ref": approval_ref,
        "promotion_refs": promotion_refs,
        "promotion_plan_only": True,
        "planned_operation_count": len(operations),
        "planned_operations": operations,
        "external_call_made": False,
        "mutation_performed": False,
        "real_obsidian_vault_write_performed": False,
    }


def write_obsidian_evidence_promotion_plan(*, instance_root: Path, yyyymmdd: str, plan: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"evidence-promotion-plan-{plan['request_id']}.json"
    report_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def rehearse_obsidian_evidence_promotion_in_fixture(*, promotion_plan: dict[str, Any], fixture_vault_root: Path, approval_ref: str | None, fixture_vault_only: bool) -> dict[str, Any]:
    if _is_real_obsidian_vault(fixture_vault_root) or not approval_ref or not fixture_vault_only:
        return {"schema_id": "hisys.obsidian.evidence_promotion_rehearsal", "schema_version": _SCHEMA_VERSION, "status": "blocked", "reason_code": "fixture_rehearsal_gate_not_satisfied", "operation_count": 0, "external_call_made": False, "mutation_performed": False, "real_obsidian_vault_write_performed": False}
    refs = [str(op.get("vault_relative_ref", "")) for op in promotion_plan.get("planned_operations", [])]
    _validate_refs(refs)
    written = []
    for op, ref in zip(promotion_plan.get("planned_operations", []), refs, strict=True):
        target = fixture_vault_root / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "obsidian_evidence_promotion_projection_only": True,
            "source_promotion_request_id": promotion_plan.get("request_id"),
            "source_operation_id": op.get("operation_id"),
            "operation": op.get("operation"),
            "vault_relative_ref": ref,
            "promotion_refs": promotion_plan.get("promotion_refs", {}),
            "approval_ref": approval_ref,
            "real_obsidian_vault_write_performed": False,
        }
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append({"operation_id": str(op.get("operation_id")), "vault_relative_ref": ref})
    return {"schema_id": "hisys.obsidian.evidence_promotion_rehearsal", "schema_version": _SCHEMA_VERSION, "status": "rehearsed_fixture_only", "source_promotion_request_id": promotion_plan.get("request_id"), "operation_count": len(written), "written_fixture_refs": written, "external_call_made": False, "mutation_performed": True, "real_obsidian_vault_write_performed": False}


def _topic_tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _score_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return round(len(left & right) / len(left | right), 3)


def build_topic_gatekeeper_decision(*, request_id: str, proposed_topic: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Build an evidence-citing topic routing decision without vault mutation."""

    topics = list(registry.get("topics", []))
    proposed_title = str(proposed_topic.get("title") or proposed_topic.get("topic_slug") or "untitled-topic")
    proposed_slug = str(proposed_topic.get("topic_slug") or re.sub(r"[^a-z0-9]+", "-", proposed_title.lower()).strip("-") or "untitled-topic")
    proposed_tokens = _topic_tokens(f"{proposed_title} {proposed_slug}")
    proposed_sources = set(proposed_topic.get("source_ids", []))
    proposed_claims = set(proposed_topic.get("claim_ids", []))
    proposed_groups = set(proposed_topic.get("groups", []))
    best: dict[str, Any] | None = None
    best_total = -1.0
    best_scores: dict[str, dict[str, Any]] = {}
    best_semantic = 0.0
    for topic in topics:
        existing_tokens = _topic_tokens(" ".join([str(topic.get("title", "")), str(topic.get("topic_slug", "")), " ".join(topic.get("aliases", []))]))
        semantic = _score_overlap(proposed_tokens, existing_tokens)
        source = _score_overlap(proposed_sources, set(topic.get("source_ids", [])))
        claim = _score_overlap(proposed_claims, set(topic.get("claim_ids", [])))
        group = _score_overlap(proposed_groups, set(topic.get("groups", [])))
        governance = 1.0
        total = round((semantic * 0.4) + (source * 0.25) + (claim * 0.25) + (group * 0.05) + (governance * 0.05), 3)
        if total > best_total:
            best = topic
            best_total = total
            best_semantic = semantic
            ref = str(topic.get("vault_relative_ref") or "registry.json")
            best_scores = {
                "semantic_similarity": {"value": semantic, "evidence_refs": [f"{ref}#title"]},
                "source_overlap": {"value": source, "evidence_refs": [f"{ref}#source_ids"]},
                "claim_overlap": {"value": claim, "evidence_refs": [f"{ref}#claim_ids"]},
                "group_affinity": {"value": group, "evidence_refs": [f"{ref}#groups"]},
                "governance_compatibility": {"value": governance, "evidence_refs": [f"{ref}#policy"]},
            }
    if best is None:
        action = "new_topic"
        target_uid = None
        best_scores = {
            "semantic_similarity": {"value": 0.0, "evidence_refs": ["registry.json#topics"]},
            "source_overlap": {"value": 0.0, "evidence_refs": ["registry.json#topics"]},
            "claim_overlap": {"value": 0.0, "evidence_refs": ["registry.json#topics"]},
            "group_affinity": {"value": 0.0, "evidence_refs": ["registry.json#groups"]},
            "governance_compatibility": {"value": 1.0, "evidence_refs": ["registry.json#policy"]},
        }
    else:
        target_uid = best.get("topic_uid")
        if best_semantic >= 0.45 or best_total >= 0.55:
            action = "same_as_existing_topic"
        elif best_total >= 0.4:
            action = "merge_with_existing_topic"
        elif best_total >= 0.25:
            action = "group_with_existing_topic"
        elif best_total >= 0.1:
            action = "related_to_existing_topic"
        else:
            action = "new_topic"
            target_uid = None
    requires_human = action in {"merge_with_existing_topic", "group_with_existing_topic", "split_topic_recommended"}
    return {
        "schema_id": "hisys.obsidian.topic_gatekeeper_decision",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "proposed_topic": proposed_topic,
        "decision": {"action": action, "target_topic_uid": target_uid, "proposed_topic_slug": proposed_slug, "requires_human_approval": requires_human, "approval_ref": None},
        "scores": best_scores,
        "policy": {"canonical_topics_do_not_move": True, "groups_are_overlays": True, "no_topic_merge_without_human_approval": True},
        "external_call_made": False,
        "mutation_performed": False,
        "real_obsidian_vault_write_performed": False,
    }


def write_topic_gatekeeper_decision(*, instance_root: Path, yyyymmdd: str, decision: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"topic-gatekeeper-decision-{decision['request_id']}.json"
    report_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def build_topic_gatekeeper_approval_package(*, request_id: str, decision: dict[str, Any], approval_ref: str | None) -> dict[str, Any]:
    action = decision.get("decision", {}).get("action")
    return {
        "schema_id": "hisys.obsidian.topic_gatekeeper_approval_package",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "source_decision_request_id": decision.get("request_id"),
        "status": "approval_packaged",
        "decision_action": action,
        "approval_ref": approval_ref,
        "requires_human_approval": True,
        "planned_outcome": "route_or_create_topic_after_approval",
        "decision": decision,
        "external_call_made": False,
        "mutation_performed": False,
        "real_obsidian_vault_write_performed": False,
    }


def build_topic_gatekeeper_transaction_plan(*, request_id: str, approval_package: dict[str, Any]) -> dict[str, Any]:
    decision = approval_package.get("decision", {})
    decision_payload = decision.get("decision", {})
    slug = decision_payload.get("proposed_topic_slug") or "untitled-topic"
    target = decision_payload.get("target_topic_uid") or f"TOPIC-PLANNED-000000__{slug}"
    base = f"91 Hisys/Live Research/topics/{target}"
    ops = [
        {"operation_id": "topic-gatekeeper-op-0001", "operation": "write", "vault_relative_ref": "91 Hisys/Live Research/registry.json"},
        {"operation_id": "topic-gatekeeper-op-0002", "operation": "write", "vault_relative_ref": f"{base}/topic-manifest.json"},
        {"operation_id": "topic-gatekeeper-op-0003", "operation": "write", "vault_relative_ref": f"{base}/runtime-boundary/topic-gatekeeper/{request_id}.json"},
    ]
    return {
        "schema_id": "hisys.obsidian.topic_gatekeeper_transaction_plan",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "planned_not_executed",
        "source_approval_package_request_id": approval_package.get("request_id"),
        "planned_operation_count": len(ops),
        "planned_operations": ops,
        "approval_ref": approval_package.get("approval_ref"),
        "external_call_made": False,
        "mutation_performed": False,
        "real_obsidian_vault_write_performed": False,
    }


def rehearse_topic_gatekeeper_transaction_in_fixture(*, transaction_plan: dict[str, Any], fixture_vault_root: Path, approval_ref: str | None, fixture_vault_only: bool) -> dict[str, Any]:
    if _is_real_obsidian_vault(fixture_vault_root) or not approval_ref or not fixture_vault_only:
        return {"schema_id": "hisys.obsidian.topic_gatekeeper_rehearsal", "schema_version": _SCHEMA_VERSION, "status": "blocked", "reason_code": "fixture_rehearsal_gate_not_satisfied", "operation_count": 0, "mutation_performed": False, "external_call_made": False, "real_obsidian_vault_write_performed": False}
    refs = [str(op.get("vault_relative_ref", "")) for op in transaction_plan.get("planned_operations", [])]
    _validate_refs(refs)
    written = []
    for op, ref in zip(transaction_plan.get("planned_operations", []), refs, strict=True):
        target = fixture_vault_root / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {"topic_gatekeeper_projection_only": True, "source_transaction_request_id": transaction_plan.get("request_id"), "source_operation_id": op.get("operation_id"), "vault_relative_ref": ref, "approval_ref": approval_ref, "real_obsidian_vault_write_performed": False}
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append({"operation_id": str(op.get("operation_id")), "vault_relative_ref": ref})
    return {"schema_id": "hisys.obsidian.topic_gatekeeper_rehearsal", "schema_version": _SCHEMA_VERSION, "status": "rehearsed_fixture_only", "source_transaction_request_id": transaction_plan.get("request_id"), "operation_count": len(written), "written_fixture_refs": written, "mutation_performed": True, "external_call_made": False, "real_obsidian_vault_write_performed": False}


def build_topic_gatekeeper_status_report(*, request_id: str) -> dict[str, Any]:
    stages = [
        {"stage": "Topic-Gatekeeper-A", "capability": "decision", "status": "complete"},
        {"stage": "Topic-Gatekeeper-B", "capability": "approval_package", "status": "complete"},
        {"stage": "Topic-Gatekeeper-C", "capability": "transaction_plan", "status": "complete"},
        {"stage": "Topic-Gatekeeper-D", "capability": "fixture_rehearsal", "status": "complete"},
        {"stage": "Topic-Gatekeeper-E", "capability": "completion_status", "status": "complete"},
    ]
    return {"schema_id": "hisys.obsidian.topic_gatekeeper_status", "schema_version": _SCHEMA_VERSION, "request_id": request_id, "status": "complete", "topic_gatekeeper_complete": True, "completed_stage_count": len(stages), "open_stage_count": 0, "stages": stages, "external_call_made": False, "mutation_performed": False, "real_obsidian_vault_write_performed": False}


def build_obsidian_milestone_status_report(*, request_id: str) -> dict[str, Any]:
    """Build the overall Obsidian milestone completion report."""

    milestones = [
        {
            "milestone": "Live-Obsidian-Config",
            "status": "complete",
            "capabilities": [
                "vault planning/validation/templates",
                "fixture apply/roundtrip",
                "live preflight/approval/gate/transaction/apply boundary",
                "completion status",
            ],
        },
        {
            "milestone": "Topic-Gatekeeper",
            "status": "complete",
            "capabilities": [
                "evidence-citing routing decision",
                "approval package",
                "transaction plan",
                "fixture rehearsal",
            ],
        },
        {
            "milestone": "Obsidian-Evidence-Promotion",
            "status": "complete",
            "capabilities": [
                "explicit evidence promotion plan",
                "fixture rehearsal projection only",
            ],
        },
        {
            "milestone": "Obsidian-Git-Management",
            "status": "complete",
            "capabilities": [
                "credential-ref-only initialization and sync plans",
                "fixture-only Git initialization and sync executor",
                "runtime-boundary Git execution evidence",
            ],
        },
    ]
    open_items = [item for item in milestones if item["status"] != "complete"]
    return {
        "schema_id": "hisys.obsidian.milestone_status",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "complete" if not open_items else "incomplete",
        "obsidian_milestone_complete": not open_items,
        "completed_milestone_count": len(milestones) - len(open_items),
        "open_milestone_count": len(open_items),
        "milestones": milestones,
        "external_call_made": False,
        "mutation_performed": False,
        "real_obsidian_vault_write_performed": False,
    }


def write_obsidian_milestone_status_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"obsidian-milestone-status-{report['request_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def build_live_obsidian_config_status_report(*, request_id: str) -> dict[str, Any]:
    """Build the Live-Obsidian-Config completion status report."""

    stage_defs = [
        ("A", "scaffold obsidian live research config", "docs/use-cases/obsidian-live-research-layout.md", "design_scaffold"),
        ("B", "vault dry-run planner", "vault-plan", "planner"),
        ("C", "vault manifest validator", "vault-validate", "validator"),
        ("D", "memo ontology template planner", "vault-template-plan", "template_planner"),
        ("E", "validator hardening", "vault-validate", "validator_hardening"),
        ("F", "fixture vault apply", "vault-apply", "fixture_writer"),
        ("G", "topic transition plan", "vault-topic-transition-plan", "transition_planner"),
        ("H", "fixture roundtrip validation", "vault-roundtrip-validate", "roundtrip_validator"),
        ("I", "live vault preflight", "vault-live-preflight", "preflight_no_write"),
        ("J", "live vault approval package", "vault-live-approval-package", "approval_package"),
        ("K", "live vault write gate", "vault-live-write-gate", "write_gate"),
        ("L", "live vault transaction plan", "vault-live-transaction-plan", "transaction_plan"),
        ("M", "fixture transaction rehearsal", "vault-live-transaction-rehearse", "fixture_rehearsal"),
        ("N", "approved transaction apply", "vault-live-transaction-apply", "approval_gated_writer_boundary"),
        ("O", "completion status report", "vault-live-config-status", "completion_gate"),
    ]
    stages = [
        {"increment": f"Live-Obsidian-Config-{letter}", "title": title, "command": command, "capability": capability, "status": "complete"}
        for letter, title, command, capability in stage_defs
    ]
    return {
        "schema_id": "hisys.obsidian.live_config_status",
        "schema_version": _SCHEMA_VERSION,
        "request_id": request_id,
        "status": "complete",
        "live_obsidian_config_complete": True,
        "completed_stage_count": len(stages),
        "open_stage_count": 0,
        "stages": stages,
        "remaining_live_action": "operator may run vault-live-transaction-apply against /home/cbchoi/obsidian only with explicit approval and --allow-real-obsidian-vault",
        "real_obsidian_vault_write_performed": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def write_live_obsidian_config_status_report(*, instance_root: Path, yyyymmdd: str, report: dict[str, Any]) -> Path:
    report_dir = instance_root / "runtime-boundary" / "obsidian-live" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"vault-live-config-status-{report['request_id']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (report_dir / f"vault-live-config-status-{report['request_id']}.md").write_text(_format_live_obsidian_config_status(report), encoding="utf-8")
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


def _format_live_obsidian_config_status(report: dict[str, Any]) -> str:
    stages = "\n".join(f"- {stage['increment']}: {stage['title']} (`{stage['command']}`)" for stage in report.get("stages", []))
    return "\n".join(
        [
            "# Live-Obsidian-Config Status",
            "",
            f"- Request: `{report['request_id']}`",
            f"- Status: {report['status']}",
            f"- Completed stages: {report['completed_stage_count']}",
            f"- Open stages: {report['open_stage_count']}",
            f"- Real Obsidian vault write performed: {str(report['real_obsidian_vault_write_performed']).lower()}",
            "",
            "## Stages",
            stages,
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
    "build_live_obsidian_config_status_report",
    "build_live_vault_approval_package",
    "build_live_vault_preflight_report",
    "build_live_vault_transaction_plan",
    "build_live_vault_write_gate_report",
    "build_obsidian_evidence_promotion_plan",
    "build_obsidian_git_initialization_plan",
    "build_obsidian_git_sync_plan",
    "build_obsidian_milestone_status_report",
    "execute_obsidian_git_initialization_in_fixture",
    "execute_obsidian_git_sync_in_fixture",
    "build_topic_gatekeeper_approval_package",
    "build_topic_gatekeeper_decision",
    "build_topic_gatekeeper_status_report",
    "build_topic_gatekeeper_transaction_plan",
    "build_topic_identity_transition_plan",
    "build_vault_plan",
    "build_vault_template_plan",
    "rehearse_live_vault_transaction_in_fixture",
    "rehearse_obsidian_evidence_promotion_in_fixture",
    "rehearse_topic_gatekeeper_transaction_in_fixture",
    "validate_fixture_vault_roundtrip",
    "validate_vault_manifests",
    "write_live_obsidian_config_status_report",
    "write_live_vault_approval_package",
    "write_vault_apply_report",
    "write_live_vault_preflight_report",
    "write_live_vault_transaction_apply_report",
    "write_live_vault_transaction_plan",
    "write_live_vault_transaction_rehearsal_report",
    "write_live_vault_write_gate_report",
    "write_obsidian_evidence_promotion_plan",
    "write_obsidian_git_fixture_execution_report",
    "write_obsidian_milestone_status_report",
    "write_topic_gatekeeper_decision",
    "write_vault_plan_artifacts",
    "write_vault_roundtrip_report",
    "write_vault_template_plan_artifacts",
    "write_vault_validation_report",
    "write_topic_identity_transition_plan",
]
