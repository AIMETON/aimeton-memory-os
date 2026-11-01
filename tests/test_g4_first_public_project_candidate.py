"""G4 real-project candidate must stay non-public until exact owner consent."""
import json
import unittest
from pathlib import Path

from aimeton_memory_os.curated_audit import compile_release, digest, validate_record

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "tests/fixtures/g4_first_public_project_candidate.json"
PINNED = "b45900a3bc2938faa25d2c5d00720601ef4316b9"


class FirstPublicProjectCandidateTest(unittest.TestCase):
    def test_exact_public_source_and_nonpublication(self):
        candidate = json.loads(FILE.read_text(encoding="utf-8"))
        self.assertEqual(set(candidate), {
            "candidate_schema", "project_source_commit", "publication_authorized",
            "real_e0_included", "release_status", "source", "notes",
        })
        self.assertEqual(candidate["project_source_commit"], PINNED)
        self.assertIs(candidate["publication_authorized"], False)
        self.assertIs(candidate["real_e0_included"], False)
        self.assertEqual(candidate["release_status"], "OWNER_APPROVAL_REQUIRED")
        source = candidate["source"]
        self.assertEqual(source["project_id"], "AIMETON/aimeton-memory-os")
        self.assertEqual(source["policy_version"], "public-curated-v1")
        self.assertEqual(len(source["records"]), 6)
        ids = set()
        kinds = set()
        for record in source["records"]:
            validate_record(record)
            self.assertNotIn(record["id"], ids)
            ids.add(record["id"])
            kinds.add(record["kind"])
            for url in record["evidence"]:
                self.assertTrue(url.startswith("https://github.com/AIMETON/"))
                self.assertNotIn("Choke_ring_antenna", url)
        self.assertEqual(kinds, {"objective", "decision", "test", "limitation", "next_action"})
        self.assertEqual(source["records"][-1]["status"], "UNRESOLVED")

    def test_digest_does_not_substitute_owner_approval(self):
        candidate = json.loads(FILE.read_text(encoding="utf-8"))
        source = candidate["source"]
        self.assertEqual(len(digest(source)), 64)
        with self.assertRaises(ValueError):
            compile_release(source, {})
        with self.assertRaises(ValueError):
            compile_release(source, None)

    def test_no_embedded_e0_or_credentials(self):
        text = FILE.read_text(encoding="utf-8").lower()
        for marker in (
            "access_token", "private_key", "authorization: bearer",
            "/var/lib/aimeton/", "api_key", "session_secret",
            "github_pat_", "ghp_",
        ):
            self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
