import unittest
from datetime import date, time
from unittest.mock import Mock
from unittest.mock import patch

import requests
import tennis_meetandplay


class FakeResponse:
    def __init__(self, text, url, status_code=200):
        self.text = text
        self.url = url
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def calendar_html(
    *,
    selected_date="20-11-2026",
    sport_id="1",
    court_cards=True,
    no_slots=False,
):
    cards = ""
    if court_cards:
        cards = """
        <div class="mp-court-type"><b>Buiten - Dubbelspel</b></div>
        <div class="timeslots">
          <h4>60 minuten</h4>
          <div class="timeslot-container">
            <a class="timeslot" wire:click="selectSlot(123)">
              <div class="timeslot-time">11:00 - 12:00
                <small>60 minuten</small>
              </div>
              <div class="timeslot-name">Baan 5</div>
              <span>Toevoegen</span>
            </a>
          </div>
        </div>
        """
    elif no_slots:
        cards = """
        <div class="mp-court-type"><b>Buiten - Dubbelspel</b></div>
        <div class="timeslots">Er zijn geen tijdslots gevonden voor je huidige filters</div>
        """
    else:
        cards = """
        <div class="mp-court-type"><b>Buiten - Dubbelspel</b></div>
        <div class="timeslots"></div>
        """

    return f"""
    <html><body>
      <div wire:snapshot='{{"data":{{"date":"{selected_date}",
        "tenantSportId":{sport_id}}},"memo":{{"name":"club.v2.court-show",
        "path":"club/02477"}}}}'></div>
      <select id="sportId">
        <option value="1">Tennis</option>
        <option value="2">Padel</option>
      </select>
      {cards}
    </body></html>
    """


class MeetAndPlayDirectCheckTests(unittest.TestCase):
    def setUp(self):
        self.booking_url = "https://meetandplay.nl/club/02477"
        self.selected_date = date(2026, 11, 20)
        self.selected_time = time(11, 0)

    def check_page(self, html, url=None):
        response = FakeResponse(
            html,
            url or f"{self.booking_url}?date=2026-11-20",
        )
        with patch.object(tennis_meetandplay.requests, "get", return_value=response):
            return tennis_meetandplay.check_meetandplay_availability(
                self.booking_url,
                self.selected_date,
                self.selected_time,
                60,
            )

    def test_exact_selectable_court_is_available(self):
        result = self.check_page(calendar_html())

        self.assertEqual(
            result["status"],
            "Available - selectable on the booking page",
        )
        self.assertEqual(
            result["available_courts"],
            [{"name": "Baan 5", "environment": "outdoor"}],
        )

    def test_requests_the_selected_date_with_a_bounded_timeout(self):
        response = FakeResponse(
            calendar_html(),
            f"{self.booking_url}?date=2026-11-20",
        )
        with patch.object(
            tennis_meetandplay.requests,
            "get",
            return_value=response,
        ) as get:
            tennis_meetandplay.check_meetandplay_availability(
                f"{self.booking_url}?date=2026-11-19",
                self.selected_date,
                self.selected_time,
                60,
            )

        self.assertIn("date=2026-11-20", get.call_args.args[0])
        self.assertEqual(get.call_args.kwargs["timeout"], (3, 6))

    def test_http_429_is_reported_without_browser_fallback(self):
        response = FakeResponse(
            "",
            f"{self.booking_url}?date=2026-11-20",
            status_code=429,
        )
        with patch.object(tennis_meetandplay.requests, "get", return_value=response):
            result = tennis_meetandplay.check_meetandplay_availability(
                self.booking_url,
                self.selected_date,
                self.selected_time,
                60,
            )

        self.assertEqual(
            result["status"],
            "Could not verify - Meet & Play rate limited",
        )
        self.assertIn("HTTP 429", result["reason"])

    def test_date_mismatch_is_reported_without_browser_fallback(self):
        result = self.check_page(calendar_html(selected_date="21-11-2026"))

        self.assertEqual(
            result["status"],
            "Could not verify - requested date was not applied",
        )

    def test_sport_mismatch_uses_browser_fallback(self):
        self.assertIsNone(
            self.check_page(calendar_html(sport_id="2"))
        )

    def test_missing_interval_is_not_reported_as_available(self):
        result = self.check_page(calendar_html(court_cards=False))

        self.assertEqual(
            result["status"],
            "Could not verify - start time is not shown",
        )

    def test_different_interval_is_not_reported_as_available(self):
        html = calendar_html().replace("11:00 - 12:00", "11:30 - 12:30")

        result = self.check_page(html)

        self.assertEqual(
            result["status"],
            "Could not verify - start time is not shown",
        )

    def test_exact_interval_without_add_action_uses_browser_fallback(self):
        html = calendar_html().replace("Toevoegen", "Geboekt")

        result = self.check_page(html)

        self.assertIsNone(result)

    def test_explicit_empty_calendar_is_reported_conservatively(self):
        result = self.check_page(
            calendar_html(court_cards=False, no_slots=True)
        )

        self.assertEqual(
            result["status"],
            "Could not verify - no court slots are shown",
        )

    def test_rejects_non_meet_and_play_urls_without_requesting_them(self):
        with patch.object(tennis_meetandplay.requests, "get") as get:
            result = tennis_meetandplay.check_meetandplay_availability(
                "https://example.com/club/02477",
                self.selected_date,
                self.selected_time,
                60,
            )

        self.assertIsNone(result)
        get.assert_not_called()

    def test_redirect_to_another_host_uses_browser_fallback(self):
        result = self.check_page(
            calendar_html(),
            "https://example.com/club/02477?date=2026-11-20",
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
