#!/usr/bin/env python3
"""Read-only bounded C02 MVP-4 activity inspection; JSON to stdout."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.activity_context import compile_activity_context, read_activity_pair


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Read-only E0 SQLite path")
    parser.add_argument("--comment-id", type=int, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    comment, run = read_activity_pair(
        args.db, "AIMETON/Choke_ring_antenna", args.comment_id, args.run_id
    )
    context = compile_activity_context(comment, run)
    print(json.dumps(context, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if context["outcome"] == "admit" else 2


if __name__ == "__main__":
    raise SystemExit(main())
