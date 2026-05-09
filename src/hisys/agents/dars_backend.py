"""Local DARS backend adapters.

Only deterministic local fixture execution is implemented here. It reads an
approved fixture response, validates it against the canonical DARS response
envelope, persists runtime-boundary artifacts, and performs no external call or
mutation.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-T-019, HISYS-T-020, HISYS-T-024, HISYS-CON-010, HISYS-CON-011,
HISYS-CON-012.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from ..config.instance import InstanceRoot
from .dars_config import DarsBackendConfig
from .dars_dispatch import DarsDispatchDecision
from .dars_protocol import DarsResponseEnvelope


class DarsFixtureBackend:
    """Run a local fixture-file DARS backend after dispatch approval."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def run(
        self,
        *,
        yyyymmdd: str,
        request_id: str,
        backend_config: DarsBackendConfig,
        dispatch_decision: DarsDispatchDecision,
    ) -> DarsResponseEnvelope:
        if dispatch_decision.decision != "allowed":
            raise ValueError("dispatch decision is not allowed")
        if backend_config.kind != "fixture_file":
            raise ValueError("DarsFixtureBackend requires a fixture_file backend")
        if backend_config.external_call_allowed:
            raise ValueError("fixture backend must not request external calls")
        if not backend_config.fixture_path:
            raise ValueError("fixture backend requires fixture_path")

        fixture_path = self.instance.root / backend_config.fixture_path
        try:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
            response = DarsResponseEnvelope.model_validate(payload)
        except (json.JSONDecodeError, OSError, ValidationError) as exc:
            _write_validation_report(
                self.instance,
                yyyymmdd,
                request_id=request_id,
                status="rejected",
                reason_code="invalid_response_envelope",
                issues=[str(exc)],
            )
            raise ValueError("invalid DARS response") from exc
        if response.request_id != request_id:
            _write_validation_report(
                self.instance,
                yyyymmdd,
                request_id=request_id,
                status="rejected",
                reason_code="request_id_mismatch",
                issues=[f"request_id mismatch: expected {request_id}, got {response.request_id}"],
            )
            raise ValueError(f"request_id mismatch: expected {request_id}, got {response.request_id}")
        _write_validation_report(
            self.instance,
            yyyymmdd,
            request_id=request_id,
            status="accepted",
            reason_code="response_valid",
            issues=[],
        )
        _write_response(self.instance, yyyymmdd, response)
        return response


def _write_validation_report(
    instance: InstanceRoot,
    yyyymmdd: str,
    *,
    request_id: str,
    status: str,
    reason_code: str,
    issues: list[str],
) -> None:
    output_dir = instance.runtime_boundary_dir / "dars" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_id": "hisys.dars.validation",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "status": status,
        "reason_code": reason_code,
        "issues": issues,
        "external_call_made": False,
        "mutation_performed": False,
    }
    json_path = output_dir / f"dars-validation-{request_id}.json"
    md_path = output_dir / f"dars-validation-{request_id}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_validation_markdown(payload), encoding="utf-8")


def _validation_markdown(payload: dict) -> str:
    issues = payload.get("issues") or []
    issue_lines = [f"- {issue}" for issue in issues] or ["- none"]
    return "\n".join(
        [
            f"# DARS validation {payload['request_id']}",
            "",
            f"- status: {payload['status']}",
            f"- reason_code: {payload['reason_code']}",
            f"- external_call_made: {payload['external_call_made']}",
            f"- mutation_performed: {payload['mutation_performed']}",
            "",
            "## Issues",
            *issue_lines,
            "",
        ]
    )


def _write_response(instance: InstanceRoot, yyyymmdd: str, response: DarsResponseEnvelope) -> None:
    output_dir = instance.runtime_boundary_dir / "dars" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = response.model_dump(mode="json")
    json_path = output_dir / f"dars-response-{response.response_id}.json"
    md_path = output_dir / f"dars-response-{response.response_id}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_response_markdown(response), encoding="utf-8")


def _response_markdown(response: DarsResponseEnvelope) -> str:
    return "\n".join(
        [
            f"# DARS response {response.response_id}",
            "",
            f"- request_id: {response.request_id}",
            f"- handoff_id: {response.handoff_id}",
            f"- backend_id: {response.producer.backend_id}",
            f"- backend_kind: {response.producer.backend_kind}",
            f"- external_call_made: {response.producer.external_call_made}",
            f"- allowed_actions: {response.boundary.allowed_actions}",
            f"- action_taken: {response.boundary.action_taken}",
            f"- blocks_decision: {response.decision_trace.blocks_decision}",
            "",
            response.critique.critique_summary,
            "",
        ]
    )


class DarsMockEndpointAdapter:
    """Disabled-by-default mock HTTP adapter skeleton.

    This adapter intentionally performs no HTTP/network operation. It exists to
    preserve the future adapter boundary and refuses blocked dispatch decisions.
    """

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def run(
        self,
        *,
        yyyymmdd: str,
        request_id: str,
        backend_config: DarsBackendConfig,
        dispatch_decision: DarsDispatchDecision,
    ) -> DarsResponseEnvelope:
        del yyyymmdd, request_id
        if dispatch_decision.decision != "allowed":
            raise ValueError("dispatch decision is not allowed")
        if backend_config.kind != "mock_http":
            raise ValueError("DarsMockEndpointAdapter requires a mock_http backend")
        raise NotImplementedError("mock endpoint adapter is a disabled-by-default harness boundary")


__all__ = ["DarsFixtureBackend", "DarsMockEndpointAdapter"]
