#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural source chunking for the RAG index.

Splits source files into logical chunks instead of fixed line blocks:

- Python: stdlib `ast` -> classes/functions/methods with qualified names,
  signatures and docstrings; imports/constants stay in module chunks.
- C++:    brace-based scanner (no tree-sitter) -> functions, classes (incl.
  methods), namespaces/extern "C"; module chunks for the gaps.
- Markdown: chunking by headings (sections), YAML frontmatter as a named
  chunk.

Each chunk carries a stable, hash-based ID and symbol metadata (symbol_type,
symbol_name, signature, docstring). This module is part of the RAG/MCP
toolchain (see mcp_rag package). Standard library only.
"""

import ast
import hashlib
import os
import re


# Max length of a module chunk (code outside named symbols) in lines.
MODULE_CHUNK_LINES = 60


def _stable_chunk_id(file_path: str, line_start: int, symbol_name: str | None,
                     line_end: int | None = None) -> str:
    """Generate a stable chunk ID from file path, start/end line and symbol name.

    Hash-based (SHA-256, first 12 hex chars = 48 bits), so the ID stays stable
    across sessions and re-indexes (unlike AUTOINCREMENT). The format matches
    `[wogd_ddsp_<hash>]` and is compatible with get_rag_chunk.

    `line_end` is included so that two chunks which share a start line and
    symbol name (e.g. overlapping member-declaration blocks emitted by the brace
    scanner) still get distinct IDs - otherwise the UNIQUE(chunk_id) constraint
    aborts incremental indexing.
    """
    raw = f"{file_path}::{line_start}::{line_end}::{symbol_name or ''}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"wogd_ddsp_{h}"


def _emit_chunk(lines, start, end, symbol_type, symbol_name, signature, docstring, file_path="") -> dict:
    """Build a chunk record from a 0-based line range [start, end].

    Contains a stable chunk ID (hash-based) that stays valid across
    sessions and re-indexes.
    """
    line_start = start + 1
    return {
        "line_start": line_start,
        "line_end": end + 1,
        "content": "\n".join(lines[start:end + 1]),
        "symbol_type": symbol_type,
        "symbol_name": symbol_name,
        "signature": (signature or "").strip() or None,
        "docstring": docstring,
        "chunk_id": _stable_chunk_id(file_path, line_start, symbol_name, end + 1),
    }


def _module_chunks(lines, start, end, file_path="") -> list:
    """Split a region without named symbols into max 60-line blocks."""
    start = max(0, start)
    end = min(len(lines) - 1, end)
    if start > end:
        return []
    out = []
    for s in range(start, end + 1, MODULE_CHUNK_LINES):
        e = min(end, s + MODULE_CHUNK_LINES - 1)
        out.append(_emit_chunk(lines, s, e, "module", None, None, None, file_path))
    return out


def _py_arglist(args) -> str:
    """Build a compact parameter list (with defaults) from ast.arguments."""
    parts = []
    npos = len(args.args)
    ndef = len(args.defaults)
    for i, a in enumerate(args.args):
        s = a.arg
        d = i - (npos - ndef)
        if d >= 0 and d < ndef and args.defaults[d] is not None:
            try:
                s += "=" + ast.unparse(args.defaults[d])
            except Exception:
                pass
        parts.append(s)
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    parts.extend(a.arg for a in args.kwonlyargs)
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    return "(" + ", ".join(parts) + ")"


def _py_bases(node) -> str:
    if not node.bases:
        return ""
    names = []
    for b in node.bases:
        try:
            names.append(ast.unparse(b))
        except Exception:
            names.append("...")
    return "(" + ", ".join(names) + ")"


def _chunk_python(source: str, file_path: str = "") -> list:
    """Split Python code via stdlib `ast` into classes/functions/methods.

    Returns chunks with symbol_type (class/function/method), qualified name,
    signature and docstring. Lines outside definitions (imports, constants)
    are collected as `module` chunks.
    """
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = source.split("\n")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _module_chunks(lines, 0, len(lines) - 1, file_path)

    chunks = []
    covered = []  # 1-based intervals [lineno, end_lineno] of the definitions

    # Top-level uppercase assignments are module constants, not anonymous
    # module text. Keep them as named symbols so the wiki can index protocol
    # constants such as MAGIC_NUMBER.
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                chunks.append(_emit_chunk(
                    lines, node.lineno - 1, node.end_lineno - 1,
                    "constant", target.id, lines[node.lineno - 1].strip(),
                    None, file_path))
                covered.append((node.lineno, node.end_lineno))

    def walk(body, parent):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{parent}.{node.name}" if parent else node.name
                kind = "method" if parent else "function"
                sig = "def " + node.name + _py_arglist(node.args)
                doc = ast.get_docstring(node)
                chunks.append(_emit_chunk(
                    lines, node.lineno - 1, node.end_lineno - 1,
                    kind, name, sig, doc, file_path))
                covered.append((node.lineno, node.end_lineno))
            elif isinstance(node, ast.ClassDef):
                name = f"{parent}.{node.name}" if parent else node.name
                sig = "class " + node.name + _py_bases(node)
                doc = ast.get_docstring(node)
                chunks.append(_emit_chunk(
                    lines, node.lineno - 1, node.end_lineno - 1,
                    "class", name, sig, doc, file_path))
                covered.append((node.lineno, node.end_lineno))
                walk(node.body, name)

    walk(tree.body, None)

    if not covered:
        return _module_chunks(lines, 0, len(lines) - 1, file_path)

    cursor = 1
    for a, b in sorted(covered):
        if a > cursor:
            chunks.extend(_module_chunks(lines, cursor - 1, a - 2, file_path))
        cursor = max(cursor, b + 1)
    if cursor <= len(lines):
        chunks.extend(_module_chunks(lines, cursor - 1, len(lines) - 1, file_path))

    chunks.sort(key=lambda c: c["line_start"])
    return chunks


# Control keywords that are not a function head (C++ heuristic)
_CPP_CTRL = {"if", "for", "while", "switch", "catch", "do", "else", "return",
             "sizeof", "new", "delete"}


def _cpp_def_kind(header: str):
    """Classify a C++ block head -> (kind, name).

    kinds: namespace, extern, class, function, block.
    """
    h = header.strip()
    if not h or h.startswith("#") or h.endswith(";"):
        return ("block", None)
    m = re.match(r"namespace\s+([A-Za-z_]\w*)", h)
    if m:
        return ("namespace", m.group(1))
    # Check for extern "C" + function before the generic extern block check.
    m = re.match(r'extern\s*"C"\s+.*?([A-Za-z_]\w*)\s*\(', h)
    if m and m.group(1) not in _CPP_CTRL:
        return ("function", m.group(1))
    if re.match(r'extern\s*"C"', h):
        return ("extern", None)
    m = re.match(
        r"(?:template\s*<[^>]*>\s*)?"
        r"(?:(?:typedef\s+)?(?:class|struct|union)\s+([A-Za-z_]\w*)|"
        r"enum(?:\s+class)?\s+([A-Za-z_]\w*))",
        h,
    )
    if m:
        return ("class", m.group(1) or m.group(2))
    m = re.search(r"([A-Za-z_]\w*)\s*\(", h)
    if m and m.group(1) not in _CPP_CTRL:
        return ("function", m.group(1))
    return ("block", None)


def _cpp_collect_header(lines, idx, prefix):
    """Reconstruct the full block head (multi-line signatures).

    If the `{` sits in the middle of a multi-line signature (e.g.
    ``inline bool foo(int a,\n                 long b) {``) or on its own line
    (``long b)\n{``), the scanner runs backwards over continuation lines and
    collects the whole head. Stops at boundaries: blank line, comment,
    preprocessor `#`, or a line ending with `;`/`{`/`}`.

    Returns:
        (header, start_idx): head text and index of its first line.
    """
    header = prefix.strip()
    start = idx
    j = idx - 1
    while j >= 0:
        stripped = lines[j].strip()
        if not stripped or stripped.startswith(("//", "*", "/*", "*/", "#")):
            break
        prev = lines[j].lstrip().rstrip()
        if prev and prev[-1] in "{};":
            break
        header = stripped + " " + header
        start = j
        j -= 1
    return header, start


def _cpp_sub_blocks(lines, start, end, base) -> list:
    """Find blocks at depth base+1 in the range [start, end].

    Returns (header_idx, header_line, end_idx). The header is reconstructed
    from the line before the `{` (supports multi-line signatures). One-line
    blocks (e.g. `int a[] = {1,2};`) are ignored (noise).
    """
    blocks = []
    depth = base
    pending = None
    for idx in range(start, end + 1):
        line = lines[idx]
        if pending is None and depth == base and "{" in line:
            brace = line.index("{")
            prefix = line[:brace].strip()
            if prefix:
                header, hstart = _cpp_collect_header(lines, idx, prefix)
                pending = (hstart, header)
            else:
                j = idx - 1
                while j >= start and not lines[j].strip():
                    j -= 1
                if j >= start:
                    header, hstart = _cpp_collect_header(lines, idx, lines[j].strip())
                    pending = (hstart, header)
                else:
                    pending = (idx, prefix)
        depth += line.count("{") - line.count("}")
        if pending is not None and depth == base:
            if pending[0] < idx:  # real blocks, not one-liners
                blocks.append((pending[0], pending[1], idx))
            pending = None
    return blocks


def _chunk_cpp_class(lines, start, end, base, name, file_path="") -> list:
    """Split a C++ class: methods separately, header/members as class chunk."""
    blocks = _cpp_sub_blocks(lines, start + 1, end - 1, base + 1)
    if not blocks:
        chunks = [_emit_chunk(lines, start, end, "class", name,
                              lines[start].strip(), None, file_path)]
        # A typedef struct has two useful names: the tag (e.g. _mab_info)
        # and the public typedef alias (e.g. t_mab_info). Keep the tag as the
        # primary class symbol, but index the alias too for callers using the
        # public C type name.
        alias_match = re.search(r"}\s*([A-Za-z_]\w*)\s*;", lines[end].strip())
        if alias_match and alias_match.group(1) != name:
            chunks.append(_emit_chunk(
                lines, start, end, "class", alias_match.group(1),
                lines[start].strip(), None, file_path))
        return chunks

    chunks = []
    cursor = start
    for (hdr_idx, hdr_line, end_idx) in blocks:
        if hdr_idx > cursor:
            chunks.append(_emit_chunk(lines, cursor, hdr_idx - 1, "class", name,
                                      lines[start].strip(), None, file_path))
        kind, mname = _cpp_def_kind(hdr_line)
        if kind == "function" and mname:
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "method",
                                      f"{name}::{mname}", hdr_line, None, file_path))
        else:
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "block", name,
                                      hdr_line, None, file_path))
        cursor = end_idx + 1
    if cursor <= end:
        chunks.append(_emit_chunk(lines, cursor, end, "class", name,
                                  lines[start].strip(), None, file_path))
    return chunks


def _chunk_cpp_defines(lines, file_path="") -> list:
    """Extract #define constants as named chunks."""
    chunks = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        m = re.match(r'#define\s+([A-Za-z_]\w*)\s+(.+)', stripped)
        if m:
            chunks.append(_emit_chunk(
                lines, idx, idx, "constant", m.group(1), stripped, None,
                file_path))
    return chunks


def _chunk_cpp_region(lines, start, end, base, file_path="") -> list:
    """Split a C++ region: blocks at depth base+1 + module gaps."""
    chunks = []
    blocks = _cpp_sub_blocks(lines, start, end, base)
    cursor = start
    for (hdr_idx, hdr_line, end_idx) in blocks:
        if hdr_idx > cursor:
            chunks.extend(_module_chunks(lines, cursor, hdr_idx - 1, file_path))
        kind, name = _cpp_def_kind(hdr_line)
        if kind in ("namespace", "extern"):
            inner = _chunk_cpp_region(lines, hdr_idx + 1, end_idx - 1, base + 1, file_path)
            if inner:
                chunks.extend(inner)
            else:
                chunks.append(_emit_chunk(lines, hdr_idx, end_idx, kind, name,
                                          hdr_line, None, file_path))
        elif kind == "class":
            chunks.extend(_chunk_cpp_class(lines, hdr_idx, end_idx, base, name, file_path))
        elif kind == "function":
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "function", name,
                                      hdr_line, None, file_path))
        else:
            chunks.append(_emit_chunk(lines, hdr_idx, end_idx, "block", name,
                                      hdr_line, None, file_path))
        cursor = end_idx + 1
    if cursor <= end:
        chunks.extend(_module_chunks(lines, cursor, end, file_path))
    return chunks


def _chunk_cpp(source: str, file_path: str = "") -> list:
    """Split C++ code structurally (brace-based, without tree-sitter)."""
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = source.split("\n")
    chunks = _chunk_cpp_defines(lines, file_path)
    chunks.extend(_chunk_cpp_region(lines, 0, len(lines) - 1, 0, file_path))
    return chunks


def _parse_frontmatter(lines: list[str]) -> tuple[dict | None, int]:
    """Extract OKF YAML frontmatter from the top of a Markdown file.

    Returns (frontmatter_dict, body_start_index).
    frontmatter_dict is None when no ``---``-delimited block is found.
    Parsing is simple line-based: supports unquoted scalars, nested
    mappings (indented), and inline lists. No external YAML dependency.
    """
    if not lines or not lines[0].strip().startswith("---"):
        return None, 0
    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end < 0:
        return None, 0
    fm: dict = {}
    current_key: str | None = None
    current_map: dict | None = None
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            key_part = stripped.split(":", 1)[0].rstrip()
            val_part = stripped.split(":", 1)[1].strip()
            # Top-level key:value
            if not raw.startswith(" ") and not raw.startswith("\t"):
                current_key = key_part
                current_map = fm
                if val_part:
                    # Inline list? [a, b, c]
                    if val_part.startswith("[") and val_part.endswith("]"):
                        fm[current_key] = [
                            v.strip().strip("'\"")
                            for v in val_part[1:-1].split(",") if v.strip()
                        ]
                    elif val_part.startswith('"') and val_part.endswith('"'):
                        fm[current_key] = val_part[1:-1]
                    else:
                        fm[current_key] = val_part
                else:
                    # Nested mapping starts
                    fm[current_key] = {}
                    current_map = fm[current_key]
            else:
                # Nested key under current mapping
                if current_map is not None and isinstance(current_map, dict):
                    if val_part:
                        if val_part.startswith('"') and val_part.endswith('"'):
                            current_map[key_part] = val_part[1:-1]
                        else:
                            current_map[key_part] = val_part
        # Empty nested value (e.g. `verified:` with no inline value)
        elif raw.startswith(" ") and current_map is not None and isinstance(current_map, dict) and ":" in stripped.rstrip(":"):
            pass  # mapping key will get its sub-keys later
    return fm if fm else None, end + 1


def _chunk_markdown(source: str, file_path: str = "") -> list:
    """Split Markdown by headings (sections = chunks).

    YAML frontmatter (``---`` ... ``---`` at the top of the file) is extracted
    and stored as a dedicated ``frontmatter`` chunk so the code wiki can carry
    concept metadata (OKF type, status, description, stale_after, etc.).
    """
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = source.split("\n")
    fm, body_start = _parse_frontmatter(lines)
    chunks = []
    # Frontmatter as a named chunk for wiki metadata
    if fm:
        chunks.append(_emit_chunk(
            lines, 0, body_start - 1, "frontmatter",
            fm.get("title") or os.path.basename(file_path),
            None, fm.get("description") or "", file_path))
    headings = [i for i, ln in enumerate(lines) if re.match(r"^#{1,6}\s", ln) and i >= body_start]
    if not headings:
        chunks.extend(_module_chunks(lines, body_start, len(lines) - 1, file_path))
        return chunks
    if headings[0] > body_start:
        chunks.extend(_module_chunks(lines, body_start, headings[0] - 1, file_path))
    for k, hi in enumerate(headings):
        e = headings[k + 1] - 1 if k + 1 < len(headings) else len(lines) - 1
        title = re.sub(r"^#+\s*", "", lines[hi]).strip() or lines[hi].strip()
        chunks.append(_emit_chunk(lines, hi, e, "section", title,
                                  lines[hi].strip(), None, file_path))
    return chunks


def chunk_file(language: str, content: str, file_path: str = "") -> list:
    """Chunk a source file language-dependently (structural instead of line blocks).

    Python/C++ are structurally chunked (AST / brace scanner); Markdown by
    headings. All other languages (web front-end: TS/JS/Vue/HTML/CSS/JSON,
    config files) fall through to generic line chunking so their full text
    stays searchable via RAG/FTS5.
    """
    if language == "python":
        return _chunk_python(content, file_path)
    if language == "cpp":
        return _chunk_cpp(content, file_path)
    if language == "markdown":
        return _chunk_markdown(content, file_path)
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    return _module_chunks(content.split("\n"), 0, len(content.split("\n")) - 1, file_path)
