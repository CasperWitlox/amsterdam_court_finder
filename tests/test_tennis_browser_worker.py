import io
import json
import sys
import types
import unittest
from unittest.mock import patch

import tennis_browser_worker


class FakeLocator:
    def wait_for(self, **kwargs):
        return None

    def input_value(self):
        return "01-01-2000"


class FakePage:
    def __init__(self):
        self.closed = False

    def goto(self, *args, **kwargs):
        return None

    def locator(self, selector):
        return FakeLocator()

    def wait_for_timeout(self, _milliseconds):
        return None

    def close(self):
        self.closed = True


class FakeContext:
    def __init__(self):
        self.pages = []
        self.close_calls = 0

    def new_page(self):
        page = FakePage()
        self.pages.append(page)
        return page

    def close(self):
        self.close_calls += 1


class FakeBrowser:
    def __init__(self):
        self.contexts = []
        self.closed = False

    def new_context(self, **kwargs):
        context = FakeContext()
        self.contexts.append(context)
        return context

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser

    def launch(self, **kwargs):
        return self.browser


class FakePlaywrightManager:
    def __init__(self, browser):
        self.playwright = types.SimpleNamespace(
            chromium=FakeChromium(browser)
        )

    def __enter__(self):
        return self.playwright

    def __exit__(self, *args):
        return False


class BrowserWorkerContextTests(unittest.TestCase):
    def test_worker_reuses_context_only_for_meetandplay_checks(self):
        browser = FakeBrowser()
        checked_contexts = []
        commands = [
            {
                "action": "CHECK",
                "url": "https://meetandplay.nl/club/00414",
                "_request_id": "first",
            },
            {
                "action": "CHECK",
                "url": "https://meetandplay.nl/club/02477",
                "_request_id": "second",
            },
            {
                "action": "CHECK",
                "url": "https://blauwwit.allbooked.com/booking",
                "_request_id": "third",
            },
            {"action": "STOP"},
        ]
        stdout = io.StringIO()
        fake_playwright = types.ModuleType("playwright")
        fake_sync_api = types.ModuleType("playwright.sync_api")
        fake_sync_api.sync_playwright = lambda: FakePlaywrightManager(browser)
        fake_playwright.sync_api = fake_sync_api

        def check_public_slot(_browser, command, context=None):
            checked_contexts.append(context)
            return {"status": "Available"}

        with (
            patch.dict(
                sys.modules,
                {
                    "playwright": fake_playwright,
                    "playwright.sync_api": fake_sync_api,
                },
            ),
            patch.object(tennis_browser_worker, "check_public_slot", check_public_slot),
            patch("sys.stdin", io.StringIO("\n".join(map(json.dumps, commands)))),
            patch("sys.stdout", stdout),
            patch("sys.stderr", io.StringIO()),
        ):
            self.assertEqual(tennis_browser_worker.run_worker(), 0)

        self.assertEqual(len(browser.contexts), 1)
        self.assertIsNotNone(checked_contexts[0])
        self.assertIs(checked_contexts[0], checked_contexts[1])
        self.assertIsNone(checked_contexts[2])
        self.assertTrue(browser.closed)

    def test_shared_context_stays_open_but_closes_each_page(self):
        context = FakeContext()
        browser = FakeBrowser()
        command = {
            "url": "https://example.test/booking",
            "date": "2026-11-20",
            "start_time": "18:00",
            "duration_minutes": 60,
        }

        with (
            patch.object(
                tennis_browser_worker,
                "url_for_date",
                side_effect=lambda url, selected_date: url,
            ),
            patch.object(tennis_browser_worker, "reject_optional_cookies"),
        ):
            result = tennis_browser_worker.check_public_slot(
                browser,
                command,
                context=context,
            )

        self.assertEqual(
            result["status"],
            "Could not verify - requested date was not applied",
        )
        self.assertEqual(context.close_calls, 0)
        self.assertTrue(context.pages[0].closed)

    def test_worker_owned_context_is_closed(self):
        browser = FakeBrowser()
        command = {
            "url": "https://example.test/booking",
            "date": "2026-11-20",
            "start_time": "18:00",
            "duration_minutes": 60,
        }

        with (
            patch.object(
                tennis_browser_worker,
                "url_for_date",
                side_effect=lambda url, selected_date: url,
            ),
            patch.object(tennis_browser_worker, "reject_optional_cookies"),
        ):
            result = tennis_browser_worker.check_public_slot(browser, command)

        self.assertEqual(
            result["status"],
            "Could not verify - requested date was not applied",
        )
        self.assertEqual(len(browser.contexts), 1)
        self.assertEqual(browser.contexts[0].close_calls, 1)


if __name__ == "__main__":
    unittest.main()
