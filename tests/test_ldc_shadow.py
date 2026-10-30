from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURE = ROOT / "tests" / "fixtures" / "ldc" / "github_issue6_lifecycle.json"
sys.path.insert(0, str(SRC))

from aimeton_memory_os.ldc import (
    AppendOnlyEvidenceLog,
    compile_shadow_case,
    ingest_github_issue_fixture,
    project_semantic_layers,
)


class ShadowLdcTest(unittest.TestCase):
    def _raw(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_real_github_receipts_become_append_only_e0(self) -> None:
        envelopes = ingest_github_issue_fixture(self._raw())
        self.assertEqual(len(envelopes), 3)
        self.assertTrue(all(x["layer"] == "E0" for x in envelopes))
        with tempfile.TemporaryDirectory() as tmp:
            log = AppendOnlyEvidenceLog(Path(tmp) / "e0.jsonl")
            self.assertTrue(all(log.append(x) for x in envelopes))
            before = (Path(tmp) / "e0.jsonl").read_bytes()
            self.assertFalse(log.append(envelopes[0]))
            self.assertEqual((Path(tmp) / "e0.jsonl").read_bytes(), before)
            changed = dict(envelopes[0])
            changed["digest"] = "0" * 64
            with self.assertRaises(ValueError):
                log.append(changed)

    def test_e1_e2_e3_e4_lineage_is_derived_without_rewriting_e0(self) -> None:
        envelopes = ingest_github_issue_fixture(self._raw())
        semantic = project_semantic_layers(envelopes, as_of="2026-10-30T14:11:09Z")
        self.assertGreaterEqual(len(semantic["E1"]), 3)
        self.assertEqual(semantic["E2"][0]["claim"], "P0 acceptance was asserted")
        self.assertEqual(semantic["E3"][0]["decision"], "accept_p0")
        self.assertEqual(semantic["E4"][0]["kind"], "derived_knowledge")
        self.assertTrue(semantic["E4"][0]["provenance"])

    def test_replay_preserves_historical_open_and_later_closed_truth(self) -> None:
        envelopes = ingest_github_issue_fixture(self._raw())
        before_close = compile_shadow_case(envelopes, as_of="2026-10-30T14:11:06Z")
        after_close = compile_shadow_case(envelopes, as_of="2026-10-30T14:11:09Z")

        self.assertEqual(before_close["mode"], "SHADOW")
        self.assertEqual(after_close["mode"], "SHADOW")
        self.assertEqual(before_close["outcome"], "admit")
        self.assertEqual(after_close["outcome"], "admit")
        self.assertEqual(before_close["projections"]["O"]["state"], "open")
        self.assertEqual(after_close["projections"]["O"]["state"], "closed")
        self.assertEqual(len(before_close["semantic_layers"]["E4"]), 0)
        self.assertEqual(len(after_close["semantic_layers"]["E4"]), 1)
        self.assertIn("github_mutation", after_close["authority_envelope"]["forbidden_actions"])

    def test_fresh_process_replay_cli_emits_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "shadow.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/replay_shadow_ldc.py",
                    str(FIXTURE),
                    "--as-of",
                    "2026-10-30T14:11:09Z",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            bundle = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(bundle["mode"], "SHADOW")
        self.assertEqual(bundle["projections"]["O"]["state"], "closed")
        self.assertEqual(bundle["trace"]["snapshot_id"], bundle["snapshot_id"])
        self.assertEqual(len(bundle["trace"]["compatibility"]), 6)

    def test_shadow_case_emits_all_cr_reason_codes(self) -> None:
        bundle = compile_shadow_case(
            ingest_github_issue_fixture(self._raw()),
            as_of="2026-10-30T14:11:09Z",
        )
        self.assertEqual(
            [x["check_id"] for x in bundle["compatibility"]],
            [f"CR-{n:02d}" for n in range(1, 7)],
        )
        self.assertTrue(all(x["reason_code"] for x in bundle["compatibility"]))


if __name__ == "__main__":
    unittest.main()
