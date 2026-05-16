"""DARS dispatch gate appraiser-separation enforcement tests.

These tests connect ``AppraiserSeparationPolicy`` to the DARS dispatch path
and prove that DARS remains advisory-only: critique/findings/recommendations
intents are allowed, but approve/execute/publish authority intents are blocked
at the dispatch boundary and recorded as policy violations.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005, HISYS-SCHEMA-001,
HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.agents.dars_config import DarsConfig
from hisys.agents.dars_dispatch import DarsDispatchGate
from hisys.config.instance import InstanceRoot
from hisys.schemas.lapidary_governance import AppraiserSeparationPolicy
from tests.unit.test_dars_config import _minimal_dars_config


def _appraiser_policy() -> AppraiserSeparationPolicy:
    return AppraiserSeparationPolicy(
        policy_id="APPRAISER-POLICY-DARS-001",
        producer_id="test",
        status="active",
        appraiser_role="DARS/Devil",
        separate_from_roles=["Chief Editor", "Jeweler", "Hisys Core Synthesizer"],
        advisory_only=True,
        may_approve_decision=False,
        may_execute_action=False,
        checks=["confirmation_bias", "stale_evidence"],
    )


def test_dispatch_allows_advisory_critique_intent_and_records_policy_ref(tmp_path: Path) -> None:
    config = DarsConfig.model_validate(_minimal_dars_config())
    policy = _appraiser_policy()

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260512",
        request_id="DARSREQ-APP-001",
        config=config,
        backend_id="loopback_placeholder",
        approval_ref=None,
        intent="advisory_critique",
        appraiser_policy=policy,
    )

    assert decision.decision == "allowed"
    assert decision.reason_code == "loopback_backend_allowed"
    assert decision.intent == "advisory_critique"
    assert decision.allowed_actions == "advisory_only"
    assert decision.action_taken == "none"
    assert decision.external_call_made is False
    assert decision.mutation_performed is False
    assert "APPRAISER-POLICY-DARS-001" in decision.policy_refs

    record_path = (
        tmp_path
        / "runtime-boundary"
        / "dars"
        / "20260512"
        / "dars-dispatch-decision-DARSREQ-APP-001.json"
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["intent"] == "advisory_critique"
    assert "APPRAISER-POLICY-DARS-001" in record["policy_refs"]

    markdown_path = record_path.with_suffix(".md")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "- intent: advisory_critique" in markdown
    assert "APPRAISER-POLICY-DARS-001" in markdown


@pytest.mark.parametrize(
    "intent",
    ["return_findings", "return_recommendations"],
)
def test_dispatch_allows_findings_and_recommendations_intents(tmp_path: Path, intent: str) -> None:
    config = DarsConfig.model_validate(_minimal_dars_config())

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260512",
        request_id=f"DARSREQ-APP-INTENT-{intent}",
        config=config,
        backend_id="loopback_placeholder",
        approval_ref=None,
        intent=intent,
        appraiser_policy=_appraiser_policy(),
    )

    assert decision.decision == "allowed"
    assert decision.intent == intent


@pytest.mark.parametrize(
    "intent",
    ["approve_decision", "execute_action", "publish_output"],
)
def test_dispatch_blocks_authority_intents_with_separation_policy_violation(
    tmp_path: Path, intent: str
) -> None:
    config = DarsConfig.model_validate(_minimal_dars_config())
    policy = _appraiser_policy()
    request_id = f"DARSREQ-APP-BLOCK-{intent}"

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260512",
        request_id=request_id,
        config=config,
        backend_id="loopback_placeholder",
        approval_ref=None,
        intent=intent,
        appraiser_policy=policy,
    )

    assert decision.decision == "blocked"
    assert decision.reason_code == "appraiser_separation_policy_violation"
    assert decision.intent == intent
    assert decision.action_taken == "none"
    assert decision.external_call_made is False
    assert decision.mutation_performed is False
    assert "APPRAISER-POLICY-DARS-001" in decision.policy_refs

    record_path = (
        tmp_path
        / "runtime-boundary"
        / "dars"
        / "20260512"
        / f"dars-dispatch-decision-{request_id}.json"
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["decision"] == "blocked"
    assert record["reason_code"] == "appraiser_separation_policy_violation"
    assert record["intent"] == intent


def test_dispatch_blocks_unknown_intent_value(tmp_path: Path) -> None:
    config = DarsConfig.model_validate(_minimal_dars_config())

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260512",
        request_id="DARSREQ-APP-UNKNOWN",
        config=config,
        backend_id="loopback_placeholder",
        approval_ref=None,
        intent="something_unauthorized",
        appraiser_policy=_appraiser_policy(),
    )

    assert decision.decision == "blocked"
    assert decision.reason_code == "appraiser_separation_policy_violation"


def test_dispatch_default_intent_is_advisory_and_uses_default_policy_ref(tmp_path: Path) -> None:
    """Existing callers that do not pass intent/policy still get advisory-only guards.

    No appraiser_policy supplied: dispatch must still record a default appraiser
    policy reference so the separation policy is always part of the audit trail.
    """

    config = DarsConfig.model_validate(_minimal_dars_config())

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260512",
        request_id="DARSREQ-APP-DEFAULT",
        config=config,
        backend_id="loopback_placeholder",
        approval_ref=None,
    )

    assert decision.decision == "allowed"
    assert decision.intent == "advisory_critique"
    assert any(ref.startswith("APPRAISER-POLICY-") for ref in decision.policy_refs)
