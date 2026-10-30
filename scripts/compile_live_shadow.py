#!/usr/bin/env python3
"""Compile immutable Shadow traces from durable AMOS E0 storage."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.live_shadow import process_shadow_store  # noqa: E402

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--verify-all", action="store_true", help="Replay and verify all immutable traces")
    args=parser.parse_args()
    result=process_shadow_store(args.db,args.output_dir,verify_all=args.verify_all)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
