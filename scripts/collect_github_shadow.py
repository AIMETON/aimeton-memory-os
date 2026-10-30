#!/usr/bin/env python3
"""Run the read-only AMOS GitHub Shadow collector."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.collector import GitHubReadOnlyClient, SQLiteShadowStore, collect_repository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--partition", default="development",
                        choices=["development","holdout_candidate","frozen_holdout"])
    args = parser.parse_args()

    store = SQLiteShadowStore(args.db)
    try:
        result = collect_repository(
            args.repo,
            store,
            GitHubReadOnlyClient(),
            partition=args.partition,
        )
    finally:
        store.close()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
