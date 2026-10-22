"""Only public, synthetic, read-only status tests."""
import json
import unittest

from synthetic_crm.public_smoke import encode_status, status


class PublicStatusSmoke(unittest.TestCase):
    def test_status_is_non_deployable(self):
        self.assertIs(status()["can_install_or_deploy"], False)

    def test_encoded_status(self):
        self.assertEqual(json.loads(encode_status()), status())

    def test_no_extra_fields(self):
        with self.assertRaises(ValueError):
            encode_status({**status(), "private": "not allowed"})

    def test_cannot_enable_install(self):
        with self.assertRaises(ValueError):
            encode_status({**status(), "can_install_or_deploy": True})

    def test_unknown_version_denied(self):
        with self.assertRaises(ValueError):
            encode_status({**status(), "version": "CRM-PRODUCTION"})

    def test_unknown_health_denied(self):
        with self.assertRaises(ValueError):
            encode_status({**status(), "health": "trade"})


if __name__ == "__main__":
    unittest.main()
