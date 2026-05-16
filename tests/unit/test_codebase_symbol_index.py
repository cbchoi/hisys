"""RED/GREEN tests for the deterministic Python AST symbol index (M16.1).

The symbol index is the second increment of `SPEC-HISYS-CODEBASE-ANALYSIS-001`.
M16.1 records, per Python source file, the module path, top-level imports,
class definitions (including nested classes and class methods), and free
function definitions, along with line ranges. Behavior is stdlib-only,
deterministic, and never persists raw source content.

Later M16 sub-tasks add parse-error evidence (M16.2), CLI/test/doc
classification (M16.3), JSON/Markdown writer + CLI (M16.4), and docs +
traceability (M16.5).
"""

from __future__ import annotations

from pathlib import Path

from hisys.operations.codebase_analysis import (
    PythonSymbolIndex,
    SymbolFunction,
    SymbolClass,
    SymbolImport,
    SymbolModule,
    SymbolParseError,
    build_python_symbol_index,
)


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
