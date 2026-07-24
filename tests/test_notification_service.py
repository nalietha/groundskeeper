import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from core.notification_service import NotificationService

FULL_CONFIG = {
    "smtp_server": "smtp.example.com",
    "smtp_port": 587,
    "sender_email": "me@example.com",
    "sender_password": "secret",
}


class NotificationServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.storage = os.path.join(self.tmp, "subscribers.json")

    def _service(self, config=None):
        return NotificationService(config if config is not None else dict(FULL_CONFIG),
                                   storage_file=self.storage)

    # --- SMTP config resolution --------------------------------------------
    def test_resolve_smtp_config_from_email_config(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            svc = self._service()
            resolved = svc._resolve_smtp_config()
        self.assertEqual(resolved, ("smtp.example.com", 587, "me@example.com", "secret"))

    def test_resolve_smtp_config_incomplete_returns_none(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            svc = self._service({"smtp_server": "only.server"})
            self.assertIsNone(svc._resolve_smtp_config())

    def test_resolve_smtp_config_env_overrides(self):
        env = {
            "SMTP_SERVER": "env.server",
            "SMTP_SENDER_EMAIL": "env@x.com",
            "SMTP_SENDER_PASSWORD": "envpw",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            svc = self._service({})
            server, port, sender, password = svc._resolve_smtp_config()
        self.assertEqual(server, "env.server")
        self.assertEqual(sender, "env@x.com")
        self.assertEqual(password, "envpw")

    # --- Subscriber management ---------------------------------------------
    def test_add_new_subscriber(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee", alias="Al", days=["Monday"])
        subs = svc._load_subscribers()
        self.assertEqual(len(subs["Coffee"]), 1)
        self.assertEqual(subs["Coffee"][0]["contact"], "a@x.com")
        self.assertEqual(subs["Coffee"][0]["days"], ["Monday"])

    def test_add_subscriber_updates_existing(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee", alias="Al", days=["Monday"])
        svc.add_subscriber("a@x.com", "Coffee", alias="Alice", days=["Tuesday"])
        subs = svc._load_subscribers()
        self.assertEqual(len(subs["Coffee"]), 1)  # no duplicate
        self.assertEqual(subs["Coffee"][0]["alias"], "Alice")
        self.assertEqual(subs["Coffee"][0]["days"], ["Tuesday"])

    def test_add_subscriber_defaults_to_weekdays(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee")
        subs = svc._load_subscribers()
        self.assertEqual(
            subs["Coffee"][0]["days"],
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        )

    def test_load_subscribers_old_format(self):
        with open(self.storage, "w", encoding="utf-8") as f:
            json.dump({"subscribers": {"Coffee": [{"contact": "a@x.com"}]}}, f)
        svc = self._service()
        self.assertIn("Coffee", svc._load_subscribers())

    def test_load_subscribers_new_format(self):
        with open(self.storage, "w", encoding="utf-8") as f:
            json.dump({"Tea": [{"contact": "b@x.com"}]}, f)
        svc = self._service()
        self.assertIn("Tea", svc._load_subscribers())

    # --- Removal / lookup ---------------------------------------------------
    def test_remove_subscriber_from_theme(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee", days=["Monday"])
        svc.add_subscriber("b@x.com", "Coffee", days=["Monday"])
        self.assertTrue(svc.remove_subscriber("a@x.com", "Coffee"))
        remaining = [s["contact"] for s in svc._load_subscribers()["Coffee"]]
        self.assertEqual(remaining, ["b@x.com"])

    def test_remove_subscriber_returns_false_when_absent(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee", days=["Monday"])
        self.assertFalse(svc.remove_subscriber("ghost@x.com", "Coffee"))
        self.assertFalse(svc.remove_subscriber("a@x.com", "Nonexistent"))

    def test_remove_last_subscriber_prunes_theme(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee", days=["Monday"])
        svc.remove_subscriber("a@x.com", "Coffee")
        self.assertNotIn("Coffee", svc._load_subscribers())

    def test_remove_subscriber_handles_legacy_string_entry(self):
        with open(self.storage, "w", encoding="utf-8") as f:
            json.dump({"Coffee": ["legacy@x.com"]}, f)
        svc = self._service()
        self.assertTrue(svc.remove_subscriber("legacy@x.com", "Coffee"))

    def test_remove_all_subscriptions(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee", days=["Monday"])
        svc.add_subscriber("a@x.com", "Tea", days=["Tuesday"])
        svc.add_subscriber("b@x.com", "Coffee", days=["Monday"])
        removed = svc.remove_all_subscriptions("a@x.com")
        self.assertEqual(sorted(removed), ["Coffee", "Tea"])
        subs = svc._load_subscribers()
        self.assertNotIn("Tea", subs)  # pruned (was a@x.com only)
        self.assertEqual([s["contact"] for s in subs["Coffee"]], ["b@x.com"])

    def test_remove_all_subscriptions_when_none(self):
        svc = self._service()
        self.assertEqual(svc.remove_all_subscriptions("ghost@x.com"), [])

    def test_get_subscriptions_for(self):
        svc = self._service()
        svc.add_subscriber("a@x.com", "Coffee", alias="Al", days=["Monday"])
        svc.add_subscriber("a@x.com", "Tea", alias="Al", days=["Friday"])
        svc.add_subscriber("b@x.com", "Coffee", days=["Monday"])
        subs = svc.get_subscriptions_for("a@x.com")
        themes = sorted(s["theme_name"] for s in subs)
        self.assertEqual(themes, ["Coffee", "Tea"])
        coffee = next(s for s in subs if s["theme_name"] == "Coffee")
        self.assertEqual(coffee["days"], ["Monday"])
        self.assertEqual(coffee["alias"], "Al")

    def test_get_subscriptions_for_unknown_contact(self):
        svc = self._service()
        self.assertEqual(svc.get_subscriptions_for("ghost@x.com"), [])

    # --- Sending (SMTP mocked) ---------------------------------------------
    def test_send_test_email_success(self):
        svc = self._service()
        with mock.patch("core.notification_service.smtplib.SMTP") as smtp:
            ok, msg = svc.send_test_email()
        self.assertTrue(ok)
        smtp.assert_called_once()

    def test_send_test_email_incomplete_config(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            svc = self._service({})
            ok, msg = svc.send_test_email()
        self.assertFalse(ok)

    def test_send_test_email_smtp_failure(self):
        svc = self._service()
        with mock.patch("core.notification_service.smtplib.SMTP",
                        side_effect=Exception("boom")):
            ok, msg = svc.send_test_email()
        self.assertFalse(ok)
        self.assertIn("boom", msg)

    def test_send_notification_test_mode_sends_to_sender(self):
        svc = self._service()
        svc.jinja_env = mock.MagicMock()
        svc.jinja_env.get_template.return_value.render.return_value = "<html>"
        with mock.patch("core.notification_service.smtplib.SMTP") as smtp:
            svc.send_notification("Coffee", {"main_message": "hi"}, test_mode=True)
        sent = smtp.return_value.__enter__.return_value.send_message
        self.assertEqual(sent.call_count, 1)

    def test_send_notification_filters_by_day(self):
        svc = self._service()
        svc.jinja_env = mock.MagicMock()
        svc.jinja_env.get_template.return_value.render.return_value = "<html>"
        # Subscriber scheduled only for a day that is NOT today -> no send.
        today = datetime.now().strftime("%A")
        other_day = "Monday" if today != "Monday" else "Tuesday"
        svc.add_subscriber("a@x.com", "Coffee", days=[other_day])
        with mock.patch("core.notification_service.smtplib.SMTP") as smtp:
            svc.send_notification("Coffee", {"main_message": "hi"})
        smtp.assert_not_called()

    def test_send_notification_includes_unsubscribe_url(self):
        svc = self._service()
        svc.jinja_env = mock.MagicMock()
        render = svc.jinja_env.get_template.return_value.render
        render.return_value = "<html>"
        with mock.patch("core.notification_service.smtplib.SMTP"):
            svc.send_notification("Coffee", {"main_message": "hi"}, test_mode=True)
        _, kwargs = render.call_args
        self.assertIn("unsubscribe_url", kwargs)
        self.assertIn("/unsubscribe", kwargs["unsubscribe_url"])
        self.assertIn("theme=Coffee", kwargs["unsubscribe_url"])

    def test_send_notification_sends_when_scheduled_today(self):
        svc = self._service()
        svc.jinja_env = mock.MagicMock()
        svc.jinja_env.get_template.return_value.render.return_value = "<html>"
        today = datetime.now().strftime("%A")
        svc.add_subscriber("a@x.com", "Coffee", days=[today])
        with mock.patch("core.notification_service.smtplib.SMTP") as smtp:
            svc.send_notification("Coffee", {"main_message": "hi"})
        sent = smtp.return_value.__enter__.return_value.send_message
        self.assertEqual(sent.call_count, 1)


if __name__ == "__main__":
    unittest.main()
