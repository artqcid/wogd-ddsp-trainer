#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite-FTS5 RAG database: schema, scanning and incremental indexing.

`ProjectRAG` here only owns the persistent storage concerns (connection,
schema/migration, file scanning, chunk insert, stale cleanup). Searching and
output serialization live in sibling modules (`query`, `formatting`), so each
concern stays small and focused (CCD). Standard library + the `chunking` module.
"""

import hashlib
import json
import os
import fnmatch
import sqlite3
from contextlib import closing

from . import chunking


# Database file lives in the project directory (passed in by the caller).
# Schema version: bump on structural changes -> forces a DB rebuild.
# v1 = line chunking, v2 = structural chunking + symbol metadata.
# v3 = C++ header reconstruction (multi-line signatures) + LF normalization.
# v4 = Stable chunk IDs (hash-based instead of AUTOINCREMENT).
# v5 = Recreate FTS5 when upgrading databases created with the incomplete
#      symbol-index schema.
# v6 = YAML frontmatter column for Markdown concept files (LLM-Wiki/OKF).
# v7 = wogd-ddsp-trainer adaptation: wogd_ddsp_ chunk ID prefix, web front-end
#      languages (TS/JS/Vue/HTML/CSS/JSON) via generic line-chunker.
RAG_SCHEMA_VERSION = 7

# Languages to index and their file extensions.
# `.md` is included so that the central guide
# (AGENTS.md, docs) is searchable via RAG.
# Python = torch/trainer code (structural AST chunking), cpp = extension/DSP
# modules, markdown = LLM-Wiki concept files (heading chunking), everything
# else (web UI) falls through to generic line chunking.
RAG_LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".md": "markdown",
    ".ts": "javascript",
    ".tsx": "javascript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".vue": "javascript",
    ".html": "markup",
    ".css": "markup",
    ".json": "json",
    ".toml": "json",
    ".yaml": "json",
    ".yml": "json",
}

# Directories skipped during scanning. SDK/framework dirs/flood the
# index with foreign code and dilute searches in the project's own code.
RAG_IGNORED_DIRS = {
    ".git", "build", "dist", "out", ".venv", "__pycache__", ".pytest_cache",
    "node_modules", ".continue", "CMakeFiles", ".vscode", ".idea",
    "third_party",
}

# Max file size to index (bytes) - prevents large binaries
RAG_MAX_FILE_SIZE = 2 * 1024 * 1024

# Do not index the generated wiki itself (meta-noise, new hash each run)
RAG_IGNORED_FILENAMES = {"code_wiki.md"}


class ProjectRAG:
    """Manages the local SQLite-FTS5 database for code retrieval."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    # -- Database connection ------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        """Open a fresh connection (thread-safe for parallel MCP calls)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    # -- Schema --------------------------------------------------------------
    def _init_schema(self):
        """Create the tables; migrate old schemas (line chunking -> v2)."""
        with closing(self._connect()) as conn:
            with conn:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version < RAG_SCHEMA_VERSION:
                    conn.execute("DROP TABLE IF EXISTS code_fts")
                    conn.execute("DROP TABLE IF EXISTS code_chunks")
                    conn.execute("PRAGMA user_version = {}".format(RAG_SCHEMA_VERSION))
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS code_chunks (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        chunk_id    TEXT    NOT NULL UNIQUE,
                        file_path   TEXT    NOT NULL,
                        language    TEXT    NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        line_start  INTEGER NOT NULL,
                        line_end    INTEGER NOT NULL,
                        content     TEXT    NOT NULL,
                        symbol_type TEXT,
                        symbol_name TEXT,
                        signature   TEXT,
                        docstring   TEXT,
                        frontmatter TEXT,
                        file_sha    TEXT    NOT NULL,
                        UNIQUE(file_path, chunk_index)
                    )
                """)
                # FTS5 virtual table: rowid references code_chunks.id.
                # Trigram tokenizer preferred, fallback to unicode61.
                # v4: symbol_name, signature, docstring as searchable FTS5 fields.
                fts_sql = (
                    "CREATE VIRTUAL TABLE IF NOT EXISTS code_fts USING fts5("
                    "file_path UNINDEXED, language UNINDEXED, "
                    "line_start UNINDEXED, line_end UNINDEXED, "
                    "symbol_name, signature, docstring, content, "
                    "tokenize = '{}')"
                )
                try:
                    conn.execute(fts_sql.format("trigram"))
                except sqlite3.OperationalError:
                    # Older SQLite builds without the trigram tokenizer
                    conn.execute(fts_sql.format("unicode61"))
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_code_chunks_path "
                    "ON code_chunks(file_path)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_code_chunks_symbol "
                    "ON code_chunks(symbol_name)"
                )

    # -- Scanning ------------------------------------------------------------
    def _ragignore_dir(self) -> str:
        """Directory holding the optional `.ragignore` file (the project root)."""
        return os.path.dirname(os.path.abspath(self.db_path))

    def _scan_directory(self, directory_path: str) -> list:
        """Collect all indexable source files under directory_path."""
        # .ragignore load (optional)
        ragignore_patterns = []
        ragignore_path = os.path.join(self._ragignore_dir(), ".ragignore")
        if os.path.isfile(ragignore_path):
            with open(ragignore_path, "r", encoding="utf-8") as rf:
                for raw in rf:
                    line = raw.strip()
                    if line and not line.startswith("#"):
                        ragignore_patterns.append(line)

        def _is_ignored(abs_path: str, rel_path: str) -> bool:
            for pat in ragignore_patterns:
                if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(abs_path, pat):
                    return True
                # Also match a directory prefix (e.g. "build/" matches "build/Debug/file.cpp")
                if pat.endswith("/") and (rel_path.startswith(pat) or abs_path.startswith(pat)):
                    return True
            return False

        files = []
        for root, dirs, names in os.walk(directory_path):
            dirs[:] = [d for d in dirs if d not in RAG_IGNORED_DIRS]
            for name in names:
                if name in RAG_IGNORED_FILENAMES:
                    continue
                ext = os.path.splitext(name)[1].lower()
                lang = RAG_LANGUAGE_EXTENSIONS.get(ext)
                if not lang:
                    continue
                abs_path = os.path.join(root, name)
                try:
                    rel_path = os.path.relpath(abs_path, directory_path)
                except ValueError:
                    rel_path = abs_path
                if _is_ignored(abs_path, rel_path):
                    continue
                try:
                    if os.path.getsize(abs_path) > RAG_MAX_FILE_SIZE:
                        continue
                    with open(abs_path, "rb") as f:
                        content_bytes = f.read()
                except OSError:
                    continue
                try:
                    content = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content = content_bytes.decode("utf-8", errors="replace")
                content = content.replace("\r\n", "\n").replace("\r", "\n")
                files.append({
                    "path": os.path.normpath(abs_path),
                    "language": lang,
                    "sha": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "content": content,
                })
        return files

    # -- Indexing ------------------------------------------------------------
    def index_directory(self, directory_path: str) -> dict:
        """Index (or incrementally update) all code files."""
        directory_path = os.path.abspath(os.path.normpath(directory_path))
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        files = self._scan_directory(directory_path)
        scanned_paths = {f["path"] for f in files}
        indexed = 0
        skipped = 0

        with closing(self._connect()) as conn:
            # Purge entries from old non-canonicalized indexing runs
            # (relative paths or different absolute roots that no longer match)
            with conn:
                conn.execute(
                    "DELETE FROM code_chunks WHERE file_path NOT LIKE ?",
                    (directory_path + os.sep + "%",)
                )
                conn.execute(
                    "DELETE FROM code_fts WHERE file_path NOT LIKE ?",
                    (directory_path + os.sep + "%",)
                )
            with conn:
                for f in files:
                    # Incremental: skip unchanged files (same SHA)
                    rows = conn.execute(
                        "SELECT file_sha FROM code_chunks WHERE file_path = ?",
                        (f["path"],),
                    ).fetchall()
                    if rows and all(r["file_sha"] == f["sha"] for r in rows):
                        skipped += 1
                        continue

                    # Remove old chunks of this file (structure + FTS)
                    conn.execute("DELETE FROM code_fts WHERE file_path = ?", (f["path"],))
                    conn.execute("DELETE FROM code_chunks WHERE file_path = ?", (f["path"],))

                    # Structurally chunk the file and insert
                    # Extract frontmatter for Markdown concept files (LLM-Wiki/OKF)
                    fm_json: str | None = None
                    if f["language"] == "markdown":
                        fm, _fb = chunking._parse_frontmatter(f["content"].split("\n"))
                        if fm:
                            fm_json = json.dumps(fm, ensure_ascii=False)
                    for idx, chunk in enumerate(chunking.chunk_file(f["language"], f["content"], f["path"])):
                        cur = conn.execute(
                            "INSERT INTO code_chunks "
                            "(chunk_id, file_path, language, chunk_index, line_start, "
                            " line_end, content, symbol_type, symbol_name, "
                            " signature, docstring, frontmatter, file_sha) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (chunk.get("chunk_id"), f["path"], f["language"], idx, chunk["line_start"],
                             chunk["line_end"], chunk["content"],
                             chunk.get("symbol_type"), chunk.get("symbol_name"),
                             chunk.get("signature"), chunk.get("docstring"), fm_json, f["sha"]),
                        )
                        conn.execute(
                            "INSERT INTO code_fts "
                            "(rowid, file_path, language, line_start, line_end, "
                            " symbol_name, signature, docstring, content) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (cur.lastrowid, f["path"], f["language"],
                             chunk["line_start"], chunk["line_end"],
                             chunk.get("symbol_name"), chunk.get("signature"),
                             chunk.get("docstring"), chunk["content"]),
                        )
                    indexed += 1

                # Cleanup: remove deleted/missing files from the index
                stale = self._find_stale_paths(conn, directory_path, scanned_paths)
                for path in stale:
                    conn.execute("DELETE FROM code_fts WHERE file_path = ?", (path,))
                    conn.execute("DELETE FROM code_chunks WHERE file_path = ?", (path,))

        return {"indexed": indexed, "skipped": skipped, "total_files": len(files)}

    @staticmethod
    def _find_stale_paths(conn, directory_path: str, scanned_paths: set) -> list:
        """Find indexed paths under directory_path that no longer exist."""
        prefix = directory_path + os.sep
        # Escape LIKE special chars in the path (backslash as ESCAPE char)
        pattern = (
            prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            + "%"
        )
        stale = []
        for row in conn.execute(
            "SELECT DISTINCT file_path FROM code_chunks "
            "WHERE file_path LIKE ? ESCAPE '\\'",
            (pattern,),
        ):
            if row["file_path"] not in scanned_paths:
                stale.append(row["file_path"])
        return stale
