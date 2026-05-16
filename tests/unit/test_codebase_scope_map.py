"""RED/GREEN tests for the codebase scope-and-validation map (M17.1..M17.4).

The scope map is the third increment of `SPEC-HISYS-CODEBASE-ANALYSIS-001`. It
turns the deterministic codebase inventory and Python symbol index into a
human-reviewable map of named scopes (such as `domain-adapter`,
`runtime-boundary`, and `docs-traceability`) and a deterministic validation
plan for each scope.

M17.1 introduces the static scope-profile registry: pure data that names each
scope, the entry files it covers, the focused tests that govern it, and the
controlled docs that describe it. The registry itself performs no source
content reads, no live action, and no mutation — it only declares the
contract that later M17 increments consume.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from hisys.operations.codebase_analysis import (
    CodebaseScopeProfile,
    get_codebase_scope_profile,
    list_codebase_scope_profiles,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


KNOWN_SCOPE_IDS: tuple[str, ...] = (
    "docs-traceability",
    "domain-adapter",
    "runtime-boundary",
)


def test_scope_profile_is_pydantic_with_safety_invariants():
    profile = CodebaseScopeProfile(scope_id="example", description="example")
    assert isinstance(profile, BaseModel)
    assert profile.schema_id == "hisys.codebase.scope_profile"
    assert profile.scope_id == "example"
    assert profile.description == "example"
    assert profile.entry_files == []
    assert profile.expected_tests == []
    assert profile.docs_refs == []


def test_list_codebase_scope_profiles_returns_known_scopes_in_sorted_order():
    profiles = list_codebase_scope_profiles()
    scope_ids = [profile.scope_id for profile in profiles]

    # Determinism: the registry returns the known scopes in a stable
    # alphabetical order so downstream artifact writers and review summaries
    # can rely on it without re-sorting.
    assert scope_ids == sorted(scope_ids)
    assert scope_ids == list(KNOWN_SCOPE_IDS)


def test_list_codebase_scope_profiles_is_deterministic():
    once = list_codebase_scope_profiles()
    twice = list_codebase_scope_profiles()

    assert [p.model_dump() for p in once] == [p.model_dump() for p in twice]


def test_list_codebase_scope_profiles_returns_independent_copies():
    profiles_a = list_codebase_scope_profiles()
    profiles_a[0].entry_files.append("scratch/should-not-leak.py")

    profiles_b = list_codebase_scope_profiles()
    for profile in profiles_b:
        assert "scratch/should-not-leak.py" not in profile.entry_files


def test_domain_adapter_profile_covers_registry_and_three_layer_use_cases():
    profile = get_codebase_scope_profile("domain-adapter")

    assert profile.scope_id == "domain-adapter"
    assert profile.description
    assert "src/hisys/domain/adapters.py" in profile.entry_files
    assert "src/hisys/domain/specs.py" in profile.entry_files
    assert "src/hisys/domain/use_cases.py" in profile.entry_files
    assert "tests/unit/test_domain_adapter_registry.py" in profile.expected_tests
    assert (
        "tests/unit/test_domain_three_layer_use_cases.py" in profile.expected_tests
    )
    assert "tests/unit/test_domain_bridge_contract.py" in profile.expected_tests
    assert "docs/traceability/README.md" in profile.docs_refs


def test_runtime_boundary_profile_covers_codebase_analysis_writer_surface():
    profile = get_codebase_scope_profile("runtime-boundary")

    assert profile.scope_id == "runtime-boundary"
    assert profile.description
    assert "src/hisys/operations/codebase_analysis.py" in profile.entry_files
    assert "src/hisys/audit/writer.py" in profile.entry_files
    assert "tests/unit/test_codebase_analysis_inventory.py" in profile.expected_tests
    assert "tests/unit/test_codebase_symbol_index.py" in profile.expected_tests
    assert "tests/unit/test_domain_runtime_artifacts.py" in profile.expected_tests
    assert "docs/public/codebase-analysis.md" in profile.docs_refs


def test_docs_traceability_profile_covers_validation_script_and_readme():
    profile = get_codebase_scope_profile("docs-traceability")

    assert profile.scope_id == "docs-traceability"
    assert profile.description
    assert "scripts/validate_traceability.py" in profile.entry_files
    assert "docs/traceability/README.md" in profile.docs_refs


def test_get_codebase_scope_profile_rejects_unknown_scope_id():
    with pytest.raises(KeyError):
        get_codebase_scope_profile("not-a-real-scope")


def test_get_codebase_scope_profile_returns_independent_copy():
    profile = get_codebase_scope_profile("domain-adapter")
    profile.entry_files.append("scratch/should-not-leak.py")

    again = get_codebase_scope_profile("domain-adapter")
    assert "scratch/should-not-leak.py" not in again.entry_files


def test_scope_profile_refs_use_repo_relative_posix_paths():
    profiles = list_codebase_scope_profiles()
    for profile in profiles:
        for ref in (*profile.entry_files, *profile.expected_tests, *profile.docs_refs):
            assert not ref.startswith("/"), (
                f"{profile.scope_id} ref {ref!r} must be relative to the repo root"
            )
            assert "\\" not in ref, (
                f"{profile.scope_id} ref {ref!r} must use POSIX separators"
            )
            assert ".." not in ref.split("/"), (
                f"{profile.scope_id} ref {ref!r} must not contain traversal segments"
            )


def test_scope_profile_refs_resolve_under_repo_root():
    # The registry is a static contract; every declared ref must exist in the
    # current repository so the M17.2 scope-map builder and the M17.5 docs
    # examples never link to a missing file.
    profiles = list_codebase_scope_profiles()
    for profile in profiles:
        for ref in (*profile.entry_files, *profile.expected_tests, *profile.docs_refs):
            absolute = REPO_ROOT / ref
            assert absolute.is_file(), (
                f"{profile.scope_id} declares {ref!r} but {absolute} does not exist"
            )


def test_scope_profile_entries_are_sorted_and_unique():
    profiles = list_codebase_scope_profiles()
    for profile in profiles:
        for label, values in (
            ("entry_files", profile.entry_files),
            ("expected_tests", profile.expected_tests),
            ("docs_refs", profile.docs_refs),
        ):
            assert values == sorted(values), (
                f"{profile.scope_id}.{label} must be sorted for determinism"
            )
            assert len(values) == len(set(values)), (
                f"{profile.scope_id}.{label} must not contain duplicate refs"
            )
