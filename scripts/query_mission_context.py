#!/usr/bin/env python3
"""Local controller-side mission context query; stdout is JSON, never public HTTP."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aimeton_memory_os.mission_context import compile_mission_context


def main():
    p = argparse.ArgumentParser(description="AMOS read-only mission context (trusted operator only)")
    p.add_argument("--db", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--allow-repo", action="append", required=True,
                   help="Trusted operator policy allowlist; NEVER accept from an untrusted remote request")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--as-of")
    args = p.parse_args()
    print(json.dumps(compile_mission_context(
        args.db, project=args.project, authorized_repositories=args.allow_repo,
        limit=args.limit, offset=args.offset, as_of=args.as_of,
    ), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
