"""DARS tag-creation execution decision checks."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-tag-creation-execution-decision-packet-v0.0.104.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.104.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.104.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
TAG_NAME = "v0.0.103"
TAG_TARGET = "ea26df6"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def test_tag_creation_execution_packet_authorizes_only_local_release_tag() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-TAG-CREATION-EXECUTION-DECISION-PACKET" in text
    assert "accepted_claim=release_tag_creation_executed_for_local_repository_only" in text
    assert "operator_instruction=실행" in text
    assert "selected_action_set=tag_creation_only" in text
    assert "tag_name=v0.0.103" in text
    assert "tag_target_commit=ea26df6" in text
    assert "tag_kind=annotated" in text
    assert "tag_creation_authorized=true" in text
    assert "tag_creation_performed=true" in text
    assert "tag_push_authorized=false" in text
    assert "tag_push_performed=false" in text


def test_tag_creation_execution_keeps_non_tag_actions_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_authorized=false",
        "deployment_authorized=false",
        "publication_authorized=false",
        "external_notification_authorized=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "standing_unattended_approval_activated=false",
        "human_review_removal_authorized=false",
        "package_upload_performed=false",
        "deployment_performed=false",
        "publication_performed=false",
        "external_notification_performed=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_local_git_tag_exists_and_points_to_approved_target() -> None:
    assert _git("rev-parse", f"{TAG_NAME}^{{commit}}") == _git("rev-parse", TAG_TARGET)
    assert _git("cat-file", "-t", TAG_NAME) == "tag"
    assert "DARS tag creation executed for local repository only" in _git("tag", "-l", TAG_NAME, "--format=%(contents)")


def test_tag_creation_execution_notes_record_traceability_and_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Local annotated Git tag `v0.0.103` created at `ea26df6`" in notes
    assert "accepted_claim=release_tag_creation_executed_for_local_repository_only" in record
    assert "tag_creation_authorized: true" in record
    assert "tag_creation_performed: true" in record
    assert "tag_push_authorized: false" in record
    assert "tag_push_performed: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-TAG-PUSH-AUTHORIZATION-PACKET" in record
    assert "DARS-LIVE-RELEASE-TAG-CREATION-EXECUTION-DECISION-PACKET — local tag created" in trace
    assert "`tag_push_performed=false`" in trace
