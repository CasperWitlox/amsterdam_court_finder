#!/usr/bin/env python3
"""Build the static, searchable venue directory from the app's public data."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urlsplit


ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = ROOT / "static_site"
OUTPUT = STATIC_ROOT / "dist"
sys.path.insert(0, str(ROOT))

from monetization import (  # noqa: E402
    Sponsor,
    cloudflare_analytics_markup,
    load_sponsor,
    sponsor_click_url,
)


SUPPORTED_SPORTS = {"tennis", "padel", "pickleball", "squash"}
ALLOWED_IMPORT_FIELDS = {
    "name",
    "city",
    "sports",
    "neighborhood",
    "address",
    "booking_url",
    "club_website",
    "price_info",
    "court_type",
    "access_notes",
    "description",
    "source_url",
    "last_verified",
    "venue_type",
}


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def bilingual(english: str, dutch: str, *, tag: str = "span") -> str:
    return (
        f'<{tag} data-en="{escape(english)}" data-nl="{escape(dutch)}">'
        f"{escape(english)}</{tag}>"
    )


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    if not slug:
        raise ValueError(f"Could not create a URL slug from {value!r}.")
    return slug


def validated_url(value: Any, *, field: str, required: bool = False) -> str:
    if value in (None, ""):
        if required:
            raise ValueError(f"Catalog field {field!r} is required.")
        return ""
    if not isinstance(value, str):
        raise ValueError(f"Catalog field {field!r} must be a URL string.")
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError(
            f"Catalog field {field!r} must be an HTTP or HTTPS URL "
            "without embedded credentials."
        )
    return value.strip()


def infer_city(name: str, neighborhood: str, address: str = "") -> str:
    text = f"{name} {neighborhood} {address}".casefold()
    for token, city in (
        ("amstelveen", "Amstelveen"),
        ("badhoevedorp", "Badhoevedorp"),
        ("ouderkerk", "Ouderkerk aan de Amstel"),
        ("diemen", "Diemen"),
    ):
        if token in text:
            return city
    if "amsterdam" in text:
        return "Amsterdam"
    return "Amsterdam area"


def _validate_imported_venue(item: Any, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"Imported venue {index} must be a JSON object.")
    unknown = set(item) - ALLOWED_IMPORT_FIELDS
    if unknown:
        raise ValueError(
            f"Imported venue {index} has unsupported fields: "
            + ", ".join(sorted(unknown))
            + "."
        )

    name = item.get("name")
    city = item.get("city")
    sports = item.get("sports")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Imported venue {index} needs a non-empty name.")
    if not isinstance(city, str) or not city.strip():
        raise ValueError(f"Imported venue {index} needs a non-empty city.")
    if (
        not isinstance(sports, list)
        or not sports
        or any(
            not isinstance(sport, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]*", sport)
            or sport not in SUPPORTED_SPORTS
            for sport in sports
        )
    ):
        raise ValueError(
            f"Imported venue {index} needs a non-empty list of supported "
            "lowercase sport identifiers (tennis, padel, pickleball, squash)."
        )

    source_url = validated_url(
        item.get("source_url"),
        field=f"venue {index} source_url",
        required=True,
    )
    text_fields = (
        "neighborhood",
        "address",
        "price_info",
        "court_type",
        "access_notes",
        "description",
        "last_verified",
        "venue_type",
    )
    result = {}
    for key in text_fields:
        value = item.get(key, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(
                f"Imported venue {index} field {key!r} must be a string."
            )
        result[key] = value.strip()
    if result["venue_type"] not in {"", "club", "public_court"}:
        raise ValueError(
            f"Imported venue {index} venue_type must be 'club' or 'public_court'."
        )
    result.update(
        name=name.strip(),
        city=city.strip(),
        sports=list(dict.fromkeys(sports)),
        booking_url=validated_url(
            item.get("booking_url"),
            field=f"venue {index} booking_url",
        ),
        club_website=validated_url(
            item.get("club_website"),
            field=f"venue {index} club_website",
        ),
        source_url=source_url,
        venue_type=result["venue_type"] or "club",
        last_verified=result["last_verified"],
    )
    if result["last_verified"]:
        try:
            date.fromisoformat(result["last_verified"])
        except ValueError as error:
            raise ValueError(
                f"Imported venue {index} last_verified must use YYYY-MM-DD."
            ) from error
    return result


def load_catalog_import(path: Path) -> list[dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read catalog import at {path}: {error}") from error
    if not isinstance(raw, list):
        raise ValueError(f"Catalog import at {path} must be a JSON list.")
    return [_validate_imported_venue(item, index + 1) for index, item in enumerate(raw)]


def application_catalog() -> list[dict[str, Any]]:
    import tennis_court_finder_app as app

    venues = []
    for club in app.default_clubs():
        name = club["name"]
        capacity_notes = app.MEMBERSHIP_CAPACITY_INFO.get(name, {}).get("notes", "")
        evidence = " ".join(
            (
                name,
                str(club.get("court_type", "")),
                str(club.get("other_notes", "")),
                str(capacity_notes),
            )
        ).casefold()
        sports = ["tennis"]
        if re.search(r"\bpadel\b", evidence):
            sports.append("padel")

        neighborhood = str(club.get("neighborhood", "")).strip()
        address = str(club.get("address", "")).strip()
        if address.startswith(f"{name}, Amsterdam,"):
            address = ""
        source_url = validated_url(
            club.get("club_website") or club.get("booking_url"),
            field=f"{name} source URL",
        )
        venues.append(
            {
                "name": name,
                "city": infer_city(name, neighborhood, address),
                "sports": sports,
                "neighborhood": neighborhood,
                "address": address,
                "booking_url": validated_url(
                    club.get("booking_url"),
                    field=f"{name} booking URL",
                ),
                "club_website": validated_url(
                    club.get("club_website"),
                    field=f"{name} club website",
                ),
                "price_info": str(club.get("price_info", "")).strip(),
                "court_type": str(club.get("court_type", "")).strip(),
                "access_notes": str(club.get("access_notes", "")).strip(),
                "description": str(club.get("other_notes", "")).strip(),
                "source_url": source_url,
                "last_verified": "",
                "venue_type": "club",
            }
        )

    for court in app.SINGLE_NOT_FOR_RENT_COURTS:
        neighborhood = str(court.get("neighborhood", "")).strip()
        address = str(court.get("address", "")).strip()
        venues.append(
            {
                "name": str(court["name"]),
                "city": infer_city(str(court["name"]), neighborhood, address),
                "sports": ["tennis"],
                "neighborhood": neighborhood,
                "address": address,
                "booking_url": "",
                "club_website": "",
                "price_info": "Public court; not reservable",
                "court_type": str(court.get("court_surface", "")).strip(),
                "access_notes": "Public access; advance booking unavailable",
                "description": "",
                "source_url": "",
                "last_verified": "",
                "venue_type": "public_court",
            }
        )

    return venues


def build_catalog(import_path: Path) -> list[dict[str, Any]]:
    venues = application_catalog() + load_catalog_import(import_path)
    seen: set[tuple[str, str]] = set()
    for venue in venues:
        venue["id"] = slugify(f"{venue['name']}-{venue['city']}")
        duplicate_key = (venue["name"].casefold(), venue["city"].casefold())
        if duplicate_key in seen:
            raise ValueError(
                f"Duplicate venue name and city in catalog: "
                f"{venue['name']} ({venue['city']})."
            )
        seen.add(duplicate_key)
    return sorted(
        venues,
        key=lambda venue: (
            venue["city"].casefold(),
            venue["name"].casefold(),
        ),
    )


def relative_link(current: Path, target: Path) -> str:
    return Path(os.path.relpath(target, current.parent)).as_posix()


def maps_search_url(venue: dict[str, Any]) -> str:
    place = venue.get("address") or venue.get("neighborhood") or venue["city"]
    query = ", ".join(
        part
        for part in (venue["name"], place, venue["city"], "Netherlands")
        if part
    )
    return "https://www.google.com/maps/search/?" + urlencode(
        {"api": "1", "query": query}
    )


def canonical_url(site_url: str, relative_path: Path) -> str:
    if relative_path.name == "index.html":
        suffix = "" if relative_path.parent == Path(".") else (
            relative_path.parent.as_posix().rstrip("/") + "/"
        )
    else:
        suffix = relative_path.as_posix()
    return f"{site_url.rstrip('/')}/{suffix}"


def sponsor_card(sponsor: Sponsor | None) -> str:
    if sponsor is None:
        return ""
    url = escape(sponsor_click_url(sponsor))
    return f"""
      <aside class="sponsor-card" aria-label="Sponsored listing">
        <span class="sponsor-label">{bilingual("Sponsored", "Gesponsord")}</span>
        <h2>{escape(sponsor.name)}</h2>
        <p>{escape(sponsor.message)}</p>
        <a class="button secondary" href="{url}" target="_blank" rel="noopener noreferrer">
          {bilingual("Visit sponsor", "Bekijk partner")}
        </a>
      </aside>
    """


def venue_card(venue: dict[str, Any], current: Path) -> str:
    details_link = relative_link(
        current,
        Path("venues") / venue["id"] / "index.html",
    )
    sports = "".join(
        f'<span class="tag">{escape(sport.title())}</span>'
        for sport in venue["sports"]
    )
    detail_rows = []
    if venue["neighborhood"]:
        detail_rows.append(
            f"<p><strong>{bilingual('Area', 'Omgeving', tag='span')}</strong>: "
            f"{escape(venue['neighborhood'])}</p>"
        )
    if venue["price_info"]:
        detail_rows.append(
            f"<p><strong>{bilingual('Price / access', 'Prijs / toegang', tag='span')}</strong>: "
            f"{escape(venue['price_info'])}</p>"
        )
    return f"""
      <article class="venue-card" data-venue-card
          data-search="{escape((venue['name'] + ' ' + venue['city'] + ' ' + venue['neighborhood']).casefold())}"
          data-city="{escape(venue['city'])}"
          data-sports="{escape(' '.join(venue['sports']))}">
        <h2><a href="{escape(details_link)}">{escape(venue['name'])}</a></h2>
        <div class="tag-list">{sports}</div>
        <p><strong>{bilingual('Location', 'Plaats', tag='span')}</strong>: {escape(venue['city'])}</p>
        {''.join(detail_rows)}
        <a href="{escape(details_link)}">{bilingual('View venue profile', 'Bekijk locatieprofiel')}</a>
        <a class="button secondary" href="{escape(maps_search_url(venue))}" target="_blank" rel="noopener noreferrer">
          {bilingual('Open map search', 'Zoek op kaart')}
        </a>
      </article>
    """


def area_navigation(venues: list[dict[str, Any]], current: Path) -> str:
    counts = Counter(venue["city"] for venue in venues)
    if not counts:
        return ""

    links = []
    for city, count in sorted(counts.items(), key=lambda item: item[0].casefold()):
        location_page = Path("locations") / slugify(city) / "index.html"
        count_label = bilingual(f"{count} listings", f"{count} locaties")
        links.append(
            f'<a class="area-link" href="{escape(relative_link(current, location_page))}">'
            f"<span>{escape(city)}</span>"
            f'<span class="area-count">{count_label}</span>'
            "</a>"
        )
    return f"""
      <section class="area-browser" aria-labelledby="area-heading">
        <h2 id="area-heading">{bilingual('Browse by location', 'Ontdek locaties per plaats')}</h2>
        <div class="area-grid">{''.join(links)}</div>
      </section>
    """


def directory_body(
    title: str,
    description: str,
    venues: list[dict[str, Any]],
    current: Path,
    cities: list[str],
    sports: list[str],
    *,
    selected_city: str = "",
    selected_sport: str = "",
    browse_areas: bool = False,
    sponsor: Sponsor | None = None,
) -> str:
    sport_options = "".join(
        f'<option value="{escape(sport)}"'
        f'{" selected" if sport == selected_sport else ""}>'
        f"{escape(sport.title())}</option>"
        for sport in sports
    )
    city_options = "".join(
        f'<option value="{escape(city)}"'
        f'{" selected" if city == selected_city else ""}>'
        f"{escape(city)}</option>"
        for city in cities
    )
    cards = "".join(venue_card(venue, current) for venue in venues)
    if not cards:
        cards = (
            '<p class="content-card">'
            "No venues are listed for this selection yet. Listings are added "
            "from verifiable sources; suggest an update on the For club owners page."
            "</p>"
        )
    return f"""
      <section class="hero">
        <p class="eyebrow">{bilingual('Amsterdam area directory', 'Gids voor Amsterdam en omgeving')}</p>
        <h1>{escape(title)}</h1>
        <p>{escape(description)}</p>
        <a class="button" href="{escape(os.environ.get('CHECKER_URL', 'https://amsterdamcourtfinder.nl/'))}">
          {bilingual('Check live availability', 'Bekijk live beschikbaarheid')}
        </a>
        <a class="button secondary" href="{relative_link(current, Path('advertise/index.html'))}">
          {bilingual('Advertise with us', 'Adverteer bij ons')}
        </a>
      </section>
      {sponsor_card(sponsor)}
      {area_navigation(venues, current) if browse_areas else ""}
      <section aria-labelledby="directory-heading">
        <h2 id="directory-heading">{bilingual('Find a venue', 'Vind een locatie')}</h2>
        <div class="directory-tools">
          <label for="venue-search">
            {bilingual('Search by venue or area', 'Zoek op locatie of omgeving')}
            <input id="venue-search" type="search" autocomplete="off">
          </label>
          <label for="sport-filter">
            {bilingual('Sport', 'Sport')}
            <select id="sport-filter">
              <option value="" data-en="All sports" data-nl="Alle sporten">All sports</option>
              {sport_options}
            </select>
          </label>
          <label for="city-filter">
            {bilingual('City / area', 'Plaats / omgeving')}
            <select id="city-filter">
              <option value="" data-en="All locations" data-nl="Alle plaatsen">All locations</option>
              {city_options}
            </select>
          </label>
        </div>
        <p id="listing-count" class="listing-count" role="status" aria-live="polite"></p>
        <p id="empty-results" hidden>
          {bilingual('No venues match these filters.', 'Geen locaties gevonden met deze filters.')}
        </p>
        <div class="venue-grid">{cards}</div>
      </section>
      <p class="disclosure">
        {bilingual(
            "Listings and prices may be outdated. Live availability is not checked on these static pages; confirm details with the venue or use its booking page.",
            "Locatie- en prijsinformatie kan verouderd zijn. Op deze statische pagina's wordt geen live beschikbaarheid gecontroleerd; bevestig gegevens bij de locatie of gebruik de boekingspagina.",
        )}
      </p>
    """


def detail_list(venue: dict[str, Any]) -> str:
    labels = (
        ("City / area", "Plaats / omgeving", "city"),
        ("Neighborhood", "Wijk", "neighborhood"),
        ("Address", "Adres", "address"),
        ("Sports", "Sporten", "sports"),
        ("Price information", "Prijsinformatie", "price_info"),
        ("Court surface", "Baansoort", "court_type"),
        ("Booking access", "Toegang", "access_notes"),
        ("Last verified", "Laatst gecontroleerd", "last_verified"),
    )
    rows = []
    for english, dutch, key in labels:
        value = ", ".join(venue[key]) if key == "sports" else venue.get(key, "")
        if value:
            rows.append(
                f"<dt>{bilingual(english, dutch)}</dt><dd>{escape(value)}</dd>"
            )
    return "".join(rows)


def profile_body(
    venue: dict[str, Any],
    sponsor: Sponsor | None,
    checker_url: str,
) -> str:
    sports = "".join(
        f'<span class="tag">{escape(sport.title())}</span>'
        for sport in venue["sports"]
    )
    links = []
    if venue["booking_url"]:
        links.append(
            f'<a class="button" href="{escape(venue["booking_url"])}" '
            'target="_blank" rel="noopener noreferrer">'
            f'{bilingual("Open booking page", "Open boekingspagina")}</a>'
        )
    if venue["club_website"]:
        links.append(
            f'<a class="button secondary" href="{escape(venue["club_website"])}" '
            'target="_blank" rel="noopener noreferrer">'
            f'{bilingual("Official website", "Officiële website")}</a>'
        )
    if venue["source_url"]:
        links.append(
            f'<a href="{escape(venue["source_url"])}" target="_blank" '
            'rel="noopener noreferrer">'
            f'{bilingual("Listing source", "Bron van vermelding")}</a>'
        )
    links.append(
        f'<a class="button secondary" href="{escape(maps_search_url(venue))}" '
        'target="_blank" rel="noopener noreferrer">'
        f'{bilingual("Open map search", "Zoek op kaart")}</a>'
    )
    if venue["venue_type"] != "public_court":
        links.append(
            f'<a class="button" href="{escape(checker_url)}">'
            f'{bilingual("Open the Amsterdam live checker", "Open de live checker voor Amsterdam")}</a>'
        )
    return f"""
      <section class="hero">
        <p class="eyebrow">{escape(venue['city'])}</p>
        <h1>{escape(venue['name'])}</h1>
        <div class="tag-list">{sports}</div>
        <p>{escape(venue.get('description', ''))}</p>
        <div>{''.join(links)}</div>
      </section>
      {sponsor_card(sponsor)}
      <section class="content-card">
        <h2>{bilingual('Venue details', 'Locatiegegevens')}</h2>
        <dl>{detail_list(venue)}</dl>
      </section>
      <p class="disclosure">
        {bilingual(
            "This profile is a static directory entry, not a live booking calendar. Information can change; confirm prices, access, and availability with the venue before travelling or paying.",
            "Dit profiel is een statische gidsvermelding en geen live boekingskalender. Informatie kan veranderen; bevestig prijzen, toegang en beschikbaarheid bij de locatie voordat je reist of betaalt.",
        )}
      </p>
    """


def advertiser_body(
    venues: list[dict[str, Any]],
    current: Path,
    sponsor: Sponsor | None,
) -> str:
    sport_counts: dict[str, int] = {}
    for venue in venues:
        for sport in venue["sports"]:
            sport_counts[sport] = sport_counts.get(sport, 0) + 1
    coverage = ", ".join(
        f"{count} {sport} listings"
        for sport, count in sorted(sport_counts.items())
    )
    subject = quote("Amsterdam Court Finder sponsorship pilot")
    return f"""
      <section class="hero">
        <p class="eyebrow">{bilingual('Local sponsorships', 'Lokale sponsoring')}</p>
        <h1>{bilingual('Reach people choosing where to play', 'Bereik mensen die een baan zoeken')}</h1>
        <p>{bilingual(
            'We are testing a small, clearly labelled sponsor placement alongside relevant venue listings. It is designed for local racket-sport businesses, not a crowded display-ad network.',
            'We testen een kleine, duidelijk gemarkeerde sponsorvermelding bij relevante locaties. Dit is bedoeld voor lokale racketsportbedrijven, niet voor een overvol netwerk met banners.',
        )}</p>
        <a class="button" href="mailto:info@amsterdamcourtfinder.nl?subject={subject}">
          {bilingual('Discuss a pilot', 'Bespreek een pilot')}
        </a>
      </section>
      {sponsor_card(sponsor)}
      <section class="content-card">
        <h2>{bilingual('A simple pilot', 'Een eenvoudige pilot')}</h2>
        <ul>
          <li>{bilingual('One clearly labelled sponsor card in relevant directory pages.', 'Eén duidelijk gemarkeerde sponsorvermelding op relevante gids-paginas.')}</li>
          <li>{bilingual('A 30-day test with a fixed fee agreed in advance; no guaranteed bookings or audience claims.', 'Een proef van 30 dagen tegen een vooraf afgesproken vast bedrag; geen gegarandeerde boekingen of bezoekersaantallen.')}</li>
          <li>{bilingual('Traffic reports only after analytics are enabled and enough data exists. Cloudflare Web Analytics reports visits and page performance, not sponsor-click conversions.', 'Verkeersrapporten pas nadat analytics actief zijn en er voldoende gegevens zijn. Cloudflare Web Analytics meet bezoeken en paginaprestaties, geen conversies van sponsorlinks.')}</li>
          <li>{bilingual('Tagged sponsor links let your own analytics identify visits referred by Amsterdam Court Finder.', 'Getagde sponsorlinks laten je eigen analytics bezoeken vanuit Amsterdam Court Finder herkennen.')}</li>
        </ul>
        <p><strong>{bilingual('Current directory coverage', 'Huidige gidsdekking')}:</strong> {escape(coverage)}.</p>
        <p>{bilingual(
            'These are listing counts, not visitor or impression counts. We will share audience numbers only when they are measured.',
            'Dit zijn aantallen vermeldingen, geen bezoekers- of vertoningsaantallen. We delen bezoekerscijfers pas wanneer die daadwerkelijk zijn gemeten.',
        )}</p>
      </section>
      <section class="content-card">
        <h2>{bilingual('Good initial partners', 'Geschikte eerste partners')}</h2>
        <p>{bilingual(
            'Racket shops, coaches, sports physiotherapists, local tournaments, and booking services whose offers fit the selected sport and area.',
            'Racketsportwinkels, trainers, sportfysiotherapeuten, lokale toernooien en boekingsdiensten met een passend aanbod voor de gekozen sport en omgeving.',
        )}</p>
      </section>
      <p class="disclosure">
        {bilingual(
            'Paid placements are labelled and do not change the order or accuracy of venue information. We do not run programmatic advertising or collect sponsor-click profiles.',
            'Betaalde vermeldingen zijn herkenbaar en veranderen de volgorde of juistheid van locatiegegevens niet. We gebruiken geen programmatic advertenties en bouwen geen profielen van sponsor-kliks op.',
        )}
      </p>
    """


def owner_body() -> str:
    subject = quote("Update a venue listing")
    return f"""
      <section class="hero">
        <p class="eyebrow">{bilingual('For venue owners', 'Voor locatiebeheerders')}</p>
        <h1>{bilingual('Help players find accurate venue information', 'Help spelers actuele locatiegegevens te vinden')}</h1>
        <p>{bilingual(
            'There is no automated claim portal yet. Send a correction or listing suggestion and we will review its public source before updating the directory.',
            'Er is nog geen automatisch beheerdersportaal. Stuur een correctie of suggestie; we controleren de openbare bron voordat we de gids aanpassen.',
        )}</p>
        <a class="button" href="mailto:info@amsterdamcourtfinder.nl?subject={subject}">
          {bilingual('Suggest an update', 'Stel een wijziging voor')}
        </a>
      </section>
      <section class="content-card">
        <h2>{bilingual('What to include', 'Wat je kunt meesturen')}</h2>
        <ul>
          <li>{bilingual('Venue name, city, and sports offered.', 'Naam van de locatie, plaats en aangeboden sporten.')}</li>
          <li>{bilingual('Official website and direct booking page.', 'Officiële website en directe boekingspagina.')}</li>
          <li>{bilingual('Court types, public or member access, and current price information.', 'Baansoorten, toegang voor bezoekers of leden, en actuele prijsinformatie.')}</li>
          <li>{bilingual('A public source URL and the date the information was last confirmed.', 'Een openbare bron-URL en de datum waarop de informatie voor het laatst is bevestigd.')}</li>
        </ul>
        <p>{bilingual(
            'Listings are informational. A correction request does not imply endorsement or a paid placement.',
            'Vermeldingen zijn informatief. Een correctieverzoek betekent geen aanbeveling of betaalde plaatsing.',
        )}</p>
      </section>
    """


def privacy_body() -> str:
    return f"""
      <section class="hero">
        <p class="eyebrow">{bilingual('Privacy & data', 'Privacy en gegevens')}</p>
        <h1>{bilingual('A lightweight directory', 'Een lichte gids')}</h1>
        <p>{bilingual(
            'These static pages do not request a starting address, booking credentials, or account details.',
            'Deze statische pagina’s vragen niet om een startadres, boekingsinloggegevens of accountgegevens.',
        )}</p>
      </section>
      <section class="content-card">
        <h2>{bilingual('Analytics', 'Analytics')}</h2>
        <p>{bilingual(
            'If enabled for this Pages project, Cloudflare Web Analytics reports page views, visits, and performance. Cloudflare states that Web Analytics does not collect or use visitors’ personal data. See the Cloudflare privacy documentation for details.',
            'Als dit Pages-project dit inschakelt, rapporteert Cloudflare Web Analytics paginaweergaven, bezoeken en prestaties. Cloudflare vermeldt dat Web Analytics geen persoonsgegevens van bezoekers verzamelt of gebruikt. Bekijk de privacydocumentatie van Cloudflare voor details.',
        )}</p>
        <p><a href="https://developers.cloudflare.com/web-analytics/about/" target="_blank" rel="noopener noreferrer">Cloudflare Web Analytics privacy information</a></p>
      </section>
      <section class="content-card">
        <h2>{bilingual('External links', 'Externe links')}</h2>
        <p>{bilingual(
            'Venue and sponsor links open external websites, which have their own privacy policies. Sponsor links use generic campaign parameters so an advertiser can identify referral traffic in its own analytics; this site does not use them to identify individual visitors.',
            'Links naar locaties en sponsors openen externe websites met hun eigen privacybeleid. Sponsorlinks gebruiken algemene campagneparameters zodat een adverteerder verwijzingsverkeer in de eigen analytics kan herkennen; deze site gebruikt die parameters niet om individuele bezoekers te identificeren.',
        )}</p>
        <p>{bilingual(
            'Availability checks, booking credentials, starting addresses, weather requests, and cycling routes are handled by the separate interactive checker.',
            'Beschikbaarheidscontroles, boekingsinloggegevens, startadressen, weerverzoeken en fietsroutes lopen via de aparte interactieve checker.',
        )}</p>
      </section>
      <p>{bilingual('Privacy questions: ', 'Privacyvragen: ')}<a href="mailto:info@amsterdamcourtfinder.nl">info@amsterdamcourtfinder.nl</a></p>
    """


def render_page(
    relative_path: Path,
    title: str,
    description: str,
    body: str,
    template: str,
    site_url: str,
    checker_url: str,
) -> str:
    privacy_path = Path("privacy") / "index.html"
    replacements = {
        "{{TITLE}}": escape(title),
        "{{DESCRIPTION}}": escape(description),
        "{{CANONICAL}}": escape(canonical_url(site_url, relative_path)),
        "{{STYLESHEET}}": escape(
            relative_link(relative_path, Path("assets/styles.css"))
        ),
        "{{SCRIPT}}": escape(relative_link(relative_path, Path("assets/site.js"))),
        "{{HOME_LINK}}": escape(relative_link(relative_path, Path("index.html"))),
        "{{ADVERTISE_LINK}}": escape(
            relative_link(relative_path, Path("advertise/index.html"))
        ),
        "{{OWNERS_LINK}}": escape(
            relative_link(relative_path, Path("for-club-owners/index.html"))
        ),
        "{{PRIVACY_LINK}}": escape(relative_link(relative_path, privacy_path)),
        "{{CHECKER_URL}}": escape(checker_url),
        "{{BODY}}": body,
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered


def write_page(
    relative_path: Path,
    title: str,
    description: str,
    body: str,
    template: str,
    site_url: str,
    checker_url: str,
) -> None:
    destination = OUTPUT / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_page(
            relative_path,
            title,
            description,
            body,
            template,
            site_url,
            checker_url,
        ),
        encoding="utf-8",
    )


def build_site() -> int:
    site_url = os.environ.get(
        "DIRECTORY_SITE_URL",
        "https://directory.amsterdamcourtfinder.nl",
    ).strip().rstrip("/")
    checker_url = os.environ.get(
        "CHECKER_URL",
        "https://amsterdamcourtfinder.nl/",
    ).strip()
    site_parts = urlsplit(site_url)
    if (
        site_parts.scheme != "https"
        or not site_parts.hostname
        or site_parts.username
        or site_parts.password
        or site_parts.path not in {"", "/"}
        or site_parts.query
        or site_parts.fragment
    ):
        raise ValueError("DIRECTORY_SITE_URL must be an absolute HTTPS URL.")
    checker_parts = urlsplit(checker_url)
    if (
        checker_parts.scheme != "https"
        or not checker_parts.hostname
        or checker_parts.username
        or checker_parts.password
    ):
        raise ValueError("CHECKER_URL must be an absolute HTTPS URL.")

    sponsor = load_sponsor()
    analytics = cloudflare_analytics_markup()
    template = (STATIC_ROOT / "template.html").read_text(encoding="utf-8")
    if analytics:
        template = template.replace(
            "</head>",
            f"    {analytics}\n  </head>",
        )

    catalog = build_catalog(STATIC_ROOT / "catalog_import.json")
    sports = sorted(
        {sport for venue in catalog for sport in venue["sports"]},
        key=str.casefold,
    )
    cities = sorted({venue["city"] for venue in catalog}, key=str.casefold)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for child in OUTPUT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    (OUTPUT / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STATIC_ROOT / "styles.css", OUTPUT / "assets" / "styles.css")
    shutil.copyfile(STATIC_ROOT / "site.js", OUTPUT / "assets" / "site.js")

    home = Path("index.html")
    write_page(
        home,
        "Tennis and padel venues near Amsterdam",
        "Search tennis and padel venues around Amsterdam by sport and location.",
        directory_body(
            "Find a court in Amsterdam and nearby",
            "Compare local racket-sport venues, access details, price information, and booking links. Live availability is checked separately.",
            catalog,
            home,
            cities,
            sports,
            browse_areas=True,
            sponsor=sponsor,
        ),
        template,
        site_url,
        checker_url,
    )

    page_paths = [home]
    for sport in sports:
        selected = [venue for venue in catalog if sport in venue["sports"]]
        relative = Path("sports") / slugify(sport) / "index.html"
        write_page(
            relative,
            f"{sport.title()} venues near Amsterdam",
            f"Browse {sport} venues in the Amsterdam area.",
            directory_body(
                f"{sport.title()} venues",
                f"Browse {sport} venues in the Amsterdam area, with official booking and club links.",
                selected,
                relative,
                cities,
                sports,
                selected_sport=sport,
                sponsor=sponsor,
            ),
            template,
            site_url,
            checker_url,
        )
        page_paths.append(relative)

    for city in cities:
        city_slug = slugify(city)
        relative = Path("locations") / city_slug / "index.html"
        selected = [venue for venue in catalog if venue["city"] == city]
        write_page(
            relative,
            f"Court venues in {city}",
            f"Browse racket-sport venues in {city}.",
            directory_body(
                f"Venues in {city}",
                f"Browse listed sports venues in {city}.",
                selected,
                relative,
                cities,
                sports,
                selected_city=city,
                sponsor=sponsor,
            ),
            template,
            site_url,
            checker_url,
        )
        page_paths.append(relative)

        for sport in sports:
            sport_venues = [
                venue
                for venue in selected
                if sport in venue["sports"]
            ]
            if not sport_venues:
                continue
            combined = (
                Path("locations")
                / city_slug
                / slugify(sport)
                / "index.html"
            )
            write_page(
                combined,
                f"{sport.title()} venues in {city}",
                f"Browse {sport} venues in {city}.",
                directory_body(
                    f"{sport.title()} venues in {city}",
                    f"Browse listed {sport} venues in {city}.",
                    sport_venues,
                    combined,
                    cities,
                    sports,
                    selected_city=city,
                    selected_sport=sport,
                    sponsor=sponsor,
                ),
                template,
                site_url,
                checker_url,
            )
            page_paths.append(combined)

    advertise = Path("advertise") / "index.html"
    write_page(
        advertise,
        "Advertise with Amsterdam Court Finder",
        "Sponsor a clearly labelled local placement for racket-sport players.",
        advertiser_body(catalog, advertise, sponsor),
        template,
        site_url,
        checker_url,
    )
    page_paths.append(advertise)

    owners = Path("for-club-owners") / "index.html"
    write_page(
        owners,
        "For club owners",
        "Suggest corrections or submit verifiable club information.",
        owner_body(),
        template,
        site_url,
        checker_url,
    )
    page_paths.append(owners)

    privacy = Path("privacy") / "index.html"
    write_page(
        privacy,
        "Privacy and data",
        "Learn what the static directory does and how its external links work.",
        privacy_body(),
        template,
        site_url,
        checker_url,
    )
    page_paths.append(privacy)

    for venue in catalog:
        relative = Path("venues") / venue["id"] / "index.html"
        write_page(
            relative,
            f"{venue['name']} | Amsterdam Court Finder",
            f"Sports, access, prices, and booking links for {venue['name']}.",
            profile_body(venue, sponsor, checker_url),
            template,
            site_url,
            checker_url,
        )
        page_paths.append(relative)

    sitemap = "\n".join(
        f"  <url><loc>{escape(canonical_url(site_url, path))}</loc></url>"
        for path in page_paths
    )
    (OUTPUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{sitemap}\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    (OUTPUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n",
        encoding="utf-8",
    )
    return len(catalog)


if __name__ == "__main__":
    try:
        count = build_site()
    except (OSError, ValueError) as error:
        print(f"Static site build failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Built static directory with {count} venues at {OUTPUT}")
