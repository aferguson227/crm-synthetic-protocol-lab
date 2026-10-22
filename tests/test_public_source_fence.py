"""Fail-closed inventory and import guards for the standalone public fixture.

This module intentionally audits only the synthetic package, not private CRM code.
Changing the approved inventory requires deliberate review of this contract.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "synthetic_crm"
EXPECTED = {"__init__.py", "demo_lease.py", "public_smoke.py"}
SAFE_IMPORTS = {"hmac", "math", "secrets", "json"}


class PublicSourceFence(unittest.TestCase):
    def test_exact_synthetic_module_inventory(self):
        actual = {p.name for p in PACKAGE.iterdir() if p.is_file()}
        self.assertEqual(actual, EXPECTED)

    def test_package_contains_only_plain_python_sources(self):
        for path in PACKAGE.iterdir():
            if path.is_dir():
                self.assertEqual(path.name, "__pycache__")
            else:
                self.assertEqual(path.suffix, ".py")
                self.assertFalse(path.is_symlink())

    def test_only_allowlisted_standard_library_imports(self):
        for name in sorted(EXPECTED):
            source = (PACKAGE / name).read_text(encoding="utf-8")
            parsed = ast.parse(source, filename=name)
            for node in ast.walk(parsed):
                if isinstance(node, ast.Import):
                    for entry in node.names:
                        self.assertIn(entry.name, SAFE_IMPORTS, (name, entry.name))
                if isinstance(node, ast.ImportFrom):
                    self.fail(f"Unexpected from-import in {name}: {node.module}")

    def test_no_external_endpoint_literal_in_fixture(self):
        for name in EXPECTED:
            source = (PACKAGE / name).read_text(encoding="utf-8")
            self.assertNotIn("https://", source)
            self.assertNotIn("http://", source)

    def test_no_dynamic_execution_apis_in_fixture(self):
        banned = {"eval", "exec", "compile", "__import__"}
        for name in EXPECTED:
            parsed = ast.parse((PACKAGE / name).read_text(encoding="utf-8"))
            for node in ast.walk(parsed):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, banned, (name, node.func.id))

    def test_public_workflow_has_no_environment_secret_names(self):
        workflow = (ROOT / ".github/workflows/synthetic-ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("environment:", workflow)
        self.assertNotIn("id-token: write", workflow)
        self.assertIn("contents: read", workflow)


if __name__ == "__main__":
    unittest.main()
