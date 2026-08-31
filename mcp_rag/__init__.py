#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAG/MCP toolchain (chunking, DB, query, formatting, wiki).

Re-exports the public API for the MCP server entry point
(`wogd_ddsp_mcp_server.py`). Each concern lives in its own module so the whole
package stays navigable (CCD): `chunking` (structural split), `db`
(SQLite schema + indexing), `query` (search), `formatting` (LLM output) and
`wiki` (symbol-index generation).
"""

from . import chunking as chunking
from . import db as db
from . import formatting as formatting
from . import ngrams as ngrams
from . import query as query
from . import wiki as wiki
from .db import ProjectRAG, RAG_SCHEMA_VERSION
from .formatting import (
    chunk_ref,
    format_compact,
    format_json,
    format_results,
    format_toon,
)

__all__ = [
    "chunking",
    "db",
    "formatting",
    "ngrams",
    "query",
    "wiki",
    "ProjectRAG",
    "RAG_SCHEMA_VERSION",
    "chunk_ref",
    "format_compact",
    "format_json",
    "format_results",
    "format_toon",
]
