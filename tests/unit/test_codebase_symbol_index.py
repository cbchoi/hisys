"""RED/GREEN tests for the deterministic Python AST symbol index (M16.1..M16.4).

The symbol index is the second increment of `SPEC-HISYS-CODEBASE-ANALYSIS-001`.
M16.1 records, per Python source file, the module path, top-level imports,
class definitions (including nested classes and class methods), and free
function definitions, along with line ranges. M16.2 adds parse errors as
evidence. M16.3 adds heuristic classification tags. M16.4 adds the
JSON/Markdown writer and the `build-code-symbol-index` CLI. Behavior is
stdlib-only, deterministic, and never persists raw source content.

The remaining M16 sub-task is M16.5 (docs + traceability).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hisys.operations.codebase_analysis import (
    PythonSymbolIndex,
    SymbolFunction,
    SymbolClass,
    SymbolImport,
    SymbolModule,
    SymbolParseError,
    build_python_symbol_index,
    write_python_symbol_index,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _seed_symbol_fixture(repo: Path) -> None:
    pkg = repo / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")

    (pkg / "module.py").write_text(
        '"""Module docstring."""\n'
        "import os\n"
        "import sys as system\n"
        "from pathlib import Path\n"
        "from typing import (\n"
        "    Any,\n"
        "    Optional,\n"
        ")\n"
        "\n"
        "TOP_CONSTANT = 1\n"
        "\n"
        "\n"
        "def top_function(x, y=2):\n"
        "    return x + y\n"
        "\n"
        "\n"
        "async def top_async(x):\n"
        "    return x\n"
        "\n"
        "\n"
        "class Outer:\n"
        "    def method_a(self):\n"
        "        return 1\n"
        "\n"
        "    class Inner:\n"
        "        def inner_method(self, value):\n"
        "            return value\n"
        "\n"
        "    async def method_b(self):\n"
        "        return 2\n",
        encoding="utf-8",
    )

    (pkg / "subpkg").mkdir()
    (pkg / "subpkg" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "subpkg" / "leaf.py").write_text(
        "def leaf():\n    return None\n", encoding="utf-8"
    )

    # Non-Python file that must be ignored by the symbol indexer.
    (repo / "README.md").write_text("# fixture\n", encoding="utf-8")


def test_symbol_index_records_modules_imports_classes_functions(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_symbol_fixture(repo)

    index = build_python_symbol_index(repo_root=repo)

    assert isinstance(index, PythonSymbolIndex)
    assert index.schema_id == "hisys.codebase.symbol_index"
    assert index.raw_source_content_persisted is False
    assert index.repo_root == str(repo)

    module_paths = [module.path for module in index.modules]
    assert module_paths == sorted(module_paths), "modules must be sorted"
    assert module_paths == [
        "src/pkg/__init__.py",
        "src/pkg/module.py",
        "src/pkg/subpkg/__init__.py",
        "src/pkg/subpkg/leaf.py",
    ]

    # README.md is not a Python file and must be ignored.
    assert all(mod.path.endswith(".py") for mod in index.modules)

    module = next(m for m in index.modules if m.path == "src/pkg/module.py")
    assert isinstance(module, SymbolModule)
    assert module.module_qualname == "src.pkg.module"

    # Imports — both `import X` and `from X import Y` are captured deterministically.
    import_records = [(imp.module, imp.name, imp.asname) for imp in module.imports]
    assert (
        "os",
        "os",
        None,
    ) in import_records
    assert (
        "sys",
        "sys",
        "system",
    ) in import_records
    assert (
        "pathlib",
        "Path",
        None,
    ) in import_records
    assert (
        "typing",
        "Any",
        None,
    ) in import_records
    assert (
        "typing",
        "Optional",
        None,
    ) in import_records
    # Imports must be ordered by (module, name, asname) for determinism.
    assert module.imports == sorted(
        module.imports,
        key=lambda imp: (imp.module, imp.name, imp.asname or ""),
    )
    for imp in module.imports:
        assert isinstance(imp, SymbolImport)
        assert imp.line >= 1

    # Top-level functions, including async, are recorded.
    function_names = [fn.name for fn in module.functions]
    assert function_names == ["top_async", "top_function"], (
        "functions must be sorted by name for determinism"
    )
    top_async = next(fn for fn in module.functions if fn.name == "top_async")
    top_function = next(fn for fn in module.functions if fn.name == "top_function")
    assert isinstance(top_async, SymbolFunction)
    assert top_async.is_async is True
    assert top_function.is_async is False
    assert top_function.line_start >= 1
    assert top_function.line_end >= top_function.line_start
    assert top_function.parameters == ["x", "y"]

    # Classes capture nested classes and their methods.
    class_names = [cls.name for cls in module.classes]
    assert class_names == ["Outer"]
    outer = module.classes[0]
    assert isinstance(outer, SymbolClass)
    method_names = [m.name for m in outer.methods]
    assert method_names == ["method_a", "method_b"], (
        "methods must be sorted by name"
    )
    method_b = next(m for m in outer.methods if m.name == "method_b")
    assert method_b.is_async is True
    nested_class_names = [cls.name for cls in outer.nested_classes]
    assert nested_class_names == ["Inner"]
    inner = outer.nested_classes[0]
    assert [m.name for m in inner.methods] == ["inner_method"]
    assert inner.methods[0].parameters == ["self", "value"]

    # Aggregate counts mirror the per-module shape.
    assert index.module_count == 4
    assert index.import_count == sum(len(m.imports) for m in index.modules)
    assert index.class_count == sum(
        len(m.classes) + sum(len(c.nested_classes) for c in m.classes)
        for m in index.modules
    )
    assert index.function_count == sum(
        len(m.functions)
        + sum(
            len(c.methods)
            + sum(len(n.methods) for n in c.nested_classes)
            for c in m.classes
        )
        for m in index.modules
    )

    # Deterministic: a second build over the same fixture yields the same model.
    twice = build_python_symbol_index(repo_root=repo)
    assert twice.model_dump() == index.model_dump()


def test_symbol_index_skips_non_python_files(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def f():\n    pass\n", encoding="utf-8")
    (repo / "b.txt").write_text("not python\n", encoding="utf-8")
    (repo / "c.md").write_text("# doc\n", encoding="utf-8")

    index = build_python_symbol_index(repo_root=repo)

    module_paths = [m.path for m in index.modules]
    assert module_paths == ["a.py"]


def test_symbol_index_records_parse_errors_as_evidence(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "good.py").write_text(
        "def alive():\n    return 'ok'\n", encoding="utf-8"
    )
    (repo / "bad.py").write_text(
        "def broken(:\n    return 0\n", encoding="utf-8"
    )

    index = build_python_symbol_index(repo_root=repo)

    # The valid module is still indexed; parse failure must not halt the build.
    module_paths = [m.path for m in index.modules]
    assert "good.py" in module_paths
    assert "bad.py" not in module_paths

    # The bad module is preserved as evidence with a stable shape.
    assert index.parse_error_count == 1
    assert len(index.parse_errors) == 1
    err = index.parse_errors[0]
    assert isinstance(err, SymbolParseError)
    assert err.path == "bad.py"
    assert err.line >= 1
    assert isinstance(err.message, str) and err.message  # SyntaxError text is non-empty

    # Aggregate counts only cover successfully parsed modules.
    assert index.module_count == len(index.modules)
    assert index.module_count == 1
    assert index.raw_source_content_persisted is False

    # The aggregated parse_errors list is sorted by path for determinism.
    twice = build_python_symbol_index(repo_root=repo)
    assert twice.model_dump() == index.model_dump()


def test_symbol_index_classifies_cli_parser_and_pytest_functions(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "cli.py").write_text(
        "import argparse\n"
        "\n"
        "def _make_parser():\n"
        "    parser = argparse.ArgumentParser(prog='demo')\n"
        "    parser.add_argument('--name')\n"
        "    return parser\n"
        "\n"
        "def _cmd_demo(args):\n"
        "    return args.name\n"
        "\n"
        "def main():\n"
        "    parser = _make_parser()\n"
        "    args = parser.parse_args()\n"
        "    return _cmd_demo(args)\n",
        encoding="utf-8",
    )
    (repo / "test_demo.py").write_text(
        "def test_alpha():\n    assert True\n"
        "\n"
        "def helper():\n    return 1\n"
        "\n"
        "class TestThing:\n"
        "    def test_method(self):\n"
        "        assert True\n"
        "    def helper(self):\n"
        "        return 0\n",
        encoding="utf-8",
    )

    index = build_python_symbol_index(repo_root=repo)

    cli = next(m for m in index.modules if m.path == "cli.py")
    fn_tags = {fn.name: fn.tags for fn in cli.functions}
    assert fn_tags["_make_parser"] == ["parser_builder"]
    assert fn_tags["_cmd_demo"] == ["cli_handler"]
    assert fn_tags["main"] == []
    # Tags are sorted for determinism.
    for fn in cli.functions:
        assert fn.tags == sorted(fn.tags)

    tests_mod = next(m for m in index.modules if m.path == "test_demo.py")
    test_tags = {fn.name: fn.tags for fn in tests_mod.functions}
    assert test_tags["test_alpha"] == ["pytest_test"]
    assert test_tags["helper"] == []

    # Test methods inside a TestXxx class are also tagged as pytest tests so a
    # downstream reviewer can locate them without re-walking class hierarchies.
    test_class = next(cls for cls in tests_mod.classes if cls.name == "TestThing")
    method_tags = {m.name: m.tags for m in test_class.methods}
    assert method_tags["test_method"] == ["pytest_test"]
    assert method_tags["helper"] == []


def test_symbol_index_supports_analysis_scope(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "kept.py").write_text("def keep():\n    return 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "ignored.py").write_text(
        "def ignored():\n    return 0\n", encoding="utf-8"
    )

    index = build_python_symbol_index(repo_root=repo, analysis_scope="src")

    assert index.analysis_scope == "src"
    module_paths = [m.path for m in index.modules]
    assert module_paths == ["src/kept.py"]


def test_write_python_symbol_index_persists_json_and_markdown(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "demo.py").write_text(
        "import os\n"
        "\n"
        "def _cmd_run():\n"
        "    return 1\n"
        "\n"
        "class Outer:\n"
        "    def method(self):\n"
        "        return 1\n",
        encoding="utf-8",
    )

    index = build_python_symbol_index(repo_root=repo)

    instance = tmp_path / "instance"
    result = write_python_symbol_index(
        instance_root=instance,
        date="20260516",
        request_id="REQ-CODEBASE-001",
        symbol_index=index,
    )

    assert result["external_call_made"] is False
    assert result["mutation_performed"] is False
    assert result["publication_or_live_action_approved"] is False
    assert result["raw_source_content_persisted"] is False
    assert result["schema_id"] == "hisys.codebase.symbol_index"
    assert result["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/symbol-index.json"
    )
    assert result["markdown_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/symbol-index.md"
    )

    json_path = instance / result["json_ref"]
    md_path = instance / result["markdown_ref"]
    assert json_path.is_file()
    assert md_path.is_file()

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["schema_id"] == "hisys.codebase.symbol_index"
    assert loaded["raw_source_content_persisted"] is False
    # Re-rendering yields a byte-identical JSON file.
    other_instance = tmp_path / "instance_two"
    other_result = write_python_symbol_index(
        instance_root=other_instance,
        date="20260516",
        request_id="REQ-CODEBASE-001",
        symbol_index=index,
    )
    other_json = (other_instance / other_result["json_ref"]).read_text(encoding="utf-8")
    assert other_json == json_path.read_text(encoding="utf-8")

    markdown = md_path.read_text(encoding="utf-8")
    assert "hisys.codebase.symbol_index" in markdown
    assert "demo.py" in markdown
    assert "_cmd_run" in markdown
    assert "cli_handler" in markdown


def test_write_python_symbol_index_rejects_traversal_in_request_id(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    index = build_python_symbol_index(repo_root=repo)
    instance = tmp_path / "instance"

    for bad in ("../escape", "REQ/with/slash", "REQ\\back", ".."):
        with pytest.raises(ValueError):
            write_python_symbol_index(
                instance_root=instance,
                date="20260516",
                request_id=bad,
                symbol_index=index,
            )

    for bad_date in ("2026/05/16", "..", "20260516/extra"):
        with pytest.raises(ValueError):
            write_python_symbol_index(
                instance_root=instance,
                date=bad_date,
                request_id="REQ-CODEBASE-001",
                symbol_index=index,
            )


def _seed_cli_symbol_fixture(repo: Path) -> None:
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "pkg" / "module.py").write_text(
        "import argparse\n"
        "\n"
        "def _make_parser():\n"
        "    return argparse.ArgumentParser(prog='demo')\n"
        "\n"
        "def _cmd_demo(args):\n"
        "    return args\n"
        "\n"
        "class Outer:\n"
        "    def method(self):\n"
        "        return 1\n",
        encoding="utf-8",
    )
    (repo / "tests").mkdir()
    (repo / "tests" / "test_demo.py").write_text(
        "def test_demo():\n    assert True\n", encoding="utf-8"
    )


def test_build_code_symbol_index_cli_writes_artifacts(tmp_path: Path):
    fixture_repo = tmp_path / "fixture_repo"
    fixture_repo.mkdir()
    _seed_cli_symbol_fixture(fixture_repo)
    instance = tmp_path / "instance"

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.cli.main",
            "build-code-symbol-index",
            "--repo",
            str(fixture_repo),
            "--instance",
            str(instance),
            "--date",
            "20260516",
            "--request-id",
            "REQ-CODEBASE-001",
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.codebase.symbol_index"
    assert payload["raw_source_content_persisted"] is False
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False
    assert payload["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/symbol-index.json"
    )
    assert payload["markdown_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/symbol-index.md"
    )

    json_path = instance / payload["json_ref"]
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    module_paths = [m["path"] for m in loaded["modules"]]
    assert "src/pkg/module.py" in module_paths
    assert "tests/test_demo.py" in module_paths
    # Heuristic tags survive the JSON round trip.
    module = next(m for m in loaded["modules"] if m["path"] == "src/pkg/module.py")
    fn_tags = {fn["name"]: fn["tags"] for fn in module["functions"]}
    assert fn_tags["_make_parser"] == ["parser_builder"]
    assert fn_tags["_cmd_demo"] == ["cli_handler"]


def test_build_code_symbol_index_cli_supports_scope_filter(tmp_path: Path):
    fixture_repo = tmp_path / "fixture_repo"
    fixture_repo.mkdir()
    _seed_cli_symbol_fixture(fixture_repo)
    instance = tmp_path / "instance"

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.cli.main",
            "build-code-symbol-index",
            "--repo",
            str(fixture_repo),
            "--instance",
            str(instance),
            "--date",
            "20260516",
            "--request-id",
            "REQ-CODEBASE-002",
            "--scope",
            "src",
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    json_path = instance / payload["json_ref"]
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["analysis_scope"] == "src"
    module_paths = [m["path"] for m in loaded["modules"]]
    assert all(path.startswith("src/") for path in module_paths)
    assert "src/pkg/module.py" in module_paths
    assert "tests/test_demo.py" not in module_paths
