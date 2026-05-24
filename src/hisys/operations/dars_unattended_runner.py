"""DARS bounded unattended advisory runner.

R5 introduces a local-safe unattended runner contract for dry-run rehearsal. The
runner validates a finite standing approval policy, checks circuit breakers,
routes only through the R2 fail-closed adapter with fake/injected transport, and
writes an audit ledger entry for every completed/blocked/failed run.

The runner performs no credential lookup and makes no live provider/model call.
It supports the R5 PREP dry-run path and a distinct R5 canary-mode contract;
the canary path still routes through the fake/injected dry-run adapter until a
separate human-gated live canary execution is approved.

Traceability:

- HISYS-FR-DARS-CP-013, HISYS-T-DARS-CP-015
- DARS-LIVE-RELEASE-R5-UNATTENDED-PREP
- docs/runbooks/dars-unattended-advisory-operation.md
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from hisys.agents.dars_live_provider_adapter import (
    DarsLiveProviderAdapterRequest,
    DarsLiveProviderAdapterResult,
    run_dars_live_provider_adapter,
)
from hisys.agents.dars_live_provider_transport import FakeLiveProviderTransport
from hisys.agents.dars_unattended_policy import (
    STANDING_APPROVAL_CANARY_REQUEST_CLASS,
    STANDING_APPROVAL_DRY_RUN_REQUEST_CLASS,
    validate_standing_approval_policy,
)
from hisys.config.instance import InstanceRoot


DARS_UNATTENDED_ADVISORY_LEDGER_SCHEMA_ID = (
    "hisys.dars.unattended_advisory.ledger_entry"
)
DARS_UNATTENDED_ADVISORY_LEDGER_SCHEMA_VERSION = "0.1.0"

_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_DATE_RE = re.compile(r"^\d{8}$")
_ALLOWED_MODES: tuple[str, ...] = ("dry_run", "canary")
_REQUEST_CLASS_BY_MODE: dict[str, str] = {
    "dry_run": STANDING_APPROVAL_DRY_RUN_REQUEST_CLASS,
    "canary": STANDING_APPROVAL_CANARY_REQUEST_CLASS,
}
_VALIDATION_MODE_BY_RUNNER_MODE: dict[str, str] = {
    "dry_run": "prep",
    "canary": "canary",
}


@dataclass(frozen=True)
class DarsUnattendedAdvisoryRequest:
    request_id: str
    source_execution_id: str
    request_class: str
    standing_approval_policy_ref: str
    policy_packet_ref: str
    activation_packet_ref: str
    approval_ref: str
    backend_id: str
    prompt_packet_ref: str
    prompt_byte_count: int
    yyyymmdd: str
    mode: Literal["dry_run", "canary"] = "dry_run"
    canary_action_decision_packet_ref: str | None = None
    now: str | None = None
    mutation_allowed: bool = False
    publication_allowed: bool = False
    external_action_allowed: bool = False
    consecutive_failures: int = 0
    cost_threshold_reached: bool = False
    secret_scan_passed: bool = True
    output_redaction_passed: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "source_execution_id",
            "request_class",
            "standing_approval_policy_ref",
            "policy_packet_ref",
            "activation_packet_ref",
            "approval_ref",
            "backend_id",
            "prompt_packet_ref",
            "yyyymmdd",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"missing_{field_name}")
        if not _SLUG_RE.fullmatch(self.request_id):
            raise ValueError("invalid_request_id")
        if not _SLUG_RE.fullmatch(self.source_execution_id):
            raise ValueError("invalid_source_execution_id")
        if not _SLUG_RE.fullmatch(self.backend_id):
            raise ValueError("invalid_backend_id")
        if not _DATE_RE.fullmatch(self.yyyymmdd):
            raise ValueError("invalid_yyyymmdd")
        if self.mode not in _ALLOWED_MODES:
            raise ValueError("invalid_unattended_runner_mode")
        if self.mode == "canary":
            if (
                not isinstance(self.canary_action_decision_packet_ref, str)
                or not self.canary_action_decision_packet_ref
            ):
                raise ValueError("missing_canary_action_decision_packet_ref")
        if (
            isinstance(self.prompt_byte_count, bool)
            or not isinstance(self.prompt_byte_count, int)
            or self.prompt_byte_count < 0
        ):
            raise ValueError("invalid_prompt_byte_count")
        for field_name in ("consecutive_failures",):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"invalid_{field_name}")


@dataclass(frozen=True)
class DarsUnattendedAdvisoryResult:
    status: Literal["completed", "blocked", "failed", "circuit_broken"]
    request_id: str
    request_class: str
    policy_id: str
    failure_code: str | None
    failure_detail: str
    ledger_ref: str | None
    adapter_boundary_ref: str | None
    external_call_made: bool
    model_boundary_crossed: bool
    mutation_performed: bool
    publication_performed: bool
    external_action_performed: bool
    advisory_only: bool
    requires_human_review: bool
    requires_post_run_human_review: bool
    policy_issue_codes: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class DarsUnattendedAdvisoryRunner:
    instance: InstanceRoot
    transport: FakeLiveProviderTransport
    kill_switch_state: Mapping[str, str]

    def run(self, request: DarsUnattendedAdvisoryRequest) -> DarsUnattendedAdvisoryResult:
        try:
            policy = _load_policy(request.standing_approval_policy_ref)
        except _PolicyLoadError as exc:
            return self._finish(
                request,
                policy={},
                status="blocked",
                failure_code="standing_approval_policy_unreadable",
                failure_detail=str(exc),
            )

        validation_mode = _VALIDATION_MODE_BY_RUNNER_MODE[request.mode]
        policy_report = validate_standing_approval_policy(
            policy,
            config_ref=request.standing_approval_policy_ref,
            now=request.now,
            mode=validation_mode,  # type: ignore[arg-type]
        )
        policy_issue_codes = {
            issue.code for issue in policy_report.issues if issue.severity == "error"
        }
        if not policy_report.valid:
            if request.mode == "canary":
                failure_code = "canary_mode_policy_invalid"
            elif "standing_approval_not_active" in policy_issue_codes:
                failure_code = "standing_approval_not_active"
            else:
                failure_code = "standing_approval_policy_invalid"
            return self._finish(
                request,
                policy=policy,
                status="blocked",
                failure_code=failure_code,
                failure_detail="; ".join(sorted(policy_issue_codes)),
                policy_issue_codes=policy_issue_codes,
            )

        preflight_failure = self._preflight_failure(request, policy)
        if preflight_failure is not None:
            status, failure_code, failure_detail = preflight_failure
            return self._finish(
                request,
                policy=policy,
                status=status,
                failure_code=failure_code,
                failure_detail=failure_detail,
            )

        adapter_request = DarsLiveProviderAdapterRequest(
            request_id=request.request_id,
            source_execution_id=request.source_execution_id,
            backend_id=request.backend_id,
            policy_packet_ref=request.policy_packet_ref,
            activation_packet_ref=request.activation_packet_ref,
            approval_ref=request.approval_ref,
            prompt_packet_ref=request.prompt_packet_ref,
            prompt_byte_count=request.prompt_byte_count,
            yyyymmdd=request.yyyymmdd,
            mode="dry_run",
            now=request.now,
        )
        adapter_result = run_dars_live_provider_adapter(
            adapter_request,
            transport=self.transport,
            instance=self.instance,
            env={},
        )
        if adapter_result.status == "completed":
            return self._finish(
                request,
                policy=policy,
                status="completed",
                failure_code=None,
                failure_detail="",
                adapter_result=adapter_result,
            )
        return self._finish(
            request,
            policy=policy,
            status="failed",
            failure_code=adapter_result.failure_code or "unattended_adapter_failed",
            failure_detail=adapter_result.failure_detail,
            adapter_result=adapter_result,
        )

    def _preflight_failure(
        self, request: DarsUnattendedAdvisoryRequest, policy: dict[str, Any]
    ) -> tuple[Literal["blocked", "circuit_broken"], str, str] | None:
        expected_class = _REQUEST_CLASS_BY_MODE[request.mode]
        if request.mode == "canary" and request.request_class != expected_class:
            return (
                "blocked",
                "canary_mode_requires_canary_request_class",
                request.request_class,
            )
        if request.request_class != expected_class:
            return ("blocked", "request_class_not_allowlisted", request.request_class)
        if request.request_class not in policy.get("request_class_allowlist", []):
            return ("blocked", "request_class_not_allowlisted", request.request_class)
        if request.mode == "canary":
            policy_decision_ref = policy.get("canary_action_decision_packet_ref")
            if (
                not isinstance(policy_decision_ref, str)
                or policy_decision_ref != request.canary_action_decision_packet_ref
            ):
                return (
                    "blocked",
                    "canary_action_decision_packet_ref_mismatch",
                    str(request.canary_action_decision_packet_ref),
                )
        kill_switch_ref = str(policy.get("kill_switch_ref", ""))
        if self.kill_switch_state.get(kill_switch_ref) != "armed":
            return ("blocked", "kill_switch_triggered", kill_switch_ref)
        if any(
            (
                request.mutation_allowed,
                request.publication_allowed,
                request.external_action_allowed,
            )
        ):
            return ("blocked", "unattended_authority_rejected", request.request_id)
        if not _ref_list_contains(policy.get("provider_policy_refs"), request.policy_packet_ref):
            return ("blocked", "provider_policy_mismatch", request.policy_packet_ref)
        if not _ref_list_contains(
            policy.get("activation_packet_refs"), request.activation_packet_ref
        ):
            return ("blocked", "provider_policy_mismatch", request.activation_packet_ref)
        breakers = policy.get("circuit_breakers", {})
        max_failures = breakers.get("max_consecutive_failures") if isinstance(breakers, dict) else None
        if isinstance(max_failures, int) and request.consecutive_failures >= max_failures:
            return (
                "circuit_broken",
                "repeated_failure_threshold_reached",
                str(request.consecutive_failures),
            )
        if request.cost_threshold_reached:
            return ("circuit_broken", "cost_threshold_reached", request.request_id)
        if not request.secret_scan_passed:
            return ("circuit_broken", "secret_scan_hit", request.request_id)
        if not request.output_redaction_passed:
            return ("circuit_broken", "output_redaction_failure", request.request_id)
        return None

    def _finish(
        self,
        request: DarsUnattendedAdvisoryRequest,
        *,
        policy: dict[str, Any],
        status: Literal["completed", "blocked", "failed", "circuit_broken"],
        failure_code: str | None,
        failure_detail: str,
        adapter_result: DarsLiveProviderAdapterResult | None = None,
        policy_issue_codes: set[str] | None = None,
    ) -> DarsUnattendedAdvisoryResult:
        ledger_ref = _write_ledger_entry(
            self.instance,
            request=request,
            policy=policy,
            status=status,
            failure_code=failure_code,
            failure_detail=failure_detail,
            adapter_result=adapter_result,
            policy_issue_codes=policy_issue_codes or set(),
        )
        return DarsUnattendedAdvisoryResult(
            status=status,
            request_id=request.request_id,
            request_class=request.request_class,
            policy_id=str(policy.get("policy_id", "")),
            failure_code=failure_code,
            failure_detail=failure_detail,
            ledger_ref=ledger_ref,
            adapter_boundary_ref=adapter_result.boundary_ref if adapter_result else None,
            external_call_made=adapter_result.external_call_made if adapter_result else False,
            model_boundary_crossed=adapter_result.model_boundary_crossed if adapter_result else False,
            mutation_performed=False,
            publication_performed=False,
            external_action_performed=False,
            advisory_only=True,
            requires_human_review=True,
            requires_post_run_human_review=True,
            policy_issue_codes=policy_issue_codes or set(),
        )


class _PolicyLoadError(Exception):
    """Raised when a standing approval policy cannot be loaded."""


def _load_policy(path_ref: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path_ref).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _PolicyLoadError(str(exc)) from None
    if not isinstance(data, dict):
        raise _PolicyLoadError("standing approval policy must be a JSON object")
    return data


def _write_ledger_entry(
    instance: InstanceRoot,
    *,
    request: DarsUnattendedAdvisoryRequest,
    policy: dict[str, Any],
    status: str,
    failure_code: str | None,
    failure_detail: str,
    adapter_result: DarsLiveProviderAdapterResult | None,
    policy_issue_codes: set[str],
) -> str:
    policy_id = str(policy.get("policy_id", "unknown-policy")) or "unknown-policy"
    output_dir = (
        instance.runtime_boundary_dir
        / "dars-unattended-advisory"
        / request.yyyymmdd
        / policy_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_id": DARS_UNATTENDED_ADVISORY_LEDGER_SCHEMA_ID,
        "schema_version": DARS_UNATTENDED_ADVISORY_LEDGER_SCHEMA_VERSION,
        "policy_id": policy_id,
        "approval_ref": policy.get("approval_ref", ""),
        "operator_id": policy.get("operator_id", ""),
        "post_run_reviewer_ref": policy.get("post_run_reviewer_ref", ""),
        "request_id": request.request_id,
        "source_execution_id": request.source_execution_id,
        "request_class": request.request_class,
        "mode": request.mode,
        "standing_approval_policy_ref": request.standing_approval_policy_ref,
        "provider_policy_ref": request.policy_packet_ref,
        "activation_packet_ref": request.activation_packet_ref,
        "provider_approval_ref": request.approval_ref,
        "backend_id": request.backend_id,
        "prompt_packet_ref": request.prompt_packet_ref,
        "prompt_byte_count": request.prompt_byte_count,
        "max_prompt_bytes_per_run": policy.get("max_prompt_bytes_per_run", 0),
        "max_output_bytes_per_run": policy.get("max_output_bytes_per_run", 0),
        "rate_limit_per_minute": policy.get("rate_limit_per_minute", 0),
        "cost_budget_ref": policy.get("cost_budget_ref", ""),
        "kill_switch_ref": policy.get("kill_switch_ref", ""),
        "kill_switch_state": "armed",
        "status": status,
        "failure_code": failure_code,
        "failure_detail": failure_detail,
        "transport_kind": (
            adapter_result.transport_kind
            if adapter_result
            else "fake_injected_provider_transport"
        ),
        "adapter_mode": adapter_result.mode if adapter_result else "dry_run",
        "adapter_boundary_ref": adapter_result.boundary_ref if adapter_result else None,
        "external_call_made": adapter_result.external_call_made if adapter_result else False,
        "model_boundary_crossed": adapter_result.model_boundary_crossed if adapter_result else False,
        "live_provider_model_call_made": False,
        "raw_provider_api_call_by_hisys": False,
        "credential_lookup_by_hisys": False,
        "mutation_performed": False,
        "publication_performed": False,
        "external_action_performed": False,
        "advisory_only": True,
        "requires_human_review": True,
        "requires_post_run_human_review": True,
        "canary_action_decision_packet_ref": (
            request.canary_action_decision_packet_ref
            if request.mode == "canary"
            else None
        ),
        "canary_post_run_reviewer_ref": (
            policy.get("canary_post_run_reviewer_ref", "")
            if request.mode == "canary"
            else ""
        ),
        "requires_post_canary_human_review": (
            policy.get("requires_post_canary_human_review", False)
            if request.mode == "canary"
            else False
        ),
        "secret_scan_passed": request.secret_scan_passed,
        "output_redaction_passed": request.output_redaction_passed,
        "policy_refs": [
            "HISYS-FR-DARS-CP-013",
            "HISYS-T-DARS-CP-015",
            "DARS-LIVE-RELEASE-R5-UNATTENDED-PREP",
            "DARS-LIVE-RELEASE-R5-CANARY-MODE-PREP",
        ],
    }
    if policy_issue_codes:
        payload["policy_issue_codes"] = sorted(policy_issue_codes)
    json_path = output_dir / f"{request.request_id}.json"
    md_path = output_dir / f"{request.request_id}.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    return str(json_path.relative_to(instance.root))


def _render_markdown(payload: dict[str, Any]) -> str:
    failure_code = payload.get("failure_code") or "-"
    return "\n".join(
        [
            f"# DARS unattended advisory ledger — {payload['request_id']}",
            "",
            f"- schema_id: {payload['schema_id']}",
            f"- policy_id: {payload['policy_id']}",
            f"- request_class: {payload['request_class']}",
            f"- mode: {payload['mode']}",
            f"- status: {payload['status']}",
            f"- failure_code: {failure_code}",
            f"- external_call_made: {str(payload['external_call_made']).lower()}",
            f"- model_boundary_crossed: {str(payload['model_boundary_crossed']).lower()}",
            f"- mutation_performed: {str(payload['mutation_performed']).lower()}",
            f"- publication_performed: {str(payload['publication_performed']).lower()}",
            f"- external_action_performed: {str(payload['external_action_performed']).lower()}",
            f"- advisory_only: {str(payload['advisory_only']).lower()}",
            f"- requires_human_review: {str(payload['requires_human_review']).lower()}",
            f"- requires_post_run_human_review: {str(payload['requires_post_run_human_review']).lower()}",
            "",
        ]
    )


def _ref_list_contains(refs: Any, target_ref: str) -> bool:
    if not isinstance(refs, list):
        return False
    target_candidates = _ref_candidates(target_ref)
    for ref in refs:
        if isinstance(ref, str) and _ref_candidates(ref) & target_candidates:
            return True
    return False


def _ref_candidates(ref: str) -> set[str]:
    candidates = {ref}
    try:
        candidates.add(str(Path(ref).resolve()))
    except OSError:
        pass
    return candidates


__all__ = [
    "DARS_UNATTENDED_ADVISORY_LEDGER_SCHEMA_ID",
    "DARS_UNATTENDED_ADVISORY_LEDGER_SCHEMA_VERSION",
    "DarsUnattendedAdvisoryRequest",
    "DarsUnattendedAdvisoryResult",
    "DarsUnattendedAdvisoryRunner",
]
