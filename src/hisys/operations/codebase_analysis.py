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


__all__ = [
    "CodebaseInventory",
    "CodebaseScopeMap",
    "CodebaseScopeMapEntry",
    "CodebaseScopeProfile",
    "DEFAULT_EXCLUDED_DIRS",
    "DEFAULT_GENERATED_MARKERS",
    "DEFAULT_GENERATED_SUFFIXES",
    "INVENTORY_RUNTIME_PREFIX",
    "PathPolicy",
    "PythonSymbolIndex",
    "SkippedPath",
    "SymbolClass",
    "SymbolFunction",
    "SymbolImport",
    "SymbolModule",
    "SymbolParseError",
    "build_codebase_inventory",
    "build_codebase_scope_map",
    "build_python_symbol_index",
    "get_codebase_scope_profile",
    "list_codebase_scope_profiles",
    "write_codebase_inventory",
    "write_python_symbol_index",
]
