import copy
import tempfile
import unittest
from pathlib import Path

from aimeton_memory_os.curated_audit import compile_release, verify_release, digest
from aimeton_memory_os.audit_findings import ingest_finding, read_findings


def sample():
    records = [{
        "id": "PUB-001", "kind": "objective", "status": "VERIFIED",
        "statement": "Develop a separately controlled external audit gateway.",
        "evidence": ["https://github.com/AIMETON/aimeton-memory-os"],
    }]
    source = {
        "project_id": "AIMETON/aimeton-memory-os",
        "as_of_utc": "2026-11-01T00:00:00Z",
        "policy_version": "public-curated-v1",
        "records": records,
    }
    approval = {
        "source_sha256": digest(source),
        "record_digests": {entry["id"]: digest(entry) for entry in records},
        "approval_id": "RELEASE-20261101A",
    }
    return source, approval


class CuratedReleaseTest(unittest.TestCase):
    def test_compilation_is_deterministic(self):
        source, approval = sample()
        pack, manifest = compile_release(source, approval)
        verify_release(pack, manifest)
        self.assertEqual((pack, manifest), compile_release(source, approval))
        self.assertEqual(manifest["snapshot_sha256"], digest(pack))

    def test_edits_without_reapproval_fail(self):
        source, approval = sample()
        source["records"][0]["statement"] = "A changed statement requires review."
        with self.assertRaises(ValueError):
            compile_release(source, approval)

    def test_denied_fields_and_sources(self):
        for mutation in ("private_repo", "unknown_key", "bad_result", "bad_project"):
            source, approval = sample()
            if mutation == "private_repo":
                source["records"][0]["evidence"] = ["https://example.invalid/private"]
            if mutation == "unknown_key":
                source["records"][0]["raw_payload"] = "confidential"
            if mutation == "bad_result":
                source["records"][0]["status"] = "INTERNAL"
            if mutation == "bad_project":
                source["project_id"] = "AIMETON/private"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_release(source, approval)

    def test_manifest_rejects_tamper(self):
        pack, manifest = compile_release(*sample())
        altered = dict(manifest)
        altered["snapshot_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            verify_release(pack, altered)

    def test_untrusted_findings_quarantined(self):
        _, manifest = compile_release(*sample())
        finding = {
            "category": "missing_evidence",
            "severity": "medium",
            "referenced_item": "PUB-001",
            "observation": "The available evidence does not establish the claimed result.",
            "recommendation": "Provide independent reproducible acceptance evidence.",
        }
        with tempfile.TemporaryDirectory() as root:
            database = Path(root) / "findings.sqlite"
            receipt = ingest_finding(database, manifest, finding)
            self.assertEqual(receipt["status"], "QUARANTINED")
            self.assertEqual(read_findings(database, manifest["snapshot_sha256"])[0]["body"], finding)
            self.assertEqual(read_findings(database, "0" * 64), [])
            invalid = dict(finding)
            invalid["execute"] = "do-not-trust"
            with self.assertRaises(ValueError):
                ingest_finding(database, manifest, invalid)


if __name__ == "__main__":
    unittest.main()
