"""DARS panel readiness/completion status surface.

DARS-CLOSE-3 in `docs/plans/dars-panel-completion-before-codebase-return.md`.

The readiness surface is advisory-only. It records which DARS panel modes
are fixture/local-complete, which are localhost-rehearsal-available but
human-gated, and which remain unproven (live external provider execution).
It performs no live action, credential lookup, browser/search/tool
execution, mutation, publication, or remote push.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "hisys.dars_panel.readiness_status"
SCHEMA_VERSION = "0.1.0"

# Stable closure pointer that DARS-CLOSE-4 will reuse to return the Ralph
# queue to the original codebase-analysis line.
_NEXT_QUEUE_AFTER_CLOSURE = "MB-CODEBASE-M21-6-PREP"
_COMPLETION_CLAIM = "local_fixture_localhost_controlled_advisory_complete"


def build_dars_panel_readiness_status() -> dict[str, Any]:
    """Return the locked advisory readiness status for the DARS panel line.

    The fields here are pinned by tests and traceability; changing them
    requires a controlled update to ``docs/plans/dars-panel-completion-
    before-codebase-return.md`` and the DARS panel traceability matrix.
    """

    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "fixture_panel_complete": True,
        "operator_report_available": True,
        "golden_fixture_available": True,
        "localhost_rehearsal_available": True,
        "localhost_rehearsal_human_gated": True,
        "remote_subscription_policy_exists": True,
        "remote_subscription_injected_executor_harness_available": True,
        "live_provider_execution_smoked": False,
        "completion_claim": _COMPLETION_CLAIM,
        "next_queue_after_closure": _NEXT_QUEUE_AFTER_CLOSURE,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "live_external_action_authorized": False,
    }


def write_dars_panel_readiness_report(
    *, instance_root: Path, yyyymmdd: str, status: dict[str, Any]
) -> str:
    """Persist a readiness snapshot under reports/run-summaries/<date>.

    Returns the instance-relative report ref string.
    """

    report_ref = f"reports/run-summaries/{yyyymmdd}/dars-panel-readiness-status.json"
    report_path = instance_root / report_ref
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report_ref


def format_text_status(status: dict[str, Any]) -> str:
    """Render the readiness status as a deterministic text block."""

    lines = []
    for key in sorted(status):
        value = status[key]
        if isinstance(value, bool):
            value_text = "true" if value else "false"
        else:
            value_text = str(value)
        lines.append(f"{key}: {value_text}")
    return "\n".join(lines)
