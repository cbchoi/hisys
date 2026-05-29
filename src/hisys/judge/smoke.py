"""Judge subsystem-local advisory smoke harness.

This module provides a deterministic, in-process, fixture-driven smoke run for
the Judge bounded advisory pipeline. It drives the whole Judge surface end to
end over built-in fixture decision packets:

    validate_judge_decision_packet
      -> render_judge_gate_result
      -> build_judge_gate_result_packet
      -> build_judge_advisory_panel_review_bundle
      -> serialize_judge_advisory_panel_review_bundle
      -> fingerprint_judge_advisory_panel_review_bundle

and records the outcome as a single deterministic, JSON-serializable smoke
report so a human reviewer can inspect that the pipeline composes correctly and
that the Judge authority locks are preserved at every stage.

The smoke command is::

    PYTHONPATH=src:. python3 -m hisys.judge.smoke

It emits the JSON smoke report to stdout and exits ``0`` when the smoke passed,
``1`` otherwise. ``--summary`` emits the compact readiness summary, ``--text``
emits a short human-readable status text, ``--status-bundle`` emits a JSON
bundle pairing that summary with its status text, ``--status-bundle-canonical``
emits that same bundle as a single canonical JSON text string (stable sorted
keys, compact separators), and ``--status-bundle-fingerprint`` emits a tiny JSON
identity packet carrying the bundle's content fingerprint; these output modes
are mutually exclusive and the default output remains the full JSON report.

The harness is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, no deployment, and
no cross-subsystem call. It exercises only the built-in in-process fixtures and
grants no execution authority -- every produced advisory result stays
advisory-only and always requires human review.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections.abc import Mapping
from typing import Any

from .gate_result import (
    JUDGE_ADVISORY_PANEL_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM,
    JUDGE_GATE_NON_AUTHORIZATION_NOTE,
    build_judge_advisory_panel_review_bundle,
    build_judge_gate_result_packet,
    fingerprint_judge_advisory_panel_review_bundle,
    render_judge_gate_result,
    serialize_judge_advisory_panel_review_bundle,
)

_ESCALATION_LOCK_KEYS: tuple[str, ...] = (
    "live_external_action_authorized",
    "mutation_authorized",
    "publication_authorized",
    "human_review_removal_authorized",
)

# Built-in, fully local fixture decision packets. They cover the whole bounded
# verdict range plus an intentionally-invalid packet so the smoke exercises both
# the rendered gate-result path and the rejected (validation-failure) path. None
# of these refs are secrets; they are opaque local handles.
JUDGE_SMOKE_FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "label": "advisory_pass_case",
        "expected_rendered": True,
        "expected_gate_status": "advisory_pass",
        "packet": {
            "packet_id": "judge-smoke-pass",
            "decision_subject_ref": "subject://judge-smoke/readiness-claim",
            "verdict": "pass",
            "rationale": "Prepared evidence supports the advisory claim.",
            "evidence_refs": ["evidence://judge-smoke/altas-packet-1"],
            "opposition_refs": ["opposition://judge-smoke/dars-packet-1"],
        },
    },
    {
        "label": "advisory_needs_human_review_case",
        "expected_rendered": True,
        "expected_gate_status": "advisory_needs_human_review",
        "packet": {
            "packet_id": "judge-smoke-needs-human-review",
            "decision_subject_ref": "subject://judge-smoke/ambiguous-claim",
            "verdict": "needs_human_review",
            "rationale": "Evidence is inconclusive; a human reviewer must decide.",
            "evidence_refs": ["evidence://judge-smoke/altas-packet-2"],
        },
    },
    {
        "label": "advisory_fail_case",
        "expected_rendered": True,
        "expected_gate_status": "advisory_fail",
        "packet": {
            "packet_id": "judge-smoke-fail",
            "decision_subject_ref": "subject://judge-smoke/unsupported-claim",
            "verdict": "fail",
            "rationale": "Prepared evidence does not support the advisory claim.",
            "evidence_refs": ["evidence://judge-smoke/altas-packet-3"],
            "opposition_refs": ["opposition://judge-smoke/dars-packet-3"],
        },
    },
    {
        "label": "advisory_block_case",
        "expected_rendered": True,
        "expected_gate_status": "advisory_block",
        "packet": {
            "packet_id": "judge-smoke-block",
            "decision_subject_ref": "subject://judge-smoke/blocking-concern",
            "verdict": "block",
            "rationale": "A blocking concern was found in the prepared evidence.",
            "evidence_refs": ["evidence://judge-smoke/altas-packet-4"],
        },
    },
    {
        "label": "rejected_case",
        "expected_rendered": False,
        "expected_gate_status": "rejected",
        # Intentionally invalid: no evidence_refs handle, so validation fails and
        # the renderer returns a rejected (non-rendered) gate result.
        "packet": {
            "packet_id": "judge-smoke-rejected",
            "decision_subject_ref": "subject://judge-smoke/incomplete-packet",
            "verdict": "pass",
            "rationale": "Packet is missing required prepared evidence handles.",
            "evidence_refs": [],
        },
    },
)


def _gate_result_packet_locks_preserved(packet: dict[str, Any]) -> dict[str, bool]:
    """Return the lock-preservation flags for one projected gate-result packet."""

    top = packet.get("authority_locks", {})
    advisory_only = top.get("advisory_only") is True
    requires_human_review = top.get("requires_human_review") is True

    decision_packet = packet.get("decision_packet")
    no_escalation = True
    if isinstance(decision_packet, dict):
        embedded = decision_packet.get("authority_locks", {})
        no_escalation = all(
            embedded.get(key) is False for key in _ESCALATION_LOCK_KEYS
        )

    return {
        "advisory_only_locked": advisory_only,
        "requires_human_review_locked": requires_human_review,
        "no_escalation_authority": no_escalation,
    }


def build_judge_smoke_report(
    fixtures: tuple[dict[str, Any], ...] | None = None,
) -> dict[str, Any]:
    """Drive the Judge advisory pipeline over fixtures and return a smoke report.

    ``fixtures`` defaults to :data:`JUDGE_SMOKE_FIXTURES`. Each fixture is run
    through the full in-process pipeline (validate -> render -> project -> panel
    bundle -> serialize -> fingerprint). The returned mapping is plain,
    deterministic, and JSON-serializable. It records per-fixture outcomes, a list
    of named invariant ``checks``, the advisory panel review ``panel_review_bundle``
    (machine view plus human-readable ``report_text``), the bundle content
    ``bundle_fingerprint``, and an overall ``smoke_passed`` flag.

    The function performs no I/O and no external action of any kind, does not
    mutate its inputs, and returns a fresh mapping on every call. It grants no
    execution authority: the top-level ``authority_locks`` pin
    ``advisory_only=true`` / ``requires_human_review=true`` with every escalation
    lock false, and ``non_authorization_note`` repeats that a human reviewer must
    decide before any action is taken.
    """

    used_fixtures = JUDGE_SMOKE_FIXTURES if fixtures is None else tuple(fixtures)

    fixture_reports: list[dict[str, Any]] = []
    gate_result_packets: list[dict[str, Any]] = []
    for fixture in used_fixtures:
        gate_result = render_judge_gate_result(fixture["packet"])
        packet = build_judge_gate_result_packet(gate_result)
        gate_result_packets.append(packet)

        locks = _gate_result_packet_locks_preserved(packet)
        outcome_matches = (
            gate_result.rendered == fixture["expected_rendered"]
            and gate_result.gate_status == fixture["expected_gate_status"]
        )
        fixture_reports.append(
            {
                "label": fixture["label"],
                "expected_rendered": fixture["expected_rendered"],
                "expected_gate_status": fixture["expected_gate_status"],
                "rendered": gate_result.rendered,
                "gate_status": gate_result.gate_status,
                "outcome_matches_expectation": outcome_matches,
                **locks,
            }
        )

    bundle = build_judge_advisory_panel_review_bundle(gate_result_packets)
    serialized = serialize_judge_advisory_panel_review_bundle(bundle)
    fingerprint = fingerprint_judge_advisory_panel_review_bundle(bundle)

    observed_statuses = {report["gate_status"] for report in fixture_reports}
    required_statuses = {
        "advisory_pass",
        "advisory_fail",
        "advisory_block",
        "advisory_needs_human_review",
        "rejected",
    }

    checks = [
        {
            "name": "all_fixture_outcomes_match_expectation",
            "passed": all(
                report["outcome_matches_expectation"] for report in fixture_reports
            ),
        },
        {
            "name": "all_gate_results_advisory_only_locked",
            "passed": all(
                report["advisory_only_locked"] for report in fixture_reports
            ),
        },
        {
            "name": "all_gate_results_require_human_review",
            "passed": all(
                report["requires_human_review_locked"] for report in fixture_reports
            ),
        },
        {
            "name": "no_escalation_authority_present",
            "passed": all(
                report["no_escalation_authority"] for report in fixture_reports
            ),
        },
        {
            "name": "panel_bundle_packet_count_matches_fixture_count",
            "passed": bundle["packet_count"] == len(used_fixtures),
        },
        {
            "name": "bundle_serialization_round_trips",
            "passed": json.loads(serialized) == bundle,
        },
        {
            "name": "bundle_fingerprint_is_stable_hex_digest",
            "passed": (
                len(fingerprint) == 64
                and fingerprint == fingerprint.lower()
                and all(ch in "0123456789abcdef" for ch in fingerprint)
                and fingerprint
                == fingerprint_judge_advisory_panel_review_bundle(bundle)
            ),
        },
        {
            "name": "verdict_range_and_rejected_path_exercised",
            "passed": required_statuses.issubset(observed_statuses),
        },
    ]

    smoke_passed = all(check["passed"] for check in checks)

    return {
        "subsystem": "judge",
        "kind": "advisory_smoke_report",
        "mode": "local_fixture_in_process",
        "fixture_count": len(used_fixtures),
        "fixtures": fixture_reports,
        "checks": checks,
        "panel_review_bundle": bundle,
        "bundle_fingerprint": fingerprint,
        "bundle_fingerprint_algorithm": (
            JUDGE_ADVISORY_PANEL_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM
        ),
        "bundle_serialized_byte_length": len(serialized.encode("utf-8")),
        "smoke_passed": smoke_passed,
        "authority_locks": {
            "advisory_only": True,
            "requires_human_review": True,
            "live_external_action_authorized": False,
            "mutation_authorized": False,
            "publication_authorized": False,
            "remote_push_authorized": False,
            "human_review_removal_authorized": False,
        },
        "non_authorization_note": JUDGE_GATE_NON_AUTHORIZATION_NOTE,
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


def summarize_judge_smoke_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Project a full Judge smoke report into a compact readiness summary.

    Consumes the mapping produced by :func:`build_judge_smoke_report` and returns
    a small, deterministic, JSON-serializable summary so a human reviewer or local
    agent can inspect Judge smoke readiness -- pass/fail, which checks failed,
    which fixtures mismatched expectation, the gate-status spread, and the bundle
    fingerprint identity -- without parsing the full report or its embedded panel
    review bundle. The summary deliberately omits the large ``panel_review_bundle``
    and the per-fixture/per-check detail lists, carrying only counts and the names
    of anything that failed.

    The summary grants no execution authority: the top-level ``authority_locks``
    pin ``advisory_only=true`` / ``requires_human_review=true`` with every
    escalation lock false, and ``non_authorization_note`` repeats that a human
    reviewer must decide before any action. The function performs no I/O, does not
    mutate ``report``, and returns a fresh mapping on every call.
    """

    fixtures = [item for item in report.get("fixtures", []) if isinstance(item, dict)]
    checks = [item for item in report.get("checks", []) if isinstance(item, dict)]

    failed_check_names = [
        str(check.get("name")) for check in checks if check.get("passed") is not True
    ]
    checks_passed = len(checks) - len(failed_check_names)

    fixture_mismatch_labels = [
        str(fixture.get("label"))
        for fixture in fixtures
        if fixture.get("outcome_matches_expectation") is not True
    ]
    fixtures_matched = len(fixtures) - len(fixture_mismatch_labels)

    raw_counts: dict[str, int] = {}
    for fixture in fixtures:
        status = str(fixture.get("gate_status"))
        raw_counts[status] = raw_counts.get(status, 0) + 1
    gate_status_counts = {status: raw_counts[status] for status in sorted(raw_counts)}

    advisory_locks_preserved = all(
        fixture.get("advisory_only_locked") is True
        and fixture.get("requires_human_review_locked") is True
        and fixture.get("no_escalation_authority") is True
        for fixture in fixtures
    )

    return {
        "subsystem": report.get("subsystem", "judge"),
        "kind": "advisory_smoke_status",
        "mode": report.get("mode"),
        "smoke_passed": report.get("smoke_passed") is True,
        "fixture_count": len(fixtures),
        "fixtures_matched_expectation": fixtures_matched,
        "fixture_mismatch_labels": fixture_mismatch_labels,
        "gate_status_counts": gate_status_counts,
        "checks_total": len(checks),
        "checks_passed": checks_passed,
        "checks_failed": len(failed_check_names),
        "failed_check_names": failed_check_names,
        "advisory_locks_preserved_for_all_fixtures": advisory_locks_preserved,
        "bundle_fingerprint": report.get("bundle_fingerprint"),
        "bundle_fingerprint_algorithm": report.get("bundle_fingerprint_algorithm"),
        "bundle_serialized_byte_length": report.get("bundle_serialized_byte_length"),
        "authority_locks": {
            "advisory_only": True,
            "requires_human_review": True,
            "live_external_action_authorized": False,
            "mutation_authorized": False,
            "publication_authorized": False,
            "remote_push_authorized": False,
            "human_review_removal_authorized": False,
        },
        "non_authorization_note": JUDGE_GATE_NON_AUTHORIZATION_NOTE,
    }


def render_judge_smoke_status_text(summary_or_report: Mapping[str, Any]) -> str:
    """Render a short human/agent-readable Judge smoke status text.

    ``summary_or_report`` is either the full smoke report produced by
    :func:`build_judge_smoke_report` or the compact summary produced by
    :func:`summarize_judge_smoke_report`. A full report is projected through
    :func:`summarize_judge_smoke_report` first (an already-compact summary is
    used as-is), so this renderer never duplicates the readiness logic. The
    returned value is a single deterministic, short, multi-line status string
    that surfaces pass/fail, the fixture/check counts, the gate-status spread,
    the bundle fingerprint identity, and -- only when present -- the names of any
    failed checks and any fixtures that mismatched expectation.

    The function performs no I/O and no external action of any kind, does not
    mutate its input, and returns a fresh string on every call. It grants no
    execution authority: the rendered text states that the result is advisory
    only and that human review is required, and it repeats the summary's
    ``non_authorization_note`` that a human reviewer must decide before any
    action is taken.
    """

    if summary_or_report.get("kind") == "advisory_smoke_status":
        summary: Mapping[str, Any] = summary_or_report
    else:
        summary = summarize_judge_smoke_report(summary_or_report)

    status = "PASS" if summary.get("smoke_passed") is True else "FAIL"

    counts = summary.get("gate_status_counts", {})
    counts_text = (
        ", ".join(f"{name}={counts[name]}" for name in sorted(counts))
        if counts
        else "(none)"
    )

    lines = [
        f"Judge Advisory Smoke Status: {status}",
        f"Mode: {summary.get('mode')}",
        "Fixtures matched expectation: "
        f"{summary.get('fixtures_matched_expectation')}/{summary.get('fixture_count')}",
    ]

    mismatches = [str(label) for label in summary.get("fixture_mismatch_labels", [])]
    if mismatches:
        lines.append(f"Fixture mismatches: {', '.join(mismatches)}")

    lines.append(
        f"Checks passed: {summary.get('checks_passed')}/{summary.get('checks_total')}"
    )

    failed_checks = [str(name) for name in summary.get("failed_check_names", [])]
    if failed_checks:
        lines.append(f"Failed checks: {', '.join(failed_checks)}")

    lines.append(f"Gate status counts: {counts_text}")
    lines.append(
        "Advisory locks preserved for all fixtures: "
        + ("yes" if summary.get("advisory_locks_preserved_for_all_fixtures") else "no")
    )
    lines.append(
        "Bundle fingerprint "
        f"({summary.get('bundle_fingerprint_algorithm')}): "
        f"{summary.get('bundle_fingerprint')}"
    )
    lines.append("Advisory only: yes")
    lines.append("Requires human review: yes")
    lines.append(f"Note: {summary.get('non_authorization_note')}")

    return "\n".join(lines)


def build_judge_smoke_status_review_bundle(
    summary_or_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Bundle the compact smoke status summary with its status text.

    ``summary_or_report`` is either the full smoke report produced by
    :func:`build_judge_smoke_report` or the compact summary produced by
    :func:`summarize_judge_smoke_report`. A full report is projected through
    :func:`summarize_judge_smoke_report` once (an already-compact summary is
    used as-is, deep-copied so the bundle is independent of the caller's
    mapping); both the bundled ``summary`` and the ``status_text`` are derived
    from that *same* projected summary via :func:`render_judge_smoke_status_text`,
    so this builder never duplicates the readiness logic and the machine view and
    human view stay consistent. This mirrors the gate-result
    :func:`build_judge_advisory_panel_review_bundle` lineage so local tooling gets
    both views of Judge smoke readiness in one JSON-serializable artifact.

    The returned mapping is plain, deterministic, and JSON-serializable, with a
    stable top-level key set (``subsystem``, ``kind``, ``smoke_passed``,
    ``summary``, ``status_text``, ``authority_locks``, ``non_authorization_note``).

    The function performs no I/O and no external action of any kind, does not
    mutate its input, and returns a fresh mapping (with an independent nested
    ``summary``) on every call. It grants no execution authority: the top-level
    ``authority_locks`` pin ``advisory_only=true`` / ``requires_human_review=true``
    (no escalation keys), and ``non_authorization_note`` repeats that a human
    reviewer must decide before any action is taken.
    """

    if summary_or_report.get("kind") == "advisory_smoke_status":
        summary: dict[str, Any] = copy.deepcopy(dict(summary_or_report))
    else:
        summary = summarize_judge_smoke_report(summary_or_report)

    return {
        "subsystem": "judge",
        "kind": "advisory_smoke_status_review_bundle",
        "smoke_passed": summary.get("smoke_passed") is True,
        "summary": summary,
        "status_text": render_judge_smoke_status_text(summary),
        "authority_locks": {
            "advisory_only": True,
            "requires_human_review": True,
        },
        "non_authorization_note": JUDGE_GATE_NON_AUTHORIZATION_NOTE,
    }


def serialize_judge_smoke_status_review_bundle(
    bundle: Mapping[str, Any],
) -> str:
    """Serialize a smoke status review bundle into canonical JSON text.

    ``bundle`` is the mapping produced by
    :func:`build_judge_smoke_status_review_bundle`. The returned value is a
    single deterministic, canonical JSON text string with stable sorted keys
    (compact separators, no insignificant whitespace) so local logging/diffing
    tooling sees the same bytes for the same advisory content regardless of the
    bundle's dict insertion order. The function returns the string only. This
    mirrors the gate-result
    :func:`hisys.judge.gate_result.serialize_judge_advisory_panel_review_bundle`
    lineage.

    The function performs no I/O and no external action of any kind, does not
    mutate ``bundle``, and returns a fresh string on every call. It grants no
    execution authority: it serializes the bundle as given, so the pinned
    ``advisory_only=true`` / ``requires_human_review=true`` locks and the
    ``non_authorization_note`` are preserved verbatim in the text.
    """

    return json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


# Standard-library hash algorithm used for the smoke status review bundle
# content fingerprint. SHA-256 (``hashlib.sha256``) is a fixed-output,
# deterministic digest from the Python standard library; its 256-bit output
# renders as 64 lowercase hexadecimal characters.
JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM = "sha256"


def fingerprint_judge_smoke_status_review_bundle(
    bundle: Mapping[str, Any],
) -> str:
    """Compute a deterministic content fingerprint of a smoke status bundle.

    ``bundle`` is the mapping produced by
    :func:`build_judge_smoke_status_review_bundle`. The returned value is a
    single lowercase hex digest string -- the
    :data:`JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM` (SHA-256)
    digest of the canonical JSON serialization produced by
    :func:`serialize_judge_smoke_status_review_bundle` (the canonical byte/text
    source), encoded as UTF-8. Because the canonical serialization has stable
    sorted keys, two bundles with insertion-order-equivalent content fingerprint
    to the same digest, while any content change changes the digest. The function
    returns the digest string only. This mirrors the gate-result
    :func:`hisys.judge.gate_result.fingerprint_judge_advisory_panel_review_bundle`
    lineage.

    The function performs no I/O and no external action of any kind, does not
    mutate ``bundle``, and returns a fresh string on every call. It grants no
    execution authority: the digest is derived purely from the canonical content,
    so the pinned ``advisory_only=true`` / ``requires_human_review=true`` locks
    and the ``non_authorization_note`` are part of what is fingerprinted, not
    mutated or escalated.
    """

    canonical = serialize_judge_smoke_status_review_bundle(bundle)
    digest = hashlib.new(JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM)
    digest.update(canonical.encode("utf-8"))
    return digest.hexdigest()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hisys.judge.smoke",
        description=(
            "Judge subsystem-local advisory smoke harness. Drives the bounded "
            "advisory pipeline over built-in in-process fixtures and emits a "
            "deterministic, side-effect-free JSON smoke report. Exits 0 when the "
            "smoke passed."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Output format for the smoke report (default: json).",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--summary",
        action="store_true",
        help=(
            "Emit the compact readiness summary instead of the full smoke "
            "report, so agents can inspect smoke readiness without parsing the "
            "full report. The exit code still reflects whether the smoke passed."
        ),
    )
    output_group.add_argument(
        "--text",
        action="store_true",
        help=(
            "Emit a short human/agent-readable status text instead of JSON, so "
            "an operator sees Judge smoke readiness at a glance. The exit code "
            "still reflects whether the smoke passed."
        ),
    )
    output_group.add_argument(
        "--status-bundle",
        action="store_true",
        help=(
            "Emit a JSON smoke status review bundle pairing the compact "
            "readiness summary with its human-readable status text, so local "
            "tooling gets both the machine and human views in one artifact. The "
            "exit code still reflects whether the smoke passed."
        ),
    )
    output_group.add_argument(
        "--status-bundle-canonical",
        action="store_true",
        help=(
            "Emit the smoke status review bundle as a single canonical JSON "
            "text string (stable sorted keys, compact separators, no "
            "insignificant whitespace), so local logging/diffing tooling sees "
            "the same bytes for the same advisory content. The exit code still "
            "reflects whether the smoke passed."
        ),
    )
    output_group.add_argument(
        "--status-bundle-fingerprint",
        action="store_true",
        help=(
            "Emit a tiny JSON identity packet carrying the smoke status review "
            "bundle's content fingerprint (the SHA-256 digest of its canonical "
            "JSON serialization), so local diffing/deduplication tooling can "
            "identify the readiness content by digest. The exit code still "
            "reflects whether the smoke passed."
        ),
    )
    return parser


def _build_fingerprint_identity_packet(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Build the tiny JSON identity packet emitted by ``--status-bundle-fingerprint``.

    The packet carries the bundle's content fingerprint plus the pinned
    advisory-only/requires-human-review locks and the non-authorization note, so
    even the fingerprint surface preserves the Judge authority boundary. It
    grants no execution authority and performs no I/O.
    """

    return {
        "subsystem": "judge",
        "kind": "advisory_smoke_status_review_bundle_fingerprint",
        "smoke_passed": bundle.get("smoke_passed") is True,
        "fingerprint": fingerprint_judge_smoke_status_review_bundle(bundle),
        "fingerprint_algorithm": JUDGE_SMOKE_STATUS_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM,
        "authority_locks": {
            "advisory_only": True,
            "requires_human_review": True,
        },
        "non_authorization_note": JUDGE_GATE_NON_AUTHORIZATION_NOTE,
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    report = build_judge_smoke_report()
    if args.text:
        sys.stdout.write(render_judge_smoke_status_text(report))
    elif args.status_bundle:
        bundle = build_judge_smoke_status_review_bundle(report)
        sys.stdout.write(json.dumps(bundle, indent=2, sort_keys=True))
    elif args.status_bundle_canonical:
        bundle = build_judge_smoke_status_review_bundle(report)
        sys.stdout.write(serialize_judge_smoke_status_review_bundle(bundle))
    elif args.status_bundle_fingerprint:
        bundle = build_judge_smoke_status_review_bundle(report)
        identity = _build_fingerprint_identity_packet(bundle)
        sys.stdout.write(json.dumps(identity, indent=2, sort_keys=True))
    else:
        payload = summarize_judge_smoke_report(report) if args.summary else report
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
    sys.stdout.write("\n")
    return 0 if report["smoke_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
