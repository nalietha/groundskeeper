import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta

from core.tracking_service import TrackingService
from tests.support import (
    make_theme,
    FakeThemeService,
    RecordingNotificationService,
    StubService,
)


class TrackingServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state_file = os.path.join(self.tmp, "state.json")
        self.theme = make_theme(name="Coffee", timer_ms=60000)
        self.theme_service = FakeThemeService([self.theme])

    def _service(self, newsletter_service=None):
        return TrackingService(
            self.state_file,
            self.theme_service,
            joke_service=StubService(),
            affirmation_service=StubService(),
            newsletter_service=newsletter_service,
        )

    # --- CRUD / persistence -------------------------------------------------
    def test_start_tracking_creates_item(self):
        svc = self._service()
        item = svc.start_tracking_item("Coffee")
        self.assertEqual(item["theme_name"], "Coffee")
        self.assertIn("id", item)
        self.assertIsInstance(item["start_time"], datetime)
        self.assertEqual(len(svc.get_tracked_items()), 1)

    def test_start_tracking_replaces_same_theme(self):
        svc = self._service()
        first = svc.start_tracking_item("Coffee")
        second = svc.start_tracking_item("Coffee")
        items = svc.get_tracked_items()
        self.assertEqual(len(items), 1)
        self.assertNotEqual(first["id"], second["id"])

    def test_start_tracking_unknown_theme_returns_none(self):
        svc = self._service()
        self.assertIsNone(svc.start_tracking_item("Nonexistent"))

    def test_reset_all_items(self):
        svc = self._service()
        svc.start_tracking_item("Coffee")
        svc.reset_all_items()
        self.assertEqual(svc.get_tracked_items(), [])

    def test_state_persists_across_instances(self):
        svc = self._service()
        svc.start_tracking_item("Coffee")
        reloaded = self._service()
        items = reloaded.get_tracked_items()
        self.assertEqual(len(items), 1)
        # start_time round-trips back into a datetime object.
        self.assertIsInstance(items[0]["start_time"], datetime)

    # --- Notification decisions --------------------------------------------
    def test_started_notification_before_timer(self):
        svc = self._service()
        svc.start_tracking_item("Coffee")  # start_time = now, elapsed ~0 < timer
        notifier = RecordingNotificationService()
        svc.check_notifications(notifier)

        self.assertEqual(len(notifier.calls), 1)
        self.assertIn("has just been started", notifier.calls[0]["context"]["main_message"])
        self.assertIn("started", svc.get_tracked_items()[0]["notified_events"])

    def test_ready_notification_after_timer(self):
        svc = self._service()
        svc.start_tracking_item("Coffee")
        # Force the item well past its timer.
        svc.get_tracked_items()[0]["start_time"] = datetime.now() - timedelta(hours=1)

        notifier = RecordingNotificationService()
        svc.check_notifications(notifier)

        messages = [c["context"]["main_message"] for c in notifier.calls]
        self.assertTrue(any("is now ready" in m for m in messages))
        events = svc.get_tracked_items()[0]["notified_events"]
        self.assertIn("started", events)
        self.assertIn("ready", events)

    def test_no_duplicate_notifications(self):
        svc = self._service()
        svc.start_tracking_item("Coffee")
        svc.get_tracked_items()[0]["start_time"] = datetime.now() - timedelta(hours=1)

        notifier = RecordingNotificationService()
        svc.check_notifications(notifier)
        first_round = len(notifier.calls)
        svc.check_notifications(notifier)
        self.assertEqual(len(notifier.calls), first_round)  # nothing new

    def test_first_brew_of_day_includes_newsletter(self):
        class FakeNewsletter:
            def generate_morning_newsletter(self, theme):
                return {"newsletter_marker": "present"}

            def get_basic_content(self, theme):
                return {}

        svc = self._service(newsletter_service=FakeNewsletter())
        svc.start_tracking_item("Coffee")
        notifier = RecordingNotificationService()
        svc.check_notifications(notifier)

        self.assertEqual(notifier.calls[0]["context"].get("newsletter_marker"), "present")
        self.assertEqual(svc.last_newsletter_date, str(datetime.now().date()))

    def test_newsletter_content_delegates_to_service(self):
        class FakeNewsletter:
            def get_basic_content(self, theme):
                return {"joke": "delegated"}

        svc = self._service(newsletter_service=FakeNewsletter())
        self.assertEqual(svc._get_newsletter_content(self.theme), {"joke": "delegated"})

    def test_newsletter_content_empty_without_service(self):
        svc = self._service(newsletter_service=None)
        self.assertEqual(svc._get_newsletter_content(self.theme), {})


if __name__ == "__main__":
    unittest.main()
