"""DARS subsystem package public-seam tests."""

from __future__ import annotations



def test_dars_subsystem_manifest_records_role_and_lock_flags() -> None:
    from hisys.dars import DarsSubsystemManifest, get_dars_subsystem_manifest

    manifest = get_dars_subsystem_manifest()

    assert isinstance(manifest, DarsSubsystemManifest)
    assert manifest.role == "dars"
    assert manifest.responsibility == "developmental opposition/advisory critique"
    assert manifest.advisory_only is True
    assert manifest.requires_human_review is True
    assert manifest.live_external_action_authorized is False
    assert manifest.completion_upgrade_claimed is False
    assert manifest.raw_provider_api_readiness is False
    assert manifest.adapter_native_readiness is False
    assert manifest.bounded_unattended_advisory_operation_ready is False



def test_dars_subsystem_package_reexports_existing_bounded_agent_seams() -> None:
    import hisys.dars as dars
    from hisys.agents import dars as legacy_dars
    from hisys.agents import dars_protocol as legacy_protocol

    assert dars.DarsRuntime is legacy_dars.DarsRuntime
    assert dars.DarsCritiqueRecord is legacy_dars.DarsCritiqueRecord
    assert dars.DarsCritiqueReport is legacy_dars.DarsCritiqueReport
    assert dars.DarsRequestEnvelope is legacy_protocol.DarsRequestEnvelope
    assert dars.DarsResponseEnvelope is legacy_protocol.DarsResponseEnvelope



def test_dars_subsystem_manifest_exports_serializable_boundary_packet() -> None:
    from dataclasses import asdict

    from hisys.dars import get_dars_subsystem_manifest

    packet = asdict(get_dars_subsystem_manifest())

    assert packet == {
        "role": "dars",
        "responsibility": "developmental opposition/advisory critique",
        "advisory_only": True,
        "requires_human_review": True,
        "live_external_action_authorized": False,
        "completion_upgrade_claimed": False,
        "raw_provider_api_readiness": False,
        "adapter_native_readiness": False,
        "bounded_unattended_advisory_operation_ready": False,
    }



def test_dars_subsystem_invocation_modes_match_architecture_doc() -> None:
    from hisys.dars import (
        DarsSubsystemInvocationMode,
        get_dars_subsystem_invocation_modes,
    )

    modes = get_dars_subsystem_invocation_modes()

    assert isinstance(modes, tuple)
    for mode in modes:
        assert isinstance(mode, DarsSubsystemInvocationMode)
        assert mode.advisory_only is True
        assert mode.requires_human_review is True

    mode_ids = tuple(mode.mode_id for mode in modes)
    assert mode_ids == ("dars-only", "full-loop")

    by_id = {mode.mode_id: mode for mode in modes}
    assert by_id["dars-only"].dars_role == "sole_subsystem"
    assert by_id["dars-only"].description == (
        "developmental opposition and advisory critique"
    )
    assert by_id["full-loop"].dars_role == "developmental_opposition_stage"
    assert by_id["full-loop"].description == "Altas -> DARS -> Judge"



def test_dars_subsystem_invocation_modes_exclude_altas_only_and_judge_only() -> None:
    from hisys.dars import get_dars_subsystem_invocation_modes

    mode_ids = {mode.mode_id for mode in get_dars_subsystem_invocation_modes()}

    assert "altas-only" not in mode_ids
    assert "judge-only" not in mode_ids



def test_dars_subsystem_invocation_modes_are_serializable() -> None:
    from dataclasses import asdict

    from hisys.dars import get_dars_subsystem_invocation_modes

    packets = [asdict(mode) for mode in get_dars_subsystem_invocation_modes()]

    assert packets == [
        {
            "mode_id": "dars-only",
            "description": "developmental opposition and advisory critique",
            "dars_role": "sole_subsystem",
            "advisory_only": True,
            "requires_human_review": True,
        },
        {
            "mode_id": "full-loop",
            "description": "Altas -> DARS -> Judge",
            "dars_role": "developmental_opposition_stage",
            "advisory_only": True,
            "requires_human_review": True,
        },
    ]
