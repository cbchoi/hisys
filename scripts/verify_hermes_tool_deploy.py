#!/usr/bin/env python3
"""Verify a Hisys Hermes tool deployment snapshot.

This script is intentionally local and side-effect free. It validates that the
Hermes-side Hisys wrapper executes an immutable deployment snapshot instead of a
live development checkout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool-root", required=True, type=Path)
    parser.add_argument("--upstream-source-root", required=True, type=Path)
    parser.add_argument("--expect-source-commit", required=True)
    args = parser.parse_args(argv)

    failures = _verify(
        tool_root=args.tool_root.expanduser().resolve(),
        upstream_source_root=args.upstream_source_root.expanduser().resolve(),
        expect_source_commit=args.expect_source_commit,
    )
    if failures:
        for failure in failures:
            print(f"deployment verification failed: {failure}")
        return 2
    print("deployment verification: ok")
    return 0


def _verify(*, tool_root: Path, upstream_source_root: Path, expect_source_commit: str) -> list[str]:
    failures: list[str] = []
    manifest_path = tool_root / "manifest.json"
    wrapper_path = tool_root / "bin" / "hisys"
    runtime_config_path = tool_root / "config" / "runtime.json"
    releases_root = tool_root / "releases"
    current_link = releases_root / "current"

    if not manifest_path.exists():
        return [f"manifest.json missing: {manifest_path}"]
    if not wrapper_path.exists():
        failures.append(f"wrapper missing: {wrapper_path}")
    if not current_link.exists():
        failures.append(f"current release link missing: {current_link}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"manifest is not valid JSON: {exc}"]

    failures.extend(_verify_manifest(
        manifest=manifest,
        tool_root=tool_root,
        upstream_source_root=upstream_source_root,
        expect_source_commit=expect_source_commit,
    ))
    failures.extend(_verify_wrapper(
        wrapper_path=wrapper_path,
        tool_root=tool_root,
        upstream_source_root=upstream_source_root,
    ))
    failures.extend(_verify_runtime_config(
        runtime_config_path=runtime_config_path,
        tool_root=tool_root,
        upstream_source_root=upstream_source_root,
    ))
    failures.extend(_verify_release_layout(
        manifest=manifest,
        tool_root=tool_root,
        current_link=current_link,
    ))
    return failures


def _verify_manifest(
    *,
    manifest: dict[str, Any],
    tool_root: Path,
    upstream_source_root: Path,
    expect_source_commit: str,
) -> list[str]:
    failures: list[str] = []
    expected_source_root = tool_root / "releases" / "current" / "source"
    expected = {
        "schema_id": "hisys.hermes_tool_deployment",
        "schema_version": "0.1.0",
        "tool_name": "hisys",
        "deployment_mode": "immutable_snapshot",
        "source_root": str(expected_source_root),
        "upstream_source_root": str(upstream_source_root),
        "target_root": str(tool_root),
        "wrapper": str(tool_root / "bin" / "hisys"),
        "runtime_config": str(tool_root / "config" / "runtime.json"),
        "runtime_root": str(tool_root / "runtime"),
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            failures.append(f"manifest {key!r} expected {value!r}, got {manifest.get(key)!r}")
    if manifest.get("source_commit") != expect_source_commit:
        failures.append(
            f"manifest source_commit expected {expect_source_commit!r}, got {manifest.get('source_commit')!r}"
        )
    release_id = manifest.get("release_id")
    if not isinstance(release_id, str) or not release_id:
        failures.append("manifest release_id missing")
    safety = manifest.get("safety_boundary")
    if not isinstance(safety, dict):
        failures.append("manifest safety_boundary missing")
    else:
        for key in (
            "cli_first",
            "read_only_browser_default",
            "human_approval_required_for_consequential_use",
        ):
            if safety.get(key) is not True:
                failures.append(f"manifest safety_boundary.{key} must be true")
        for key in ("mutation_performed", "publication_or_live_action_approved"):
            if safety.get(key) is not False:
                failures.append(f"manifest safety_boundary.{key} must be false")
    return failures


def _verify_wrapper(*, wrapper_path: Path, tool_root: Path, upstream_source_root: Path) -> list[str]:
    if not wrapper_path.exists():
        return []
    text = wrapper_path.read_text(encoding="utf-8")
    failures: list[str] = []
    if str(upstream_source_root) in text:
        failures.append("wrapper references live upstream source checkout")
    expected_source = str(tool_root / "releases" / "current" / "source")
    if expected_source not in text and "HISYS_RUNTIME_CONFIG" not in text:
        failures.append("wrapper does not reference releases/current/source snapshot or runtime config")
    if "HISYS_RUNTIME_CONFIG" not in text:
        match = re.search(r"^HISYS_SOURCE_ROOT=(['\"]?)(.+?)\1$", text, re.MULTILINE)
        if not match:
            failures.append("wrapper HISYS_SOURCE_ROOT assignment or HISYS_RUNTIME_CONFIG missing")
    return failures


def _verify_runtime_config(*, runtime_config_path: Path, tool_root: Path, upstream_source_root: Path) -> list[str]:
    failures: list[str] = []
    if not runtime_config_path.exists():
        return [f"runtime config missing: {runtime_config_path}"]
    try:
        config = json.loads(runtime_config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"runtime config is not valid JSON: {exc}"]
    expected_source = str(tool_root / "releases" / "current" / "source")
    expected = {
        "schema_id": "hisys.hermes_tool_runtime_config",
        "schema_version": "0.1.0",
        "tool_name": "hisys",
        "execution_mode": "installed_snapshot",
        "source_root": expected_source,
        "runtime_root": str(tool_root / "runtime"),
        "manifest": str(tool_root / "manifest.json"),
        "deployment_root": str(tool_root),
    }
    for key, value in expected.items():
        if config.get(key) != value:
            failures.append(f"runtime config {key!r} expected {value!r}, got {config.get(key)!r}")
    if str(upstream_source_root) in json.dumps(config, ensure_ascii=False):
        failures.append("runtime config references live upstream source checkout")
    policy = config.get("source_root_policy")
    if not isinstance(policy, dict):
        failures.append("runtime config source_root_policy missing")
    else:
        if policy.get("required_path_suffix") != "releases/current/source":
            failures.append("runtime config must require releases/current/source")
        for key in ("allow_live_source_checkout", "allow_upstream_source_root"):
            if policy.get(key) is not False:
                failures.append(f"runtime config source_root_policy.{key} must be false")
        if policy.get("fail_closed_on_config_error") is not True:
            failures.append("runtime config source_root_policy.fail_closed_on_config_error must be true")
    return failures


def _verify_release_layout(*, manifest: dict[str, Any], tool_root: Path, current_link: Path) -> list[str]:
    failures: list[str] = []
    source_root = tool_root / "releases" / "current" / "source"
    if not source_root.exists():
        failures.append(f"deployed source snapshot missing: {source_root}")
    if not (source_root / "src" / "hisys").exists():
        failures.append(f"deployed source package missing: {source_root / 'src' / 'hisys'}")
    release_id = manifest.get("release_id")
    if isinstance(release_id, str) and release_id:
        expected_release = tool_root / "releases" / release_id
        if not expected_release.exists():
            failures.append(f"manifest release_id directory missing: {expected_release}")
        if current_link.is_symlink() and current_link.readlink() != Path(release_id):
            failures.append(
                f"current link expected {release_id!r}, got {str(current_link.readlink())!r}"
            )
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
