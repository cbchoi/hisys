"""Investment decision packet CLI product workflow tests.

Traceability: HISYS-SCHEMA-001, HISYS-FR-CE-002..006,
HISYS-DARS-CONTRACT-001, HISYS-NFR-SEC-004, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _packet_payload() -> dict:
    return {
        "packet_id": "IDP-CLI-SP500-001",
        "producer_id": "hisys-investment-decision-support-cli-test",
        "status": "draft",
        "asset": "S&P 500",
        "instrument_refs": ["SPY", "VOO"],
        "time_horizon": "6-12 months",
        "proposed_action": "staged_buy",
        "weight_policy_ref": "IW-POLICY-CLI-SP500-BALANCED-001",
        "recommendation_summary": "Conditional staged exposure only after human review accepts valuation risk.",
        "confidence": 0.58,
        "evidence_score": 0.72,
        "risk_score": 0.61,
        "contradiction_score": 0.54,
        "signals": [
            {
                "signal_id": "SIG-CLI-SP500-GDP-001",
                "name": "Real GDP growth",
                "direction": "bullish",
                "strength": 0.68,
                "evidence_refs": ["EV-CLI-SP500-GDP-001"],
                "interpretation": "Positive real GDP growth supports risk assets over the stated horizon.",
            }
        ],
        "bull_case": {
            "case_id": "CASE-CLI-SP500-BULL-001",
            "summary": "Growth and liquidity conditions improve.",
            "probability": 0.35,
            "evidence_refs": ["EV-CLI-SP500-GDP-001"],
        },
        "base_case": {
            "case_id": "CASE-CLI-SP500-BASE-001",
            "summary": "Index grinds higher with valuation volatility.",
            "probability": 0.45,
            "evidence_refs": ["EV-CLI-SP500-GDP-001"],
        },
        "bear_case": {
            "case_id": "CASE-CLI-SP500-BEAR-001",
            "summary": "Valuation compresses if inflation/rates reaccelerate.",
            "probability": 0.20,
            "evidence_refs": ["EV-CLI-SP500-PE-001"],
        },
        "decision_boundary": ["No execution or publication without approved human scope."],
        "risk_register": ["High trailing P/E makes downside asymmetry material."],
        "contradicting_evidence_refs": ["EV-CLI-SP500-PE-001"],
        "chief_editor_status": "accepted_for_human_reviewed_use",
        "devil_review_status": "completed",
        "dars_review_status": "completed",
        "human_insight_refs": ["runtime-boundary/dars/DARSRESP-CLI-SP500-001.json"],
        "human_approval": {
            "required": True,
            "status": "pending",
            "approver_ref": "human:professor",
            "responsibility_statement": "Human accepts responsibility before any consequential use.",
        },
        "disclaimers": ["not financial advice", "no autonomous execution"],
        "hisys_mode": {
            "level": "decision",
            "routing_policy_ref": "lapidary-routing-policy/operational-governance-v1",
            "upgrade_triggers": ["decision_requested"],
        },
        "evidence_chain": {
            "chain_id": "CHAIN-CLI-SP500-001",
            "producer_id": "hisys-investment-decision-support-cli-test",
            "status": "active",
            "decision_ref": "ALERT-CLI-SP500-001",
            "synthesis_refs": ["PERSP-CLI-SP500-001"],
            "claim_ledger_refs": ["MEM-CLI-SP500-001"],
            "evidence_refs": ["SIG-CLI-SP500-GDP-001"],
            "source_refs": ["SRC-CLI-SP500-GDP-001"],
        },
        "weighted_alternatives": [
            {
                "alternative_id": "ALT-CLI-SP500-001",
                "producer_id": "hisys-investment-decision-support-cli-test",
                "status": "active",
                "label": "Staged buy under valuation guardrails",
                "claim": "Stagger exposure while contradiction risk remains elevated.",
                "origin_weights": [
                    {
                        "evidence_origin": "external_source",
                        "ref": "SRC-CLI-SP500-GDP-001",
                        "origin_weight": 0.45,
                        "source_quality": 0.80,
                        "verification_status": 0.75,
                        "recency": 0.70,
                        "independence": 0.80,
                        "contradiction_status": 0.65,
                        "domain_fit": 0.80,
                    }
                ],
                "recommended_use": "hybrid",
                "limitations": ["Human review required before consequential use."],
            }
        ],
    }


def _weight_policy_payload() -> dict:
    return {
        "policy_id": "IW-POLICY-CLI-SP500-BALANCED-001",
        "producer_id": "hisys-investment-decision-support-cli-test",
        "status": "active",
        "profile_name": "Balanced S&P 500 6-12 month support",
        "risk_tolerance": "balanced",
        "time_horizon_profile": "6-12 months",
        "evidence_weight": 0.40,
        "risk_weight": 0.25,
        "contradiction_weight": 0.20,
        "confidence_weight": 0.15,
        "contradiction_handling": "require_human_review",
        "contradiction_threshold": 0.60,
    }


def test_build_investment_decision_packet_cli_writes_product_artifacts_and_audit(
    tmp_path: Path, capsys
) -> None:
    from hisys.cli.main import main

    request_path = tmp_path / "packet-input.json"
    request_path.write_text(json.dumps(_packet_payload()), encoding="utf-8")

    result = main(
        [
            "build-investment-decision-packet",
            "--instance",
            str(tmp_path),
            "--date",
            "20260512",
            "--packet",
            str(request_path),
        ]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "packet_id=IDP-CLI-SP500-001" in output
    assert "execution_authorized=false" in output
    assert "publication_or_live_action_approved=false" in output
    packet_json = tmp_path / "runtime-boundary" / "investment-decisions" / "20260512" / "IDP-CLI-SP500-001.json"
    packet_md = packet_json.with_suffix(".md")
    audit_alt = tmp_path / "data" / "audit" / "20260512" / "lapidary-governance" / "weighted-alternatives" / "ALT-CLI-SP500-001.json"
    audit_chain = tmp_path / "data" / "audit" / "20260512" / "lapidary-governance" / "evidence-chains" / "CHAIN-CLI-SP500-001.json"
    report_json = tmp_path / "runtime-boundary" / "investment-decisions" / "20260512" / "investment-decision-packet-report.json"

    assert packet_json.exists()
    assert packet_md.exists()
    assert audit_alt.exists()
    assert audit_chain.exists()
    assert report_json.exists()

    packet = json.loads(packet_json.read_text(encoding="utf-8"))
    assert packet["human_approval"]["status"] == "pending"
    assert packet["execution_authorized"] is False
    assert packet["publication_or_live_action_approved"] is False
    assert packet["hisys_mode"]["level"] == "decision"
    assert packet["disclaimers"] == ["not financial advice", "no autonomous execution"]
    assert "weighted_score" not in packet["weighted_alternatives"][0]
    assert "score" not in packet["weighted_alternatives"][0]["origin_weights"][0]

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["packet_ref"] == "runtime-boundary/investment-decisions/20260512/IDP-CLI-SP500-001.json"
    assert report["human_approval_required_for_consequential_use"] is True
    assert report["requested_approval_scopes"] == ["human_reviewed_use"]
    assert report["approved_approval_scopes"] == []
    assert report["action_taken"] == "none"
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False


def test_build_investment_decision_packet_cli_attaches_weight_policy(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    request_path = tmp_path / "packet-input.json"
    policy_path = tmp_path / "weight-policy.json"
    request_path.write_text(json.dumps(_packet_payload()), encoding="utf-8")
    policy_path.write_text(json.dumps(_weight_policy_payload()), encoding="utf-8")

    result = main(
        [
            "build-investment-decision-packet",
            "--instance",
            str(tmp_path),
            "--date",
            "20260512",
            "--packet",
            str(request_path),
            "--weight-policy",
            str(policy_path),
        ]
    )

    assert result == 0
    assert "weight_policy_ref=runtime-boundary/investment-decisions/20260512/IW-POLICY-CLI-SP500-BALANCED-001.json" in capsys.readouterr().out
    report_json = tmp_path / "runtime-boundary" / "investment-decisions" / "20260512" / "investment-decision-packet-report.json"
    persisted_policy = tmp_path / "runtime-boundary" / "investment-decisions" / "20260512" / "IW-POLICY-CLI-SP500-BALANCED-001.json"

    assert persisted_policy.exists()
    policy = json.loads(persisted_policy.read_text(encoding="utf-8"))
    assert policy["schema_id"] == "hisys.investment_weight_policy"
    assert policy["contradiction_handling"] == "require_human_review"
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["weight_policy_ref"] == "runtime-boundary/investment-decisions/20260512/IW-POLICY-CLI-SP500-BALANCED-001.json"
    assert report["packet_weight_policy_ref"] == "IW-POLICY-CLI-SP500-BALANCED-001"


def test_build_investment_decision_packet_cli_rejects_mismatched_weight_policy(tmp_path: Path) -> None:
    from hisys.cli.main import main

    request_path = tmp_path / "packet-input.json"
    policy_path = tmp_path / "weight-policy.json"
    mismatched_policy = _weight_policy_payload()
    mismatched_policy["policy_id"] = "IW-POLICY-CLI-SP500-CONSERVATIVE-001"
    request_path.write_text(json.dumps(_packet_payload()), encoding="utf-8")
    policy_path.write_text(json.dumps(mismatched_policy), encoding="utf-8")

    with pytest.raises(ValueError, match="weight policy id does not match packet.weight_policy_ref"):
        main(
            [
                "build-investment-decision-packet",
                "--instance",
                str(tmp_path),
                "--date",
                "20260512",
                "--packet",
                str(request_path),
                "--weight-policy",
                str(policy_path),
            ]
        )


def test_run_investment_decision_dry_run_assembles_packet_from_evidence_artifacts(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    evidence_path = tmp_path / "evidence-package.json"
    policy_path = tmp_path / "weight-policy.json"
    evidence_path.write_text(
        json.dumps(
            {
                "package_id": "PKG-INVDRY-SP500-001",
                "task_id": "TASK-INVDRY-SP500-001",
                "agent_id": "browser-read-only-evidence-artifact",
                "agent_type": "investment_decision_support",
                "claims": [
                    {
                        "claim_id": "CLAIM-INVDRY-SP500-GROWTH-001",
                        "text": "Macro growth evidence supports a staged S&P 500 exposure review.",
                        "confidence": 0.66,
                        "evidence_refs": ["EV-INVDRY-SP500-GDP-001"],
                        "limitations": ["Evidence artifact is read-only and not a live market feed."],
                    }
                ],
                "evidence": [
                    {
                        "evidence_id": "EV-INVDRY-SP500-GDP-001",
                        "task_id": "TASK-INVDRY-SP500-001",
                        "agent_id": "browser-read-only-evidence-artifact",
                        "source_id": "SRC-INVDRY-SP500-GDP-001",
                        "url": "https://example.org/read-only-market-evidence",
                        "title": "Read-only market evidence artifact",
                        "quoted_text": "Growth remains positive while valuation risk is material.",
                        "retrieved_at": "2026-05-12T00:00:00Z",
                        "content_hash": "sha256:dryrun",
                    }
                ],
                "limitations": ["Dry-run evidence artifact; no autonomous execution."],
                "open_questions": ["Validate with additional independent sources before stronger use."],
                "external_side_effects": False,
                "actions_taken": ["read_only_artifact_ingested"],
            }
        ),
        encoding="utf-8",
    )
    policy_path.write_text(json.dumps(_weight_policy_payload()), encoding="utf-8")

    result = main(
        [
            "run-investment-decision-dry-run",
            "--instance",
            str(tmp_path),
            "--date",
            "20260512",
            "--asset",
            "S&P 500",
            "--instrument",
            "SPY",
            "--instrument",
            "VOO",
            "--time-horizon",
            "6-12 months",
            "--evidence-package",
            str(evidence_path),
            "--weight-policy",
            str(policy_path),
        ]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "investment decision dry run: assembled packet_id=IDP-INVDRY-SP500-001" in output
    assert "fixture_backend_used=false" in output
    packet_json = tmp_path / "runtime-boundary" / "investment-decisions" / "20260512" / "IDP-INVDRY-SP500-001.json"
    report_json = tmp_path / "runtime-boundary" / "investment-decisions" / "20260512" / "investment-decision-packet-report.json"
    assert packet_json.exists()
    packet = json.loads(packet_json.read_text(encoding="utf-8"))
    assert packet["asset"] == "S&P 500"
    assert packet["instrument_refs"] == ["SPY", "VOO"]
    assert packet["evidence_chain"]["source_refs"] == ["SRC-INVDRY-SP500-GDP-001"]
    assert packet["weighted_alternatives"][0]["alternative_id"] == "ALT-INVDRY-SP500-001"
    assert packet["chief_editor_status"] == "accepted_for_human_reviewed_use"
    assert packet["dars_review_status"] == "not_started"
    assert packet["execution_authorized"] is False
    assert packet["publication_or_live_action_approved"] is False
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["workflow"] == "investment_decision_dry_run"
    assert report["fixture_backend_used"] is False
    assert report["input_evidence_package_refs"] == [str(evidence_path)]
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False


def test_review_investment_decision_packet_cli_prints_operator_summary(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    request_path = tmp_path / "packet-input.json"
    request_path.write_text(json.dumps(_packet_payload()), encoding="utf-8")
    assert main(
        [
            "build-investment-decision-packet",
            "--instance",
            str(tmp_path),
            "--date",
            "20260512",
            "--packet",
            str(request_path),
        ]
    ) == 0
    capsys.readouterr()

    result = main(
        [
            "review-investment-decision-packet",
            "--instance",
            str(tmp_path),
            "--date",
            "20260512",
            "--packet-id",
            "IDP-CLI-SP500-001",
            "--format",
            "json",
        ]
    )

    assert result == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["packet_id"] == "IDP-CLI-SP500-001"
    assert summary["asset"] == "S&P 500"
    assert summary["proposed_action"] == "staged_buy"
    assert summary["human_approval_status"] == "pending"
    assert summary["requested_approval_scopes"] == ["human_reviewed_use"]
    assert summary["boundary"]["action_taken"] == "none"
    assert summary["boundary"]["external_call_made"] is False
    assert summary["artifact_refs"]["packet_markdown_ref"].endswith("IDP-CLI-SP500-001.md")
