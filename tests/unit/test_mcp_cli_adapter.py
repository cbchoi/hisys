"""Subprocess-safe Hisys MCP CLI adapter tests.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Tasks 2.1-2.2 and Claude review safety revisions.
"""

from __future__ import annotations

import importlib
import sys


def _adapter_module():
    return importlib.import_module("hisys.mcp.cli_adapter")


def test_cli_adapter_captures_json_stdout_from_fixture_command() -> None:
    adapter = _adapter_module()

    result = adapter.run_hisys_cli(
        [sys.executable, "-c", "import json; print(json.dumps({'status': 'ok', 'value': 3}))"],
        timeout_seconds=10,
        env={"HISYS_TEST_SAFE_ENV": "1"},
    )

    assert result.returncode == 0
    assert result.timed_out is False
    assert result.stderr == ""
    assert adapter.parse_json_stdout(result) == {"status": "ok", "value": 3}


def test_cli_adapter_returns_nonzero_exit_and_stderr_without_raising() -> None:
    adapter = _adapter_module()

    result = adapter.run_hisys_cli(
        [sys.executable, "-c", "import sys; print('bad tok' + 'en=SHOULD_REDACT', file=sys.stderr); sys.exit(7)"],
        timeout_seconds=10,
        env={},
    )

    assert result.returncode == 7
    assert result.timed_out is False
    assert "SHOULD_REDACT" not in adapter.summarize_cli_error(result)
    assert "tok" + "en=<redacted>" in adapter.summarize_cli_error(result)


def test_cli_adapter_timeout_returns_timed_out_result() -> None:
    adapter = _adapter_module()

    result = adapter.run_hisys_cli(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout_seconds=1,
        env={},
    )

    assert result.timed_out is True
    assert result.returncode is None
    assert "timeout" in adapter.summarize_cli_error(result).lower()


def test_json_parse_error_is_bounded_and_redacts_secrets() -> None:
    adapter = _adapter_module()
    result = adapter.CliInvocationResult(
        args=("hisys", "fixture"),
        stdout="not-json pass" + "word=SHOULD_REDACT",
        stderr="Authorization: Bearer SHOULD_REDACT_TOO",
        returncode=0,
        timed_out=False,
    )

    error = adapter.parse_json_stdout(result)

    assert error["status"] == "error"
    assert "SHOULD_REDACT" not in str(error)
    assert "Authorization: Bearer <redacted>" in str(error)
