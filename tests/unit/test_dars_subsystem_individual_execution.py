"""DARS subsystem individual execution command tests.

These tests pin the DARS-only readiness command that lets DARS be invoked
independently of root-level RLOO orchestration via
``python3 -m hisys.dars.rloo --check --format json``.

The command must be deterministic, side-effect free, and stay inside the
DARS authority boundary recorded in ``src/hisys/dars/ralph.md`` and
``docs/design/hisys-subsystem-architecture.md``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DARS_RALPH = ROOT / "src" / "hisys" / "dars" / "ralph.md"


def _run_dars_rloo(*args: str) -> subprocess.CompletedProcess[str]:
    env_pythonpath = f"{SRC}:{ROOT}"
    return subprocess.run(
        [sys.executable, "-m", "hisys.dars.rloo", *args],
        cwd=str(ROOT),
        env={
            "PYTHONPATH": env_pythonpath,
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_dars_subsystem_rloo_module_is_importable_without_side_effects() -> None:
    from hisys.dars import rloo

    assert hasattr(rloo, "build_dars_subsystem_readiness_packet")
    assert callable(rloo.build_dars_subsystem_readiness_packet)


def test_dars_subsystem_rloo_check_json_returns_zero_and_valid_json() -> None:
    completed = _run_dars_rloo("--check", "--format", "json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert isinstance(payload, dict)


def test_dars_subsystem_rloo_check_json_records_subsystem_identity() -> None:
    completed = _run_dars_rloo("--check", "--format", "json")
    payload = json.loads(completed.stdout)

    assert payload["subsystem"] == "dars"
    assert payload["scope"] == "DARS only"
    assert payload["ready"] is True


def test_dars_subsystem_rloo_check_json_pins_authority_locks() -> None:
    completed = _run_dars_rloo("--check", "--format", "json")
    payload = json.loads(completed.stdout)

    locks = payload["authority_locks"]
    assert locks["advisory_only"] is True
    assert locks["requires_human_review"] is True
    assert locks["live_external_action_authorized"] is False
    assert locks["completion_upgrade_claimed"] is False
    assert locks["raw_provider_api_readiness"] is False
    assert locks["adapter_native_readiness"] is False
    assert locks["bounded_unattended_advisory_operation_ready"] is False
    assert locks["mutation_authorized"] is False
    assert locks["publication_authorized"] is False
    assert locks["remote_push_authorized"] is False


def test_dars_subsystem_rloo_check_json_records_controller_anchor() -> None:
    completed = _run_dars_rloo("--check", "--format", "json")
    payload = json.loads(completed.stdout)

    controller = payload["controller"]
    assert controller["exists"] is True
    assert controller["path"] == "src/hisys/dars/ralph.md"
    metadata = controller["metadata"]
    assert metadata["subsystem"] == "dars"
    assert metadata["scope"] == "DARS only"
    assert metadata["branch"] == "dars"
    assert metadata["package_root"] == "src/hisys/dars"
    assert metadata["architecture_ref"] == (
        "docs/design/hisys-subsystem-architecture.md"
    )
    assert isinstance(controller["current_next_safe_task"], str)
    assert controller["current_next_safe_task"].strip() != ""


def test_dars_subsystem_rloo_check_json_records_manifest_and_invocation_modes() -> None:
    completed = _run_dars_rloo("--check", "--format", "json")
    payload = json.loads(completed.stdout)

    assert payload["manifest"]["role"] == "dars"
    assert payload["manifest"]["advisory_only"] is True
    assert payload["manifest"]["requires_human_review"] is True

    mode_ids = [mode["mode_id"] for mode in payload["invocation_modes"]]
    assert mode_ids == ["dars-only", "full-loop"]
    assert "altas-only" not in mode_ids
    assert "judge-only" not in mode_ids


def test_dars_subsystem_rloo_check_json_records_no_side_effects() -> None:
    completed = _run_dars_rloo("--check", "--format", "json")
    payload = json.loads(completed.stdout)

    side_effects = payload["side_effects"]
    assert side_effects["performed_live_provider_call"] is False
    assert side_effects["performed_credential_lookup"] is False
    assert side_effects["performed_network_call"] is False
    assert side_effects["performed_remote_push"] is False
    assert side_effects["performed_vault_mutation"] is False
    assert side_effects["performed_evidence_mutation"] is False
    assert side_effects["performed_cross_subsystem_call"] is False


def test_dars_subsystem_rloo_check_runs_independently_of_root_orchestration() -> None:
    completed = _run_dars_rloo("--check", "--format", "json")
    payload = json.loads(completed.stdout)

    independence = payload["independence"]
    assert independence["depends_on_root_rloo"] is False
    assert independence["depends_on_altas"] is False
    assert independence["depends_on_judge"] is False
    assert independence["subsystem_locally_invocable"] is True


def test_dars_subsystem_rloo_check_does_not_mutate_controller_file() -> None:
    before = DARS_RALPH.read_text(encoding="utf-8")
    completed = _run_dars_rloo("--check", "--format", "json")
    assert completed.returncode == 0, completed.stderr
    after = DARS_RALPH.read_text(encoding="utf-8")
    assert before == after


def test_dars_subsystem_rloo_builder_function_returns_same_packet() -> None:
    from hisys.dars.rloo import build_dars_subsystem_readiness_packet

    packet = build_dars_subsystem_readiness_packet()

    assert packet["subsystem"] == "dars"
    assert packet["scope"] == "DARS only"
    assert packet["ready"] is True
    assert packet["authority_locks"]["advisory_only"] is True
    assert packet["authority_locks"]["requires_human_review"] is True
    assert packet["independence"]["subsystem_locally_invocable"] is True


def test_dars_subsystem_rloo_help_lists_check_and_format_flags() -> None:
    completed = _run_dars_rloo("--help")

    assert completed.returncode == 0, completed.stderr
    assert "--check" in completed.stdout
    assert "--format" in completed.stdout
