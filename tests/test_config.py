import json
import os
import tempfile
import unittest
from unittest import mock

from configs.config import Config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _write(self, data):
        path = os.path.join(self.tmp, "appsettings.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_defaults_when_file_missing(self):
        cfg = Config(filename=os.path.join(self.tmp, "nope.json"))
        self.assertEqual(cfg.SCREEN_WIDTH, 240)
        self.assertEqual(cfg.SCREEN_HEIGHT, 320)
        self.assertEqual(cfg.DEFAULT_THEME, "Coffee")
        self.assertEqual(cfg.LATENCY_MS, 1500)

    def test_loads_values_from_file(self):
        path = self._write({
            "screen": {"width": 480, "height": 640, "base_width_for_scaling": 400},
            "app": {"default_theme": "Tea"},
            "timing": {"inactivity_timeout_ms": 9000, "use_24h_clock": True},
            "latency": {"menu_load_ms": 200, "loading_image_interval_ms": 100},
        })
        cfg = Config(filename=path)
        self.assertEqual(cfg.SCREEN_WIDTH, 480)
        self.assertEqual(cfg.SCREEN_HEIGHT, 640)
        self.assertEqual(cfg.BASE_WIDTH, 400)
        self.assertEqual(cfg.DEFAULT_THEME, "Tea")
        self.assertEqual(cfg.INACTIVITY_TIMEOUT_MS, 9000)
        self.assertTrue(cfg.USE_24H_CLOCK)
        self.assertEqual(cfg.LATENCY_MS, 200)

    def test_partial_file_keeps_defaults(self):
        path = self._write({"screen": {"width": 999}})
        cfg = Config(filename=path)
        self.assertEqual(cfg.SCREEN_WIDTH, 999)
        self.assertEqual(cfg.SCREEN_HEIGHT, 320)  # default preserved

    def test_email_config_loaded(self):
        path = self._write({"email": {"sender_email": "file@x.com"}})
        with mock.patch.dict(os.environ, {}, clear=True):
            cfg = Config(filename=path)
        self.assertEqual(cfg.EMAIL_CONFIG["sender_email"], "file@x.com")

    def test_env_overrides_email_credentials(self):
        path = self._write({"email": {"sender_email": "file@x.com"}})
        env = {"SMTP_SENDER_EMAIL": "env@x.com", "SMTP_SENDER_PASSWORD": "envpw"}
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = Config(filename=path)
        self.assertEqual(cfg.EMAIL_CONFIG["sender_email"], "env@x.com")
        self.assertEqual(cfg.EMAIL_CONFIG["sender_password"], "envpw")


if __name__ == "__main__":
    unittest.main()
