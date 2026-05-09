"""CLI tests for domain-general Hisys MVP boundary.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024,
HISYS-CON-010..012.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def _write_domain_request(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": "HISYS-REQ-RESEARCH-GAP-001",
                "domain": "research",
                "objective": "find research gap among formalisms for self-organizing structure",
                "sources": [
                    {
                        "source_id": "SRC-FORMALISM-FIXTURE-001",
                        "source_type": "fixture",
                        "ref": "fixture://formalism-gap",
                        "access_mode": "read_only",
                    }
                ],
                "user_focus": "Separate source evidence from interpreted gap statements.",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_investigate_domain_writes_request_and_tool_result_boundary(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "domain investigation run" in captured.out
    assert "domain: research" in captured.out
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    request_artifact = boundary_dir / "hisys-tool-request-HISYS-REQ-RESEARCH-GAP-001.json"
    result_artifact = boundary_dir / "hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.json"
    assert request_artifact.exists()
    assert result_artifact.exists()

    request_data = json.loads(request_artifact.read_text(encoding="utf-8"))
    tool_result = json.loads(result_artifact.read_text(encoding="utf-8"))
    assert request_data["constraints"] == {
        "credential_use_allowed": False,
        "external_calls_allowed": False,
        "max_rounds": 3,
        "mutation_allowed": False,
    }
    assert tool_result["status"] == "needs_more_evidence"
    assert tool_result["domain"] == "research"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False
    assert tool_result["quality_gate"] == "needs_more_evidence"
    assert str(result_artifact.relative_to(tmp_path)) in tool_result["runtime_boundary_refs"]

    report = json.loads(
        (tmp_path / "reports" / "run-summaries" / "20260509" / "domain-investigation-report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["request_id"] == "HISYS-REQ-RESEARCH-GAP-001"
    assert report["domain"] == "research"
    assert report["tool_result_ref"] == str(result_artifact.relative_to(tmp_path))
