"""Runtime-local DARS advisory handoff loopback foundation.

DARS is intentionally not implemented here. This module records the handoff
contract and returns a local loopback placeholder so a future DARS adapter can be
attached without changing downstream artifact shapes.

The optional ``openai_compatible`` adapter implements the Local DARS / ByeSys
Provenance plan Milestones 2 and 3: it accepts requests only against loopback
endpoints, requires an explicit ``approval_ref`` even for localhost dispatch,
and treats a local LLM call as a model-boundary event rather than a live
external call.

Traceability: HISYS-FR-AGT-001..005, HISYS-DARS-CONTRACT-001,
HISYS-D-015, HISYS-T-023, HISYS-T-024.
"""

from __future__ import annotations

import json
import socket
import subprocess
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..config.instance import InstanceRoot
from ..schemas import AgentHandoffPackage
from .dars_config import (
    DarsBackendConfig,
    _classify_local_endpoint,
    derive_local_backend_metadata,
    load_dars_config,
)
from .dars_dispatch import DarsDispatchGate


class DarsCritiqueRecord(BaseModel):
    critique_id: str
    handoff_ref: str
    source_execution_ref: str
    target_agent_system: str = "DARS"
    critique_text: str
    dars_backend: str = "loopback_placeholder"
    external_call_made: bool = False
    model_boundary_crossed: bool = False
    local_model_call_made: bool = False
    endpoint_scope: str | None = None
    allowed_actions: Literal["advisory_only"] = "advisory_only"
    action_taken: Literal["none"] = "none"
    status: Literal["received"] = "received"
    producer_id: str
    policy_refs: list[str] = Field(default_factory=lambda: ["HISYS-FR-AGT-001", "HISYS-FR-AGT-002", "HISYS-FR-AGT-003", "HISYS-T-023", "HISYS-T-024"])


@dataclass(frozen=True)
class DarsCritiqueReport:
    report_ref: str
    handoff_refs: list[str] = field(default_factory=list)
    critique_refs: list[str] = field(default_factory=list)
    linked_execution_refs: list[str] = field(default_factory=list)
    skipped_execution_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=lambda: ["HISYS-FR-AGT-001", "HISYS-FR-AGT-002", "HISYS-FR-AGT-003", "HISYS-T-023", "HISYS-T-024"])


class DarsRuntime:
    """Record advisory DARS handoff contracts; use loopback until DARS exists."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def run_loopback_placeholder(
        self,
        *,
        yyyymmdd: str,
        source_execution_id: str,
        producer_id: str,
    ) -> DarsCritiqueReport:
        return self.run_fixture_critique(
            yyyymmdd=yyyymmdd,
            source_execution_id=source_execution_id,
            critique_text=(
                "DARS is not implemented yet; loopback placeholder returned so "
                "the handoff contract can be validated and replaced by a future "
                "DARS adapter without changing downstream artifacts."
            ),
            producer_id=producer_id,
        )

    def run_fixture_critique(
        self,
        *,
        yyyymmdd: str,
        source_execution_id: str,
        critique_text: str,
        producer_id: str,
        dars_backend: str = "loopback_placeholder",
        external_call_made: bool = False,
        model_boundary_crossed: bool = False,
        local_model_call_made: bool = False,
        endpoint_scope: str | None = None,
        extra_constraints: list[str] | None = None,
    ) -> DarsCritiqueReport:
        execution = _load_connector_execution(self.instance, yyyymmdd, source_execution_id)
        report = DarsCritiqueReport(report_ref=str(_report_json_path(self.instance, yyyymmdd).relative_to(self.instance.root)))
        if not execution:
            report.skipped_execution_refs.append(source_execution_id)
            _write_report(self.instance, yyyymmdd, report)
            return report

        suffix = _suffix(source_execution_id)
        handoff_id = f"HANDOFF-DARS-{suffix}"
        critique_id = f"CRITIQUE-DARS-{suffix}"
        constraints = [
            "advisory_only",
            "no live external action",
            f"dars_backend={dars_backend}",
            f"external_call_made={str(external_call_made).lower()}",
            "do not mutate alert decisions or connector executions",
        ]
        if extra_constraints:
            constraints.extend(extra_constraints)
        handoff = AgentHandoffPackage(
            handoff_id=handoff_id,
            target_agent_system="DARS",
            task="critique_alert_connector_execution",
            context=(
                "Runtime-local disabled connector execution requires advisory critique; "
                f"execution={source_execution_id}; alert_decision={execution.get('alert_decision_ref', '')}."
            ),
            evidence_bundle=[source_execution_id],
            constraints=constraints,
            expected_output="advisory critique text and optional improvement notes",
            allowed_actions="advisory_only",
            approval_state="not_required",
            result_refs=[critique_id],
            status="linked",
            producer_id=producer_id,
        )
        critique = DarsCritiqueRecord(
            critique_id=critique_id,
            handoff_ref=handoff_id,
            source_execution_ref=source_execution_id,
            critique_text=critique_text,
            producer_id=producer_id,
            dars_backend=dars_backend,
            external_call_made=external_call_made,
            model_boundary_crossed=model_boundary_crossed,
            local_model_call_made=local_model_call_made,
            endpoint_scope=endpoint_scope,
        )
        _write_handoff(self.instance, yyyymmdd, handoff)
        _write_critique(self.instance, yyyymmdd, critique)
        report.handoff_refs.append(handoff_id)
        report.critique_refs.append(critique_id)
        report.linked_execution_refs.append(source_execution_id)
        _write_report(self.instance, yyyymmdd, report)
        return report

    def run_configured_critique(
        self,
        *,
        yyyymmdd: str,
        source_execution_id: str,
        producer_id: str,
        approval_ref: str | None = None,
    ) -> DarsCritiqueReport:
        config = load_dars_config(self.instance)
        backend_id = config.spec.default_backend
        backend = config.spec.backends[backend_id]
        dispatch = DarsDispatchGate(instance=self.instance).evaluate(
            yyyymmdd=yyyymmdd,
            request_id=source_execution_id,
            config=config,
            backend_id=backend_id,
            approval_ref=approval_ref,
            intent="advisory_critique",
        )
        if dispatch.decision != "allowed":
            raise ValueError(dispatch.reason_code)
        if backend.kind == "loopback":
            return self.run_loopback_placeholder(
                yyyymmdd=yyyymmdd,
                source_execution_id=source_execution_id,
                producer_id=producer_id,
            )
        if backend.kind == "cli_agent":
            critique_text = self._run_cli_agent(
                yyyymmdd=yyyymmdd,
                source_execution_id=source_execution_id,
                backend_id=backend_id,
                backend=backend,
                timeout_seconds=config.spec.policy.max_runtime_seconds,
            )
            return self.run_fixture_critique(
                yyyymmdd=yyyymmdd,
                source_execution_id=source_execution_id,
                critique_text=critique_text,
                producer_id=producer_id,
                dars_backend=backend_id,
                external_call_made=backend.external_call_allowed,
            )
        if backend.kind == "openai_compatible":
            critique_text = self._run_openai_compatible_backend(
                yyyymmdd=yyyymmdd,
                source_execution_id=source_execution_id,
                backend=backend,
                timeout_seconds=config.spec.policy.max_runtime_seconds,
            )
            metadata = derive_local_backend_metadata(backend)
            # `derive_local_backend_metadata` describes the boundary class for
            # the backend (model_boundary_required, external_call_expected);
            # after a successful local LLM call we record that the boundary was
            # actually crossed.
            endpoint_scope = str(metadata.get("endpoint_scope") or "localhost_only")
            report = self.run_fixture_critique(
                yyyymmdd=yyyymmdd,
                source_execution_id=source_execution_id,
                critique_text=critique_text,
                producer_id=producer_id,
                dars_backend=backend_id,
                external_call_made=False,
                model_boundary_crossed=True,
                local_model_call_made=True,
                endpoint_scope=endpoint_scope,
                extra_constraints=[
                    f"endpoint_scope={endpoint_scope}",
                    "model_boundary_crossed=true",
                    "local_model_call_made=true",
                ],
            )
            _write_local_llm_boundary(
                self.instance,
                yyyymmdd=yyyymmdd,
                request_id=source_execution_id,
                backend_id=backend_id,
                approval_ref=approval_ref,
                metadata={
                    "endpoint_scope": endpoint_scope,
                    "model_boundary_crossed": True,
                    "local_model_call_made": True,
                    "external_call_made": False,
                },
            )
            return report
        raise ValueError(f"unsupported DARS backend kind: {backend.kind}")

    def _run_openai_compatible_backend(
        self,
        *,
        yyyymmdd: str,
        source_execution_id: str,
        backend: DarsBackendConfig,
        timeout_seconds: int,
    ) -> str:
        # Defense-in-depth: reject non-loopback endpoints before any socket
        # is opened, even though dars_config validation also rejects them.
        if _classify_local_endpoint(backend.endpoint) is not None:
            raise ValueError("local DARS endpoint failed loopback policy")
        payload = _build_openai_chat_payload(
            backend=backend,
            yyyymmdd=yyyymmdd,
            source_execution_id=source_execution_id,
        )
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            backend.endpoint,
            method="POST",
            data=body,
            headers={
                "content-type": "application/json",
                "accept": "application/json",
                "user-agent": "hisys-dars-local-llm/0.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError:
            raise ValueError("local DARS non-2xx HTTP response") from None
        except (socket.timeout, TimeoutError):
            raise ValueError("local DARS request timed out") from None
        except (urllib.error.URLError, ConnectionError, OSError):
            raise ValueError("local DARS HTTP request failed") from None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("local DARS response is malformed JSON") from None
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ValueError("local DARS response is missing message content") from None
        if not isinstance(content, str) or not content.strip():
            raise ValueError("local DARS response is missing message content")
        return content

    def _run_cli_agent(
        self,
        *,
        yyyymmdd: str,
        source_execution_id: str,
        backend_id: str,
        backend: DarsBackendConfig,
        timeout_seconds: int,
    ) -> str:
        if not backend.command:
            raise ValueError("cli_agent backend requires command")
        prompt = _configured_cli_prompt(yyyymmdd=yyyymmdd, source_execution_id=source_execution_id, backend_id=backend_id)
        if Path(backend.command).name == "claude":
            command = [backend.command, "-p", prompt, *backend.args]
        else:
            command = [backend.command, *backend.args, prompt]
        if backend.model:
            command.extend(["--model", backend.model])
        command.extend(_claude_tool_args(backend))
        completed = subprocess.run(
            command,
            cwd=str(self.instance.root),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError(f"DARS cli_agent failed: {completed.stderr.strip() or completed.stdout.strip()}")
        return _extract_cli_text(completed.stdout)


def _claude_tool_args(backend: DarsBackendConfig) -> list[str]:
    command_name = Path(backend.command or "").name
    if command_name != "claude":
        return []
    args = ["--output-format", "json", "--permission-mode", "dontAsk", "--no-session-persistence"]
    if backend.allowed_tools:
        args.extend(["--allowedTools", ",".join(backend.allowed_tools)])
    if backend.disallowed_tools:
        args.extend(["--disallowedTools", ",".join(backend.disallowed_tools)])
    return args


def _configured_cli_prompt(*, yyyymmdd: str, source_execution_id: str, backend_id: str) -> str:
    return (
        "You are acting as DARS, an advisory-only Hisys critique role. "
        "Return a concise critique of the referenced Hisys connector execution. "
        "Do not write files, mutate state, browse the web, or approve live action. "
        f"date={yyyymmdd}; source_execution_id={source_execution_id}; backend_id={backend_id}."
    )


def _extract_cli_text(stdout: str) -> str:
    text = stdout.strip()
    if not text:
        return "DARS cli_agent returned an empty critique."
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict):
        result = payload.get("result") or payload.get("content") or payload.get("text")
        if isinstance(result, str) and result.strip():
            return result.strip()
    return text


def _load_connector_execution(instance: InstanceRoot, yyyymmdd: str, execution_id: str) -> dict | None:
    path = instance.data_dir / "alert-connector-executions" / yyyymmdd / f"{execution_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_handoff(instance: InstanceRoot, yyyymmdd: str, handoff: AgentHandoffPackage) -> None:
    output_dir = instance.data_dir / "agent-handoffs" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = handoff.model_dump(mode="json")
    (output_dir / f"{handoff.handoff_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / f"{handoff.handoff_id}.md").write_text(
        "\n".join([
            f"# DARS handoff {handoff.handoff_id}",
            "",
            f"- target_agent_system: {handoff.target_agent_system}",
            f"- task: {handoff.task}",
            f"- allowed_actions: {handoff.allowed_actions}",
            f"- approval_state: {handoff.approval_state}",
            f"- status: {handoff.status}",
            f"- evidence_bundle: {', '.join(handoff.evidence_bundle)}",
            "",
        ]),
        encoding="utf-8",
    )


def _write_critique(instance: InstanceRoot, yyyymmdd: str, critique: DarsCritiqueRecord) -> None:
    output_dir = instance.data_dir / "agent-critiques" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = critique.model_dump(mode="json")
    (output_dir / f"{critique.critique_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / f"{critique.critique_id}.md").write_text(
        "\n".join([
            f"# DARS critique {critique.critique_id}",
            "",
            f"- handoff_ref: {critique.handoff_ref}",
            f"- source_execution_ref: {critique.source_execution_ref}",
            f"- allowed_actions: {critique.allowed_actions}",
            f"- dars_backend: {critique.dars_backend}",
            f"- external_call_made: {critique.external_call_made}",
            f"- action_taken: {critique.action_taken}",
            "",
            critique.critique_text,
            "",
        ]),
        encoding="utf-8",
    )


def _write_report(instance: InstanceRoot, yyyymmdd: str, report: DarsCritiqueReport) -> None:
    report_path = _report_json_path(instance, yyyymmdd)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _report_md_path(instance, yyyymmdd).write_text(
        "\n".join([
            "# DARS Critique Report",
            "",
            f"- handoffs: {len(report.handoff_refs)}",
            f"- critiques: {len(report.critique_refs)}",
            f"- linked_executions: {len(report.linked_execution_refs)}",
            f"- skipped_executions: {len(report.skipped_execution_refs)}",
            "",
        ]),
        encoding="utf-8",
    )


def _report_json_path(instance: InstanceRoot, yyyymmdd: str) -> Path:
    return instance.reports_dir / "run-summaries" / yyyymmdd / "dars-critique-report.json"


def _report_md_path(instance: InstanceRoot, yyyymmdd: str) -> Path:
    return instance.reports_dir / "run-summaries" / yyyymmdd / "dars-critique-report.md"


def _suffix(source_execution_id: str) -> str:
    raw = source_execution_id.removeprefix("EXEC-")
    if raw.startswith("DARS-"):
        return raw.removeprefix("DARS-")
    return raw


def _build_openai_chat_payload(
    *,
    backend: DarsBackendConfig,
    yyyymmdd: str,
    source_execution_id: str,
) -> dict[str, Any]:
    system_prompt = (
        "You are DARS, an advisory-only critique role for Hisys. "
        "Your output is advisory_only with no autonomous execution. "
        "Do not mutate state, browse the web, place orders, or approve "
        "live external action.\n\n"
        "Provenance instructions:\n"
        "- Internal knowledge-management sources: cite each source_ref and the supported claim.\n"
        "- External sources are forbidden in this localhost-only review unless explicitly allowed; "
        "if used, cite the DOI/URL/location and the claim supported.\n"
        "- ByeSys generated/unsupported synthesis: label any generated or unsupported claim with "
        "source=ByeSys and evidential_weight=0.0 so reviewers can ignore it as corroboration."
    )
    user_prompt = (
        f"Critique the connector execution recorded under date={yyyymmdd}, "
        f"source_execution_id={source_execution_id}. "
        "Return a concise, structured critique with explicit source provenance."
    )
    return {
        "model": backend.model or "",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }


def _write_local_llm_boundary(
    instance: InstanceRoot,
    *,
    yyyymmdd: str,
    request_id: str,
    backend_id: str,
    approval_ref: str | None,
    metadata: dict[str, Any],
) -> None:
    output_dir = instance.runtime_boundary_dir / "dars" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_id": "hisys.dars.local_llm_boundary",
        "schema_version": "0.1.0",
        "request_id": request_id,
        "backend_id": backend_id,
        "approval_ref": approval_ref,
        "endpoint_scope": metadata.get("endpoint_scope", "localhost_only"),
        "model_boundary_crossed": bool(metadata.get("model_boundary_crossed", True)),
        "local_model_call_made": bool(metadata.get("local_model_call_made", True)),
        "external_call_made": bool(metadata.get("external_call_expected", False)),
        "mutation_performed": False,
        "policy_refs": [
            "HISYS-FR-AGT-001",
            "HISYS-FR-AGT-003",
            "HISYS-CON-010",
            "HISYS-CON-012",
        ],
    }
    json_path = output_dir / f"dars-local-llm-boundary-{request_id}.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = ["DarsCritiqueRecord", "DarsCritiqueReport", "DarsRuntime"]
