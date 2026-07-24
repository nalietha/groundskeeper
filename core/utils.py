# groundskeeper/core/utils.py
"""Small shared helpers used across services and views."""
import json
import socket


def load_json(path, default=None, encoding="utf-8"):
    """Loads JSON from ``path``, returning ``default`` if the file is missing or unparseable.

    Centralizes the ``try/open/json.load/except`` pattern that was previously
    hand-rolled in nearly every service.
    """
    try:
        with open(path, "r", encoding=encoding) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def get_local_ip(fallback="127.0.0.1"):
    """Best-effort discovery of the machine's LAN IP address.

    Opens a throwaway UDP socket toward a public address so the OS picks the
    outbound interface; nothing is actually sent.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception:
        return fallback
