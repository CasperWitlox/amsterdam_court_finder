"""Validated sponsor and Cloudflare Web Analytics configuration."""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


@dataclass(frozen=True)
class Sponsor:
    name: str
    message: str
    url: str


SPONSOR_ENVIRONMENT_KEYS = (
    "ACF_SPONSOR_NAME",
    "ACF_SPONSOR_MESSAGE",
    "ACF_SPONSOR_URL",
)


def load_sponsor(
    environment: Mapping[str, str] | None = None,
) -> Sponsor | None:
    values = environment if environment is not None else os.environ
    configured = {
        key: str(values.get(key, "")).strip()
        for key in SPONSOR_ENVIRONMENT_KEYS
    }
    if not any(configured.values()):
        return None

    missing = [key for key, value in configured.items() if not value]
    if missing:
        raise ValueError(
            "Sponsor configuration is incomplete. Set all of: "
            + ", ".join(SPONSOR_ENVIRONMENT_KEYS)
            + "."
        )

    name = configured["ACF_SPONSOR_NAME"]
    message = configured["ACF_SPONSOR_MESSAGE"]
    url = configured["ACF_SPONSOR_URL"]
    if len(name) > 100 or len(message) > 280:
        raise ValueError(
            "ACF_SPONSOR_NAME must be at most 100 characters and "
            "ACF_SPONSOR_MESSAGE at most 280 characters."
        )

    parsed_url = urlsplit(url)
    if (
        parsed_url.scheme != "https"
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
    ):
        raise ValueError("ACF_SPONSOR_URL must be a valid HTTPS URL.")

    return Sponsor(name=name, message=message, url=url)


def sponsor_click_url(sponsor: Sponsor) -> str:
    parsed_url = urlsplit(sponsor.url)
    campaign = re.sub(r"[^a-z0-9]+", "-", sponsor.name.casefold()).strip("-")
    query = [
        (key, value)
        for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)
        if key.casefold()
        not in {"utm_source", "utm_medium", "utm_campaign"}
    ]
    query.extend(
        (
            ("utm_source", "amsterdamcourtfinder"),
            ("utm_medium", "sponsored"),
            ("utm_campaign", campaign or "local-sponsor"),
        )
    )
    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            urlencode(query),
            parsed_url.fragment,
        )
    )


def cloudflare_analytics_markup(
    environment: Mapping[str, str] | None = None,
) -> str | None:
    values = environment if environment is not None else os.environ
    token = str(values.get("CLOUDFLARE_WEB_ANALYTICS_TOKEN", "")).strip()
    if not token:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", token):
        raise ValueError(
            "CLOUDFLARE_WEB_ANALYTICS_TOKEN must contain 8–128 letters, "
            "numbers, underscores, or hyphens."
        )

    beacon_config = html.escape(
        json.dumps({"token": token}, separators=(",", ":")),
        quote=True,
    )
    return (
        '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
        f'data-cf-beacon="{beacon_config}"></script>'
    )
