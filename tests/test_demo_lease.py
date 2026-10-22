"""Isolation tests for a deliberately fake in-memory lease."""
import unittest

from synthetic_crm.demo_lease import DemoLease


class DemoLeaseTests(unittest.TestCase):
    def test_no_lease_by_default(self):
        self.assertFalse(DemoLease().check("unknown", 1))

    def test_lease_expires(self):
        lease = DemoLease()
        token = lease.rotate(10, 20)
        self.assertTrue(lease.check(token, 29))
        self.assertFalse(lease.check(token, 30))

    def test_rotation_revokes_old_token(self):
        lease = DemoLease()
        old = lease.rotate(10)
        new = lease.rotate(11)
        self.assertNotEqual(old, new)
        self.assertFalse(lease.check(old, 12))
        self.assertTrue(lease.check(new, 12))

    def test_explicit_revocation(self):
        lease = DemoLease()
        token = lease.rotate(10)
        lease.revoke()
        self.assertFalse(lease.check(token, 11))

    def test_invalid_time_and_duration(self):
        lease = DemoLease()
        for ttl in (0, 121, True, 0.5):
            with self.subTest(ttl=ttl), self.assertRaises(ValueError):
                lease.rotate(10, ttl)
        token = lease.rotate(10)
        self.assertFalse(lease.check(token, float("nan")))


if __name__ == "__main__":
    unittest.main()
