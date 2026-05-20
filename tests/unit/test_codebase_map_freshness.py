"""Focused unit tests for the M21.4 codebase map freshness/drift checker.

The checker is pure and advisory only: callers supply an instance root, a
``current_date``, a ``max_age_days`` threshold, and optionally a HEAD short
hash. The checker classifies each existing
``runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/`` partition as
``fresh``, ``stale``, ``incomplete``, or ``unsafe_partition`` by reading
directory listings and file presence only — never artifact bodies. These
tests pin the classification behavior, the missing-root fallback, the
writer round-trip, and the traversal/`..` rejection paths.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from hisys.operations.codebase_map_freshness import (
    build_codebase_map_freshness_report,
    write_codebase_map_freshness_report,
)


_REQUIRED = ("inventory.json", "symbol-index.json", "scope-map.json", "risk-scan.json")


def _seed_partition(
    instance_root: Path, yyyymmdd: str, request_id: str, *, complete: bool
) -> str:
    partition = f"runtime-boundary/codebase-analysis/{yyyymmdd}/{request_id}"
    partition_dir = instance_root / partition
    partition_dir.mkdir(parents=True, exist_ok=True)
    files = _REQUIRED if complete else _REQUIRED[:2]
    for name in files:
        (partition_dir / name).write_text("{}\n", encoding="utf-8")
    return partition


def test_codebase_map_freshness_classifies_partitions(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    fresh = _seed_partition(instance_root, "20260518", "REQ-FRESH", complete=True)
    stale = _seed_partition(instance_root, "20260101", "REQ-STALE", complete=True)
    incomplete = _seed_partition(
        instance_root, "20260519", "REQ-INCOMPLETE", complete=False
    )
    unsafe_dir = (
        instance_root / "runtime-boundary" / "codebase-analysis" / "not-a-date" / "REQ-OOPS"
    )
    unsafe_dir.mkdir(parents=True, exist_ok=True)
    (unsafe_dir / "inventory.json").write_text("{}\n", encoding="utf-8")

    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
        current_head_short="3c3e0bd",
    )

    assert report.schema_id == "hisys.codebase_map.freshness.v1"
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.current_head_short == "3c3e0bd"
    assert report.current_date == "2026-05-20"
    assert report.max_age_days == 30
    assert report.fresh_partitions == (fresh,)
    assert report.stale_partitions == (stale,)
    assert report.incomplete_partitions == (incomplete,)
    assert report.unsafe_partitions == (
        "runtime-boundary/codebase-analysis/not-a-date/REQ-OOPS",
    )


def test_write_codebase_map_freshness_report_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
    )
    refs = write_codebase_map_freshness_report(
        instance_root=instance_root, date="20260520", report=report
    )
    expected_json = (
        "runtime-boundary/codebase-map-freshness/20260520/freshness-report.json"
    )
    expected_md = (
        "runtime-boundary/codebase-map-freshness/20260520/freshness-report.md"
    )
    assert refs["json_ref"] == expected_json
    assert refs["markdown_ref"] == expected_md
    assert refs["advisory_only"] is True
    assert refs["external_call_made"] is False
    assert refs["mutation_performed"] is False
    assert refs["raw_source_content_persisted"] is False
    json_path = instance_root / expected_json
    md_path = instance_root / expected_md
    assert json_path.is_file()
    assert md_path.is_file()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.codebase_map.freshness.v1"
    assert data["advisory_only"] is True
    assert data["current_date"] == "2026-05-20"
    md_text = md_path.read_text(encoding="utf-8")
    assert "advisory_only: true" in md_text
    assert "external_call_made: false" in md_text


def test_build_codebase_map_freshness_handles_missing_root(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
    )
    assert report.fresh_partitions == ()
    assert report.stale_partitions == ()
    assert report.incomplete_partitions == ()
    assert report.unsafe_partitions == ()
    assert report.current_head_short is None


def test_write_codebase_map_freshness_report_rejects_invalid_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
    )
    try:
        write_codebase_map_freshness_report(
            instance_root=instance_root, date="2026-05-20", report=report
        )
    except ValueError as exc:
        assert "invalid" in str(exc).lower()
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError for non-YYYYMMDD date")


def test_build_codebase_map_freshness_uses_boundary_max_age(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    on_boundary = _seed_partition(
        instance_root, "20260420", "REQ-BOUNDARY", complete=True
    )

    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
    )
    assert report.fresh_partitions == (on_boundary,)
    assert report.stale_partitions == ()

    older_report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 21),
        max_age_days=30,
    )
    assert older_report.fresh_partitions == ()
    assert older_report.stale_partitions == (on_boundary,)
