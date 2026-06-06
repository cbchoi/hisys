"""Subprocess-safe Hisys CLI adapter used by the MCP wrapper layer."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Mapping, Sequence

_SECRET_PATTERNS = (
    (re.compile(r"(?i)(token" + r"=)[^\s]+"), r"\1<redacted>"),
    (re.compile(r"(?i)(password" + r"=)[^\s]+"), r"\1<redacted>"),
    (re.compile(r"(?i)(Authorization:\s*Bearer\s+)[^\s]+"), r"\1<redacted>"),
)


@dataclass(frozen=True)
class CliInvocationResult:
    args: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int | None
    timed_out: bool = False


def redact_text(text: str) -> str:
    redacted = text
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _text_from_timeout_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def run_hisys_cli(
    args: Sequence[str],
    *,
    timeout_seconds: int,
    env: Mapping[str, str] | None = None,
) -> CliInvocationResult:
    """Run a local CLI command, capturing stdout/stderr without raising on failures."""

    command = tuple(str(arg) for arg in args)
    merged_env = os.environ.copy()
    if env:
        merged_env.update({str(key): str(value) for key, value in env.items()})
    try:
        completed = subprocess.run(
            command,
            env=merged_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CliInvocationResult(
            args=command,
            stdout=redact_text(_text_from_timeout_stream(exc.stdout)),
            stderr=redact_text(_text_from_timeout_stream(exc.stderr)),
            returncode=None,
            timed_out=True,
        )
    return CliInvocationResult(
        args=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
        timed_out=False,
    )


def parse_json_stdout(result: CliInvocationResult) -> dict:
    """Parse JSON stdout or return a bounded redacted error mapping."""

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {
            "status": "error",
            "error": f"invalid JSON stdout: {exc.msg}",
            "stdout": redact_text(result.stdout),
            "stderr": redact_text(result.stderr),
        }
    if isinstance(parsed, dict):
        return parsed
    return {"status": "error", "error": "JSON stdout was not an object", "payload": parsed}


def summarize_cli_error(result: CliInvocationResult) -> str:
    if result.timed_out:
        return f"timeout while running {' '.join(result.args)}"
    return redact_text(result.stderr or result.stdout or f"exit code {result.returncode}")


__all__ = [
    "CliInvocationResult",
    "parse_json_stdout",
    "redact_text",
    "run_hisys_cli",
    "summarize_cli_error",
]
