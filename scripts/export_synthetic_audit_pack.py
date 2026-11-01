#!/usr/bin/env python3
"""Offline synthetic audit pack exporter. Does not access AMOS or GitHub."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aimeton_memory_os.audit_export import (
    canonical_bytes, export_synthetic_audit_pack, verify_synthetic_audit_pack
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads(args.fixture.read_text(encoding="utf-8"))
    snapshot, manifest = export_synthetic_audit_pack(source)
    verify_synthetic_audit_pack(snapshot, manifest)
    # The path must be new; no overwrite or implicit public/static publish.
    if args.out.is_symlink() or args.out.exists():
        raise ValueError("audit export destination must not exist")
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "snapshot.json").write_bytes(canonical_bytes(snapshot))
    (args.out / "manifest.json").write_bytes(canonical_bytes(manifest))
    verify_synthetic_audit_pack(
        json.loads((args.out / "snapshot.json").read_text(encoding="utf-8")),
        json.loads((args.out / "manifest.json").read_text(encoding="utf-8")),
    )
    print("synthetic offline audit pack verified; not authorized for publication")


if __name__ == "__main__":
    main()
