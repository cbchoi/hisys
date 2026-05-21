"""DARS backend-boundary decision record tests.

Traceability: M-DARS-BE-3, docs/plans/dars-live-backend-implementation-plan.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.agents.dars_backend_boundary import (
    DARS_BACKEND_BOUNDARY_SCHEMA_ID,
    write_dars_backend_boundary_record,
)
from hisys.config.instance import InstanceRoot


def _record_paths(
    tmp_path: Path,
    *,
    yyyymmdd: str,
    request_id: str,
    backend_id: str,
) -> tuple[Path, Path]:
    base = (
        tmp_path
        / "runtime-boundary"
        / "dars-backends"
        / yyyymmdd
        / request_id
    )
    return base / f"{backend_id}.json", base / f"{backend_id}.md"


def test_backend_boundary_writer_persists_json_and_markdown_pair(tmp_path: Path):
    instance = InstanceRoot(tmp_path)
    json_path, md_path = _record_paths(
        tmp_path,
        yyyymmdd="20260516",
        request_id="EXEC-LOCAL-LLM-001",
        backend_id="local_llm_dars",
    )

    written = write_dars_backend_boundary_record(
        instance,
        yyyymmdd="20260516",
        request_id="EXEC-LOCAL-LLM-001",
        backend_id="local_llm_dars",
        backend_kind="openai_compatible",
        endpoint_scope="localhost_only",
        approval_ref="APPROVAL-DARS-LOCAL-LLM-001",
        activation_ref="/tmp/backend-activation-packet.json",
    )

    assert written.json_path == json_path
    assert written.markdown_path == md_path
    assert json_path.exists()
    assert md_path.exists()


def test_backend_boundary_record_carries_required_fields(tmp_path: Path):
    instance = InstanceRoot(tmp_path)

    write_dars_backend_boundary_record(
        instance,
        yyyymmdd="20260516",
        request_id="EXEC-LOCAL-LLM-002",
        backend_id="local_llm_dars",
        backend_kind="openai_compatible",
        endpoint_scope="localhost_only",
        approval_ref="APPROVAL-DARS-LOCAL-LLM-002",
        activation_ref="/tmp/backend-activation-packet-2.json",
    )

    json_path, _ = _record_paths(
        tmp_path,
        yyyymmdd="20260516",
        request_id="EXEC-LOCAL-LLM-002",
        backend_id="local_llm_dars",
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["schema_id"] == DARS_BACKEND_BOUNDARY_SCHEMA_ID
    assert payload["backend_id"] == "local_llm_dars"
    assert payload["backend_kind"] == "openai_compatible"
    assert payload["endpoint_scope"] == "localhost_only"
    assert payload["approval_ref"] == "APPROVAL-DARS-LOCAL-LLM-002"
    assert payload["activation_ref"] == "/tmp/backend-activation-packet-2.json"
    assert payload["model_boundary_crossed"] is True
    assert payload["local_model_call_made"] is True
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["allowed_actions"] == "advisory_only"
    assert payload["requires_human_review"] is True


def test_backend_boundary_writer_rejects_non_localhost_endpoint_scope(tmp_path: Path):
    instance = InstanceRoot(tmp_path)

    with pytest.raises(ValueError) as exc_info:
        write_dars_backend_boundary_record(
            instance,
            yyyymmdd="20260516",
            request_id="EXEC-LOCAL-LLM-003",
            backend_id="external-openai",
            backend_kind="openai_compatible",
            endpoint_scope="external_api",
            approval_ref="APPROVAL-DARS-EXT",
            activation_ref="/tmp/external-activation.json",
        )

    assert "endpoint_scope" in str(exc_info.value)


def test_backend_boundary_writer_rejects_invalid_date(tmp_path: Path):
    instance = InstanceRoot(tmp_path)

    with pytest.raises(ValueError):
        write_dars_backend_boundary_record(
            instance,
            yyyymmdd="2026-05-16",
            request_id="EXEC-LOCAL-LLM-004",
            backend_id="local_llm_dars",
            backend_kind="openai_compatible",
            endpoint_scope="localhost_only",
            approval_ref="APPROVAL-DARS-LOCAL-LLM-004",
            activation_ref="/tmp/backend-activation-packet-4.json",
        )


def test_runtime_writes_backend_boundary_record_for_openai_compatible(tmp_path: Path):
    """The DarsRuntime must persist the new M-DARS-BE-3 boundary record
    alongside the existing local-llm boundary record.
    """

    from tests.unit.test_dars_runtime import (
        FakeOpenAIServer,
        _seed_local_llm_instance,
        _write_backend_activation_packet,
    )
    from hisys.agents.dars import DarsRuntime

    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-LOCAL-LLM-BE3",
    )

    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(
            tmp_path, endpoint=server.endpoint
        )
        DarsRuntime(instance=instance).run_configured_critique(
            yyyymmdd="20260516",
            source_execution_id=source_execution_id,
            producer_id="dars-local-llm-be3",
            approval_ref="APPROVAL-DARS-LOCAL-LLM-BE3",
            backend_activation_packet_ref=str(activation_packet),
        )

    json_path, md_path = _record_paths(
        tmp_path,
        yyyymmdd="20260516",
        request_id=source_execution_id,
        backend_id="local_llm_dars",
    )
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == DARS_BACKEND_BOUNDARY_SCHEMA_ID
    assert payload["approval_ref"] == "APPROVAL-DARS-LOCAL-LLM-BE3"
    assert payload["activation_ref"] == str(activation_packet)
    assert payload["endpoint_scope"] == "localhost_only"
    assert payload["model_boundary_crossed"] is True
    assert payload["local_model_call_made"] is True
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
