"""Synthetic in-memory lease used only for isolated public tests."""
import hmac
import math
import secrets


class DemoLease:
    def __init__(self):
        self._token = None
        self.expiry = 0
        self.revoked = True

    def rotate(self, now, seconds=30):
        if not _time(now) or type(seconds) is not int or not 1 <= seconds <= 120:
            raise ValueError("invalid demo lease")
        self._token = secrets.token_urlsafe(24)
        self.expiry = now + seconds
        self.revoked = False
        return self._token

    def check(self, token, now):
        return bool(not self.revoked and _time(now) and now < self.expiry
                    and isinstance(token, str) and self._token
                    and hmac.compare_digest(self._token, token))

    def revoke(self):
        self.revoked = True


def _time(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0
