"""Judge subsystem-local RLOO entry point.

This module makes the Judge subsystem individually executable without depending
on root-level Hisys RLOO orchestration. It exposes a deterministic,
side-effect-free readiness/status command:

    PYTHONPATH=src:. python3 -m hisys.judge.rloo --check --format json

The command reads ``src/hisys/judge/ralph.md``, composes the Judge-only manifest
and invocation-mode seams from :mod:`hisys.judge`, and emits a machine-readable
packet that pins the Judge authority locks recorded in the controller and in
``docs/design/hisys-subsystem-architecture.md``.

The command does **not** call live providers, make raw provider API calls,
perform network requests, look up credentials, mutate vault or evidence stores,
push to remotes, or invoke other Hisys subsystems.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import (
    get_judge_subsystem_invocation_modes,
    get_judge_subsystem_manifest,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTROLLER_PATH = Path("src/hisys/judge/ralph.md")

_REQUIRED_LOCKS: tuple[tuple[str, bool], ...] = (
    ("advisory_only", True),
    ("requires_human_review", True),
    ("live_external_action_authorized", False),
    ("mutation_authorized", False),
    ("publication_authorized", False),
    ("remote_push_authorized", False),
    ("human_review_removal_authorized", False),
)

_METADATA_KEYS: tuple[str, ...] = (
    "subsystem",
    "scope",
    "architecture_ref",
    "branch",
    "package_root",
)


def _read_controller_text() -> str:
    return (_REPO_ROOT / _CONTROLLER_PATH).read_text(encoding="utf-8")


def _parse_controller_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for key in _METADATA_KEYS:
        match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
        if match is not None:
            metadata[key] = match.group(1)
    return metadata


def _parse_controller_locks(text: str) -> dict[str, bool]:
    locks: dict[str, bool] = {}
    for name, _ in _REQUIRED_LOCKS:
        match = re.search(
            rf"^{re.escape(name)}:\s*(true|false)\s*$",
            text,
            re.MULTILINE,
        )
        if match is not None:
            locks[name] = match.group(1) == "true"
    return locks


def _parse_current_next_safe_task(text: str) -> str:
    match = re.search(
        r"## Current next safe task\s*\n+```text\s*\n([^\n]+)\s*\n```",
        text,
    )
    if match is None:
        return ""
    return match.group(1).strip()


def _locks_match_required(parsed: dict[str, bool]) -> bool:
    for name, expected in _REQUIRED_LOCKS:
        if parsed.get(name) != expected:
            return False
    return True


def _yes_no(value: Any) -> str:
    return "yes" if value is True else "no"


def build_judge_subsystem_readiness_packet() -> dict[str, Any]:
    """Return a deterministic Judge subsystem readiness packet.

    The packet records the Judge subsystem identity, the controller anchor
    metadata, the Judge authority locks, the subsystem manifest, the documented
    invocation modes, and explicit side-effect/independence declarations. It is
    composed without any live external action.
    """

    text = _read_controller_text()
    metadata = _parse_controller_metadata(text)
    parsed_locks = _parse_controller_locks(text)
    locks = {name: parsed_locks.get(name, expected) for name, expected in _REQUIRED_LOCKS}
    current_task = _parse_current_next_safe_task(text)

    manifest = asdict(get_judge_subsystem_manifest())
    invocation_modes = [asdict(mode) for mode in get_judge_subsystem_invocation_modes()]

    controller_packet = {
        "path": str(_CONTROLLER_PATH),
        "exists": True,
        "metadata": metadata,
        "current_next_safe_task": current_task,
    }

    ready = (
        manifest["advisory_only"] is True
        and manifest["requires_human_review"] is True
        and manifest["live_external_action_authorized"] is False
        and manifest["mutation_authorized"] is False
        and manifest["publication_authorized"] is False
        and _locks_match_required(parsed_locks)
        and metadata.get("subsystem") == "judge"
        and metadata.get("scope") == "Judge only"
        and current_task != ""
    )

    return {
        "subsystem": "judge",
        "scope": "Judge only",
        "ready": ready,
        "controller": controller_packet,
        "authority_locks": locks,
        "manifest": manifest,
        "invocation_modes": invocation_modes,
        "independence": {
            "depends_on_root_rloo": False,
            "depends_on_altas": False,
            "depends_on_dars": False,
            "subsystem_locally_invocable": True,
        },
        "side_effects": {
            "performed_live_provider_call": False,
            "performed_credential_lookup": False,
            "performed_network_call": False,
            "performed_remote_push": False,
            "performed_vault_mutation": False,
            "performed_evidence_mutation": False,
            "performed_cross_subsystem_call": False,
        },
    }


def render_judge_subsystem_readiness_text(packet: dict[str, Any]) -> str:
    """Render a Judge subsystem readiness packet as deterministic text.

    The renderer is read-only: it consumes the already-built readiness packet,
    performs no I/O or external action, does not mutate the packet, and grants no
    execution authority. It exists so human reviewers and local agents can inspect
    Judge readiness without parsing the JSON packet.
    """

    controller = packet.get("controller", {})
    authority_locks = packet.get("authority_locks", {})
    independence = packet.get("independence", {})
    side_effects = packet.get("side_effects", {})
    status = "READY" if packet.get("ready") is True else "NOT READY"

    lines = [
        f"Judge Subsystem Readiness: {status}",
        f"Subsystem: {packet.get('subsystem', '')}",
        f"Scope: {packet.get('scope', '')}",
        f"Controller: {controller.get('path', '')}",
        f"Next safe task: {controller.get('current_next_safe_task', '')}",
        f"Advisory only: {_yes_no(authority_locks.get('advisory_only'))}",
        f"Requires human review: {_yes_no(authority_locks.get('requires_human_review'))}",
        f"Live external action authorized: {_yes_no(authority_locks.get('live_external_action_authorized'))}",
        f"Mutation authorized: {_yes_no(authority_locks.get('mutation_authorized'))}",
        f"Publication authorized: {_yes_no(authority_locks.get('publication_authorized'))}",
        f"Remote push authorized: {_yes_no(authority_locks.get('remote_push_authorized'))}",
        f"Human-review removal authorized: {_yes_no(authority_locks.get('human_review_removal_authorized'))}",
        f"Depends on root RLOO: {_yes_no(independence.get('depends_on_root_rloo'))}",
        f"Depends on Altas: {_yes_no(independence.get('depends_on_altas'))}",
        f"Depends on DARS: {_yes_no(independence.get('depends_on_dars'))}",
        f"Subsystem locally invocable: {_yes_no(independence.get('subsystem_locally_invocable'))}",
        f"Performed live provider call: {_yes_no(side_effects.get('performed_live_provider_call'))}",
        f"Performed credential lookup: {_yes_no(side_effects.get('performed_credential_lookup'))}",
        f"Performed network call: {_yes_no(side_effects.get('performed_network_call'))}",
        f"Performed remote push: {_yes_no(side_effects.get('performed_remote_push'))}",
        f"Performed vault mutation: {_yes_no(side_effects.get('performed_vault_mutation'))}",
        f"Performed evidence mutation: {_yes_no(side_effects.get('performed_evidence_mutation'))}",
        f"Performed cross-subsystem call: {_yes_no(side_effects.get('performed_cross_subsystem_call'))}",
        "Note: This readiness text grants no execution authority; a human reviewer must decide before any action.",
    ]
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hisys.judge.rloo",
        description=(
            "Judge subsystem-local RLOO entry point. Reads the Judge RLOO "
            "controller and emits a deterministic, side-effect-free readiness "
            "packet so Judge can be exercised independently of root-level Hisys "
            "orchestration."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Perform a Judge-only readiness check against "
            "src/hisys/judge/ralph.md without any live external action."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for the readiness packet (default: json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.check:
        parser.print_help()
        return 0

    packet = build_judge_subsystem_readiness_packet()
    if args.format == "text":
        sys.stdout.write(render_judge_subsystem_readiness_text(packet))
    else:
        sys.stdout.write(json.dumps(packet, indent=2, sort_keys=True))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
