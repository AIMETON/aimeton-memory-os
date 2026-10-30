#!/usr/bin/env python3
"""Replay a bounded Shadow LDC GitHub lifecycle fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.ldc import compile_shadow_case, ingest_github_issue_fixture  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    raw = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    bundle = compile_shadow_case(ingest_github_issue_fixture(raw), as_of=args.as_of)
    rendered = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if bundle["outcome"] == "admit" else 3


if __name__ == "__main__":
    raise SystemExit(main())
