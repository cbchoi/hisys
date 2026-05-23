"""Advisory local LSP adapter (M23, governed subprocess).

This is the first Hisys row that spawns a local subprocess. The runner
follows a strict safety contract: caller-supplied command allowlist,
timeout cap, workspace-root containment, output truncation, no shell,
no environment inheritance beyond PATH, no raw message persistence, and
no LSP server installation. The output is an advisory diagnostic report
that records refs, counts, severities, and message digests — never raw
upstream source bodies, secrets, credentials, or live action.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_COMMAND_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_\-]{1,63}$")
_SHELL_METACHARACTERS = (";", "|", "&", "`", "$(", "<(", ">(", "\n", "\r")
_MAX_TIMEOUT_SECONDS = 120
_MAX_OUTPUT_BYTES = 4_194_304  # 4 MiB
_ALLOWED_OUTPUT_FORMATS = frozenset(
    {"pyright_json", "mypy_json", "ruff_json", "flake8_json", "eslint_json"}
)
_LSP_PREFIX = "runtime-boundary/lsp-adapter"


class LspAdapterCommand(BaseModel):
    command_id: str
    argv: tuple[str, ...]
    timeout_seconds: int
    expected_exit_codes: tuple[int, ...] = (0, 1)
    output_format: str


class LspAdapterRequest(BaseModel):
    instance_root: Path
    date: str
    workspace_root: Path
    command: LspAdapterCommand
    target_refs: tuple[str, ...] = ()
    command_allowlist: tuple[str, ...] = ()
    human_approval_ref: str
    current_head_short: str | None = None


class LspAdapterDiagnostic(BaseModel):
    severity: str
    code: str
    file_ref: str
    line: int
    column: int
    message_digest: str
    category_ref: str


class LspAdapterReport(BaseModel):
    schema_id: str = "hisys.lsp_adapter.v1"
    date: str
    current_head_short: str | None = None
    command_id: str
    output_format: str
    workspace_root_ref: str
    target_refs: tuple[str, ...] = ()
    diagnostics: tuple[LspAdapterDiagnostic, ...] = ()
    diagnostic_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    category_ref_summary: tuple[str, ...] = ()
    unsafe_refs: tuple[str, ...] = ()
    subprocess_exit_code: int
    subprocess_timed_out: bool = False
    subprocess_killed: bool = False
    output_truncated: bool = False
    output_bytes: int = 0
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    live_external_action_authorized: bool = False
    allowed_actions: str = "advisory_only"


def _normalize(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(v for v in values if v is not None)))


def _is_unsafe_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        return True
    return False


def _digest_message(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]


def _normalize_severity(value: str) -> str:
    lowered = (value or "").lower()
    if lowered in {"error", "fatal", "severe"}:
        return "error"
    if lowered in {"warning", "warn"}:
        return "warning"
    if lowered in {"info", "information", "note", "hint"}:
        return "info"
    return "info"


def _derive_from_code(code: str) -> tuple[str, str]:
    """Return (severity, category_ref) from a rule code prefix."""

    upper = (code or "").upper()
    if not upper:
        return "info", "other"
    first = upper[0]
    if first == "F":
        return "error", "unused"
    if first == "E":
        return "error", "style"
    if first == "W":
        return "warning", "style_warning"
    if first == "I":
        return "info", "imports"
    if first == "D":
        return "info", "docstring"
    if first == "N":
        return "info", "naming"
    if first == "C":
        return "warning", "complexity"
    if first == "B":
        return "warning", "bugbear"
    if first == "S":
        return "warning", "security"
    return "info", "other"


def _safe_file_ref(raw_path: str, workspace_root: Path) -> tuple[str, bool]:
    """Return (rel_ref, is_unsafe).

    If absolute, attempt to make it relative to ``workspace_root``. If that
    fails (path outside workspace), mark unsafe but still emit the original
    string for traceability.
    """

    if not raw_path:
        return "", True
    candidate = Path(raw_path)
    if candidate.is_absolute():
        try:
            rel = candidate.resolve().relative_to(workspace_root.resolve())
            rel_str = rel.as_posix()
        except ValueError:
            return raw_path, True
    else:
        rel_str = raw_path
    if _is_unsafe_ref(rel_str):
        return rel_str, True
    return rel_str, False


def _validate_lsp_request(request: LspAdapterRequest) -> None:
    if not _DATE_PATTERN.fullmatch(request.date):
        raise ValueError(f"lsp_invalid_date: {request.date!r}")
    if not _COMMAND_ID_PATTERN.fullmatch(request.command.command_id):
        raise ValueError(
            f"lsp_invalid_command_id: {request.command.command_id!r}"
        )
    if request.command.output_format not in _ALLOWED_OUTPUT_FORMATS:
        raise ValueError("lsp_output_format_not_allowed")
    if (
        request.command.timeout_seconds <= 0
        or request.command.timeout_seconds > _MAX_TIMEOUT_SECONDS
    ):
        raise ValueError("lsp_timeout_out_of_range")
    if not request.command.argv:
        raise ValueError("lsp_argv_empty")
    if request.command.argv[0] not in request.command_allowlist:
        raise ValueError("lsp_command_not_in_allowlist")
    for arg in request.command.argv:
        for meta in _SHELL_METACHARACTERS:
            if meta in arg:
                raise ValueError("lsp_argv_shell_metacharacter")
    if not request.human_approval_ref:
        raise ValueError("lsp_human_approval_required")
    try:
        workspace_real = request.workspace_root.resolve()
        instance_real = request.instance_root.resolve()
        workspace_real.relative_to(instance_real)
    except ValueError as exc:
        raise ValueError("lsp_workspace_root_outside_instance") from exc


def _split_target_refs(
    target_refs: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    safe: list[str] = []
    unsafe: list[str] = []
    for ref in target_refs:
        if _is_unsafe_ref(ref):
            unsafe.append(ref)
        else:
            safe.append(ref)
    return tuple(safe), tuple(unsafe)


def _truncate_output(stdout: str) -> tuple[str, int, bool]:
    if stdout is None:
        return "", 0, False
    encoded = stdout.encode("utf-8")
    if len(encoded) <= _MAX_OUTPUT_BYTES:
        return stdout, len(encoded), False
    truncated_bytes = encoded[:_MAX_OUTPUT_BYTES]
    truncated = truncated_bytes.decode("utf-8", errors="ignore")
    return truncated, _MAX_OUTPUT_BYTES, True


def _build_diagnostic(
    *,
    severity: str,
    code: str,
    file_ref: str,
    line: int,
    column: int,
    message: str,
    category_ref: str,
) -> LspAdapterDiagnostic:
    return LspAdapterDiagnostic(
        severity=_normalize_severity(severity),
        code=str(code)[:64],
        file_ref=file_ref,
        line=max(1, int(line) if line else 1),
        column=max(1, int(column) if column else 1),
        message_digest=_digest_message(message or ""),
        category_ref=category_ref,
    )


def _safe_json_loads(raw: str) -> object | None:
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _parse_ruff_json(
    raw: str, workspace_root: Path
) -> tuple[tuple[LspAdapterDiagnostic, ...], tuple[str, ...]]:
    payload = _safe_json_loads(raw)
    if not isinstance(payload, list):
        return (), ()
    diagnostics: list[LspAdapterDiagnostic] = []
    unsafe: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "")
        message = str(item.get("message") or "")
        filename = str(item.get("filename") or "")
        location = item.get("location") or {}
        raw_row = location.get("row") if isinstance(location, dict) else 1
        raw_col = location.get("column") if isinstance(location, dict) else 1
        row = raw_row if isinstance(raw_row, int) else 1
        col = raw_col if isinstance(raw_col, int) else 1
        file_ref, is_unsafe = _safe_file_ref(filename, workspace_root)
        if is_unsafe:
            unsafe.append(file_ref)
            continue
        severity, category = _derive_from_code(code)
        diagnostics.append(
            _build_diagnostic(
                severity=severity,
                code=code,
                file_ref=file_ref,
                line=row,
                column=col,
                message=message,
                category_ref=category,
            )
        )
    return tuple(diagnostics), tuple(unsafe)


def _parse_pyright_json(
    raw: str, workspace_root: Path
) -> tuple[tuple[LspAdapterDiagnostic, ...], tuple[str, ...]]:
    payload = _safe_json_loads(raw)
    if not isinstance(payload, dict):
        return (), ()
    items = payload.get("generalDiagnostics") or []
    if not isinstance(items, list):
        return (), ()
    diagnostics: list[LspAdapterDiagnostic] = []
    unsafe: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        filename = str(item.get("file") or "")
        severity = str(item.get("severity") or "info")
        message = str(item.get("message") or "")
        rule = str(item.get("rule") or "")
        rng = item.get("range") or {}
        start = rng.get("start") if isinstance(rng, dict) else {}
        raw_line = start.get("line") if isinstance(start, dict) else 0
        raw_col = start.get("character") if isinstance(start, dict) else 0
        line = raw_line if isinstance(raw_line, int) else 0
        col = raw_col if isinstance(raw_col, int) else 0
        file_ref, is_unsafe = _safe_file_ref(filename, workspace_root)
        if is_unsafe:
            unsafe.append(file_ref)
            continue
        diagnostics.append(
            _build_diagnostic(
                severity=severity,
                code=rule,
                file_ref=file_ref,
                line=line + 1,
                column=col + 1,
                message=message,
                category_ref="type_check",
            )
        )
    return tuple(diagnostics), tuple(unsafe)


def _parse_mypy_json(
    raw: str, workspace_root: Path
) -> tuple[tuple[LspAdapterDiagnostic, ...], tuple[str, ...]]:
    payload = _safe_json_loads(raw)
    if not isinstance(payload, list):
        return (), ()
    diagnostics: list[LspAdapterDiagnostic] = []
    unsafe: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        filename = str(item.get("path") or item.get("file") or "")
        severity = str(item.get("severity") or "error")
        code = str(item.get("code") or "")
        line = int(item.get("line") or 1)
        col = int(item.get("column") or 1)
        message = str(item.get("message") or "")
        file_ref, is_unsafe = _safe_file_ref(filename, workspace_root)
        if is_unsafe:
            unsafe.append(file_ref)
            continue
        diagnostics.append(
            _build_diagnostic(
                severity=severity,
                code=code,
                file_ref=file_ref,
                line=line,
                column=col,
                message=message,
                category_ref="type_check",
            )
        )
    return tuple(diagnostics), tuple(unsafe)


def _parse_flake8_json(
    raw: str, workspace_root: Path
) -> tuple[tuple[LspAdapterDiagnostic, ...], tuple[str, ...]]:
    payload = _safe_json_loads(raw)
    if not isinstance(payload, dict):
        return (), ()
    diagnostics: list[LspAdapterDiagnostic] = []
    unsafe: list[str] = []
    for filename, items in payload.items():
        if not isinstance(items, list):
            continue
        file_ref, is_unsafe = _safe_file_ref(str(filename), workspace_root)
        if is_unsafe:
            unsafe.append(file_ref)
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "")
            line = int(item.get("line_number") or 1)
            col = int(item.get("column_number") or 1)
            message = str(item.get("text") or "")
            severity, category = _derive_from_code(code)
            diagnostics.append(
                _build_diagnostic(
                    severity=severity,
                    code=code,
                    file_ref=file_ref,
                    line=line,
                    column=col,
                    message=message,
                    category_ref=category,
                )
            )
    return tuple(diagnostics), tuple(unsafe)


def _parse_eslint_json(
    raw: str, workspace_root: Path
) -> tuple[tuple[LspAdapterDiagnostic, ...], tuple[str, ...]]:
    payload = _safe_json_loads(raw)
    if not isinstance(payload, list):
        return (), ()
    diagnostics: list[LspAdapterDiagnostic] = []
    unsafe: list[str] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        filename = str(entry.get("filePath") or "")
        file_ref, is_unsafe = _safe_file_ref(filename, workspace_root)
        if is_unsafe:
            unsafe.append(file_ref)
            continue
        messages = entry.get("messages") or []
        if not isinstance(messages, list):
            continue
        for item in messages:
            if not isinstance(item, dict):
                continue
            sev_raw = item.get("severity")
            if sev_raw == 2:
                severity = "error"
            elif sev_raw == 1:
                severity = "warning"
            else:
                severity = "info"
            code = str(item.get("ruleId") or "")
            line = int(item.get("line") or 1)
            col = int(item.get("column") or 1)
            message = str(item.get("message") or "")
            diagnostics.append(
                _build_diagnostic(
                    severity=severity,
                    code=code,
                    file_ref=file_ref,
                    line=line,
                    column=col,
                    message=message,
                    category_ref="lint",
                )
            )
    return tuple(diagnostics), tuple(unsafe)


_PARSERS = {
    "ruff_json": _parse_ruff_json,
    "pyright_json": _parse_pyright_json,
    "mypy_json": _parse_mypy_json,
    "flake8_json": _parse_flake8_json,
    "eslint_json": _parse_eslint_json,
}


def _aggregate_counts(
    diagnostics: tuple[LspAdapterDiagnostic, ...],
) -> tuple[int, int, int, tuple[str, ...]]:
    err = sum(1 for d in diagnostics if d.severity == "error")
    warn = sum(1 for d in diagnostics if d.severity == "warning")
    info = sum(1 for d in diagnostics if d.severity == "info")
    categories = _normalize(d.category_ref for d in diagnostics)
    return err, warn, info, categories


def _sorted_diagnostics(
    diagnostics: tuple[LspAdapterDiagnostic, ...],
) -> tuple[LspAdapterDiagnostic, ...]:
    return tuple(
        sorted(
            diagnostics,
            key=lambda d: (d.file_ref, d.line, d.column, d.code, d.severity),
        )
    )


def run_lsp_adapter(*, request: LspAdapterRequest) -> LspAdapterReport:
    _validate_lsp_request(request)

    safe_targets, unsafe_targets = _split_target_refs(request.target_refs)

    workspace_real = request.workspace_root.resolve()
    instance_real = request.instance_root.resolve()
    workspace_root_ref = workspace_real.relative_to(instance_real).as_posix()
    if workspace_root_ref == "":
        workspace_root_ref = "."

    try:
        completed = subprocess.run(
            list(request.command.argv),
            cwd=request.workspace_root,
            env={"PATH": os.environ.get("PATH", "")},
            timeout=request.command.timeout_seconds,
            capture_output=True,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return LspAdapterReport(
            date=request.date,
            current_head_short=request.current_head_short,
            command_id=request.command.command_id,
            output_format=request.command.output_format,
            workspace_root_ref=workspace_root_ref,
            target_refs=_normalize(safe_targets),
            diagnostics=(),
            diagnostic_count=0,
            error_count=0,
            warning_count=0,
            info_count=0,
            category_ref_summary=(),
            unsafe_refs=_normalize(unsafe_targets),
            subprocess_exit_code=-1,
            subprocess_timed_out=True,
            subprocess_killed=False,
            output_truncated=False,
            output_bytes=0,
        )
    except FileNotFoundError as exc:
        raise ValueError("lsp_command_not_found") from exc

    stdout_text = completed.stdout
    if isinstance(stdout_text, bytes):
        stdout_text = stdout_text.decode("utf-8", errors="ignore")
    truncated, output_bytes, output_truncated = _truncate_output(
        stdout_text or ""
    )

    parser = _PARSERS[request.command.output_format]
    parsed_diagnostics, parse_unsafe = parser(truncated, request.workspace_root)
    diagnostics = _sorted_diagnostics(parsed_diagnostics)
    err, warn, info, categories = _aggregate_counts(diagnostics)
    unsafe_all = _normalize(tuple(unsafe_targets) + tuple(parse_unsafe))

    return LspAdapterReport(
        date=request.date,
        current_head_short=request.current_head_short,
        command_id=request.command.command_id,
        output_format=request.command.output_format,
        workspace_root_ref=workspace_root_ref,
        target_refs=_normalize(safe_targets),
        diagnostics=diagnostics,
        diagnostic_count=len(diagnostics),
        error_count=err,
        warning_count=warn,
        info_count=info,
        category_ref_summary=categories,
        unsafe_refs=unsafe_all,
        subprocess_exit_code=int(completed.returncode),
        subprocess_timed_out=False,
        subprocess_killed=False,
        output_truncated=output_truncated,
        output_bytes=output_bytes,
    )


def render_lsp_adapter_markdown(report: LspAdapterReport) -> str:
    lines: list[str] = []
    lines.append(f"# LSP Adapter Report — {report.schema_id}")
    lines.append("")
    lines.append(f"- date: {report.date}")
    lines.append(f"- current_head_short: {report.current_head_short or 'n/a'}")
    lines.append(f"- command_id: {report.command_id}")
    lines.append(f"- output_format: {report.output_format}")
    lines.append(f"- workspace_root_ref: {report.workspace_root_ref}")
    lines.append(f"- diagnostic_count: {report.diagnostic_count}")
    lines.append(f"- error_count: {report.error_count}")
    lines.append(f"- warning_count: {report.warning_count}")
    lines.append(f"- info_count: {report.info_count}")
    lines.append(f"- subprocess_exit_code: {report.subprocess_exit_code}")
    lines.append(
        f"- subprocess_timed_out: {str(report.subprocess_timed_out).lower()}"
    )
    lines.append(
        f"- subprocess_killed: {str(report.subprocess_killed).lower()}"
    )
    lines.append(f"- output_truncated: {str(report.output_truncated).lower()}")
    lines.append(f"- output_bytes: {report.output_bytes}")
    lines.append(f"- advisory_only: {str(report.advisory_only).lower()}")
    lines.append(
        f"- requires_human_review: "
        f"{str(report.requires_human_review).lower()}"
    )
    lines.append(
        f"- external_call_made: {str(report.external_call_made).lower()}"
    )
    lines.append(
        f"- mutation_performed: {str(report.mutation_performed).lower()}"
    )
    lines.append(
        "- raw_source_content_persisted: "
        f"{str(report.raw_source_content_persisted).lower()}"
    )
    lines.append(
        "- live_external_action_authorized: "
        f"{str(report.live_external_action_authorized).lower()}"
    )
    lines.append(f"- allowed_actions: {report.allowed_actions}")
    lines.append("")

    def _section(title: str, values: tuple[str, ...]) -> None:
        lines.append(f"## {title}")
        if not values:
            lines.append("- (none)")
        else:
            for value in values:
                lines.append(f"- {value}")
        lines.append("")

    _section("Target refs", report.target_refs)
    _section("Category refs", report.category_ref_summary)
    _section("Unsafe refs", report.unsafe_refs)

    lines.append("## Diagnostics")
    if not report.diagnostics:
        lines.append("- (none)")
    else:
        lines.append(
            "| severity | code | file_ref | line | column | "
            "category_ref | message_digest |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for diag in report.diagnostics:
            lines.append(
                f"| {diag.severity} | {diag.code} | {diag.file_ref} | "
                f"{diag.line} | {diag.column} | {diag.category_ref} | "
                f"{diag.message_digest} |"
            )
    lines.append("")
    return "\n".join(lines) + "\n"


def write_lsp_adapter_report(
    *,
    instance_root: Path,
    date: str,
    report: LspAdapterReport,
) -> dict[str, object]:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid lsp adapter report date: {date!r}")
    if not _COMMAND_ID_PATTERN.fullmatch(report.command_id):
        raise ValueError(
            f"invalid lsp adapter command_id: {report.command_id!r}"
        )
    rel_dir = f"{_LSP_PREFIX}/{date}/{report.command_id}"
    json_ref = f"{rel_dir}/lsp-report.json"
    md_ref = f"{rel_dir}/lsp-report.md"
    json_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=json_ref
    )
    md_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=md_ref
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        render_lsp_adapter_markdown(report), encoding="utf-8"
    )
    return {
        "schema_id": report.schema_id,
        "json_ref": json_ref,
        "markdown_ref": md_ref,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "live_external_action_authorized": False,
        "allowed_actions": "advisory_only",
    }


__all__ = [
    "LspAdapterCommand",
    "LspAdapterRequest",
    "LspAdapterDiagnostic",
    "LspAdapterReport",
    "run_lsp_adapter",
    "render_lsp_adapter_markdown",
    "write_lsp_adapter_report",
]
