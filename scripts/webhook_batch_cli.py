#!/usr/bin/env python3
"""Bounded receipt-batch transition helper for the trusted AMOS oneshot worker."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aimeton_memory_os.webhook_inbox import begin_batch, finish_batch, pending_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["begin", "success", "failure"])
    parser.add_argument("--db", required=True)
    parser.add_argument("--batch-file", required=True)
    parser.add_argument("--wake-file", required=True)
    args = parser.parse_args()
    batch = Path(args.batch_file)
    if args.phase == "begin":
        ids = begin_batch(args.db)
        batch.parent.mkdir(parents=True, exist_ok=True)
        staged = batch.with_suffix(".tmp")
        fd = os.open(staged, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(ids, file)
        staged.replace(batch)
        print(json.dumps({"claimed": len(ids)}))
    else:
        if not batch.is_file():
            raise ValueError("batch state missing: cannot silently acknowledge")
        ids = json.loads(batch.read_text(encoding="utf-8"))
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            raise ValueError("invalid batch state")
        changed = finish_batch(args.db, ids, success=args.phase == "success")
        batch.unlink()
        pending = pending_count(args.db)
        if pending and args.phase == "success":
            with Path(args.wake_file).open("ab") as out:
                out.write(b"1")
        print(json.dumps({"acknowledged": changed, "pending": pending, "success": args.phase == "success"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
