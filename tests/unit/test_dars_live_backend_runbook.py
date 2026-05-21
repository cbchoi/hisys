"""M-DARS-BE-4 local backend smoke runbook documentation tests.

The runbook must preserve advisory-only / fail-closed semantics for a real
local-model boundary call. These tests are smoke tests for the runbook
contract; they never start a model runner, contact a remote endpoint, or
look up credentials.

Traceability: M-DARS-BE-4, docs/plans/dars-live-backend-implementation-plan.md.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "runbooks" / "dars-live-backend-localhost-smoke.md"
EXAMPLE = ROOT / "docs" / "examples" / "dars" / "backend-activation-localhost.example.json"


def test_backend_activation_example_is_secret_free_and_localhost_only() -> None:
    payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert payload["endpoint_scope"] == "localhost_only"
    assert payload["allowed_actions"] == "advisory_only"
    assert payload["human_approved"] is True
    assert payload["approval_ref"].startswith("APPROVAL-DARS-BE-")
    forbidden_keys = {"api_key", "token", "secret", "password", "credential"}
    assert not (set(payload.keys()) & forbidden_keys)
    for value in payload.values():
        assert not (
            isinstance(value, str)
            and (value.startswith("sk-") or value.startswith("ghp_"))
        )


def test_backend_localhost_smoke_runbook_requires_operator_supplied_localhost_endpoint() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "operator-supplied localhost endpoint" in text
    assert "already-running localhost-only model endpoint" in text
    assert "HISYS_DARS_LOCAL_ENDPOINT" in text
    assert "http://127.0.0.1:<port>/v1/chat/completions" in text
    assert "--backend-activation-packet" in text


def test_backend_localhost_smoke_runbook_preserves_stop_conditions_and_boundaries() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    required_phrases = [
        "Do not run this procedure unless the operator has already started the model runner",
        "non-loopback endpoint",
        "missing activation packet",
        "credential requirement",
        "tool/search/browser permission",
        "mutation request",
        "failed secret scan",
        "human uncertainty",
        "external_call_made=false",
        "mutation_performed=false",
        "publication_performed=false",
        "allowed_actions=advisory_only",
        "No credential lookup",
        "No remote API",
        "No Authorization header",
        "Remote providers are not covered",
    ]
    for phrase in required_phrases:
        assert phrase in text, f"missing required phrase: {phrase!r}"


def test_backend_localhost_smoke_runbook_is_traceable_to_implementation_increments() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    for increment in ("M-DARS-BE-1", "M-DARS-BE-2", "M-DARS-BE-3", "M-DARS-BE-4"):
        assert increment in text
    assert "tests/unit/test_dars_backend_activation.py" in text
    assert "tests/unit/test_dars_runtime.py" in text
    assert "tests/unit/test_dars_backend_boundary.py" in text
