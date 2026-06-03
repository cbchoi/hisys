"""Tests for natural-language domain intent resolution before investigate-domain.

Traceability: domain request construction guard for implemented adapter routing.
"""

import json

from hisys.cli.main import main
from hisys.domain.intent import DomainIntentInput, infer_domain_intent
from hisys.schemas.domain_investigation import DomainSourceRef


def _source(ref: str, *, source_id: str = "SRC-001") -> DomainSourceRef:
    return DomainSourceRef(
        source_id=source_id,
        source_type="current_artifact",
        ref=ref,
        access_mode="read_only",
    )


def test_paper_review_maps_to_research_instead_of_general() -> None:
    result = infer_domain_intent(
        DomainIntentInput(
            objective="Use Hisys DARS and Judge to review this research paper for journal fit.",
            sources=[_source("/work/papers/main.tex")],
            user_focus="manuscript review, claim/evidence validity, source/PDF checks",
        )
    )

    assert result.domain == "research"
    assert result.confidence == "high"
    assert "manuscript_or_paper_review_signal" in result.reason_codes
    assert result.audit_ref == "domain-inference:research:high"


def test_codebase_architecture_maps_to_codebase_even_with_review_language() -> None:
    result = infer_domain_intent(
        DomainIntentInput(
            objective="Use Hisys DARS and Judge to review adapter architecture and tests.",
            sources=[_source("/home/cbchoi/workspaces/develop/repos/hisys/src/hisys/domain/adapters.py")],
            user_focus="implementation gap, architecture recommendation, tests",
        )
    )

    assert result.domain == "codebase"
    assert result.confidence == "high"
    assert "codebase_artifact_signal" in result.reason_codes


def test_general_is_last_fallback_when_no_implemented_adapter_signal_matches() -> None:
    result = infer_domain_intent(
        DomainIntentInput(
            objective="Assess a broad personal naming convention and open-ended tradeoffs.",
            sources=[_source("/tmp/topic-note.md")],
            user_focus="general advisory synthesis",
        )
    )

    assert result.domain == "general"
    assert result.confidence == "low"
    assert result.reason_codes == ("no_specific_implemented_adapter_signal",)


def test_explicit_domain_override_is_preserved_with_audit_reason() -> None:
    result = infer_domain_intent(
        DomainIntentInput(
            objective="Review manuscript journal fit.",
            sources=[_source("/work/papers/main.tex")],
            explicit_domain="general",
        )
    )

    assert result.domain == "general"
    assert result.confidence == "explicit"
    assert result.reason_codes == ("explicit_domain_override",)


def test_investigate_domain_can_infer_research_from_general_paper_review_request(tmp_path) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": "REQ-PAPER-REVIEW-INFER-001",
                "domain": "general",
                "objective": "Use Hisys DARS and Judge to review this manuscript for journal fit.",
                "sources": [
                    {
                        "source_id": "primary-manuscript",
                        "source_type": "current_artifact",
                        "ref": "/work/papers/main.tex",
                        "access_mode": "read_only",
                    }
                ],
                "user_focus": "research paper review, claim/evidence validity, source/PDF checks",
            }
        ),
        encoding="utf-8",
    )

    assert main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path / "instance"),
            "--request",
            str(request_path),
            "--date",
            "20260603",
            "--infer-domain-intent",
        ]
    ) == 0

    request_artifact = (
        tmp_path
        / "instance"
        / "runtime-boundary/domain-investigation/research/20260603/hisys-tool-request-REQ-PAPER-REVIEW-INFER-001.json"
    )
    payload = json.loads(request_artifact.read_text(encoding="utf-8"))

    assert payload["domain"] == "research"
    assert "domain-inference:research:high" in payload["config_snapshot_refs"]
