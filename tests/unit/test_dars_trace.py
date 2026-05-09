"""DARS trace-link tests.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-T-024, HISYS-FR-AGT-001..005,
HISYS-FR-INV-001..006, HISYS-FR-MEM-001..005.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.agents.dars_protocol import DarsRequestEnvelope, DarsResponseEnvelope
from hisys.agents.dars_trace import DarsTraceLinker
from hisys.config.instance import InstanceRoot
from tests.unit.test_dars_protocol import _valid_request_payload, _valid_response_payload


def test_dars_trace_linker_records_end_to_end_source_to_critique_path(tmp_path: Path):
    request = DarsRequestEnvelope.model_validate(_valid_request_payload())
    response_payload = _valid_response_payload()
    response_payload["request_id"] = request.request_id
    response_payload["handoff_id"] = request.handoff_id
    response_payload["critique"]["linked_record_refs"] = {
        "sources": ["SRC-001"],
        "memos": ["MEMO-001"],
        "alerts": ["ALERT-001"],
        "handoffs": [request.handoff_id],
        "runtime_boundary": [
            "runtime-boundary/dars/20260509/dars-dispatch-decision-DARSREQ-001.json",
            "runtime-boundary/dars/20260509/dars-response-DARSRESP-001.json",
        ],
    }
    response = DarsResponseEnvelope.model_validate(response_payload)

    link = DarsTraceLinker(instance=InstanceRoot(tmp_path)).write_trace_link(
        yyyymmdd="20260509",
        request=request,
        response=response,
        dispatch_decision_ref="runtime-boundary/dars/20260509/dars-dispatch-decision-DARSREQ-001.json",
        validation_ref="runtime-boundary/dars/20260509/dars-validation-DARSREQ-001.json",
        response_ref="runtime-boundary/dars/20260509/dars-response-DARSRESP-001.json",
    )

    assert link.trace_id == "DARSTRACE-DARSREQ-001"
    assert link.request_id == "DARSREQ-001"
    assert link.response_id == "DARSRESP-001"
    assert link.source_refs == ["SRC-001"]
    assert link.memo_refs == ["MEMO-001"]
    assert link.alert_refs == ["ALERT-001"]
    assert link.trace_complete is True
    assert link.external_call_made is False
    assert link.mutation_performed is False

    trace_path = tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-001.json"
    record = json.loads(trace_path.read_text(encoding="utf-8"))
    assert record["schema_id"] == "hisys.dars.trace_link"
    assert record["trace_complete"] is True
    assert record["runtime_boundary_refs"] == [
        "runtime-boundary/dars/20260509/dars-dispatch-decision-DARSREQ-001.json",
        "runtime-boundary/dars/20260509/dars-validation-DARSREQ-001.json",
        "runtime-boundary/dars/20260509/dars-response-DARSRESP-001.json",
        "runtime-boundary/dars/20260509/request.json",
    ]
    assert (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-001.md").exists()


def test_dars_trace_linker_marks_incomplete_when_core_refs_missing(tmp_path: Path):
    request_payload = _valid_request_payload()
    request_payload["record_refs"]["sources"] = []
    request_payload["record_refs"]["memos"] = []
    request_payload["record_refs"]["alerts"] = []
    request = DarsRequestEnvelope.model_validate(request_payload)
    response_payload = _valid_response_payload()
    response_payload["request_id"] = request.request_id
    response_payload["handoff_id"] = request.handoff_id
    response_payload["critique"]["linked_record_refs"] = {"handoffs": [request.handoff_id]}
    response = DarsResponseEnvelope.model_validate(response_payload)

    link = DarsTraceLinker(instance=InstanceRoot(tmp_path)).write_trace_link(
        yyyymmdd="20260509",
        request=request,
        response=response,
        dispatch_decision_ref="runtime-boundary/dars/20260509/dars-dispatch-decision-DARSREQ-001.json",
        validation_ref="runtime-boundary/dars/20260509/dars-validation-DARSREQ-001.json",
        response_ref="runtime-boundary/dars/20260509/dars-response-DARSRESP-001.json",
    )

    assert link.trace_complete is False
    assert "no source/memo/alert refs" in link.gaps
