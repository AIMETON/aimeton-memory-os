from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AmosBaselineContractsTest(unittest.TestCase):
    def test_contract_validator_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_contracts.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_manifest_declares_governed_amos_identity(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["repository"], "AIMETON/aimeton-memory-os")
        self.assertEqual(manifest["namespace"], "AIMETON.COGOPS")
        self.assertEqual(manifest["license"], "Apache-2.0")
        self.assertIn("compatibility_registry", manifest["authoritative_interfaces"])
        self.assertIn("verification_trace", manifest["authoritative_interfaces"])
        self.assertIn("cognitive_continuity", manifest["authoritative_interfaces"])

    def test_baseline_ci_is_self_hosted_and_marketplace_free(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "baseline-ci.yml").read_text(encoding="utf-8")
        self.assertIn("runs-on: [self-hosted, Linux, X64, memory-os-ci]", workflow)
        self.assertNotIn("ubuntu-latest", workflow)
        self.assertFalse(any(line.lstrip().startswith("uses:") for line in workflow.splitlines()))
        self.assertIn("git fetch --no-tags --depth=1 origin \"$TARGET_SHA\"", workflow)
        self.assertIn('test "$RUNNER_NAME" = "aimeton-memory-os-ci"', workflow)


if __name__ == "__main__":
    unittest.main()
