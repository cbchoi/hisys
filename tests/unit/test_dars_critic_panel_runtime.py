"""DARS critic panel runtime TDD anchors.

Traceability:
- Requirements: HISYS-FR-DARS-CP-001..008, HISYS-NFR-DARS-CP-001..002
- SDD: docs/design/dars-critic-panel-runtime-sdd.md
- STD: docs/test/dars-critic-panel-runtime-std.md

These tests are intentionally written before production implementation. The
initial RED result is expected to fail because ``hisys.agents.dars_panel`` does
not exist yet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.config.instance import InstanceRoot


def _candidate_fixture(tmp_path: Path) -> tuple[str, list[str], str]:
    data_dir = tmp_path / "data" / "dars-panel-fixtures" / "20260519"
    data_dir.mkdir(parents=True)
    candidate = data_dir / "candidate-001.json"
    evidence = data_dir / "evidence-001.json"
    rubric = data_dir / "rubric-001.json"
    candidate.write_text(json.dumps({"candidate_id": "CAND-001", "claim": "candidate requires critique"}), encoding="utf-8")
    evidence.write_text(json.dumps({"evidence_id": "EVID-001", "source_refs": ["SRC-001"]}), encoding="utf-8")
    rubric.write_text(json.dumps({"rubric_id": "RUBRIC-DARS-001", "version": "0.1.0"}), encoding="utf-8")
    return str(candidate.relative_to(tmp_path)), [str(evidence.relative_to(tmp_path))], str(rubric.relative_to(tmp_path))


def _two_role_panel_config(rubric_ref: str):
    from hisys.agents.dars_panel import DarsCriticPanelConfig, DarsCriticRoleConfig

    return DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-001",
        max_parallel_critics=2,
        failure_policy="continue_collect_errors",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity", "unsupported_claims"],
                enabled=True,
                output_contract="DarsCritiqueRecord",
            ),
            DarsCriticRoleConfig(
                critic_id="evidence-devil",
                critic_role="evidence_governance_devil",
                backend_id="fixture-evidence",
                rubric_ref=rubric_ref,
                critique_dimensions=["missing_evidence", "source_quality"],
                enabled=True,
                output_contract="DarsCritiqueRecord",
            ),
        ],
    )


def test_dars_critic_panel_config_validates_two_advisory_roles(tmp_path: Path):
    """HISYS-T-DARS-CP-001 / HISYS-FR-DARS-CP-001."""
    _, _, rubric_ref = _candidate_fixture(tmp_path)
    config = _two_role_panel_config(rubric_ref)

    assert config.advisory_only is True
    assert config.default_output_contract == "DarsCritiqueRecord"
    assert [critic.critic_id for critic in config.critics] == ["logical-devil", "evidence-devil"]
    assert all(critic.mutation_allowed is False for critic in config.critics)
    assert all(critic.external_call_allowed is False for critic in config.critics)


def test_dars_round_plan_creates_independent_critic_tasks_before_synthesis(tmp_path: Path):
    """HISYS-T-DARS-CP-002 / HISYS-FR-DARS-CP-002."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    runtime = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path))

    plan = runtime.build_round_plan(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-001",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=_two_role_panel_config(rubric_ref),
    )

    assert len(plan.critic_tasks) == 2
    assert {task.critic_role for task in plan.critic_tasks} == {"logical_devil", "evidence_governance_devil"}
    assert all(task.candidate_ref == candidate_ref for task in plan.critic_tasks)
    assert all(task.expected_output_contract == "DarsCritiqueRecord" for task in plan.critic_tasks)
    assert all(edge.to_task_id == plan.synthesis_task.task_id for edge in plan.edges)


def test_dars_panel_runtime_writes_advisory_critique_artifacts(tmp_path: Path):
    """HISYS-T-DARS-CP-003 / HISYS-FR-DARS-CP-003."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    runtime = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path))

    result = runtime.run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-001",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=_two_role_panel_config(rubric_ref),
    )

    assert len(result.critique_refs) == 2
    for critique_ref in result.critique_refs:
        critique = json.loads((tmp_path / critique_ref).read_text(encoding="utf-8"))
        assert critique["allowed_actions"] == "advisory_only"
        assert critique["action_taken"] == "none"
        assert critique["external_call_made"] is False
        assert critique["mutation_performed"] is False


def test_dars_panel_runtime_persists_round_trace_lineage(tmp_path: Path):
    """HISYS-T-DARS-CP-004 / HISYS-FR-DARS-CP-004."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    result = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path)).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-TRACE",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=_two_role_panel_config(rubric_ref),
    )

    trace = json.loads((tmp_path / result.round_trace_ref).read_text(encoding="utf-8"))
    assert trace["candidate_ref"] == candidate_ref
    assert trace["critique_refs"] == result.critique_refs
    assert trace["synthesis_ref"] == result.synthesis_ref
    assert trace["advisory_only"] is True
    assert trace["requires_human_review"] is True


def test_dars_critique_synthesis_is_advisory_and_preserves_role_provenance(tmp_path: Path):
    """HISYS-T-DARS-CP-005 / HISYS-FR-DARS-CP-005, HISYS-FR-DARS-CP-008."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    result = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path)).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-SYN",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=_two_role_panel_config(rubric_ref),
    )

    synthesis = json.loads((tmp_path / result.synthesis_ref).read_text(encoding="utf-8"))
    assert synthesis["advisory_only"] is True
    assert synthesis["action_authorized"] is False
    assert synthesis["requires_human_review"] is True
    assert {item["critic_role"] for item in synthesis["role_provenance"]} == {"logical_devil", "evidence_governance_devil"}


def test_dars_round_plan_is_serial_compatible_with_bounded_parallel_policy(tmp_path: Path):
    """HISYS-T-DARS-CP-006 / HISYS-FR-DARS-CP-006."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    plan = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path)).build_round_plan(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-PAR",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=_two_role_panel_config(rubric_ref),
    )

    assert plan.execution_mode in {"serial", "bounded_parallel"}
    assert plan.max_parallel_critics == 2
    assert all(task.concurrency_group == "dars-critics" for task in plan.critic_tasks)


def test_dars_panel_blocks_external_backend_without_approval(tmp_path: Path):
    """HISYS-T-DARS-CP-007 / HISYS-FR-DARS-CP-007."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config = _two_role_panel_config(rubric_ref)
    config.critics[0].backend_id = "external-dars"
    config.critics[0].external_call_allowed = True
    config.critics[0].approval_ref = None

    result = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path)).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-BLOCK",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    assert result.task_results[0].status == "blocked"
    assert result.task_results[0].external_call_made is False


def test_dars_panel_artifacts_preserve_advisory_human_decision_separation(tmp_path: Path):
    """HISYS-T-DARS-CP-008 / HISYS-FR-DARS-CP-008."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    result = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path)).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-GOV",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=_two_role_panel_config(rubric_ref),
    )

    for artifact_ref in [*result.critique_refs, result.round_trace_ref, result.synthesis_ref]:
        artifact = json.loads((tmp_path / artifact_ref).read_text(encoding="utf-8"))
        assert artifact["advisory_only"] is True
        assert artifact["requires_human_review"] is True
        assert artifact.get("human_approved", False) is False


def test_dars_panel_isolates_one_critic_failure_and_reports_partial_evidence(tmp_path: Path):
    """HISYS-T-DARS-CP-009 / HISYS-NFR-DARS-CP-001."""
    from hisys.agents.dars_panel import DarsCriticPanelRuntime

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config = _two_role_panel_config(rubric_ref)
    config.critics[0].backend_id = "fixture-failing-critic"

    result = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path)).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-FAILURE",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    statuses = [task.status for task in result.task_results]
    assert "failed" in statuses
    assert "completed" in statuses
    synthesis = json.loads((tmp_path / result.synthesis_ref).read_text(encoding="utf-8"))
    assert synthesis["disposition"] == "needs_more_evidence"
