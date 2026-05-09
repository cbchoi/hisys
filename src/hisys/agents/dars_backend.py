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
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        response = DarsResponseEnvelope.model_validate(payload)
        if response.request_id != request_id:
            raise ValueError(f"request_id mismatch: expected {request_id}, got {response.request_id}")
        _write_response(self.instance, yyyymmdd, response)
        return response


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


__all__ = ["DarsFixtureBackend"]
