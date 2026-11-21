"""Low-memory availability checks for the server-rendered Meet & Play calendar."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


MEET_AND_PLAY_HOST = "meetandplay.nl"
MEET_AND_PLAY_COMPONENT = "club.v2.court-show"
MEET_AND_PLAY_NO_SLOTS_TEXT = (
    "er zijn geen tijdslots gevonden voor je huidige filters"
)
TIME_PATTERN = re.compile(r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)")
COURT_NAME_PATTERN = re.compile(r"\bBaan\s+\S+", re.IGNORECASE)


def is_meetandplay_booking_url(booking_url: str) -> bool:
    try:
        parsed_url = urlparse(booking_url)
        port = parsed_url.port
    except ValueError:
        return False
    return (
        parsed_url.scheme.casefold() == "https"
        and (parsed_url.hostname or "").casefold() == MEET_AND_PLAY_HOST
        and port in (None, 443)
        and parsed_url.username is None
        and parsed_url.password is None
        and parsed_url.path.startswith("/club/")
        and re.fullmatch(r"/club/\d+", parsed_url.path) is not None
    )


def check_meetandplay_availability(
    booking_url: str,
    selected_date: date,
    selected_time: time,
    duration_minutes: int,
) -> dict[str, Any] | None:
    """Return a verified result, or None when the page needs browser fallback."""
    if not 15 <= duration_minutes <= 300:
        raise ValueError("Duration must be between 15 and 300 minutes.")
    if not is_meetandplay_booking_url(booking_url):
        return None

    parsed_url = urlparse(booking_url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)
        if key.casefold() != "date"
    ]
    query.append(("date", selected_date.isoformat()))
    requested_url = urlunparse(parsed_url._replace(query=urlencode(query)))

    response = requests.get(
        requested_url,
        headers={"Accept": "text/html"},
        timeout=(3, 6),
    )
    if response.status_code >= 400:
        if response.status_code == 429:
            return {
                "status": "Could not verify - Meet & Play rate limited",
                "reason": (
                    "Meet & Play temporarily rejected the availability request "
                    "with HTTP 429. Try again later."
                ),
            }
        return {
            "status": (
                "Could not verify - Meet & Play returned "
                f"HTTP {response.status_code}"
            ),
            "reason": (
                "Meet & Play did not return a readable calendar. "
                f"The booking page returned HTTP {response.status_code}."
            ),
        }

    response_url = urlparse(response.url)
    if (
        (response_url.hostname or "").casefold() != MEET_AND_PLAY_HOST
        or response_url.path.rstrip("/") != parsed_url.path.rstrip("/")
    ):
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    component = _court_show_component(soup)
    if component is None:
        return None

    data = component.get("data", {})
    memo = component.get("memo", {})
    if (
        not isinstance(data, dict)
        or not isinstance(memo, dict)
        or str(memo.get("path", "")).lstrip("/")
        != parsed_url.path.lstrip("/")
    ):
        return None
    if data.get("date") != selected_date.strftime("%d-%m-%Y"):
        return {
            "status": "Could not verify - requested date was not applied",
            "reason": (
                "Meet & Play did not render the date selected in the dashboard."
            ),
        }
    if not _is_tennis_selected(soup, data.get("tenantSportId")):
        return None

    court_sections = soup.select(".mp-court-type")
    if not court_sections:
        return None

    requested_start = selected_time.strftime("%H:%M")
    requested_end = (
        datetime.combine(selected_date, selected_time)
        + timedelta(minutes=duration_minutes)
    ).strftime("%H:%M")
    available_courts = []
    ambiguous_interval = False
    recognized_calendar = False

    for section in court_sections:
        court_container = section.find_next_sibling()
        if (
            not court_container
            or "timeslots" not in court_container.get("class", [])
        ):
            continue
        recognized_calendar = True
        section_label = section.get_text(" ", strip=True).casefold()
        if "buiten" in section_label:
            environment = "outdoor"
        elif "binnen" in section_label:
            environment = "indoor"
        elif "overkapt" in section_label:
            environment = "covered"
        else:
            environment = "unknown"

        for anchor in court_container.select(".timeslot-container a.timeslot"):
            click_action = str(anchor.get("wire:click", "")).casefold()
            slot_time = anchor.select_one(".timeslot-time")
            duration_text = (
                slot_time.get_text(" ", strip=True) if slot_time else ""
            )
            displayed_times = TIME_PATTERN.findall(duration_text)
            duration_match = re.search(
                r"(\d+)\s*(?:min(?:uten)?|minutes?)",
                duration_text,
                re.IGNORECASE,
            )
            if (
                displayed_times != [requested_start, requested_end]
                or duration_match is None
                or int(duration_match.group(1)) != duration_minutes
            ):
                continue
            class_names = {
                str(class_name).casefold()
                for class_name in anchor.get("class", [])
            }
            if (
                not click_action.startswith("selectslot(")
                or "toevoegen"
                not in anchor.get_text(" ", strip=True).casefold()
                or anchor.has_attr("disabled")
                or str(anchor.get("aria-disabled", "")).casefold() == "true"
                or "disabled" in class_names
                or anchor.has_attr("hidden")
                or str(anchor.get("aria-hidden", "")).casefold() == "true"
            ):
                ambiguous_interval = True
                continue

            name_element = anchor.select_one(".timeslot-name")
            name_text = name_element.get_text(" ", strip=True) if name_element else ""
            name_match = COURT_NAME_PATTERN.search(name_text)
            available_courts.append(
                {
                    "name": name_match.group(0) if name_match else "",
                    "environment": environment,
                }
            )

    if not recognized_calendar:
        return None

    if available_courts:
        return {
            "status": "Available - selectable on the booking page",
            "reason": (
                "Meet & Play lists a selectable court for the requested date, "
                f"start time, and {duration_minutes}-minute duration."
            ),
            "available_courts": available_courts,
        }

    if ambiguous_interval:
        return None

    normalized_text = " ".join(soup.get_text(" ", strip=True).casefold().split())
    if MEET_AND_PLAY_NO_SLOTS_TEXT in normalized_text:
        status = "Could not verify - no court slots are shown"
        reason = "Meet & Play showed no court slots for the selected date."
    else:
        status = "Could not verify - start time is not shown"
        reason = (
            "Meet & Play did not list a selectable court for the requested "
            "time and duration."
        )
    return {"status": status, "reason": reason}


def _court_show_component(soup: BeautifulSoup) -> dict[str, Any] | None:
    for element in soup.find_all(attrs={"wire:snapshot": True}):
        try:
            component = json.loads(element["wire:snapshot"])
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(component, dict):
            continue
        memo = component.get("memo")
        if (
            isinstance(memo, dict)
            and memo.get("name") == MEET_AND_PLAY_COMPONENT
        ):
            return component
    return None


def _is_tennis_selected(soup: BeautifulSoup, sport_id: Any) -> bool:
    sport_select = soup.find("select", id="sportId")
    if sport_select is None or sport_id is None:
        return False
    selected_option = next(
        (
            option
            for option in sport_select.find_all("option")
            if option.get("value") == str(sport_id)
        ),
        None,
    )
    return (
        selected_option is not None
        and selected_option.get_text(" ", strip=True).casefold() == "tennis"
    )
