"""Hisys CLI runtime entry points.

Traceability: HISYS-PKG-ARCH-001 Section 3, HISYS-RUNTIME-DIR-001,
HISYS-INST-INV-001, HISYS-D-015, HISYS-D-016, HISYS-T-001,
HISYS-T-007, HISYS-T-008.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .. import __version__
from ..adapters import AgentSystemMockSource, HardwareMockSource, HermesToolMockSource, WebNewsMockSource
from ..adapters.hermes_tool_mock import HermesCollectionInputs
from ..config import InstanceRoot, load_source_registry
from ..investigator import CollectionReport, InvestigatorRuntime
from ..registry import SourceRegistry
from ..schemas import SourceRegistryEntry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hisys", description="Hisys runtime CLI.")
    parser.add_argument("--version", action="version", version=f"hisys {__version__}")
    sub = parser.add_subparsers(dest="command")

    validate = sub.add_parser("validate-config", help="validate a Hisys runtime instance config")
    validate.add_argument("--instance", required=True, help="runtime instance root containing config/")

    collect = sub.add_parser("collect", help="run fixture-backed Investigator collection")
    collect.add_argument("--instance", required=True, help="runtime instance root for outputs")
    collect.add_argument(
        "--config-from",
        help="optional runtime instance root to read config from; outputs still go to --instance",
    )
    collect.add_argument(
        "--source",
        dest="sources",
        action="append",
        required=True,
        help="source_id to collect; repeat for multiple sources",
    )
    collect.add_argument("--date", required=True, help="YYYYMMDD output partition")
    collect.add_argument("--collector-id", default="investigator-cli", help="collector actor id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "validate-config":
        return _cmd_validate_config(Path(args.instance))
    if args.command == "collect":
        config_root = Path(args.config_from) if args.config_from else Path(args.instance)
        return _cmd_collect(
            output_root=Path(args.instance),
            config_root=config_root,
            source_ids=args.sources,
            yyyymmdd=args.date,
            collector_id=args.collector_id,
        )
    parser.error(f"unknown command: {args.command}")
    return 2


def _cmd_validate_config(instance_root: Path) -> int:
    registry = load_source_registry(InstanceRoot(instance_root))
    source_ids = sorted(registry.entries)
    print(f"config valid: {instance_root}")
    print(f"sources: {len(source_ids)}")
    for source_id in source_ids:
        entry = registry.entries[source_id]
        print(f"- {source_id} [{entry.source_type}] {entry.lifecycle_state}")
    return 0


def _cmd_collect(
    *,
    output_root: Path,
    config_root: Path,
    source_ids: list[str],
    yyyymmdd: str,
    collector_id: str,
) -> int:
    registry = load_source_registry(InstanceRoot(config_root))
    runtime = InvestigatorRuntime(
        registry=registry,
        adapters=_build_fixture_adapters(registry, source_ids),
        instance=InstanceRoot(output_root),
        collector_id=collector_id,
    )
    report = runtime.collect_run(source_ids, yyyymmdd=yyyymmdd)
    report_path = _write_collection_report(InstanceRoot(output_root), report, yyyymmdd)
    print(f"collection run {report.collection_run_id}: report={report_path}")
    print(f"collected: {len(report.collected_observation_refs)}")
    print(f"skipped: {len(report.skipped_source_ids)}")
    if not report.collected_observation_refs:
        print("no observations collected", file=sys.stderr)
        return 1
    return 0


def _build_fixture_adapters(
    registry: SourceRegistry,
    requested_source_ids: Iterable[str],
) -> dict[str, object]:
    adapters: dict[str, object] = {}
    for source_id in requested_source_ids:
        entry = registry.entries.get(source_id)
        if entry is None:
            continue
        adapters[source_id] = _adapter_for_entry(entry)
    return adapters


def _adapter_for_entry(entry: SourceRegistryEntry) -> object:
    if entry.source_type == "hardware_sensor":
        return HardwareMockSource(
            entry,
            payload={"temperature_c": 92.4, "unit": "C", "fixture": "cli-runtime"},
            device_identity="cli-mock-device",
        )
    if entry.source_type == "web_news":
        return WebNewsMockSource(
            entry,
            payload={"title": "Fixture RSS item", "summary": "Controlled fixture item."},
            citation_url="https://example.test/feed/item-001",
            citation_title="Fixture RSS item",
        )
    if entry.source_type == "agent_system":
        return AgentSystemMockSource(
            entry,
            payload={"critique": "Fixture advisory critique."},
            agent_identity="cli-agent-fixture",
        )
    if entry.source_type == "hermes_tool":
        return HermesToolMockSource(
            entry,
            payload={"finding": "Fixture Hermes collection output."},
            inputs=_hermes_inputs(entry),
        )
    raise ValueError(f"unsupported source_type for fixture adapter: {entry.source_type}")


def _hermes_inputs(entry: SourceRegistryEntry) -> HermesCollectionInputs:
    campaign_id = "CAMP-HERMES-CLI-001"
    prefix = f"hisys/runtime-boundary/hermes/20260508/{campaign_id}"
    return HermesCollectionInputs(
        campaign_id=campaign_id,
        hermes_parent_run_id="run-cli-parent-001",
        user_input_ref=f"{prefix}/user_input-001.md",
        prompt_or_query_ref=f"{prefix}/prompt-001.md",
        tool_output_ref=f"{prefix}/tool_output-001.md",
        boundary_record_ref=f"{prefix}/tool_output-HERMES-CLI-001.md",
        working_directory="examples/instance",
        scope_policy_ref=entry.scope_policy_ref or "HERMES-SCOPE-001",
        approval_state="preapproved",
        tool_invocation_id="tool-cli-001",
        tool_name="mock_search",
        enabled_toolsets=("read_only_search",),
        delegated_task_id="task-cli-001",
        delegated_subagent_preapproval_ref=(
            entry.delegated_subagent_preapproval_ref or "HERMES-PREAPPROVAL-001"
        ),
        source_scope="approved_fixture_sources",
    )


def _write_collection_report(instance: InstanceRoot, report: CollectionReport, yyyymmdd: str) -> Path:
    directory = instance.root / "reports" / "run-summaries" / yyyymmdd
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "collection-report.json"
    data = asdict(report)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path = directory / "collection-report.md"
    markdown_path.write_text(_format_report_markdown(report), encoding="utf-8")
    return json_path


def _format_report_markdown(report: CollectionReport) -> str:
    return "\n".join(
        [
            "# Hisys Collection Report",
            "",
            f"- collection_run_id: `{report.collection_run_id}`",
            f"- requested_source_ids: {', '.join(report.requested_source_ids)}",
            f"- collected_observations: {len(report.collected_observation_refs)}",
            f"- skipped_sources: {len(report.skipped_source_ids)}",
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
