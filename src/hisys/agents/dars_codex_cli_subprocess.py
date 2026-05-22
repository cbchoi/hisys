"""Codex CLI subprocess prompt-mode executor preparation.

This module prepares the narrow executor shape for the governed Codex DARS path.
It does not inspect Codex credentials, import a Codex SDK, call a raw provider
API, configure provider accounts, publish, mutate, or grant tools/search/browser
authority. Runtime callers must still supply an explicit activation/policy gate
through the remote subscription dispatch harness before this executor is used.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

_CODEX_PROVIDER_ID = "codex"
_CODEX_ADAPTER_CLASS = "codex_subscription"
_TRANSPORT_KIND = "codex_cli_subprocess_prompt_mode"
_ALLOWED_ACTIONS = "advisory_only"
_MAX_PROMPT_CHARS = 24_000
_MAX_STDERR_PREVIEW_CHARS = 500
_MAX_CRITIQUE_CHARS = 32_000
_RAW_SECRET_MARKERS = re.compile(
    r"(?i)(api[_-]?key\s*[:=]|auth[_-]?token\s*[:=]|access[_-]?token\s*[:=]|authorization\s*:|"
    r"refresh[_-]?token\s*[:=]|password\s*[:=]|credentials?\s*[:=]|secrets?\s*[:=]|"
    r"sk-[A-Za-z0-9]|sk_[A-Za-z0-9]|ghp_[A-Za-z0-9]|xoxb-|xoxp-|hf_[A-Za-z0-9])"
)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_FORBIDDEN_AUTHORITY_MARKERS = re.compile(
    r"(?i)("
    r"workspace[_\-\s]?write\s*[:=]+\s*true|"
    r"web[_\-\s]?search\s*[:=]+\s*true|"
    r"sandbox[_\-\s]?bypass|"
    r"danger[_\-\s]?full[_\-\s]?access|"
    r"mutation[_\-\s]?performed\s*[:=]+\s*true|"
    r"publication[_\-\s]?performed\s*[:=]+\s*true|"
    r"requires[_\-\s]?human[_\-\s]?review\s*[:=]+\s*false|"
    r"<<\s*executing\s+shell\s*>>|"
    r"<<\s*tool\s+call\s*>>"
    r")"
)


class SubprocessRunner(Protocol):
    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True)
class CodexCliSubprocessConfig:
    codex_executable: str
    workdir: Path
    timeout_seconds: int = 120
    redaction_policy_ref: str = "policy://hisys/dars/codex-subscription-redaction-v1"


def build_codex_cli_prompt_mode_executor(
    config: CodexCliSubprocessConfig,
    *,
    runner: SubprocessRunner | None = None,
) -> Callable[[dict[str, Any]], str]:
    """Build a `RemoteSubscriptionExecutor` for bounded Codex CLI prompt mode.

    The returned callable matches the existing injected-executor seam:
    ``Callable[[dict[str, Any]], str]``. Tests can inject a fake runner; the
    default runner is ``subprocess.run``. The executor constructs a fixed
    noninteractive read-only command and fails closed before spawning on policy,
    redaction, mutation, or publication violations.
    """

    _validate_config(config)
    run = runner or subprocess.run

    def executor(payload: dict[str, Any]) -> str:
        prompt_packet = build_redacted_codex_dars_prompt_packet(payload, config=config)
        argv = [
            config.codex_executable,
            "--ask-for-approval",
            "never",
            "exec",
            "--sandbox",
            "read-only",
            "--cd",
            str(config.workdir),
            "--",
            prompt_packet,
        ]
        try:
            completed = run(
                argv,
                cwd=config.workdir,
                env={"PATH": os.environ.get("PATH", "")},
                timeout=config.timeout_seconds,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError(
                f"codex_cli_subprocess_timeout: timeout_seconds={config.timeout_seconds}"
            ) from exc
        if completed.returncode != 0:
            stderr_preview = _redact_stderr_for_error_message(
                (completed.stderr or "")[:_MAX_STDERR_PREVIEW_CHARS]
            )
            raise ValueError(f"codex_cli_subprocess_failed: returncode={completed.returncode}: {stderr_preview}")
        critique_text = (completed.stdout or "").strip()
        if not critique_text:
            raise ValueError("codex_cli_subprocess_empty_output")
        if len(critique_text) > _MAX_CRITIQUE_CHARS:
            raise ValueError("codex_cli_subprocess_output_too_long")
        if _CONTROL_CHAR_RE.search(critique_text):
            raise ValueError("codex_cli_subprocess_output_contains_control_chars")
        if _FORBIDDEN_AUTHORITY_MARKERS.search(critique_text):
            raise ValueError("codex_cli_subprocess_output_claims_unauthorized_authority")
        if _RAW_SECRET_MARKERS.search(critique_text):
            raise ValueError("codex_cli_output_not_redacted")
        return critique_text

    return executor


def build_redacted_codex_dars_prompt_packet(
    payload: dict[str, Any],
    *,
    config: CodexCliSubprocessConfig,
) -> str:
    """Validate and render the bounded prompt crossing into Codex CLI."""

    _validate_payload(payload)
    raw_prompt = str(payload["prompt"])
    if _RAW_SECRET_MARKERS.search(raw_prompt):
        raise ValueError("codex_cli_prompt_not_redacted")
    bounded_prompt = raw_prompt[:_MAX_PROMPT_CHARS]
    packet_lines = [
        "DARS Codex CLI subprocess prompt-mode packet",
        f"transport_kind={_TRANSPORT_KIND}",
        f"provider_id={_CODEX_PROVIDER_ID}",
        f"adapter_class={_CODEX_ADAPTER_CLASS}",
        f"allowed_actions={_ALLOWED_ACTIONS}",
        f"redaction_policy_ref={config.redaction_policy_ref}",
        f"request_id={payload['request_id']}",
        f"source_execution_id={payload['source_execution_id']}",
        f"approval_ref={payload['approval_ref']}",
        "",
        "Boundary:",
        "- Advisory critique only.",
        "- Do not mutate files, git state, runtime state, credentials, accounts, or external systems.",
        "- Do not use web search, browser tools, shell tools, code execution tools, publication, deployment, PRs, or issues.",
        "- Do not request credential material, Authorization headers, API keys, refresh tokens, vault unseal, or account configuration.",
        "- Do not upgrade the DARS completion claim; requires_human_review remains true.",
        "",
        "Critique prompt:",
        bounded_prompt,
    ]
    return "\n".join(packet_lines)


def _redact_stderr_for_error_message(stderr_preview: str) -> str:
    if stderr_preview and _RAW_SECRET_MARKERS.search(stderr_preview):
        return f"<stderr-redacted-secret-detected len={len(stderr_preview)}>"
    return stderr_preview


def _validate_config(config: CodexCliSubprocessConfig) -> None:
    if not config.codex_executable or any(sep in config.codex_executable for sep in ("\n", "\r", "\x00")):
        raise ValueError("codex_cli_invalid_executable")
    if not config.workdir.exists() or not config.workdir.is_dir():
        raise ValueError("codex_cli_invalid_workdir")
    if not (1 <= config.timeout_seconds <= 600):
        raise ValueError("codex_cli_invalid_timeout")
    if not config.redaction_policy_ref.startswith("policy://"):
        raise ValueError("codex_cli_invalid_redaction_policy_ref")


def _validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("provider_id") != _CODEX_PROVIDER_ID:
        raise ValueError("codex_cli_invalid_provider")
    if payload.get("adapter_class") != _CODEX_ADAPTER_CLASS:
        raise ValueError("codex_cli_invalid_adapter_class")
    if payload.get("transport_kind") != _TRANSPORT_KIND:
        raise ValueError("codex_cli_invalid_transport_kind")
    if payload.get("allowed_actions") != _ALLOWED_ACTIONS:
        raise ValueError("codex_cli_invalid_allowed_actions")
    if payload.get("mutation_performed") is not False:
        raise ValueError("codex_cli_mutation_flag_not_allowed")
    if payload.get("publication_performed") is not False:
        raise ValueError("codex_cli_publication_flag_not_allowed")
    for field_name in (
        "request_id",
        "source_execution_id",
        "backend_id",
        "backend_kind",
        "approval_ref",
        "policy_ref",
        "activation_ref",
        "prompt",
    ):
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"codex_cli_missing_{field_name}")
