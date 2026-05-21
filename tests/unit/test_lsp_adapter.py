"""M23 local LSP adapter tests.

Caller-supplied governance contract for a local subprocess: command allowlist,
timeout cap, workspace-root containment, output truncation, no shell, no
environment inheritance beyond PATH, no raw message persistence. The runner
never installs an LSP server, never crosses the network, never reads .git/,
never speaks the LSP wire protocol, and never claims live action.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hisys.operations.lsp_adapter import (
    LspAdapterCommand,
    LspAdapterRequest,
    run_lsp_adapter,
    write_lsp_adapter_report,
)


_FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "lsp-adapter"
)


def _canned_ruff_stdout() -> str:
    return (_FIXTURE_DIR / "ruff" / "canned_ruff_output.json").read_text(
        encoding="utf-8"
    )


def _ruff_command() -> LspAdapterCommand:
    return LspAdapterCommand(
        command_id="ruff-check",
        argv=("ruff", "check", "--output-format=json", "src/"),
        timeout_seconds=30,
        expected_exit_codes=(0, 1),
        output_format="ruff_json",
    )


def _prepare_workspace(tmp_path: Path) -> tuple[Path, Path]:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    workspace_root = instance_root / "workspace"
    workspace_root.mkdir()
    (workspace_root / "src").mkdir()
    (workspace_root / "src" / "a.py").write_text("", encoding="utf-8")
    (workspace_root / "src" / "b.py").write_text("", encoding="utf-8")
    return instance_root, workspace_root


def test_run_lsp_adapter_aggregates_ruff_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py", "src/b.py"),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
        current_head_short="0a172d3",
    )
    fake_run = MagicMock()
    fake_run.return_value = subprocess.CompletedProcess(
        args=list(request.command.argv),
        returncode=1,
        stdout=_canned_ruff_stdout(),
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    report = run_lsp_adapter(request=request)

    assert report.schema_id == "hisys.lsp_adapter.v1"
    assert report.date == "20260522"
    assert report.current_head_short == "0a172d3"
    assert report.command_id == "ruff-check"
    assert report.output_format == "ruff_json"
    assert report.subprocess_exit_code == 1
    assert report.subprocess_timed_out is False
    assert report.subprocess_killed is False
    assert report.output_truncated is False
    assert report.diagnostic_count >= 1
    assert report.error_count + report.warning_count + report.info_count == (
        report.diagnostic_count
    )
    assert report.unsafe_refs == ()
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.live_external_action_authorized is False
    assert report.allowed_actions == "advisory_only"
    for diag in report.diagnostics:
        assert len(diag.message_digest) == 16
        assert all(c in "0123456789abcdef" for c in diag.message_digest)
        assert not hasattr(diag, "message")
    fake_run.assert_called_once()
    called_argv = fake_run.call_args[0][0]
    called_kwargs = fake_run.call_args[1]
    assert called_argv == list(request.command.argv)
    assert called_kwargs["shell"] is False
    assert called_kwargs["cwd"] == workspace_root
    assert "PATH" in called_kwargs["env"]
    assert set(called_kwargs["env"].keys()) == {"PATH"}


def test_run_lsp_adapter_rejects_command_not_in_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=LspAdapterCommand(
            command_id="rm-rf",
            argv=("rm", "-rf", "/"),
            timeout_seconds=30,
            output_format="ruff_json",
        ),
        target_refs=(),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="lsp_command_not_in_allowlist"):
        run_lsp_adapter(request=request)
    fake_run.assert_not_called()


def test_run_lsp_adapter_records_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )

    def _raise_timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", _raise_timeout)

    report = run_lsp_adapter(request=request)
    assert report.subprocess_timed_out is True
    assert report.diagnostics == ()
    assert report.diagnostic_count == 0
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.info_count == 0
    assert report.advisory_only is True
    assert report.external_call_made is False


def test_run_lsp_adapter_truncates_oversize_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    oversize_payload = "[" + ("," * 5_000_000) + "]"
    fake_run = MagicMock()
    fake_run.return_value = subprocess.CompletedProcess(
        args=list(request.command.argv),
        returncode=0,
        stdout=oversize_payload,
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    report = run_lsp_adapter(request=request)
    assert report.output_truncated is True
    assert report.output_bytes == 4_194_304


def test_run_lsp_adapter_rejects_output_format_outside_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=LspAdapterCommand(
            command_id="ruff-check",
            argv=("ruff", "check", "src/"),
            timeout_seconds=30,
            output_format="custom_xml",
        ),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="lsp_output_format_not_allowed"):
        run_lsp_adapter(request=request)
    fake_run.assert_not_called()


def test_run_lsp_adapter_rejects_timeout_out_of_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=LspAdapterCommand(
            command_id="ruff-check",
            argv=("ruff", "check", "src/"),
            timeout_seconds=600,
            output_format="ruff_json",
        ),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="lsp_timeout_out_of_range"):
        run_lsp_adapter(request=request)
    fake_run.assert_not_called()


def test_run_lsp_adapter_rejects_shell_metacharacter_in_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=LspAdapterCommand(
            command_id="ruff-check",
            argv=("ruff", "check", "$(rm -rf /)", "src/"),
            timeout_seconds=30,
            output_format="ruff_json",
        ),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="lsp_argv_shell_metacharacter"):
        run_lsp_adapter(request=request)
    fake_run.assert_not_called()


def test_run_lsp_adapter_rejects_missing_human_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="lsp_human_approval_required"):
        run_lsp_adapter(request=request)
    fake_run.assert_not_called()


def test_run_lsp_adapter_rejects_workspace_root_outside_instance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    outside_workspace = tmp_path / "outside-workspace"
    outside_workspace.mkdir()
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=outside_workspace,
        command=_ruff_command(),
        target_refs=(),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="lsp_workspace_root_outside_instance"):
        run_lsp_adapter(request=request)
    fake_run.assert_not_called()


def test_run_lsp_adapter_converts_filenotfound_to_command_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )

    def _raise_filenotfound(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("ruff: command not found")

    monkeypatch.setattr(subprocess, "run", _raise_filenotfound)

    with pytest.raises(ValueError, match="lsp_command_not_found"):
        run_lsp_adapter(request=request)


def test_run_lsp_adapter_rejects_unsafe_target_refs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py", "../escape.py", "/etc/passwd"),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    fake_run.return_value = subprocess.CompletedProcess(
        args=list(request.command.argv),
        returncode=0,
        stdout="[]",
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    report = run_lsp_adapter(request=request)
    assert "../escape.py" in report.unsafe_refs
    assert "/etc/passwd" in report.unsafe_refs
    assert "src/a.py" in report.target_refs
    assert "../escape.py" not in report.target_refs
    assert "/etc/passwd" not in report.target_refs


def test_write_lsp_adapter_persists_safe_refs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py", "src/b.py"),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    fake_run.return_value = subprocess.CompletedProcess(
        args=list(request.command.argv),
        returncode=1,
        stdout=_canned_ruff_stdout(),
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)
    report = run_lsp_adapter(request=request)

    refs = write_lsp_adapter_report(
        instance_root=instance_root, date="20260522", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/lsp-adapter/20260522/ruff-check/lsp-report.json"
    )
    assert refs["markdown_ref"] == (
        "runtime-boundary/lsp-adapter/20260522/ruff-check/lsp-report.md"
    )
    assert refs["external_call_made"] is False
    assert refs["mutation_performed"] is False
    assert refs["raw_source_content_persisted"] is False
    assert refs["allowed_actions"] == "advisory_only"
    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()
    md_body = md_path.read_text(encoding="utf-8")
    raw_messages = [
        diag["message"] for diag in json.loads(_canned_ruff_stdout())
    ]
    for raw in raw_messages:
        assert raw not in md_body


def test_write_lsp_adapter_rejects_bad_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root, workspace_root = _prepare_workspace(tmp_path)
    request = LspAdapterRequest(
        instance_root=instance_root,
        date="20260522",
        workspace_root=workspace_root,
        command=_ruff_command(),
        target_refs=("src/a.py",),
        command_allowlist=("ruff",),
        human_approval_ref="docs/approvals/lsp-adapter-test.md",
    )
    fake_run = MagicMock()
    fake_run.return_value = subprocess.CompletedProcess(
        args=list(request.command.argv),
        returncode=0,
        stdout="[]",
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)
    report = run_lsp_adapter(request=request)
    with pytest.raises(ValueError):
        write_lsp_adapter_report(
            instance_root=instance_root,
            date="2026-05-22",
            report=report,
        )
