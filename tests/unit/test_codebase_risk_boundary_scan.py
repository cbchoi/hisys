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

from pathlib import Path

import pytest

from hisys.operations.codebase_analysis import (
    CodebaseRiskScan,
    RiskBoundaryFinding,
    SymbolParseError,
    scan_codebase_risk_boundaries,
)


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
            "subprocess_execution",
        }
