"""Structural checks on the explicitly approved public synthetic CI workflow."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
APPROVED = WORKFLOWS / "synthetic-ci.yml"


class PublicCIBoundary(unittest.TestCase):
    def test_single_allowlisted_workflow(self):
        self.assertEqual([path.name for path in WORKFLOWS.iterdir() if path.is_file()],
                         ["synthetic-ci.yml"])

    def test_read_only_permissions_and_no_stored_credentials(self):
        text = APPROVED.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertNotRegex(text, r"(?im)^\s*[^#\n]*:\s*write\s*$")

    def test_forbidden_triggers_and_secret_contexts_absent(self):
        text = APPROVED.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?im)^\s*(pull_request_target|workflow_run):")
        self.assertNotRegex(text, r"\bsecrets\.\w+")
        self.assertNotIn("self-hosted", text)

    def test_only_standard_public_runners_and_full_matrix(self):
        text = APPROVED.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-latest", text)
        self.assertIn("runs-on: windows-latest", text)
        self.assertIn("python-version: ['3.11', '3.13']", text)
        self.assertIn("cancel-in-progress: true", text)

    def test_no_install_or_promotion_job(self):
        text = APPROVED.read_text(encoding="utf-8")
        self.assertIn("NOT CRM certification", text)
        self.assertIn("NON-CERTIFYING", text)
        for name in ("deploy:", "publish:", "install:"):
            self.assertNotRegex(text, rf"(?m)^  {re.escape(name)}\s*$")


if __name__ == "__main__":
    unittest.main()
