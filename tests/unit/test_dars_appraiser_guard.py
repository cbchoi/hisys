"""Shared DARS appraiser-separation guard tests.

Increment 3/6 of operational governance: apply ``AppraiserSeparationPolicy``
fail-closed across DARS backends/gates beyond ``dars_dispatch``. These tests
exercise the shared guard module directly and the non-dispatch DARS backend
paths so that a forged ``allowed`` dispatch decision carrying an authority
intent cannot bypass the policy.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-SCHEMA-001, HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.agents.dars_backend import DarsFixtureBackend, DarsMockEndpointAdapter
from hisys.agents.dars_config import DarsConfig
from hisys.agents.dars_dispatch import DarsDispatchDecision
from hisys.config.instance import InstanceRoot
from tests.unit.test_dars_config import _minimal_dars_config


# ---------------------------------------------------------------------------
# Shared guard helper tests
# ---------------------------------------------------------------------------


def test_shared_guard_module_exposes_advisory_and_authority_intents() -> None:
    from hisys.agents import appraiser_separation as guard

    assert "advisory_critique" in guard.ADVISORY_INTENTS
    assert "return_findings" in guard.ADVISORY_INTENTS
    assert "return_recommendations" in guard.ADVISORY_INTENTS
    assert "approve_decision" in guard.AUTHORITY_INTENTS
    assert "execute_action" in guard.AUTHORITY_INTENTS
    assert "publish_output" in guard.AUTHORITY_INTENTS
    assert guard.ADVISORY_INTENTS.isdisjoint(guard.AUTHORITY_INTENTS)
    assert guard.DEFAULT_APPRAISER_POLICY_REF.startswith("APPRAISER-POLICY-")


@pytest.mark.parametrize("intent", ["advisory_critique", "return_findings", "return_recommendations"])
def test_classify_intent_allows_advisory_intents(intent: str) -> None:
    from hisys.agents.appraiser_separation import classify_intent

    verdict = classify_intent(intent)

    assert verdict.decision == "allowed"
    assert verdict.intent == intent
    assert verdict.reason_code == "advisory_intent"


@pytest.mark.parametrize("intent", ["approve_decision", "execute_action", "publish_output"])
def test_classify_intent_blocks_authority_intents(intent: str) -> None:
    from hisys.agents.appraiser_separation import classify_intent

    verdict = classify_intent(intent)

    assert verdict.decision == "blocked"
    assert verdict.intent == intent
    assert verdict.reason_code == "appraiser_separation_policy_violation"
    assert "advisory-only" in verdict.reason.lower()


def test_classify_intent_blocks_unknown_intent_fail_closed() -> None:
    from hisys.agents.appraiser_separation import classify_intent

    verdict = classify_intent("definitely_not_an_advisory_intent")

    assert verdict.decision == "blocked"
    assert verdict.reason_code == "appraiser_separation_policy_violation"


def test_enforce_advisory_intent_raises_for_authority_intent() -> None:
    from hisys.agents.appraiser_separation import (
        AppraiserSeparationViolation,
        enforce_advisory_intent,
    )

    with pytest.raises(AppraiserSeparationViolation) as excinfo:
        enforce_advisory_intent("approve_decision")

    assert excinfo.value.reason_code == "appraiser_separation_policy_violation"
    assert excinfo.value.intent == "approve_decision"


def test_enforce_advisory_intent_returns_verdict_for_advisory_intent() -> None:
    from hisys.agents.appraiser_separation import enforce_advisory_intent

    verdict = enforce_advisory_intent("advisory_critique")

    assert verdict.decision == "allowed"
    assert verdict.intent == "advisory_critique"


# ---------------------------------------------------------------------------
# DarsFixtureBackend fail-closed enforcement (non-dispatch path)
# ---------------------------------------------------------------------------


def _fixture_backend_config() -> DarsConfig:
    data = _minimal_dars_config()
    data["spec"]["backends"]["fixture_file"] = {
        "kind": "fixture_file",
        "enabled": True,
        "mode": "local_only",
        "fixture_path": "harness/fixtures/dars/critique-response.json",
        "external_call_allowed": False,
        "output_contract": "DarsCritiqueRecord",
    }
    return DarsConfig.model_validate(data)


def _forged_allowed_decision(*, intent: str, backend_id: str = "fixture_file", request_id: str = "DARSREQ-FORGED-001") -> DarsDispatchDecision:
    return DarsDispatchDecision(
        request_id=request_id,
        backend_id=backend_id,
        backend_kind="fixture_file" if backend_id == "fixture_file" else "mock_http",
        decision="allowed",
        reason_code="forged_allowed_for_test",
        reason="Forged dispatch decision used to prove non-dispatch paths fail-closed.",
        approval_ref=None,
        intent=intent,
        external_call_requested=False,
        mutation_requested=False,
        output_contract="DarsCritiqueRecord",
        config_ref="dars-default@0.1.0",
        policy_refs=["APPRAISER-POLICY-DARS-001"],
    )


@pytest.mark.parametrize(
    "intent",
    ["approve_decision", "execute_action", "publish_output", "definitely_not_advisory"],
)
def test_fixture_backend_refuses_authority_intent_in_dispatch_decision(
    tmp_path: Path, intent: str
) -> None:
    """A forged ``allowed`` decision with a non-advisory intent must fail-closed.

    The backend must refuse before any fixture I/O, write a runtime-boundary
    validation report with the policy-violation reason code, and perform no
    external call or mutation.
    """

    instance = InstanceRoot(tmp_path)
    config = _fixture_backend_config()
    request_id = f"DARSREQ-FORGED-{intent}"
    decision = _forged_allowed_decision(intent=intent, request_id=request_id)

    with pytest.raises(ValueError, match="appraiser_separation_policy_violation"):
        DarsFixtureBackend(instance=instance).run(
            yyyymmdd="20260512",
            request_id=request_id,
            backend_config=config.spec.backends["fixture_file"],
            dispatch_decision=decision,
        )

    report_path = (
        tmp_path
        / "runtime-boundary"
        / "dars"
        / "20260512"
        / f"dars-validation-{request_id}.json"
    )
    assert report_path.exists(), "fixture backend must write validation report on policy violation"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_id"] == "hisys.dars.validation"
    assert report["status"] == "rejected"
    assert report["reason_code"] == "appraiser_separation_policy_violation"
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False


def test_fixture_backend_does_not_read_fixture_on_authority_intent(tmp_path: Path) -> None:
    """The guard must trip before any fixture file is opened."""

    instance = InstanceRoot(tmp_path)
    config = _fixture_backend_config()
    # Deliberately do NOT create the fixture file. A working guard prevents
    # the fixture read entirely; a missing guard would surface a different
    # error (file-not-found / invalid response) instead of the policy code.
    decision = _forged_allowed_decision(intent="approve_decision", request_id="DARSREQ-NOREAD-001")

    with pytest.raises(ValueError, match="appraiser_separation_policy_violation"):
        DarsFixtureBackend(instance=instance).run(
            yyyymmdd="20260512",
            request_id="DARSREQ-NOREAD-001",
            backend_config=config.spec.backends["fixture_file"],
            dispatch_decision=decision,
        )


# ---------------------------------------------------------------------------
# DarsMockEndpointAdapter fail-closed enforcement (non-dispatch path)
# ---------------------------------------------------------------------------


def _mock_backend_config() -> DarsConfig:
    data = _minimal_dars_config()
    data["spec"]["backends"]["mock_endpoint"] = {
        "kind": "mock_http",
        "enabled": False,
        "mode": "local_network_only",
        "external_call_allowed": False,
        "output_contract": "DarsCritiqueRecord",
    }
    return DarsConfig.model_validate(data)


@pytest.mark.parametrize(
    "intent",
    ["approve_decision", "execute_action", "publish_output", "definitely_not_advisory"],
)
def test_mock_endpoint_adapter_refuses_authority_intent_in_dispatch_decision(
    tmp_path: Path, intent: str
) -> None:
    instance = InstanceRoot(tmp_path)
    config = _mock_backend_config()
    request_id = f"DARSREQ-FORGED-MOCK-{intent}"
    decision = _forged_allowed_decision(
        intent=intent, backend_id="mock_endpoint", request_id=request_id
    )

    with pytest.raises(ValueError, match="appraiser_separation_policy_violation"):
        DarsMockEndpointAdapter(instance=instance).run(
            yyyymmdd="20260512",
            request_id=request_id,
            backend_config=config.spec.backends["mock_endpoint"],
            dispatch_decision=decision,
        )


# ---------------------------------------------------------------------------
# Existing dispatch behavior must continue to use the shared guard
# ---------------------------------------------------------------------------


def test_dispatch_module_reexports_shared_guard_constants() -> None:
    """Refactor must keep dispatch's public constants pointing at the shared module."""

    from hisys.agents import appraiser_separation as guard
    from hisys.agents import dars_dispatch

    assert dars_dispatch.ADVISORY_INTENTS is guard.ADVISORY_INTENTS
    assert dars_dispatch.AUTHORITY_INTENTS is guard.AUTHORITY_INTENTS
    assert dars_dispatch.DEFAULT_APPRAISER_POLICY_REF == guard.DEFAULT_APPRAISER_POLICY_REF
