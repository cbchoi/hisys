"""Deployment CI/CD workflow checks for Hisys Hermes tool deployment.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-hermes-tool.yml"
VERIFY_SCRIPT = ROOT / "scripts" / "verify_hermes_tool_deploy.py"


def test_deploy_workflow_runs_after_ci_and_uses_snapshot_verifier():
    assert WORKFLOW.exists(), "deploy-hermes-tool workflow must exist"
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    assert workflow["name"] == "Hisys Hermes Tool Deploy"
    assert workflow["on"]["workflow_run"]["workflows"] == ["Hisys CI"]
    assert workflow["on"]["workflow_run"]["types"] == ["completed"]
    assert workflow["concurrency"]["group"] == "hisys-hermes-tool-deploy"

    job = workflow["jobs"]["deploy-hermes-tool"]
    assert "github.event.workflow_run.conclusion == 'success'" in job["if"]
    assert job["permissions"]["contents"] == "read"
    assert job["permissions"]["actions"] == "read"
    assert job["permissions"]["id-token"] == "none"

    joined_steps = "\n".join(step.get("run", "") for step in job["steps"])
    assert "deploy-hermes-tool" in joined_steps
    assert "--target" in joined_steps
    assert "verify_hermes_tool_deploy.py" in joined_steps
    assert "git diff --check" in joined_steps
    assert "scripts/validate_traceability.py" in joined_steps
    assert "scripts/scan_secrets.py" in joined_steps


def test_verify_hermes_tool_deploy_rejects_live_source_wrapper(tmp_path):
    tool_root = tmp_path / "hisys"
    (tool_root / "bin").mkdir(parents=True)
    upstream = tmp_path / "repo"
    upstream.mkdir()
    wrapper = tool_root / "bin" / "hisys"
    wrapper.write_text(f"#!/usr/bin/env bash\nHISYS_SOURCE_ROOT='{upstream}'\n", encoding="utf-8")
    wrapper.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(VERIFY_SCRIPT),
            "--tool-root",
            str(tool_root),
            "--upstream-source-root",
            str(upstream),
            "--expect-source-commit",
            "abc123",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 2
    assert "manifest.json missing" in result.stdout or "live upstream source" in result.stdout


def test_verify_hermes_tool_deploy_accepts_snapshot_layout(tmp_path):
    tool_root = tmp_path / "hisys"
    release = tool_root / "releases" / "20260513T070327Z-abcdef123456"
    source = release / "source"
    (source / "src" / "hisys").mkdir(parents=True)
    (tool_root / "bin").mkdir(parents=True)
    (tool_root / "config").mkdir(parents=True)
    (tool_root / "runtime").mkdir(parents=True)
    (tool_root / "releases" / "current").symlink_to(release.name)
    wrapper = tool_root / "bin" / "hisys"
    wrapper.write_text(
        f"#!/usr/bin/env bash\nHISYS_SOURCE_ROOT='{tool_root / 'releases' / 'current' / 'source'}'\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    (tool_root / "manifest.json").write_text(
        """
{
  "schema_id": "hisys.hermes_tool_deployment",
  "schema_version": "0.1.0",
  "tool_name": "hisys",
  "deployment_mode": "immutable_snapshot",
  "release_id": "20260513T070327Z-abcdef123456",
  "source_commit": "abcdef1234567890",
  "source_root": "REPLACE_SOURCE",
  "upstream_source_root": "REPLACE_UPSTREAM",
  "target_root": "REPLACE_TARGET",
  "wrapper": "REPLACE_WRAPPER",
  "runtime_root": "REPLACE_RUNTIME",
  "public_browser_profile": "REPLACE_PROFILE",
  "safety_boundary": {
    "cli_first": true,
    "read_only_browser_default": true,
    "mutation_performed": false,
    "publication_or_live_action_approved": false,
    "human_approval_required_for_consequential_use": true
  }
}
""".replace("REPLACE_SOURCE", str(tool_root / "releases" / "current" / "source"))
        .replace("REPLACE_UPSTREAM", str(tmp_path / "repo"))
        .replace("REPLACE_TARGET", str(tool_root))
        .replace("REPLACE_WRAPPER", str(wrapper))
        .replace("REPLACE_RUNTIME", str(tool_root / "runtime"))
        .replace("REPLACE_PROFILE", str(tool_root / "config" / "public-browser.yaml")),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(VERIFY_SCRIPT),
            "--tool-root",
            str(tool_root),
            "--upstream-source-root",
            str(tmp_path / "repo"),
            "--expect-source-commit",
            "abcdef1234567890",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    assert "deployment verification: ok" in result.stdout
