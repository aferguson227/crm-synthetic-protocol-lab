"""Public synthetic status fixture only. No private CRM imports."""
import json

FIELDS = ("version", "health", "can_install_or_deploy")

def status():
    return {"version": "SYNTHETIC-ONLY", "health": "unknown",
            "can_install_or_deploy": False}

def encode_status(data=None):
    data = status() if data is None else data
    if not isinstance(data, dict) or set(data) != set(FIELDS):
        raise ValueError("invalid synthetic status shape")
    if data["version"] != "SYNTHETIC-ONLY" or data["can_install_or_deploy"] is not False:
        raise ValueError("non-deployable invariant")
    if data["health"] not in ("unknown", "healthy", "degraded"):
        raise ValueError("unexpected synthetic health")
    return json.dumps(data, sort_keys=True).encode("utf-8")
