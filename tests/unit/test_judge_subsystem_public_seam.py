"""Judge subsystem package public-seam tests."""

from __future__ import annotations


def test_judge_subsystem_manifest_records_role_and_lock_flags() -> None:
    from hisys.judge import JudgeSubsystemManifest, get_judge_subsystem_manifest

    manifest = get_judge_subsystem_manifest()

    assert isinstance(manifest, JudgeSubsystemManifest)
    assert manifest.role == "judge"
    assert manifest.responsibility == "bounded advisory judgment/gates"
    assert manifest.advisory_only is True
    assert manifest.requires_human_review is True
    assert manifest.live_external_action_authorized is False
    assert manifest.mutation_authorized is False
    assert manifest.publication_authorized is False
    assert manifest.remote_push_authorized is False
    assert manifest.human_review_removal_authorized is False


def test_judge_subsystem_manifest_exports_serializable_boundary_packet() -> None:
    from dataclasses import asdict

    from hisys.judge import get_judge_subsystem_manifest

    packet = asdict(get_judge_subsystem_manifest())

    assert packet == {
        "role": "judge",
        "responsibility": "bounded advisory judgment/gates",
        "advisory_only": True,
        "requires_human_review": True,
        "live_external_action_authorized": False,
        "mutation_authorized": False,
        "publication_authorized": False,
        "remote_push_authorized": False,
        "human_review_removal_authorized": False,
    }


def test_judge_subsystem_invocation_modes_match_architecture_doc() -> None:
    from hisys.judge import (
        JudgeSubsystemInvocationMode,
        get_judge_subsystem_invocation_modes,
    )

    modes = get_judge_subsystem_invocation_modes()

    assert isinstance(modes, tuple)
    for mode in modes:
        assert isinstance(mode, JudgeSubsystemInvocationMode)
        assert mode.advisory_only is True
        assert mode.requires_human_review is True

    mode_ids = tuple(mode.mode_id for mode in modes)
    assert mode_ids == ("judge-only", "full-loop")

    by_id = {mode.mode_id: mode for mode in modes}
    assert by_id["judge-only"].judge_role == "sole_subsystem"
    assert by_id["judge-only"].description == (
        "bounded advisory judgment over already prepared packets"
    )
    assert by_id["full-loop"].judge_role == "bounded_advisory_decision_stage"
    assert by_id["full-loop"].description == "Altas -> DARS -> Judge"


def test_judge_subsystem_invocation_modes_exclude_altas_only_and_dars_only() -> None:
    from hisys.judge import get_judge_subsystem_invocation_modes

    mode_ids = {mode.mode_id for mode in get_judge_subsystem_invocation_modes()}

    assert "altas-only" not in mode_ids
    assert "dars-only" not in mode_ids


def test_judge_subsystem_invocation_modes_are_serializable() -> None:
    from dataclasses import asdict

    from hisys.judge import get_judge_subsystem_invocation_modes

    packets = [asdict(mode) for mode in get_judge_subsystem_invocation_modes()]

    assert packets == [
        {
            "mode_id": "judge-only",
            "description": "bounded advisory judgment over already prepared packets",
            "judge_role": "sole_subsystem",
            "advisory_only": True,
            "requires_human_review": True,
        },
        {
            "mode_id": "full-loop",
            "description": "Altas -> DARS -> Judge",
            "judge_role": "bounded_advisory_decision_stage",
            "advisory_only": True,
            "requires_human_review": True,
        },
    ]
