"""CLI entry point: re-index project files into RAG + regenerate code_wiki.md.

Called automatically via post-commit hook, or manually at any time:
    python scripts/sync-wiki.py

Only re-indexes files whose SHA-256 has changed since last index.
"""

import os
import sys

# Ensure the repo root is on sys.path so mcp_rag is importable
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from mcp_rag import ProjectRAG  # noqa: E402
from mcp_rag import wiki as ragwiki  # noqa: E402

DB_PATH = os.path.join(_REPO_ROOT, "wogd_ddsp.db")
WIKI_PATH = os.path.join(_REPO_ROOT, "doc", "code_wiki.md")


def main() -> None:
    if not os.path.isdir(_REPO_ROOT):
        print(f"Error: repo root not found: {_REPO_ROOT}", file=sys.stderr)
        sys.exit(1)

    rag = ProjectRAG(DB_PATH)
    stats = rag.index_directory(_REPO_ROOT)

    wiki_result = {"path": "?", "symbols": 0, "files": 0}
    try:
        wiki_result = ragwiki.generate_wiki(rag, WIKI_PATH)
    except OSError as e:
        print(f"Wiki generation skipped: {e}", file=sys.stderr)

    print(
        f"Wiki sync: {stats['indexed']} new, {stats['skipped']} skipped, "
        f"{wiki_result['symbols']} symbols in {wiki_result['files']} files"
    )


if __name__ == "__main__":
    main()
