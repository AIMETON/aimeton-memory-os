#!/usr/bin/env python3
"""Compile an AMOS ContextBundle from canonical mission/evidence JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimeton_memory_os.continuity import compile_context_bundle, load_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mission_state")
    parser.add_argument("evidence")
    parser.add_argument("--output")
    args = parser.parse_args()

    state = load_json(args.mission_state)
    evidence = load_json(args.evidence)
    bundle = compile_context_bundle(state, evidence)
    rendered = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if bundle["outcome"] == "admit" else 3


if __name__ == "__main__":
    raise SystemExit(main())
