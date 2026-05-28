from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DARS_RALPH = ROOT / "src" / "hisys" / "dars" / "ralph.md"


def test_dars_subsystem_has_local_ralph_control_file() -> None:
    assert DARS_RALPH.exists()
    content = DARS_RALPH.read_text(encoding="utf-8")
    assert "# DARS RLOO Control" in content
    assert "subsystem: dars" in content
    assert "scope: DARS only" in content


def test_dars_subsystem_ralph_preserves_authority_locks() -> None:
    content = DARS_RALPH.read_text(encoding="utf-8")
    required_locks = [
        "advisory_only: true",
        "requires_human_review: true",
        "live_external_action_authorized: false",
        "completion_upgrade_claimed: false",
        "bounded_unattended_advisory_operation_ready: false",
    ]
    for required_lock in required_locks:
        assert required_lock in content
