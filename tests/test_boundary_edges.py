"""Extra negative controls for public synthetic-only state transitions."""
from concurrent.futures import ThreadPoolExecutor
import json
import unittest

from synthetic_crm.demo_lease import DemoLease
from synthetic_crm.public_smoke import encode_status, status


class PureBoundaryEdges(unittest.TestCase):
    def test_new_lease_is_unavailable(self):
        lease = DemoLease()
        for candidate in ("", "fake", None, True):
            with self.subTest(candidate=candidate):
                self.assertFalse(lease.check(candidate, 12))

    def test_token_is_opaque_and_distinct_between_leases(self):
        first = DemoLease().rotate(10)
        second = DemoLease().rotate(10)
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 24)

    def test_boundary_before_and_at_expiry(self):
        lease = DemoLease()
        token = lease.rotate(10, seconds=30)
        self.assertTrue(lease.check(token, 39.99))
        self.assertFalse(lease.check(token, 40))

    def test_bad_credential_does_not_revoke_correct_token(self):
        lease = DemoLease()
        token = lease.rotate(10)
        self.assertFalse(lease.check(token + "x", 11))
        self.assertTrue(lease.check(token, 11))

    def test_explicit_revoke_stays_revoked(self):
        lease = DemoLease()
        token = lease.rotate(10)
        lease.revoke()
        self.assertFalse(lease.check(token, 11))
        self.assertFalse(lease.check(token, 12))

    def test_zero_and_negative_clock_are_invalid(self):
        lease = DemoLease()
        for clock in (True, None, "5", float("inf"), float("nan"), -1):
            with self.subTest(clock=clock), self.assertRaises(ValueError):
                lease.rotate(clock)

    def test_invalid_ttl_rejected_before_issuance(self):
        lease = DemoLease()
        for ttl in (False, 0, 121, -1, 1.2, "30"):
            with self.subTest(ttl=ttl), self.assertRaises(ValueError):
                lease.rotate(10, seconds=ttl)
        self.assertFalse(lease.check("anything", 11))

    def test_untrusted_clock_never_authorizes(self):
        lease = DemoLease()
        token = lease.rotate(10)
        for clock in (None, False, "11", float("inf"), float("nan"), -5):
            with self.subTest(clock=clock):
                self.assertFalse(lease.check(token, clock))

    def test_parallel_checks_are_read_only(self):
        lease = DemoLease()
        token = lease.rotate(10)
        with ThreadPoolExecutor(max_workers=4) as pool:
            answers = list(pool.map(lambda _: lease.check(token, 11), range(32)))
        self.assertEqual(answers, [True] * 32)

    def test_public_status_rejects_non_mapping_values(self):
        for item in ([], "anything", 22):
            with self.subTest(item=item), self.assertRaises(ValueError):
                encode_status(item)

    def test_public_status_denies_boolean_substitution(self):
        for item in (0, 1, None, "false", []):
            with self.subTest(item=item), self.assertRaises(ValueError):
                encode_status({**status(), "can_install_or_deploy": item})

    def test_public_status_no_additional_capabilities(self):
        payload = json.loads(encode_status())
        self.assertEqual(set(payload), {"version", "health", "can_install_or_deploy"})
        self.assertIs(payload["can_install_or_deploy"], False)


if __name__ == "__main__":
    unittest.main()
