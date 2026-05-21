# Milestone M23 — Local LSP Adapter Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M23-LSP-ADAPTER-PREP`. Subsequent rows `M23-LSP-ADAPTER-RED-GREEN`, and the later `M23-LSP-ADAPTER-CLI` / `M23-LSP-ADAPTER-GOLDEN` follow-ons are scoped at the end of this file.

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for the M23 local LSP adapter line, authored after the M23-OSS-ADAPTER-GATE closure at `0a172d3 docs: close m23 oss comparison adapter milestone` and after the OSS adapter line landed at `9963ccc test: pin oss comparison adapter golden fixture`. The LSP adapter is the **first** Hisys row that authorizes local `subprocess` spawning under a strict caller-supplied governance contract. It does **not** authorize network access, credential lookup, secret capture, live LSP server installation, package installation, raw source archival, publication, deployment, or unbounded process execution.

**Goal:** Add a pure, local-only, advisory `local LSP adapter` surface that runs a caller-supplied LSP-aware command (e.g. `pyright --outputjson <file>`, `mypy --json-report - <file>`, `ruff check --output-format=json <file>`) against a caller-supplied workspace root under a strict subprocess safety contract, parses the deterministic JSON output, and records bounded LSP diagnostic refs (severity, code, message digest, file ref, line, column) plus advisory flags. The adapter never installs an LSP server, never starts a long-lived daemon, never speaks the LSP protocol over a socket, never reads `.git/`, never crosses the network, never embeds raw source bodies in the report, and never captures secrets or credentials.

**Architecture:** Add a new pure-Python module `src/hisys/operations/lsp_adapter.py` exposing:

1. A Pydantic `LspAdapterCommand` record describing one caller-supplied command: `command_id` (matching `^[a-z][a-z0-9_\-]{1,63}$`), sorted `argv: tuple[str, ...]` (the exact argv list; `argv[0]` is the command binary name only — no path), `timeout_seconds: int` (positive, capped at a module-level `_MAX_TIMEOUT_SECONDS=120`), `expected_exit_codes: tuple[int, ...]` (allowed exit codes; default `(0, 1)` since most linters exit 1 on findings), and `output_format: str` (one of the deterministic-parser allowlist: `pyright_json`, `mypy_json`, `ruff_json`, `flake8_json`, `eslint_json`).
2. A Pydantic `LspAdapterRequest` record carrying `instance_root: Path`, `date: str` (`YYYYMMDD`), `workspace_root: Path` (must be inside `instance_root` or a caller-supplied trusted local directory; never absolute outside the host workspace), `command: LspAdapterCommand`, `target_refs: tuple[str, ...]` (sorted relative paths under `workspace_root`; same `_is_unsafe_ref` rule as M22/M23 — `..`, absolute, empty all rejected), `command_allowlist: tuple[str, ...]` (caller-supplied set of allowed `argv[0]` values; `command.argv[0]` must be in this set), `human_approval_ref: str` (caller-supplied approval anchor, e.g. `docs/approvals/lsp-adapter-2026-05-22.md`), and optional `current_head_short: str | None`. The request is the single intake surface; no implicit `date.today()`, `.git/` read, network call, package install, environment inheritance beyond `PATH`, or shell expansion may be added.
3. A Pydantic `LspAdapterDiagnostic` record holding `severity` (`error`, `warning`, `info`), `code` (LSP rule code, max 64 chars, ASCII), `file_ref` (relative path under `workspace_root`), `line` (1-indexed), `column` (1-indexed), `message_digest` (SHA-256 first-16-hex of the raw message; the raw message body is **not** stored), and `category_ref` (sorted normalization e.g. `type_error`, `unused_import`, `style`). Raw message text is never persisted to avoid leaking secrets or proprietary source quotes.
4. A Pydantic `LspAdapterReport` record holding `schema_id = "hisys.lsp_adapter.v1"`, `date`, `current_head_short`, `command_id`, `output_format`, `workspace_root_ref` (the relative ref under `instance_root`), sorted `target_refs`, sorted `diagnostics: tuple[LspAdapterDiagnostic, ...]`, `diagnostic_count`, `error_count`, `warning_count`, `info_count`, sorted `category_ref_summary`, sorted `unsafe_refs`, `subprocess_exit_code`, `subprocess_timed_out`, `subprocess_killed`, `output_truncated`, `output_bytes`, the existing advisory flag set (`advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `live_external_action_authorized=false`), and `allowed_actions = "advisory_only"`.
5. A pure function `_validate_lsp_request(request)` that rejects: an `argv[0]` not in `command_allowlist`; a `workspace_root` that is absolute outside the host workspace or contains `..`; `target_refs` that contain unsafe paths; a `timeout_seconds` outside `(0, _MAX_TIMEOUT_SECONDS]`; an `output_format` outside the parser allowlist; a missing `human_approval_ref`; any value in `command.argv` that contains a shell metacharacter (`;`, `|`, `&`, `` ` ``, `$(`, `<(`, `>(`, newline). All rejections raise deterministic `ValueError` with the rule code.
6. A function `run_lsp_adapter(*, request)` that executes the validated command using `subprocess.run(argv, cwd=workspace_root, env={"PATH": os.environ.get("PATH", "")}, timeout=timeout_seconds, capture_output=True, check=False, shell=False)`, truncates stdout to `_MAX_OUTPUT_BYTES=4_194_304` (4 MiB) before parsing, parses the output through one of the deterministic format-specific parsers (no `eval`, no `exec`, no `pickle`), normalizes diagnostics through the unsafe-ref rule, and returns an `LspAdapterReport`. If the subprocess times out, raises `subprocess.TimeoutExpired`, which is caught and the report is emitted with `subprocess_timed_out=true`, `diagnostics=()`, and `error_count=0` so the caller knows the run was incomplete. If `argv[0]` cannot be found on `PATH`, the `FileNotFoundError` raised by `subprocess.run` is converted to a deterministic `ValueError("lsp_command_not_found")`.
7. A writer `write_lsp_adapter_report(*, instance_root, date, report)` that persists JSON + Markdown only under `runtime-boundary/lsp-adapter/<YYYYMMDD>/<command_id>/lsp-report.{json,md}` through the existing `resolve_instance_runtime_ref` chokepoint. The writer never writes outside that partition and never copies raw subprocess output.

Reuse the `_DATE_PATTERN`, `resolve_instance_runtime_ref`, and unsafe-ref rule from `src/hisys/operations/codebase_analysis.py` and `src/hisys/operations/oss_comparison_adapter.py`. Mirror the writer convention shared by `change_impact.py`, `architecture_candidates.py`, `codebase_map_freshness.py`, `codebase_evidence_portfolio.py`, and `oss_comparison_adapter.py`. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, no `git log` execution, no CLI argument expansion in this RED-GREEN increment, no raw subprocess output archival beyond the truncated parsed report, no LSP server installation, and no `pip` install. A thin `hisys lsp-adapter` CLI wrapper is deferred to `M23-LSP-ADAPTER-CLI` after the pure runner is stable. A deterministic golden-fixture round-trip (against a checked-in canonical subprocess output blob, not against a live LSP run) is deferred to `M23-LSP-ADAPTER-GOLDEN`.

**Tech Stack:** Python 3.11 (`subprocess`, `hashlib.sha256`, `pathlib`, `re`), Pydantic v2, pytest. No new dependency. No LSP-protocol library, no language-server-protocol package install. The first GREEN run will use a fake/stubbed subprocess via `monkeypatch.setattr(subprocess, "run", fake_run)` or via a small caller-supplied bash script that emits canned JSON; the production-mode invocation against a real LSP-aware tool is human-gated to the operator running the CLI later.

**Context Packet:** Required source handles:

- `docs/plans/m23-advanced-codebase-adapter-integration-plan.md` (parent M23 plan; lists the LSP adapter as a pending row after OSS adapter closure).
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.21.md` (user authorization record for M23, including the local subprocess boundary stipulation).
- `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md`, `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md`, `docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md` (sibling PREP/CLI/GOLDEN shape; mirror caller-supplied input, no auto-discovery, advisory-only output, set-based bounded surface).
- `src/hisys/operations/oss_comparison_adapter.py` (label/date/unsafe-ref patterns reused; the LSP adapter does not import the OSS adapter types).
- `src/hisys/operations/codebase_analysis.py` (`resolve_instance_runtime_ref` chokepoint).
- `src/hisys/operations/change_impact.py`, `src/hisys/operations/architecture_candidates.py`, `src/hisys/operations/codebase_map_freshness.py` (sibling writer/report shapes for record consistency).
- `docs/traceability/README.md` (controlled traceability anchor; an `M23-LSP-ADAPTER-RED-GREEN` row is appended only in the implementation increment).
- `tests/unit/test_oss_comparison_adapter.py` (test layout pattern; mirror its `tmp_path` plus subprocess-mocking approach).
- `ralph.md` Section 16 + Reflection Log (PREP/RED/GREEN/GATE checkpoints).

**Boundary Record:** This Prepare packet performs only docs/control writes. Subsequent rows perform fixture-local test/code edits inside the M23 authorization boundary. **Not authorized** in any M23 LSP adapter increment without a separate human gate: network fetch, package installation (`pip install`), LSP server installation, live LSP protocol over a socket, credential lookup, secret capture, raw source archival, raw message text persistence in the report, environment inheritance beyond `PATH`, shell expansion (`shell=True`), command spawning outside the caller-supplied `command_allowlist`, subprocess execution outside the caller-supplied `workspace_root`, timeout > 120 seconds, output > 4 MiB, kill-policy violations (orphan processes), or publication / deployment / release. The adapter is advisory only and never claims compliance, fitness, or readiness for live action.

---

## Accepted decisions

1. **Caller-supplied allowlist only.** The adapter never has a built-in command list; the caller (test fixture or future CLI front-end) supplies `command_allowlist` explicitly. The runner refuses to spawn anything outside that allowlist.
2. **No shell, no environment inheritance.** `subprocess.run(argv, shell=False, env={"PATH": os.environ.get("PATH", "")})`. No `bash -c`, no string interpolation, no `os.environ` passthrough.
3. **Timeout enforced.** `timeout_seconds` is bounded at `_MAX_TIMEOUT_SECONDS=120`. The runner raises `subprocess.TimeoutExpired` internally, sets `subprocess_timed_out=true` in the report, and returns without re-raising — the caller decides what to do with a timeout.
4. **Output truncated.** stdout is truncated at `_MAX_OUTPUT_BYTES=4_194_304` (4 MiB) before parsing. `output_truncated=true` is recorded in the report if truncation happened. stderr is discarded except for the bounded exit-code summary (`subprocess_exit_code`).
5. **Workspace-root containment.** `workspace_root` must resolve to a directory that exists and contains all `target_refs` after `Path.resolve()`. Any `..` traversal or absolute path outside the host workspace is rejected. The runner does **not** chroot or sandbox the subprocess — that is a future row.
6. **Format-specific parsers.** The runner accepts exactly five `output_format` values: `pyright_json`, `mypy_json`, `ruff_json`, `flake8_json`, `eslint_json`. Each parser is a pure function `parse_<format>(raw: str) -> tuple[LspAdapterDiagnostic, ...]` that uses only `json.loads`. No `eval`, `exec`, `pickle`, `yaml.load`, or `xml.etree.ElementTree.fromstring`.
7. **No raw message text.** Diagnostics record the SHA-256 first-16-hex digest of the raw message, plus the category/severity/code/line/column refs. The raw text is never persisted to JSON or Markdown so secrets, proprietary source quotes, or PII cannot leak through diagnostic messages.
8. **No LSP server installation.** The PREP packet, the RED test, and the GREEN runner all explicitly forbid `pip install`, `npm install`, `apt-get install`, or any package manager call. The first GREEN test uses `monkeypatch` or a `tests/fixtures/lsp-adapter/<format>/fake-<tool>.sh` that emits canned JSON; production use is human-gated to the operator.
9. **Advisory only.** The report carries `advisory_only=true`, `requires_human_review=true`, `external_call_made=false` (a local LSP subprocess is **not** an external network call), `mutation_performed=false`, `raw_source_content_persisted=false`, `live_external_action_authorized=false`, and `allowed_actions="advisory_only"`. The report must not be treated as a compliance certificate or a build-pass claim.
10. **No CLI in this increment.** A `hisys lsp-adapter` subcommand is `M23-LSP-ADAPTER-CLI` work, planned separately. `M23-LSP-ADAPTER-RED-GREEN` ships only the pure module + parsers + writer; a golden fixture round-trip against a checked-in subprocess output blob comes in `M23-LSP-ADAPTER-GOLDEN`.
11. **Traceability required.** Update `docs/traceability/README.md` with an `M23-LSP-ADAPTER-RED-GREEN` row only in the implementation increment, and append a Reflection Log entry plus Resume checkpoint to `ralph.md` for every M23 LSP checkpoint.

---

## Task 0: Reconstruct baseline before any edit

**Objective:** Confirm the M23-OSS-ADAPTER-GATE closure is current, working tree is clean, and the M21/M22/M23/DARS focused gates remain green.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_domain_cli.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `0a172d3 docs: close m23 oss comparison adapter milestone`; combined M21+M22+M23 focused gate passes; DARS critic-panel focused regression passes; governance current-state test passes (v0.0.26, next_safe_task=M23-LSP-ADAPTER-PREP); traceability validator OK; secret scan `hit_count=0`; `git diff --check` clean.

---

## Task 1: RED — pure LSP adapter runner accepts a valid request and rejects an unsafe one

**Objective:** Add a failing pytest that constructs in-memory `LspAdapterRequest` records, monkey-patches `subprocess.run` to return canned ruff JSON output, calls `run_lsp_adapter`, and asserts the report aggregates diagnostics by severity/category. A second test confirms an `argv[0]` outside the allowlist is rejected with `ValueError("lsp_command_not_in_allowlist")` before any subprocess call.

**Files:**

- Create: `tests/unit/test_lsp_adapter.py`
- Create: `tests/fixtures/lsp-adapter/ruff/canned_ruff_output.json` (caller-supplied canned subprocess stdout payload pinning three diagnostics across two files; no real LSP run)

**Test sketch:**

```python
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


def test_run_lsp_adapter_aggregates_ruff_diagnostics(
    tmp_path: Path, monkeypatch
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    workspace_root = instance_root / "workspace"
    workspace_root.mkdir()
    (workspace_root / "src").mkdir()
    (workspace_root / "src" / "a.py").write_text("", encoding="utf-8")
    (workspace_root / "src" / "b.py").write_text("", encoding="utf-8")
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
        args=request.command.argv,
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
    # Confirm raw message text is NOT in any diagnostic
    for diag in report.diagnostics:
        assert len(diag.message_digest) == 16
        assert all(c in "0123456789abcdef" for c in diag.message_digest)
        # No raw message field exposed
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
    tmp_path: Path, monkeypatch
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    workspace_root = instance_root / "workspace"
    workspace_root.mkdir()
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
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py::test_run_lsp_adapter_aggregates_ruff_diagnostics -q
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.lsp_adapter'` because the module has not been created yet.

---

## Task 2: GREEN — implement minimal pure LSP adapter runner and parsers

**Objective:** Add the smallest production logic that satisfies the RED tests and the safety contract.

**Files:**

- Create: `src/hisys/operations/lsp_adapter.py`

**Module shape (illustrative; minor naming may evolve during GREEN):**

```python
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


def _validate_lsp_request(request: LspAdapterRequest) -> None: ...


def _digest_message(message: str) -> str: ...


def _parse_ruff_json(raw: str) -> tuple[LspAdapterDiagnostic, ...]: ...


def _parse_pyright_json(raw: str) -> tuple[LspAdapterDiagnostic, ...]: ...


def _parse_mypy_json(raw: str) -> tuple[LspAdapterDiagnostic, ...]: ...


def _parse_flake8_json(raw: str) -> tuple[LspAdapterDiagnostic, ...]: ...


def _parse_eslint_json(raw: str) -> tuple[LspAdapterDiagnostic, ...]: ...


def run_lsp_adapter(*, request: LspAdapterRequest) -> LspAdapterReport: ...


def write_lsp_adapter_report(
    *,
    instance_root: Path,
    date: str,
    report: LspAdapterReport,
) -> dict[str, object]: ...
```

**GREEN behavior contract:**

1. Reject `argv[0] not in command_allowlist` with `ValueError("lsp_command_not_in_allowlist")` **before any subprocess call**.
2. Reject `timeout_seconds > _MAX_TIMEOUT_SECONDS` or `<= 0` with `ValueError("lsp_timeout_out_of_range")`.
3. Reject `output_format not in _ALLOWED_OUTPUT_FORMATS` with `ValueError("lsp_output_format_not_allowed")`.
4. Reject any `argv` element containing a shell metacharacter from `_SHELL_METACHARACTERS` with `ValueError("lsp_argv_shell_metacharacter")`.
5. Reject empty `human_approval_ref` with `ValueError("lsp_human_approval_required")`.
6. Reject `target_refs` that fail the `_is_unsafe_ref` rule; collect them in `unsafe_refs` rather than raising (matches M22/M23 sibling pattern).
7. Reject `workspace_root` outside `instance_root` (after `Path.resolve()`) with `ValueError("lsp_workspace_root_outside_instance")`.
8. After validation, call `subprocess.run(list(command.argv), cwd=workspace_root, env={"PATH": os.environ.get("PATH", "")}, timeout=command.timeout_seconds, capture_output=True, check=False, shell=False)`. Catch `subprocess.TimeoutExpired` and return a report with `subprocess_timed_out=true`, `diagnostics=()`. Catch `FileNotFoundError` and raise `ValueError("lsp_command_not_found")`.
9. Truncate stdout to `_MAX_OUTPUT_BYTES`; set `output_truncated=true` if truncation happened.
10. Dispatch to the format-specific parser; normalize diagnostics through the unsafe-ref rule (paths outside `workspace_root` are recorded in `unsafe_refs`).
11. Aggregate severity counts and `category_ref_summary` (deduplicated sorted tuple of `category_ref` strings).
12. Return the `LspAdapterReport` without mutating any input record.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py -q
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py -q
```

**Expected GREEN:** focused LSP adapter tests pass; combined LSP + M22 portfolio + M23 OSS adapter sibling tests pass.

---

## Task 3: Supplemental regression — timeout, oversize output, output-format rejection, shell-metacharacter rejection, missing-approval rejection

**Objective:** Pin the safety invariants and confirm the runner enforces each rule from the safety contract independently.

**Files:**

- Modify: `tests/unit/test_lsp_adapter.py`

**Test cases (sketch):**

```python
def test_run_lsp_adapter_records_timeout(tmp_path, monkeypatch) -> None:
    # subprocess.run raises subprocess.TimeoutExpired; report records
    # subprocess_timed_out=true, diagnostics=().
    ...


def test_run_lsp_adapter_truncates_oversize_output(tmp_path, monkeypatch) -> None:
    # subprocess returns stdout > 4 MiB; report records output_truncated=true,
    # output_bytes=_MAX_OUTPUT_BYTES, and parses only the truncated prefix.
    ...


def test_run_lsp_adapter_rejects_output_format_outside_allowlist(
    tmp_path,
) -> None:
    # output_format="custom_xml" raises ValueError("lsp_output_format_not_allowed")
    # before any subprocess call.
    ...


def test_run_lsp_adapter_rejects_shell_metacharacter_in_argv(
    tmp_path,
) -> None:
    # argv=("ruff", "check", "$(rm -rf /)", "src/") raises
    # ValueError("lsp_argv_shell_metacharacter").
    ...


def test_run_lsp_adapter_rejects_missing_human_approval(tmp_path) -> None:
    # human_approval_ref="" raises ValueError("lsp_human_approval_required").
    ...


def test_run_lsp_adapter_rejects_workspace_root_outside_instance(
    tmp_path,
) -> None:
    # workspace_root="/etc" with instance_root=tmp_path raises
    # ValueError("lsp_workspace_root_outside_instance").
    ...


def test_run_lsp_adapter_converts_filenotfound_to_command_not_found(
    tmp_path, monkeypatch
) -> None:
    # subprocess.run raises FileNotFoundError; runner raises
    # ValueError("lsp_command_not_found") with no boundary record persisted.
    ...


def test_write_lsp_adapter_persists_safe_refs(tmp_path, monkeypatch) -> None:
    # writer round-trip: JSON and Markdown land under
    # runtime-boundary/lsp-adapter/<date>/<command_id>/lsp-report.{json,md}.
    # Markdown body contains no raw message text — only digests, codes, refs.
    ...


def test_write_lsp_adapter_rejects_bad_date(tmp_path) -> None:
    # date="2026-05-22" raises ValueError on the writer.
    ...
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py -q
```

**Expected:** all LSP adapter focused tests pass; no regression in M22/M23 OSS adapter tests.

---

## Task 4: Documentation, gate, and commit

**Objective:** Record M23-LSP-ADAPTER-RED-GREEN implementation evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M23-LSP-ADAPTER-RED-GREEN` row referencing the new module, fixture, tests, parent plan, the M23 authorization decision record, and the verified subprocess safety invariants (allowlist, timeout cap, workspace-root containment, no-shell, no-env-inherit-beyond-PATH, output truncation, no raw message persistence, no LSP server installation, no network).
- Modify: `ralph.md` — append a Reflection Log entry following the existing M22-PORTFOLIO format with Resume checkpoint and an updated Section 16 next-row pointer to `M23-LSP-ADAPTER-CLI` (or, if the user pauses, to `QUEUE-REFILL-PREP-STOP`).
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump to `v0.0.27` with `next_safe_task: M23-LSP-ADAPTER-RED-GREEN` (after this PREP commit), then bump again to `v0.0.28` after RED/GREEN. Mirror the update in `tests/unit/test_governance_docs_current_state.py`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN/regression and traceability update):**

```bash
git add tests/unit/test_lsp_adapter.py tests/fixtures/lsp-adapter/ src/hisys/operations/lsp_adapter.py docs/traceability/README.md ralph.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py
git commit -m "feat: add local lsp adapter"
```

---

## M23-LSP-ADAPTER-CLI deferral note

After `M23-LSP-ADAPTER-RED-GREEN` is committed and the focused gates remain green, the CLI wrapper follows the M23-OSS-ADAPTER-CLI pattern:

- Add `hisys lsp-adapter --instance <root> --date <YYYYMMDD> --request-bundle <json> [--current-head-short <hash>]` to `src/hisys/cli/main.py`. The bundle JSON contains `workspace_root`, `command` (object), `target_refs` (list), `command_allowlist` (list), and `human_approval_ref`.
- Reuse the existing `_load_json_report` helper. Build the request through `LspAdapterCommand` / `LspAdapterRequest` Pydantic models so the CLI does not duplicate the M23 shape.
- Print bounded summary lines: `lsp-adapter report`, `markdown`, `command_id`, `diagnostic_count`, `error_count`, `warning_count`, `info_count`, `subprocess_exit_code`, `subprocess_timed_out`, `subprocess_killed`, `output_truncated`, `output_bytes`, `unsafe_ref_count`, `advisory_only: true`, `requires_human_review: true`, `external_call_made: false`, `mutation_performed: false`, `raw_source_content_persisted: false`, `live_external_action_authorized: false`, `allowed_actions: advisory_only`.
- The CLI must not call `date.today()`, must not read `.git/`, must not crawl `tests/fixtures/`, must not auto-discover bundle files, must not install LSP servers, must not invoke `pip`/`npm`/`apt-get`, and must not expand the command-id or output-format vocabulary.

A full RED/GREEN plan for the CLI lives in a separate `docs/plans/m23-cli-lsp-adapter-implementation-tasks.md` authored only after the pure runner is committed.

## M23-LSP-ADAPTER-GOLDEN scope

After the CLI ships, add a deterministic golden-fixture test that pins one canonical canned subprocess output (e.g. `tests/fixtures/lsp-adapter/ruff/canned_ruff_output.json`), runs the pure runner with a monkey-patched `subprocess.run` returning that output, and compares its JSON/Markdown output against checked-in expected files under `tests/fixtures/lsp-adapter/expected/`. The golden fixture must not embed raw upstream source bodies, raw diagnostic messages, or any secret; it only pins severities, codes, line/column refs, message digests, and counts.

## M23-LSP-ADAPTER-GATE scope

After the golden fixture passes, append a `Done: M23-LSP-ADAPTER-GATE` line to `ralph.md` Section 16 with full focused/full gate evidence, run a QUEUE-REFILL-PREP preflight, and continue to `M23-ADAPTER-PORTFOLIO-INTEGRATION`.

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- network fetch, package installation (`pip`, `npm`, `apt-get`), LSP server installation, or any external HTTP call from the adapter, runner, writer, or CLI;
- credential lookup, mutation, or persistence;
- shelling out via `shell=True`, `os.system`, `subprocess.Popen(..., shell=True)`, or any string-interpolated command;
- environment inheritance beyond `PATH` (`os.environ` passthrough, `PYTHONPATH` injection, `LD_LIBRARY_PATH` modification);
- reading `.git/` directly or calling `date.today()` inside the runner;
- raw message text, raw source content, or raw subprocess output archival in the report;
- timeout > 120 seconds, output > 4 MiB, or any unbounded subprocess execution;
- spawning a long-lived daemon, opening a socket, speaking the LSP wire protocol, or holding a subprocess across multiple `run_lsp_adapter` calls;
- repair, deletion, retry, or quarantine of artifacts under inspection;
- expanding the report into approval / safe-to-deploy / compliance / build-pass language;
- adding the CLI in the `M23-LSP-ADAPTER-RED-GREEN` increment (CLI is `M23-LSP-ADAPTER-CLI`, planned separately after the pure runner stabilizes);
- mutating existing M21 / M22 / M23 OSS adapter / DARS schema shapes rather than referencing them by id;
- subagent execution, model invocation, or any live external provider call from this LSP adapter line.

## Out of scope for the LSP adapter (deferred or human-gated)

- LSP socket / wire protocol implementation (`textDocument/diagnostic`, `initialize`, `shutdown`, etc.). The adapter is one-shot CLI invocation only.
- Persistent daemon mode or watch mode; each `run_lsp_adapter` call is independent.
- Multi-language detection or automatic toolchain selection; the caller picks the exact `argv`.
- Symbol-level or function-level cross-reference; diagnostics are the only output surface.
- Auto-fix / quick-fix application; the report is advisory only.
- License detection or compliance verdicts.
- Live LSP server installation (deferred — operator installs `ruff` / `pyright` / `mypy` separately and runs the CLI with the correct allowlist).
- Cross-branch comparison, base-branch fetch, or `origin/main` resolution.

## Next executable action

After this Prepare plan is committed and pushed (normal push to existing `origin/dars`), run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py::test_run_lsp_adapter_aggregates_ruff_diagnostics -q
```

Expected failure: `ModuleNotFoundError: No module named 'hisys.operations.lsp_adapter'`.
