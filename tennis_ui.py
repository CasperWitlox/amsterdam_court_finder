"""Localization and filtering helpers for the Amsterdam Court Finder UI."""

from __future__ import annotations

import re
from typing import Any


DUTCH_TRANSLATIONS = {
    "Language / Taal": "Taal / Language",
    "English": "Engels",
    "Nederlands": "Nederlands",
    "court": "baan",
    "Court": "Baan",
    "Available courts": "Beschikbare banen",
    "Booking platform": "Boekingsplatform",
    "Privacy & data": "Privacy en gegevens",
    "Club profiles": "Clubprofielen",
    "Availability filter": "Beschikbaarheid",
    "Maximum cycling time (minutes)": "Maximale fietstijd (minuten)",
    "All availability": "Alle statussen",
    "Could not verify": "Niet te verifiëren",
    "Unavailable": "Niet beschikbaar",
    "Too early to check": "Nog te vroeg om te controleren",
    "Not checked": "Niet gecontroleerd",
    "Other status": "Overige status",
    "Showing {shown} of {total} clubs.": "{shown} van {total} clubs worden getoond.",
    "No clubs match these filters.": "Geen clubs voldoen aan deze filters.",
    "Last checked": "Laatst gecontroleerd",
    "Availability can change; confirm the slot on the club's booking page.": (
        "Beschikbaarheid kan veranderen; bevestig de baan op de boekingspagina "
        "van de club."
    ),
    "Stand-alone courts": "Vrij toegankelijke tennisbanen",
    "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": (
        "Openbare tennisclubs met beschikbaarheid, fietstijd, prijzen, baansoort, "
        "boekingspagina's en overige informatie"
    ),
    "Types of court available for the selected time, including outdoor, indoor, or covered.": (
        "Baansoorten die op het gekozen tijdstip beschikbaar zijn, zoals buiten, "
        "binnen of overdekt."
    ),
    "Open booking page": "Open boekingspagina",
    "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": (
        "Tennisclubs met lidmaatschap, prijzen, fietstijden, introducébeleid, "
        "wachtlijsten en clubwebsites"
    ),
    "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": (
        "Geschat aantal leden per tennisbaan. Groen ≤75, geel 76–150, rood >150; "
        "bij bereiken wordt de laagste waarde gebruikt. Sorteer numeriek via "
        "Tabel sorteren op."
    ),
    "Use the Sort table by control for numeric sorting; ranges use their lower value.": (
        "Gebruik Tabel sorteren op om numeriek te sorteren; bij bereiken wordt "
        "de laagste waarde gebruikt."
    ),
    "Use Sort table by for numeric sorting; price ranges use their lower amount.": (
        "Gebruik Tabel sorteren op om numeriek te sorteren; bij prijsbereiken "
        "wordt het laagste bedrag gebruikt."
    ),
    "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": (
        "Moeite met het vinden van de juiste tennisclub? Vergelijk clubs in "
        "Amsterdam voor een losse wedstrijd of een lidmaatschap. Bekijk locaties, "
        "fietstijden en prijzen, ontdek lidmaatschappen en controleer de "
        "beschikbaarheid voor je gekozen datum, tijd en speelduur."
    ),
    "🔓 Public (non-member) clubs": "🔓 Openbare clubs (niet-leden)",
    "Booking date": "Speeldatum",
    "Start time": "Starttijd",
    "Duration": "Speelduur",
    "minutes": "minuten",
    "Include sign-in-required clubs": "Clubs waarvoor inloggen nodig is meenemen",
    "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": (
        "Neem USC, Frans Otten Stadion en Amstelpark Tennisclub mee in de "
        "openbare clubtabel en beschikbaarheidscontrole."
    ),
    "Requested slot": "Gekozen tijd",
    "Amsterdam weather forecast": "Weersverwachting Amsterdam",
    "A forecast is not available for a past date.": "Er is geen weersverwachting voor een datum in het verleden.",
    "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": (
        "De weerservice geeft verwachtingen tot 16 dagen vooruit. Voor deze "
        "datum is nog geen verwachting beschikbaar."
    ),
    "Could not load the Amsterdam weather forecast:": "De weersverwachting voor Amsterdam kon niet worden geladen:",
    "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": (
        "Er is geen weersverwachting voor dit tijdstip. Open-Meteo geeft "
        "verwachtingen tot 16 dagen vooruit; de terugvalservices minder ver."
    ),
    "A forecast is not available for that hour yet. Choose a future time or check again later.": (
        "Voor dit uur is nog geen weersverwachting beschikbaar. Kies een later "
        "tijdstip of probeer het later opnieuw."
    ),
    "Temperature": "Temperatuur",
    "Precipitation chance": "Kans op neerslag",
    "Wind": "Wind",
    "Expected rainfall": "Verwachte neerslag",
    "Expected rainfall ({interval_hours}-hour period)": "Verwachte neerslag ({interval_hours}-uursperiode)",
    "Forecast rainfall for the selected hour or forecast period.": "Verwachte neerslag voor het gekozen uur of de voorspellingsperiode.",
    "Indoor": "Binnen",
    "Outdoor": "Buiten",
    "Indoor is preferable for": "Binnen spelen is aan te raden vanwege",
    "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": (
        "Buiten spelen lijkt goed mogelijk; als het verschil niet duidelijk is, "
        "zijn buitenbanen meestal goedkoper."
    ),
    "Recommended court:": "Aanbevolen baan:",
    "Could not verify - ": "Niet te verifiëren - ",
    "Could not verify - Meet & Play rate limited": "Niet te verifiëren - Meet & Play heeft de aanvraag beperkt",
    "Could not verify - Meet & Play returned HTTP 403": "Niet te verifiëren - Meet & Play gaf HTTP 403 terug",
    "Could not verify - requested date was not applied": "Niet te verifiëren - de gekozen datum is niet toegepast",
    "Could not verify - calendar date control did not load": "Niet te verifiëren - de kalenderdatum kon niet worden geladen",
    "Available - selectable on the booking page": "Beschikbaar - te selecteren op de boekingspagina",
    "✅ Available": "✅ Beschikbaar",
    "Not checked for this slot": "Niet gecontroleerd voor dit tijdstip",
    "Members-only portal": "Portaal alleen voor leden",
    "Only through phone": "Alleen telefonisch",
    "Not configured - automated check unavailable": "Niet ingesteld - automatische controle niet beschikbaar",
    "Could not verify - Bookaball cloud browser verification blocked": "Niet te verifiëren - browsercontrole van Bookaball wordt geblokkeerd",
    "Public (non-members)": "Openbaar (ook voor niet-leden)",
    "Public seasonally; members can invite guests": "Seizoensgebonden openbaar; leden kunnen gasten uitnodigen",
    "Members only": "Alleen leden",
    "🔒Member only": "🔒Alleen leden",
    "🔒Member+🔓Non-Member": "🔒Leden + 🔓niet-leden",
    "Not specified": "Niet opgegeven",
    "Not listed": "Niet vermeld",
    "Not published": "Niet gepubliceerd",
    "Not applicable": "Niet van toepassing",
    "Not calculated": "Niet berekend",
    "Type not reported": "Baantype niet vermeld",
    "Court type unknown": "Baantype onbekend",
    "☀️ Outdoor": "☀️ Buiten",
    "🏠 Indoor": "🏠 Binnen",
    "⛱️ Covered": "⛱️ Overdekt",
    "Club": "Club",
    "Neighbourhood": "Wijk",
    "Cycling time": "Fietstijd",
    "Availability": "Beschikbaarheid",
    "Available type": "Beschikbaar baantype",
    "Booking access": "Toegang",
    "Price / court / hour (€)": "Prijs / baan / uur (€)",
    "Court surface": "Baansoort",
    "Booking page": "Boekingspagina",
    "Other info": "Overige informatie",
    "Membership price": "Lidmaatschapsprijs",
    "Senior membership price": "Seniorenlidmaatschap",
    "Introducé allowed?": "Introducé toegestaan?",
    "Introducé price": "Prijs introducé",
    "Waiting list": "Wachtlijst",
    "Club site": "Clubwebsite",
    "Members (approx.)": "Leden (schatting)",
    "Courts": "Banen",
    "Ratio (members/court)": "Leden per baan",
    "Address": "Adres",
    "Check availability": "Controleer beschikbaarheid",
    "Calculate cycling times": "Bereken fietstijden",
    "Court surface info": "Informatie over baansoorten",
    "Update credentials": "Inloggegevens wijzigen",
    "Forget saved credentials": "Opgeslagen inloggegevens wissen",
    "Forget street address": "Startadres wissen",
    "Checking all public (non-member) clubs...": "Beschikbaarheid van openbare clubs controleren...",
    "Calculating public-club cycling times...": "Fietstijden voor openbare clubs berekenen...",
    "Calculating cycling times for both tables...": "Fietstijden voor beide tabellen berekenen...",
    "Calculating cycling times for single courts...": "Fietstijden voor losse banen berekenen...",
    "Cycling-time calculation failed": "Berekenen van fietstijden mislukt",
    "Booking-portal credentials are available for this app session.": "Inloggegevens voor de boekingsportalen zijn beschikbaar in deze appsessie.",
    "How availability is checked": "Hoe de beschikbaarheid wordt gecontroleerd",
    "Membership options": "Lidmaatschapsopties",
    "🔒 Membership options": "🔒 Lidmaatschapsopties",
    "Looking for a longer-term commitment? Explore these club senior membership options below.": (
        "Zoek je een lidmaatschap voor langere tijd? Bekijk hieronder de "
        "seniorenlidmaatschappen."
    ),
    "Sort table by": "Tabel sorteren op",
    "Sort order": "Sorteervolgorde",
    "Ranges use their lower value, and entries without a number are placed last.": (
        "Bij bereiken wordt de laagste waarde gebruikt; vermeldingen zonder "
        "getal komen onderaan."
    ),
    "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": (
        "Rijachtergrond: groen = geen wachtlijst; rood = wel een wachtlijst. "
        "Seniorenlidmaatschap: groen ≤ €200, oranje €201–€275, rood > €275. "
        "Fietstijden behouden hun kleurcodering."
    ),
    "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": (
        "Leden per baan: groen ≤75, geel 76–150, rood >150. Ledenaantallen en "
        "baanaantallen zijn bij benadering waar dit staat vermeld. De KNLTB "
        "hanteert 60–90 leden per verlichte buitenbaan als richtlijn."
    ),
    "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": (
        "Spontaan spelen? Probeer een van de vrij toegankelijke tennisbanen in "
        "Amsterdam. Deze banen kunnen niet vooraf worden gereserveerd."
    ),
    "Filter clubs": "Clubs filteren",
    "Neighbourhoods": "Wijken",
    "Court surfaces": "Baansoorten",
    "Available": "Beschikbaar",
    "Calculate cycling times to enable the cycling-time filter.": "Bereken eerst fietstijden om op fietstijd te kunnen filteren.",
    "Choose a club": "Kies een club",
    "Official club website": "Officiële clubwebsite",
    "No booking page listed": "Geen boekingspagina vermeld",
    "Selected slot": "Gekozen tijd",
    "Privacy and data use": "Privacy en gegevensgebruik",
    "Data & sources": "Gegevens en bronnen",
    "Filter by neighborhood, access type, court surface, availability, and calculated cycling time.": (
        "Filter op wijk, toegang, baansoort, beschikbaarheid en berekende fietstijd."
    ),
    "Privacy notice": "Privacyverklaring",
    "This summary describes how the app currently handles data.": "Deze samenvatting beschrijft hoe de app momenteel met gegevens omgaat.",
    "Club names and source-provided notes are shown in their original wording.": "Clubnamen en bronvermeldingen worden in de oorspronkelijke bewoording getoond.",
    "Open club site": "Open clubwebsite",
    "Not reported": "Niet vermeld",
    "Surface type not specified": "Baansoort niet opgegeven",
    "Clay": "Gravel",
    "Hard court": "Hardcourt",
    "Synthetic grass": "Kunstgras",
    "Cushioned hard court": "Gecushioneerde hardcourt",
    "Indoor synthetic tennis floor": "Indoor synthetische tennisvloer",
    "Unspecified all-weather": "Onbekende all-weatherbaan",
    "Yes": "Ja",
    "No": "Nee",
    "I agree to send my starting address and club addresses to Google Routes.": (
        "Ik geef toestemming om mijn startadres en de clubadressen naar Google "
        "Routes te sturen."
    ),
    "Starting address": "Startadres",
}


def translate_text(value: Any, language: str) -> Any:
    if language not in {"nl", "Nederlands"} or not isinstance(value, str):
        return value
    translated = DUTCH_TRANSLATIONS.get(value)
    if translated is not None:
        return translated
    if value.startswith("Could not verify - "):
        return "Niet te verifiëren - " + value.removeprefix("Could not verify - ")
    if value.startswith("Not checked"):
        return "Niet gecontroleerd" + value.removeprefix("Not checked")
    if value.startswith("✅ Available"):
        return "✅ Beschikbaar" + value.removeprefix("✅ Available")
    return value


def translate_to_english(value: Any, language: str) -> Any:
    if language not in {"nl", "Nederlands"} or not isinstance(value, str):
        return value
    for dutch, english in (
        ("Niet te verifiëren - ", "Could not verify - "),
        ("Niet gecontroleerd", "Not checked"),
        ("✅ Beschikbaar", "✅ Available"),
        ("☀️ Buiten", "☀️ Outdoor"),
        ("🏠 Binnen", "🏠 Indoor"),
        ("⛱️ Overdekt", "⛱️ Covered"),
    ):
        if value.startswith(dutch):
            return english + value.removeprefix(dutch)
    reverse = {translated: source for source, translated in DUTCH_TRANSLATIONS.items()}
    return reverse.get(value, value)


def localize_frame(frame: Any, language: str) -> Any:
    if language not in {"nl", "Nederlands"}:
        return frame
    localized = frame.copy()
    localized.columns = [
        translate_text(column, language) for column in localized.columns
    ]
    for column in localized.columns:
        localized[column] = localized[column].map(
            lambda value: translate_text(value, language)
        )
    return localized


def availability_category(value: str) -> str:
    normalized = str(value).strip().casefold()
    if normalized.startswith("could not verify"):
        return "Could not verify"
    if normalized.startswith("✅ available") or normalized.startswith("available"):
        return "Available"
    if normalized.startswith("unavailable"):
        return "Unavailable"
    if normalized.startswith("too early"):
        return "Too early to check"
    if normalized.startswith("not checked"):
        return "Not checked"
    return "Other status"


def filter_club_rows(
    rows: list[dict[str, Any]],
    *,
    neighborhoods: set[str],
    booking_access: set[str],
    court_surfaces: set[str],
    surface_categories_by_club: dict[str, set[str]],
    availability: str,
    max_cycling_minutes: int | None,
) -> list[dict[str, Any]]:
    filtered = []
    for row in rows:
        if neighborhoods and row.get("Neighbourhood") not in neighborhoods:
            continue
        if booking_access and row.get("Booking access") not in booking_access:
            continue
        if court_surfaces and not (
            surface_categories_by_club.get(str(row.get("Club", "")), set())
            & court_surfaces
        ):
            continue
        if availability != "All availability" and availability_category(
            str(row.get("Availability", ""))
        ) != availability:
            continue
        if max_cycling_minutes is not None:
            match = re.match(r"\s*(\d+)\s+min\b", str(row.get("Cycling time", "")))
            if match is None or int(match.group(1)) > max_cycling_minutes:
                continue
        filtered.append(row)
    return filtered


def privacy_statement(language: str) -> str:
    if language in {"nl", "Nederlands"}:
        return """
**Verantwoordelijke:** Casper Witlox / Amsterdam Court Finder<br>
**Privacyvragen:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### Welke gegevens de app gebruikt
- **Startadres en fietsroutes:** het startadres en de adressen van de gekozen clubs worden alleen naar Google Routes gestuurd nadat je toestemming geeft en fietstijden laat berekenen. Het adres en de route-uitkomsten blijven in de huidige appsessie; het startadres kan ook vooraf door de beheerder zijn ingesteld.
- **Inloggegevens voor boekingsportalen:** deze worden via de app naar de server gestuurd, in het geheugen van de huidige Streamlit-sessie bewaard zodat je meerdere controles kunt doen, en naar het betreffende boekingsportaal gestuurd wanneer je een controle start. De app schrijft ze niet naar het clubgegevensbestand. Gebruik **Inloggegevens wissen** om ze eerder uit de sessie te verwijderen; ze verdwijnen ook wanneer de sessie eindigt of de app opnieuw start. De boekingsportalen verwerken ze volgens hun eigen beleid.
- **Beschikbaarheidscontrole:** de gekozen datum, tijd en speelduur en de openbare boekingspagina's worden opgevraagd bij Meet & Play en andere betreffende boekingsdiensten. De app plaatst geen reserveringen.
- **Weer:** weergegevens worden opgevraagd voor de vaste locatie Amsterdam. Je startadres wordt niet met weerproviders gedeeld; de geselecteerde datum en tijd worden lokaal met de prognose vergeleken. Bronnen: [Open-Meteo](https://open-meteo.com/), [MET Norway](https://api.met.no/) en, indien geconfigureerd, [WeatherAPI.com](https://www.weatherapi.com/).
- **Clubgegevens:** clubinformatie wordt lokaal door de app beheerd en kan worden gecontroleerd via de gelinkte websites en boekingspagina's. De informatie kan verouderd zijn.

### Opslag en externe diensten
De app bewaart het startadres, route-uitkomsten en boekingsinloggegevens in de actieve appsessie; deze gegevens worden niet toegevoegd aan het clubgegevensbestand. De appbeheerder kan een standaard startadres instellen via serverconfiguratie. De app draait op [Render](https://render.com/privacy); Render kan technische verbindings- en servergegevens verwerken voor hosting en beveiliging. [Google](https://policies.google.com/privacy), weerproviders en boekingsdiensten verwerken gegevens wanneer je hun functies gebruikt, volgens hun eigen privacybeleid.

Voor inzage, correctie, verwijdering of vragen kun je mailen naar [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl). Beschikbaarheid en prijzen zijn momentopnamen; controleer de gegevens bij de club voordat je boekt.
"""
    return """
**Controller:** Casper Witlox / Amsterdam Court Finder<br>
**Privacy contact:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### Data used by the app
- **Starting address and cycling routes:** your starting address and the selected clubs' addresses are sent to Google Routes only after you give consent and request route calculations. The address and route results stay in the current app session; the operator may also configure a default starting address.
- **Booking-portal credentials:** credentials are sent through the app to its server, held in the current Streamlit session's memory so you can run more than one check, and forwarded to the relevant booking portal when you start a check. The app does not write them to the club-data file. Use **Forget saved credentials** to remove them sooner; they are also cleared when the session ends or the app restarts. Booking portals process them under their own privacy policies.
- **Availability checks:** the selected date, time, duration, and public booking pages are requested from Meet & Play and other relevant booking services. The app does not make reservations.
- **Weather:** weather data is requested for Amsterdam's fixed forecast location. Your starting address is not shared with weather providers; the selected date and time are matched to the forecast locally. Sources include [Open-Meteo](https://open-meteo.com/), [MET Norway](https://api.met.no/), and, if configured, [WeatherAPI.com](https://www.weatherapi.com/).
- **Club information:** club details are maintained in the app's local data file and can be checked against the linked club and booking websites. Details may become outdated.

### Storage and third-party services
The starting address, route results, and booking credentials are kept in the active app session; they are not added to the club-data file. The operator may configure a default starting address through server settings. The app is hosted by [Render](https://render.com/privacy), which may process technical connection and server information for hosting and security. [Google](https://policies.google.com/privacy), weather providers, and booking services process data when you use their features, under their own privacy policies.

For access, correction, deletion, or other privacy requests, email [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl). Availability and prices are snapshots; confirm details with the club before booking.
"""
