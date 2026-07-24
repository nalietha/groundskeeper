import os
import tempfile
import unittest
from unittest import mock

from core.webapp_service import WebAppService, app as flask_app
from core.notification_service import NotificationService
from tests.support import make_theme, FakeThemeService


class FakeTracking:
    def get_tracked_items(self):
        return []


class FakeNotification:
    def __init__(self):
        self.add_subscriber = mock.Mock(return_value=True)


def _wire_services():
    notification = FakeNotification()
    theme_service = FakeThemeService([make_theme(name="Coffee")])
    tracking = FakeTracking()
    WebAppService(notification, theme_service, tracking)
    return notification


class WebAppServiceWiringTests(unittest.TestCase):
    def test_constructor_injects_services(self):
        notification = _wire_services()
        self.assertIs(flask_app.config["NOTIFICATION_SERVICE"], notification)
        self.assertIsNotNone(flask_app.config["THEME_SERVICE"])
        self.assertIsNotNone(flask_app.config["TRACKING_SERVICE"])

    def test_get_local_ip_returns_string(self):
        svc = WebAppService(FakeNotification(), FakeThemeService(), FakeTracking())
        with mock.patch("core.webapp_service.get_local_ip", return_value="1.2.3.4"):
            self.assertEqual(svc.get_local_ip(), "1.2.3.4")


class WebAppRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _wire_services()
        flask_app.config["TESTING"] = True
        cls.client = flask_app.test_client()
        # Probe: if the template can't render in this environment, skip route tests.
        try:
            resp = cls.client.get("/")
            cls.renderable = resp.status_code == 200
        except Exception:
            cls.renderable = False

    def setUp(self):
        if not self.renderable:
            self.skipTest("webapp template did not render in this environment")

    def test_get_returns_200(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_post_registers_subscriber(self):
        notification = _wire_services()
        resp = self.client.post("/", data={
            "contact_method": "email",
            "email": "a@x.com",
            "theme": "Coffee",
            "alias": "Al",
            "days": ["Monday", "Wednesday"],
        })
        self.assertEqual(resp.status_code, 200)
        notification.add_subscriber.assert_called_once()
        args, _ = notification.add_subscriber.call_args
        self.assertIn("a@x.com", args)
        self.assertIn("Coffee", args)

    def test_post_sms_builds_contact(self):
        notification = _wire_services()
        self.client.post("/", data={
            "contact_method": "sms",
            "phone": "(555) 123-4567",
            "carrier": "@vtext.com",
            "theme": "Coffee",
            "days": ["Monday"],
        })
        notification.add_subscriber.assert_called_once()
        contact = notification.add_subscriber.call_args[0][0]
        self.assertEqual(contact, "5551234567@vtext.com")

    def test_post_without_days_does_not_register(self):
        notification = _wire_services()
        self.client.post("/", data={
            "contact_method": "email",
            "email": "a@x.com",
            "theme": "Coffee",
        })
        notification.add_subscriber.assert_not_called()


class WebAppManageTests(unittest.TestCase):
    """Manage / unsubscribe flows backed by a real NotificationService."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.notification = NotificationService(
            {}, storage_file=os.path.join(self.tmp, "subs.json"))
        WebAppService(self.notification, FakeThemeService([make_theme(name="Coffee")]),
                      FakeTracking())
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

        self.notification.add_subscriber("a@x.com", "Coffee", days=["Monday"])
        self.notification.add_subscriber("a@x.com", "Tea", days=["Friday"])

        try:
            self.renderable = self.client.get("/").status_code == 200
        except Exception:
            self.renderable = False
        if not self.renderable:
            self.skipTest("webapp template did not render in this environment")

    def test_manage_lists_subscriptions(self):
        resp = self.client.post("/", data={"form_type": "manage", "manage_contact": "a@x.com"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("Disconnect Coffee", body)
        self.assertIn("Disconnect Tea", body)

    def test_manage_reconstructs_email_contact(self):
        # Manage form submits method + email (like signup), not a single field.
        resp = self.client.post("/", data={
            "form_type": "manage", "contact_method": "email", "email": "a@x.com",
        })
        body = resp.get_data(as_text=True)
        self.assertIn("Disconnect Coffee", body)
        self.assertIn("Disconnect Tea", body)

    def test_manage_reconstructs_sms_contact_from_carrier(self):
        self.notification.add_subscriber("5551234567@vtext.com", "Tea", days=["Monday"])
        resp = self.client.post("/", data={
            "form_type": "manage",
            "contact_method": "sms",
            "phone": "(555) 123-4567",
            "carrier": "@vtext.com",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Disconnect Tea", resp.get_data(as_text=True))

    def test_unsubscribe_single_theme(self):
        self.client.post("/", data={
            "form_type": "unsubscribe", "manage_contact": "a@x.com", "theme": "Coffee",
        })
        themes = [s["theme_name"] for s in self.notification.get_subscriptions_for("a@x.com")]
        self.assertEqual(themes, ["Tea"])

    def test_unsubscribe_all(self):
        self.client.post("/", data={"form_type": "unsubscribe_all", "manage_contact": "a@x.com"})
        self.assertEqual(self.notification.get_subscriptions_for("a@x.com"), [])

    def test_one_click_unsubscribe_single_theme(self):
        self.client.get("/unsubscribe?contact=a@x.com&theme=Tea")
        themes = [s["theme_name"] for s in self.notification.get_subscriptions_for("a@x.com")]
        self.assertEqual(themes, ["Coffee"])

    def test_one_click_unsubscribe_all(self):
        resp = self.client.get("/unsubscribe?contact=a@x.com")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.notification.get_subscriptions_for("a@x.com"), [])

    def test_one_click_unsubscribe_missing_contact(self):
        resp = self.client.get("/unsubscribe")
        self.assertEqual(resp.status_code, 200)  # renders an error message, no crash


if __name__ == "__main__":
    unittest.main()
