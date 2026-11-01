#!/usr/bin/env python3
"""Run synthetic G3 audit HTTP prototype on IPv4 loopback only."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aimeton_memory_os.audit_http import LoopbackAuditServer

def main():
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True, type=Path)
    p.add_argument("--fixture", type=Path,
                   default=root / "tests/fixtures/audit_synthetic_policy_input.json")
    p.add_argument("--port", type=int, default=0)
    args = p.parse_args()
    if not 0 <= args.port <= 65535:
        p.error("invalid port")
    with LoopbackAuditServer(("127.0.0.1", args.port), args.db, args.fixture) as server:
        print(f"SYNTHETIC_LOOPBACK_ONLY port={server.server_address[1]}", flush=True)
        server.serve_forever(poll_interval=0.2)

if __name__ == "__main__":
    main()
