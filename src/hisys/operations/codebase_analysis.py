"""Deterministic, fixture-local codebase inventory.

The inventory builder is the first increment of the codebase-analysis surface
(`SPEC-HISYS-CODEBASE-ANALYSIS-001`). It performs a pure local repository walk
under an explicit caller-supplied root and excludes transient/generated paths
so downstream analyses operate on a stable file set without depending on the
working-directory state of CI runners or developer machines.

M15.1 introduced the deterministic walk and transient-path exclusion. M15.2
adds the path policy contract, safety classifications (binary / large /
generated), skip-reason recording, and realpath anchors. Subsequent
milestones add the JSON/Markdown writer (M15.3), CLI wrapper (M15.4), and
docs/traceability rows (M15.5). The schema_id remains `hisys.codebase.inventory`
across those increments.
"""

from __future__ import annotations

import ast
import json
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# Directories whose contents are transient build/cache/VCS state and never
# represent reviewable source. The exclusion is purely name-based so the walk
# stays deterministic and free of host-specific lookups.
DEFAULT_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".cache",
        ".eggs",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
    }
)

# Substrings that indicate a text file is machine-generated. Matched against
# the first `binary_null_byte_probe_bytes` of file content so the probe stays
# bounded and deterministic.
DEFAULT_GENERATED_MARKERS: tuple[str, ...] = (
    "@generated",
    "DO NOT EDIT",
    "Auto-generated",
    "AUTO-GENERATED",
)

# Filename suffixes that are conventionally machine-produced artifacts.
DEFAULT_GENERATED_SUFFIXES: tuple[str, ...] = (
    ".min.js",
    ".min.css",
    ".lock",
    ".lockb",
)


class PathPolicy(BaseModel):
    follow_symlinks: bool = False
    reject_outside_repo: bool = True
    max_file_size_bytes: int = 1_048_576
    binary_null_byte_probe_bytes: int = 8192
    excluded_dirs: list[str] = Field(
        default_factory=lambda: sorted(DEFAULT_EXCLUDED_DIRS)
    )
    generated_marker_substrings: list[str] = Field(
        default_factory=lambda: list(DEFAULT_GENERATED_MARKERS)
    )
    generated_suffixes: list[str] = Field(
        default_factory=lambda: list(DEFAULT_GENERATED_SUFFIXES)
    )


class SkippedPath(BaseModel):
    path: str
    reason: str


class CodebaseInventory(BaseModel):
    schema_id: str = "hisys.codebase.inventory"
    repo_root: str
    repo_root_realpath: str | None = None
    analysis_scope: str | None = None
    files: list[str] = Field(default_factory=list)
    excluded_paths: list[str] = Field(default_factory=list)
    skipped_paths: list[SkippedPath] = Field(default_factory=list)
    path_policy: PathPolicy = Field(default_factory=PathPolicy)
    file_count: int = 0
    binary_file_count: int = 0
    large_file_count: int = 0
    generated_file_count: int = 0
    raw_source_content_persisted: bool = False


def _classify_file(
    path: Path, policy: PathPolicy
) -> tuple[bool, bool, bool]:
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    try:
        with path.open("rb") as handle:
            head = handle.read(policy.binary_null_byte_probe_bytes)
    except OSError:
        head = b""

    is_binary = b"\x00" in head
    is_large = size > policy.max_file_size_bytes

    if any(path.name.endswith(suffix) for suffix in policy.generated_suffixes):
        is_generated = True
    elif is_binary:
        is_generated = False
    else:
        # `errors='ignore'` keeps the marker scan deterministic on partial
        # multi-byte boundaries — generated markers are ASCII so the scan
        # cannot miss them through codec failure.
        text = head.decode("utf-8", errors="ignore")
        is_generated = any(
            marker in text for marker in policy.generated_marker_substrings
        )
    return is_binary, is_large, is_generated


def build_codebase_inventory(
    repo_root: Path,
    *,
    analysis_scope: str | None = None,
    path_policy: PathPolicy | None = None,
) -> CodebaseInventory:
    root = Path(repo_root)
    if not root.is_dir():
        raise NotADirectoryError(f"repo_root is not a directory: {root}")

    if analysis_scope is not None:
        scope_path = (root / analysis_scope).resolve()
        try:
            scope_path.relative_to(root.resolve())
        except ValueError as exc:  # scope escapes the repo root
            raise ValueError(
                f"analysis_scope {analysis_scope!r} resolves outside repo_root"
            ) from exc
        if not scope_path.is_dir():
            raise NotADirectoryError(
                f"analysis_scope {analysis_scope!r} is not a directory under repo_root"
            )
        walk_root = root / analysis_scope
    else:
        walk_root = root

    policy = path_policy or PathPolicy()
    excluded_dirs = set(policy.excluded_dirs)
    real_root = Path(os.path.realpath(root))

    files: list[str] = []
    excluded: list[str] = []
    skipped: list[SkippedPath] = []
    counters = {"binary": 0, "large": 0, "generated": 0}

    def is_outside_repo(symlink_path: Path) -> bool:
        try:
            target_real = Path(os.path.realpath(symlink_path))
            target_real.relative_to(real_root)
        except ValueError:
            return True
        return False

    def walk(current: Path) -> None:
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except PermissionError:
            return
        for entry in entries:
            rel = entry.relative_to(root).as_posix()
            if entry.is_symlink():
                if policy.reject_outside_repo and is_outside_repo(entry):
                    skipped.append(
                        SkippedPath(path=rel, reason="outside_repo_symlink")
                    )
                else:
                    skipped.append(SkippedPath(path=rel, reason="symlink_skipped"))
                continue
            if entry.is_dir():
                if entry.name in excluded_dirs:
                    excluded.append(rel)
                    continue
                walk(entry)
            elif entry.is_file():
                files.append(rel)
                is_binary, is_large, is_generated = _classify_file(entry, policy)
                if is_binary:
                    counters["binary"] += 1
                if is_large:
                    counters["large"] += 1
                if is_generated:
                    counters["generated"] += 1

    walk(walk_root)

    return CodebaseInventory(
        repo_root=str(root),
        repo_root_realpath=str(real_root),
        analysis_scope=analysis_scope,
        files=sorted(files),
        excluded_paths=sorted(excluded),
        skipped_paths=sorted(skipped, key=lambda s: s.path),
        path_policy=policy,
        file_count=len(files),
        binary_file_count=counters["binary"],
        large_file_count=counters["large"],
        generated_file_count=counters["generated"],
        raw_source_content_persisted=False,
    )


# Limit `date` and `request_id` to a conservative slug shape so the writer
# cannot be tricked into writing outside the `<instance>/runtime-boundary/...`
# subtree via traversal segments. Callers that need richer characters must
# normalize before invocation.
_DATE_PATTERN = re.compile(r"^\d{8}$")
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

INVENTORY_RUNTIME_PREFIX = "runtime-boundary/codebase-analysis"


def _validate_slug(name: str, value: str, pattern: re.Pattern[str]) -> None:
    if not pattern.fullmatch(value):
        raise ValueError(
            f"invalid {name} for inventory writer: {value!r}; "
            f"must match {pattern.pattern}"
        )
    if value in {".", ".."}:
        raise ValueError(
            f"invalid {name} for inventory writer: {value!r}; "
            "traversal segments are not allowed"
        )


def _render_inventory_markdown(inventory: CodebaseInventory) -> str:
    policy = inventory.path_policy
    lines: list[str] = []
    lines.append(f"# Codebase Inventory — {inventory.schema_id}")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(f"- repo_root: `{inventory.repo_root}`")
    lines.append(f"- repo_root_realpath: `{inventory.repo_root_realpath or ''}`")
    lines.append(
        f"- analysis_scope: `{inventory.analysis_scope}`"
        if inventory.analysis_scope is not None
        else "- analysis_scope: (whole repo)"
    )
    lines.append(f"- raw_source_content_persisted: {inventory.raw_source_content_persisted}")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- file_count: {inventory.file_count}")
    lines.append(f"- binary_file_count: {inventory.binary_file_count}")
    lines.append(f"- large_file_count: {inventory.large_file_count}")
    lines.append(f"- generated_file_count: {inventory.generated_file_count}")
    lines.append("")
    lines.append("## Path Policy")
    lines.append("")
    lines.append(f"- follow_symlinks: {policy.follow_symlinks}")
    lines.append(f"- reject_outside_repo: {policy.reject_outside_repo}")
    lines.append(f"- max_file_size_bytes: {policy.max_file_size_bytes}")
    lines.append(f"- binary_null_byte_probe_bytes: {policy.binary_null_byte_probe_bytes}")
    lines.append("- excluded_dirs:")
    for entry in policy.excluded_dirs:
        lines.append(f"  - `{entry}`")
    lines.append("- generated_suffixes:")
    for entry in policy.generated_suffixes:
        lines.append(f"  - `{entry}`")
    lines.append("- generated_marker_substrings:")
    for entry in policy.generated_marker_substrings:
        lines.append(f"  - `{entry}`")
    lines.append("")
    lines.append("## Excluded Paths")
    lines.append("")
    if inventory.excluded_paths:
        for entry in inventory.excluded_paths:
            lines.append(f"- `{entry}`")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Skipped Paths")
    lines.append("")
    if inventory.skipped_paths:
        for entry in inventory.skipped_paths:
            lines.append(f"- `{entry.path}` — {entry.reason}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    if inventory.files:
        for entry in inventory.files:
            lines.append(f"- `{entry}`")
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def write_codebase_inventory(
    *,
    instance_root: Path,
    date: str,
    request_id: str,
    inventory: CodebaseInventory,
) -> dict[str, object]:
    _validate_slug("date", date, _DATE_PATTERN)
    _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)

    rel_dir = f"{INVENTORY_RUNTIME_PREFIX}/{date}/{request_id}"
    out_dir = Path(instance_root) / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    json_rel = f"{rel_dir}/inventory.json"
    md_rel = f"{rel_dir}/inventory.md"
    json_path = Path(instance_root) / json_rel
    md_path = Path(instance_root) / md_rel

    payload = inventory.model_dump(mode="json")
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_inventory_markdown(inventory), encoding="utf-8")

    return {
        "schema_id": inventory.schema_id,
        "json_ref": json_rel,
        "markdown_ref": md_rel,
        "raw_source_content_persisted": inventory.raw_source_content_persisted,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }


class SymbolImport(BaseModel):
    module: str
    name: str
    asname: str | None = None
    line: int


class SymbolFunction(BaseModel):
    name: str
    line_start: int
    line_end: int
    is_async: bool = False
    parameters: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SymbolClass(BaseModel):
    name: str
    line_start: int
    line_end: int
    methods: list[SymbolFunction] = Field(default_factory=list)
    nested_classes: list["SymbolClass"] = Field(default_factory=list)


SymbolClass.model_rebuild()


class SymbolModule(BaseModel):
    path: str
    module_qualname: str
    imports: list[SymbolImport] = Field(default_factory=list)
    functions: list[SymbolFunction] = Field(default_factory=list)
    classes: list[SymbolClass] = Field(default_factory=list)


class SymbolParseError(BaseModel):
    path: str
    line: int
    column: int = 0
    message: str


class PythonSymbolIndex(BaseModel):
    schema_id: str = "hisys.codebase.symbol_index"
    repo_root: str
    analysis_scope: str | None = None
    modules: list[SymbolModule] = Field(default_factory=list)
    parse_errors: list[SymbolParseError] = Field(default_factory=list)
    module_count: int = 0
    import_count: int = 0
    class_count: int = 0
    function_count: int = 0
    parse_error_count: int = 0
    raw_source_content_persisted: bool = False


def _module_qualname(rel_path: str) -> str:
    parts = rel_path.split("/")
    if parts and parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def _parameter_names(args: ast.arguments) -> list[str]:
    names: list[str] = []
    for arg in args.posonlyargs:
        names.append(arg.arg)
    for arg in args.args:
        names.append(arg.arg)
    if args.vararg is not None:
        names.append(args.vararg.arg)
    for arg in args.kwonlyargs:
        names.append(arg.arg)
    if args.kwarg is not None:
        names.append(args.kwarg.arg)
    return names


def _classify_function_tags(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> list[str]:
    tags: list[str] = []
    if node.name.startswith("test_"):
        tags.append("pytest_test")
    if node.name.startswith("_cmd_"):
        tags.append("cli_handler")
    if _function_builds_argparse_parser(node):
        tags.append("parser_builder")
    tags.sort()
    return tags


def _function_builds_argparse_parser(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        callee = child.func
        if isinstance(callee, ast.Attribute) and callee.attr == "ArgumentParser":
            if isinstance(callee.value, ast.Name) and callee.value.id == "argparse":
                return True
        if isinstance(callee, ast.Name) and callee.id == "ArgumentParser":
            return True
    return False


def _function_node_to_symbol(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> SymbolFunction:
    end_line = getattr(node, "end_lineno", None) or node.lineno
    return SymbolFunction(
        name=node.name,
        line_start=node.lineno,
        line_end=end_line,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        parameters=_parameter_names(node.args),
        tags=_classify_function_tags(node),
    )


def _class_node_to_symbol(node: ast.ClassDef) -> SymbolClass:
    methods: list[SymbolFunction] = []
    nested_classes: list[SymbolClass] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_function_node_to_symbol(child))
        elif isinstance(child, ast.ClassDef):
            nested_classes.append(_class_node_to_symbol(child))
    methods.sort(key=lambda m: m.name)
    nested_classes.sort(key=lambda c: c.name)
    end_line = getattr(node, "end_lineno", None) or node.lineno
    return SymbolClass(
        name=node.name,
        line_start=node.lineno,
        line_end=end_line,
        methods=methods,
        nested_classes=nested_classes,
    )


def _import_nodes_to_symbols(node: ast.Import | ast.ImportFrom) -> list[SymbolImport]:
    if isinstance(node, ast.Import):
        return [
            SymbolImport(
                module=alias.name,
                name=alias.name,
                asname=alias.asname,
                line=node.lineno,
            )
            for alias in node.names
        ]
    # ImportFrom — `from module import name [as asname]`. `node.module` is
    # None for purely relative imports such as `from . import x`; preserve the
    # relative dot prefix so the record is unambiguous.
    base = node.module or ""
    prefix = "." * (node.level or 0)
    module_label = f"{prefix}{base}" if prefix else base
    return [
        SymbolImport(
            module=module_label,
            name=alias.name,
            asname=alias.asname,
            line=node.lineno,
        )
        for alias in node.names
    ]


def _build_module_symbols(rel_path: str, source: str) -> SymbolModule:
    tree = ast.parse(source)
    imports: list[SymbolImport] = []
    functions: list[SymbolFunction] = []
    classes: list[SymbolClass] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(_import_nodes_to_symbols(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_function_node_to_symbol(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_class_node_to_symbol(node))
    imports.sort(key=lambda imp: (imp.module, imp.name, imp.asname or ""))
    functions.sort(key=lambda fn: fn.name)
    classes.sort(key=lambda cls: cls.name)
    return SymbolModule(
        path=rel_path,
        module_qualname=_module_qualname(rel_path),
        imports=imports,
        functions=functions,
        classes=classes,
    )


def _count_class_symbols(cls: SymbolClass) -> tuple[int, int]:
    class_count = 1
    method_count = len(cls.methods)
    for nested in cls.nested_classes:
        nested_classes, nested_methods = _count_class_symbols(nested)
        class_count += nested_classes
        method_count += nested_methods
    return class_count, method_count


def _render_symbol_class_markdown(
    cls: SymbolClass, lines: list[str], indent: int
) -> None:
    pad = "  " * indent
    lines.append(f"{pad}- class `{cls.name}` (lines {cls.line_start}–{cls.line_end})")
    for method in cls.methods:
        method_label = f"async def {method.name}" if method.is_async else f"def {method.name}"
        params = ", ".join(method.parameters)
        tag_label = f" — tags: {', '.join(method.tags)}" if method.tags else ""
        lines.append(
            f"{pad}  - {method_label}({params}) "
            f"(lines {method.line_start}–{method.line_end}){tag_label}"
        )
    for nested in cls.nested_classes:
        _render_symbol_class_markdown(nested, lines, indent + 1)


def _render_symbol_index_markdown(index: PythonSymbolIndex) -> str:
    lines: list[str] = []
    lines.append(f"# Codebase Symbol Index — {index.schema_id}")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(f"- repo_root: `{index.repo_root}`")
    if index.analysis_scope is not None:
        lines.append(f"- analysis_scope: `{index.analysis_scope}`")
    else:
        lines.append("- analysis_scope: (whole repo)")
    lines.append(
        f"- raw_source_content_persisted: {index.raw_source_content_persisted}"
    )
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- module_count: {index.module_count}")
    lines.append(f"- import_count: {index.import_count}")
    lines.append(f"- class_count: {index.class_count}")
    lines.append(f"- function_count: {index.function_count}")
    lines.append(f"- parse_error_count: {index.parse_error_count}")
    lines.append("")
    lines.append("## Parse Errors")
    lines.append("")
    if index.parse_errors:
        for err in index.parse_errors:
            lines.append(
                f"- `{err.path}` line {err.line} col {err.column}: {err.message}"
            )
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Modules")
    lines.append("")
    if not index.modules:
        lines.append("- (none)")
        lines.append("")
        return "\n".join(lines)
    for module in index.modules:
        lines.append(f"### `{module.path}` ({module.module_qualname})")
        lines.append("")
        lines.append("- Imports:")
        if module.imports:
            for imp in module.imports:
                asname = f" as {imp.asname}" if imp.asname else ""
                lines.append(
                    f"  - `{imp.module}.{imp.name}{asname}` (line {imp.line})"
                )
        else:
            lines.append("  - (none)")
        lines.append("- Functions:")
        if module.functions:
            for fn in module.functions:
                kw = "async def" if fn.is_async else "def"
                params = ", ".join(fn.parameters)
                tag_label = f" — tags: {', '.join(fn.tags)}" if fn.tags else ""
                lines.append(
                    f"  - {kw} {fn.name}({params}) "
                    f"(lines {fn.line_start}–{fn.line_end}){tag_label}"
                )
        else:
            lines.append("  - (none)")
        lines.append("- Classes:")
        if module.classes:
            for cls in module.classes:
                _render_symbol_class_markdown(cls, lines, indent=1)
        else:
            lines.append("  - (none)")
        lines.append("")
    return "\n".join(lines)


def write_python_symbol_index(
    *,
    instance_root: Path,
    date: str,
    request_id: str,
    symbol_index: PythonSymbolIndex,
) -> dict[str, object]:
    _validate_slug("date", date, _DATE_PATTERN)
    _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)

    rel_dir = f"{INVENTORY_RUNTIME_PREFIX}/{date}/{request_id}"
    out_dir = Path(instance_root) / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    json_rel = f"{rel_dir}/symbol-index.json"
    md_rel = f"{rel_dir}/symbol-index.md"
    json_path = Path(instance_root) / json_rel
    md_path = Path(instance_root) / md_rel

    payload = symbol_index.model_dump(mode="json")
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_symbol_index_markdown(symbol_index), encoding="utf-8")

    return {
        "schema_id": symbol_index.schema_id,
        "json_ref": json_rel,
        "markdown_ref": md_rel,
        "raw_source_content_persisted": symbol_index.raw_source_content_persisted,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }


def build_python_symbol_index(
    repo_root: Path,
    *,
    analysis_scope: str | None = None,
    path_policy: PathPolicy | None = None,
) -> PythonSymbolIndex:
    """Build a deterministic Python AST symbol index for a local repository.

    M16.1 records modules, top-level imports, classes (with nested classes
    and methods), and free functions. Parse errors are out of scope for M16.1
    and will be added as evidence in M16.2.
    """

    inventory = build_codebase_inventory(
        repo_root=repo_root,
        analysis_scope=analysis_scope,
        path_policy=path_policy,
    )

    modules: list[SymbolModule] = []
    parse_errors: list[SymbolParseError] = []
    import_total = 0
    class_total = 0
    function_total = 0
    for rel_path in inventory.files:
        if not rel_path.endswith(".py"):
            continue
        source_path = Path(inventory.repo_root) / rel_path
        try:
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            module = _build_module_symbols(rel_path, source)
        except SyntaxError as exc:
            parse_errors.append(
                SymbolParseError(
                    path=rel_path,
                    line=exc.lineno or 0,
                    column=exc.offset or 0,
                    message=exc.msg or "syntax error",
                )
            )
            continue
        modules.append(module)
        import_total += len(module.imports)
        function_total += len(module.functions)
        for cls in module.classes:
            class_count, method_count = _count_class_symbols(cls)
            class_total += class_count
            function_total += method_count

    modules.sort(key=lambda mod: mod.path)
    parse_errors.sort(key=lambda err: err.path)
    return PythonSymbolIndex(
        repo_root=inventory.repo_root,
        analysis_scope=analysis_scope,
        modules=modules,
        parse_errors=parse_errors,
        module_count=len(modules),
        import_count=import_total,
        class_count=class_total,
        function_count=function_total,
        parse_error_count=len(parse_errors),
        raw_source_content_persisted=False,
    )


class CodebaseScopeProfile(BaseModel):
    """Static contract that names a reviewable scope of the Hisys codebase.

    A scope profile is pure data: it names the scope (`scope_id`), explains
    why it exists (`description`), and lists the repo-relative entry files,
    focused test files, and controlled docs that govern it. M17.1 introduces
    the registry; M17.2 consumes profiles to assemble a scope map from the
    deterministic inventory and symbol-index artifacts. The profile itself
    performs no source content read, no live action, and no mutation.
    """

    schema_id: str = "hisys.codebase.scope_profile"
    scope_id: str
    description: str = ""
    entry_files: list[str] = Field(default_factory=list)
    expected_tests: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)


# Static scope-profile registry. Profiles are stored in scope_id-sorted order
# so list_codebase_scope_profiles() is deterministic without re-sorting at
# call time. Adding a scope requires updating this tuple and the matching
# docs/traceability rows in M17.5.
_CODEBASE_SCOPE_PROFILES: tuple[CodebaseScopeProfile, ...] = (
    CodebaseScopeProfile(
        scope_id="docs-traceability",
        description=(
            "Traceability gate covering the implemented-increment table, the "
            "module-to-controlled-doc map, and the validate_traceability.py "
            "guardrail script that pins every implementation row to a "
            "controlled anchor."
        ),
        entry_files=[
            "scripts/validate_traceability.py",
        ],
        expected_tests=[],
        docs_refs=[
            "docs/traceability/README.md",
        ],
    ),
    CodebaseScopeProfile(
        scope_id="domain-adapter",
        description=(
            "Domain-investigation adapter registry, structured spec records, "
            "three-layer use cases, runtime artifact projection, and the "
            "bridge contract between Hermes domain requests and Hisys "
            "domain results."
        ),
        entry_files=[
            "src/hisys/domain/adapters.py",
            "src/hisys/domain/domain_adapters.py",
            "src/hisys/domain/layers.py",
            "src/hisys/domain/runtime.py",
            "src/hisys/domain/specs.py",
            "src/hisys/domain/use_cases.py",
        ],
        expected_tests=[
            "tests/unit/test_domain_adapter_registry.py",
            "tests/unit/test_domain_bridge_contract.py",
            "tests/unit/test_domain_name_strategy.py",
            "tests/unit/test_domain_postprocessing_guard.py",
            "tests/unit/test_domain_runtime_artifacts.py",
            "tests/unit/test_domain_three_layer_use_cases.py",
            "tests/unit/test_structured_domain_adapter.py",
        ],
        docs_refs=[
            "docs/traceability/README.md",
        ],
    ),
    CodebaseScopeProfile(
        scope_id="runtime-boundary",
        description=(
            "Runtime-boundary writers that persist Hisys artifacts under an "
            "instance-rooted runtime-boundary subtree only, plus the "
            "codebase-analysis inventory and symbol-index foundation that "
            "downstream M17/M18 scope and risk artifacts will consume."
        ),
        entry_files=[
            "src/hisys/audit/writer.py",
            "src/hisys/operations/codebase_analysis.py",
        ],
        expected_tests=[
            "tests/unit/test_codebase_analysis_inventory.py",
            "tests/unit/test_codebase_symbol_index.py",
            "tests/unit/test_domain_runtime_artifacts.py",
        ],
        docs_refs=[
            "docs/public/codebase-analysis.md",
        ],
    ),
)


_CODEBASE_SCOPE_PROFILE_INDEX: dict[str, CodebaseScopeProfile] = {
    profile.scope_id: profile for profile in _CODEBASE_SCOPE_PROFILES
}


def list_codebase_scope_profiles() -> list[CodebaseScopeProfile]:
    """Return the static codebase scope profiles in deterministic order.

    Profiles are returned as independent deep copies so a caller may mutate
    its local list without leaking changes back into the registry contract.
    """

    return [profile.model_copy(deep=True) for profile in _CODEBASE_SCOPE_PROFILES]


def get_codebase_scope_profile(scope_id: str) -> CodebaseScopeProfile:
    """Return one codebase scope profile by ``scope_id`` or raise ``KeyError``.

    Unknown scope IDs fail closed so M17.2..M17.4 consumers never silently
    produce an empty scope map for a typo.
    """

    profile = _CODEBASE_SCOPE_PROFILE_INDEX.get(scope_id)
    if profile is None:
        raise KeyError(f"unknown codebase scope id: {scope_id!r}")
    return profile.model_copy(deep=True)


# A docs ref is treated as a traceability anchor when its path crosses the
# `docs/traceability/` subtree. The downstream M17.3 validation plan and the
# M17.5 examples will rely on this split so a reviewer can find the RTM rows
# linked to a scope without re-walking the docs tree.
_TRACEABILITY_PATH_TOKEN = "docs/traceability/"


class CodebaseScopeMapEntry(BaseModel):
    """Materialized scope view linking a profile to inventory and symbol data.

    Each list field is sorted so the entry has a deterministic shape that
    downstream artifact writers (M17.4) and review summaries (M17.5) can
    serialize without re-sorting.
    """

    schema_id: str = "hisys.codebase.scope_map_entry"
    scope_id: str
    description: str = ""
    files_in_scope: list[str] = Field(default_factory=list)
    missing_entry_files: list[str] = Field(default_factory=list)
    tests_in_scope: list[str] = Field(default_factory=list)
    missing_expected_tests: list[str] = Field(default_factory=list)
    docs_in_scope: list[str] = Field(default_factory=list)
    missing_docs_refs: list[str] = Field(default_factory=list)
    traceability_refs_in_scope: list[str] = Field(default_factory=list)
    modules: list[SymbolModule] = Field(default_factory=list)
    module_count: int = 0
    import_count: int = 0
    class_count: int = 0
    function_count: int = 0
    parse_errors_in_scope: list[SymbolParseError] = Field(default_factory=list)


class CodebaseScopeMap(BaseModel):
    """Top-level scope map produced from a loaded inventory and symbol index.

    The map is pure data over already-loaded artifact records. It performs no
    source content read of its own and inherits the safety invariants of its
    inputs.
    """

    schema_id: str = "hisys.codebase.scope_map"
    repo_root: str
    analysis_scope: str | None = None
    inventory_schema_id: str
    symbol_index_schema_id: str
    scope_entries: list[CodebaseScopeMapEntry] = Field(default_factory=list)
    raw_source_content_persisted: bool = False


def _partition_refs(declared: list[str], present: set[str]) -> tuple[list[str], list[str]]:
    in_scope = sorted(ref for ref in declared if ref in present)
    missing = sorted(ref for ref in declared if ref not in present)
    return in_scope, missing


def _filter_modules_for_scope(
    modules: list[SymbolModule], scope_files: set[str]
) -> list[SymbolModule]:
    return sorted(
        (module for module in modules if module.path in scope_files),
        key=lambda module: module.path,
    )


def _filter_parse_errors_for_scope(
    parse_errors: list[SymbolParseError], scope_files: set[str]
) -> list[SymbolParseError]:
    return sorted(
        (err for err in parse_errors if err.path in scope_files),
        key=lambda err: (err.path, err.line),
    )


def _module_counters(modules: list[SymbolModule]) -> tuple[int, int, int, int]:
    module_count = len(modules)
    import_total = 0
    class_total = 0
    function_total = 0
    for module in modules:
        import_total += len(module.imports)
        function_total += len(module.functions)
        for cls in module.classes:
            class_count, method_count = _count_class_symbols(cls)
            class_total += class_count
            function_total += method_count
    return module_count, import_total, class_total, function_total


def build_codebase_scope_map(
    *,
    inventory: CodebaseInventory,
    symbol_index: PythonSymbolIndex,
    profiles: Iterable[CodebaseScopeProfile] | None = None,
) -> CodebaseScopeMap:
    """Build a deterministic scope map from already-loaded artifact records.

    The function is pure: it does no filesystem walk, no source content read,
    and no live action. Each scope entry partitions the profile's declared
    refs into the subset that exists in the inventory and the subset that is
    missing, projects the matching symbol-index modules and parse errors into
    the entry, and splits traceability refs out of the docs list so reviewers
    can locate the RTM anchor directly.
    """

    if profiles is None:
        active_profiles = list_codebase_scope_profiles()
    else:
        active_profiles = list(profiles)

    inventory_paths = set(inventory.files)

    entries: list[CodebaseScopeMapEntry] = []
    for profile in sorted(active_profiles, key=lambda p: p.scope_id):
        files_in_scope, missing_entry_files = _partition_refs(
            profile.entry_files, inventory_paths
        )
        tests_in_scope, missing_expected_tests = _partition_refs(
            profile.expected_tests, inventory_paths
        )
        docs_in_scope, missing_docs_refs = _partition_refs(
            profile.docs_refs, inventory_paths
        )
        traceability_refs = sorted(
            ref for ref in docs_in_scope if _TRACEABILITY_PATH_TOKEN in ref
        )

        scope_files_set = set(files_in_scope)
        modules = _filter_modules_for_scope(symbol_index.modules, scope_files_set)
        parse_errors = _filter_parse_errors_for_scope(
            symbol_index.parse_errors, scope_files_set
        )
        module_count, import_total, class_total, function_total = _module_counters(
            modules
        )

        entries.append(
            CodebaseScopeMapEntry(
                scope_id=profile.scope_id,
                description=profile.description,
                files_in_scope=files_in_scope,
                missing_entry_files=missing_entry_files,
                tests_in_scope=tests_in_scope,
                missing_expected_tests=missing_expected_tests,
                docs_in_scope=docs_in_scope,
                missing_docs_refs=missing_docs_refs,
                traceability_refs_in_scope=traceability_refs,
                modules=modules,
                module_count=module_count,
                import_count=import_total,
                class_count=class_total,
                function_count=function_total,
                parse_errors_in_scope=parse_errors,
            )
        )

    return CodebaseScopeMap(
        repo_root=inventory.repo_root,
        analysis_scope=inventory.analysis_scope,
        inventory_schema_id=inventory.schema_id,
        symbol_index_schema_id=symbol_index.schema_id,
        scope_entries=entries,
        raw_source_content_persisted=False,
    )


# Scope IDs whose validation rationale crosses many subsystems. The synthesis
# rule escalates these scopes to the full pytest suite even when their
# focused tests pass, because focused coverage cannot represent the surface
# they protect (e.g. every runtime-boundary writer is observed by callers in
# many other test files).
_CROSS_CUTTING_SCOPE_IDS: frozenset[str] = frozenset({"runtime-boundary"})


class ValidationPlanCommand(BaseModel):
    """One concrete validation command in a scope's validation plan.

    `argv` is the command tokens (no shell), `kind` is one of the controlled
    kinds, and `purpose` is a short human-readable explanation that flows
    into the M17.4 writer output.
    """

    schema_id: str = "hisys.codebase.validation_plan_command"
    kind: str
    argv: list[str]
    purpose: str


class ScopeValidationPlan(BaseModel):
    schema_id: str = "hisys.codebase.scope_validation_plan"
    scope_id: str
    commands: list[ValidationPlanCommand] = Field(default_factory=list)
    requires_full_suite: bool = False


class CodebaseValidationPlan(BaseModel):
    schema_id: str = "hisys.codebase.validation_plan"
    scope_plans: list[ScopeValidationPlan] = Field(default_factory=list)
    raw_source_content_persisted: bool = False


def _plan_for_scope_entry(entry: CodebaseScopeMapEntry) -> ScopeValidationPlan:
    has_drift = bool(entry.missing_entry_files) or bool(entry.missing_expected_tests)
    cross_cutting = entry.scope_id in _CROSS_CUTTING_SCOPE_IDS
    requires_full_suite = has_drift or cross_cutting

    commands: list[ValidationPlanCommand] = []

    commands.append(
        ValidationPlanCommand(
            kind="git_diff_check",
            argv=["git", "diff", "--check"],
            purpose="reject whitespace and conflict markers before commit",
        )
    )
    commands.append(
        ValidationPlanCommand(
            kind="traceability",
            argv=["python3", "scripts/validate_traceability.py"],
            purpose="re-validate controlled-document traceability for the scope",
        )
    )

    if entry.tests_in_scope:
        commands.append(
            ValidationPlanCommand(
                kind="focused_tests",
                argv=[
                    "python3",
                    "-m",
                    "pytest",
                    *entry.tests_in_scope,
                    "-q",
                ],
                purpose="run the focused pytest suite that governs this scope",
            )
        )

    # Secret scan is appropriate whenever a scope owns code or docs; an
    # entirely empty scope (no inventory hits) skips it to keep the plan
    # honest about what it actually touches.
    if entry.files_in_scope or entry.docs_in_scope:
        commands.append(
            ValidationPlanCommand(
                kind="secret_scan",
                argv=["python3", "scripts/scan_secrets.py"],
                purpose="scan touched files for secret-like content",
            )
        )

    if requires_full_suite:
        commands.append(
            ValidationPlanCommand(
                kind="full_tests",
                argv=["python3", "-m", "pytest", "-q"],
                purpose=(
                    "run the full pytest suite to cover scope drift or "
                    "cross-cutting surface that the focused gate cannot"
                ),
            )
        )

    commands.sort(key=lambda cmd: cmd.kind)

    return ScopeValidationPlan(
        scope_id=entry.scope_id,
        commands=commands,
        requires_full_suite=requires_full_suite,
    )


class RiskBoundaryFinding(BaseModel):
    """One AST call-site that conservatively looks like a boundary crossing.

    A finding is review evidence, not a vulnerability verdict.
    `action_authorized=false` is asserted at the finding level so a
    reviewer can grep findings without inferring authority from absence.
    """

    schema_id: str = "hisys.codebase.risk_boundary_finding"
    category: str
    path: str
    line: int
    signal: str
    action_authorized: bool = False


class CodebaseRiskScan(BaseModel):
    schema_id: str = "hisys.codebase.risk_scan"
    repo_root: str
    analysis_scope: str | None = None
    findings: list[RiskBoundaryFinding] = Field(default_factory=list)
    finding_count: int = 0
    category_counts: dict[str, int] = Field(default_factory=dict)
    parse_errors: list[SymbolParseError] = Field(default_factory=list)
    parse_error_count: int = 0
    raw_source_content_persisted: bool = False
    action_authorized: bool = False


# Conservative AST signal rules for M18.1. Each rule maps a module prefix
# (the `value.id` of an `ast.Attribute`) plus an optional set of attribute
# names to a category + canonical signal label. M18.2..M18.3 will extend
# this with runtime-boundary-writer separation and model/LLM categories.
_NETWORK_MODULES: dict[str, set[str] | None] = {
    "requests": {"get", "post", "put", "delete", "head", "patch", "options", "request"},
    "httpx": None,  # any attribute call on the imported `httpx` module
    "urllib3": None,
}
_BROWSER_MODULES: dict[str, set[str] | None] = {
    "webbrowser": {"open", "open_new", "open_new_tab"},
}
_SUBPROCESS_MODULES: dict[str, set[str] | None] = {
    "subprocess": {"run", "Popen", "call", "check_call", "check_output", "getoutput"},
    "os": {"system", "spawnl", "spawnle", "spawnlp", "spawnv", "spawnve", "spawnvp"},
}
# Method names on any receiver that conservatively imply filesystem
# mutation. The receiver expression is not analyzed deeply (it could be a
# `Path`, a file-like, or anything else); the signal label embeds
# `<receiver>` to make that ambiguity explicit in the finding.
_FILESYSTEM_MUTATION_METHODS: frozenset[str] = frozenset(
    {"write_text", "write_bytes"}
)

# Marker token that, when present anywhere in a module's string literals,
# reclassifies that module's `.write_text`/`.write_bytes` calls as a
# runtime-boundary artifact write (not a generic filesystem mutation). The
# token mirrors the controlled `runtime-boundary/...` artifact subtree the
# Hisys writers use; it keeps the rule deterministic and AST-only.
_RUNTIME_BOUNDARY_LITERAL_TOKEN = "runtime-boundary"

# Module-level signals that mark a Python file as crossing a model/LLM
# boundary. The tokens cover external API endpoints and local-LLM server
# paths so a `requests.post`/`httpx.post` call in such a module is
# reclassified as a model/LLM boundary rather than a generic network call.
_MODEL_ENDPOINT_LITERAL_TOKENS: tuple[str, ...] = (
    "/v1/chat/completions",
    "/v1/completions",
    "/v1/messages",
    "/v1/embeddings",
)

# Module-level signals that mark a Python file as containing generated or
# fabricated evidence that must be reviewed as ByeSys. The tokens are the
# canonical Hisys markers used in policy docs and reviewer prose.
_BYESYS_LITERAL_TOKENS: tuple[str, ...] = (
    "ByeSys",
    "byesys_generated",
)

# Modules whose attribute-chain calls are unambiguous model/LLM crossings.
# `None` means any attribute call on the imported module counts; the
# scanner walks the full `ast.Attribute` chain so calls like
# `openai.ChatCompletion.create(...)` and `client.messages.create(...)`
# (where `client = anthropic.Anthropic()`) are both detected.
_MODEL_LLM_MODULES: dict[str, set[str] | None] = {
    "openai": None,
    "anthropic": None,
}


def _module_has_literal_token(tree: ast.AST, token: str) -> bool:
    """Return True when any string literal in `tree` contains ``token``."""

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if token in node.value:
                return True
    return False


def _module_has_any_literal_token(tree: ast.AST, tokens: tuple[str, ...]) -> bool:
    return any(_module_has_literal_token(tree, token) for token in tokens)


def _byesys_literal_findings(rel_path: str, tree: ast.AST) -> list[RiskBoundaryFinding]:
    """Return one finding per string literal that contains a ByeSys marker."""

    findings: list[RiskBoundaryFinding] = []
    seen: set[tuple[int, str]] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        value = node.value
        for token in _BYESYS_LITERAL_TOKENS:
            if token in value:
                line = getattr(node, "lineno", 0) or 0
                # Truncate the signal to keep the finding line-readable
                # without leaking long fabricated content.
                excerpt = value.replace("\n", " ").strip()
                if len(excerpt) > 64:
                    excerpt = excerpt[:61] + "..."
                key = (line, excerpt)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    RiskBoundaryFinding(
                        category="byesys_generated_evidence",
                        path=rel_path,
                        line=line,
                        signal=f"byesys_literal:{excerpt}",
                    )
                )
                break
    return findings


def _attribute_chain(expr: ast.AST) -> tuple[str, list[str]] | None:
    """Walk an attribute chain and return (root_name, [attr, ...]) or None.

    For ``openai.ChatCompletion.create``, returns ``("openai",
    ["ChatCompletion", "create"])``. For ``client.messages.create``,
    returns ``("client", ["messages", "create"])``.
    """

    parts: list[str] = []
    cur: ast.AST = expr
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        return cur.id, list(reversed(parts))
    return None


def _classify_attribute_call(
    callee: ast.Attribute,
    *,
    runtime_boundary_module: bool,
    model_endpoint_module: bool,
) -> tuple[str, str] | None:
    """Return (category, signal) for a recognized boundary call, or None."""

    attr_name = callee.attr
    receiver = callee.value

    # Attribute chains rooted at openai/anthropic mark unambiguous model
    # boundary calls (e.g., ``openai.ChatCompletion.create(...)``).
    chain = _attribute_chain(callee)
    if chain is not None:
        root_id, attr_parts = chain
        if root_id in _MODEL_LLM_MODULES and attr_parts:
            allowed = _MODEL_LLM_MODULES[root_id]
            if allowed is None or attr_parts[0] in allowed:
                return (
                    "model_llm_boundary",
                    f"{root_id}.{'.'.join(attr_parts)}",
                )

    if isinstance(receiver, ast.Name):
        receiver_id = receiver.id
        for module, allowed in _NETWORK_MODULES.items():
            if receiver_id == module and (allowed is None or attr_name in allowed):
                category = (
                    "model_llm_boundary"
                    if model_endpoint_module
                    else "network_external_call"
                )
                return category, f"{module}.{attr_name}"
        for module, allowed in _BROWSER_MODULES.items():
            if receiver_id == module and (allowed is None or attr_name in allowed):
                return "browser_external_call", f"{module}.{attr_name}"
        for module, allowed in _SUBPROCESS_MODULES.items():
            if receiver_id == module and (allowed is None or attr_name in allowed):
                return "subprocess_execution", f"{module}.{attr_name}"

    if attr_name in _FILESYSTEM_MUTATION_METHODS:
        category = (
            "runtime_boundary_artifact_write"
            if runtime_boundary_module
            else "filesystem_mutation"
        )
        return category, f"<receiver>.{attr_name}"

    return None


def _scan_module_findings(
    rel_path: str, source: str
) -> tuple[list[RiskBoundaryFinding], SymbolParseError | None]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [], SymbolParseError(
            path=rel_path,
            line=exc.lineno or 0,
            column=exc.offset or 0,
            message=exc.msg or "syntax error",
        )

    runtime_boundary_module = _module_has_literal_token(
        tree, _RUNTIME_BOUNDARY_LITERAL_TOKEN
    )
    model_endpoint_module = _module_has_any_literal_token(
        tree, _MODEL_ENDPOINT_LITERAL_TOKENS
    )
    findings: list[RiskBoundaryFinding] = []
    findings.extend(_byesys_literal_findings(rel_path, tree))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        if not isinstance(callee, ast.Attribute):
            continue
        classified = _classify_attribute_call(
            callee,
            runtime_boundary_module=runtime_boundary_module,
            model_endpoint_module=model_endpoint_module,
        )
        if classified is None:
            continue
        category, signal = classified
        findings.append(
            RiskBoundaryFinding(
                category=category,
                path=rel_path,
                line=node.lineno,
                signal=signal,
            )
        )
    return findings, None


def scan_codebase_risk_boundaries(
    *,
    repo_root: Path,
    analysis_scope: str | None = None,
    path_policy: PathPolicy | None = None,
) -> CodebaseRiskScan:
    """Scan a local repository for boundary-crossing call sites.

    The scanner is conservative and AST-only. It makes no live call and
    persists no raw source content. Each finding is review evidence, not a
    vulnerability verdict — `action_authorized=false` at both the scan and
    finding levels.
    """

    inventory = build_codebase_inventory(
        repo_root=repo_root,
        analysis_scope=analysis_scope,
        path_policy=path_policy,
    )

    findings: list[RiskBoundaryFinding] = []
    parse_errors: list[SymbolParseError] = []
    for rel_path in inventory.files:
        if not rel_path.endswith(".py"):
            continue
        source_path = Path(inventory.repo_root) / rel_path
        try:
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        file_findings, parse_error = _scan_module_findings(rel_path, source)
        if parse_error is not None:
            parse_errors.append(parse_error)
            continue
        findings.extend(file_findings)

    findings.sort(key=lambda f: (f.path, f.line, f.category, f.signal))
    parse_errors.sort(key=lambda err: (err.path, err.line))

    category_counts: dict[str, int] = {}
    for finding in findings:
        category_counts[finding.category] = category_counts.get(finding.category, 0) + 1

    return CodebaseRiskScan(
        repo_root=inventory.repo_root,
        analysis_scope=analysis_scope,
        findings=findings,
        finding_count=len(findings),
        category_counts=dict(sorted(category_counts.items())),
        parse_errors=parse_errors,
        parse_error_count=len(parse_errors),
        raw_source_content_persisted=False,
        action_authorized=False,
    )


def _render_risk_scan_markdown(scan: CodebaseRiskScan) -> str:
    lines: list[str] = []
    lines.append(f"# Codebase Risk-Boundary Scan — {scan.schema_id}")
    lines.append("")
    lines.append(
        "Findings are review evidence, not vulnerability or action verdicts. "
        "`action_authorized=false` is asserted at both the scan and finding "
        "level. The scanner performs no live call, no source content "
        "persistence, and no mutation."
    )
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(f"- repo_root: `{scan.repo_root}`")
    if scan.analysis_scope is not None:
        lines.append(f"- analysis_scope: `{scan.analysis_scope}`")
    else:
        lines.append("- analysis_scope: (whole repo)")
    lines.append(f"- finding_count: {scan.finding_count}")
    lines.append(f"- raw_source_content_persisted: {scan.raw_source_content_persisted}")
    lines.append(f"- action_authorized: {scan.action_authorized}")
    lines.append("")
    lines.append("## Category counts")
    lines.append("")
    if scan.category_counts:
        for category, count in scan.category_counts.items():
            lines.append(f"- `{category}`: {count}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Parse errors")
    lines.append("")
    if scan.parse_errors:
        for err in scan.parse_errors:
            lines.append(
                f"- `{err.path}` line {err.line}: {err.message}"
            )
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if scan.findings:
        for finding in scan.findings:
            lines.append(
                f"- `{finding.path}` line {finding.line} "
                f"[{finding.category}] — {finding.signal} "
                f"(action_authorized={finding.action_authorized})"
            )
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


RISK_SCAN_JSON_FILENAME = "risk-scan.json"
RISK_SCAN_MARKDOWN_FILENAME = "risk-scan.md"


def write_codebase_risk_scan(
    *,
    instance_root: Path,
    date: str,
    request_id: str,
    scan: CodebaseRiskScan,
) -> dict[str, object]:
    """Persist a risk-boundary scan as JSON + Markdown under the instance root.

    The Markdown rendering explicitly states the findings are review
    evidence rather than vulnerability verdicts so a reviewer cannot
    misread the artifact as an authorization signal.
    """

    _validate_slug("date", date, _DATE_PATTERN)
    _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)

    rel_dir = f"{INVENTORY_RUNTIME_PREFIX}/{date}/{request_id}"
    out_dir = Path(instance_root) / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    json_rel = f"{rel_dir}/{RISK_SCAN_JSON_FILENAME}"
    md_rel = f"{rel_dir}/{RISK_SCAN_MARKDOWN_FILENAME}"
    json_path = Path(instance_root) / json_rel
    md_path = Path(instance_root) / md_rel

    payload = scan.model_dump(mode="json")
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_risk_scan_markdown(scan), encoding="utf-8")

    return {
        "schema_id": scan.schema_id,
        "json_ref": json_rel,
        "markdown_ref": md_rel,
        "raw_source_content_persisted": scan.raw_source_content_persisted,
        "action_authorized": scan.action_authorized,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }


def resolve_instance_runtime_ref(
    *, instance_root: Path, relative_ref: str
) -> Path:
    """Return an absolute path inside ``instance_root`` for a safe local ref.

    The function rejects empty refs, absolute paths, ``..`` traversal
    segments, and symlinks whose real target escapes the instance root. It
    is the single chokepoint M17.4+ consumers use before reading a caller-
    supplied artifact path, so an unsafe ref cannot reach the filesystem.
    """

    if not relative_ref:
        raise ValueError("instance runtime ref must be a non-empty string")
    if relative_ref.startswith("/"):
        raise ValueError(
            f"instance runtime ref must be relative, got absolute: {relative_ref!r}"
        )
    parts = relative_ref.replace("\\", "/").split("/")
    if any(part in {"", ".."} for part in parts):
        raise ValueError(
            f"instance runtime ref contains traversal segments: {relative_ref!r}"
        )

    instance_real = Path(os.path.realpath(instance_root))
    candidate = Path(os.path.realpath(instance_root / relative_ref))
    try:
        candidate.relative_to(instance_real)
    except ValueError as exc:
        raise ValueError(
            f"instance runtime ref resolves outside instance root: {relative_ref!r}"
        ) from exc
    return candidate


def _render_scope_map_markdown(
    scope_map: CodebaseScopeMap, validation_plan: CodebaseValidationPlan
) -> str:
    lines: list[str] = []
    lines.append(f"# Codebase Scope Map — {scope_map.schema_id}")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(f"- repo_root: `{scope_map.repo_root}`")
    if scope_map.analysis_scope is not None:
        lines.append(f"- analysis_scope: `{scope_map.analysis_scope}`")
    else:
        lines.append("- analysis_scope: (whole repo)")
    lines.append(f"- inventory_schema_id: `{scope_map.inventory_schema_id}`")
    lines.append(f"- symbol_index_schema_id: `{scope_map.symbol_index_schema_id}`")
    lines.append(
        f"- raw_source_content_persisted: {scope_map.raw_source_content_persisted}"
    )
    lines.append("")
    plan_by_scope = {sp.scope_id: sp for sp in validation_plan.scope_plans}
    for entry in scope_map.scope_entries:
        lines.append(f"## Scope `{entry.scope_id}`")
        lines.append("")
        if entry.description:
            lines.append(entry.description)
            lines.append("")
        lines.append(
            f"- module_count: {entry.module_count}, "
            f"function_count: {entry.function_count}, "
            f"class_count: {entry.class_count}, "
            f"import_count: {entry.import_count}"
        )
        lines.append("- Files in scope:")
        if entry.files_in_scope:
            for path in entry.files_in_scope:
                lines.append(f"  - `{path}`")
        else:
            lines.append("  - (none)")
        if entry.missing_entry_files:
            lines.append("- Missing entry files:")
            for path in entry.missing_entry_files:
                lines.append(f"  - `{path}`")
        lines.append("- Tests in scope:")
        if entry.tests_in_scope:
            for path in entry.tests_in_scope:
                lines.append(f"  - `{path}`")
        else:
            lines.append("  - (none)")
        if entry.missing_expected_tests:
            lines.append("- Missing expected tests:")
            for path in entry.missing_expected_tests:
                lines.append(f"  - `{path}`")
        lines.append("- Docs in scope:")
        if entry.docs_in_scope:
            for path in entry.docs_in_scope:
                lines.append(f"  - `{path}`")
        else:
            lines.append("  - (none)")
        if entry.traceability_refs_in_scope:
            lines.append("- Traceability refs:")
            for path in entry.traceability_refs_in_scope:
                lines.append(f"  - `{path}`")
        if entry.parse_errors_in_scope:
            lines.append("- Parse errors:")
            for err in entry.parse_errors_in_scope:
                lines.append(
                    f"  - `{err.path}` line {err.line}: {err.message}"
                )
        lines.append("")
        plan = plan_by_scope.get(entry.scope_id)
        if plan is not None:
            lines.append(
                f"### Validation plan for `{entry.scope_id}` "
                f"(requires_full_suite={plan.requires_full_suite})"
            )
            lines.append("")
            for cmd in plan.commands:
                argv = " ".join(cmd.argv)
                lines.append(f"- {cmd.kind}: `{argv}` — {cmd.purpose}")
            lines.append("")
    return "\n".join(lines)


SCOPE_MAP_ARTIFACT_FILENAME = "scope-map.json"
SCOPE_MAP_MARKDOWN_FILENAME = "scope-map.md"


def write_codebase_scope_map(
    *,
    instance_root: Path,
    date: str,
    request_id: str,
    scope_map: CodebaseScopeMap,
    validation_plan: CodebaseValidationPlan,
) -> dict[str, object]:
    """Persist a scope map and matching validation plan as JSON + Markdown.

    Both artifacts are written under the inventory runtime-boundary subtree
    so a downstream review CLI can locate them next to the inventory and
    symbol-index that produced them.
    """

    _validate_slug("date", date, _DATE_PATTERN)
    _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)

    rel_dir = f"{INVENTORY_RUNTIME_PREFIX}/{date}/{request_id}"
    out_dir = Path(instance_root) / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    json_rel = f"{rel_dir}/{SCOPE_MAP_ARTIFACT_FILENAME}"
    md_rel = f"{rel_dir}/{SCOPE_MAP_MARKDOWN_FILENAME}"
    json_path = Path(instance_root) / json_rel
    md_path = Path(instance_root) / md_rel

    payload = {
        "scope_map": scope_map.model_dump(mode="json"),
        "validation_plan": validation_plan.model_dump(mode="json"),
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        _render_scope_map_markdown(scope_map, validation_plan), encoding="utf-8"
    )

    return {
        "schema_id": scope_map.schema_id,
        "validation_plan_schema_id": validation_plan.schema_id,
        "json_ref": json_rel,
        "markdown_ref": md_rel,
        "raw_source_content_persisted": scope_map.raw_source_content_persisted,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }


def build_codebase_validation_plan(
    scope_map: CodebaseScopeMap,
) -> CodebaseValidationPlan:
    """Synthesize a deterministic validation plan from a scope map.

    The plan never executes commands and never reads source content. It is
    pure data that the M17.4 writer can persist and a human reviewer can run.
    """

    scope_plans = [_plan_for_scope_entry(entry) for entry in scope_map.scope_entries]
    return CodebaseValidationPlan(
        scope_plans=scope_plans,
        raw_source_content_persisted=False,
    )


# Allowed decision values for the codebase source-inspection reviewer.
# Per ralph.md Milestone M19, the reviewer must not adopt `approved`,
# `safe_to_deploy`, or `ready_for_live_action`; those would cross the no-
# live-action boundary the Hisys domain adapter protects.
CodebaseSourceInspectionDecisionValue = Literal[
    "complete_for_human_review",
    "blocked_needs_more_evidence",
]


class CodebaseSourceInspectionDecision(BaseModel):
    """Pure review verdict over the codebase-analysis four-file bundle.

    The reviewer never executes commands, never reads source content, and
    never authorizes a live action. The safety envelope below repeats the
    invariants the upstream artifact writers already assert so a reviewer
    grepping a persisted decision sees the boundary at the top level.
    """

    schema_id: str = "hisys.codebase.source_inspection_decision"
    decision: CodebaseSourceInspectionDecisionValue = (
        "blocked_needs_more_evidence"
    )
    missing_evidence: list[str] = Field(default_factory=list)
    validation_findings: list[str] = Field(default_factory=list)
    unresolved_blockers: list[str] = Field(default_factory=list)
    raw_source_content_persisted: bool = False
    action_authorized: bool = False
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_or_live_action_approved: bool = False


# Canonical names of the four artifacts the M19 reviewer expects. The
# order here is not a presentation order — the reviewer sorts the missing
# list before emitting it so downstream writers see a deterministic shape.
_REQUIRED_ARTIFACT_NAMES: tuple[str, ...] = (
    "inventory",
    "symbol_index",
    "scope_map",
    "validation_plan",
    "risk_scan",
)


class CodebaseReviewBundle(BaseModel):
    """Loaded four-file codebase-analysis bundle ready for review.

    The bundle is the in-memory form of the artifacts written by
    `write_codebase_inventory`, `write_python_symbol_index`,
    `write_codebase_scope_map`, and `write_codebase_risk_scan`. The scope-
    map JSON file persists both the scope map and its matching validation
    plan together; the loader unwraps that pair so a downstream reviewer
    sees five typed records.
    """

    schema_id: str = "hisys.codebase.review_bundle"
    inventory: CodebaseInventory
    symbol_index: PythonSymbolIndex
    scope_map: CodebaseScopeMap
    validation_plan: CodebaseValidationPlan
    risk_scan: CodebaseRiskScan
    raw_source_content_persisted: bool = False
    action_authorized: bool = False


def load_codebase_review_bundle(
    *,
    instance_root: Path,
    inventory_ref: str,
    symbol_index_ref: str,
    scope_map_ref: str,
    risk_scan_ref: str,
) -> CodebaseReviewBundle:
    """Resolve, read, and validate the four codebase-analysis artifact files.

    Every caller-supplied ref passes through `resolve_instance_runtime_ref`
    so absolute paths, empty refs, `..` traversal segments, and symlinks
    that escape the instance root fail closed before any read. The scope-
    map JSON is the `{scope_map, validation_plan}` wrapper the M17.4
    writer produces; the loader unpacks both records from that file.
    """

    inv_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=inventory_ref
    )
    sym_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=symbol_index_ref
    )
    scope_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=scope_map_ref
    )
    risk_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=risk_scan_ref
    )

    inventory = CodebaseInventory.model_validate(
        json.loads(inv_path.read_text(encoding="utf-8"))
    )
    symbol_index = PythonSymbolIndex.model_validate(
        json.loads(sym_path.read_text(encoding="utf-8"))
    )
    scope_payload = json.loads(scope_path.read_text(encoding="utf-8"))
    if not isinstance(scope_payload, dict):
        raise ValueError(
            f"scope-map artifact at {scope_map_ref!r} is not a JSON object"
        )
    if "scope_map" not in scope_payload or "validation_plan" not in scope_payload:
        raise ValueError(
            f"scope-map artifact at {scope_map_ref!r} must contain "
            "'scope_map' and 'validation_plan' keys"
        )
    scope_map = CodebaseScopeMap.model_validate(scope_payload["scope_map"])
    validation_plan = CodebaseValidationPlan.model_validate(
        scope_payload["validation_plan"]
    )
    risk_scan = CodebaseRiskScan.model_validate(
        json.loads(risk_path.read_text(encoding="utf-8"))
    )

    return CodebaseReviewBundle(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=scope_map,
        validation_plan=validation_plan,
        risk_scan=risk_scan,
    )


SOURCE_INSPECTION_DECISION_JSON_FILENAME = "source-inspection-decision.json"
SOURCE_INSPECTION_DECISION_MARKDOWN_FILENAME = "source-inspection-decision.md"


def _render_source_inspection_decision_markdown(
    decision: CodebaseSourceInspectionDecision,
) -> str:
    lines: list[str] = []
    lines.append(
        f"# Codebase Source-Inspection Decision — {decision.schema_id}"
    )
    lines.append("")
    lines.append(
        "This decision packet is review evidence, not an authorization. "
        "Allowed decision values are `complete_for_human_review` and "
        "`blocked_needs_more_evidence`; `approved`, `safe_to_deploy`, and "
        "`ready_for_live_action` are explicitly out of scope for this packet."
    )
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- decision: `{decision.decision}`")
    lines.append(
        f"- raw_source_content_persisted: {decision.raw_source_content_persisted}"
    )
    lines.append(f"- action_authorized: {decision.action_authorized}")
    lines.append(f"- external_call_made: {decision.external_call_made}")
    lines.append(f"- mutation_performed: {decision.mutation_performed}")
    lines.append(
        "- publication_or_live_action_approved: "
        f"{decision.publication_or_live_action_approved}"
    )
    lines.append("")
    lines.append("## Missing evidence")
    lines.append("")
    if decision.missing_evidence:
        for name in decision.missing_evidence:
            lines.append(f"- `{name}`")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Validation findings")
    lines.append("")
    if decision.validation_findings:
        for finding in decision.validation_findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Unresolved blockers")
    lines.append("")
    if decision.unresolved_blockers:
        for blocker in decision.unresolved_blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def write_codebase_source_inspection_decision(
    *,
    instance_root: Path,
    date: str,
    request_id: str,
    decision: CodebaseSourceInspectionDecision,
) -> dict[str, object]:
    """Persist a codebase source-inspection decision as JSON + Markdown.

    The artifact joins the same four-file runtime-boundary bundle the M15..M18
    writers produce under
    `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/`. The
    Markdown preamble explicitly states the artifact is review evidence and
    enumerates the two allowed decision values so a reviewer reading the
    artifact in isolation cannot misread it as an authorization signal.
    """

    _validate_slug("date", date, _DATE_PATTERN)
    _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)

    rel_dir = f"{INVENTORY_RUNTIME_PREFIX}/{date}/{request_id}"
    out_dir = Path(instance_root) / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    json_rel = f"{rel_dir}/{SOURCE_INSPECTION_DECISION_JSON_FILENAME}"
    md_rel = f"{rel_dir}/{SOURCE_INSPECTION_DECISION_MARKDOWN_FILENAME}"
    json_path = Path(instance_root) / json_rel
    md_path = Path(instance_root) / md_rel

    payload = decision.model_dump(mode="json")
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        _render_source_inspection_decision_markdown(decision), encoding="utf-8"
    )

    return {
        "schema_id": decision.schema_id,
        "decision": decision.decision,
        "json_ref": json_rel,
        "markdown_ref": md_rel,
        "raw_source_content_persisted": decision.raw_source_content_persisted,
        "action_authorized": decision.action_authorized,
        "external_call_made": decision.external_call_made,
        "mutation_performed": decision.mutation_performed,
        "publication_or_live_action_approved": (
            decision.publication_or_live_action_approved
        ),
    }


def _aggregate_validation_findings(
    *,
    inventory: CodebaseInventory | None,
    symbol_index: PythonSymbolIndex | None,
    scope_map: CodebaseScopeMap | None,
    validation_plan: CodebaseValidationPlan | None,
    risk_scan: CodebaseRiskScan | None,
) -> list[str]:
    """Collect consistency findings across the loaded artifact records.

    Each entry is a short, grep-friendly string keyed by the field it
    flagged. A consistency check that depends on a missing artifact is
    skipped — the missing-evidence list is the dedicated channel for that
    failure mode so a reviewer is not double-charged.
    """

    findings: list[str] = []

    raw_persist_checks: tuple[tuple[str, BaseModel | None], ...] = (
        ("inventory", inventory),
        ("symbol_index", symbol_index),
        ("scope_map", scope_map),
        ("validation_plan", validation_plan),
        ("risk_scan", risk_scan),
    )
    for name, record in raw_persist_checks:
        if record is None:
            continue
        if getattr(record, "raw_source_content_persisted", False):
            findings.append(
                f"{name}.raw_source_content_persisted=true; "
                "must remain false for review-evidence artifacts"
            )

    if risk_scan is not None and risk_scan.action_authorized:
        findings.append(
            "risk_scan.action_authorized=true; "
            "risk-boundary scans are review evidence, not authorizations"
        )

    if risk_scan is not None:
        for finding in risk_scan.findings:
            if finding.action_authorized:
                findings.append(
                    "risk_boundary_finding.action_authorized=true at "
                    f"{finding.path}:{finding.line} ({finding.signal}); "
                    "findings must remain unauthorized review evidence"
                )

    if scope_map is not None and inventory is not None:
        if scope_map.inventory_schema_id != inventory.schema_id:
            findings.append(
                "scope_map.inventory_schema_id "
                f"{scope_map.inventory_schema_id!r} does not match "
                f"inventory.schema_id {inventory.schema_id!r}"
            )

    if scope_map is not None and symbol_index is not None:
        if scope_map.symbol_index_schema_id != symbol_index.schema_id:
            findings.append(
                "scope_map.symbol_index_schema_id "
                f"{scope_map.symbol_index_schema_id!r} does not match "
                f"symbol_index.schema_id {symbol_index.schema_id!r}"
            )

    return sorted(findings)


def review_codebase_source_inspection(
    *,
    inventory: CodebaseInventory | None,
    symbol_index: PythonSymbolIndex | None,
    scope_map: CodebaseScopeMap | None,
    validation_plan: CodebaseValidationPlan | None,
    risk_scan: CodebaseRiskScan | None,
    unresolved_blockers: Iterable[str] | None = None,
) -> CodebaseSourceInspectionDecision:
    """Decide whether the codebase-analysis bundle is complete for human review.

    The function is pure: it inspects already-loaded artifact records and
    returns a `CodebaseSourceInspectionDecision`. It does no filesystem
    read, no source content read, and no live action. M19.1 covered the
    missing-artifact case. M19.2 adds full-bundle consistency checks that
    populate `validation_findings` and downgrade the decision to
    `blocked_needs_more_evidence` when a cross-record safety invariant or
    schema-id contract fails.
    """

    artifact_by_name: dict[str, BaseModel | None] = {
        "inventory": inventory,
        "symbol_index": symbol_index,
        "scope_map": scope_map,
        "validation_plan": validation_plan,
        "risk_scan": risk_scan,
    }
    missing = sorted(
        name for name in _REQUIRED_ARTIFACT_NAMES if artifact_by_name[name] is None
    )

    blockers = [blocker for blocker in (unresolved_blockers or []) if blocker]

    validation_findings = _aggregate_validation_findings(
        inventory=inventory,
        symbol_index=symbol_index,
        scope_map=scope_map,
        validation_plan=validation_plan,
        risk_scan=risk_scan,
    )

    if missing or blockers or validation_findings:
        decision_value: CodebaseSourceInspectionDecisionValue = (
            "blocked_needs_more_evidence"
        )
    else:
        decision_value = "complete_for_human_review"

    return CodebaseSourceInspectionDecision(
        decision=decision_value,
        missing_evidence=missing,
        validation_findings=validation_findings,
        unresolved_blockers=blockers,
    )


__all__ = [
    "CodebaseInventory",
    "CodebaseReviewBundle",
    "CodebaseRiskScan",
    "CodebaseScopeMap",
    "CodebaseScopeMapEntry",
    "CodebaseScopeProfile",
    "CodebaseSourceInspectionDecision",
    "CodebaseSourceInspectionDecisionValue",
    "CodebaseValidationPlan",
    "DEFAULT_EXCLUDED_DIRS",
    "DEFAULT_GENERATED_MARKERS",
    "DEFAULT_GENERATED_SUFFIXES",
    "INVENTORY_RUNTIME_PREFIX",
    "PathPolicy",
    "PythonSymbolIndex",
    "RISK_SCAN_JSON_FILENAME",
    "RISK_SCAN_MARKDOWN_FILENAME",
    "RiskBoundaryFinding",
    "SCOPE_MAP_ARTIFACT_FILENAME",
    "SCOPE_MAP_MARKDOWN_FILENAME",
    "SOURCE_INSPECTION_DECISION_JSON_FILENAME",
    "SOURCE_INSPECTION_DECISION_MARKDOWN_FILENAME",
    "ScopeValidationPlan",
    "SkippedPath",
    "SymbolClass",
    "SymbolFunction",
    "SymbolImport",
    "SymbolModule",
    "SymbolParseError",
    "ValidationPlanCommand",
    "build_codebase_inventory",
    "build_codebase_scope_map",
    "build_codebase_validation_plan",
    "build_python_symbol_index",
    "get_codebase_scope_profile",
    "list_codebase_scope_profiles",
    "load_codebase_review_bundle",
    "resolve_instance_runtime_ref",
    "review_codebase_source_inspection",
    "scan_codebase_risk_boundaries",
    "write_codebase_inventory",
    "write_codebase_risk_scan",
    "write_codebase_scope_map",
    "write_codebase_source_inspection_decision",
    "write_python_symbol_index",
]
