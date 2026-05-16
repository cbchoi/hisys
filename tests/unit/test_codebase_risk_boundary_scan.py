"""RED/GREEN tests for the codebase risk-boundary scanner (M18.1..M18.4).

The risk-boundary scanner is the fourth increment of
`SPEC-HISYS-CODEBASE-ANALYSIS-001`. It conservatively flags AST call sites
that look like they cross sensitive boundaries — network calls, browser
calls, filesystem mutation, subprocess execution — without making any live
call itself. Findings are review evidence, not vulnerability verdicts:
each finding records `action_authorized=false`, and the top-level scan
record carries `action_authorized=false` and
`raw_source_content_persisted=false`.

M18.1 covers `requests.get`/`requests.<verb>`, `httpx.<verb>`, browser
calls (`webbrowser.open`), `Path.write_text` (and any `.write_text` call),
and `subprocess.<runner>`. M18.2..M18.5 add runtime-boundary write
separation, model/LLM and ByeSys categories, the writer/CLI, and docs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hisys.operations.codebase_analysis import (
    CodebaseRiskScan,
    RiskBoundaryFinding,
    SymbolParseError,
    scan_codebase_risk_boundaries,
    write_codebase_risk_scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _seed_risk_fixture(repo: Path) -> None:
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pkg" / "network.py").write_text(
        "import requests\n"
        "import httpx\n"
        "\n"
        "def fetch():\n"
        "    response = requests.get('https://example.com')\n"
        "    requests.post('https://example.com', json={'k': 1})\n"
        "    httpx.get('https://example.com')\n"
        "    return response\n",
        encoding="utf-8",
    )
    (repo / "pkg" / "browser.py").write_text(
        "import webbrowser\n"
        "\n"
        "def open_docs():\n"
        "    webbrowser.open('https://docs.example.com')\n",
        encoding="utf-8",
    )
    (repo / "pkg" / "mutation.py").write_text(
        "from pathlib import Path\n"
        "\n"
        "def persist(target: Path):\n"
        "    target.write_text('hello', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (repo / "pkg" / "exec.py").write_text(
        "import subprocess\n"
        "\n"
        "def run_thing():\n"
        "    subprocess.run(['ls', '-l'], check=True)\n"
        "    subprocess.Popen(['echo', 'hi'])\n",
        encoding="utf-8",
    )
    # Non-Python file that the scanner must ignore.
    (repo / "README.md").write_text("# fixture\n", encoding="utf-8")


def _by_category(findings: list[RiskBoundaryFinding]) -> dict[str, list[RiskBoundaryFinding]]:
    grouped: dict[str, list[RiskBoundaryFinding]] = {}
    for finding in findings:
        grouped.setdefault(finding.category, []).append(finding)
    return grouped


def test_scan_records_safety_invariants_on_top_level_record(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    assert isinstance(scan, CodebaseRiskScan)
    assert scan.schema_id == "hisys.codebase.risk_scan"
    assert scan.repo_root == str(repo)
    assert scan.raw_source_content_persisted is False
    assert scan.action_authorized is False
    assert scan.finding_count == len(scan.findings)
    assert scan.finding_count > 0


def test_scan_flags_requests_and_httpx_as_network_external_call(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    network = [f for f in scan.findings if f.category == "network_external_call"]
    signals = {(f.path, f.signal) for f in network}
    assert ("pkg/network.py", "requests.get") in signals
    assert ("pkg/network.py", "requests.post") in signals
    assert ("pkg/network.py", "httpx.get") in signals

    for finding in network:
        assert finding.line >= 1
        assert finding.action_authorized is False


def test_scan_flags_webbrowser_open_as_browser_external_call(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    browser = [f for f in scan.findings if f.category == "browser_external_call"]
    signals = {(f.path, f.signal) for f in browser}
    assert ("pkg/browser.py", "webbrowser.open") in signals


def test_scan_flags_write_text_as_filesystem_mutation(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    fs = [f for f in scan.findings if f.category == "filesystem_mutation"]
    signals = {(f.path, f.signal) for f in fs}
    assert ("pkg/mutation.py", "<receiver>.write_text") in signals


def test_scan_flags_subprocess_calls_as_subprocess_execution(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    sub = [f for f in scan.findings if f.category == "subprocess_execution"]
    signals = {(f.path, f.signal) for f in sub}
    assert ("pkg/exec.py", "subprocess.run") in signals
    assert ("pkg/exec.py", "subprocess.Popen") in signals


def test_scan_category_counts_match_grouped_findings(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    grouped = _by_category(scan.findings)
    expected_counts = {key: len(values) for key, values in grouped.items()}
    assert dict(scan.category_counts) == expected_counts


def test_scan_is_deterministic_for_same_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    once = scan_codebase_risk_boundaries(repo_root=repo)
    twice = scan_codebase_risk_boundaries(repo_root=repo)
    assert once.model_dump() == twice.model_dump()


def test_scan_orders_findings_deterministically(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    keys = [(f.path, f.line, f.category, f.signal) for f in scan.findings]
    assert keys == sorted(keys)


def test_scan_skips_non_python_files(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("import requests\nrequests.get('https://x')\n", encoding="utf-8")
    (repo / "b.txt").write_text("requests.get('https://x')\n", encoding="utf-8")
    (repo / "c.md").write_text("requests.get('https://x')\n", encoding="utf-8")

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    paths = {finding.path for finding in scan.findings}
    assert paths == {"a.py"}


def test_scan_records_parse_errors_without_failing(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "good.py").write_text(
        "import requests\nrequests.get('https://x')\n", encoding="utf-8"
    )
    (repo / "bad.py").write_text("def broken(:\n    return 0\n", encoding="utf-8")

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    paths = {finding.path for finding in scan.findings}
    assert "good.py" in paths
    assert "bad.py" not in paths

    assert scan.parse_error_count == 1
    assert len(scan.parse_errors) == 1
    err = scan.parse_errors[0]
    assert isinstance(err, SymbolParseError)
    assert err.path == "bad.py"


def test_scan_supports_analysis_scope_filter(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "kept.py").write_text(
        "import requests\nrequests.get('https://x')\n", encoding="utf-8"
    )
    (repo / "tests").mkdir()
    (repo / "tests" / "ignored.py").write_text(
        "import requests\nrequests.get('https://y')\n", encoding="utf-8"
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo, analysis_scope="src")

    assert scan.analysis_scope == "src"
    paths = {finding.path for finding in scan.findings}
    assert paths == {"src/kept.py"}


def test_scan_finding_carries_argv_or_pattern_string(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)

    scan = scan_codebase_risk_boundaries(repo_root=repo)

    for finding in scan.findings:
        assert isinstance(finding, RiskBoundaryFinding)
        assert finding.signal, "signal must be a non-empty descriptor"
        assert finding.category in {
            "network_external_call",
            "browser_external_call",
            "filesystem_mutation",
            "runtime_boundary_artifact_write",
            "subprocess_execution",
        }


# ---------------------------------------------------------------------------
# M18.2 — runtime-boundary writer fixture vs ordinary filesystem mutation
# ---------------------------------------------------------------------------


def test_scan_classifies_runtime_boundary_writer_separately(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "writer.py").write_text(
        "from pathlib import Path\n"
        "\n"
        "INVENTORY_RUNTIME_PREFIX = 'runtime-boundary/codebase-analysis'\n"
        "\n"
        "def write_artifact(instance_root: Path, date: str, request_id: str) -> None:\n"
        "    rel_dir = f'{INVENTORY_RUNTIME_PREFIX}/{date}/{request_id}'\n"
        "    out_dir = Path(instance_root) / rel_dir\n"
        "    out_dir.mkdir(parents=True, exist_ok=True)\n"
        "    (out_dir / 'artifact.json').write_text('{}', encoding='utf-8')\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "writer.py"]

    categories = {f.category for f in findings}
    assert "runtime_boundary_artifact_write" in categories
    # The same writer file must not also report `filesystem_mutation` for the
    # same `.write_text` line; the classification is exclusive per call site.
    rb = [f for f in findings if f.category == "runtime_boundary_artifact_write"]
    fs = [f for f in findings if f.category == "filesystem_mutation"]
    assert rb, "runtime_boundary_artifact_write category must surface"
    assert not fs, (
        f"runtime-boundary writer file must not also report filesystem_mutation; got {fs}"
    )

    for finding in rb:
        assert finding.action_authorized is False


def test_scan_keeps_ordinary_filesystem_mutation_classification(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "ordinary.py").write_text(
        "from pathlib import Path\n"
        "\n"
        "def persist(target: Path):\n"
        "    target.write_text('hello', encoding='utf-8')\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "ordinary.py"]

    categories = {f.category for f in findings}
    assert "filesystem_mutation" in categories
    assert "runtime_boundary_artifact_write" not in categories


def test_scan_runtime_boundary_classification_uses_string_literal_signal(tmp_path: Path):
    # Any string literal value that contains the controlled
    # `runtime-boundary` token in the same module is sufficient to
    # classify subsequent `.write_text` calls as a runtime-boundary
    # writer. This keeps the rule deterministic and AST-only.
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "indirect.py").write_text(
        "from pathlib import Path\n"
        "\n"
        "SCOPE_TOKEN = 'runtime-boundary/codebase-analysis'\n"
        "\n"
        "def write(target: Path):\n"
        "    target.write_text(SCOPE_TOKEN, encoding='utf-8')\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "indirect.py"]
    categories = {f.category for f in findings}
    assert "runtime_boundary_artifact_write" in categories
    assert "filesystem_mutation" not in categories


# ---------------------------------------------------------------------------
# M18.3 — model/LLM and ByeSys categories
# ---------------------------------------------------------------------------


def test_scan_flags_openai_calls_as_model_llm_boundary(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "llm.py").write_text(
        "import openai\n"
        "\n"
        "def ask():\n"
        "    return openai.ChatCompletion.create(model='gpt-4', messages=[])\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "llm.py"]
    categories = {f.category for f in findings}
    assert "model_llm_boundary" in categories


def test_scan_flags_anthropic_calls_as_model_llm_boundary(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "llm.py").write_text(
        "import anthropic\n"
        "\n"
        "def ask():\n"
        "    client = anthropic.Anthropic()\n"
        "    return client.messages.create(model='claude', messages=[])\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "llm.py"]
    categories = {f.category for f in findings}
    assert "model_llm_boundary" in categories


def test_scan_flags_local_model_endpoint_call_as_model_llm_boundary(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "local_llm.py").write_text(
        "import requests\n"
        "\n"
        "LOCAL_MODEL_ENDPOINT = 'http://localhost:8080/v1/chat/completions'\n"
        "\n"
        "def call_local_model():\n"
        "    return requests.post(LOCAL_MODEL_ENDPOINT, json={'model': 'local'})\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "local_llm.py"]
    categories = {f.category for f in findings}
    # Local model endpoint is still a model/LLM boundary, distinct from a
    # generic network call — the local LLM still crosses the model boundary.
    assert "model_llm_boundary" in categories


def test_scan_flags_byesys_marker_string_as_byesys_generated_evidence(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "synth.py").write_text(
        '"""Module that fabricates evidence — marked ByeSys."""\n'
        "\n"
        "def synthesize_evidence():\n"
        "    return {\n"
        "        'kind': 'byesys_generated',\n"
        "        'note': 'ByeSys: fabricated evidence pending human review',\n"
        "    }\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "synth.py"]
    categories = {f.category for f in findings}
    assert "byesys_generated_evidence" in categories
    for finding in findings:
        if finding.category == "byesys_generated_evidence":
            assert finding.action_authorized is False


def test_scan_byesys_finding_carries_module_level_signal(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "synth.py").write_text(
        "BYESYS_MARKER = 'ByeSys: see policy doc'\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    findings = [f for f in scan.findings if f.path == "synth.py"]
    byesys = [f for f in findings if f.category == "byesys_generated_evidence"]
    assert byesys, "expected a ByeSys generated-evidence finding"
    # The finding records the line of the marker so a reviewer can navigate.
    for finding in byesys:
        assert finding.line >= 1
        assert finding.signal


def test_scan_finding_categories_widened_for_model_and_byesys(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "llm.py").write_text(
        "import openai\n"
        "\n"
        "def ask():\n"
        "    return openai.ChatCompletion.create(model='gpt-4', messages=[])\n",
        encoding="utf-8",
    )
    (repo / "synth.py").write_text(
        "BYESYS_MARKER = 'ByeSys: fabricated'\n",
        encoding="utf-8",
    )

    scan = scan_codebase_risk_boundaries(repo_root=repo)
    for finding in scan.findings:
        assert finding.category in {
            "network_external_call",
            "browser_external_call",
            "filesystem_mutation",
            "runtime_boundary_artifact_write",
            "subprocess_execution",
            "model_llm_boundary",
            "byesys_generated_evidence",
        }


# ---------------------------------------------------------------------------
# M18.4 — writer and CLI (`scan-codebase-boundaries`)
# ---------------------------------------------------------------------------


def test_write_codebase_risk_scan_persists_json_and_markdown(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)
    scan = scan_codebase_risk_boundaries(repo_root=repo)

    instance = tmp_path / "instance"
    result = write_codebase_risk_scan(
        instance_root=instance,
        date="20260517",
        request_id="REQ-CODEBASE-RISK-001",
        scan=scan,
    )

    assert result["external_call_made"] is False
    assert result["mutation_performed"] is False
    assert result["publication_or_live_action_approved"] is False
    assert result["raw_source_content_persisted"] is False
    assert result["action_authorized"] is False
    assert result["schema_id"] == "hisys.codebase.risk_scan"
    assert result["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-RISK-001/risk-scan.json"
    )
    assert result["markdown_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-RISK-001/risk-scan.md"
    )

    json_path = instance / result["json_ref"]
    md_path = instance / result["markdown_ref"]
    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "hisys.codebase.risk_scan"
    assert payload["raw_source_content_persisted"] is False
    assert payload["action_authorized"] is False

    markdown = md_path.read_text(encoding="utf-8")
    assert "review evidence" in markdown.lower()
    assert "vulnerability" in markdown.lower()


def test_write_codebase_risk_scan_rejects_traversal_in_request_id(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_risk_fixture(repo)
    scan = scan_codebase_risk_boundaries(repo_root=repo)
    instance = tmp_path / "instance"

    for bad in ("../escape", "REQ/with/slash", ".."):
        with pytest.raises(ValueError):
            write_codebase_risk_scan(
                instance_root=instance,
                date="20260517",
                request_id=bad,
                scan=scan,
            )

    for bad_date in ("2026/05/17", "..", "20260517/extra"):
        with pytest.raises(ValueError):
            write_codebase_risk_scan(
                instance_root=instance,
                date=bad_date,
                request_id="REQ-CODEBASE-RISK-001",
                scan=scan,
            )


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
    return subprocess.run(
        [sys.executable, "-m", "hisys.cli.main", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_scan_codebase_boundaries_cli_writes_artifacts(tmp_path: Path):
    fixture_repo = tmp_path / "fixture_repo"
    fixture_repo.mkdir()
    _seed_risk_fixture(fixture_repo)
    instance = tmp_path / "instance"

    completed = _run_cli(
        "scan-codebase-boundaries",
        "--repo",
        str(fixture_repo),
        "--instance",
        str(instance),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-RISK-001",
        "--format",
        "json",
        cwd=REPO_ROOT,
    )

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.codebase.risk_scan"
    assert payload["external_call_made"] is False
    assert payload["action_authorized"] is False
    assert payload["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-RISK-001/risk-scan.json"
    )

    json_path = instance / payload["json_ref"]
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    categories = {finding["category"] for finding in loaded["findings"]}
    assert "network_external_call" in categories
    assert "subprocess_execution" in categories


def test_scan_codebase_boundaries_cli_supports_scope_filter(tmp_path: Path):
    fixture_repo = tmp_path / "fixture_repo"
    fixture_repo.mkdir()
    (fixture_repo / "src").mkdir()
    (fixture_repo / "src" / "kept.py").write_text(
        "import requests\nrequests.get('https://x')\n", encoding="utf-8"
    )
    (fixture_repo / "tests").mkdir()
    (fixture_repo / "tests" / "ignored.py").write_text(
        "import requests\nrequests.get('https://y')\n", encoding="utf-8"
    )
    instance = tmp_path / "instance"

    completed = _run_cli(
        "scan-codebase-boundaries",
        "--repo",
        str(fixture_repo),
        "--instance",
        str(instance),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-RISK-002",
        "--scope",
        "src",
        "--format",
        "json",
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    json_path = instance / payload["json_ref"]
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    paths = {finding["path"] for finding in loaded["findings"]}
    assert paths == {"src/kept.py"}
