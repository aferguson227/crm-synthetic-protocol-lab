"""Temporary-directory mock transaction. No CRM imports, updater or live installation."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

DUMMY_BYTES = b"SYNTHETIC-ONLY: not a usable application\n"
PHASES = ("validate", "stage", "verify", "pointer_swap", "post_swap", "mandatory_restore")


class MockTransaction:
    def __init__(self, root):
        self.root = Path(root)
        self.versions = self.root / "versions"
        self.versions.mkdir()
        self.durable = self.root / "durable"
        self.durable.mkdir()
        (self.durable / "mock-orders.json").write_bytes(b'{"mock_exit_count":2}')
        (self.durable / "mock-user-preferences.json").write_bytes(b'{"synthetic_mode":true}')
        self.current = self.root / "current.txt"
        self.current.write_bytes(b"OLD_SYNTHETIC_RELEASE\n")
        self.staging = self.root / "synthetic-stage"
        self.target = self.versions / "NEW_SYNTHETIC_RELEASE"

    def run(self, *, expected_digest=None, replacement=DUMMY_BYTES,
            interrupt=None, existing_target=False, inject_symlink=False):
        before_pointer = self.current.read_bytes()
        before_orders = (self.durable / "mock-orders.json").read_bytes()
        before_preferences = (self.durable / "mock-user-preferences.json").read_bytes()
        expected_digest = hashlib.sha256(DUMMY_BYTES).hexdigest() if expected_digest is None else expected_digest
        reason = "SIMULATED_SUCCESS_RESTORED"
        passed = []
        created_stage = False
        try:
            if self.root.name != "synthetic-transaction-rehearsal":
                raise ValueError("non_disposable_root")
            if self.staging.exists() or self.staging.is_symlink():
                raise ValueError("staging_collision")
            if self.target.exists() or self.target.is_symlink() or existing_target:
                raise ValueError("target_collision")
            if inject_symlink or self.versions.is_symlink() or self.durable.is_symlink():
                raise ValueError("unsafe_path")
            if (type(replacement) is not bytes or type(expected_digest) is not str
                    or len(expected_digest) != 64):
                raise ValueError("invalid_payload")
            if hashlib.sha256(replacement).hexdigest() != expected_digest:
                raise ValueError("payload_hash_mismatch")
            for phase in PHASES:
                if phase == interrupt:
                    raise ValueError("synthetic_interrupt_" + phase)
                if phase == "stage":
                    self.staging.mkdir()
                    created_stage = True
                    (self.staging / "demo.txt").write_bytes(replacement)
                elif phase == "verify":
                    blob = (self.staging / "demo.txt").read_bytes()
                    if hashlib.sha256(blob).hexdigest() != expected_digest:
                        raise ValueError("staging_hash_mismatch")
                elif phase == "pointer_swap":
                    self.current.write_bytes(b"NEW_SYNTHETIC_RELEASE\n")
                elif phase == "post_swap":
                    if self.current.read_bytes() != b"NEW_SYNTHETIC_RELEASE\n":
                        raise ValueError("invalid_mock_pointer")
                passed.append(phase)
        except ValueError as error:
            reason = str(error)
        finally:
            self.current.write_bytes(before_pointer)
            if created_stage:
                (self.staging / "demo.txt").unlink()
                self.staging.rmdir()
        return {
            "reason": reason,
            "passed_phases": tuple(passed),
            "pointer_bytes_restored": self.current.read_bytes() == before_pointer,
            "mock_orders_preserved": (self.durable / "mock-orders.json").read_bytes() == before_orders,
            "mock_preferences_preserved": (self.durable / "mock-user-preferences.json").read_bytes() == before_preferences,
            "can_install_or_deploy": False,
            "private_release_certified": False,
        }


class DisposableFilesystemTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="crm-public-rehearsal-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "synthetic-transaction-rehearsal"
        self.root.mkdir()
        self.model = MockTransaction(self.root)

    def assert_safe(self, result):
        self.assertFalse(result["can_install_or_deploy"])
        self.assertFalse(result["private_release_certified"])
        self.assertTrue(result["pointer_bytes_restored"])
        self.assertTrue(result["mock_orders_preserved"])
        self.assertTrue(result["mock_preferences_preserved"])
        self.assertFalse(self.model.staging.exists())
        self.assertEqual(self.model.current.read_bytes(), b"OLD_SYNTHETIC_RELEASE\n")

    def test_success_is_always_rolled_back(self):
        result = self.model.run()
        self.assertEqual(result["reason"], "SIMULATED_SUCCESS_RESTORED")
        self.assertEqual(result["passed_phases"], PHASES)
        self.assert_safe(result)

    def test_injection_at_every_phase_preserves_state(self):
        for phase in PHASES:
            with self.subTest(phase=phase):
                self.assert_safe(self.model.run(interrupt=phase))

    def test_hash_mismatch_does_not_create_staging(self):
        result = self.model.run(expected_digest="00" * 32)
        self.assertEqual(result["reason"], "payload_hash_mismatch")
        self.assertEqual(result["passed_phases"], ())
        self.assert_safe(result)

    def test_disallows_non_bytes_payload(self):
        for value in ("str", None, bytearray(DUMMY_BYTES)):
            with self.subTest(t=type(value).__name__):
                self.assert_safe(self.model.run(replacement=value))

    def test_disallows_malformed_digest(self):
        for value in ("", None, 5, "bad"):
            with self.subTest(value=value):
                self.assert_safe(self.model.run(expected_digest=value))

    def test_existing_target_never_overwritten(self):
        self.model.target.mkdir()
        marker = self.model.target / "marker.txt"
        marker.write_bytes(b"ORIGINAL-DO-NOT-OVERWRITE")
        result = self.model.run()
        self.assertEqual(result["reason"], "target_collision")
        self.assertEqual(marker.read_bytes(), b"ORIGINAL-DO-NOT-OVERWRITE")
        self.assert_safe(result)

    def test_existing_staging_never_overwritten(self):
        self.model.staging.mkdir()
        marker = self.model.staging / "marker.txt"
        marker.write_bytes(b"ORIGINAL-DO-NOT-OVERWRITE")
        result = self.model.run()
        self.assertEqual(result["reason"], "staging_collision")
        self.assertEqual(marker.read_bytes(), b"ORIGINAL-DO-NOT-OVERWRITE")
        self.assertTrue(result["pointer_bytes_restored"])

    def test_spoofed_existing_target_flag_fails_closed(self):
        result = self.model.run(existing_target=True)
        self.assertEqual(result["reason"], "target_collision")
        self.assert_safe(result)

    def test_symlink_hazard_flag_fails_closed(self):
        result = self.model.run(inject_symlink=True)
        self.assertEqual(result["reason"], "unsafe_path")
        self.assert_safe(result)

    def test_durable_mock_orders_survive_multiple_rehearsals(self):
        for _ in range(3):
            self.assert_safe(self.model.run())

    def test_no_target_ever_activated(self):
        self.assert_safe(self.model.run())
        self.assertFalse(self.model.target.exists())

    def test_original_pointer_is_byte_identical_after_late_failure(self):
        self.model.current.write_bytes(b"LEGACY\r\n")
        result = self.model.run(interrupt="post_swap")
        self.assertFalse(result["can_install_or_deploy"])
        self.assertTrue(result["pointer_bytes_restored"])
        self.assertEqual(self.model.current.read_bytes(), b"LEGACY\r\n")
        self.assertFalse(self.model.staging.exists())


if __name__ == "__main__":
    unittest.main()
