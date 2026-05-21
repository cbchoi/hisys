"""DARS backend-boundary decision record writer.

M-DARS-BE-3 persists a backend-level decision record under
``runtime-boundary/dars-backends/<YYYYMMDD>/<REQUEST_ID>/<BACKEND_ID>.{json,md}``
so audit consumers can see backend-boundary crossings separately from panel
task records and dispatch-decision records.

Traceability: docs/plans/dars-live-backend-implementation-plan.md (M-DARS-BE-3).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ..config.instance import InstanceRoot


DARS_BACKEND_BOUNDARY_SCHEMA_ID = "hisys.dars.backend_boundary"
DARS_BACKEND_BOUNDARY_SCHEMA_VERSION = "0.1.0"

_DATE_RE = re.compile(r"^\d{8}$")
_ALLOWED_ENDPOINT_SCOPE = "localhost_only"


@dataclass(frozen=True)
class DarsBackendBoundaryRecord:
    json_path: Path
    markdown_path: Path


def write_dars_backend_boundary_record(
    instance: InstanceRoot,
    *,
    yyyymmdd: str,
    request_id: str,
    backend_id: str,
    backend_kind: str,
    endpoint_scope: str,
    approval_ref: str,
    activation_ref: str,
) -> DarsBackendBoundaryRecord:
    """Persist a backend-level boundary decision JSON/Markdown pair.

    The writer carries advisory-only semantics: ``mutation_performed``,
    ``external_call_made``, and ``publication_performed`` are always ``false``
    and ``allowed_actions`` is always ``advisory_only``. The writer performs
    no HTTP call, no model call, no credential lookup, no remote action.
    """

    if not _DATE_RE.match(yyyymmdd):
        raise ValueError(f"invalid date partition: {yyyymmdd!r}; expected YYYYMMDD")
    if endpoint_scope != _ALLOWED_ENDPOINT_SCOPE:
        raise ValueError(
            "endpoint_scope must be 'localhost_only' for M-DARS-BE-3 backend"
            " boundary records; remote dispatch is fail-closed preparation only"
        )

    output_dir = (
        instance.runtime_boundary_dir
        / "dars-backends"
        / yyyymmdd
        / request_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_id": DARS_BACKEND_BOUNDARY_SCHEMA_ID,
        "schema_version": DARS_BACKEND_BOUNDARY_SCHEMA_VERSION,
        "request_id": request_id,
        "backend_id": backend_id,
        "backend_kind": backend_kind,
        "endpoint_scope": endpoint_scope,
        "approval_ref": approval_ref,
        "activation_ref": activation_ref,
        "model_boundary_crossed": True,
        "local_model_call_made": True,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "allowed_actions": "advisory_only",
        "requires_human_review": True,
        "policy_refs": [
            "HISYS-FR-AGT-001",
            "HISYS-FR-AGT-003",
            "HISYS-CON-010",
            "HISYS-CON-012",
        ],
    }

    json_path = output_dir / f"{backend_id}.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    markdown_path = output_dir / f"{backend_id}.md"
    markdown_path.write_text(
        _render_markdown(payload),
        encoding="utf-8",
    )

    return DarsBackendBoundaryRecord(json_path=json_path, markdown_path=markdown_path)


def _render_markdown(payload: dict[str, object]) -> str:
    lines = [
        f"# DARS backend boundary — {payload['backend_id']}",
        "",
        f"- schema_id: {payload['schema_id']}",
        f"- schema_version: {payload['schema_version']}",
        f"- request_id: {payload['request_id']}",
        f"- backend_id: {payload['backend_id']}",
        f"- backend_kind: {payload['backend_kind']}",
        f"- endpoint_scope: {payload['endpoint_scope']}",
        f"- approval_ref: {payload['approval_ref']}",
        f"- activation_ref: {payload['activation_ref']}",
        f"- model_boundary_crossed: {str(payload['model_boundary_crossed']).lower()}",
        f"- local_model_call_made: {str(payload['local_model_call_made']).lower()}",
        f"- external_call_made: {str(payload['external_call_made']).lower()}",
        f"- mutation_performed: {str(payload['mutation_performed']).lower()}",
        f"- publication_performed: {str(payload['publication_performed']).lower()}",
        f"- allowed_actions: {payload['allowed_actions']}",
        f"- requires_human_review: {str(payload['requires_human_review']).lower()}",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "DARS_BACKEND_BOUNDARY_SCHEMA_ID",
    "DARS_BACKEND_BOUNDARY_SCHEMA_VERSION",
    "DarsBackendBoundaryRecord",
    "write_dars_backend_boundary_record",
]
