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
    CodebaseInventory,
    CodebaseScopeMap,
    CodebaseScopeMapEntry,
    CodebaseScopeProfile,
    PythonSymbolIndex,
    SymbolFunction,
    SymbolImport,
    SymbolModule,
    SymbolParseError,
    build_codebase_scope_map,
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


# ---------------------------------------------------------------------------
# M17.2 — scope-map builder
# ---------------------------------------------------------------------------


def _make_inventory(repo_root: str, files: list[str]) -> CodebaseInventory:
    sorted_files = sorted(files)
    return CodebaseInventory(
        repo_root=repo_root,
        repo_root_realpath=repo_root,
        analysis_scope=None,
        files=sorted_files,
        excluded_paths=[],
        skipped_paths=[],
        file_count=len(sorted_files),
        binary_file_count=0,
        large_file_count=0,
        generated_file_count=0,
        raw_source_content_persisted=False,
    )


def _make_symbol_module(path: str) -> SymbolModule:
    return SymbolModule(
        path=path,
        module_qualname=path.replace("/", ".").removesuffix(".py"),
        imports=[SymbolImport(module="os", name="os", asname=None, line=1)],
        functions=[
            SymbolFunction(
                name="alpha",
                line_start=1,
                line_end=2,
                is_async=False,
                parameters=[],
                tags=[],
            )
        ],
        classes=[],
    )


def _make_symbol_index(
    repo_root: str, module_paths: list[str], parse_errors: list[SymbolParseError] | None = None
) -> PythonSymbolIndex:
    modules = [_make_symbol_module(p) for p in sorted(module_paths)]
    function_total = sum(len(m.functions) for m in modules)
    import_total = sum(len(m.imports) for m in modules)
    errors = sorted(parse_errors or [], key=lambda err: err.path)
    return PythonSymbolIndex(
        repo_root=repo_root,
        analysis_scope=None,
        modules=modules,
        parse_errors=errors,
        module_count=len(modules),
        import_count=import_total,
        class_count=0,
        function_count=function_total,
        parse_error_count=len(errors),
        raw_source_content_persisted=False,
    )


def test_scope_map_uses_default_registry_when_no_profiles_given():
    repo = "/fake/repo"
    inventory = _make_inventory(
        repo,
        [
            "src/hisys/audit/writer.py",
            "src/hisys/domain/adapters.py",
            "src/hisys/domain/specs.py",
            "src/hisys/operations/codebase_analysis.py",
            "scripts/validate_traceability.py",
            "docs/traceability/README.md",
            "docs/public/codebase-analysis.md",
            "tests/unit/test_codebase_analysis_inventory.py",
            "tests/unit/test_codebase_symbol_index.py",
            "tests/unit/test_domain_runtime_artifacts.py",
            "tests/unit/test_domain_adapter_registry.py",
            "tests/unit/test_domain_bridge_contract.py",
            "tests/unit/test_domain_name_strategy.py",
            "tests/unit/test_domain_postprocessing_guard.py",
            "tests/unit/test_domain_three_layer_use_cases.py",
            "tests/unit/test_structured_domain_adapter.py",
        ],
    )
    symbol_index = _make_symbol_index(
        repo,
        [
            "src/hisys/audit/writer.py",
            "src/hisys/domain/adapters.py",
            "src/hisys/domain/specs.py",
            "src/hisys/operations/codebase_analysis.py",
        ],
    )

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index
    )

    assert isinstance(scope_map, CodebaseScopeMap)
    assert scope_map.schema_id == "hisys.codebase.scope_map"
    assert scope_map.raw_source_content_persisted is False
    assert scope_map.repo_root == repo
    assert scope_map.inventory_schema_id == "hisys.codebase.inventory"
    assert scope_map.symbol_index_schema_id == "hisys.codebase.symbol_index"

    scope_ids = [entry.scope_id for entry in scope_map.scope_entries]
    assert scope_ids == ["docs-traceability", "domain-adapter", "runtime-boundary"]


def test_scope_map_entry_partitions_inventory_into_present_and_missing():
    repo = "/fake/repo"
    inventory = _make_inventory(
        repo,
        [
            "src/hisys/domain/adapters.py",
            "src/hisys/domain/specs.py",
            "tests/unit/test_domain_adapter_registry.py",
            "tests/unit/test_domain_three_layer_use_cases.py",
            "docs/traceability/README.md",
        ],
    )
    symbol_index = _make_symbol_index(
        repo, ["src/hisys/domain/adapters.py", "src/hisys/domain/specs.py"]
    )

    profile = get_codebase_scope_profile("domain-adapter")
    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )

    assert len(scope_map.scope_entries) == 1
    entry = scope_map.scope_entries[0]
    assert isinstance(entry, CodebaseScopeMapEntry)
    assert entry.scope_id == "domain-adapter"
    assert entry.description == profile.description

    assert entry.files_in_scope == [
        "src/hisys/domain/adapters.py",
        "src/hisys/domain/specs.py",
    ]
    assert entry.missing_entry_files == [
        "src/hisys/domain/domain_adapters.py",
        "src/hisys/domain/layers.py",
        "src/hisys/domain/runtime.py",
        "src/hisys/domain/use_cases.py",
    ]

    assert entry.tests_in_scope == [
        "tests/unit/test_domain_adapter_registry.py",
        "tests/unit/test_domain_three_layer_use_cases.py",
    ]
    assert entry.missing_expected_tests == [
        "tests/unit/test_domain_bridge_contract.py",
        "tests/unit/test_domain_name_strategy.py",
        "tests/unit/test_domain_postprocessing_guard.py",
        "tests/unit/test_domain_runtime_artifacts.py",
        "tests/unit/test_structured_domain_adapter.py",
    ]

    assert entry.docs_in_scope == ["docs/traceability/README.md"]
    assert entry.missing_docs_refs == []
    assert entry.traceability_refs_in_scope == ["docs/traceability/README.md"]


def test_scope_map_filters_symbols_by_scope_entry_files():
    repo = "/fake/repo"
    domain_path = "src/hisys/domain/adapters.py"
    other_path = "src/hisys/operations/codebase_analysis.py"
    inventory = _make_inventory(repo, [domain_path, other_path])
    symbol_index = _make_symbol_index(repo, [domain_path, other_path])

    profile = CodebaseScopeProfile(
        scope_id="domain-only",
        description="only domain adapters",
        entry_files=[domain_path],
    )
    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )

    entry = scope_map.scope_entries[0]
    assert [mod.path for mod in entry.modules] == [domain_path]
    assert entry.module_count == 1
    assert entry.function_count == 1
    assert entry.class_count == 0
    assert entry.import_count == 1


def test_scope_map_records_parse_errors_only_for_scope_entries():
    repo = "/fake/repo"
    in_scope_bad = "src/hisys/domain/broken.py"
    out_of_scope_bad = "src/hisys/unrelated/oops.py"
    inventory = _make_inventory(repo, [in_scope_bad, out_of_scope_bad])
    symbol_index = _make_symbol_index(
        repo,
        [],
        parse_errors=[
            SymbolParseError(path=in_scope_bad, line=1, message="bad"),
            SymbolParseError(path=out_of_scope_bad, line=2, message="other"),
        ],
    )
    profile = CodebaseScopeProfile(
        scope_id="domain-broken",
        description="only domain",
        entry_files=[in_scope_bad],
    )

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )

    entry = scope_map.scope_entries[0]
    assert [err.path for err in entry.parse_errors_in_scope] == [in_scope_bad]
    assert entry.module_count == 0
    assert entry.function_count == 0


def test_scope_map_traceability_refs_isolates_traceability_subpath():
    repo = "/fake/repo"
    inventory = _make_inventory(
        repo,
        [
            "docs/public/codebase-analysis.md",
            "docs/traceability/README.md",
        ],
    )
    symbol_index = _make_symbol_index(repo, [])

    profile = CodebaseScopeProfile(
        scope_id="docs-mixed",
        description="docs mixed",
        entry_files=[],
        expected_tests=[],
        docs_refs=[
            "docs/public/codebase-analysis.md",
            "docs/traceability/README.md",
        ],
    )

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )
    entry = scope_map.scope_entries[0]
    assert entry.docs_in_scope == [
        "docs/public/codebase-analysis.md",
        "docs/traceability/README.md",
    ]
    assert entry.traceability_refs_in_scope == ["docs/traceability/README.md"]


def test_scope_map_is_deterministic_for_same_inputs():
    repo = "/fake/repo"
    inventory = _make_inventory(repo, ["src/hisys/domain/adapters.py"])
    symbol_index = _make_symbol_index(repo, ["src/hisys/domain/adapters.py"])

    profile = CodebaseScopeProfile(
        scope_id="domain-only",
        description="x",
        entry_files=["src/hisys/domain/adapters.py"],
    )

    once = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )
    twice = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )
    assert once.model_dump() == twice.model_dump()


def test_scope_map_orders_entries_by_scope_id():
    repo = "/fake/repo"
    inventory = _make_inventory(repo, [])
    symbol_index = _make_symbol_index(repo, [])

    profiles = [
        CodebaseScopeProfile(scope_id="zeta", description="z"),
        CodebaseScopeProfile(scope_id="alpha", description="a"),
        CodebaseScopeProfile(scope_id="mu", description="m"),
    ]
    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=profiles
    )
    assert [entry.scope_id for entry in scope_map.scope_entries] == [
        "alpha",
        "mu",
        "zeta",
    ]


def test_scope_map_preserves_safety_invariants_from_inputs():
    repo = "/fake/repo"
    inventory = _make_inventory(repo, [])
    symbol_index = _make_symbol_index(repo, [])

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[]
    )

    # The scope map is built from already-loaded artifact records, so it
    # never reads raw source content of its own.
    assert scope_map.raw_source_content_persisted is False
    for entry in scope_map.scope_entries:
        assert isinstance(entry, CodebaseScopeMapEntry)
