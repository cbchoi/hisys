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

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from hisys.operations.codebase_analysis import (
    CodebaseInventory,
    CodebaseScopeMap,
    CodebaseScopeMapEntry,
    CodebaseScopeProfile,
    CodebaseValidationPlan,
    PythonSymbolIndex,
    ScopeValidationPlan,
    SymbolFunction,
    SymbolImport,
    SymbolModule,
    SymbolParseError,
    ValidationPlanCommand,
    build_codebase_inventory,
    build_codebase_scope_map,
    build_codebase_validation_plan,
    build_python_symbol_index,
    get_codebase_scope_profile,
    list_codebase_scope_profiles,
    resolve_instance_runtime_ref,
    write_codebase_inventory,
    write_codebase_scope_map,
    write_python_symbol_index,
)

import os
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


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


# ---------------------------------------------------------------------------
# M17.3 — validation plan synthesis
# ---------------------------------------------------------------------------


def _scope_map_for_validation_plan(
    profiles: list[CodebaseScopeProfile], file_set: list[str]
) -> CodebaseScopeMap:
    repo = "/fake/repo"
    inventory = _make_inventory(repo, file_set)
    py_files = [path for path in file_set if path.endswith(".py")]
    symbol_index = _make_symbol_index(repo, py_files)
    return build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=profiles
    )


def _find_command(plan: ScopeValidationPlan, kind: str) -> ValidationPlanCommand:
    matches = [cmd for cmd in plan.commands if cmd.kind == kind]
    assert matches, f"validation plan for {plan.scope_id} missing {kind} command"
    assert len(matches) == 1, (
        f"validation plan for {plan.scope_id} has multiple {kind} commands"
    )
    return matches[0]


def test_validation_plan_top_level_envelope_records_safety_invariants():
    profile = CodebaseScopeProfile(
        scope_id="example",
        description="x",
        entry_files=["src/example.py"],
    )
    scope_map = _scope_map_for_validation_plan([profile], ["src/example.py"])

    plan = build_codebase_validation_plan(scope_map)

    assert isinstance(plan, CodebaseValidationPlan)
    assert plan.schema_id == "hisys.codebase.validation_plan"
    assert plan.raw_source_content_persisted is False
    assert [sp.scope_id for sp in plan.scope_plans] == ["example"]


def test_validation_plan_for_docs_traceability_scope_skips_focused_pytest():
    docs_profile = get_codebase_scope_profile("docs-traceability")
    scope_map = _scope_map_for_validation_plan(
        [docs_profile],
        [
            "scripts/validate_traceability.py",
            "docs/traceability/README.md",
        ],
    )

    plan = build_codebase_validation_plan(scope_map)
    scope_plan = plan.scope_plans[0]
    assert scope_plan.scope_id == "docs-traceability"

    kinds = [cmd.kind for cmd in scope_plan.commands]
    assert "focused_tests" not in kinds  # no expected_tests in this scope
    assert "traceability" in kinds
    assert "git_diff_check" in kinds
    assert "secret_scan" in kinds

    traceability_cmd = _find_command(scope_plan, "traceability")
    assert traceability_cmd.argv == [
        "python3",
        "scripts/validate_traceability.py",
    ]
    git_cmd = _find_command(scope_plan, "git_diff_check")
    assert git_cmd.argv == ["git", "diff", "--check"]


def test_validation_plan_for_domain_adapter_emits_focused_pytest_invocation():
    domain_profile = get_codebase_scope_profile("domain-adapter")
    file_set = list(domain_profile.entry_files) + list(domain_profile.expected_tests) + [
        "docs/traceability/README.md",
    ]
    scope_map = _scope_map_for_validation_plan([domain_profile], file_set)

    plan = build_codebase_validation_plan(scope_map)
    scope_plan = plan.scope_plans[0]
    assert scope_plan.scope_id == "domain-adapter"

    focused = _find_command(scope_plan, "focused_tests")
    assert focused.argv[:3] == ["python3", "-m", "pytest"]
    assert focused.argv[-1] == "-q"
    selected_tests = focused.argv[3:-1]
    assert selected_tests == sorted(selected_tests)  # deterministic ordering
    assert selected_tests == list(domain_profile.expected_tests)

    # No drift -> the focused suite is sufficient and the full suite is not
    # required for this scope.
    assert scope_plan.requires_full_suite is False
    kinds = [cmd.kind for cmd in scope_plan.commands]
    assert "full_tests" not in kinds


def test_validation_plan_marks_runtime_boundary_scope_as_cross_cutting():
    runtime_profile = get_codebase_scope_profile("runtime-boundary")
    file_set = list(runtime_profile.entry_files) + list(runtime_profile.expected_tests) + [
        "docs/public/codebase-analysis.md",
    ]
    scope_map = _scope_map_for_validation_plan([runtime_profile], file_set)

    plan = build_codebase_validation_plan(scope_map)
    scope_plan = plan.scope_plans[0]
    assert scope_plan.scope_id == "runtime-boundary"
    assert scope_plan.requires_full_suite is True

    full = _find_command(scope_plan, "full_tests")
    assert full.argv == ["python3", "-m", "pytest", "-q"]


def test_validation_plan_requires_full_suite_when_inventory_drift_detected():
    # The inventory deliberately omits one of the profile's expected_tests so
    # `missing_expected_tests` is non-empty; the plan must escalate to the
    # full suite so a reviewer notices the drift instead of trusting a
    # partial focused gate.
    profile = CodebaseScopeProfile(
        scope_id="drifted",
        description="drift signal",
        entry_files=["src/example.py"],
        expected_tests=[
            "tests/unit/test_example_a.py",
            "tests/unit/test_example_b.py",
        ],
    )
    scope_map = _scope_map_for_validation_plan(
        [profile],
        [
            "src/example.py",
            "tests/unit/test_example_a.py",
            # test_example_b.py intentionally missing
        ],
    )

    plan = build_codebase_validation_plan(scope_map)
    scope_plan = plan.scope_plans[0]
    assert scope_plan.requires_full_suite is True
    assert "tests/unit/test_example_b.py" in (
        scope_map.scope_entries[0].missing_expected_tests
    )


def test_validation_plan_commands_are_sorted_by_kind_and_deterministic():
    profile = get_codebase_scope_profile("domain-adapter")
    file_set = list(profile.entry_files) + list(profile.expected_tests) + [
        "docs/traceability/README.md",
    ]
    scope_map = _scope_map_for_validation_plan([profile], file_set)

    plan_once = build_codebase_validation_plan(scope_map)
    plan_twice = build_codebase_validation_plan(scope_map)
    assert plan_once.model_dump() == plan_twice.model_dump()

    for scope_plan in plan_once.scope_plans:
        kinds = [cmd.kind for cmd in scope_plan.commands]
        assert kinds == sorted(kinds)


def test_validation_plan_secret_scan_only_added_when_scope_has_content():
    empty_profile = CodebaseScopeProfile(
        scope_id="empty",
        description="empty",
        entry_files=[],
        expected_tests=[],
        docs_refs=[],
    )
    scope_map = _scope_map_for_validation_plan([empty_profile], [])

    plan = build_codebase_validation_plan(scope_map)
    scope_plan = plan.scope_plans[0]
    kinds = [cmd.kind for cmd in scope_plan.commands]
    assert "secret_scan" not in kinds
    # traceability and git_diff_check remain mandatory.
    assert "traceability" in kinds
    assert "git_diff_check" in kinds


def test_validation_plan_command_carries_purpose_string():
    profile = CodebaseScopeProfile(
        scope_id="explainer",
        description="x",
        entry_files=["src/example.py"],
        expected_tests=["tests/unit/test_example.py"],
    )
    scope_map = _scope_map_for_validation_plan(
        [profile], ["src/example.py", "tests/unit/test_example.py"]
    )
    plan = build_codebase_validation_plan(scope_map)
    scope_plan = plan.scope_plans[0]

    for cmd in scope_plan.commands:
        assert isinstance(cmd, ValidationPlanCommand)
        assert cmd.purpose, f"{cmd.kind} command must carry a non-empty purpose"


# ---------------------------------------------------------------------------
# M17.4 — writer and CLI (`build-codebase-map`)
# ---------------------------------------------------------------------------


def _seed_writer_fixture(repo: Path) -> None:
    (repo / "src" / "hisys" / "domain").mkdir(parents=True)
    (repo / "src" / "hisys" / "domain" / "adapters.py").write_text(
        "def f():\n    return 1\n", encoding="utf-8"
    )
    (repo / "tests" / "unit").mkdir(parents=True)
    (repo / "tests" / "unit" / "test_domain_adapter_registry.py").write_text(
        "def test_x():\n    assert True\n", encoding="utf-8"
    )
    (repo / "docs" / "traceability").mkdir(parents=True)
    (repo / "docs" / "traceability" / "README.md").write_text("# trace\n", encoding="utf-8")


def test_resolve_instance_runtime_ref_accepts_safe_subpath(tmp_path: Path):
    instance = tmp_path / "instance"
    instance.mkdir()
    target = (
        instance
        / "runtime-boundary"
        / "codebase-analysis"
        / "20260517"
        / "REQ-A"
        / "inventory.json"
    )
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")

    resolved = resolve_instance_runtime_ref(
        instance_root=instance,
        relative_ref=(
            "runtime-boundary/codebase-analysis/20260517/REQ-A/inventory.json"
        ),
    )
    assert resolved == target.resolve()


def test_resolve_instance_runtime_ref_rejects_absolute_and_traversal(tmp_path: Path):
    instance = tmp_path / "instance"
    instance.mkdir()

    for bad in (
        "/etc/passwd",
        "../escape.json",
        "runtime-boundary/../../etc/passwd",
        "",
    ):
        with pytest.raises(ValueError):
            resolve_instance_runtime_ref(
                instance_root=instance, relative_ref=bad
            )


def test_resolve_instance_runtime_ref_rejects_symlink_outside_instance(tmp_path: Path):
    instance = tmp_path / "instance"
    instance.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.json").write_text("{}", encoding="utf-8")

    # A symlinked subpath that leaves the instance root must fail closed.
    link = instance / "leak.json"
    os.symlink(outside / "secret.json", link)

    with pytest.raises(ValueError):
        resolve_instance_runtime_ref(instance_root=instance, relative_ref="leak.json")


def test_write_codebase_scope_map_persists_json_and_markdown(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_writer_fixture(repo)
    inventory = build_codebase_inventory(repo_root=repo)
    symbol_index = build_python_symbol_index(repo_root=repo)
    profile = get_codebase_scope_profile("domain-adapter")
    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )
    validation_plan = build_codebase_validation_plan(scope_map)

    instance = tmp_path / "instance"
    result = write_codebase_scope_map(
        instance_root=instance,
        date="20260517",
        request_id="REQ-CODEBASE-001",
        scope_map=scope_map,
        validation_plan=validation_plan,
    )

    assert result["external_call_made"] is False
    assert result["mutation_performed"] is False
    assert result["publication_or_live_action_approved"] is False
    assert result["raw_source_content_persisted"] is False
    assert result["schema_id"] == "hisys.codebase.scope_map"
    assert result["validation_plan_schema_id"] == "hisys.codebase.validation_plan"
    assert result["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/scope-map.json"
    )
    assert result["markdown_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/scope-map.md"
    )

    json_path = instance / result["json_ref"]
    md_path = instance / result["markdown_ref"]
    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["scope_map"]["schema_id"] == "hisys.codebase.scope_map"
    assert payload["validation_plan"]["schema_id"] == "hisys.codebase.validation_plan"
    assert payload["scope_map"]["raw_source_content_persisted"] is False

    # Determinism: re-writing yields a byte-identical JSON file.
    other_instance = tmp_path / "instance_two"
    other_result = write_codebase_scope_map(
        instance_root=other_instance,
        date="20260517",
        request_id="REQ-CODEBASE-001",
        scope_map=scope_map,
        validation_plan=validation_plan,
    )
    other_json = (other_instance / other_result["json_ref"]).read_text(encoding="utf-8")
    assert other_json == json_path.read_text(encoding="utf-8")

    markdown = md_path.read_text(encoding="utf-8")
    assert "hisys.codebase.scope_map" in markdown
    assert "domain-adapter" in markdown


def test_write_codebase_scope_map_rejects_traversal_in_request_id(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_writer_fixture(repo)
    inventory = build_codebase_inventory(repo_root=repo)
    symbol_index = build_python_symbol_index(repo_root=repo)
    profile = get_codebase_scope_profile("domain-adapter")
    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index, profiles=[profile]
    )
    validation_plan = build_codebase_validation_plan(scope_map)

    instance = tmp_path / "instance"
    for bad in ("../escape", "REQ/with/slash", ".."):
        with pytest.raises(ValueError):
            write_codebase_scope_map(
                instance_root=instance,
                date="20260517",
                request_id=bad,
                scope_map=scope_map,
                validation_plan=validation_plan,
            )

    for bad_date in ("2026/05/17", "..", "20260517/extra"):
        with pytest.raises(ValueError):
            write_codebase_scope_map(
                instance_root=instance,
                date=bad_date,
                request_id="REQ-CODEBASE-001",
                scope_map=scope_map,
                validation_plan=validation_plan,
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


def _prepare_cli_inputs(tmp_path: Path) -> tuple[Path, Path, str, str]:
    fixture_repo = tmp_path / "fixture_repo"
    fixture_repo.mkdir()
    _seed_writer_fixture(fixture_repo)
    instance = tmp_path / "instance"

    inventory_result = _run_cli(
        "build-codebase-inventory",
        "--repo",
        str(fixture_repo),
        "--instance",
        str(instance),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-001",
        "--format",
        "json",
        cwd=REPO_ROOT,
    )
    assert inventory_result.returncode == 0, inventory_result.stderr
    inventory_payload = json.loads(inventory_result.stdout)

    symbol_result = _run_cli(
        "build-code-symbol-index",
        "--repo",
        str(fixture_repo),
        "--instance",
        str(instance),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-001",
        "--format",
        "json",
        cwd=REPO_ROOT,
    )
    assert symbol_result.returncode == 0, symbol_result.stderr
    symbol_payload = json.loads(symbol_result.stdout)

    return (
        fixture_repo,
        instance,
        inventory_payload["json_ref"],
        symbol_payload["json_ref"],
    )


def test_build_codebase_map_cli_writes_artifacts(tmp_path: Path):
    _, instance, inventory_ref, symbol_ref = _prepare_cli_inputs(tmp_path)

    completed = _run_cli(
        "build-codebase-map",
        "--instance",
        str(instance),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-001",
        "--inventory-ref",
        inventory_ref,
        "--symbol-index-ref",
        symbol_ref,
        "--format",
        "json",
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.codebase.scope_map"
    assert payload["validation_plan_schema_id"] == "hisys.codebase.validation_plan"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False
    assert payload["raw_source_content_persisted"] is False
    assert payload["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/scope-map.json"
    )

    json_path = instance / payload["json_ref"]
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    scope_ids = [entry["scope_id"] for entry in loaded["scope_map"]["scope_entries"]]
    assert scope_ids == ["docs-traceability", "domain-adapter", "runtime-boundary"]


def test_build_codebase_map_cli_rejects_absolute_input_refs(tmp_path: Path):
    _, instance, inventory_ref, symbol_ref = _prepare_cli_inputs(tmp_path)

    abs_path = str((instance / inventory_ref).resolve())
    completed = _run_cli(
        "build-codebase-map",
        "--instance",
        str(instance),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-002",
        "--inventory-ref",
        abs_path,  # absolute path is rejected by the safe ref resolver
        "--symbol-index-ref",
        symbol_ref,
        "--format",
        "json",
        cwd=REPO_ROOT,
    )
    assert completed.returncode != 0
    assert "inventory" in (completed.stderr + completed.stdout).lower() or (
        "absolute" in (completed.stderr + completed.stdout).lower()
    )


def test_build_codebase_map_cli_rejects_traversal_input_refs(tmp_path: Path):
    _, instance, _, symbol_ref = _prepare_cli_inputs(tmp_path)

    completed = _run_cli(
        "build-codebase-map",
        "--instance",
        str(instance),
        "--date",
        "20260517",
        "--request-id",
        "REQ-CODEBASE-003",
        "--inventory-ref",
        "../escape/inventory.json",
        "--symbol-index-ref",
        symbol_ref,
        "--format",
        "json",
        cwd=REPO_ROOT,
    )
    assert completed.returncode != 0
    assert "traversal" in (completed.stderr + completed.stdout).lower() or (
        "outside" in (completed.stderr + completed.stdout).lower()
    )
