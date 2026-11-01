import tempfile
import unittest
from pathlib import Path

from aimeton_memory_os.curated_audit import compile_release, digest
from aimeton_memory_os.audit_findings import ingest_curated_finding, read_findings


def candidate():
    source = {
        "project_id": "AIMETON/aimeton-memory-os",
        "as_of_utc": "2026-11-01T00:00:00Z",
        "policy_version": "public-curated-v1",
        "records": [{
            "id": "PUB-001", "kind": "objective", "status": "VERIFIED",
            "statement": "The public project has a deliberately bounded audit prototype.",
            "evidence": ["https://github.com/AIMETON/aimeton-memory-os"],
        }],
    }
    approval = {
        "source_sha256": digest(source),
        "record_digests": {"PUB-001": digest(source["records"][0])},
        "approval_id": "RELEASE-20261101A",
    }
    return compile_release(source, approval)


def review():
    return {
        "category": "missing_evidence", "severity": "medium",
        "referenced_item": "PUB-001",
        "observation": "The claim still needs a separately reproducible acceptance proof.",
        "recommendation": "Cite a specific run and its immutable evidence for independent verification.",
        "evidence_urls": ["https://github.com/AIMETON/aimeton-memory-os/pull/49"],
    }


class CuratedFindingBindingTests(unittest.TestCase):
    def test_bound_quarantine_with_public_evidence(self):
        pack, manifest = candidate()
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "findings.sqlite"
            receipt = ingest_curated_finding(db, pack, manifest, review())
            self.assertEqual(receipt["status"], "QUARANTINED")
            results = read_findings(db, manifest["snapshot_sha256"])
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["body"], review())
            self.assertEqual(results[0]["status"], "QUARANTINED")

    def test_unknown_reference_never_ingested(self):
        pack, manifest = candidate()
        invalid = review()
        invalid["referenced_item"] = "PUB-999"
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "findings.sqlite"
            with self.assertRaises(ValueError):
                ingest_curated_finding(db, pack, manifest, invalid)
            self.assertFalse(db.exists())

    def test_bad_source_or_unknown_fields_are_refused(self):
        pack, manifest = candidate()
        variants = [
            {"evidence_urls": ["http://github.com/AIMETON/aimeton-memory-os"]},
            {"evidence_urls": ["https://example.invalid/untrusted"]},
            {"evidence_urls": ["https://github.com/AIMETON/aimeton-memory-os?token=abc"]},
            {"evidence_urls": [123]},
            {"evidence_urls": ["https://github.com/AIMETON/aimeton-memory-os"] * 2},
            {"execute": "do-not-run"},
        ]
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "findings.sqlite"
            for delta in variants:
                invalid = dict(review(), **delta)
                with self.subTest(delta=delta), self.assertRaises(ValueError):
                    ingest_curated_finding(db, pack, manifest, invalid)
            self.assertFalse(db.exists())

    def test_manifest_tamper_fails_before_storage(self):
        pack, manifest = candidate()
        tampered = dict(manifest, snapshot_sha256="0" * 64)
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "findings.sqlite"
            with self.assertRaises(ValueError):
                ingest_curated_finding(db, pack, tampered, review())
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
