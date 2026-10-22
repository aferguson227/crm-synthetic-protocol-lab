"""Independent, in-memory upgrade decision rehearsal for dummy test data only.

No private application modules, installer execution, filesystem writes, exchange
connections, device access, or permission to activate any real release.
"""
from copy import deepcopy
import unittest

REQUIRED = frozenset({
    "sample_digest", "sample_allowlist", "sample_windows_replay",
    "sample_restore", "sample_continuity", "sample_reviewer",
})
FAKE_SHA = "ab" * 32
PHASES = (
    "draft_review", "fake_stage", "fake_hash_check", "fake_pointer_change",
    "mock_health_probe", "mandatory_restore",
)


class MockGate:
    """Never authorises an actual installation, even when all dummy checks pass."""

    def __init__(self):
        self.state = {
            "active_pointer": "OLD_DEMO",
            "durable_data": {"synthetic_deals": ["open-a", "open-b"]},
            "synthetic_order_book": {"open_exit": 2},
            "demo_credentials": "PLACEHOLDER_ONLY",
        }

    def review(self, evidence, *, proposed_sha=FAKE_SHA, expected_sha=FAKE_SHA,
               now=100, expires_at=120, isolated=True, reviewer_confirmed=True,
               existing_target=False, interruption=None):
        original = deepcopy(self.state)
        reason = "DUMMY_SUCCESS_RESTORED"
        completed = []
        try:
            if type(now) is not int or type(expires_at) is not int or not 0 <= now < expires_at:
                raise ValueError("stale_or_invalid_mock_evidence")
            if not isinstance(evidence, dict) or set(evidence) != REQUIRED:
                raise ValueError("missing_or_extra_mock_evidence")
            if any(value is not True for value in evidence.values()):
                raise ValueError("mock_gate_not_passed")
            if (type(proposed_sha) is not str or len(proposed_sha) != 64
                    or proposed_sha != expected_sha):
                raise ValueError("mock_hash_mismatch")
            if isolated is not True or reviewer_confirmed is not True:
                raise ValueError("missing_mock_isolation_or_review")
            if existing_target:
                raise ValueError("mock_target_collision")
            for phase in PHASES:
                if interruption == phase:
                    raise ValueError("synthetic_interruption_" + phase)
                completed.append(phase)
                if phase == "fake_pointer_change":
                    self.state["active_pointer"] = "NEW_DEMO_ONLY"
        except ValueError as exc:
            reason = str(exc)
        finally:
            self.state = original
        return {
            "reason": reason,
            "completed_phases": tuple(completed),
            "state_restored": self.state == original,
            "can_install_or_deploy": False,
            "may_modify_orders": False,
            "private_release_certified": False,
        }


def dummy_evidence():
    return {name: True for name in REQUIRED}


class MockReleaseRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.model = MockGate()
        self.before = deepcopy(self.model.state)

    def verify_denial(self, report):
        self.assertFalse(report["can_install_or_deploy"])
        self.assertFalse(report["may_modify_orders"])
        self.assertFalse(report["private_release_certified"])
        self.assertTrue(report["state_restored"])
        self.assertEqual(self.model.state, self.before)

    def test_fully_green_dummy_case_remains_non_deployable(self):
        report = self.model.review(dummy_evidence())
        self.assertEqual(report["reason"], "DUMMY_SUCCESS_RESTORED")
        self.assertEqual(report["completed_phases"], PHASES)
        self.verify_denial(report)

    def test_missing_each_dummy_receipt(self):
        for name in REQUIRED:
            with self.subTest(name=name):
                evidence = dummy_evidence()
                del evidence[name]
                report = self.model.review(evidence)
                self.assertEqual(report["reason"], "missing_or_extra_mock_evidence")
                self.verify_denial(report)

    def test_unexpected_dummy_receipt_is_rejected(self):
        self.assertEqual(self.model.review({**dummy_evidence(), "extra": True})["reason"],
                         "missing_or_extra_mock_evidence")
        self.assertEqual(self.model.state, self.before)

    def test_false_or_non_boolean_approval_is_rejected(self):
        for value in (False, 1, "true", None):
            with self.subTest(value=value):
                report = self.model.review({**dummy_evidence(), "sample_reviewer": value})
                self.assertEqual(report["reason"], "mock_gate_not_passed")
                self.verify_denial(report)

    def test_wrong_digest_fails_closed(self):
        report = self.model.review(dummy_evidence(), proposed_sha="00" * 32)
        self.assertEqual(report["reason"], "mock_hash_mismatch")
        self.verify_denial(report)

    def test_malformed_digest_fails_closed(self):
        for sha in ("short", 5, None):
            with self.subTest(sha=sha):
                self.verify_denial(self.model.review(dummy_evidence(), proposed_sha=sha))

    def test_expired_evidence_fails_closed(self):
        report = self.model.review(dummy_evidence(), now=120)
        self.assertEqual(report["reason"], "stale_or_invalid_mock_evidence")
        self.verify_denial(report)

    def test_malformed_time_fails_closed(self):
        for now in (True, "100", -1, 121):
            with self.subTest(now=now):
                self.verify_denial(self.model.review(dummy_evidence(), now=now))

    def test_non_isolated_environment_fails_closed(self):
        for value in (False, "true", None):
            with self.subTest(value=value):
                self.verify_denial(self.model.review(dummy_evidence(), isolated=value))

    def test_missing_independent_review_fails_closed(self):
        self.verify_denial(self.model.review(dummy_evidence(), reviewer_confirmed=False))

    def test_existing_target_refused_without_mutations(self):
        report = self.model.review(dummy_evidence(), existing_target=True)
        self.assertEqual(report["reason"], "mock_target_collision")
        self.assertEqual(report["completed_phases"], ())
        self.verify_denial(report)

    def test_interruption_at_every_phase_restores_original(self):
        for phase in PHASES:
            with self.subTest(phase=phase):
                report = self.model.review(dummy_evidence(), interruption=phase)
                self.assertEqual(report["reason"], "synthetic_interruption_" + phase)
                self.verify_denial(report)

    def test_success_preserves_synthetic_exit_records(self):
        self.verify_denial(self.model.review(dummy_evidence()))
        self.assertEqual(self.model.state["synthetic_order_book"]["open_exit"], 2)

    def test_success_preserves_dummy_credential_marker(self):
        self.verify_denial(self.model.review(dummy_evidence()))
        self.assertEqual(self.model.state["demo_credentials"], "PLACEHOLDER_ONLY")

    def test_does_not_mutate_external_evidence(self):
        evidence = dummy_evidence()
        old_evidence = deepcopy(evidence)
        self.verify_denial(self.model.review(evidence))
        self.assertEqual(evidence, old_evidence)

    def test_replay_twice_has_no_authority_accumulation(self):
        self.verify_denial(self.model.review(dummy_evidence()))
        self.verify_denial(self.model.review(dummy_evidence()))


if __name__ == "__main__":
    unittest.main()
