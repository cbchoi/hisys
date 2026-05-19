"""DARS critic panel adapter registry tests.

Traceability:
- HISYS-FR-DARS-CP-001
- HISYS-FR-DARS-CP-007
- M-CP-EXT-1 in docs/plans/dars-critic-panel-platform-runtime-next.md
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
    candidate.write_text(json.dumps({"candidate_id": "CAND-001"}), encoding="utf-8")
    evidence.write_text(json.dumps({"evidence_id": "EVID-001"}), encoding="utf-8")
    rubric.write_text(json.dumps({"rubric_id": "RUBRIC-DARS-001"}), encoding="utf-8")
    return (
        str(candidate.relative_to(tmp_path)),
        [str(evidence.relative_to(tmp_path))],
        str(rubric.relative_to(tmp_path)),
    )


def test_critic_adapter_registry_blocks_external_without_explicit_allow_flag():
    from hisys.agents.dars_panel import CriticAdapterRegistry, FixtureCriticAdapter

    registry = CriticAdapterRegistry(external_dispatch_allowed=False)
    registry.register(
        FixtureCriticAdapter(
            critic_role="logical_devil",
            backend_id="external-dars",
            adapter_class="external",
        )
    )

    with pytest.raises(PermissionError, match="external adapter dispatch is disabled"):
        registry.resolve(
            critic_role="logical_devil",
            backend_id="external-dars",
            approval_ref="APPROVAL-DARS-001",
        )


def test_critic_adapter_registry_rejects_duplicate_role_backend_pair():
    from hisys.agents.dars_panel import CriticAdapterRegistry, FixtureCriticAdapter

    registry = CriticAdapterRegistry()
    registry.register(FixtureCriticAdapter(critic_role="logical_devil", backend_id="fixture-logical"))

    with pytest.raises(ValueError, match="duplicate critic adapter"):
        registry.register(FixtureCriticAdapter(critic_role="logical_devil", backend_id="fixture-logical"))


def test_fixture_critic_adapter_records_declared_outcome_without_keyword_match():
    from hisys.agents.dars_panel import FixtureCriticAdapter

    adapter = FixtureCriticAdapter(
        critic_role="logical_devil",
        backend_id="fixture-logical-outcome-001",
        fixture_outcome="failed",
    )

    assert adapter.fixture_outcome == "failed"
    assert "fail" not in adapter.backend_id


def test_panel_runtime_isolates_failed_adapter_outcome_without_keyword_match(tmp_path: Path):
    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
        FixtureCriticAdapter,
    )

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()
    registry.register(
        FixtureCriticAdapter(
            critic_role="logical_devil",
            backend_id="fixture-logical-outcome-001",
            fixture_outcome="failed",
        )
    )
    registry.register(
        FixtureCriticAdapter(
            critic_role="evidence_governance_devil",
            backend_id="fixture-evidence-outcome-001",
            fixture_outcome="completed",
        )
    )
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-1",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-outcome-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
            DarsCriticRoleConfig(
                critic_id="evidence-devil",
                critic_role="evidence_governance_devil",
                backend_id="fixture-evidence-outcome-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["source_quality"],
            ),
        ],
    )

    result = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        adapter_registry=registry,
    ).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-EXT-FAIL",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    statuses = [task.status for task in result.task_results]
    assert statuses == ["failed", "completed"]
    assert len(result.critique_refs) == 1


def test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role(tmp_path: Path):
    """M-CP-EXT-4: explicit registry without a matching adapter -> typed blocked task."""

    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()  # explicit, no adapters registered

    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-4",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-unregistered",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
        ],
    )

    result = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        adapter_registry=registry,
    ).run_round(
        yyyymmdd="20260520",
        request_id="REQ-DARS-CP-EXT-4",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    assert [task.status for task in result.task_results] == ["blocked"]
    assert result.task_results[0].critique_ref is None
    assert result.task_results[0].external_call_made is False
    assert "no critic adapter registered" in (result.task_results[0].error_message or "")
    assert result.critique_refs == []
    assert len(result.execution_boundary_refs) == 1

    boundary_path = tmp_path / result.execution_boundary_refs[0]
    payload = json.loads(boundary_path.read_text(encoding="utf-8"))
    assert payload["dispatch_decision"] == "blocked"
    assert "no critic adapter registered" in payload["dispatch_reason"]
    assert payload["critique_ref"] is None
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["action_authorized"] is False
    assert payload["advisory_only"] is True
    assert payload["requires_human_review"] is True
