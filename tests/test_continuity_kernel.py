from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURES = ROOT / "tests" / "fixtures" / "continuity"
sys.path.insert(0, str(SRC))

from aimeton_memory_os.continuity import compile_context_bundle, recovery_assertions


class ContinuityKernelTest(unittest.TestCase):
    def _load(self, name: str):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_fixture_compiles_to_admitted_context_bundle(self) -> None:
        state = self._load("mission_state.json")
        evidence = self._load("evidence.json")
        bundle = compile_context_bundle(state, evidence)
        self.assertEqual(bundle["outcome"], "admit")
        self.assertEqual([c["check_id"] for c in bundle["compatibility"]], [f"CR-{n:02d}" for n in range(1, 7)])
        self.assertTrue(all(c["state"] == "satisfied" for c in bundle["compatibility"]))

    def test_fresh_process_recovers_mission_without_chat_history(self) -> None:
        expected = self._load("expected_recovery.json")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/recover_context.py",
                    str(FIXTURES / "mission_state.json"),
                    str(FIXTURES / "evidence.json"),
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
        result = recovery_assertions(bundle, expected)
        self.assertTrue(result["mission_id_match"])
        self.assertTrue(result["state_match"])
        self.assertTrue(result["next_match"])
        self.assertTrue(result["next_after_next_match"])
        self.assertEqual(result["duplicate_mutation_count"], 0)
        self.assertTrue(result["authority_preserved"])
        self.assertTrue(result["evidence_refs_match"])
        self.assertEqual(result["outcome"], "admit")

    def test_completed_action_cannot_be_reissued(self) -> None:
        state = self._load("mission_state.json")
        state["completed"].append({"action_id": state["next_safe_action"]["action_id"], "result": "already done"})
        bundle = compile_context_bundle(state, self._load("evidence.json"))
        cr03 = next(c for c in bundle["compatibility"] if c["check_id"] == "CR-03")
        self.assertEqual(cr03["state"], "blocked")
        self.assertEqual(bundle["outcome"], "escalate")

    def test_cr06_blocks_source_version_drift(self) -> None:
        state = self._load("mission_state.json")
        state = copy.deepcopy(state)
        state["expected_evidence_digests"]["ev-repo-current"] = "0" * 64
        bundle = compile_context_bundle(state, self._load("evidence.json"))
        cr06 = next(c for c in bundle["compatibility"] if c["check_id"] == "CR-06")
        self.assertEqual(cr06["state"], "blocked")
        self.assertEqual(cr06["reason_code"], "source_version_changed_or_unreconstructable")
        self.assertEqual(bundle["outcome"], "escalate")


if __name__ == "__main__":
    unittest.main()
