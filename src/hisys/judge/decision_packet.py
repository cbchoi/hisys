"""Judge bounded advisory decision packet schema.

Judge issues bounded advisory judgments and decision packets from already
prepared evidence, Altas retrieval packets, and DARS opposition packets
(see ``docs/design/hisys-subsystem-architecture.md``). This module defines the
Judge-only decision packet schema and a pure, deterministic validator that
consumes an already-prepared local packet mapping.

The validator is side-effect free: it performs no live provider/model call,
no raw provider API call, no network request, no credential lookup, no vault
or evidence mutation, no remote push, no publication, and no cross-subsystem
call. It only inspects a mapping passed in by the caller.

The schema pins the Judge authority locks recorded in
``src/hisys/judge/ralph.md``: every validated packet is advisory-only and
always requires human review, and the validator refuses any packet that tries
to escalate to live external action, mutation, publication, or human-review
removal. A structurally valid packet emits an explicit warning that schema
validity does not by itself authorize any action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

JUDGE_VERDICTS: tuple[str, ...] = ("pass", "fail", "block", "needs_human_review")

SCHEMA_VALIDITY_WARNING = (
    "judge_decision_packet_schema_validity_does_not_authorize_action"
)

_REQUIRED_STRING_FIELDS: tuple[str, ...] = (
    "packet_id",
    "decision_subject_ref",
    "verdict",
    "rationale",
)

# (payload key, required safe value, failure code on violation)
_AUTHORITY_LOCKS: tuple[tuple[str, bool, str], ...] = (
    ("advisory_only", True, "judge_decision_packet_advisory_only_must_be_true"),
    (
        "requires_human_review",
        True,
        "judge_decision_packet_requires_human_review_must_be_true",
    ),
    (
        "live_external_action_authorized",
        False,
        "judge_decision_packet_live_external_action_not_authorized",
    ),
    ("mutation_authorized", False, "judge_decision_packet_mutation_not_authorized"),
    (
        "publication_authorized",
        False,
        "judge_decision_packet_publication_not_authorized",
    ),
    (
        "human_review_removal_authorized",
        False,
        "judge_decision_packet_human_review_removal_not_authorized",
    ),
)


@dataclass(frozen=True)
class JudgeAdvisoryDecisionPacket:
    """A validated Judge bounded advisory decision packet.

    The packet records the subject under judgment, the bounded advisory verdict,
    the rationale, and the already-prepared evidence/opposition handles it was
    synthesized from. Authority locks are pinned to advisory-only, human-review-
    required values and can never represent an escalated authority.
    """

    packet_id: str
    decision_subject_ref: str
    verdict: str
    rationale: str
    evidence_refs: tuple[str, ...]
    opposition_refs: tuple[str, ...] = ()
    advisory_only: bool = True
    requires_human_review: bool = True
    live_external_action_authorized: bool = False
    mutation_authorized: bool = False
    publication_authorized: bool = False
    human_review_removal_authorized: bool = False


@dataclass(frozen=True)
class JudgeDecisionPacketValidation:
    """Deterministic result of validating an advisory decision packet mapping."""

    valid: bool
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    packet: JudgeAdvisoryDecisionPacket | None = None


def _validate_string_fields(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for name in _REQUIRED_STRING_FIELDS:
        if name not in payload:
            failures.append(f"judge_decision_packet_missing_field:{name}")
            continue
        value = payload[name]
        if not isinstance(value, str):
            failures.append(f"judge_decision_packet_field_not_a_string:{name}")
            continue
        if value.strip() == "":
            failures.append(f"judge_decision_packet_empty_field:{name}")
    return failures


def _validate_verdict(payload: Mapping[str, Any]) -> list[str]:
    verdict = payload.get("verdict")
    if isinstance(verdict, str) and verdict not in JUDGE_VERDICTS:
        return ["judge_decision_packet_invalid_verdict"]
    return []


def _validate_refs(
    payload: Mapping[str, Any],
    *,
    key: str,
    require_non_empty: bool,
    not_a_list_code: str,
    empty_code: str,
    ref_not_a_string_code: str,
) -> tuple[list[str], tuple[str, ...]]:
    failures: list[str] = []
    raw = payload.get(key, [])
    if not isinstance(raw, list):
        return [not_a_list_code], ()
    if require_non_empty and not raw:
        failures.append(empty_code)
    if any(not isinstance(item, str) for item in raw):
        failures.append(ref_not_a_string_code)
    refs = tuple(item for item in raw if isinstance(item, str))
    return failures, refs


def _validate_authority_locks(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for key, safe_value, code in _AUTHORITY_LOCKS:
        if key in payload and payload[key] != safe_value:
            failures.append(code)
    return failures


def validate_judge_decision_packet(
    payload: Any,
) -> JudgeDecisionPacketValidation:
    """Validate an already-prepared Judge advisory decision packet mapping.

    Returns a :class:`JudgeDecisionPacketValidation`. On success ``packet`` is a
    frozen :class:`JudgeAdvisoryDecisionPacket` with authority locks pinned to
    advisory-only, human-review-required values, and ``warnings`` includes
    :data:`SCHEMA_VALIDITY_WARNING`. The function never mutates ``payload`` and
    performs no external action of any kind.
    """

    if not isinstance(payload, Mapping):
        return JudgeDecisionPacketValidation(
            valid=False,
            failures=("judge_decision_packet_not_a_mapping",),
        )

    failures: list[str] = []
    failures.extend(_validate_string_fields(payload))
    failures.extend(_validate_verdict(payload))

    evidence_failures, evidence_refs = _validate_refs(
        payload,
        key="evidence_refs",
        require_non_empty=True,
        not_a_list_code="judge_decision_packet_evidence_refs_not_a_list",
        empty_code="judge_decision_packet_evidence_refs_empty",
        ref_not_a_string_code="judge_decision_packet_evidence_ref_not_a_string",
    )
    failures.extend(evidence_failures)

    opposition_failures, opposition_refs = _validate_refs(
        payload,
        key="opposition_refs",
        require_non_empty=False,
        not_a_list_code="judge_decision_packet_opposition_refs_not_a_list",
        empty_code="",
        ref_not_a_string_code="judge_decision_packet_opposition_ref_not_a_string",
    )
    failures.extend(opposition_failures)

    failures.extend(_validate_authority_locks(payload))

    if failures:
        return JudgeDecisionPacketValidation(
            valid=False,
            failures=tuple(failures),
        )

    packet = JudgeAdvisoryDecisionPacket(
        packet_id=payload["packet_id"],
        decision_subject_ref=payload["decision_subject_ref"],
        verdict=payload["verdict"],
        rationale=payload["rationale"],
        evidence_refs=evidence_refs,
        opposition_refs=opposition_refs,
    )
    return JudgeDecisionPacketValidation(
        valid=True,
        warnings=(SCHEMA_VALIDITY_WARNING,),
        packet=packet,
    )


__all__ = [
    "JUDGE_VERDICTS",
    "SCHEMA_VALIDITY_WARNING",
    "JudgeAdvisoryDecisionPacket",
    "JudgeDecisionPacketValidation",
    "validate_judge_decision_packet",
]
