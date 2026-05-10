"""CLI runtime glue tests for the I4 Investigator increment.

Traceability: HISYS-INST-INV-001, HISYS-RUNTIME-DIR-001, HISYS-D-015,
HISYS-D-016, HISYS-T-001, HISYS-T-007, HISYS-T-008, HISYS-T-009,
HISYS-T-010, HISYS-T-011, HISYS-T-012, HISYS-T-013, HISYS-T-014,
HISYS-T-015, HISYS-T-016, HISYS-T-017, HISYS-T-018, HISYS-T-019,
HISYS-T-020, HISYS-T-021, HISYS-T-022, HISYS-T-023, HISYS-T-024,
HISYS-T-025, HISYS-T-026, HISYS-T-027.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


EXAMPLE_INSTANCE = Path(__file__).resolve().parents[2] / "examples" / "instance"


def _prepare_flagged_conflict_memo(tmp_path: Path, capsys) -> str:
    assert (
        main(
            [
                "collect",
                "--instance",
                str(tmp_path),
                "--config-from",
                str(EXAMPLE_INSTANCE),
                "--source",
                "SRC-HW-MOCK-001",
                "--date",
                "20260508",
            ]
        )
        == 0
    )
    assert main(["extract", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    assert (
        main(
            [
                "draft-memo",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--perspective",
                "PERSP-OPS-001",
            ]
        )
        == 0
    )
    memo_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-draft-report.json"
    memo_id = json.loads(memo_report_path.read_text(encoding="utf-8"))["draft_memo_refs"][0]
    memo_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
    memo = json.loads(memo_path.read_text(encoding="utf-8"))
    memo["review_status"] = "flagged_conflict"
    memo["status"] = "flagged_conflict"
    memo_path.write_text(json.dumps(memo, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    review_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-review-report.json"
    review_report_path.write_text(
        json.dumps(
            {
                "reviewed_memo_refs": [memo_id],
                "duplicate_memo_refs": [],
                "conflict_memo_refs": [memo_id],
                "clean_memo_refs": [],
                "policy_refs": ["HISYS-FR-MEM-004", "HISYS-T-013"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    capsys.readouterr()
    return memo_id


def test_investigate_memo_command_researches_topic_and_writes_template_memo(tmp_path: Path, capsys):
    result = main(
        [
            "investigate-memo",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
            "--topic",
            "hardware overheating risk",
            "--goal",
            "Assess whether fixture sensor evidence requires operations attention.",
            "--perspective",
            "PERSP-OPS-001",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "investigation memo run" in captured.out
    assert "memos: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "investigation-memo-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    memo_id = report["memo_refs"][0]
    memo_path = tmp_path / "data" / "investigation-memos" / "20260508" / f"{memo_id}.json"
    markdown_path = tmp_path / "data" / "investigation-memos" / "20260508" / f"{memo_id}.md"
    assert memo_path.exists()
    assert markdown_path.exists()
    memo = json.loads(memo_path.read_text(encoding="utf-8"))
    assert memo["title"] == "Investigation Memo: hardware overheating risk"
    assert memo["summary"] == "Fixture sensor indicates over-threshold temperature condition."
    assert memo["source_refs"] == ["SRC-HW-MOCK-001"]
    assert memo["signal_refs"] == report["signal_refs"]
    assert "template:research-topic-search" in memo["tags"]
    assert "## Research Question" in memo["body"]
    assert "hardware overheating risk" in memo["body"]
    assert "## Query Set" in memo["body"]
    assert "hardware overheating risk operations evidence" in memo["body"]
    assert "## Accepted Source Records" in memo["body"]
    assert "SRC-HW-MOCK-001" in memo["body"]
    assert "## Investigation Findings" in memo["body"]
    assert "Fixture sensor indicates over-threshold temperature condition." in memo["body"]
    assert "## Evidence Trace" in memo["body"]
    assert report["observation_refs"][0] in memo["body"]
    assert report["signal_refs"][0] in memo["body"]
    assert "## Open Questions" in memo["body"]
    assert "raw payload is not copied" in memo["body"]
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Investigation Memo: hardware overheating risk" in markdown
    assert "## Investigation Findings" in markdown





def test_investigate_memo_formalism_domain_agents_write_substantive_domain_memo(tmp_path):
    instance = tmp_path / "hisys-formalism"
    result = main(
        [
            "investigate-memo",
            "--instance",
            str(instance),
            "--config-from",
            "examples/instance",
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
            "--topic",
            "formalism that can express self-organizing systems",
            "--goal",
            "Assess formalism candidates for representing self-organizing systems.",
            "--perspective",
            "PERSP-OPS-001",
            "--agent",
            "formalism_comparison",
            "--agent",
            "self_organization_mechanism",
        ]
    )

    assert result == 0
    memo_files = sorted((instance / "data" / "investigation-memos" / "20260508").glob("*.md"))
    assert len(memo_files) == 1
    memo_text = memo_files[0].read_text(encoding="utf-8")
    assert "Dynamic Structure DEVS" in memo_text
    assert "graph rewriting" in memo_text
    assert "agent-based modeling" in memo_text
    assert "local interaction rules" in memo_text
    assert "emergent global structure" in memo_text
    assert "Does the target formalism need executable simulation semantics?" in memo_text
    assert "Assessment criteria" in memo_text
    assert "Expressiveness: high for topology-changing discrete-event systems" in memo_text
    assert "Simulation semantics: native executable semantics" in memo_text
    assert "Verification/readability tradeoff" in memo_text
    assert "Selection heuristic" in memo_text
    assert "Choose Dynamic Structure DEVS" in memo_text
    assert "Choose graph rewriting" in memo_text
    assert "Choose agent-based modeling" in memo_text
    assert "boundary between component state and network topology" in memo_text
    report = json.loads((instance / "reports" / "run-summaries" / "20260508" / "investigation-memo-report.json").read_text())
    assert report["agent_ids"] == ["formalism-comparison-agent", "self-organization-mechanism-agent"]
    assert report["evidence_package_refs"] == [
        "EPKG-TASK-INV-001-FORMALISM",
        "EPKG-TASK-INV-002-SELFORG",
    ]


def test_investigate_memo_auto_selects_research_idea_discovery_guideline(tmp_path):
    instance = tmp_path / "hisys-research-guideline"
    result = main(
        [
            "investigate-memo",
            "--instance",
            str(instance),
            "--config-from",
            "examples/instance",
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
            "--topic",
            "formalism gap for self organizing systems",
            "--goal",
            "Find new research ideas and gaps between existing formalisms.",
            "--perspective",
            "PERSP-OPS-001",
        ]
    )

    assert result == 0
    memo_text = next((instance / "data" / "investigation-memos" / "20260508").glob("*.md")).read_text(
        encoding="utf-8"
    )
    assert "Guideline Profile: `research_idea_discovery`" in memo_text
    assert "Gap statements between competing ideas" in memo_text
    assert "Novelty candidates and synthesis opportunities" in memo_text
    assert "Evaluation scenarios for validating the new idea" in memo_text
    assert "Self-organizing Dynamic Structure DEVS" in memo_text
    assert "Can graph rewrite rules be embedded as structural-transition guards in DSDEVS?" in memo_text
    report = json.loads((instance / "reports" / "run-summaries" / "20260508" / "investigation-memo-report.json").read_text())
    assert report["guideline_profile_id"] == "research_idea_discovery"
    assert report["agent_ids"] == ["formalism-gap-analysis-agent"]
    assert report["evidence_package_refs"] == ["EPKG-TASK-INV-001-GAP"]
    assert report["agent_plan_source"] == "config_default"
    assert "publisher_web_search" in report["disabled_optional_agent_refs"]
    assert "claude_research_evidence" in report["disabled_optional_agent_refs"]
    assert "HISYS-T-030" in report["policy_refs"]
    assert "HISYS-T-032" in report["policy_refs"]


def test_investigate_memo_auto_selects_investment_decision_guideline(tmp_path):
    instance = tmp_path / "hisys-investment-guideline"
    result = main(
        [
            "investigate-memo",
            "--instance",
            str(instance),
            "--config-from",
            "examples/instance",
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
            "--topic",
            "semiconductor company stock trend",
            "--goal",
            "Gather trends and company information to decide whether to buy the stock.",
            "--perspective",
            "PERSP-OPS-001",
        ]
    )

    assert result == 0
    memo_text = next((instance / "data" / "investigation-memos" / "20260508").glob("*.md")).read_text(
        encoding="utf-8"
    )
    assert "Guideline Profile: `investment_decision_support`" in memo_text
    assert "Company fundamentals and financial health" in memo_text
    assert "Market trend, competitors, valuation, and risk factors" in memo_text
    assert "Decision framing: buy, hold, avoid, or needs more evidence" in memo_text
    assert "Company fundamentals" in memo_text
    assert "Decision frame: needs more evidence" in memo_text
    assert "not financial advice" in memo_text
    report = json.loads((instance / "reports" / "run-summaries" / "20260508" / "investigation-memo-report.json").read_text())
    assert report["guideline_profile_id"] == "investment_decision_support"
    assert report["agent_ids"] == ["investment-decision-support-agent"]
    assert report["evidence_package_refs"] == ["EPKG-TASK-INV-001-INVEST"]
    assert report["agent_plan_source"] == "config_default"
    assert "market_news_search" in report["disabled_optional_agent_refs"]
    assert "company_filing_search" in report["disabled_optional_agent_refs"]


def test_investigate_memo_preserves_explicit_agent_override_for_general_topic(tmp_path: Path):
    result = main(
        [
            "investigate-memo",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
            "--topic",
            "hardware overheating risk",
            "--goal",
            "Assess whether evidence requires operations attention.",
            "--perspective",
            "PERSP-OPS-001",
            "--agent",
            "fixture",
            "--agent",
            "fixture_contradiction",
        ]
    )

    assert result == 0
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "investigation-memo-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["guideline_profile_id"] == "general_investigation"
    assert report["agent_ids"] == ["fixture-research-agent", "fixture-contradiction-agent"]
    assert report["evidence_package_refs"] == ["EPKG-TASK-INV-001-FIXTURE", "EPKG-TASK-INV-002-CONTRADICTION"]
    assert report["agent_plan_source"] == "explicit"
    assert report["disabled_optional_agent_refs"] == []


def test_investigate_memo_accepts_orchestrator_harness_source_plan_and_user_opinion(tmp_path: Path):
    harness = tmp_path / "orchestrator-harness.json"
    harness.write_text(
        json.dumps(
            {
                "schema_id": "hisys.investigator.orchestrator_harness",
                "schema_version": "0.1.0",
                "harness_id": "ORCH-HARNESS-001",
                "source_ids": ["SRC-WEB-RSS-001", "SRC-HERMES-TOOL-001"],
                "agent_types": ["fixture", "fixture_contradiction"],
                "user_opinion": "I suspect the Hermes tool evidence is more relevant than the RSS fixture.",
                "rationale": "Select richer fixture sources for investigator assessment.",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "investigate-memo",
            "--instance",
            str(tmp_path / "instance"),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--date",
            "20260508",
            "--topic",
            "autonomous investigator source planning",
            "--goal",
            "Assess whether orchestrator-selected sources and user opinion guide investigation.",
            "--perspective",
            "PERSP-OPS-001",
            "--orchestrator-harness",
            str(harness),
        ]
    )

    assert result == 0
    report_path = tmp_path / "instance" / "reports" / "run-summaries" / "20260508" / "investigation-memo-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["agent_plan_source"] == "orchestrator_harness"
    assert report["orchestrator_harness_ref"] == str(harness)
    assert report["harness_source_refs"] == ["SRC-WEB-RSS-001", "SRC-HERMES-TOOL-001"]
    assert report["source_refs"] == ["SRC-HERMES-TOOL-001", "SRC-WEB-RSS-001"]
    assert report["agent_ids"] == ["fixture-research-agent", "fixture-contradiction-agent"]
    assert report["user_opinion"] == "I suspect the Hermes tool evidence is more relevant than the RSS fixture."
    memo_text = next((tmp_path / "instance" / "data" / "investigation-memos" / "20260508").glob("*.md")).read_text(encoding="utf-8")
    assert "## Orchestrator Harness" in memo_text
    assert "SRC-HERMES-TOOL-001" in memo_text
    assert "## User Opinion" in memo_text
    assert "more relevant than the RSS fixture" in memo_text


def test_investigate_memo_blocks_disabled_harness_external_connector(tmp_path: Path, capsys):
    harness = tmp_path / "unsafe-orchestrator-harness.json"
    harness.write_text(
        json.dumps(
            {
                "schema_id": "hisys.investigator.orchestrator_harness",
                "schema_version": "0.1.0",
                "harness_id": "ORCH-HARNESS-UNSAFE-001",
                "source_ids": ["SRC-HW-MOCK-001"],
                "agent_types": ["publisher_web_search"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "investigate-memo",
            "--instance",
            str(tmp_path / "instance"),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--date",
            "20260508",
            "--topic",
            "formalism gap",
            "--goal",
            "Find research gaps.",
            "--perspective",
            "PERSP-OPS-001",
            "--orchestrator-harness",
            str(harness),
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "investigator agent connector blocked" in captured.err
    assert "publisher_web_search" in captured.err
    assert not (tmp_path / "instance" / "data" / "evidence-packages" / "20260508").exists()


def test_investigate_memo_blocks_disabled_explicit_external_connector(tmp_path: Path, capsys):
    result = main(
        [
            "investigate-memo",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
            "--topic",
            "formalism gap",
            "--goal",
            "Find research gaps.",
            "--perspective",
            "PERSP-OPS-001",
            "--agent",
            "publisher_web_search",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "investigator agent connector blocked" in captured.err
    assert "publisher_web_search" in captured.err
    assert not (tmp_path / "data" / "evidence-packages" / "20260508").exists()


def test_investigate_memo_dispatches_multiple_fixture_agents(tmp_path: Path, capsys):
    result = main(
        [
            "investigate-memo",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
            "--topic",
            "hardware overheating risk",
            "--goal",
            "Assess whether evidence requires operations attention.",
            "--perspective",
            "PERSP-OPS-001",
            "--agent",
            "fixture",
            "--agent",
            "fixture_contradiction",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "agents: 2" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "investigation-memo-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["research_task_refs"]) == 2
    assert len(report["evidence_package_refs"]) == 2
    assert report["agent_ids"] == ["fixture-research-agent", "fixture-contradiction-agent"]
    assert report["open_questions"] == ["Is the observed condition repeated across time or independent sources?"]
    for task_id in report["research_task_refs"]:
        assert (tmp_path / "data" / "research-tasks" / "20260508" / f"{task_id}.json").exists()
    for package_id in report["evidence_package_refs"]:
        assert (tmp_path / "data" / "evidence-packages" / "20260508" / f"{package_id}.json").exists()
    memo_id = report["memo_refs"][0]
    memo = json.loads(
        (tmp_path / "data" / "investigation-memos" / "20260508" / f"{memo_id}.json").read_text(
            encoding="utf-8"
        )
    )
    assert "## Research Agent Evidence" in memo["body"]
    assert "fixture-research-agent" in memo["body"]
    assert "fixture-contradiction-agent" in memo["body"]
    assert "## Agent Limitations" in memo["body"]
    assert "## Open Questions" in memo["body"]


def test_validate_config_accepts_example_instance(capsys):
    result = main(["validate-config", "--instance", str(EXAMPLE_INSTANCE)])

    captured = capsys.readouterr()
    assert result == 0
    assert "config valid" in captured.out
    assert "SRC-HW-MOCK-001" in captured.out
    assert "SRC-HERMES-TOOL-001" in captured.out


def test_collect_command_writes_report_summary_and_runtime_records(tmp_path: Path, capsys):
    result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "collection run" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["requested_source_ids"] == ["SRC-HW-MOCK-001"]
    assert len(report["collected_observation_refs"]) == 1
    assert report["skipped_source_ids"] == []
    obs_id = report["collected_observation_refs"][0]
    assert (tmp_path / "data" / "raw-observations" / "20260508" / f"{obs_id}.json").exists()
    assert (tmp_path / "data" / "audit" / "20260508" / "AUDIT-20260508.jsonl").exists()


def test_collect_command_writes_hermes_boundary_markdown_for_hermes_source(
    tmp_path: Path,
    capsys,
):
    result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HERMES-TOOL-001",
            "--date",
            "20260508",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "boundary_records: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["boundary_record_refs"] == [
        "hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-CLI-001/tool_output-HERMES-CLI-001.md"
    ]
    boundary_path = (
        tmp_path
        / "runtime-boundary"
        / "hermes"
        / "20260508"
        / "CAMP-HERMES-CLI-001"
        / "tool_output-HERMES-CLI-001.md"
    )
    assert boundary_path.exists()
    markdown = boundary_path.read_text(encoding="utf-8")
    assert "record_kind: tool_output" in markdown
    assert "SRC-HERMES-TOOL-001" in markdown
    assert "Fixture Hermes collection output" in markdown


def test_extract_command_writes_signal_report_from_collected_observations(tmp_path: Path, capsys):
    collect_result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )
    assert collect_result == 0
    capsys.readouterr()

    result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "extraction run" in captured.out
    assert "signals: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "extraction-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["requested_observation_refs"]) == 1
    assert len(report["extracted_signal_refs"]) == 1
    signal_id = report["extracted_signal_refs"][0]
    signal_path = tmp_path / "data" / "extracted-signals" / "20260508" / f"{signal_id}.json"
    assert signal_path.exists()
    signal = json.loads(signal_path.read_text(encoding="utf-8"))
    assert signal["observation_refs"] == report["requested_observation_refs"]
    assert signal["signal_type"] == "anomaly"
    assert "temperature_c" not in signal["claim_or_event"]


def test_draft_memo_command_writes_runtime_local_memo_draft(tmp_path: Path, capsys):
    collect_result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )
    assert collect_result == 0
    extract_result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])
    assert extract_result == 0
    capsys.readouterr()

    result = main(
        [
            "draft-memo",
            "--instance",
            str(tmp_path),
            "--date",
            "20260508",
            "--perspective",
            "PERSP-OPS-001",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "memo draft run" in captured.out
    assert "drafts: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-draft-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["perspective_id"] == "PERSP-OPS-001"
    assert len(report["requested_signal_refs"]) == 1
    assert len(report["draft_memo_refs"]) == 1
    memo_id = report["draft_memo_refs"][0]
    memo_json_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
    memo_md_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.md"
    assert memo_json_path.exists()
    assert memo_md_path.exists()
    memo = json.loads(memo_json_path.read_text(encoding="utf-8"))
    assert memo["review_status"] == "draft"
    assert memo["perspective_id"] == "PERSP-OPS-001"
    assert memo["signal_refs"] == report["requested_signal_refs"]
    markdown = memo_md_path.read_text(encoding="utf-8")
    assert "# Operations perspective" in markdown
    assert "temperature_c" not in markdown


def test_review_memos_command_flags_duplicate_runtime_drafts(tmp_path: Path, capsys):
    collect_result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )
    assert collect_result == 0
    extract_result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])
    assert extract_result == 0
    for _ in range(2):
        draft_result = main(
            [
                "draft-memo",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--perspective",
                "PERSP-OPS-001",
            ]
        )
        assert draft_result == 0
    capsys.readouterr()

    result = main(["review-memos", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "memo review run" in captured.out
    assert "duplicates: 2" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-review-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["reviewed_memo_refs"]) == 2
    assert len(report["duplicate_memo_refs"]) == 2
    for memo_id in report["duplicate_memo_refs"]:
        memo_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
        memo = json.loads(memo_path.read_text(encoding="utf-8"))
        assert memo["review_status"] == "flagged_duplicate"


def test_decide_alerts_command_writes_alert_decision_records(tmp_path: Path, capsys):
    collect_result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )
    assert collect_result == 0
    extract_result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])
    assert extract_result == 0
    draft_result = main(
        [
            "draft-memo",
            "--instance",
            str(tmp_path),
            "--date",
            "20260508",
            "--perspective",
            "PERSP-OPS-001",
        ]
    )
    assert draft_result == 0
    memo_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-draft-report.json"
    memo_report = json.loads(memo_report_path.read_text(encoding="utf-8"))
    memo_id = memo_report["draft_memo_refs"][0]
    memo_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
    memo = json.loads(memo_path.read_text(encoding="utf-8"))
    memo["review_status"] = "flagged_conflict"
    memo["status"] = "flagged_conflict"
    memo_path.write_text(json.dumps(memo, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    review_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-review-report.json"
    review_report_path.write_text(
        json.dumps(
            {
                "reviewed_memo_refs": [memo_id],
                "duplicate_memo_refs": [],
                "conflict_memo_refs": [memo_id],
                "clean_memo_refs": [],
                "policy_refs": ["HISYS-FR-MEM-004", "HISYS-T-013"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    capsys.readouterr()

    result = main(["decide-alerts", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "alert decision run" in captured.out
    assert "alert_decisions: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["reviewed_memo_refs"] == [memo_id]
    assert len(report["alert_decision_refs"]) == 1
    alert_id = report["alert_decision_refs"][0]
    alert_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    assert alert_path.exists()
    alert = json.loads(alert_path.read_text(encoding="utf-8"))
    assert alert["memo_refs"] == [memo_id]
    assert alert["trigger_reason"] == "memo_conflict_detected"
    assert alert["action_taken"] == "none"


def test_decide_alerts_command_suppresses_repeated_alert_decision(tmp_path: Path, capsys):
    collect_result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )
    assert collect_result == 0
    assert main(["extract", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    assert (
        main(
            [
                "draft-memo",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--perspective",
                "PERSP-OPS-001",
            ]
        )
        == 0
    )
    memo_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-draft-report.json"
    memo_id = json.loads(memo_report_path.read_text(encoding="utf-8"))["draft_memo_refs"][0]
    memo_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
    memo = json.loads(memo_path.read_text(encoding="utf-8"))
    memo["review_status"] = "flagged_conflict"
    memo["status"] = "flagged_conflict"
    memo_path.write_text(json.dumps(memo, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    review_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-review-report.json"
    review_report_path.write_text(
        json.dumps(
            {
                "reviewed_memo_refs": [memo_id],
                "duplicate_memo_refs": [],
                "conflict_memo_refs": [memo_id],
                "clean_memo_refs": [],
                "policy_refs": ["HISYS-FR-MEM-004", "HISYS-T-013"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    assert main(["decide-alerts", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    capsys.readouterr()

    result = main(["decide-alerts", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "alert_decisions: 0" in captured.out
    assert "non_escalation_decisions: 1" in captured.out
    assert "suppressed_memos: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["alert_decision_refs"] == []
    assert report["suppressed_memo_refs"] == [memo_id]
    suppressed_id = report["non_escalation_decision_refs"][0]
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{suppressed_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["trigger_reason"] == "suppression_window_duplicate_alert"
    assert decision["status"] == "suppressed"



def test_decide_alerts_command_requests_approval_for_high_impact_candidate(tmp_path: Path, capsys):
    collect_result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )
    assert collect_result == 0
    assert main(["extract", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    assert (
        main(
            [
                "draft-memo",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--perspective",
                "PERSP-OPS-001",
            ]
        )
        == 0
    )
    memo_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-draft-report.json"
    memo_id = json.loads(memo_report_path.read_text(encoding="utf-8"))["draft_memo_refs"][0]
    memo_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
    memo = json.loads(memo_path.read_text(encoding="utf-8"))
    memo["review_status"] = "flagged_conflict"
    memo["status"] = "flagged_conflict"
    memo_path.write_text(json.dumps(memo, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    review_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-review-report.json"
    review_report_path.write_text(
        json.dumps(
            {
                "reviewed_memo_refs": [memo_id],
                "duplicate_memo_refs": [],
                "conflict_memo_refs": [memo_id],
                "clean_memo_refs": [],
                "policy_refs": ["HISYS-FR-MEM-004", "HISYS-T-013"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    capsys.readouterr()

    result = main(
        [
            "decide-alerts",
            "--instance",
            str(tmp_path),
            "--date",
            "20260508",
            "--conflict-severity",
            "high",
            "--target-channel",
            "discord:#ops",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "alert_decisions: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    alert_id = report["alert_decision_refs"][0]
    alert_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    alert = json.loads(alert_path.read_text(encoding="utf-8"))
    assert alert["severity"] == "high"
    assert alert["approval_status"] == "requested"
    assert alert["status"] == "needs_approval"
    assert alert["action_taken"] == "none"
    assert alert["target_channel"] == "discord:#ops"



def test_review_alert_approval_command_updates_requested_decision(tmp_path: Path, capsys):
    _prepare_flagged_conflict_memo(tmp_path, capsys)
    assert (
        main(
            [
                "decide-alerts",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--conflict-severity",
                "high",
                "--target-channel",
                "discord:#ops",
            ]
        )
        == 0
    )
    decision_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json"
    alert_id = json.loads(decision_report_path.read_text(encoding="utf-8"))["alert_decision_refs"][0]
    capsys.readouterr()

    result = main(
        [
            "review-alert-approval",
            "--instance",
            str(tmp_path),
            "--date",
            "20260508",
            "--alert-id",
            alert_id,
            "--outcome",
            "approved",
            "--rationale",
            "fixture approval via CLI",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "alert approval transition" in captured.out
    assert "previous: requested/needs_approval" in captured.out
    assert "new: approved/pending" in captured.out
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["approval_status"] == "approved"
    assert decision["status"] == "pending"
    assert decision["action_taken"] == "none"
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-approval-transition-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["alert_decision_ref"] == alert_id
    assert report["new_approval_status"] == "approved"



def test_plan_alert_actions_command_writes_dry_run_action_plan(tmp_path: Path, capsys):
    _prepare_flagged_conflict_memo(tmp_path, capsys)
    assert (
        main(
            [
                "decide-alerts",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--conflict-severity",
                "high",
                "--target-channel",
                "discord:#ops",
            ]
        )
        == 0
    )
    decision_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json"
    alert_id = json.loads(decision_report_path.read_text(encoding="utf-8"))["alert_decision_refs"][0]
    capsys.readouterr()

    result = main(["plan-alert-actions", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "alert action plan run" in captured.out
    assert "action_plans: 1" in captured.out
    assert "would_send: 0" in captured.out
    assert "blocked: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-action-plan-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["alert_decision_refs"] == [alert_id]
    plan_id = report["action_plan_refs"][0]
    plan_path = tmp_path / "data" / "alert-action-plans" / "20260508" / f"{plan_id}.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["alert_decision_ref"] == alert_id
    assert plan["would_send"] is False
    assert plan["blocked_reason"] == "approval_required"
    assert plan["live_delivery_permitted"] is False
    assert plan["action_taken"] == "none"



def test_plan_alert_actions_command_marks_approved_decision_as_dry_run_send_candidate(
    tmp_path: Path,
    capsys,
):
    _prepare_flagged_conflict_memo(tmp_path, capsys)
    assert (
        main(
            [
                "decide-alerts",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--conflict-severity",
                "high",
                "--target-channel",
                "discord:#ops",
            ]
        )
        == 0
    )
    decision_report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json"
    alert_id = json.loads(decision_report_path.read_text(encoding="utf-8"))["alert_decision_refs"][0]
    assert (
        main(
            [
                "review-alert-approval",
                "--instance",
                str(tmp_path),
                "--date",
                "20260508",
                "--alert-id",
                alert_id,
                "--outcome",
                "approved",
                "--rationale",
                "fixture approval for dry-run send candidate",
            ]
        )
        == 0
    )
    capsys.readouterr()

    result = main(["plan-alert-actions", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "would_send: 1" in captured.out
    assert "blocked: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-action-plan-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    plan_id = report["action_plan_refs"][0]
    assert report["would_send_refs"] == [plan_id]
    assert report["blocked_refs"] == [plan_id]
    plan_path = tmp_path / "data" / "alert-action-plans" / "20260508" / f"{plan_id}.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["alert_decision_ref"] == alert_id
    assert plan["approval_required"] is False
    assert plan["would_send"] is True
    assert plan["blocked_reason"] == "live_delivery_disabled"
    assert plan["live_delivery_permitted"] is False
    assert plan["action_taken"] == "none"



def test_execute_alert_actions_command_records_disabled_connector_block(tmp_path: Path, capsys):
    _prepare_flagged_conflict_memo(tmp_path, capsys)
    assert main([
        "decide-alerts", "--instance", str(tmp_path), "--date", "20260508",
        "--conflict-severity", "high", "--target-channel", "discord:#ops",
    ]) == 0
    alert_id = json.loads((tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json").read_text(encoding="utf-8"))["alert_decision_refs"][0]
    assert main([
        "review-alert-approval", "--instance", str(tmp_path), "--date", "20260508",
        "--alert-id", alert_id, "--outcome", "approved", "--rationale", "fixture connector test",
    ]) == 0
    assert main(["plan-alert-actions", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    capsys.readouterr()

    result = main(["execute-alert-actions", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "alert connector execution" in captured.out
    assert "sent: 0" in captured.out
    assert "blocked: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-connector-execution-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    exec_id = report["execution_refs"][0]
    execution_path = tmp_path / "data" / "alert-connector-executions" / "20260508" / f"{exec_id}.json"
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    assert execution["would_send"] is True
    assert execution["live_delivery_permitted"] is False
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "live_delivery_disabled"
    assert execution["action_taken"] == "none"



def test_request_browser_dars_review_consumes_chief_editor_artifact_and_flags_adversarial_questions(tmp_path: Path, capsys):
    date = "20260510"
    request_id = "HISYS-REQ-BROWSER-DARS-001"
    matrix_ref = f"data/competitive-matrices/{date}/MATRIX-{request_id}-BROWSER.json"
    sufficiency_ref = f"data/evidence-sufficiency/{date}/SUFF-{request_id}-BROWSER.json"
    chief_ref = f"data/chief-editor-reviews/{date}/CHIEF-REVIEW-{request_id}-BROWSER.json"
    (tmp_path / matrix_ref).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / matrix_ref).write_text(
        json.dumps(
            {
                "schema_id": "hisys.browser_investigation.competitive_matrix",
                "rows": [
                    {
                        "company_or_source": "DUNLEE | LMB Tube Technology",
                        "technology_signals": "liquid metal bearing",
                        "competitive_signal_strength": "high",
                        "evidence_refs": ["EV-DUNLEE"],
                    },
                    {
                        "company_or_source": "Industrial X-ray Tubes - Varex Imaging",
                        "technology_signals": "stable dose/resolution, customized tube design",
                        "competitive_signal_strength": "high",
                        "evidence_refs": ["EV-VAREX"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / sufficiency_ref).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / sufficiency_ref).write_text(
        json.dumps(
            {
                "review_readiness": "ready_for_fair_chief_editor_and_devil_review",
                "chief_editor_decision_allowed": True,
                "devil_review_allowed": True,
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / chief_ref).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / chief_ref).write_text(
        json.dumps(
            {
                "schema_id": "hisys.chief_editor.browser_investigation_review",
                "request_id": request_id,
                "decision": "accept_for_devil_dars_adversarial_review",
                "basis_refs": {"competitive_matrix": matrix_ref, "evidence_sufficiency": sufficiency_ref},
                "chief_editor_questions_for_devil_dars": [
                    "Are Dunlee liquid-metal-bearing claims independently supported?",
                    "Are Varex breadth claims comparable to COMET or just marketing scope?",
                ],
            }
        ),
        encoding="utf-8",
    )

    result = main([
        "request-browser-dars-review",
        "--instance", str(tmp_path),
        "--date", date,
        "--chief-editor-review-ref", chief_ref,
        "--producer-id", "dars-browser-test",
    ])

    captured = capsys.readouterr()
    assert result == 0
    assert "browser dars review" in captured.out
    review_ref = f"data/dars-browser-reviews/{date}/DARS-REVIEW-{request_id}-BROWSER.json"
    review = json.loads((tmp_path / review_ref).read_text(encoding="utf-8"))
    assert review["decision"] == "requires_revision_before_final_acceptance"
    assert review["allowed_actions"] == "advisory_only"
    assert review["external_call_made"] is False
    assert review["chief_editor_review_ref"] == chief_ref
    assert "Dunlee" in "\n".join(review["adversarial_findings"])
    handoff_ref = f"data/agent-handoffs/{date}/HANDOFF-DARS-{request_id}-BROWSER.json"
    handoff = json.loads((tmp_path / handoff_ref).read_text(encoding="utf-8"))
    assert handoff["target_agent_system"] == "DARS"
    assert handoff["allowed_actions"] == "advisory_only"
    assert chief_ref in handoff["evidence_bundle"]


def test_resolve_browser_dars_revisions_marks_segment_and_corroboration_ready(tmp_path: Path, capsys):
    date = "20260510"
    request_id = "HISYS-REQ-BROWSER-REVISION-001"
    matrix_ref = f"data/competitive-matrices/{date}/MATRIX-{request_id}-BROWSER.json"
    chief_ref = f"data/chief-editor-reviews/{date}/CHIEF-REVIEW-{request_id}-BROWSER.json"
    dars_ref = f"data/dars-browser-reviews/{date}/DARS-REVIEW-{request_id}-BROWSER.json"
    (tmp_path / matrix_ref).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / matrix_ref).write_text(
        json.dumps(
            {
                "schema_id": "hisys.browser_investigation.competitive_matrix",
                "rows": [
                    {
                        "company_or_source": "DUNLEE | LMB Tube Technology",
                        "technology_signals": "liquid metal bearing for CT tube cooling",
                        "competitive_signal_strength": "high",
                        "segment": "ct",
                        "corroborating_evidence_class": "patent",
                        "evidence_refs": ["EV-DUNLEE-PATENT"],
                    },
                    {
                        "company_or_source": "Industrial X-ray Tubes - Varex Imaging",
                        "technology_signals": "stable dose/resolution for NDT inspection",
                        "competitive_signal_strength": "high",
                        "segment": "industrial_ndt",
                        "corroborating_evidence_class": "datasheet_or_specification",
                        "evidence_refs": ["EV-VAREX-DATASHEET"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / chief_ref).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / chief_ref).write_text(
        json.dumps(
            {
                "schema_id": "hisys.chief_editor.browser_investigation_review",
                "request_id": request_id,
                "decision": "accept_for_devil_dars_adversarial_review",
                "basis_refs": {"competitive_matrix": matrix_ref},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / dars_ref).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / dars_ref).write_text(
        json.dumps(
            {
                "schema_id": "hisys.dars.browser_investigation_review",
                "request_id": request_id,
                "chief_editor_review_ref": chief_ref,
                "decision": "requires_revision_before_final_acceptance",
                "required_revisions": [
                    "Normalize conclusions by segment: CT, medical/dental, industrial/NDT, analytical XRF/XRD, and security/irradiation.",
                    "Map every high-strength row to at least one corroborating evidence class: patent, datasheet/specification, distributor/spec page, filing, or paper.",
                ],
                "allowed_actions": "advisory_only",
                "external_call_made": False,
                "mutation_performed": False,
            }
        ),
        encoding="utf-8",
    )

    result = main([
        "resolve-browser-dars-revisions",
        "--instance", str(tmp_path),
        "--date", date,
        "--dars-review-ref", dars_ref,
        "--producer-id", "revision-test",
    ])

    captured = capsys.readouterr()
    assert result == 0
    assert "ready_for_final_acceptance_review" in captured.out
    revision_ref = f"data/browser-dars-revision-resolutions/{date}/REVISION-{request_id}-BROWSER.json"
    revision = json.loads((tmp_path / revision_ref).read_text(encoding="utf-8"))
    assert revision["decision"] == "ready_for_final_acceptance_review"
    assert revision["segment_normalization_status"] == "complete"
    assert revision["corroboration_mapping_status"] == "complete"
    assert revision["final_acceptance_allowed"] is True
    assert revision["external_call_made"] is False
    assert revision["mutation_performed"] is False
    assert revision["remaining_blockers"] == []


def test_request_dars_critique_command_records_advisory_result(tmp_path: Path, capsys):
    _prepare_flagged_conflict_memo(tmp_path, capsys)
    assert main([
        "decide-alerts", "--instance", str(tmp_path), "--date", "20260508",
        "--conflict-severity", "high", "--target-channel", "discord:#ops",
    ]) == 0
    alert_id = json.loads((tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json").read_text(encoding="utf-8"))["alert_decision_refs"][0]
    assert main([
        "review-alert-approval", "--instance", str(tmp_path), "--date", "20260508",
        "--alert-id", alert_id, "--outcome", "approved", "--rationale", "fixture dars test",
    ]) == 0
    assert main(["plan-alert-actions", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    assert main(["execute-alert-actions", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    exec_report = json.loads((tmp_path / "reports" / "run-summaries" / "20260508" / "alert-connector-execution-report.json").read_text(encoding="utf-8"))
    execution_id = exec_report["execution_refs"][0]
    capsys.readouterr()

    result = main([
        "request-dars-critique", "--instance", str(tmp_path), "--date", "20260508",
        "--source-execution-id", execution_id,
        "--critique-text", "Confidence overstated; cite raw payload.",
    ])

    captured = capsys.readouterr()
    assert result == 0
    assert "dars critique" in captured.out
    assert "handoffs: 1" in captured.out
    assert "critiques: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "dars-critique-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["handoff_refs"]
    assert report["critique_refs"]
    assert report["linked_execution_refs"] == [execution_id]
    handoff_id = report["handoff_refs"][0]
    critique_id = report["critique_refs"][0]
    assert handoff_id.startswith("HANDOFF-")
    assert critique_id.startswith("CRITIQUE-")
    critique = json.loads((tmp_path / "data" / "agent-critiques" / "20260508" / f"{critique_id}.json").read_text(encoding="utf-8"))
    assert critique["handoff_ref"] == handoff_id
    assert critique["source_execution_ref"] == execution_id



def test_request_dars_critique_command_can_loop_back_without_dars_implementation(tmp_path: Path, capsys):
    _prepare_flagged_conflict_memo(tmp_path, capsys)
    assert main([
        "decide-alerts", "--instance", str(tmp_path), "--date", "20260508",
        "--conflict-severity", "high", "--target-channel", "discord:#ops",
    ]) == 0
    alert_id = json.loads((tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json").read_text(encoding="utf-8"))["alert_decision_refs"][0]
    assert main([
        "review-alert-approval", "--instance", str(tmp_path), "--date", "20260508",
        "--alert-id", alert_id, "--outcome", "approved", "--rationale", "fixture loopback dars test",
    ]) == 0
    assert main(["plan-alert-actions", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    assert main(["execute-alert-actions", "--instance", str(tmp_path), "--date", "20260508"]) == 0
    exec_report = json.loads((tmp_path / "reports" / "run-summaries" / "20260508" / "alert-connector-execution-report.json").read_text(encoding="utf-8"))
    execution_id = exec_report["execution_refs"][0]
    capsys.readouterr()

    result = main([
        "request-dars-critique", "--instance", str(tmp_path), "--date", "20260508",
        "--source-execution-id", execution_id,
    ])

    captured = capsys.readouterr()
    assert result == 0
    assert "dars_backend: loopback_placeholder" in captured.out
    report = json.loads((tmp_path / "reports" / "run-summaries" / "20260508" / "dars-critique-report.json").read_text(encoding="utf-8"))
    critique_id = report["critique_refs"][0]
    critique = json.loads((tmp_path / "data" / "agent-critiques" / "20260508" / f"{critique_id}.json").read_text(encoding="utf-8"))
    assert critique["dars_backend"] == "loopback_placeholder"
    assert critique["external_call_made"] is False
    assert critique["action_taken"] == "none"



def test_decide_alerts_command_uses_analysis_only_product_from_config(tmp_path: Path, capsys):
    _prepare_flagged_conflict_memo(tmp_path, capsys)
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "chief-editor.yaml").write_text(
        "product_type: analysis_only\n"
        "target_channel: discord:#ops\n"
        "conflict_severity: high\n",
        encoding="utf-8",
    )

    result = main(["decide-alerts", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "product_type: analysis_only" in captured.out
    report = json.loads((tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json").read_text(encoding="utf-8"))
    alert_id = report["alert_decision_refs"][0]
    decision = json.loads((tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json").read_text(encoding="utf-8"))
    assert decision["severity"] == "high"
    assert decision["target_channel"] is None
    assert decision["approval_status"] == "not_required"
    assert decision["status"] == "closed"
    assert decision["action_taken"] == "none"



def test_extract_command_rejects_missing_observation_partition(tmp_path: Path, capsys):
    result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 1
    assert "no raw observations found" in captured.err


def test_collect_command_rejects_unknown_source_without_unhandled_exception(tmp_path: Path, capsys):
    result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-NOT-REGISTERED-001",
            "--date",
            "20260508",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "no observations collected" in captured.err
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["skipped_source_ids"] == ["SRC-NOT-REGISTERED-001"]
    assert "SRC-NOT-REGISTERED-001" in report["adapter_errors"]
