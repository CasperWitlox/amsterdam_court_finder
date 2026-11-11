#!/usr/bin/env python3
"""Check public booking availability in a temporary, read-only browser session."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo


MONTH_NAMES = {
    1: ("januari", "january", "jan"),
    2: ("februari", "february", "feb"),
    3: ("maart", "march", "mrt", "mar"),
    4: ("april", "april", "apr"),
    5: ("mei", "may", "may"),
    6: ("juni", "june", "jun"),
    7: ("juli", "july", "jul"),
    8: ("augustus", "august", "aug"),
    9: ("september", "september", "sep"),
    10: ("oktober", "october", "okt", "oct"),
    11: ("november", "november", "nov"),
    12: ("december", "december", "dec"),
}
TIME_PATTERN = re.compile(r"(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)(?!\d)")
USC_ALLOWED_HOSTS = {
    "my.uscsport.nl",
    "backbone-web-api.production.uva.delcom.nl",
    "firebase.googleapis.com",
    "firebaseinstallations.googleapis.com",
    "identitytoolkit.googleapis.com",
    "securetoken.googleapis.com",
}
AVAILABLE_WORDS = (
    "book",
    "book now",
    "bookable",
    "booking",
    "reserve",
    "reservation",
    "reserver",
    "reserveren",
    "boek",
    "boeken",
    "toevoegen",
    "beschikbaar",
    "available",
    "vrij",
)
UNAVAILABLE_WORDS = (
    "unavailable",
    "not available",
    "not bookable",
    "cannot book",
    "can't book",
    "fully booked",
    "booked",
    "sold out",
    "niet beschikbaar",
    "niet boekbaar",
    "niet te boeken",
    "bezet",
    "blocked",
    "geblokkeerd",
    "gereserveerd",
    "onderhoud",
    "niet bespeelbaar",
    "baanonderhoud",
    "leden",
    "vol",
    "closed",
    "gesloten",
)


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char)).split()
    )


def date_tokens(selected_date: date) -> tuple[str, ...]:
    day = selected_date.day
    month = selected_date.month
    year = selected_date.year
    tokens = {
        f"{day:02d}-{month:02d}-{year}",
        f"{day:02d}/{month:02d}/{year}",
        f"{year}-{month:02d}-{day:02d}",
        f"{day:02d}.{month:02d}.{year}",
    }
    for month_name in MONTH_NAMES[month]:
        tokens.add(f"{day} {month_name} {year}")
        tokens.add(f"{day:02d} {month_name} {year}")
        tokens.add(f"{month_name} {day}, {year}")
    return tuple(sorted(tokens, key=len, reverse=True))


def matches_requested_date(page_text: str, selected_date: date) -> bool:
    normalized_text = normalize_text(page_text)
    return any(
        re.search(rf"(?<!\d){re.escape(normalize_text(token))}(?!\d)", normalized_text)
        for token in date_tokens(selected_date)
    )


def visible_numeric_dates(page_text: str) -> set[date]:
    dates = set()
    pattern = re.compile(
        r"(?<!\d)(?:(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})|"
        r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}))(?!\d)"
    )
    for match in pattern.finditer(page_text):
        year_first = match.group(1) is not None
        year, month, day = (
            (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if year_first
            else (int(match.group(6)), int(match.group(5)), int(match.group(4)))
        )
        try:
            dates.add(date(year, month, day))
        except ValueError:
            continue
    return dates


def slot_times(text: str) -> list[int]:
    return [
        int(hour) * 60 + int(minute)
        for hour, minute in TIME_PATTERN.findall(text)
    ]


def contains_term(text: str, terms: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text)
        for term in terms
    )


def inspect_slot(
    *,
    page_text: str,
    controls: list[dict[str, Any]],
    current_url: str,
    selected_date: date,
    start_time: str,
    duration_minutes: int,
    expected_hostname: str | None = None,
    require_visible_date: bool = False,
) -> dict[str, str]:
    """Report only a visible, exact-date, exact-duration interactive slot."""
    parsed_url = urlparse(current_url)
    host = (parsed_url.hostname or "").casefold()
    correct_host = (
        host == expected_hostname
        if expected_hostname is not None
        else host == "meetandplay.nl" or host.endswith(".meetandplay.nl")
    )
    if not correct_host:
        if expected_hostname is None:
            return {
                "status": "Could not verify - not on the Meet & Play booking page",
                "reason": "The requested club calendar is not on Meet & Play.",
            }
        return {
            "status": "Could not verify - not on the expected booking page",
            "reason": "The booking page host does not match the selected portal.",
        }

    page_shows_date = matches_requested_date(page_text, selected_date)
    if require_visible_date and not page_shows_date:
        return {
            "status": "Could not verify - selected date is not visible",
            "reason": "The booking page did not visibly confirm the selected date.",
        }
    if not page_shows_date:
        visible_dates = visible_numeric_dates(page_text)
        if visible_dates and selected_date not in visible_dates:
            return {
                "status": "Could not verify - displayed date does not match",
                "reason": (
                    "The booking page visibly shows a different date from the "
                    "date selected in the dashboard."
                ),
            }
    if not page_shows_date and not matches_requested_date(current_url, selected_date):
        return {
            "status": "Could not verify - selected date is not visible",
            "reason": "The requested date must be visible on the booking page.",
        }

    start_hour, start_minute = (int(part) for part in start_time.split(":"))
    requested_start = start_hour * 60 + start_minute
    requested_end = (requested_start + duration_minutes) % (24 * 60)
    for control in controls:
        if not control.get("visible", True):
            continue
        times = slot_times(
            " ".join(
                str(control.get(key, ""))
                for key in ("text", "aria_label", "title")
            )
        )
        has_exact_interval = any(
            first == requested_start and second == requested_end
            for first, second in zip(times, times[1:])
        )
        if not has_exact_interval:
            continue

        control_text = normalize_text(
            " ".join(
                str(control.get(key, ""))
                for key in ("text", "aria_label", "title")
            )
        )
        if contains_term(control_text, UNAVAILABLE_WORDS):
            return {
                "status": "Unavailable - slot marked as unavailable",
                "reason": "The exact time interval is shown as unavailable.",
            }
        if control.get("disabled") or control.get("aria_disabled"):
            return {
                "status": "Unavailable - slot is disabled",
                "reason": "The exact time interval is shown in a disabled control.",
            }
        if contains_term(control_text, AVAILABLE_WORDS) or "toevoegen" in control_text:
            return {
                "status": "Available - selectable on the booking page",
                "reason": "The exact date and interval are shown as selectable.",
            }
        return {
            "status": "Could not verify - slot control is ambiguous",
            "reason": "The page shows the exact interval but does not identify it as bookable.",
        }

    return {
        "status": "Could not verify - exact interval not shown",
        "reason": "No visible booking control matches both the requested start and end time.",
    }


def inspect_baanreserveren_slot(
    *,
    page_text: str,
    row_times: list[dict[str, Any]],
    slots: list[dict[str, Any]],
    selected_date: date,
    start_time: str,
    duration_minutes: int,
    court_environment: str,
) -> dict[str, Any]:
    if not matches_requested_date(page_text, selected_date):
        return {
            "status": "Could not verify - selected date is not visible",
            "reason": (
                "The signed-in booking calendar did not visibly confirm the "
                "date selected in the dashboard."
            ),
        }

    start_values = slot_times(start_time)
    if len(start_values) != 1:
        return {
            "status": "Could not verify - start time is invalid",
            "reason": "The requested start time could not be interpreted.",
        }
    start_hour, start_minute = (int(value) for value in start_time.split(":"))
    requested_start = datetime.combine(
        selected_date,
        time(start_hour, start_minute),
        tzinfo=ZoneInfo("Europe/Amsterdam"),
    ).timestamp()
    requested_end = requested_start + duration_minutes * 60
    calendar_rows: list[tuple[int, int]] = []
    for row in row_times:
        try:
            row_index = int(row["row_index"])
        except (KeyError, TypeError, ValueError):
            continue
        visible_times = slot_times(str(row.get("displayed_time", "")))
        if len(visible_times) == 1:
            row_hour, row_minute = divmod(visible_times[0], 60)
            timestamp = int(
                datetime.combine(
                    selected_date,
                    time(row_hour, row_minute),
                    tzinfo=ZoneInfo("Europe/Amsterdam"),
                ).timestamp()
            )
        else:
            try:
                timestamp = int(row["timestamp"])
            except (KeyError, TypeError, ValueError):
                continue
            if abs(timestamp) >= 1_000_000_000_000:
                timestamp //= 1000
        calendar_rows.append((row_index, timestamp))
    calendar_rows.sort()
    if len(calendar_rows) < 2:
        return {
            "status": "Could not verify - calendar time grid is missing",
            "reason": "The portal did not expose a readable time grid for its court slots.",
        }

    intervals = [
        next_timestamp - timestamp
        for (_row, timestamp), (_next_row, next_timestamp)
        in zip(calendar_rows, calendar_rows[1:])
        if next_timestamp > timestamp
    ]
    if not intervals:
        return {
            "status": "Could not verify - calendar time grid is ambiguous",
            "reason": "The portal's time grid did not expose consecutive court rows.",
        }
    interval_seconds = min(intervals)
    duration_seconds = duration_minutes * 60
    if interval_seconds <= 0 or duration_seconds % interval_seconds:
        return {
            "status": "Could not verify - duration does not match court slots",
            "reason": (
                "The requested duration cannot be mapped exactly to the "
                f"portal's {interval_seconds}-second court slots."
            ),
        }

    row_indexes_by_timestamp = {
        timestamp: row_index for row_index, timestamp in calendar_rows
    }
    target_start = int(requested_start)
    target_end = int(requested_end)
    target_timestamps = list(range(target_start, target_end, interval_seconds))
    if (
        not target_timestamps
        or target_timestamps[0] != target_start
        or target_timestamps[-1] + interval_seconds != target_end
        or any(
            timestamp not in row_indexes_by_timestamp
            for timestamp in target_timestamps
        )
    ):
        visible_start = datetime.fromtimestamp(
            calendar_rows[0][1],
            tz=ZoneInfo("Europe/Amsterdam"),
        ).strftime("%H:%M")
        visible_end = datetime.fromtimestamp(
            calendar_rows[-1][1],
            tz=ZoneInfo("Europe/Amsterdam"),
        ).strftime("%H:%M")
        slot_step = (
            f"{interval_seconds // 60} minutes"
            if interval_seconds % 60 == 0
            else f"{interval_seconds} seconds"
        )
        return {
            "status": "Could not verify - exact interval not shown",
            "reason": (
                "The portal's time grid does not contain every court row in "
                f"the requested interval. Grid rows: {len(calendar_rows)}, "
                f"slot step: {slot_step}, visible range: "
                f"{visible_start}-{visible_end}."
            ),
        }

    def slot_status(slot: dict[str, Any]) -> str:
        class_names = normalize_text(str(slot.get("class_names", "")))
        text = normalize_text(
            " ".join(
                str(slot.get(key, ""))
                for key in ("text", "title", "aria_label")
            )
        )
        combined = f"{class_names} {text}"
        background_color = str(slot.get("background_color", "")).casefold()
        color_match = re.fullmatch(
            r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)",
            background_color,
        )
        red_background = False
        light_background = False
        if color_match:
            red, green, blue = (int(value) for value in color_match.groups())
            red_background = red >= 180 and red > green * 1.35 and red > blue * 1.35
            light_background = min(red, green, blue) >= 225
        if (
            "taken" in class_names.split()
            or "closed" in class_names.split()
            or "reserved" in class_names.split()
            or "booked" in class_names.split()
            or red_background
            or slot.get("disabled")
            or slot.get("aria_disabled")
            or contains_term(combined, UNAVAILABLE_WORDS)
        ):
            return "unavailable"
        if "free" in class_names.split() or contains_term(
            text, AVAILABLE_WORDS
        ):
            return "available"
        if light_background or background_color in {"transparent", "rgba(0, 0, 0, 0)"}:
            return "available"
        return "unknown"

    court_rows: dict[str, dict[int, dict[str, Any]]] = {}
    ordered_row_indexes = [row_index for row_index, _minute in calendar_rows]
    row_positions = {
        row_index: position for position, row_index in enumerate(ordered_row_indexes)
    }
    for slot in slots:
        try:
            court = str(slot["court_index"])
            row_index = int(slot["row_index"])
            row_span = max(1, int(slot.get("row_span", 1)))
        except (KeyError, TypeError, ValueError):
            continue
        if row_index not in row_positions:
            continue
        status = slot_status(slot)
        first_position = row_positions[row_index]
        for position in range(first_position, min(first_position + row_span, len(ordered_row_indexes))):
            court_rows.setdefault(court, {})[ordered_row_indexes[position]] = {
                "status": status,
                "text": str(slot.get("text", "")),
            }

    if not court_rows:
        return {
            "status": "Could not verify - court slots are missing",
            "reason": "The portal did not expose any court slot cells in its calendar.",
        }

    court_states: dict[str, list[str]] = {}
    for court, rows in court_rows.items():
        states = []
        for timestamp in target_timestamps:
            row_index = row_indexes_by_timestamp[timestamp]
            states.append(rows.get(row_index, {}).get("status", "unknown"))
        court_states[court] = states

    available_courts = [
        court
        for court, states in court_states.items()
        if states and all(state == "available" for state in states)
    ]
    if available_courts:
        return {
            "status": "Available - selectable in the booking calendar",
            "reason": (
                "The requested interval is open for the full duration on "
                f"{len(available_courts)} court(s) in this category."
            ),
            "available_courts": [
                {"name": court, "environment": court_environment}
                for court in available_courts
            ],
        }

    unavailable_courts = [
        court
        for court, states in court_states.items()
        if "unavailable" in states
    ]
    if court_states and len(unavailable_courts) == len(court_states):
        return {
            "status": "Unavailable - slot marked as unavailable",
            "reason": (
                "Every court in this category has an occupied, closed, or "
                "members-only slot during the requested interval."
            ),
        }

    return {
        "status": "Could not verify - slot control is ambiguous",
        "reason": (
            "The portal grid did not clearly show every court slot in the "
            "requested interval as either bookable or occupied."
        ),
    }


def combine_baanreserveren_slot_results(
    results: list[tuple[str, dict[str, Any]]],
    required_categories: tuple[str, ...] = ("TENNIS BINNEN", "TENNIS BUITEN"),
) -> dict[str, Any]:
    available_categories = [
        category
        for category, result in results
        if result["status"].startswith("Available")
    ]
    if available_categories:
        return {
            "status": "Available - selectable in the booking calendar",
            "reason": (
                "The requested interval is available in "
                + ", ".join(available_categories)
                + "."
            ),
            "available_courts": [
                court
                for category, result in results
                if category in available_categories
                for court in result.get("available_courts", [])
            ],
        }

    checked_categories = {category for category, _result in results}
    missing_categories = [
        category for category in required_categories
        if category not in checked_categories
    ]
    if missing_categories:
        missing_text = ", ".join(missing_categories)
        details = "; ".join(
            f"{category}: {result['status']}"
            for category, result in results
        )
        return {
            "status": "Could not verify - tennis court category missing",
            "reason": (
                f"The portal did not offer {missing_text}, so availability "
                f"could not be confirmed across indoor and outdoor courts. {details}"
            ).strip(),
        }

    if results and all(
        result["status"].startswith("Unavailable")
        for _category, result in results
    ):
        return {
            "status": "Unavailable - slot marked as unavailable",
            "reason": (
                "The requested interval is unavailable in both TENNIS BINNEN "
                "and TENNIS BUITEN."
            ),
        }

    details = "; ".join(
        f"{category}: {result['status']} — {result['reason']}"
        for category, result in results
    )
    return {
        "status": "Could not verify - exact interval not shown",
        "reason": details or "No tennis calendar category could be checked.",
    }


def inspect_allbooked_calendar(
    *,
    calendar: dict[str, Any],
    selected_date: date,
    start_time: str,
    duration_minutes: int,
) -> dict[str, Any]:
    if not matches_requested_date(str(calendar.get("date_text", "")), selected_date):
        return {
            "status": "Could not verify - displayed date does not match",
            "reason": "The AllBooked calendar does not show the date selected in the dashboard.",
        }

    courts = calendar.get("courts", [])
    if not courts or any(not isinstance(court, str) or not court.strip() for court in courts):
        return {
            "status": "Could not verify - courts are not identified",
            "reason": "The public calendar did not expose its court columns clearly.",
        }

    labels = calendar.get("time_labels", [])
    axis_minutes = slot_times(" ".join(str(label) for label in labels))
    if len(axis_minutes) < 2:
        return {
            "status": "Could not verify - calendar hours are not visible",
            "reason": "The public calendar did not expose its operating hours.",
        }
    axis_minutes = sorted(set(axis_minutes))
    if any(
        next_minute - minute != 60
        for minute, next_minute in zip(axis_minutes, axis_minutes[1:])
    ):
        return {
            "status": "Could not verify - calendar hours are ambiguous",
            "reason": "The public calendar time axis is incomplete or irregular.",
        }

    requested_start = slot_times(start_time)
    if len(requested_start) != 1:
        return {
            "status": "Could not verify - start time is invalid",
            "reason": "The requested start time could not be interpreted.",
        }
    start_minute = requested_start[0]
    end_minute = start_minute + duration_minutes
    calendar_start = axis_minutes[0]
    calendar_end = axis_minutes[-1] + 60
    if start_minute < calendar_start or end_minute > calendar_end:
        return {
            "status": "Unavailable - outside published calendar hours",
            "reason": (
                "The requested interval is outside the hours shown in "
                "Blauw-Wit's public day calendar."
            ),
        }

    unavailable_courts: set[int] = set()
    for event in calendar.get("events", []):
        try:
            court_index = int(event["court_index"])
        except (KeyError, TypeError, ValueError):
            return {
                "status": "Could not verify - reservation details are ambiguous",
                "reason": "A visible calendar reservation could not be assigned to a court.",
            }
        event_times = slot_times(str(event.get("text", "")))
        if (
            court_index < 0
            or court_index >= len(courts)
            or len(event_times) != 2
            or event_times[1] <= event_times[0]
        ):
            return {
                "status": "Could not verify - reservation details are ambiguous",
                "reason": "A visible calendar reservation has an unclear court or time.",
            }
        if event_times[0] < end_minute and event_times[1] > start_minute:
            unavailable_courts.add(court_index)

    available_courts = [
        court for index, court in enumerate(courts)
        if index not in unavailable_courts
    ]
    if available_courts:
        court_list = ", ".join(available_courts)
        return {
            "status": "Available - selectable in the public calendar",
            "reason": (
                f"At least one court is unreserved for the full requested interval: "
                f"{court_list}."
            ),
            "available_courts": [
                {"name": court, "environment": "outdoor"}
                for court in available_courts
            ],
        }
    return {
        "status": "Unavailable - all courts are occupied",
        "reason": "Every court has a visible reservation overlapping the requested interval.",
    }


def read_visible_page(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const visible = (element) => {
            const style = window.getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return style.visibility !== "hidden" &&
              style.display !== "none" &&
              rect.width > 0 &&
              rect.height > 0;
          };
          const timePattern = /\\b(?:[01]?\\d|2[0-3]):[0-5]\\d\\b/g;
          const controls = Array.from(document.querySelectorAll(
            "button, a, [role='button'], [role='option']"
          )).filter(visible).map((element) => {
            let slot = element;
            let slotText = (slot.innerText || "").trim();
            for (let depth = 0; depth < 6 && slot.parentElement; depth += 1) {
              const timeMatches = slotText.match(timePattern) || [];
              if (timeMatches.length >= 2 || slotText.length > 500) break;
              slot = slot.parentElement;
              slotText = (slot.innerText || "").trim();
            }
            return {
              text: slotText || (element.innerText || "").trim(),
              aria_label: element.getAttribute("aria-label") || "",
              title: element.getAttribute("title") || "",
              disabled: Boolean(element.disabled),
              aria_disabled: element.getAttribute("aria-disabled") === "true"
            };
          });
          const visibleFieldValues = Array.from(document.querySelectorAll(
            "input, select, textarea"
          )).filter(visible).map((element) => {
            const label = element.getAttribute("aria-label") ||
              element.getAttribute("name") ||
              element.getAttribute("placeholder") ||
              "";
            const value = element.tagName === "SELECT"
              ? (element.selectedOptions[0] && element.selectedOptions[0].textContent) || element.value
              : element.value;
            return [label, value].filter(Boolean).join(": ");
          }).filter(Boolean);
          return {
            text: [
              (document.body && document.body.innerText) || "",
              ...visibleFieldValues
            ].join(" ")
              .replace(/\\s+/g, " ")
              .trim(),
            controls
          };
        }"""
    )


def url_for_date(url: str, selected_date: date) -> str:
    parsed = urlparse(validate_http_url(url))
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["date"] = selected_date.isoformat()
    return urlunparse(parsed._replace(query=urlencode(query)))


def allbooked_url_for_date(url: Any, selected_date: date) -> str:
    if not isinstance(url, str):
        raise ValueError("Booking page URL must be a string.")
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "blauwwit.allbooked.com"
        or parsed.path.rstrip("/") != "/booking"
    ):
        raise ValueError("This availability checker only opens Blauw-Wit's public AllBooked calendar.")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["viewdate"] = selected_date.isoformat()
    return urlunparse(parsed._replace(query=urlencode(query)))


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def log_worker_diagnostic(message: str) -> None:
    sys.stderr.write(f"[booking-check] {message}\n")
    sys.stderr.flush()


def log_worker_result(result: dict[str, Any]) -> None:
    sys.stderr.write(
        "[booking-result] "
        + json.dumps({"ok": True, **result}, ensure_ascii=False)
        + "\n"
    )
    sys.stderr.flush()


def save_worker_result(command: dict[str, Any], result: dict[str, Any]) -> None:
    result_path = command.get("_result_path")
    if not isinstance(result_path, str) or not result_path:
        return
    path = Path(result_path)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps({"ok": True, **result}, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def sanitized_worker_error(error: Exception, command: dict[str, Any]) -> str:
    message = str(error)
    for field in ("username", "email", "password"):
        secret = command.get(field)
        if isinstance(secret, str) and secret:
            message = message.replace(secret, "[redacted]")
    return f"{type(error).__name__}: {message}"


def validate_http_url(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Booking page URL must be a string.")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Booking page must use HTTPS.")
    host = parsed.hostname.casefold()
    if host != "meetandplay.nl" and not host.endswith(".meetandplay.nl"):
        raise ValueError("This availability checker only opens Meet & Play pages.")
    if not parsed.path.startswith("/club/"):
        raise ValueError("This availability checker only opens Meet & Play club calendars.")
    return value


def validate_baanreserveren_url(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Booking page URL must be a string.")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {
            "amstelpark.baanreserveren.nl",
            "fransotten.baanreserveren.nl",
        }
    ):
        raise ValueError("This checker only opens the Amstelpark and Frans Otten portals.")
    return value


def validate_usc_url(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Booking page URL must be a string.")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "my.uscsport.nl"
        or parsed.path.rstrip("/") != "/bookings/rent"
    ):
        raise ValueError("This checker only opens USC's tennis rental page.")
    return value


def validate_bookaball_url(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Booking page URL must be a string.")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "rscbuitenveldert.bookaball.com"
        or parsed.path.rstrip("/") != "/nl/bookings/create"
    ):
        raise ValueError("This checker only opens Amsterdam Racket Club's Bookaball page.")
    return value


def bookaball_calendar_month(label: str) -> tuple[int, int] | None:
    match = re.search(r"([a-z]+),?\s+(\d{4})", normalize_text(label))
    if not match:
        return None
    month_label, year_text = match.groups()
    month_number = next(
        (
            month
            for month, names in MONTH_NAMES.items()
            if month_label in {normalize_text(name) for name in names}
        ),
        None,
    )
    if month_number is None:
        return None
    return int(year_text), month_number


def select_bookaball_date(page: Any, selected_date: date) -> str | None:
    month_label = page.locator(
        "#bookings-date-step-calendar-navigation-months"
    )
    target_month = (selected_date.year, selected_date.month)
    target_day_id = f"bookings-date-step-calendar-day-{selected_date.isoformat()}"
    for _ in range(24):
        current_month = bookaball_calendar_month(month_label.inner_text())
        if current_month is None:
            return "Bookaball did not identify the month shown in its calendar."
        if current_month == target_month:
            target_day = page.locator(f'[id="{target_day_id}"]')
            if target_day.count() != 1:
                return "Bookaball did not show the requested date in its calendar."
            day_class = target_day.get_attribute("class") or ""
            if "cursor-not-allowed" in day_class:
                return "The requested date is not selectable in Bookaball."
            if "cursor-pointer" not in day_class:
                return "Bookaball did not confirm that the requested date is selectable."
            target_day.click()
            page.wait_for_function(
                """dayId => {
                  const day = document.getElementById(dayId);
                  return day && day.className.includes("bg-secondary-brand-color");
                }""",
                arg=target_day_id,
                timeout=10_000,
            )
            page.wait_for_timeout(500)
            return None

        arrow_id = (
            "bookings-date-step-calendar-arrow-forward"
            if current_month < target_month
            else "bookings-date-step-calendar-arrow-back"
        )
        arrow = page.locator(f"#{arrow_id}")
        if arrow.count() != 1:
            return "Bookaball did not provide calendar navigation for the requested date."
        previous_label = month_label.inner_text()
        arrow.click()
        page.wait_for_function(
            """previous => {
              const label = document.querySelector(
                "#bookings-date-step-calendar-navigation-months"
              );
              return label && label.textContent.trim() !== previous;
            }""",
            arg=previous_label,
            timeout=10_000,
        )
    return "The requested date is beyond the range shown in Bookaball's calendar."


def select_bookaball_court_type(page: Any, court_type: str) -> None:
    selector = page.locator(
        "#bookings-size-step-select-courtType-listbox-button"
    )
    selector.click()
    option = page.get_by_role("option", name=court_type, exact=True)
    option.wait_for(state="visible", timeout=10_000)
    option.click()
    page.wait_for_function(
        """courtType => {
          const selector = document.querySelector(
            "#bookings-size-step-select-courtType-listbox-button"
          );
          return selector && selector.innerText.trim() === courtType;
        }""",
        arg=court_type,
        timeout=10_000,
    )
    page.wait_for_timeout(700)


def check_bookaball_slot(browser: Any, command: dict[str, Any]) -> dict[str, Any]:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    booking_url = validate_bookaball_url(command.get("url"))
    selected_date = date.fromisoformat(command["date"])
    start_time = str(command["start_time"])
    duration_minutes = int(command["duration_minutes"])
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time):
        raise ValueError("Start time must use HH:MM in 24-hour format.")
    if duration_minutes not in {60, 90}:
        return {
            "status": "Could not verify - duration is not supported",
            "reason": "Bookaball only offers 60- or 90-minute court bookings.",
        }

    parsed_url = urlparse(booking_url)
    context = browser.new_context(
        locale="nl-NL",
        timezone_id="Europe/Amsterdam",
    )
    context.route(
        "**/*",
        lambda route: (
            route.continue_()
            if urlparse(route.request.url).hostname == parsed_url.hostname
            else route.abort()
        ),
    )
    api_responses: list[str] = []

    def record_api_response(response: Any) -> None:
        response_url = urlparse(response.url)
        if (
            response_url.hostname == parsed_url.hostname
            and response_url.path
            in {
                "/api/locations",
                "/api/bookings/create/STEP_LOCATION",
            }
        ):
            api_responses.append(
                f"{response_url.path} returned HTTP {response.status}"
            )

    try:
        page = context.new_page()
        page.on("response", record_api_response)
        page.set_default_timeout(12_000)
        page.set_default_navigation_timeout(45_000)
        page.goto(booking_url, wait_until="domcontentloaded", timeout=45_000)
        dismiss_bookaball_preferences(page)
        club_card = page.get_by_text("Amsterdam Racket Club", exact=True).first
        try:
            club_card.wait_for(state="visible", timeout=25_000)
        except PlaywrightTimeoutError:
            api_summary = (
                "; ".join(api_responses[-4:])
                if api_responses
                else "No response observed from Bookaball's club-selection APIs."
            )
            page_title = page.title()
            page_path = urlparse(page.url).path
            page_text = normalize_text(page.locator("body").inner_text()).casefold()
            if any(
                marker in page_text
                for marker in (
                    "cloudflare",
                    "verify you are human",
                    "checking your browser",
                    "captcha",
                )
            ):
                page_state = "The page appears to show a browser-verification challenge."
            elif any(marker in page_text for marker in ("inloggen", "sign in", "log in")):
                page_state = "The page appears to require sign-in."
            else:
                page_state = (
                    f"Page title: {page_title or 'unknown'}; path: "
                    f"{page_path or '/'}."
                )
            return {
                "status": "Could not verify - Bookaball club list did not load",
                "reason": (
                    "The Amsterdam Racket Club card did not appear within 25 seconds. "
                    f"{page_state} {api_summary}"
                ),
            }
        club_card.click()
        page.locator("#bookings-date-step-calendar-navigation-months").wait_for(
            state="visible",
            timeout=25_000,
        )

        available_types: list[str] = []
        unavailable_types: list[str] = []
        ambiguous_types: list[str] = []
        for court_type in ("Indoor", "Outdoor"):
            select_bookaball_court_type(page, court_type)
            date_error = select_bookaball_date(page, selected_date)
            if date_error:
                return {
                    "status": "Could not verify - requested date is not selectable",
                    "reason": date_error,
                }

            duration_id = f"bookings-date-step-duration-{duration_minutes}"
            duration = page.locator(f'[id="{duration_id}"]')
            if duration.count() != 1:
                return {
                    "status": "Could not verify - duration is not supported",
                    "reason": (
                        f"Bookaball did not offer a {duration_minutes}-minute booking."
                    ),
                }
            duration_class = duration.get_attribute("class") or ""
            if "border-secondary-brand-color" not in duration_class:
                duration.click()
                page.wait_for_function(
                    """durationId => {
                      const duration = document.getElementById(durationId);
                      return duration &&
                        duration.className.includes("border-secondary-brand-color");
                    }""",
                    arg=duration_id,
                    timeout=10_000,
                )
            page.locator('[data-e2e="booking-times"]').wait_for(
                state="visible",
                timeout=15_000,
            )
            page.wait_for_timeout(500)

            slot_id = f"bookings-date-step-time-{start_time}"
            slot = page.locator(f'[id="{slot_id}"]')
            if slot.count() == 0:
                ambiguous_types.append(court_type)
                continue
            slot_class = slot.get_attribute("class") or ""
            waitlist = (
                "border-dashed" in slot_class
                or page.locator(f'[id="{slot_id}-spare"]').count() > 0
            )
            if waitlist:
                unavailable_types.append(court_type)
            elif "cursor-pointer" in slot_class:
                available_types.append(court_type.casefold())
            else:
                ambiguous_types.append(court_type)

        if available_types:
            return {
                "status": "Available - selectable in the booking calendar",
                "reason": (
                    "Bookaball lists the requested time as available for "
                    + " and ".join(court_type.lower() for court_type in available_types)
                    + " courts."
                ),
                "available_court_types": available_types,
            }
        if ambiguous_types:
            return {
                "status": "Could not verify - requested time is not shown",
                "reason": (
                    "Bookaball did not show a slot control for "
                    + " and ".join(court_type.lower() for court_type in ambiguous_types)
                    + " courts, so the booking horizon cannot be distinguished "
                    "from a time with no bookable court."
                ),
            }
        unavailable_summary = " and ".join(
            court_type.lower() for court_type in unavailable_types
        )
        return {
            "status": "Unavailable - no court available for selected interval",
            "reason": (
                "Bookaball did not list a bookable court for the requested "
                f"date, time and duration for {unavailable_summary} courts. "
                "Wait-list times are treated as unavailable."
            ),
        }
    finally:
        context.close()


def usc_url_for_date(url: str, selected_date: date) -> str:
    parsed = urlparse(validate_usc_url(url))
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["date"] = selected_date.isoformat()
    return urlunparse(parsed._replace(query=urlencode(query)))


def usc_day_tab_date(
    text: str,
    aria_label: str,
    today: date,
) -> date | None:
    if normalize_text(text).strip() == "vandaag":
        return today

    match = re.search(r"(?<!\d)(\d{1,2})\s+([a-z]+)", normalize_text(aria_label))
    if match:
        day = int(match.group(1))
        month_text = match.group(2)
        month = next(
            (
                number
                for number, names in MONTH_NAMES.items()
                if any(normalize_text(name) == month_text for name in names)
            ),
            None,
        )
    else:
        match = re.search(r"(?<!\d)(\d{1,2})-(\d{1,2})(?!\d)", text)
        if not match:
            return None
        day, month = int(match.group(1)), int(match.group(2))

    if month is None:
        return None
    candidates = []
    for year in (today.year, today.year + 1):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if candidate >= today:
            candidates.append(candidate)
    return min(candidates) if candidates else None


def usc_day_tab_index(
    tabs: list[tuple[str, str]],
    selected_date: date,
    today: date,
) -> int | None:
    if selected_date == today:
        return next(
            (
                index
                for index, (text, _aria_label) in enumerate(tabs)
                if normalize_text(text).strip() == "vandaag"
            ),
            None,
        )
    return next(
        (
            index
            for index, (text, aria_label) in enumerate(tabs)
            if usc_day_tab_date(text, aria_label, today) == selected_date
        ),
        None,
    )


def inspect_usc_available_slots(
    slots: list[dict[str, Any]],
    start_time: str,
    duration_minutes: int,
) -> dict[str, Any]:
    requested_start = slot_times(start_time)
    if len(requested_start) != 1:
        return {
            "status": "Could not verify - start time is invalid",
            "reason": "The requested start time could not be interpreted.",
        }
    for slot in slots:
        slot_start = slot_times(slot.get("start_time", ""))
        duration_match = re.search(
            r"(\d+)\s*min",
            slot.get("duration", ""),
            re.I,
        )
        if (
            slot_start
            and slot_start[0] == requested_start[0]
            and duration_match
            and int(duration_match.group(1)) == duration_minutes
        ):
            return {
                "status": "Available - selectable on the booking page",
                "reason": (
                    "USC displayed a selectable court slot for the requested "
                    f"date, start time, and {duration_minutes}-minute duration."
                ),
            }
    return {
        "status": "Unavailable - no court slot shown",
        "reason": (
            "USC displays only available court slots. The requested "
            "date, start time, and duration were not among its selectable slots."
        ),
    }


def inspect_meetandplay_available_courts(
    calendar: dict[str, Any],
    start_time: str,
    duration_minutes: int,
) -> list[dict[str, str]]:
    requested_start = slot_times(start_time)
    if len(requested_start) != 1:
        return []
    available_courts = []
    for section in calendar.get("sections", []):
        label = normalize_text(str(section.get("label", "")))
        if "buiten" in label:
            environment = "outdoor"
        elif "binnen" in label:
            environment = "indoor"
        elif "overkapt" in label:
            environment = "covered"
        else:
            environment = "unknown"
        for court in section.get("courts", []):
            times = slot_times(str(court.get("text", "")))
            duration_match = re.search(
                r"(\d+)\s*(?:min(?:uten)?|minutes?)",
                str(court.get("text", "")),
                re.I,
            )
            if (
                len(times) != 2
                or times[0] != requested_start[0]
                or times[1] - times[0] != duration_minutes
                or not duration_match
                or int(duration_match.group(1)) != duration_minutes
            ):
                continue
            available_courts.append(
                {
                    "name": str(court.get("name", "")).strip(),
                    "environment": environment,
                }
            )
    return available_courts


def inspect_usc_available_courts(labels: list[str]) -> list[dict[str, str]]:
    courts = []
    for value in labels:
        normalized = normalize_text(value)
        if re.search(r"\btennis\s*\|\s*niet overdekt\b", normalized):
            courts.append({"name": "", "environment": "outdoor"})
        elif re.search(r"\btennis\s*\|\s*overdekt\b", normalized):
            courts.append({"name": "", "environment": "indoor"})
    return courts


def reject_optional_cookies(page: Any) -> None:
    reject_button = page.locator("#CybotCookiebotDialogBodyButtonDecline")
    if reject_button.count() and reject_button.first.is_visible():
        reject_button.first.click(timeout=5_000)
        page.wait_for_timeout(300)
        return

    reject_button = page.get_by_role("button", name=re.compile(r"^Weigeren$", re.I))
    if reject_button.count() and reject_button.first.is_visible():
        reject_button.first.click(timeout=5_000)
        page.wait_for_timeout(300)


def dismiss_bookaball_preferences(page: Any) -> None:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    skip_button = page.locator('[data-e2e="user-preferences-popup-skip"]')
    try:
        skip_button.wait_for(state="visible", timeout=5_000)
    except PlaywrightTimeoutError:
        return
    skip_button.click(timeout=5_000)
    skip_button.wait_for(state="hidden", timeout=5_000)


def check_usc_slot(browser: Any, command: dict[str, Any]) -> dict[str, Any]:
    booking_url = validate_usc_url(command.get("url"))
    selected_date = date.fromisoformat(command["date"])
    start_time = str(command["start_time"])
    duration_minutes = int(command["duration_minutes"])
    email = command.get("email")
    password = command.get("password")
    if not isinstance(email, str) or not email.strip():
        raise ValueError("A USC email address is required.")
    if not isinstance(password, str) or not password:
        raise ValueError("A USC password is required.")
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time):
        raise ValueError("Start time must use HH:MM in 24-hour format.")
    if duration_minutes < 15 or duration_minutes > 300:
        raise ValueError("Duration must be between 15 and 300 minutes.")

    log_worker_diagnostic("Opening the USC booking page.")
    context = browser.new_context(
        locale="nl-NL",
        timezone_id="Europe/Amsterdam",
    )
    try:
        page = context.new_page()
        page.set_default_timeout(12_000)
        page.set_default_navigation_timeout(30_000)
        page.on(
            "crash",
            lambda: log_worker_diagnostic("USC booking page crashed."),
        )
        page.route(
            "**/*",
            lambda route: (
                route.continue_()
                if urlparse(route.request.url).hostname in USC_ALLOWED_HOSTS
                else route.abort()
            ),
        )
        page.goto(booking_url, wait_until="domcontentloaded", timeout=30_000)
        reject_optional_cookies(page)

        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        try:
            page.wait_for_function(
                """() => {
                  const visible = element => {
                    if (!element) return false;
                    const style = getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return style.visibility !== "hidden" &&
                      style.display !== "none" &&
                      rect.width > 0 &&
                      rect.height > 0;
                  };
                  return visible(document.querySelector("#password")) ||
                    Array.from(document.querySelectorAll("button")).some(button =>
                      visible(button) &&
                      /e-mail en wachtwoord/i.test(button.innerText || "")
                    );
                }""",
                timeout=15_000,
            )
        except PlaywrightTimeoutError:
            return {
                "status": "Could not verify - USC login page did not finish loading",
                "reason": (
                    "USC did not render its email-and-password sign-in controls "
                    "within 15 seconds."
                ),
            }

        password_input = page.locator("#password")
        if not (password_input.count() and password_input.first.is_visible()):
            login_choice = page.get_by_role(
                "button",
                name=re.compile(r"e-mail en wachtwoord", re.I),
            )
            if not (login_choice.count() and login_choice.first.is_visible()):
                return {
                    "status": "Could not verify - USC login option is missing",
                    "reason": "USC did not show the email-and-password sign-in option.",
                }
            login_choice.first.click(timeout=10_000)

        email_input = page.locator("#email")
        password_input = page.locator("#password")
        email_input.wait_for(state="visible", timeout=10_000)
        password_input.wait_for(state="visible", timeout=10_000)
        email_input.fill(email.strip(), timeout=10_000)
        password_input.fill(password, timeout=10_000)
        login_button = page.get_by_role(
            "button",
            name=re.compile(r"e-mail en wachtwoord", re.I),
        ).last
        log_worker_diagnostic("Submitting sign-in to USC.")
        login_button.click(timeout=10_000, no_wait_after=True)
        log_worker_diagnostic("USC accepted the sign-in form submission.")
        try:
            page.wait_for_url(
                lambda url: urlparse(str(url)).path.rstrip("/") != "/pages/login",
                timeout=15_000,
            )
        except PlaywrightTimeoutError:
            return {
                "status": "Could not verify - USC login did not complete",
                "reason": (
                    "USC kept the browser on its login page after the form was "
                    "submitted. Check the USC email and password, and try again."
                ),
            }

        log_worker_diagnostic("USC sign-in completed; opening the tennis calendar.")
        page.goto(
            usc_url_for_date(booking_url, selected_date),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(1_000)
        reject_optional_cookies(page)
        if (
            urlparse(page.url).hostname != "my.uscsport.nl"
            or urlparse(page.url).path.rstrip("/") == "/pages/login"
            or (password_input.count() and password_input.first.is_visible())
        ):
            return {
                "status": "Could not verify - USC login failed",
                "reason": (
                    "USC did not open the rental calendar after sign-in. "
                    "Check the email, password, and booking-account access."
                ),
            }

        today = datetime.now(ZoneInfo("Europe/Amsterdam")).date()
        day_tabs = page.locator('[role="tablist"] [role="tab"]')
        day_tabs.first.wait_for(state="visible", timeout=15_000)
        tab_labels = []
        for tab in day_tabs.all():
            tab_labels.append(
                (
                    tab.inner_text(),
                    tab.locator("[aria-label]").first.get_attribute("aria-label")
                    if tab.locator("[aria-label]").count()
                    else "",
                )
            )

        target_tab = usc_day_tab_index(tab_labels, selected_date, today)
        if target_tab is None:
            return {
                "status": "Could not verify - requested date is not offered",
                "reason": (
                    "USC's booking page does not currently show a day tab for "
                    f"{selected_date.isoformat()}."
                ),
            }

        selected_tab = day_tabs.nth(target_tab)
        if selected_tab.get_attribute("aria-selected") != "true":
            selected_tab.click(timeout=10_000)
            page.wait_for_function(
                """index => {
                  const tab = document.querySelector(
                    `[role="tablist"] [role="tab"][data-test-id="day-selector-${index}"]`
                  );
                  return tab && tab.getAttribute("aria-selected") === "true";
                }""",
                arg=target_tab,
                timeout=10_000,
            )
        page.wait_for_timeout(700)

        calendar = page.evaluate(
            """() => {
              const visible = element => {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return style.visibility !== "hidden" &&
                  style.display !== "none" &&
                  rect.width > 0 &&
                  rect.height > 0;
              };
              const tab = document.querySelector(
                '[role="tablist"] [role="tab"][aria-selected="true"]'
              );
              const slots = Array.from(document.querySelectorAll(
                '[data-test-id="selectable-slot-start-time"]'
              )).filter(visible).map(element => {
                const card = element.closest("button") || element.parentElement;
                const duration = card && card.querySelector(
                  '[data-test-id="selectable-slot-duration"]'
                );
                return {
                  start_time: (element.innerText || "").trim(),
                  duration: duration ? (duration.innerText || "").trim() : "",
                  text: card ? (card.innerText || "").trim() : ""
                };
              });
              return {
                selected_tab: tab ? (tab.innerText || "").trim() : "",
                selected_tab_date: tab
                  ? ((tab.querySelector("[aria-label]") &&
                      tab.querySelector("[aria-label]").getAttribute("aria-label")) || "")
                  : "",
                category_visible: (document.querySelector("main")?.innerText || "")
                  .includes("Tennis - losse baanhuur"),
                slots
              };
            }"""
        )
        actual_date = usc_day_tab_date(
            calendar["selected_tab"],
            calendar["selected_tab_date"],
            today,
        )
        if actual_date != selected_date or not calendar["category_visible"]:
            return {
                "status": "Could not verify - requested date was not applied",
                "reason": (
                    "USC did not confirm the requested day and tennis rental "
                    "category in its booking calendar."
                ),
            }

        result = inspect_usc_available_slots(
            calendar["slots"],
            start_time,
            duration_minutes,
        )
        if result["status"].startswith("Available"):
            matching_slot_index = next(
                (
                    index
                    for index, slot in enumerate(calendar["slots"])
                    if slot["start_time"] == start_time
                    and re.search(
                        rf"\b{duration_minutes}\s*min",
                        slot["duration"],
                        re.I,
                    )
                ),
                None,
            )
            if matching_slot_index is not None:
                matching_slot = page.locator(
                    '[data-test-id="selectable-slot-start-time"]:visible'
                ).nth(matching_slot_index)
                matching_slot.locator("xpath=ancestor::button[1]").click(
                    timeout=10_000,
                    no_wait_after=True,
                )
                page.wait_for_timeout(500)
                court_labels = page.evaluate(
                    """() => {
                      const visible = element => {
                        const style = window.getComputedStyle(element);
                        const rect = element.getBoundingClientRect();
                        return style.visibility !== "hidden" &&
                          style.display !== "none" &&
                          rect.width > 0 &&
                          rect.height > 0;
                      };
                      return Array.from(document.querySelectorAll("body *"))
                        .filter(element => visible(element) &&
                          element.children.length === 0)
                        .map(element => (element.innerText || "").trim())
                        .filter(text => /^Tennis\\s*\\|\\s*(?:niet overdekt|overdekt)$/i
                          .test(text));
                    }"""
                )
                result["available_courts"] = inspect_usc_available_courts(
                    court_labels
                )
        return result
    finally:
        context.close()


def wait_for_livewire_update(page: Any, action: Any) -> None:
    with page.expect_response(
        lambda response: "/livewire/update" in response.url,
        timeout=15_000,
    ) as response_info:
        action()
    response = response_info.value
    if not response.ok:
        raise RuntimeError(
            f"Meet & Play did not apply the requested filter (HTTP {response.status})."
        )


def check_baanreserveren_slot(browser: Any, command: dict[str, Any]) -> dict[str, str]:
    booking_url = validate_baanreserveren_url(command.get("url"))
    parsed_url = urlparse(booking_url)
    origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
    selected_date = date.fromisoformat(command["date"])
    start_time = str(command["start_time"])
    duration_minutes = int(command["duration_minutes"])
    username = command.get("username")
    password = command.get("password")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("A username is required for this booking portal.")
    if not isinstance(password, str) or not password:
        raise ValueError("A password is required for this booking portal.")
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time):
        raise ValueError("Start time must use HH:MM in 24-hour format.")
    if duration_minutes < 15 or duration_minutes > 300:
        raise ValueError("Duration must be between 15 and 300 minutes.")

    log_worker_diagnostic(f"Opening sign-in page for {parsed_url.hostname}.")
    context = browser.new_context(
        locale="nl-NL",
        timezone_id="Europe/Amsterdam",
    )
    try:
        page = context.new_page()
        page.set_default_timeout(12_000)
        page.set_default_navigation_timeout(30_000)
        page.route(
            "**/*",
            lambda route: (
                route.continue_()
                if urlparse(route.request.url).hostname == parsed_url.hostname
                else route.abort()
            ),
        )
        page.goto(booking_url, wait_until="domcontentloaded", timeout=30_000)
        username_input = page.locator('input[name="username"]')
        password_input = page.locator('input[name="password"]')
        if password_input.count() and password_input.first.is_visible():
            username_input.fill(username.strip(), timeout=10_000)
            password_input.fill(password, timeout=10_000)
            log_worker_diagnostic(f"Submitting sign-in for {parsed_url.hostname}.")
            page.locator('form[action$="/auth/login"] button').click(timeout=10_000)
            page.wait_for_load_state("domcontentloaded", timeout=12_000)
            page.wait_for_timeout(500)

        log_worker_diagnostic(f"Opening reservations calendar for {parsed_url.hostname}.")
        page.goto(
            f"{origin}/reservations/{selected_date.isoformat()}/sport/971",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(500)
        log_worker_diagnostic(f"Reservations calendar loaded for {parsed_url.hostname}.")
        password_input = page.locator('input[name="password"]')
        if password_input.count() and password_input.first.is_visible():
            return {
                "status": "Could not verify - login failed",
                "reason": (
                    "The portal did not open its reservations page after sign-in. "
                    "Check the username and password."
                ),
            }

        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        try:
            page.wait_for_function(
                """() => Array.from(document.querySelectorAll("select option"))
                  .some(option => /^(tennis binnen|tennis buiten)(\\s|$)/i
                    .test((option.textContent || "").replace(/\\s+/g, " ").trim()))""",
                timeout=8_000,
            )
        except PlaywrightTimeoutError:
            available_options = page.locator("select").evaluate_all(
                """selects => selects.map(select => Array.from(select.options)
                  .map(option => (option.textContent || "").replace(/\\s+/g, " ").trim())
                  .filter(Boolean))"""
            )
            return {
                "status": "Could not verify - tennis filter is missing",
                "reason": (
                    "The signed-in portal did not load TENNIS BINNEN or TENNIS "
                    f"BUITEN. Visible filter options: {available_options or 'none'}."
                ),
            }

        filters: dict[str, tuple[Any, str]] = {}
        for select_index, select in enumerate(page.locator("select").all()):
            for option in select.locator("option").all():
                label = " ".join(option.inner_text().split())
                normalized_label = normalize_text(label).upper()
                category = next(
                    (
                        expected
                        for expected in ("TENNIS BINNEN", "TENNIS BUITEN")
                        if normalized_label == expected
                        or normalized_label.startswith(expected + " ")
                    ),
                    None,
                )
                if category is not None:
                    filters[category] = (
                        page.locator("select").nth(select_index),
                        option.get_attribute("value") or label,
                    )

        log_worker_diagnostic(
            f"Loaded tennis categories for {parsed_url.hostname}: "
            f"{', '.join(filters) if filters else 'none'}."
        )
        category_results: list[tuple[str, dict[str, Any]]] = []
        for category, (select, option_value) in filters.items():
            log_worker_diagnostic(f"Checking {category} for {parsed_url.hostname}.")
            if select.input_value() != option_value:
                select.select_option(option_value)
            page.wait_for_function(
                """category => {
                  const slot = document.querySelector("td.slot[slot]");
                  const table = slot && slot.closest("table");
                  return table && (table.innerText || "")
                    .toLocaleUpperCase().includes(category);
                }""",
                arg=category,
                timeout=10_000,
            )
            selected_category = " ".join(
                select.locator("option:checked").inner_text().split()
            )
            if normalize_text(selected_category).upper() != category:
                category_results.append(
                    (
                        category,
                        {
                            "status": "Could not verify - tennis filter was not applied",
                            "reason": f"The portal did not confirm the {category} filter.",
                        },
                    )
                )
                continue

            calendar = page.evaluate(
                """() => {
                  const visible = (element) => {
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return style.visibility !== "hidden" &&
                      style.display !== "none" &&
                      rect.width > 0 &&
                      rect.height > 0;
                  };
                  const slotElements = Array.from(document.querySelectorAll(
                    "td.slot[slot]"
                  )).filter(visible);
                  const matrix = slotElements[0] &&
                    slotElements[0].closest("table");
                  if (!matrix) {
                    return {
                      text: (document.body && document.body.innerText) || "",
                      row_times: [],
                      slots: []
                    };
                  }
                  const rows = Array.from(matrix.querySelectorAll("tr[utc]"))
                    .filter(visible);
                  const row_times = rows.map((row) => {
                    const rawUtc = Number(row.getAttribute("utc"));
                    const timestamp = Math.abs(rawUtc) >= 1000000000000
                      ? Math.trunc(rawUtc / 1000)
                      : Math.trunc(rawUtc);
                    const firstSlot = row.querySelector("td.slot[slot]");
                    return {
                      row_index: row.rowIndex,
                      timestamp,
                      displayed_time: firstSlot
                        ? (firstSlot.innerText || "").trim()
                        : ""
                    };
                  }).filter(row => Number.isFinite(row.row_index) &&
                    Number.isFinite(row.timestamp));
                  const slots = slotElements
                    .filter(element => element.closest("table") === matrix)
                    .map((element) => {
                      const row = element.closest("tr[utc]");
                      const rawUtc = row && Number(row.getAttribute("utc"));
                      const timestamp = Number.isFinite(rawUtc)
                        ? (Math.abs(rawUtc) >= 1000000000000
                          ? Math.trunc(rawUtc / 1000)
                          : Math.trunc(rawUtc))
                        : null;
                      return {
                        court_index: element.getAttribute("slot"),
                        row_index: row ? row.rowIndex : -1,
                        row_span: element.rowSpan || 1,
                        class_names: Array.from(element.classList).join(" "),
                        text: (element.innerText || "").trim(),
                        title: element.getAttribute("title") || "",
                        aria_label: element.getAttribute("aria-label") || "",
                        disabled: Boolean(element.disabled),
                        aria_disabled: element.getAttribute("aria-disabled") === "true",
                        background_color: window.getComputedStyle(element).backgroundColor,
                        timestamp: Number.isFinite(timestamp) ? timestamp : null
                      };
                    });
                  return {
                    text: (document.body && document.body.innerText) || "",
                    row_times,
                    slots
                  };
                }"""
            )
            category_results.append(
                (
                    category,
                    inspect_baanreserveren_slot(
                        page_text=calendar["text"],
                        row_times=calendar["row_times"],
                        slots=calendar["slots"],
                        selected_date=selected_date,
                        start_time=start_time,
                        duration_minutes=duration_minutes,
                        court_environment=(
                            "indoor" if category == "TENNIS BINNEN" else "outdoor"
                        ),
                    ),
                )
            )
        result = combine_baanreserveren_slot_results(category_results)
        log_worker_diagnostic(
            f"Completed calendar check for {parsed_url.hostname}: {result['status']}."
        )
        return result
    finally:
        log_worker_diagnostic(
            f"Finished reading the calendar for {parsed_url.hostname}; "
            "the worker will release its temporary browser context on shutdown."
        )


def check_public_slot(browser: Any, command: dict[str, Any]) -> dict[str, Any]:
    parsed_url = urlparse(str(command.get("url", "")))
    if parsed_url.hostname == "blauwwit.allbooked.com":
        return check_allbooked_slot(browser, command)
    if parsed_url.hostname == "rscbuitenveldert.bookaball.com":
        return check_bookaball_slot(browser, command)
    if parsed_url.hostname == "my.uscsport.nl":
        return check_usc_slot(browser, command)
    if parsed_url.hostname in {
        "amstelpark.baanreserveren.nl",
        "fransotten.baanreserveren.nl",
    }:
        return check_baanreserveren_slot(browser, command)

    selected_date = date.fromisoformat(command["date"])
    start_time = str(command["start_time"])
    duration_minutes = int(command["duration_minutes"])
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time):
        raise ValueError("Start time must use HH:MM in 24-hour format.")
    if duration_minutes < 15 or duration_minutes > 300:
        raise ValueError("Duration must be between 15 and 300 minutes.")

    context = browser.new_context(locale="nl-NL")
    try:
        page = context.new_page()
        booking_url = url_for_date(command["url"], selected_date)
        page.goto(
            booking_url,
            wait_until="domcontentloaded",
            timeout=45_000,
        )
        page.locator("#date").wait_for(state="visible", timeout=25_000)
        page.wait_for_timeout(700)
        reject_optional_cookies(page)

        expected_page_date = selected_date.strftime("%d-%m-%Y")
        if page.locator("#date").input_value() != expected_page_date:
            return {
                "status": "Could not verify - requested date was not applied",
                "reason": "Meet & Play did not display the date selected in the dashboard.",
            }

        sport_filter = page.locator("#sportId")
        if not sport_filter.count():
            return {
                "status": "Could not verify - tennis filter is missing",
                "reason": "Meet & Play did not expose a sport filter for this club.",
            }
        tennis_option = next(
            (
                option
                for option in sport_filter.locator("option").all()
                if option.inner_text().strip().casefold() == "tennis"
            ),
            None,
        )
        if tennis_option is None:
            return {
                "status": "Could not verify - tennis is not offered",
                "reason": "This Meet & Play club does not list a tennis sport option.",
            }
        tennis_value = tennis_option.get_attribute("value")
        if sport_filter.input_value() != tennis_value:
            if sport_filter.is_disabled():
                return {
                    "status": "Could not verify - tennis filter is unavailable",
                    "reason": "Meet & Play did not allow selecting tennis for this club.",
                }
            wait_for_livewire_update(
                page,
                lambda: sport_filter.select_option(tennis_value),
            )
            page.wait_for_function(
                """value => {
                    const select = document.querySelector("#sportId");
                    return select && select.value === value;
                }""",
                arg=tennis_value,
                timeout=10_000,
            )

        duration_label = f"{duration_minutes} minuten"
        duration_control = next(
            (
                control
                for control in page.locator("span.pill").all()
                if control.inner_text().strip() == duration_label
            ),
            None,
        )
        if duration_control is None:
            return {
                "status": "Could not verify - duration is not offered",
                "reason": (
                    f"Meet & Play does not offer a {duration_minutes}-minute "
                    "court duration for this club."
                ),
            }
        if not duration_control.evaluate("element => element.classList.contains('active')"):
            wait_for_livewire_update(page, duration_control.click)
            page.wait_for_function(
                """label => Array.from(document.querySelectorAll("span.pill"))
                    .some(element => element.innerText.trim() === label &&
                      element.classList.contains("active"))""",
                arg=duration_label,
                timeout=10_000,
            )

        time_options = page.locator('input[name="time"]')
        available_start_times = time_options.evaluate_all(
            "elements => elements.map(element => element.value)"
        )
        if start_time not in available_start_times:
            return {
                "status": "Could not verify - start time is not shown",
                "reason": (
                    "Meet & Play did not list the requested start time for this "
                    "date and duration. The page does not indicate whether this "
                    "is due to the booking horizon, seasonal availability, or "
                    "the selected time not being offered."
                ),
            }

        requested_time_option = page.locator(
            f'input[name="time"][value="{start_time}"]'
        )
        if not requested_time_option.is_checked():
            time_label = page.locator(f'label[for="time-{start_time}"]')
            wait_for_livewire_update(page, time_label.click)
            page.wait_for_function(
                """value => {
                    const input = document.querySelector(
                      `input[name="time"][value="${value}"]`
                    );
                    return input && input.checked;
                }""",
                arg=start_time,
                timeout=10_000,
            )

        page.wait_for_timeout(500)
        page_content = read_visible_page(page)
        result = inspect_slot(
            page_text=page_content["text"],
            controls=page_content["controls"],
            current_url=page.url,
            selected_date=selected_date,
            start_time=start_time,
            duration_minutes=duration_minutes,
        )
        if result["status"] == "Could not verify - exact interval not shown":
            normalized_page_text = normalize_text(page_content["text"])
            if "er zijn geen tijdslots gevonden voor je huidige filters" in normalized_page_text:
                return {
                    "status": "Could not verify - no court slots are shown",
                    "reason": (
                        "Meet & Play showed no time slots for the selected date. "
                        "The page does not indicate whether this is due to the "
                        "booking horizon, seasonal availability, or the selected "
                        "time being fully booked."
                    ),
                }
        if result["status"].startswith("Available"):
            court_calendar = page.evaluate(
                """() => {
                  const sections = Array.from(document.querySelectorAll(
                    ".mp-court-type"
                  )).map(header => {
                    const courtContainer = header.nextElementSibling;
                    const courts = courtContainer &&
                      courtContainer.classList.contains("timeslots")
                      ? Array.from(courtContainer.querySelectorAll(
                          ".timeslot-container .timeslot"
                        )).map(element => ({
                          text: (element.innerText || "").trim(),
                          name: ((element.innerText || "").match(
                            /\\bBaan\\s+\\S+/i
                          ) || [""])[0]
                        }))
                      : [];
                    return {
                      label: (header.innerText || "").trim(),
                      courts
                    };
                  });
                  return {sections};
                }"""
            )
            result["available_courts"] = inspect_meetandplay_available_courts(
                court_calendar,
                start_time,
                duration_minutes,
            )
        return result
    finally:
        context.close()


def check_allbooked_slot(browser: Any, command: dict[str, Any]) -> dict[str, Any]:
    selected_date = date.fromisoformat(command["date"])
    start_time = str(command["start_time"])
    duration_minutes = int(command["duration_minutes"])
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time):
        raise ValueError("Start time must use HH:MM in 24-hour format.")
    if duration_minutes < 15 or duration_minutes > 300:
        raise ValueError("Duration must be between 15 and 300 minutes.")

    context = browser.new_context(
        locale="nl-NL",
        viewport={"width": 1920, "height": 1000},
    )
    try:
        page = context.new_page()
        page.goto(
            allbooked_url_for_date(command.get("url"), selected_date),
            wait_until="domcontentloaded",
            timeout=45_000,
        )
        page.locator('th[title^="Click for info about"]').first.wait_for(
            state="visible",
            timeout=25_000,
        )
        page.wait_for_timeout(500)
        if (
            urlparse(page.url).hostname != "blauwwit.allbooked.com"
            or urlparse(page.url).path.rstrip("/") != "/booking"
        ):
            return {
                "status": "Could not verify - public calendar is unavailable",
                "reason": "Blauw-Wit's public AllBooked day calendar did not load.",
            }

        calendar = page.evaluate(
            """() => {
              const dateButton = Array.from(document.querySelectorAll("button"))
                .find(element => /\\b\\d{1,2}\\s+[A-Z]+\\s+\\d{4}\\b/i.test(
                  (element.innerText || "").trim()
                ));
              const courts = Array.from(document.querySelectorAll("th"))
                .filter(element =>
                  !element.classList.contains("scheduler-time-column")
                )
                .map(element => (element.innerText || "").trim())
                .filter(Boolean);
              const timeLabels = Array.from(document.querySelectorAll(
                "th.scheduler-time-column"
              )).map(element => (element.innerText || "").trim()).filter(Boolean);
              const visible = element => {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return style.visibility !== "hidden" &&
                  style.display !== "none" &&
                  rect.width > 0 &&
                  rect.height > 0;
              };
              const events = Array.from(document.querySelectorAll(
                ".day-mode-bookings-table .booking-div"
              )).filter(visible).map(element => ({
                court_index: element.getAttribute("data-space-index"),
                text: (element.innerText || "").trim()
              }));
              return {
                date_text: dateButton ? dateButton.innerText : "",
                courts,
                time_labels: timeLabels,
                events
              };
            }"""
        )
        return inspect_allbooked_calendar(
            calendar=calendar,
            selected_date=selected_date,
            start_time=start_time,
            duration_minutes=duration_minutes,
        )
    finally:
        context.close()


def run_worker() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        emit({"ok": False, "error": f"Playwright is not installed: {error}"})
        return 1

    try:
        with sync_playwright() as playwright:
            log_worker_diagnostic("Starting Chromium.")
            browser = playwright.chromium.launch(headless=True)
            try:
                log_worker_diagnostic("Chromium is ready.")
                emit({"ok": True, "ready": True})
                for line in sys.stdin:
                    command: dict[str, Any] = {}
                    try:
                        command = json.loads(line)
                        action = command.get("action")
                        if action == "CHECK":
                            result = check_public_slot(browser, command)
                            save_worker_result(command, result)
                            log_worker_result(result)
                            emit(
                                {
                                    "ok": True,
                                    **result,
                                }
                            )
                        elif action == "STOP":
                            emit({"ok": True, "stopped": True})
                            return 0
                        else:
                            raise ValueError("Unknown browser command.")
                    except (KeyError, TypeError, ValueError) as error:
                        error_message = sanitized_worker_error(error, command)
                        log_worker_diagnostic(f"Check rejected: {error_message}")
                        if command.get("action") == "CHECK":
                            error_result = {
                                "status": "Could not verify - check failed",
                                "reason": error_message,
                            }
                            save_worker_result(command, error_result)
                            log_worker_result(error_result)
                        emit({"ok": False, "error": error_message})
                    except Exception as error:
                        error_message = sanitized_worker_error(error, command)
                        log_worker_diagnostic(f"Check failed: {error_message}")
                        if command.get("action") == "CHECK":
                            error_result = {
                                "status": "Could not verify - check failed",
                                "reason": error_message,
                            }
                            save_worker_result(command, error_result)
                            log_worker_result(error_result)
                        emit(
                            {
                                "ok": False,
                                "error": f"Booking page could not be read: {error_message}",
                            }
                        )
                        if any(
                            marker in error_message.casefold()
                            for marker in (
                                "target page, context or browser has been closed",
                                "browser has been closed",
                                "context has been closed",
                                "page has been closed",
                                "browser is disconnected",
                            )
                        ):
                            return 1
            finally:
                browser.close()
    except Exception as error:
        emit({"ok": False, "error": f"Could not start the automatic checker: {error}"})
        return 1
    return 0


def main() -> int:
    return run_worker()


if __name__ == "__main__":
    raise SystemExit(main())
