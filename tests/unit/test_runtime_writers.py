"""Audit writer and Hermes Markdown boundary tests.

Traceability: HISYS-D-015, HISYS-D-016, HISYS-FR-ADM-002,
HISYS-FR-INV-006, HISYS-DATA-005, HISYS-T-005A, HISYS-T-008.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.audit import AuditJsonlWriter
from hisys.config import InstanceRoot
from hisys.integrations import HermesBoundaryWriter
from hisys.schemas import AuditEvent


def test_audit_writer_redacts_secrets_and_appends_jsonl(tmp_path: Path):
    writer = AuditJsonlWriter(InstanceRoot(tmp_path))
    event = AuditEvent(
        audit_id="AUDIT-TEST-001",
        event_type="collection_run",
        actor_id="investigator-test",
        record_refs=["OBS-TEST-001"],
        summary="Collected with token=FAKE_TEST_TOKEN and API_KEY=FAKE_TEST_KEY",
        result="success",
        producer_id="test",
        status="success",
    )

    path = writer.append(event, yyyymmdd="20260508")

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["audit_id"] == "AUDIT-TEST-001"
    assert "FAKE_TEST_TOKEN" not in data["summary"]
    assert "FAKE_TEST_KEY" not in data["summary"]
    assert "[REDACTED]" in data["summary"]


def test_hermes_boundary_writer_creates_markdown_and_schema_ref(tmp_path: Path):
    writer = HermesBoundaryWriter(InstanceRoot(tmp_path))

    ref = writer.write_record(
        yyyymmdd="20260508",
        campaign_id="CAMP-HERMES-001",
        record_kind="prompt",
        stable_id="001",
        title="Prompt record",
        body="Search only approved sources.",
    )

    assert ref == "hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-001/prompt-001.md"
    actual_path = tmp_path / "runtime-boundary" / "hermes" / "20260508" / "CAMP-HERMES-001" / "prompt-001.md"
    text = actual_path.read_text(encoding="utf-8")
    assert "# Prompt record" in text
    assert "Search only approved sources." in text
