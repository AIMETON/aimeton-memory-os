"""Fail-closed G1 exporter tests, fully synthetic: no real project export."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aimeton_memory_os.audit_export import (
    export_synthetic_audit_pack, verify_synthetic_audit_pack, canonical_bytes
)

FIXTURE = json.loads(
    (ROOT / "tests/fixtures/audit_synthetic_policy_input.json").read_text(encoding="utf-8")
)
SENTINEL = "NEVER_EXPORT_THIS_SECRET"


class AuditExportG1Test(unittest.TestCase):
    def test_deterministic_redaction_and_independent_replay(self):
        source = copy.deepcopy(FIXTURE)
        snapshot, manifest = export_synthetic_audit_pack(source)
        self.assertEqual(len(snapshot["records"]), 2)
        self.assertNotIn(SENTINEL, canonical_bytes(snapshot).decode("utf-8"))
        self.assertNotIn(SENTINEL, canonical_bytes(manifest).decode("utf-8"))
        self.assertNotIn("PRIVATE-DO-NOT-EXPOSE", canonical_bytes(snapshot).decode("utf-8"))
        self.assertNotIn("internal.invalid", canonical_bytes(snapshot).decode("utf-8"))
        verify_synthetic_audit_pack(snapshot, manifest)
        source["records"].reverse()
        self.assertEqual(export_synthetic_audit_pack(source), (snapshot, manifest))
        next(row for row in source["records"] if row["export_rule"] == "deny")["deeply_nested"]["secret"] = "OTHER_SECRET"
        self.assertEqual(export_synthetic_audit_pack(source), (snapshot, manifest))

    def test_reject_real_project_and_untrusted_profiles(self):
        for key, value in (
            ("project_id", "AIMETON/Choke_ring_antenna"),
            ("project_id", "AIMETON/aimeton-memory-os"),
            ("source_profile", "live_e0"),
            ("authorization", "owner-approved"),
            ("export_policy_version", "production-v1"),
            ("as_of_utc", "not-a-time"),
        ):
            source = copy.deepcopy(FIXTURE)
            source[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                export_synthetic_audit_pack(source)

    def test_fail_closed_on_unknown_and_restricted_allow(self):
        for change in ("top_level_extra", "allow_private", "allow_with_raw_content",
                       "unknown_result", "duplicate_id", "bad_digest", "no_allowed"):
            source = copy.deepcopy(FIXTURE)
            record = source["records"][0]
            if change == "top_level_extra": source["raw_amos_e0"] = {"secret": SENTINEL}
            if change == "allow_private": record["security_label"] = "private"
            if change == "allow_with_raw_content": record["body"] = SENTINEL
            if change == "unknown_result": record["result"] = "NICE"
            if change == "duplicate_id": source["records"][1]["record_id"] = record["record_id"]
            if change == "bad_digest": record["evidence_digest"] = "abc"
            if change == "no_allowed": source["records"] = [source["records"][-1]]
            with self.subTest(change=change), self.assertRaises(ValueError):
                export_synthetic_audit_pack(source)

    def test_manifest_corruption_and_snapshot_injection_rejected(self):
        snapshot, manifest = export_synthetic_audit_pack(FIXTURE)
        for key, value in (("snapshot_sha256", "0" * 64),
                           ("snapshot_size_bytes", 3),
                           ("snapshot_filename", "../private.db")):
            tampered = copy.deepcopy(manifest)
            tampered[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_synthetic_audit_pack(snapshot, tampered)
        bad = copy.deepcopy(snapshot)
        bad["records"][0]["raw_secret"] = SENTINEL
        with self.assertRaises(ValueError):
            verify_synthetic_audit_pack(bad, manifest)

    def test_cli_output_is_new_only_and_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "audit-output"
            command = [
                sys.executable, str(ROOT / "scripts/export_synthetic_audit_pack.py"),
                "--fixture", str(ROOT / "tests/fixtures/audit_synthetic_policy_input.json"),
                "--out", str(output)
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            snapshot = json.loads((output / "snapshot.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            verify_synthetic_audit_pack(snapshot, manifest)
            with self.assertRaises(subprocess.CalledProcessError):
                subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertEqual((output / "snapshot.json").read_bytes(), canonical_bytes(snapshot))
            self.assertEqual((output / "manifest.json").read_bytes(), canonical_bytes(manifest))


if __name__ == "__main__":
    unittest.main()
