#!/usr/bin/env python3
"""Local Amsterdam tennis-club comparison dashboard."""

from __future__ import annotations

import base64
import json
import math
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st


ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
ROUTE_FIELD_MASK = "routes.duration"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AMSTERDAM_TIMEZONE = ZoneInfo("Europe/Amsterdam")
CLUB_NAMES = (
    "A.L.T.C. De Aemstelburgh",
    "Tennisvereniging A.M.V.J.",
    "Amstelpark Tennisclub",
    "Amsterdamse Tennis Club Kadoelen",
    "TOB Tennisvereniging",
    "TV Osdorp",
    "Tennisclub IJburg",
    "A.T.C. Sloterplas",
    "TV Tie-Breakers",
    "Tennisclub A.T.V.D.",
    "USC Tennis",
    "Frans Otten Stadion",
    "Tennisclub Gaasperpark",
    "Tennispark Blauw-Wit",
    "Tennis club Elzenhagen",
    "Tennisvereniging Rivierenbuurt (TVR)",
    "Tennisvereniging PST",
    "De Meer tennis",
    "Tennisclub Kattenlaan",
    "TV Linnaeushof",
    "Amsterdam Racket Club",
    "Tennispark Randwijck",
    "SV Club Triaz",
    "VVGA Tennis Club",
    "Joy Jaagpad tennis",
    "De Algemene",
    "T.C. Ijsbaanpad",
    "T.C. Amsterdam",
    "Tennis in West",
    "Tennisvereniging Amsterdamse Bos",
    "Tennis- en padelvereniging Badhoevedorp",
    "TV Geuzenveld",
    "Tennisvereniging Diemen-Zuid (TVDZ)",
    "PARK Tennis",
    "Tennisvereniging Lucky Strike",
    "Tennisvereniging Ouderkerk",
    "LTC Startbaan",
)
SINGLE_NOT_FOR_RENT_COURTS = (
    {
        "name": "Tennisbaan Mijehof",
        "neighborhood": "Gaasperdam",
        "address": "Mijehof 53, 1106 HB Amsterdam",
        "court_surface": "Hardcourt / Asphalt",
    },
    {
        "name": "Tennisbaan Kraaiennest",
        "neighborhood": "Kraaiennest (Bijlmer-Oost)",
        "address": "Kraaiennest, 1104 EA Amsterdam",
        "court_surface": "Concrete / Hardcourt (under metro station)",
    },
    {
        "name": "Tennisbaan Kartinistraat",
        "neighborhood": "Ganzenhoef (Bijlmer-Oost)",
        "address": "Raden Adjeng Kartinistraat 41, 1103 MV Amsterdam",
        "court_surface": "Hardcourt / Asphalt",
    },
    {
        "name": "Tennisbaan Raphael Lemkinstraat",
        "neighborhood": "Bijlmer-Centrum",
        "address": "Raphael Lemkinstraat 61, 1102 JW Amsterdam",
        "court_surface": "Hardcourt / Asphalt",
    },
    {
        "name": "Openbare tennisbaan Mercator",
        "neighborhood": "Mercatorbuurt (De Baarsjes)",
        "address": "1056 NW Amsterdam",
        "court_surface": "Hardcourt / Asphalt (in park/playground)",
    },
    {
        "name": "Tennisbaan Gerbrandypark",
        "neighborhood": "Geuzenveld-Slotermeer",
        "address": "1063 TW Amsterdam",
        "court_surface": "Asphalt (part of Krajicek Playground)",
    },
    {
        "name": "Tennisbaan Westerpark",
        "neighborhood": "Westerpark",
        "address": "Westerpark 5, 1014 BX Amsterdam",
        "court_surface": "Hardcourt / Asphalt",
    },
    {
        "name": "Tenniscourt Van der Madeweg",
        "neighborhood": "Diemen-Zuid",
        "address": "Lepelaarpad, 1112 LC Diemen",
        "court_surface": "Hardcourt / Asphalt",
    },
    {
        "name": "Tennisbaan Oosterpark",
        "neighborhood": "Oosterparkbuurt",
        "address": "Oosterparkbuurt, 1092 AD Amsterdam",
        "court_surface": "Asphalt",
    },
    {
        "name": "Tennisveld Winterdijkstraat",
        "neighborhood": "Rivierenbuurt",
        "address": "1079 GT Amsterdam",
        "court_surface": "Hardcourt / Asphalt",
    },
    {
        "name": "Tennisbaan Rietlandpark",
        "neighborhood": "Oostelijk Havengebied",
        "address": "Rietlanden, 1019 EW Amsterdam",
        "court_surface": "Concrete / Hardcourt (stone court)",
    },
    {
        "name": "Tennisbaan Ostwaldstraat",
        "neighborhood": "Watergraafsmeer",
        "address": "Ostwaldstraat 20, 1097 JA Amsterdam",
        "court_surface": "Hardcourt / Asphalt",
    },
)
CLUB_DETAILS = (
    {
        "name": CLUB_NAMES[0],
        "neighborhood": "Amstelveen",
        "club_website": "https://aemstelburgh.nl",
        "booking_url": "https://meetandplay.nl/club/00414",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "€20.00 - €25.00",
        "court_type": "Clay (Gravel)",
        "access_notes": "Public guest booking",
    },
    {
        "name": CLUB_NAMES[1],
        "neighborhood": "Amsterdamse Bos / Amstelveen",
        "club_website": "https://amvjtennis.nl",
        "booking_url": "https://amvjtennis.nl",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Included in membership",
        "court_type": "Clay & All-Weather",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[2],
        "neighborhood": "Buitenveldert (Amsterdam-Zuid)",
        "club_website": "https://amstelpark.nl",
        "booking_url": "https://amstelpark.baanreserveren.nl/",
        "booking_platform": "Custom Portal",
        "price_info": "€22.00 - €32.00",
        "court_type": "Clay & Hardcourt",
        "access_notes": "Public guest booking",
    },
    {
        "name": CLUB_NAMES[3],
        "neighborhood": "Amsterdam-Noord",
        "club_website": "https://atckadoelen.nl",
        "booking_url": "https://atckadoelen.nl",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Included in membership",
        "court_type": "SmashCourt & Clay",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[4],
        "neighborhood": "Amsterdam-Noord",
        "club_website": "https://tobtennis.nl",
        "booking_url": "https://tobtennis.nl",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Included in membership",
        "court_type": "Hardcourt & Smashcourt",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[5],
        "neighborhood": "Amsterdam Nieuw-West",
        "club_website": "https://tvosdorp.nl",
        "booking_url": "https://tvosdorp.nl",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Included in membership",
        "court_type": "Clay (Gravel)",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[6],
        "address": "Zandzeggestraat 1, 1087 SL Amsterdam",
        "neighborhood": "Amsterdam-Oost (IJburg)",
        "club_website": "https://www.tennisclubijburg.nl/",
        "booking_url": "https://www.tennisclubijburg.nl/",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Included in membership",
        "court_type": "SmashCourt",
        "access_notes": "Members only",
        "other_notes": (
            "Members can add a paid introducé during off-peak hours; the fee is "
            "shown in the club app."
        ),
    },
    {
        "name": CLUB_NAMES[7],
        "neighborhood": "Amsterdam Nieuw-West",
        "club_website": "https://tcsloterplas.nl",
        "booking_url": "",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Included in membership",
        "court_type": "SmashCourt",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[8],
        "neighborhood": "Amsterdam-Oost (Flevopark)",
        "club_website": "https://tiebreakers.nl",
        "booking_url": "https://meetandplay.nl/club/02477",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "€20.00",
        "court_type": "SmashCourt",
        "access_notes": "Public guest booking",
    },
    {
        "name": CLUB_NAMES[9],
        "address": "Tennisclub A.T.V.D., Diemen, Netherlands",
        "neighborhood": "Diemen",
        "club_website": "",
        "booking_url": "https://meetandplay.nl/club/02600",
        "booking_platform": "KNLTB Meet & Play / KNLTB ClubApp",
        "price_info": "€25.00",
        "court_type": "Gravel",
        "access_notes": (
            "Public guest booking via Meet & Play during spring and summer; "
            "ATVD members can invite guests year-round via the ClubApp"
        ),
        "other_notes": (
            "Casual Meet & Play court rental is unavailable in autumn and winter "
            "while the clubhouse is closed."
        ),
    },
    {
        "name": CLUB_NAMES[10],
        "neighborhood": "Amsterdam-Oost (Watergraafsmeer)",
        "club_website": "https://uscsport.nl",
        "booking_url": "https://my.uscsport.nl/bookings/rent?tags=228",
        "booking_platform": "Custom Portal",
        "price_info": "€18.00 - €26.00",
        "court_type": "Artificial Grass & Hardcourt",
        "access_notes": "Public guest booking",
        "other_notes": (
            "Only 60-minute slots are offered. Availability is shown for the "
            "coming four days, including today."
        ),
    },
    {
        "name": CLUB_NAMES[11],
        "neighborhood": "Amsterdam-Zuid",
        "club_website": "https://fransottenstadion.nl/",
        "booking_url": "https://fransotten.baanreserveren.nl/",
        "booking_platform": "Custom Portal",
        "price_info": "€30.00 - €35.00",
        "court_type": "Indoor (Pro Tennisfloor) & Outdoor Clay",
        "access_notes": "Public guest booking",
    },
    {
        "name": CLUB_NAMES[12],
        "neighborhood": "Amsterdam-Zuidoost",
        "club_website": "http://www.gaasperpark.amsterdam/",
        "booking_url": "https://meetandplay.nl/club/02709",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "€15.00",
        "court_type": "Premium Plus Clay",
        "access_notes": "Public guest booking",
        "other_notes": (
            "Non-members can book tennis courts up to 10 days ahead. "
            "Weekday rentals are generally 09:00-18:00; weekend rentals 09:00-23:00."
        ),
    },
    {
        "name": CLUB_NAMES[13],
        "neighborhood": "Amsterdam-West",
        "club_website": "https://tennisparkblauwwit.nl",
        "booking_url": "https://blauwwit.allbooked.com/booking",
        "booking_platform": "Custom Portal",
        "price_info": "€20.00 - €25.00",
        "court_type": "Artificial Grass",
        "access_notes": "Public guest booking",
    },
    {
        "name": CLUB_NAMES[14],
        "address": "Nieuwendammerkade 15, Amsterdam",
        "neighborhood": "Amsterdam-Noord",
        "club_website": "",
        "booking_url": "https://meetandplay.nl/club/01347",
        "booking_platform": "",
        "price_info": "€27.50",
        "court_type": "SmashCourt",
        "access_notes": "Public guest booking",
    },
    {
        "name": CLUB_NAMES[15],
        "neighborhood": "Rivierenbuurt",
        "club_website": "https://www.tvramsterdam.nl/baan_reserveren",
        "booking_url": "https://meetandplay.nl/club/01762",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "€20.00",
        "court_type": "Kushion court",
        "access_notes": "Public guest booking",
        "other_notes": (
            "The club website says members can reserve up to 72 hours ahead "
            "through the ClubApp or website; these reservations are members-only. "
            "Non-members book through Meet & Play, which lists a 24-hour "
            "advance window."
        ),
    },
    {
        "name": CLUB_NAMES[16],
        "address": "Plantage Parklaan 20A, 1018 ST Amsterdam",
        "neighborhood": "Plantage",
        "club_website": "https://www.tennisclubpst.nl/",
        "booking_url": "",
        "booking_platform": "Not specified",
        "price_info": "Not listed",
        "court_type": "Artificial grass",
        "access_notes": "Members only",
        "other_notes": "Also known as Plantage Speelt Tennis.",
    },
    {
        "name": CLUB_NAMES[17],
        "address": "Drieburgpad 8, 1097 HK Amsterdam",
        "neighborhood": "Watergraafsmeer (Sportpark Drieburg)",
        "club_website": "https://www.demeertennis.nl/",
        "booking_url": "",
        "booking_platform": "Club reservation facility",
        "price_info": "Not listed",
        "court_type": "Gravel",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[18],
        "address": "Kattenlaan 13, 1054 KA Amsterdam",
        "neighborhood": "Vondelpark",
        "club_website": "https://www.tennisclubkattenlaan.nl/",
        "booking_url": "",
        "booking_platform": "Club app",
        "price_info": "Not listed",
        "court_type": "Smash Court (all-weather)",
        "access_notes": "Members only",
        "other_notes": (
            "Summer tennis club; listed season is 1 April to 14 October. "
            "Winter tennis is a separate club."
        ),
    },
    {
        "name": CLUB_NAMES[19],
        "address": "Linnaeushof 46, 1098 KM Amsterdam",
        "neighborhood": "Amsterdam-Oost",
        "club_website": "https://www.tvlinnaeushof.nl/",
        "booking_url": "",
        "booking_platform": "Club booking",
        "price_info": "Not listed",
        "court_type": "Hardcourt",
        "access_notes": "Members only",
        "other_notes": (
            "Bookings are available up to 72 hours before the slot. The club "
            "reports a membership waiting list."
        ),
    },
    {
        "name": CLUB_NAMES[20],
        "address": "Van der Boechorststraat 38, 1081 BT Amsterdam",
        "neighborhood": "Buitenveldert (Amsterdam-Zuid)",
        "club_website": "https://amsterdamracketclub.nl/",
        "booking_url": "https://rscbuitenveldert.bookaball.com/nl/bookings/create",
        "booking_platform": "Bookaball",
        "price_info": "€25.00",
        "court_type": "Outdoor gravel; indoor (surface not specified)",
        "access_notes": "Public guest booking",
        "other_notes": "Credentials are required to book through the club's own portal.",
    },
    {
        "name": CLUB_NAMES[21],
        "address": "Barend van Dorenweerdelaan 18, 1181 BK Amstelveen",
        "neighborhood": "Amstelveen (Randwijck)",
        "club_website": "https://www.higginstennis.nl/tennispark-randwijck",
        "booking_url": "https://www.higginstennis.nl/randwijck-court-reservation",
        "booking_platform": "Email account request",
        "price_info": "€30.00",
        "court_type": "Clay",
        "access_notes": "Public booking after account creation",
        "other_notes": (
            "Email play@higginstennis.nl to create an account. Closed for the "
            "winter season."
        ),
    },
    {
        "name": CLUB_NAMES[22],
        "address": "Sportpark Van Heenvlietlaan, Van Heenvlietlaan 6, 1083 CL Amsterdam",
        "neighborhood": "Amsterdam-Zuid",
        "club_website": "https://www.higginstennis.nl/club-sv-triaz",
        "booking_url": "https://www.supersaas.com/schedule/randwijck/Club_Triaz",
        "booking_platform": "SuperSaaS",
        "price_info": "Not listed",
        "court_type": "Artificial Grass (Edel Agile)",
        "access_notes": "Members only",
        "other_notes": "Membership costs €126; the membership period was not specified.",
    },
    {
        "name": CLUB_NAMES[23],
        "address": "Wembleylaan 5, 1098 WG Amsterdam",
        "neighborhood": "Watergraafsmeer",
        "club_website": "https://www.vvga.nl/",
        "booking_url": "",
        "booking_platform": "Not specified",
        "price_info": "Not listed",
        "court_type": "Gravel",
        "access_notes": "Members only",
        "other_notes": "Courts cannot be played on in rainy weather.",
    },
    {
        "name": CLUB_NAMES[24],
        "address": "Jaagpad 48, 1059 BP Amsterdam",
        "neighborhood": "Amsterdam-Zuid (Jaagpad)",
        "club_website": "https://www.joyjaagpad.nl/",
        "booking_url": "",
        "booking_platform": "Club app",
        "price_info": "Not listed",
        "court_type": "Gravel",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[25],
        "address": "IJsbaanpad 45, 1076 CV Amsterdam",
        "neighborhood": "Amsterdam-Zuid (IJsbaanpad)",
        "club_website": "https://dealgemene.nl/",
        "booking_url": "",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Not listed",
        "court_type": "Claytech",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[26],
        "address": "IJsbaanpad 45, 1076 CV Amsterdam",
        "neighborhood": "Amsterdam-Zuid (Ijsbaanpad)",
        "club_website": "https://www.ijsbaanpad.nl/",
        "booking_url": "",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Not listed",
        "court_type": "Outdoor Claytech (all-weather)",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[27],
        "address": "Nieuwe Kalfjeslaan 19a, 1182 AA Amstelveen",
        "neighborhood": "Amstelveen (Amsterdamse Bos edge)",
        "club_website": "https://www.tcamsterdam.net/",
        "booking_url": "",
        "booking_platform": "Not specified",
        "price_info": "Not listed",
        "court_type": "Gravel",
        "access_notes": "Members only",
        "other_notes": "Tennis Club Amsterdam (TCA), in Amstelveen; not at IJsbaanpad.",
    },
    {
        "name": CLUB_NAMES[28],
        "address": "De Roos van Dekamaweg 1, 1061 HR Amsterdam",
        "neighborhood": "Amsterdam-West (Sportpark Multatuli)",
        "club_website": "https://tennisinwest.nl",
        "booking_url": "",
        "booking_platform": "Not specified",
        "price_info": "Not listed",
        "court_type": "LED-lit gravel",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[29],
        "address": "Jan Tooroplaan 48, 1182 AE Amstelveen",
        "neighborhood": "Amsterdamse Bos",
        "club_website": "https://www.tvamsterdamsebos.nl",
        "booking_url": "https://meetandplay.nl/club/00455",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "Not listed",
        "court_type": "Gravel",
        "price_info": "€35.00",
        "access_notes": "Public guest booking",
    },
    {
        "name": CLUB_NAMES[30],
        "address": "Snelliuslaan 41, 1171 CZ Badhoevedorp",
        "neighborhood": "Badhoevedorp",
        "club_website": "https://www.tvbadhoevedorp.nl/",
        "booking_url": "",
        "booking_platform": "Not specified",
        "price_info": "Not listed",
        "court_type": "Gravel; prestige gravel",
        "access_notes": "Members only",
    },
    {
        "name": CLUB_NAMES[31],
        "address": "Tom Schreursweg 12, 1067 MC Amsterdam",
        "neighborhood": "Amsterdam Nieuw-West (Sportpark De Eendracht)",
        "club_website": "https://www.tvgeuzenveld.nl",
        "booking_url": "https://meetandplay.nl/club/02295",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "€19.00",
        "court_type": "All-weather",
        "access_notes": "Public guest booking",
        "other_notes": "Limited times are open for casual rental through Meet & Play.",
    },
    {
        "name": CLUB_NAMES[32],
        "address": "Sportlaan 7, 1111 PX Diemen",
        "neighborhood": "Diemen-Zuid",
        "club_website": "https://www.facebook.com/DiemenTVDZ/",
        "booking_url": "",
        "booking_platform": "Phone booking",
        "price_info": "€20.00",
        "court_type": "Outdoor artificial grass",
        "access_notes": "Public (non-members)",
        "other_notes": (
            "Availability checks and bookings are by phone only: 020 - 6001857."
        ),
    },
    {
        "name": CLUB_NAMES[33],
        "address": "Bankrasweg 12A, 1183 TP Amstelveen",
        "neighborhood": "Amstelveen",
        "club_website": "https://www.parktennis.nl/",
        "booking_url": "https://www.supersaas.nl/schedule/PARK/Niet_Leden",
        "booking_platform": "Court Flexibel / SuperSaaS",
        "price_info": "€32.50",
        "court_type": "Gravel",
        "access_notes": "Public (non-members)",
        "other_notes": (
            "Purchased points are used to pay when reserving and are valid for "
            "one season."
        ),
    },
    {
        "name": CLUB_NAMES[34],
        "address": "Populierenlaan 42, 1161 SP Zwanenburg",
        "neighborhood": "Zwanenburg",
        "club_website": "https://www.tvluckystrike.nl/",
        "booking_url": "https://www.tvluckystrike.nl/",
        "booking_platform": "Not specified",
        "price_info": "Not listed",
        "court_type": "Lit gravel",
        "access_notes": "Members only",
        "other_notes": "Closed for the winter season; reopens in April.",
    },
    {
        "name": CLUB_NAMES[35],
        "address": "Holendrechterweg 34, 1191 KV Ouderkerk aan de Amstel",
        "neighborhood": "Ouderkerk aan de Amstel",
        "club_website": "https://www.tcotennis.nl",
        "booking_url": "",
        "booking_platform": "Members' court booking",
        "price_info": "Included in membership",
        "court_type": "Gravel",
        "access_notes": "Members only",
        "other_notes": (
            "The club website says courts are for members and are not rented. "
            "The supplied Meet & Play link (73155) is for T.C. Ouderkerk aan den "
            "IJssel, not this club."
        ),
    },
    {
        "name": CLUB_NAMES[36],
        "address": "Startbaan 2, 1185 XR Amstelveen",
        "neighborhood": "Amstelveen (Startbaan)",
        "club_website": "https://www.ltcstartbaan.nl/",
        "booking_url": "https://meetandplay.nl/club/00224",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "€15.00",
        "court_type": "Gravel (outdoor) & Hardcourt (indoor)",
        "access_notes": "Public guest booking",
        "other_notes": "Price varies per slot.",
    },
)
EDITABLE_FIELDS = (
    "name",
    "address",
    "neighborhood",
    "club_website",
    "booking_url",
    "booking_platform",
    "price_info",
    "membership_price",
    "court_type",
    "access_notes",
    "other_notes",
)
DEFAULT_CLUB_NAME_SET = set(CLUB_NAMES)
BROWSER_CHECK_CLUBS = {
    CLUB_NAMES[0],
    CLUB_NAMES[2],
    CLUB_NAMES[9],
    CLUB_NAMES[10],
    CLUB_NAMES[11],
    CLUB_NAMES[12],
    CLUB_NAMES[13],
    CLUB_NAMES[14],
    CLUB_NAMES[15],
    CLUB_NAMES[8],
    CLUB_NAMES[29],
    CLUB_NAMES[31],
    CLUB_NAMES[36],
    CLUB_NAMES[20],
}
BAANRESERVEREN_CREDENTIAL_CHECK_CLUBS = {
    CLUB_NAMES[2],
    CLUB_NAMES[11],
}
USC_CREDENTIAL_CHECK_CLUBS = {CLUB_NAMES[10]}
CREDENTIAL_CHECK_CLUBS = (
    BAANRESERVEREN_CREDENTIAL_CHECK_CLUBS | USC_CREDENTIAL_CHECK_CLUBS
)
AUTOMATIC_CHECKER_PROTOCOL = 10
LEGACY_DEFAULT_CLUB_NAMES = {
    "TOB Tennis vereniging",
    "Tennis- en Padelvereniging Geinburgia",
    "T.V. Tie-Breakers",
    "Tennisvereniging Amsterdamse Bos",
    "A.L.T.C. D.D.V.",
}
LEGACY_NAME_ALIASES = {
    "Tennis- en Padelvereniging IJburg": "Tennisclub IJburg",
    "Tennisvereniging IJburg": "Tennisclub IJburg",
    "Tennisclub Ijburg": "Tennisclub IJburg",
    "USC Tennis & Padel": "USC Tennis",
    "Tennis & Padel Club Gaasperpark": "Tennisclub Gaasperpark",
    "TOB Tennis vereniging": "TOB Tennisvereniging",
    "T.V. Tie-Breakers": "TV Tie-Breakers",
    "Tennisclub Sloterplas": "A.T.C. Sloterplas",
    "Tennisvereniging ATVO": "Tennisclub A.T.V.D.",
    "Tennisclub ATVO": "Tennisclub A.T.V.D.",
    "Tennisvereniging ATVD": "Tennisclub A.T.V.D.",
    "Tennisclub ATVD": "Tennisclub A.T.V.D.",
}
CLUB_DATA_CORRECTIONS = {
    "A.L.T.C. De Aemstelburgh": {
        "booking_url": "https://meetandplay.nl/club/00414",
        "other_notes": (
            "Meet & Play displays the price by time block; its listed court-hire "
            "prices exclude a 1% KNLTB maintenance surcharge."
        ),
    },
    "Frans Otten Stadion": {
        "booking_url": "https://fransotten.baanreserveren.nl/",
        "price_info": (
            "€32.50–€52.50 (varies by tariff schedule and time; check booking page)"
        ),
        "other_notes": (
            "The official tennis tariff page lists one schedule at €40/hour on "
            "weekdays 07:00–16:00 and 22:00–24:00, €52.50/hour on weekdays "
            "16:00–22:00, and €47.50/hour on weekends. Separate tariff sections "
            "list €32.50/hour off-peak and €37.50/hour at weekday peak times "
            "and on weekends. The page does not clearly map each schedule to "
            "indoor versus outdoor courts; confirm the selected court and slot "
            "in the booking system."
        ),
    },
    "Amstelpark Tennisclub": {
        "booking_url": "https://amstelpark.baanreserveren.nl/",
        "booking_platform": "Custom Portal",
        "court_type": "Clay & Hardcourt",
        "other_notes": (
            "The rate varies with the booked court and slot. The club's website "
            "says same-day telephone reservations are available for half the "
            "court-hire price; check the booking portal for the rate of a specific slot."
        ),
    },
    "Tennisclub IJburg": {
        "court_type": "SmashCourt",
    },
    "TV Tie-Breakers": {
        "booking_url": "https://meetandplay.nl/club/02477",
        "booking_platform": "KNLTB Meet & Play",
        "price_info": "€20.00",
        "access_notes": "Public guest booking",
    },
    "USC Tennis": {
        "booking_url": "https://my.uscsport.nl/bookings/rent?tags=228",
        "booking_platform": "Custom Portal",
        "court_type": "Artificial Grass & Hardcourt",
        "other_notes": (
            "Only 60-minute slots are offered. Availability is shown for the "
            "coming four days, including today."
        ),
    },
    "Tennisclub Gaasperpark": {
        "booking_url": "https://meetandplay.nl/club/02709",
        "price_info": "€15.00",
        "court_type": "Premium Plus Clay",
        "other_notes": (
            "Non-members can book tennis courts up to 10 days ahead. "
            "Weekday rentals are generally 09:00-18:00; weekend rentals 09:00-23:00."
        ),
    },
    "A.T.C. Sloterplas": {
        "booking_url": "",
        "booking_platform": "KNLTB ClubApp",
        "price_info": "Included in membership",
        "access_notes": "Members only",
    },
    "Tennisclub A.T.V.D.": {
        "address": "Tennisclub A.T.V.D., Diemen, Netherlands",
        "neighborhood": "Diemen",
        "club_website": "",
        "booking_url": "https://meetandplay.nl/club/02600",
        "booking_platform": "KNLTB Meet & Play / KNLTB ClubApp",
        "price_info": "€25.00",
        "court_type": "Gravel",
        "access_notes": (
            "Public guest booking via Meet & Play during spring and summer; "
            "ATVD members can invite guests year-round via the ClubApp"
        ),
        "other_notes": (
            "Casual Meet & Play court rental is unavailable in autumn and winter "
            "while the clubhouse is closed."
        ),
    },
    "Tennisvereniging Rivierenbuurt (TVR)": {
        "other_notes": (
            "The club website says members can reserve up to 72 hours ahead "
            "through the ClubApp or website; these reservations are members-only. "
            "Non-members book through Meet & Play, which lists a 24-hour "
            "advance window."
        ),
    },
    "Tennispark Blauw-Wit": {
        "booking_url": "https://blauwwit.allbooked.com/booking",
        "booking_platform": "Custom Portal",
        "court_type": "Artificial Grass",
    },
    "Tennis club Elzenhagen": {
        "address": "Nieuwendammerkade 15, Amsterdam",
        "booking_url": "https://meetandplay.nl/club/01347",
        "price_info": "€27.50",
        "court_type": "SmashCourt",
    },
    "Tennisvereniging PST": {
        "access_notes": "Members only",
        "court_type": "Artificial grass",
    },
    "TOB Tennisvereniging": {
        "court_type": "Hardcourt & Smashcourt",
    },
    "Tennisclub Kattenlaan": {
        "court_type": "Smash Court (all-weather)",
    },
    "SV Club Triaz": {
        "court_type": "Artificial Grass (Edel Agile)",
    },
    "VVGA Tennis Club": {
        "court_type": "Gravel",
        "other_notes": "Courts cannot be played on in rainy weather.",
    },
    "De Meer tennis": {
        "court_type": "Gravel",
    },
    "TV Linnaeushof": {
        "court_type": "Hardcourt",
    },
    "Amsterdam Racket Club": {
        "court_type": "Outdoor gravel; indoor (surface not specified)",
        "other_notes": (
            "Availability can be checked up to 20 days in advance. "
            "Credentials are required to book through the club's own portal."
        ),
    },
    "Tennispark Randwijck": {
        "court_type": "Clay",
        "booking_url": "https://www.higginstennis.nl/randwijck-court-reservation",
    },
    "Joy Jaagpad tennis": {
        "court_type": "Gravel",
    },
    "De Algemene": {
        "court_type": "Claytech",
    },
    "T.C. Amsterdam": {
        "court_type": "Gravel",
    },
    "T.C. Ijsbaanpad": {
        "court_type": "Outdoor Claytech (all-weather)",
    },
    "Tennis in West": {
        "court_type": "LED-lit gravel",
    },
    "Tennisvereniging Amsterdamse Bos": {
        "price_info": "€35.00",
        "court_type": "Gravel",
    },
    "Tennis- en padelvereniging Badhoevedorp": {
        "court_type": "Gravel; prestige gravel",
    },
    "TV Geuzenveld": {
        "court_type": "All-weather",
    },
    "Tennisvereniging Diemen-Zuid (TVDZ)": {
        "price_info": "€20.00",
        "court_type": "Outdoor artificial grass",
        "booking_url": "",
    },
    "PARK Tennis": {
        "price_info": "€32.50",
        "court_type": "Gravel",
        "other_notes": (
            "Purchased points are used to pay when reserving and are valid for "
            "one season."
        ),
    },
    "Tennisvereniging Lucky Strike": {
        "court_type": "Lit gravel",
    },
    "Tennisvereniging Ouderkerk": {
        "court_type": "Gravel",
    },
    "LTC Startbaan": {
        "court_type": "Gravel (outdoor) & Hardcourt (indoor)",
    },
}
SENIOR_MEMBERSHIP_PRICES = {
    "Tennisvereniging A.M.V.J.": "€257.50/year (2026), senior 18+",
    "Amsterdamse Tennis Club Kadoelen": "€185.00/year",
    "TOB Tennisvereniging": (
        "€210.00/year (2027 provisional), senior 18+"
    ),
    "TV Osdorp": "Not published",
    "Tennisclub IJburg": (
        "€295.00/year"
    ),
    "A.T.C. Sloterplas": (
        "€260.00/year (2026); €265.00/year in 2027"
    ),
    "Tennisvereniging PST": "€125.00/year",
    "De Meer tennis": "€199.00/year",
    "Tennisclub Kattenlaan": "Not published",
    "TV Linnaeushof": "€330.00/year",
    "SV Club Triaz": "€126.00/year",
    "VVGA Tennis Club": "Not published",
    "Joy Jaagpad tennis": "€256.00/year",
    "De Algemene": "€210.00/year",
    "T.C. Ijsbaanpad": "€220.00/year",
    "T.C. Amsterdam": "€227.00/year (senior from age 26)",
    "Tennis in West": "Not published",
    "Tennis- en padelvereniging Badhoevedorp": "Not published",
    "Tennisvereniging Lucky Strike": (
        "€205.00/year"
    ),
    "Tennisvereniging Ouderkerk": "€175.00–€180.00/year",
}
MEMBERSHIP_CAPACITY_INFO = {
    "TOB Tennisvereniging": {
        "members": "170",
        "courts": "5",
        "ratio": "34",
        "notes": "Includes 2 indoor and 3 outdoor courts; located in Noord.",
    },
    "Amsterdamse Tennis Club Kadoelen": {
        "members": "600",
        "courts": "12",
        "ratio": "50",
        "notes": "11 of 12 courts are lit; open year-round.",
    },
    "TV Osdorp": {
        "members": "600",
        "courts": "10",
        "ratio": "60",
        "notes": "Also features an air dome (indoor bubble) during winter.",
    },
    "Tennisvereniging A.M.V.J.": {
        "members": "500–600",
        "courts": "8",
        "ratio": "63–75",
        "notes": "Only 2 of 8 courts are playable during winter.",
    },
    "Tennisclub IJburg": {
        "members": "1,100",
        "courts": "13",
        "ratio": "85",
        "notes": "High number of league players (over 50 competitive teams).",
    },
    "De Algemene": {
        "members": "570",
        "courts": "6",
        "ratio": "95",
        "notes": "All-weather courts allow year-round outdoor play.",
    },
    "TV Linnaeushof": {
        "members": "290–300",
        "courts": "3",
        "ratio": "97–100",
        "notes": "Waiting list for regular senior members.",
    },
    "T.C. Amsterdam": {
        "members": "600",
        "courts": "6",
        "ratio": "100",
        "notes": "Membership cap at 600; park is open only April–October.",
    },
    "A.T.C. Sloterplas": {
        "members": "~1,000",
        "courts": "10",
        "ratio": "100",
        "notes": "At most 2 courts are used simultaneously for tennis lessons.",
    },
    "De Meer tennis": {
        "members": ">900",
        "courts": "8",
        "ratio": "113+",
        "notes": "Waiting list of about 2.5 years; open March–November.",
    },
    "VVGA Tennis Club": {
        "members": "800",
        "courts": "7",
        "ratio": "114",
        "notes": "Senior membership is frozen; only off-peak daytime and youth "
        "members are accepted.",
    },
    "Tennis- en padelvereniging Badhoevedorp": {
        "members": "1,510*",
        "courts": "13",
        "ratio": "116*",
        "notes": "*1,510 active playing members (1,849 total); also has 3 padel "
        "courts.",
    },
    "T.C. Ijsbaanpad": {
        "members": "700",
        "courts": "6",
        "ratio": "117",
        "notes": "All-weather courts allow year-round outdoor play.",
    },
    "Tennisvereniging Ouderkerk": {
        "members": "1,100",
        "courts": "9",
        "ratio": "122",
        "notes": "Senior waiting list; off-peak daytime membership is available "
        "immediately.",
    },
    "Joy Jaagpad tennis": {
        "members": "1,750–1,900",
        "courts": "15",
        "ratio": "117–127",
        "notes": "Waiting list; 14 of 15 courts are lit.",
    },
    "Tennisvereniging PST": {
        "members": "900",
        "courts": "5",
        "ratio": "180",
        "notes": "Shares 3 of 5 courts with other sports clubs; 2 courts are "
        "dedicated to tennis.",
    },
    "Tennisclub Kattenlaan": {
        "members": "1,000–1,100",
        "courts": "5",
        "ratio": "200–220",
        "notes": "Summer season only; courts are commercially operated during "
        "winter.",
    },
    "Tennis in West": {
        "members": "Unknown",
        "courts": "5",
        "ratio": "Unknown",
        "notes": "Newer club with a waiting list; public membership numbers are "
        "unavailable.",
    },
    "SV Club Triaz": {
        "members": "Unknown",
        "courts": "4–5",
        "ratio": "Unknown",
        "notes": "Small-scale club; shares fields in part with korfball.",
    },
    "Tennisvereniging Lucky Strike": {
        "members": "Unknown",
        "courts": "7",
        "ratio": "Unknown",
        "notes": "Located in Zwanenburg; 6 of 7 courts are lit.",
    },
}
SENIOR_MEMBERSHIP_OTHER_INFO = {
    "Tennisvereniging PST": (
        "Residency zone applies; lottery enrollment is December 1–31."
    ),
    "SV Club Triaz": "€10 refundable key deposit.",
    "Tennisvereniging Ouderkerk": (
        "Young senior (18–25) rate is €110/year; €50 signup fee."
    ),
    "Amsterdamse Tennis Club Kadoelen": (
        "Young senior (18–19) rate is €140/year; €25 signup/tag fee."
    ),
    "De Meer tennis": "Waitlist is about 2.5 years; €25 waitlist/signup fee.",
    "Tennisvereniging Lucky Strike": "No waitlist; €25 signup fee.",
    "De Algemene": "Stadspas discount available (€165 full).",
    "TOB Tennisvereniging": (
        "€15 signup fee; free for members aged 55+ with Stadspas."
    ),
    "T.C. Ijsbaanpad": (
        "Full waitlist is closed; €50 refundable bar deposit."
    ),
    "T.C. Amsterdam": (
        "Student rate is €148/year; €40 one-time entry fee."
    ),
    "Joy Jaagpad tennis": "Waitlist is about 1.5 years; €16 signup fee.",
    "Tennisvereniging A.M.V.J.": (
        "Student rate is €173.50/year; €27.50 entry fee."
    ),
    "A.T.C. Sloterplas": (
        "Waitlist is active; €20 signup fee (€25 in 2027)."
    ),
    "Tennisclub IJburg": (
        "€75 refundable bar deposit and €50 signup fee."
    ),
    "TV Linnaeushof": "Full membership is closed; daytime membership is open.",
    "Tennisclub Kattenlaan": (
        "€27.50 one-time registration fee; current senior annual fee is not "
        "publicly posted."
    ),
    "VVGA Tennis Club": (
        "Membership stop and waitlist for full senior tennis membership; "
        "daytime membership is open. Exact fees are restricted to the member portal."
    ),
    "Tennis in West": (
        "Operates five gravel courts at Sportpark Multatuli and has active "
        "registration forms; its standard annual senior tariff is not published."
    ),
    "TV Osdorp": (
        "No waitlist, registration fee, or mandatory bar duty; exact senior "
        "tariffs are shown only in the signup workflow."
    ),
    "Tennis- en padelvereniging Badhoevedorp": (
        "€35 registration fee. Seniors can only join combined tennis and padel "
        "memberships: young senior (18–25) or senior (26+); annual rates require "
        "member login."
    ),
}
INTRODUCE_ALLOWED = {
    "Tennisvereniging A.M.V.J.": "Yes",
    "Amsterdamse Tennis Club Kadoelen": "Yes (up to 6 times/year)",
    "TOB Tennisvereniging": "Yes (outdoor SmashCourt)",
    "TV Osdorp": "Yes",
    "Tennisclub IJburg": "Yes (peak-hour limits may apply)",
    "A.T.C. Sloterplas": "Yes (up to 4 times/season)",
    "Tennisvereniging PST": "Yes",
    "De Meer tennis": "Yes",
    "Tennisclub Kattenlaan": "Yes",
    "TV Linnaeushof": "Yes",
    "SV Club Triaz": "Yes",
    "VVGA Tennis Club": "Yes (peak-hour limits may apply)",
    "Joy Jaagpad tennis": "Yes (except peak hours/competition days)",
    "De Algemene": "Yes",
    "T.C. Ijsbaanpad": "Yes",
    "T.C. Amsterdam": "Yes",
    "Tennis in West": "Yes",
    "Tennis- en padelvereniging Badhoevedorp": "Yes",
    "Tennisvereniging Lucky Strike": "Yes",
    "Tennisvereniging Ouderkerk": "Yes",
}
INTRODUCE_PRICE = {
    "Tennisvereniging A.M.V.J.": "€7.50 per visit",
    "Amsterdamse Tennis Club Kadoelen": "€7.50 per visit",
    "TOB Tennisvereniging": "€5.00–€7.50/hour",
    "TV Osdorp": "€7.50 per visit",
    "Tennisclub IJburg": "€7.50 per introducé",
    "A.T.C. Sloterplas": "€10.00 per visit",
    "Tennisvereniging PST": "€10.00 per visit",
    "De Meer tennis": "€7.50 per daypart",
    "Tennisclub Kattenlaan": "About €7.50 per visit",
    "TV Linnaeushof": "About €7.50 per introducé",
    "SV Club Triaz": "About €5.00–€7.50",
    "VVGA Tennis Club": "€7.50 per introducé",
    "Joy Jaagpad tennis": "About €7.50 per visit",
    "De Algemene": "About €7.50–€10.00",
    "T.C. Ijsbaanpad": "About €7.50",
    "T.C. Amsterdam": "About €7.50",
    "Tennis in West": "€7.50–€10.00",
    "Tennis- en padelvereniging Badhoevedorp": "Usually about €7.50–€10.00",
    "Tennisvereniging Lucky Strike": "€5.00–€7.50",
    "Tennisvereniging Ouderkerk": "€7.50",
}
MEMBERSHIP_WAITLISTS = {
    "Tennisvereniging A.M.V.J.": "No",
    "Amsterdamse Tennis Club Kadoelen": (
        "Yes (seniors 17+; placements usually Jan/Feb; no junior waitlist)"
    ),
    "TOB Tennisvereniging": "No",
    "TV Osdorp": "No",
    "Tennisclub IJburg": "Yes (length unknown)",
    "A.T.C. Sloterplas": (
        "Yes (adults; reviewed at year-end; under-17s can join directly)"
    ),
    "Tennisvereniging PST": "No",
    "De Meer tennis": "Yes (2.5 years; €25 registration fee)",
    "Tennisclub Kattenlaan": "No",
    "TV Linnaeushof": "Yes (currently closed; length unknown)",
    "SV Club Triaz": "No",
    "VVGA Tennis Club": (
        "Yes (seniors and young adults; timing depends on winter resignations; "
        "day and youth memberships have no waitlist)"
    ),
    "Joy Jaagpad tennis": "Yes (1.5 years)",
    "De Algemene": "No",
    "T.C. Ijsbaanpad": "Yes (temporarily closed; length unknown)",
    "T.C. Amsterdam": "Yes (at least 1 year for seniors)",
    "Tennis in West": "No active formal waiting list reported",
    "Tennis- en padelvereniging Badhoevedorp": (
        "Yes (seniors; variable; separate local and non-local lists; youth can "
        "join directly)"
    ),
    "Tennisvereniging Lucky Strike": "No",
    "Tennisvereniging Ouderkerk": (
        "Yes (full senior membership; day membership and junior membership "
        "available without a waitlist)"
    ),
}
DUAL_ACCESS_MEMBERSHIP_DATA = {
    "A.L.T.C. De Aemstelburgh": {
        "membership_price": "€260/year; €35 one-time entrance fee",
        "waiting_list": "No (direct entry available)",
    },
    "Amstelpark Tennisclub": {
        "membership_price": "€430/year full membership; €25 registration fee",
        "waiting_list": "No (direct online signup)",
    },
    "Amsterdam Racket Club": {
        "membership_price": "€540–€630/season (off-peak/peak; not an annual fee)",
        "waiting_list": "No (seasonal pass options)",
    },
    "Frans Otten Stadion": {
        "membership_price": (
            "€315/year for ALTC DDV club membership; venue also rents courts"
        ),
        "waiting_list": "Yes (active waitlist for adults)",
    },
    "LTC Startbaan": {
        "membership_price": "€230/year for regular seniors",
        "waiting_list": "No (direct online signup)",
    },
    "PARK Tennis": {
        "membership_price": "€198/year for Classic membership",
        "waiting_list": "No",
    },
    "Tennis club Elzenhagen": {
        "membership_price": "€200/year; estimate, senior fee varies by year",
        "waiting_list": "Yes (active waitlist for adults)",
    },
    "Tennisclub A.T.V.D.": {
        "membership_price": "€215/year age 24+; €160/year through age 23",
        "waiting_list": "No (space available for new members)",
    },
    "Tennisclub Gaasperpark": {
        "membership_price": "€223/year for seniors age 25+",
        "waiting_list": "No for tennis (padel has a waitlist)",
    },
    "Tennispark Blauw-Wit": {
        "membership_price": "€200/year; estimate, exact fee not listed",
        "waiting_list": (
            "Yes (historical tennis membership stop; confirm current status)"
        ),
    },
    "Tennispark Randwijck": {
        "membership_price": (
            "€126/year (2026 rate); €63 prorated through 31 Mar 2027; "
            "new annual rate unknown"
        ),
        "waiting_list": "No known standing waitlist",
    },
    "Tennisvereniging Amsterdamse Bos": {
        "membership_price": "€225/year",
        "waiting_list": "No (direct entry available)",
    },
    "Tennisvereniging Diemen-Zuid (TVDZ)": {
        "membership_price": "€208/year; €7.50 one-time registration fee",
        "waiting_list": "No active waitlist",
    },
    "Tennisvereniging Rivierenbuurt (TVR)": {
        "membership_price": "€137.50/year; €100 bar-duty deposit",
        "waiting_list": (
            "Yes (long-term membership stop; full-membership waitlist closed)"
        ),
    },
    "TV Geuzenveld": {
        "membership_price": "€215/year; 25% first-year discount for new members",
        "waiting_list": "No (direct signup)",
    },
    "TV Tie-Breakers": {
        "membership_price": (
            "€275/year age 27+; €203/year age 18–26; €33 registration fee"
        ),
        "waiting_list": (
            "Yes (senior membership stop; admission by selection committee)"
        ),
    },
    "USC Tennis": {
        "membership_price": (
            "€462/year (€38.50/month, students €19.50/month)"
        ),
        "waiting_list": "No",
    },
}

st.set_page_config(
    page_title="Amsterdam Court Finder",
    page_icon=":material/sports_tennis:",
    layout="wide",
)


def data_path() -> Path:
    default_root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return Path(
        os.environ.get(
            "TENNIS_FINDER_DATA",
            str(default_root / "TennisCourtFinder" / "clubs.json"),
        )
    )


def default_clubs() -> list[dict[str, Any]]:
    return [
        {
            **details,
            "address": details.get(
                "address", f"{details['name']}, Amsterdam, Netherlands"
            ),
            "membership_price": SENIOR_MEMBERSHIP_PRICES.get(
                details["name"],
                "",
            ),
            "other_notes": details.get("other_notes", ""),
        }
        for details in CLUB_DETAILS
    ]


def load_clubs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return default_clubs()

    try:
        clubs = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read club data at {path}: {error}") from error
    if not isinstance(clubs, list):
        raise ValueError(f"Club data at {path} must be a JSON list.")

    by_name = {}
    for club in clubs:
        if not isinstance(club, dict) or not isinstance(club.get("name"), str):
            raise ValueError(f"Club data at {path} contains an invalid entry.")
        name = LEGACY_NAME_ALIASES.get(club["name"], club["name"])
        if name in by_name:
            raise ValueError(f"Club data at {path} contains duplicate clubs.")
        by_name[name] = club

    defaults = default_clubs()
    result = []
    for default in defaults:
        stored = by_name.get(default["name"], {})
        merged = dict(default)
        for key, value in stored.items():
            if key in {"name", "price_per_hour_eur"} or value is None or value == "":
                continue
            merged[key] = value
        legacy_price = stored.get("price_per_hour_eur")
        if not stored.get("price_info") and legacy_price is not None:
            merged["price_info"] = f"€{float(legacy_price):.2f}"
        for key, value in CLUB_DATA_CORRECTIONS.get(default["name"], {}).items():
            merged[key] = value
        if not merged.get("membership_price"):
            merged["membership_price"] = SENIOR_MEMBERSHIP_PRICES.get(
                default["name"],
                "",
            )
        if default["name"] == "Tennisclub A.T.V.D.":
            merged["other_notes"] = CLUB_DATA_CORRECTIONS["Tennisclub A.T.V.D."][
                "other_notes"
            ]
        result.append(merged)
    result.extend(
        club
        for name, club in by_name.items()
        if name not in DEFAULT_CLUB_NAME_SET
        and name not in LEGACY_DEFAULT_CLUB_NAMES
    )
    return result


def save_clubs(path: Path, clubs: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(clubs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def clean_optional_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def normalize_url(value: Any, label: str) -> str:
    url = clean_optional_text(value)
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be an http or https URL.")
    return url


def normalize_club_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": clean_optional_text(record.get("name")),
        "address": clean_optional_text(record.get("address")),
        "neighborhood": clean_optional_text(record.get("neighborhood")),
        "club_website": normalize_url(record.get("club_website"), "Club website"),
        "booking_url": normalize_url(record.get("booking_url"), "Booking URL"),
        "booking_platform": clean_optional_text(record.get("booking_platform")),
        "price_info": clean_optional_text(record.get("price_info")),
        "membership_price": clean_optional_text(record.get("membership_price")),
        "court_type": clean_optional_text(record.get("court_type")),
        "access_notes": clean_optional_text(record.get("access_notes")),
        "other_notes": clean_optional_text(record.get("other_notes")),
    }


def cycling_route(
    origin: str,
    destination: str,
    api_key: str,
    session: requests.Session,
) -> float | None:
    response = session.post(
        ROUTES_URL,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": ROUTE_FIELD_MASK,
        },
        json={
            "origin": {"address": origin},
            "destination": {"address": destination},
            "travelMode": "BICYCLE",
        },
        timeout=30,
    )
    response.raise_for_status()
    routes = response.json().get("routes", [])
    if not routes:
        return None

    duration = routes[0].get("duration", "")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)s", duration)
    if match is None:
        raise ValueError("Google Routes returned an incomplete cycling duration.")
    return round(float(match.group(1)) / 60, 1)


def google_routes_error(error: requests.RequestException, api_key: str) -> str:
    response = getattr(error, "response", None)
    if response is None:
        return str(error)
    try:
        google_error = response.json().get("error", {})
    except (ValueError, AttributeError):
        google_error = {}
    message = google_error.get("message")
    status = google_error.get("status")
    if not message:
        return str(error)
    safe_message = str(message).replace(api_key, "[redacted]") if api_key else str(message)
    status_code = response.status_code
    status_detail = f" ({status})" if status else ""
    return f"Google Routes returned HTTP {status_code}{status_detail}: {safe_message}"


def routing_origin(address: str) -> str:
    """Add Amsterdam context to a short home address for reliable geocoding."""
    normalized = clean_optional_text(address)
    if not normalized:
        return ""
    has_location_context = (
        re.search(r"\b(amsterdam|amstelveen|diemen|duivendrecht|nederland|netherlands)\b", normalized, re.I)
        or re.search(r"\b\d{4}\s?[A-Z]{2}\b", normalized, re.I)
    )
    if has_location_context:
        return normalized
    return f"{normalized}, Amsterdam, Netherlands"


@st.cache_data(ttl=3600, show_spinner=False)
def amsterdam_hourly_forecast() -> dict[str, Any]:
    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": 52.3676,
            "longitude": 4.9041,
            "hourly": (
                "temperature_2m,precipitation_probability,weather_code,"
                "wind_speed_10m,precipitation"
            ),
            "timezone": "Europe/Amsterdam",
            "forecast_days": 16,
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    hourly = payload.get("hourly") if isinstance(payload, dict) else None
    fields = (
        "time",
        "temperature_2m",
        "precipitation_probability",
        "weather_code",
        "wind_speed_10m",
        "precipitation",
    )
    if not isinstance(hourly, dict) or any(
        not isinstance(hourly.get(field), list) for field in fields
    ):
        raise ValueError("The weather service returned an incomplete hourly forecast.")
    if len({len(hourly[field]) for field in fields}) != 1:
        raise ValueError("The weather service returned mismatched hourly data.")
    return hourly


def weather_description(code: Any) -> str:
    if not isinstance(code, (int, float)):
        return "Conditions unavailable"
    code = int(code)
    if code == 0:
        return "Clear sky"
    if code == 1:
        return "Mainly clear"
    if code == 2:
        return "Partly cloudy"
    if code == 3:
        return "Overcast"
    if code in {45, 48}:
        return "Fog"
    if code in {51, 53, 55, 56, 57}:
        return "Drizzle"
    if code in {61, 63, 65, 66, 67}:
        return "Rain"
    if code in {71, 73, 75, 77}:
        return "Snow"
    if code in {80, 81, 82}:
        return "Rain showers"
    if code in {85, 86}:
        return "Snow showers"
    if code in {95, 96, 99}:
        return "Thunderstorm"
    return "Conditions unavailable"


def recommend_court_environment(
    temperature: Any,
    precipitation_probability: Any,
    rainfall: Any,
    wind_speed: Any,
) -> tuple[str, str] | None:
    values = (temperature, precipitation_probability, rainfall, wind_speed)
    if not all(
        isinstance(value, (int, float)) and math.isfinite(value)
        for value in values
    ):
        return None

    reasons = []
    if temperature <= 5:
        reasons.append(f"cold ({temperature:.0f}°C)")
    if wind_speed >= 35:
        reasons.append(f"strong wind ({wind_speed:.0f} km/h)")
    if precipitation_probability >= 50 and rainfall >= 0.3:
        reasons.append(
            f"rain likely ({precipitation_probability:.0f}%, {rainfall:.1f} mm)"
        )
    if reasons:
        return "Indoor", "Indoor is preferable for " + ", ".join(reasons) + "."
    return (
        "Outdoor",
        "Outdoor conditions look manageable; when the choice is unclear, "
        "outdoor courts are usually cheaper.",
    )


def show_amsterdam_weather(
    selected_date: date,
    selected_time: time,
) -> str | None:
    amsterdam_today = datetime.now(AMSTERDAM_TIMEZONE).date()
    forecast_end = amsterdam_today + timedelta(days=15)
    with st.container(
        border=True,
        key="amsterdam_weather_forecast",
    ):
        st.markdown("**Amsterdam weather forecast**")
        if selected_date < amsterdam_today:
            st.caption("A forecast is not available for a past date.")
            return
        if selected_date > forecast_end:
            st.caption(
                "The weather service provides forecasts up to 16 days ahead. "
                "A forecast for this date is not available yet."
            )
            return

        selected_hour = selected_time.replace(minute=0, second=0, microsecond=0)
        forecast_timestamp = (
            f"{selected_date.isoformat()}T{selected_hour:%H:%M}"
        )
        try:
            hourly = amsterdam_hourly_forecast()
        except (requests.RequestException, ValueError) as error:
            st.warning(f"Could not load the Amsterdam weather forecast: {error}")
            return

        try:
            index = hourly["time"].index(forecast_timestamp)
        except ValueError:
            st.caption(
                "A forecast is not available for that hour yet. "
                "Choose a future time or check again later."
            )
            return

        temperature = hourly["temperature_2m"][index]
        precipitation = hourly["precipitation_probability"][index]
        wind_speed = hourly["wind_speed_10m"][index]
        rainfall = hourly["precipitation"][index]
        condition = weather_description(hourly["weather_code"][index])
        next_hour = datetime.combine(selected_date, selected_hour) + timedelta(hours=1)
        st.caption(
            f"{condition} · forecast for {selected_hour:%H:%M}–"
            f"{next_hour:%H:%M} Amsterdam time"
        )
        metric_columns = st.columns(4)
        metric_columns[0].metric(
            "Temperature",
            f"{temperature:.0f} °C" if isinstance(temperature, (int, float)) else "—",
        )
        metric_columns[1].metric(
            "Precipitation chance",
            f"{precipitation:.0f}%" if isinstance(precipitation, (int, float)) else "—",
        )
        metric_columns[2].metric(
            "Wind",
            f"{wind_speed:.0f} km/h" if isinstance(wind_speed, (int, float)) else "—",
        )
        metric_columns[3].metric(
            "Expected rainfall",
            f"{rainfall:.1f} mm" if isinstance(rainfall, (int, float)) else "—",
            help="Forecast rainfall for the selected hour.",
        )
        recommendation = recommend_court_environment(
            temperature,
            precipitation,
            rainfall,
            wind_speed,
        )
        if recommendation is not None:
            environment, explanation = recommendation
            st.markdown(f"**Recommended court: {environment}.** {explanation}")
        else:
            environment = None
        st.caption(
            "Hourly forecast by [Open-Meteo](https://open-meteo.com/) · "
            "no API key required · forecast coverage is up to 16 days."
        )
        return environment


def booking_slot_key(selected_date: date, start_time: time, duration: int) -> str:
    return f"{selected_date.isoformat()}|{start_time:%H:%M}|{duration}"


TWO_WEEK_MEET_AND_PLAY_CLUBS = {
    "A.L.T.C. De Aemstelburgh",
    "TV Tie-Breakers",
    "Tennisclub A.T.V.D.",
    "Tennis club Elzenhagen",
    "Tennisvereniging Amsterdamse Bos",
    "TV Geuzenveld",
    "LTC Startbaan",
}
BOOKING_ADVANCE_DAYS = {
    "USC Tennis": 3,
    "Tennisclub Gaasperpark": 10,
    **dict.fromkeys(TWO_WEEK_MEET_AND_PLAY_CLUBS, 14),
    "Amsterdam Racket Club": 20,
}
BOOKING_ADVANCE_HOURS = {
    "Tennisvereniging Rivierenbuurt (TVR)": 24,
}
SLOW_PORTAL_TIMEOUT_CLUBS = {
    "Amstelpark Tennisclub",
    "Frans Otten Stadion",
}


def should_treat_timeout_as_too_early(
    club_name: str,
    error: Exception,
) -> bool:
    if club_name not in SLOW_PORTAL_TIMEOUT_CLUBS:
        return False
    if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)):
        return True
    error_message = str(error).casefold()
    return any(
        marker in error_message
        for marker in ("timeouterror", "timeout", "timed out")
    )


def booking_slot_is_too_early(
    club_name: str,
    requested_slot: str,
    now: datetime | None = None,
) -> bool:
    selected_date_text, _, slot_details = requested_slot.partition("|")
    selected_date = date.fromisoformat(selected_date_text)

    advance_days = BOOKING_ADVANCE_DAYS.get(club_name)
    if advance_days is not None:
        amsterdam_today = (
            now.astimezone(AMSTERDAM_TIMEZONE).date()
            if now is not None
            else datetime.now(AMSTERDAM_TIMEZONE).date()
        )
        return selected_date > amsterdam_today + timedelta(days=advance_days)

    advance_hours = BOOKING_ADVANCE_HOURS.get(club_name)
    if advance_hours is None:
        return False

    slot_time_text, _, _ = slot_details.partition("|")
    selected_start = datetime.combine(
        selected_date,
        time.fromisoformat(slot_time_text),
        tzinfo=AMSTERDAM_TIMEZONE,
    ).astimezone(timezone.utc)
    current_time = (now or datetime.now(AMSTERDAM_TIMEZONE)).astimezone(timezone.utc)
    return selected_start > current_time + timedelta(hours=advance_hours)


def availability_label(
    club: dict[str, Any],
    availability_results: dict[str, dict[str, Any]],
    requested_slot: str,
) -> str:
    result = availability_results.get(club["name"], {})
    if result.get("slot_key") == requested_slot:
        status = str(result["status"])
        if (
            club["name"] in TWO_WEEK_MEET_AND_PLAY_CLUBS
            and status
            in {
                "Could not verify - start time is not shown",
                "Could not verify - no court slots are shown",
            }
        ):
            return "Unavailable"
        if status.startswith("Unavailable"):
            return "Unavailable"
        if status.startswith("Available"):
            return "✅ Available"
        return str(result["status"])
    if club["name"] == "Tennisvereniging Diemen-Zuid (TVDZ)":
        return "Only through phone"
    if club["name"] in BROWSER_CHECK_CLUBS:
        return "Not checked for this slot"
    if "members only" in str(club.get("access_notes", "")).casefold():
        return "Members-only portal"
    return "Not configured - automated check unavailable"


def booking_access_label(club: dict[str, Any]) -> str:
    access = str(club.get("access_notes", "")).casefold()
    if "members only" in access:
        return "Members only"
    if "public guest booking" in access:
        if "spring and summer" in access or "seasonal" in access:
            return "Public seasonally; members can invite guests"
        return "Public (non-members)"
    if "public" in access or "non-members" in access:
        return "Public (non-members)"
    return "Not specified"


def available_courts_label(
    club: dict[str, Any],
    availability_results: dict[str, dict[str, Any]],
    requested_slot: str,
) -> str:
    if (
        availability_label(club, availability_results, requested_slot)
        == "Too early to check"
    ):
        return "—"
    result = availability_results.get(club["name"], {})
    if result.get("slot_key") != requested_slot:
        return "—"
    status = str(result.get("status", ""))
    if status.startswith("Unavailable"):
        return "None"
    if not status.startswith("Available"):
        return "—"

    labels = {
        "outdoor": "☀️ Outdoor",
        "indoor": "🏠 Indoor",
        "covered": "⛱️ Covered",
        "unknown": "Court type unknown",
    }
    available_types = result.get("available_court_types")
    if isinstance(available_types, list):
        return " · ".join(
            labels[court_type]
            for court_type in available_types
            if court_type in labels
        ) or "Type not reported"

    courts = result.get("available_courts", [])
    if not isinstance(courts, list) or not courts:
        if club["name"] == "Tennispark Blauw-Wit":
            return "☀️ Outdoor"
        return "Type not reported"

    counts: dict[str, int] = {}
    for court in courts:
        if not isinstance(court, dict):
            continue
        environment = str(court.get("environment", "unknown"))
        if environment not in labels:
            environment = "unknown"
        counts[environment] = counts.get(environment, 0) + 1
    if not counts:
        return "Type not reported"
    return " · ".join(
        f"{labels[environment]} ({count})"
        for environment, count in counts.items()
    )


def display_clubs(
    clubs: list[dict[str, Any]],
    route_results: dict[str, dict[str, Any]],
    current_origin: str,
    route_origin: str,
    availability_results: dict[str, dict[str, Any]],
    requested_slot: str,
) -> pd.DataFrame:
    rows = []
    current_routes = route_results if current_origin == route_origin else {}

    def route_minutes(club: dict[str, Any]) -> float:
        route = current_routes.get(club["name"], {})
        if route.get("address") != club.get("address"):
            return float("inf")
        try:
            return float(route.get("minutes", float("inf")))
        except (TypeError, ValueError):
            return float("inf")

    def availability_group(club: dict[str, Any]) -> int:
        label = availability_label(club, availability_results, requested_slot)
        if label.startswith("✅ Available"):
            return 0
        if label == "Too early to check":
            return 1
        if label == "Unavailable":
            return 2
        return 3

    def precheck_access_group(club: dict[str, Any]) -> int:
        access = booking_access_label(club)
        if access.startswith("Public"):
            return 0
        if access == "Members only":
            return 2
        return 1

    has_slot_results = any(
        result.get("slot_key") == requested_slot
        for result in availability_results.values()
        if isinstance(result, dict)
    )
    for club in sorted(
        clubs,
        key=lambda item: (
            availability_group(item)
            if has_slot_results
            else precheck_access_group(item),
            route_minutes(item),
            item["name"].casefold(),
        ),
    ):
        route_result = current_routes.get(club["name"], {})
        if route_result.get("address") != club.get("address"):
            route_result = {}
        minutes = route_result.get("minutes")
        route = (
            f"{minutes:.0f} min"
            if minutes is not None
            else "Not calculated"
        )
        rows.append(
            {
                "Club": club["name"],
                "Neighbourhood": club.get("neighborhood") or "Not specified",
                "Availability": availability_label(
                    club, availability_results, requested_slot
                ),
                "Available type": available_courts_label(
                    club, availability_results, requested_slot
                ),
                "Booking access": booking_access_label(club),
                "Cycling time": route,
                "Price / court / hour (€)": club.get("price_info") or "Not listed",
                "Membership price": (
                    DUAL_ACCESS_MEMBERSHIP_DATA.get(club["name"], {}).get(
                        "membership_price"
                    )
                    or club.get("membership_price")
                    or "Not published"
                ),
                "Court surface": club.get("court_type") or "Not listed",
                "Introducé allowed?": INTRODUCE_ALLOWED.get(
                    club["name"],
                    "Not published",
                ),
                "Introducé price": (
                    "Not applicable"
                    if INTRODUCE_ALLOWED.get(club["name"]) == "No"
                    else INTRODUCE_PRICE.get(club["name"], "Not published")
                ),
                "Waiting list": (
                    DUAL_ACCESS_MEMBERSHIP_DATA.get(club["name"], {}).get(
                        "waiting_list"
                    )
                    or MEMBERSHIP_WAITLISTS.get(club["name"], "Not published")
                ),
                "Booking page": (
                    "Not applicable"
                    if club["name"] == "Tennisvereniging Diemen-Zuid (TVDZ)"
                    else club.get("booking_url") or ""
                ),
                "Club site": club.get("club_website") or "",
                "Other info": club.get("other_notes") or "",
            }
        )
    return pd.DataFrame(rows)


def append_membership_other_info(existing: Any, membership_note: str) -> str:
    existing_text = clean_optional_text(existing)
    if existing_text.casefold() == "not listed":
        existing_text = ""
    notes = [
        note
        for note in (existing_text, membership_note.strip())
        if note
    ]
    return " ".join(notes) if notes else "Not listed"


def membership_table_other_info(club_name: str, existing: Any) -> str:
    notes = [
        SENIOR_MEMBERSHIP_OTHER_INFO.get(club_name, ""),
        MEMBERSHIP_CAPACITY_INFO.get(club_name, {}).get("notes", ""),
    ]
    return append_membership_other_info(
        existing,
        " ".join(note for note in notes if note),
    )


def membership_capacity_value(info: Any, key: str) -> str:
    if not isinstance(info, dict):
        return "Not published"
    return info.get(key, "Not published")


def style_club_rows(
    frame: pd.DataFrame,
    recommended_environment: str | None = None,
    all_rows_gray: bool = False,
) -> pd.io.formats.style.Styler:
    def row_color(row: pd.Series) -> list[str]:
        availability = str(row.get("Availability", ""))
        waiting_list = str(row.get("Waiting list", "")).strip().casefold()
        has_waiting_list_status = waiting_list.startswith(("yes", "no"))
        if (
            all_rows_gray
            or str(row.get("Booking access", "")).casefold() == "members only"
            or availability.startswith("Could not verify")
            or availability.startswith("Not checked")
            or availability.startswith("Not configured")
            or availability == "Members-only portal"
            or availability == "Only through phone"
        ):
            row_color_value = "background-color: #EEEEEE"
        elif waiting_list.startswith("no"):
            row_color_value = "background-color: #E8F4E7"
        elif waiting_list.startswith("yes"):
            row_color_value = "background-color: #FCE9E7"
        elif availability.startswith("✅ Available"):
            row_color_value = "background-color: #E8F4E7"
        elif availability.startswith("Unavailable") or availability == "Too early to check":
            row_color_value = "background-color: #FCE9E7"
        else:
            row_color_value = ""
        colors = [row_color_value] * len(row)

        cycling_time = str(row.get("Cycling time", ""))
        match = re.match(r"(\d+)\s+min\b", cycling_time)
        if match and "Cycling time" in row.index:
            minutes = int(match.group(1))
            if minutes <= 15:
                cycling_style = "#DDF2DF"
                cycling_text_color = "#287A32"
            elif minutes <= 30:
                cycling_style = "#FFF1C7"
                cycling_text_color = "#8A6500"
            else:
                cycling_style = "#F8DEDA"
                cycling_text_color = "#A93226"
            if has_waiting_list_status:
                colors[row.index.get_loc("Cycling time")] = (
                    f"{row_color_value}; color: {cycling_text_color}; "
                    "font-weight: bold"
                )
            else:
                colors[row.index.get_loc("Cycling time")] = (
                    f"background-color: {cycling_style}"
                )
        if "Membership price" in row.index:
            price_match = re.search(
                r"€\s*(\d+(?:[.,]\d{1,2})?)",
                str(row["Membership price"]),
            )
            if price_match:
                price = float(price_match.group(1).replace(",", "."))
                price_color = (
                    "#287A32"
                    if price <= 200
                    else "#8A6500"
                    if price <= 275
                    else "#A93226"
                )
                colors[row.index.get_loc("Membership price")] = (
                    f"{row_color_value}; color: {price_color}; font-weight: bold"
                    if has_waiting_list_status
                    else f"color: {price_color}; font-weight: bold"
                )
        if "Ratio (members/court)" in row.index:
            ratio_match = re.search(
                r"\d+",
                str(row["Ratio (members/court)"]),
            )
            if ratio_match:
                ratio = int(ratio_match.group())
                ratio_background, ratio_text = (
                    ("#DDF2DF", "#287A32")
                    if ratio <= 75
                    else ("#FFF1C7", "#8A6500")
                    if ratio <= 150
                    else ("#F8DEDA", "#A93226")
                )
                colors[row.index.get_loc("Ratio (members/court)")] = (
                    f"background-color: {ratio_background}; "
                    f"color: {ratio_text}; font-weight: bold"
                )
        court_types = str(row.get("Available type", "")).casefold()
        has_outdoor = "outdoor" in court_types
        has_indoor = "indoor" in court_types
        recommended = (
            recommended_environment.casefold()
            if isinstance(recommended_environment, str)
            else ""
        )
        if (
            not all_rows_gray
            and availability.startswith("✅ Available")
            and recommended in {"outdoor", "indoor"}
            and not (
                (recommended == "outdoor" and has_outdoor)
                or (recommended == "indoor" and has_indoor)
            )
            and (has_outdoor or has_indoor)
            and "Available type" in row.index
        ):
            colors[row.index.get_loc("Available type")] = (
                "background-color: #FCE9E7"
            )
        return colors

    return frame.style.apply(row_color, axis=1)


def release_browser_worker_registry(
    registry: dict[str, dict[str, Any]],
) -> None:
    for worker in tuple(registry.values()):
        process = worker["process"]
        if process.poll() is not None:
            continue
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@st.cache_resource(scope="session", on_release=release_browser_worker_registry)
def browser_worker_registry() -> tuple[dict[str, dict[str, Any]], threading.RLock]:
    return {}, threading.RLock()


def current_browser_worker() -> dict[str, Any] | None:
    registry, lock = browser_worker_registry()
    with lock:
        worker = registry.get("active")
        legacy_worker = st.session_state.get("booking_browser_worker")
        if worker is None and legacy_worker:
            if legacy_worker["process"].poll() is None:
                worker = legacy_worker
                registry["active"] = worker
            st.session_state.pop("booking_browser_worker", None)
        if worker and worker.get("protocol") != AUTOMATIC_CHECKER_PROTOCOL:
            close_failed_browser_worker(worker["process"])
            registry.pop("active", None)
            worker = None
        if worker and worker["process"].poll() is not None:
            registry.pop("active", None)
            worker = None
    return worker


def store_browser_worker(worker: dict[str, Any] | None) -> None:
    registry, lock = browser_worker_registry()
    with lock:
        if worker is None:
            registry.pop("active", None)
        else:
            registry["active"] = worker


def read_browser_worker_output(
    process: subprocess.Popen[str],
    responses: queue.Queue[dict[str, Any]],
    stderr_lines: list[str],
    stderr_finished: threading.Event,
) -> None:
    if process.stdout is None:
        responses.put({"ok": False, "error": "Booking browser output is unavailable."})
        return
    received_check_response = False
    try:
        for line in process.stdout:
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                responses.put(
                    {"ok": False, "error": "Booking browser returned an invalid response."}
                )
                continue
            responses.put(response)
            if (
                response.get("ok")
                and not response.get("ready")
                and not response.get("stopped")
            ):
                received_check_response = True
    except OSError as error:
        responses.put({"ok": False, "error": f"Could not read the booking browser: {error}"})
    finally:
        stderr_finished.wait(timeout=2)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        exit_code = process.poll()
        completed_calendar_check = any(
            "Completed calendar check for " in line
            for line in stderr_lines
        )
        if exit_code == 0 or received_check_response or completed_calendar_check:
            return
        error_message = (
            "The booking browser closed its output stream but remained running"
            if exit_code is None
            else f"The booking browser process exited unexpectedly (exit code {exit_code})"
        )
        if stderr_lines:
            error_message += ": " + " | ".join(stderr_lines[-8:])
        responses.put({"ok": False, "error": error_message})


@st.cache_resource
def ensure_playwright_browser_installed() -> bool:
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "playwright",
                "install",
                "chromium",
                "--only-shell",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            "Installing the Playwright Chromium browser timed out. "
            "Try again after the app restarts."
        ) from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or "").strip()
        if details:
            details = details[-3000:]
        message = "Could not install the Playwright Chromium browser."
        if details:
            message += f" Installer output: {details}"
        raise RuntimeError(message) from error
    except OSError as error:
        raise RuntimeError(
            f"Could not run the Playwright browser installer: {error}"
        ) from error
    return True


def start_browser_worker(
    secrets: tuple[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ensure_playwright_browser_installed()
    worker_script = Path(__file__).with_name("tennis_browser_worker.py")
    process = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(worker_script),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    responses: queue.Queue[dict[str, Any]] = queue.Queue()
    stderr_lines: list[str] = []
    stderr_finished = threading.Event()
    threading.Thread(
        target=read_browser_worker_output,
        args=(process, responses, stderr_lines, stderr_finished),
        daemon=True,
    ).start()
    threading.Thread(
        target=drain_browser_worker_errors,
        args=(process, stderr_lines, stderr_finished, secrets or ()),
        daemon=True,
    ).start()
    worker = {
        "process": process,
        "responses": responses,
        "diagnostics": stderr_lines,
        "protocol": AUTOMATIC_CHECKER_PROTOCOL,
    }
    try:
        response = responses.get(timeout=60)
    except queue.Empty as error:
        close_failed_browser_worker(process)
        raise TimeoutError(
            "The local booking browser did not start within 60 seconds."
        ) from error
    if not response.get("ok"):
        close_failed_browser_worker(process)
        raise RuntimeError(response.get("error", "Could not start the booking browser."))
    return worker, response


def close_failed_browser_worker(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if process.stdin is not None:
        process.stdin.close()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def drain_browser_worker_errors(
    process: subprocess.Popen[str],
    stderr_lines: list[str],
    finished: threading.Event,
    secrets: tuple[str, ...] = (),
) -> None:
    try:
        if process.stderr is not None:
            for line in process.stderr:
                clean_line = " ".join(line.split())
                if clean_line:
                    for secret in secrets:
                        if secret:
                            clean_line = clean_line.replace(secret, "[redacted]")
                    max_length = 10_000 if clean_line.startswith("[booking-result] ") else 500
                    stderr_lines.append(clean_line[:max_length])
                    del stderr_lines[:-20]
    finally:
        finished.set()


def completed_result_from_diagnostics(
    diagnostics: list[str],
) -> dict[str, Any] | None:
    for line in reversed(diagnostics):
        prefix = "[booking-result] "
        if not line.startswith(prefix):
            continue
        try:
            response = json.loads(line[len(prefix):])
        except json.JSONDecodeError:
            continue
        if isinstance(response, dict) and response.get("ok") and response.get("status"):
            return response
    return None


def read_worker_result_file(path: Path) -> dict[str, Any] | None:
    try:
        response = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(response, dict) and response.get("ok") and response.get("status"):
        return response
    return None


def browser_worker_request(
    worker: dict[str, Any],
    command: dict[str, Any],
    *,
    timeout: float = 30,
) -> dict[str, Any]:
    process = worker["process"]
    if process.poll() is not None:
        raise RuntimeError(
            "The local booking browser has stopped. Open a new browser session."
        )
    if process.stdin is None:
        raise RuntimeError("The local booking browser input is unavailable.")
    result_path: Path | None = None
    try:
        command = dict(command)
        if command.get("action") == "CHECK":
            descriptor, path_string = tempfile.mkstemp(
                prefix="tennis-booking-result-",
                suffix=".json",
            )
            os.close(descriptor)
            result_path = Path(path_string)
            command["_result_path"] = str(result_path)
        try:
            process.stdin.write(json.dumps(command) + "\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise RuntimeError(
                f"Could not send a command to the booking browser: {error}"
            ) from error

        deadline = monotonic() + timeout
        while True:
            if result_path is not None:
                file_result = read_worker_result_file(result_path)
                if file_result is not None:
                    return file_result
            diagnostics = worker.get("diagnostics", [])
            completed_result = completed_result_from_diagnostics(diagnostics)
            if completed_result is not None:
                return completed_result
            remaining = deadline - monotonic()
            if remaining <= 0:
                last_messages = " | ".join(diagnostics[-6:])
                message = (
                    f"The booking browser did not respond within {timeout:g} seconds."
                )
                if last_messages:
                    message += f" Last progress: {last_messages}"
                raise TimeoutError(message)
            try:
                response = worker["responses"].get(
                    timeout=max(0.01, min(remaining, 0.25))
                )
                break
            except queue.Empty:
                continue
        if not response.get("ok"):
            raise RuntimeError(
                response.get("error", "The booking browser could not complete the request.")
            )
        return response
    finally:
        if result_path is not None:
            try:
                result_path.unlink()
            except FileNotFoundError:
                pass


def check_club_availability(
    club: dict[str, Any],
    selected_date: date,
    selected_time: time,
    duration_minutes: int,
    credentials: tuple[str, str] | None = None,
) -> dict[str, Any]:
    worker = None
    try:
        worker, _ready = start_browser_worker(credentials)
        command = {
            "action": "CHECK",
            "url": club.get("booking_url", ""),
            "date": selected_date.isoformat(),
            "start_time": selected_time.strftime("%H:%M"),
            "duration_minutes": int(duration_minutes),
        }
        if club["name"] in CREDENTIAL_CHECK_CLUBS:
            if credentials is None:
                raise RuntimeError("Sign-in is required for this booking portal.")
            if club["name"] in USC_CREDENTIAL_CHECK_CLUBS:
                command["email"], command["password"] = credentials
            else:
                command["username"], command["password"] = credentials
        return browser_worker_request(worker, command, timeout=120)
    except RuntimeError as error:
        message = str(error)
        if credentials:
            for secret in credentials:
                if secret:
                    message = message.replace(secret, "[redacted]")
        raise RuntimeError(message) from error
    finally:
        if worker is not None:
            process = worker["process"]
            if process.poll() is None:
                try:
                    browser_worker_request(
                        worker,
                        {"action": "STOP"},
                        timeout=10,
                    )
                    process.wait(timeout=10)
                except (OSError, RuntimeError, TimeoutError, subprocess.TimeoutExpired):
                    close_failed_browser_worker(process)


def run_availability_checks(
    available_clubs: list[dict[str, Any]],
    selected_date: date,
    selected_time: time,
    duration_minutes: int,
    credentials: dict[str, tuple[str, str]],
) -> None:
    previous_worker = current_browser_worker()
    if previous_worker is not None:
        browser_worker_request(previous_worker, {"action": "STOP"})
        previous_worker["process"].wait(timeout=10)
        store_browser_worker(None)

    requested_slot = booking_slot_key(selected_date, selected_time, duration_minutes)
    responses: dict[str, dict[str, Any]] = {}
    failures: dict[str, str] = {}
    early_clubs = [
        club
        for club in available_clubs
        if booking_slot_is_too_early(club["name"], requested_slot)
    ]
    for club in early_clubs:
        responses[club["name"]] = {
            "status": "Too early to check",
            "reason": "The selected date is outside this club's booking window.",
        }
    ordered_clubs = sorted(
        (
            club
            for club in available_clubs
            if club not in early_clubs
        ),
        key=lambda club: club["name"] not in CREDENTIAL_CHECK_CLUBS,
    )
    with ThreadPoolExecutor(
        max_workers=max(1, min(len(ordered_clubs), 2))
    ) as executor:
        futures = {
            executor.submit(
                check_club_availability,
                club,
                selected_date,
                selected_time,
                duration_minutes,
                (
                    credentials["usc"]
                    if club["name"] in USC_CREDENTIAL_CHECK_CLUBS
                    else credentials["baanreserveren"]
                    if club["name"] in BAANRESERVEREN_CREDENTIAL_CHECK_CLUBS
                    else None
                ),
            ): club
            for club in ordered_clubs
        }
        for future in as_completed(futures):
            club = futures[future]
            try:
                response = future.result()
                responses[club["name"]] = response
                if (
                    club["name"] == "Amsterdam Racket Club"
                    and str(response.get("status", "")).startswith(
                        "Could not verify"
                    )
                ):
                    failures[club["name"]] = response.get(
                        "reason",
                        "Bookaball did not provide enough information to verify this slot.",
                    )
                if "login failed" in str(response.get("status", "")).casefold():
                    failures[club["name"]] = response.get(
                        "reason",
                        "The booking portal sign-in failed.",
                    )
            except (KeyError, OSError, RuntimeError, TimeoutError, ValueError) as error:
                if should_treat_timeout_as_too_early(club["name"], error):
                    responses[club["name"]] = {
                        "status": "Too early to check",
                        "reason": (
                            "The booking calendar did not finish loading within "
                            "the time limit; this timeout is treated as too early "
                            "to check."
                        ),
                    }
                else:
                    failures[club["name"]] = str(error)

    checked_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    results = st.session_state.setdefault("availability_results", {})
    for club in available_clubs:
        response = responses.get(club["name"])
        results[club["name"]] = {
            "slot_key": requested_slot,
            "status": (
                response["status"]
                if response
                else "Could not verify - check failed"
            ),
            "reason": (
                response.get("reason", "")
                if response
                else failures.get(club["name"], "The availability check failed.")
            ),
            "checked_at": checked_at,
            "available_courts": (
                response.get("available_courts", [])
                if response
                else []
            ),
            "available_court_types": (
                response.get("available_court_types")
                if response
                else None
            ),
        }
    st.session_state["availability_check_failures"] = failures


@st.dialog("Booking portal sign-in", width="small")
def availability_credentials_dialog(
    available_clubs: list[dict[str, Any]],
    selected_date: date,
    selected_time: time,
    duration_minutes: int,
) -> None:
    st.markdown(
        "Register using the same booking-portal credentials for "
        "[Amstelpark](https://amstelpark.baanreserveren.nl/) and "
        "[Frans Otten](https://fransotten.baanreserveren.nl/). "
        "[USC](https://my.uscsport.nl/pages/login) registration requires "
        "separate credentials; enter its email "
        "and password as well."
    )
    st.caption(
        "Credentials are kept in this app session's memory so you can check "
        "different slots without entering them again. They are not written to "
        "disk or app logs; use “Forget saved credentials” when finished."
    )
    with st.form("booking_portal_credentials", clear_on_submit=True):
        baan_username = st.text_input(
            "Amstelpark / Frans Otten username",
            autocomplete="username",
        )
        baan_password = st.text_input(
            "Password",
            type="password",
            autocomplete="current-password",
        )
        usc_email = st.text_input("USC email", autocomplete="email")
        usc_password = st.text_input(
            "USC password",
            type="password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button("Check all clubs", type="primary")

    if not submitted:
        return
    if (
        not baan_username.strip()
        or not baan_password
        or not usc_email.strip()
        or not usc_password
    ):
        st.error("Enter the credentials for both booking portals to continue.")
        return

    credentials = {
        "baanreserveren": (baan_username.strip(), baan_password),
        "usc": (usc_email.strip(), usc_password),
    }
    st.session_state["availability_portal_credentials"] = credentials
    st.session_state["availability_check_started"] = True
    try:
        with st.spinner("Checking all public (non-member) clubs..."):
            run_availability_checks(
                available_clubs,
                selected_date,
                selected_time,
                duration_minutes,
                credentials,
            )
    except (OSError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as error:
        st.session_state["availability_check_failures"] = {
            "All configured clubs": str(error)
        }
    st.rerun()


def booking_browser_controls(
    clubs: list[dict[str, Any]],
    action_column: Any,
) -> bool:
    club_names = {item["name"] for item in clubs}
    missing_clubs = BROWSER_CHECK_CLUBS - club_names
    if missing_clubs:
        st.error(
            "Configured availability-check club(s) are missing from the saved club list: "
            + ", ".join(sorted(missing_clubs))
        )
        return False
    return action_column.button(
        "Check availability",
        key="check_all_booking_availability",
        type="primary",
    )


def availability_search_explanation() -> None:
    with st.expander("How availability is checked"):
        st.markdown(
            "Choose a date, start time and session length, then select **Check "
            "availability**. The dashboard checks the "
            "booking pages it supports and reports what they show for that slot."
        )
        st.markdown(
            """
            - **Public booking pages**
              - KNLTB Meet & Play: Aemstelburgh, Tie-Breakers, Gaasperpark,
                ATVD, Elzenhagen, TVR, Tennisvereniging Amsterdamse Bos,
                TV Geuzenveld and LTC Startbaan. Gaasperpark is filtered to
                tennis courts; ATVD's public rental is seasonal.
              - USC: public rental is available through its booking site; sign-in
                is needed to view slots. It offers 60-minute bookings for today and
                the next three days.
              - Amsterdam Racket Club: Bookaball publicly shows available indoor
                and outdoor slots. An account is needed only to complete a booking.
              - Amstelpark and Frans Otten: both offer public court bookings through
                the same type of booking portal and use the same portal credentials.
              - Blauw-Wit: its public calendar is checked for reservations. Booking
                still requires an account with the club.
              - Tennisvereniging Diemen-Zuid (TVDZ) checks availability by phone
                only; call 020 - 6001857.
              - Tennisvereniging Ouderkerk uses KNLTB Meet & Play, and Tennispark
                Randwijck has an online reservation page, but neither is currently
                included in the automatic availability checker.
              - PARK Tennis offers public court booking; its booking flow is not
                currently checked automatically.
            - **Sign-in required**
              - Register using the same booking-portal credentials for
                [Amstelpark](https://amstelpark.baanreserveren.nl/) and
                [Frans Otten](https://fransotten.baanreserveren.nl/).
                [USC](https://my.uscsport.nl/pages/login) requires separate
                credentials.
              - Credentials can be reused during this app session. Browser cookies are
                temporary and are discarded after each check.
            - **What the checker does**
              - It compares the selected date, start time and session length with the
                booking page.
              - When needed, it opens a time-slot detail to identify indoor or outdoor
                courts, but it never reserves or books a court.
              - If a page does not clearly confirm the slot, the result stays
                **Could not verify** rather than guessing.
            - **A few limits**
              - ATVD guest invitations through ClubApp are not checked.
              - For Meet & Play clubs other than TVR and Gaasperpark, dates more
                than 14 days ahead are labeled **Too early to check** and are not
                checked. Within that window, a slot missing from the portal is
                treated as **Unavailable**.
              - Amsterdam Racket Club's Bookaball calendar can be checked up to
                20 days ahead; later dates are labeled **Too early to check**.
            """
        )


COURT_SURFACE_DESCRIPTIONS = {
    "Clay": (
        "Natural or clay-style mineral court material is relatively slow and "
        "usually gives a higher bounce. It allows controlled sliding and suits "
        "topspin players, patient baseliners and longer rallies. The label "
        "\"gravel\" in these club listings is grouped here."
    ),
    "Hard court": (
        "A firm paved or layered court, including asphalt and concrete, generally "
        "offers a predictable medium-to-fast bounce and supports direct, flatter "
        "hitting. It suits players who like a consistent pace, though it is firmer "
        "underfoot than clay or cushioned courts."
    ),
    "Synthetic grass": (
        "Artificial grass, often sand-dressed, generally has a lower bounce and "
        "quick response. It can suit fast reactions, flatter shots and serve-and-"
        "volley play; grip and bounce depend on the infill and condition."
    ),
    "SmashCourt": (
        "A sand-dressed synthetic all-weather court designed for drainage and "
        "reliable grip. It is intended for use across more weather conditions than "
        "natural clay; its exact pace and bounce vary with upkeep."
    ),
    "Claytech": (
        "An engineered clay-style surface intended to retain clay-like grip and "
        "rally feel with more weather-resistant use. Its generally slower, higher "
        "bounce suits topspin and point construction."
    ),
    "Cushioned hard court": (
        "A hard court with a resilient cushioning layer. It keeps a firm, "
        "predictable bounce while softening impact underfoot, suiting frequent "
        "players who prefer hard-court response with added comfort."
    ),
    "Indoor synthetic tennis floor": (
        "A synthetic indoor floor provides consistent footing without weather "
        "disruption. Its speed and bounce depend on the floor specification; the "
        "club listing identifies Tennisfloor-Pro."
    ),
    "Unspecified all-weather": (
        "This label indicates intended use in varied conditions but does not "
        "identify the material. Pace, bounce and grip therefore depend on the "
        "specific court system."
    ),
}


def court_surface_categories(surface: str) -> list[str]:
    normalized = surface.casefold()
    compact = re.sub(r"\s+", "", normalized)
    categories = []
    if "kushion" in normalized:
        categories.append("Cushioned hard court")
    else:
        if "claytech" in normalized:
            categories.append("Claytech")
        elif "clay" in normalized or "gravel" in normalized:
            categories.append("Clay")
        if "smashcourt" in compact:
            categories.append("SmashCourt")
        if "artificial grass" in normalized or "edel agile" in normalized:
            categories.append("Synthetic grass")
        if any(term in normalized for term in ("hardcourt", "asphalt", "concrete")):
            categories.append("Hard court")
        if "pro tennisfloor" in normalized or "tennisfloor" in normalized:
            categories.append("Indoor synthetic tennis floor")
        if "all-weather" in normalized and not categories:
            categories.append("Unspecified all-weather")
    return categories or ["Surface type not specified"]


@st.dialog("Court surface info")
def show_court_surface_info(frame: pd.DataFrame) -> None:
    labels = sorted(
        {
            str(surface).strip()
            for surface in frame["Court surface"]
            if str(surface).strip() and str(surface).casefold() != "not listed"
        },
        key=str.casefold,
    )
    labels_by_category: dict[str, set[str]] = {}
    for label in labels:
        for category in court_surface_categories(label):
            labels_by_category.setdefault(category, set()).add(label)

    st.caption(
        "Playing characteristics are general and vary by court construction, "
        "upkeep, weather and footwear."
    )
    for category in COURT_SURFACE_DESCRIPTIONS:
        if category not in labels_by_category:
            continue
        st.markdown(f"**{category}**")
        st.write(COURT_SURFACE_DESCRIPTIONS[category])
    if "Surface type not specified" in labels_by_category:
        st.markdown("**Surface type not specified**")
        st.write(
            "The club listing does not identify the court material. Ask the venue "
            "for details if pace, bounce or underfoot feel is important."
        )


def edit_club_details(clubs: list[dict[str, Any]]) -> None:
    st.subheader("Club details")
    st.caption(
        "Add or confirm routing addresses, neighbourhoods, official booking pages, prices, court types, "
        "and visitor-access rules. Unknown details are left blank rather than guessed."
    )
    editor_data = pd.DataFrame(
        [{field: club.get(field) for field in EDITABLE_FIELDS} for club in clubs]
    )
    edited = st.data_editor(
        editor_data,
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        key="club_details_editor",
        alt="Edit booking and price details for the tennis clubs",
        column_config={
            "name": st.column_config.TextColumn("Club", disabled=True),
            "address": st.column_config.TextColumn(
                "Routing address",
                help="Street address or venue name used for cycling-route estimates.",
            ),
            "neighborhood": st.column_config.TextColumn(
                "Neighbourhood / district",
                help="Broad area shown in the club table; this does not replace the routing address.",
            ),
            "club_website": st.column_config.TextColumn("Club website"),
            "booking_url": st.column_config.TextColumn("Booking page"),
            "booking_platform": st.column_config.TextColumn("Booking platform"),
            "price_info": st.column_config.TextColumn(
                "Price / court / hour (€)",
                help="Enter a price or range (for example €20–€25), or a note such as Included in membership.",
            ),
            "membership_price": st.column_config.TextColumn(
                "Senior membership price",
                help="Enter the published senior membership fee, billing period, and age requirement if available.",
            ),
            "court_type": st.column_config.TextColumn(
                "Court type", help="For example: outdoor clay, indoor hard court."
            ),
            "access_notes": st.column_config.TextColumn(
                "Access", help="For example: members only or public guest booking."
            ),
            "other_notes": st.column_config.TextColumn("Other info"),
        },
    )

    if st.button("Save club details"):
        try:
            updated_by_name = {
                record["name"]: normalize_club_record(record)
                for record in edited.to_dict("records")
            }
            updated_clubs = []
            for club in clubs:
                updated = {**club, **updated_by_name[club["name"]]}
                updated_clubs.append(updated)
            save_clubs(data_path(), updated_clubs)
        except (OSError, ValueError) as error:
            st.error(str(error))
        else:
            st.success("Club details saved locally.")
            st.rerun()


def calculate_routes(
    clubs: list[dict[str, Any]],
    origin: str,
    api_key: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    routes = {}
    failures = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "AmsterdamTennisCourtFinder/1.0"})
        for club in clubs:
            address = clean_optional_text(club.get("address"))
            if not address:
                failures.append(f"{club['name']}: add and confirm its street address first.")
                continue
            try:
                route = cycling_route(origin, address, api_key, session)
            except requests.RequestException as error:
                failures.append(
                    f"{club['name']}: {google_routes_error(error, api_key)}"
                )
                continue
            except ValueError as error:
                failures.append(f"{club['name']}: {error}")
                continue

            if route is None:
                failures.append(f"{club['name']}: no cycling route was returned.")
                continue
            minutes = route
            routes[club["name"]] = {
                "address": address,
                "minutes": minutes,
            }
    return routes, failures


def google_maps_setup_popover() -> None:
    with st.popover("How to setup", width=600):
        st.markdown(
            "#### Get a Google Maps API key\n"
            "1. Open the [Google Cloud Console](https://console.cloud.google.com/) "
            "and select a project, or create one.\n"
            "2. Enable billing for that project. Google Routes requires a billing "
            "account.\n"
            "3. In **APIs & Services → Library**, find **Routes API** and select "
            "**Enable**.\n"
            "4. In **APIs & Services → Credentials**, choose **Create credentials "
            "→ API key** and copy the key.\n"
            "5. Open the key’s settings and restrict it to **Routes API** under "
            "API restrictions. This dashboard makes requests from your computer, "
            "so HTTP-referrer restrictions are not appropriate.\n\n"
            "#### Add the key to Windows\n"
            "1. Search Windows for **Edit environment variables for your account** "
            "and open it.\n"
            "2. Under **User variables**, choose **New**. Set the variable name "
            "to `GOOGLE_MAPS_API_KEY` and paste your key as its value.\n"
            "3. Save the changes, then fully close and reopen VS Code and restart "
            "the dashboard. The dashboard reads the key when it starts.\n\n"
            "Keep the key private: do not put it in the app’s code, club data, "
            "screenshots, or Git. It is sent to Google only when you calculate "
            "cycling times."
        )


def save_home_address_input() -> None:
    st.session_state["home_address"] = st.session_state["home_address_input"].strip()


def clubs_for_access_group(
    clubs: list[dict[str, Any]],
    group: str,
) -> list[dict[str, Any]]:
    if group == "membership_options":
        return clubs
    return [
        club
        for club in clubs
        if (booking_access_label(club) == "Members only")
        == (group == "members")
    ]


def calculate_route_group(
    clubs: list[dict[str, Any]],
    group: str,
    origin: str,
    api_key: str,
) -> None:
    target_clubs = (
        clubs
        if group == "single_courts"
        else clubs_for_access_group(clubs, group)
    )
    current_origin = st.session_state.get("route_origin", "")
    same_origin = current_origin.strip() == origin.strip()
    routes = (
        dict(st.session_state.get("route_results", {}))
        if same_origin
        else {}
    )
    for club in target_clubs:
        routes.pop(club["name"], None)
    st.session_state["route_results"] = routes
    st.session_state["route_origin"] = origin.strip()
    st.session_state["home_address"] = origin.strip()
    if not same_origin:
        st.session_state["route_group_feedback"] = {}
    completed_groups = (
        set(st.session_state.get("route_calculated_groups", []))
        if same_origin
        else set()
    )
    completed_groups.discard(group)
    st.session_state["route_calculated_groups"] = sorted(completed_groups)

    try:
        calculated_routes, failures = calculate_routes(
            target_clubs,
            routing_origin(origin),
            api_key,
        )
    except requests.RequestException as error:
        feedback = {
            "kind": "error",
            "message": (
                "Google Routes request failed: "
                f"{google_routes_error(error, api_key)}"
            ),
            "failures": [],
        }
    else:
        routes.update(calculated_routes)
        st.session_state["route_results"] = routes
        completed_groups.add(group)
        st.session_state["route_calculated_groups"] = sorted(completed_groups)
        st.session_state["route_calculation_completed"] = True
        if calculated_routes:
            target_label = {
                "members": "members-only clubs",
                "single_courts": "single not-for-rent courts",
                "public": "public clubs",
                "membership_options": "clubs across both tables",
            }.get(group, "clubs")
            feedback = {
                "kind": "success",
                "message": (
                    f"Calculated cycling times for {len(calculated_routes)} "
                    f"{target_label}."
                ),
                "failures": failures,
            }
        else:
            feedback = {
                "kind": "error",
                "message": (
                    "No cycling times were calculated for this table. Review the "
                    "details below and confirm the API key, Google Routes API access, "
                    "billing, and club routing addresses."
                ),
                "failures": failures,
            }
    st.session_state["route_calculation_completed"] = bool(
        st.session_state["route_results"]
    )
    st.session_state.setdefault("route_group_feedback", {})[group] = feedback


@st.dialog("Cycling-time setup", width="small")
def cycling_time_setup_dialog(
    clubs: list[dict[str, Any]],
    group: str,
) -> None:
    target_label = {
        "members": "members-only clubs",
        "single_courts": "single not-for-rent courts",
        "public": "public clubs",
        "membership_options": "all clubs in the public and membership tables",
    }.get(group, "clubs")
    st.markdown(
        "Your starting address is shared by all tables. This button will "
        f"calculate cycling times for {target_label}."
    )
    if "home_address_input" not in st.session_state:
        st.session_state["home_address_input"] = st.session_state.get(
            "home_address", ""
        )
    origin = st.text_input(
        "Starting address",
        key="home_address_input",
        on_change=save_home_address_input,
        placeholder="e.g. Lepelstraat 2C",
        help="A street and house number are enough. Short addresses are interpreted as being in Amsterdam.",
    )
    google_maps_setup_popover()
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        st.warning(
            "Set GOOGLE_MAPS_API_KEY in your environment to calculate cycling "
            "routes. The key is not stored in this app."
        )
    consent = st.checkbox(
        "I agree to send my starting address and club addresses to Google Routes.",
        key="route_address_consent",
    )
    if st.button(
        "Calculate cycling times",
        key=f"calculate_{group}_routes_from_dialog",
        type="primary",
    ):
        missing_requirements = []
        if not api_key:
            missing_requirements.append(
                "The dashboard process cannot see GOOGLE_MAPS_API_KEY. "
                "Set it in the environment used to launch Streamlit, then "
                "restart VS Code (or its terminal) and the dashboard."
            )
        if not consent:
            missing_requirements.append(
                "Check the box to consent to sending the addresses to Google Routes."
            )
        if not origin.strip():
            missing_requirements.append(
                "Enter a starting address, for example 'Lepelstraat 2C'."
            )
        if missing_requirements:
            st.error(
                "Cycling times were not requested:\n\n"
                + "\n".join(f"- {item}" for item in missing_requirements),
                title="Complete the cycling-time setup",
            )
            return

        calculate_route_group(clubs, group, origin, api_key)
        st.rerun()


def apply_dashboard_background() -> None:
    background_path = Path(__file__).with_name("tennis_court_background.svg")
    background_data = base64.b64encode(background_path.read_bytes()).decode("ascii")
    st.html(
        f"""
        <style>
          [data-testid="stAppViewContainer"] {{
            background:
              linear-gradient(120deg, rgba(8, 29, 27, 0.70), rgba(11, 37, 34, 0.78)),
              url("data:image/svg+xml;base64,{background_data}") center / cover fixed;
          }}
          [data-testid="stHeader"] {{
            background: rgba(8, 29, 27, 0.18);
          }}
          [data-testid="stMain"] {{
            background: transparent;
          }}
          [data-testid="stMainBlockContainer"] {{
            max-width: 1440px;
            margin-top: 1.25rem;
            margin-right: auto;
            margin-bottom: 2rem;
            margin-left: auto;
            padding: 2rem clamp(1rem, 3vw, 3rem) 3rem;
            border: 1px solid rgba(255, 255, 255, 0.45);
            border-radius: 1.25rem;
            background: rgba(250, 252, 249, 0.86);
            box-shadow: 0 1.5rem 4rem rgba(4, 20, 18, 0.22);
            backdrop-filter: blur(2px);
          }}
          [data-testid="stSidebar"] {{
            background: rgba(248, 251, 247, 0.96);
          }}
          .st-key-amsterdam_weather_forecast {{
            background: rgba(229, 239, 230, 0.68);
            border-radius: 0.75rem;
          }}
          .st-key-calculate_public_routes button,
          .st-key-calculate_members_routes button,
          .st-key-calculate_single_court_routes button,
          .st-key-calculate_public_routes_from_dialog button,
          .st-key-calculate_members_routes_from_dialog button,
          .st-key-calculate_membership_options_routes_from_dialog button,
          .st-key-calculate_single_courts_routes_from_dialog button {{
            background-color: #173B67;
            border-color: #173B67;
            color: #FFFFFF;
          }}
          .st-key-calculate_public_routes button:hover,
          .st-key-calculate_members_routes button:hover,
          .st-key-calculate_single_court_routes button:hover,
          .st-key-calculate_public_routes_from_dialog button:hover,
          .st-key-calculate_members_routes_from_dialog button:hover,
          .st-key-calculate_membership_options_routes_from_dialog button:hover,
          .st-key-calculate_single_courts_routes_from_dialog button:hover {{
            background-color: #102B4C;
            border-color: #102B4C;
            color: #FFFFFF;
          }}
          .st-key-booking_portal_credentials button {{
            background-color: #B42318;
            border-color: #B42318;
            color: #FFFFFF;
          }}
          .st-key-booking_portal_credentials button:hover {{
            background-color: #912018;
            border-color: #912018;
            color: #FFFFFF;
          }}
        </style>
        """
    )


def main() -> None:
    apply_dashboard_background()
    title_column, image_column = st.columns([0.78, 0.22], vertical_alignment="center")
    with title_column:
        st.title("Amsterdam Court Finder", icon=":material/sports_tennis:")
        st.markdown(
            "Trouble finding the right tennis club for you? No worries, we've got "
            "your back. Explore clubs across Amsterdam, whether you're looking for "
            "an occasional match or a longer-term commitment. Compare locations, "
            "cycling times and prices, explore membership options, and check "
            "availability for your chosen date, time and session length—all in "
            "one place."
        )
    with image_column:
        st.image(
            Path(__file__).with_name("tennis_hero.svg"),
            alt="Illustration of a tennis racket and ball",
            width="stretch",
        )
    try:
        clubs = load_clubs(data_path())
    except ValueError as error:
        st.error(str(error))
        st.stop()

    if "home_address" not in st.session_state:
        st.session_state["home_address"] = os.environ.get(
            "TENNIS_FINDER_HOME_ADDRESS", ""
        )
    if "route_results" not in st.session_state:
        st.session_state["route_results"] = {}
    if "route_origin" not in st.session_state:
        st.session_state["route_origin"] = ""
    if "availability_results" not in st.session_state:
        st.session_state["availability_results"] = {}
    if "availability_check_started" not in st.session_state:
        st.session_state["availability_check_started"] = False
    if "route_calculation_feedback" not in st.session_state:
        st.session_state["route_calculation_feedback"] = None
    if "route_calculation_completed" not in st.session_state:
        st.session_state["route_calculation_completed"] = bool(
            st.session_state["route_results"] and st.session_state["route_origin"]
        )
    if "route_calculated_groups" not in st.session_state:
        st.session_state["route_calculated_groups"] = (
            ["members", "public"]
            if st.session_state["route_calculation_completed"]
            else []
        )
    if "route_group_feedback" not in st.session_state:
        st.session_state["route_group_feedback"] = {}

    st.subheader("🔓 Public (non-member) clubs")
    today = date.today()
    next_day = today + timedelta(days=1)
    controls_column, weather_column = st.columns(
        [1, 2],
        gap="medium",
        vertical_alignment="top",
    )
    with controls_column:
        selected_date = st.date_input(
            "Booking date",
            value=next_day,
            min_value=today,
            key="booking_date",
        )
        selected_time = st.time_input(
            "Start time",
            value=time(18, 0),
            step=timedelta(minutes=15),
            key="booking_start_time",
        )
        duration_minutes = st.segmented_control(
            "Duration",
            options=(60, 90),
            default=60,
            format_func=lambda minutes: f"{minutes} minutes",
            key="duration_minutes",
        )
        start = datetime.combine(selected_date, selected_time)
        end = start + timedelta(minutes=duration_minutes)
        st.caption(
            f"Requested slot: 1 court · {start:%A %d %B %Y} · "
            f"{start:%H:%M}–{end:%H:%M}"
        )
    with weather_column:
        recommended_environment = show_amsterdam_weather(
            selected_date,
            selected_time,
        )

    saved_credentials = st.session_state.get("availability_portal_credentials")
    with st.container(
        horizontal=True,
        gap="small",
        horizontal_alignment="left",
        vertical_alignment="bottom",
        wrap=False,
    ):
        with st.container(width="content"):
            check_availability_clicked = booking_browser_controls(
                clubs,
                st,
            )
        if st.button(
            "Calculate cycling times",
            key="calculate_public_routes",
        ):
            origin = st.session_state.get("home_address", "").strip()
            api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
            if origin and st.session_state.get("route_address_consent") and api_key:
                with st.spinner("Calculating public-club cycling times..."):
                    calculate_route_group(clubs, "public", origin, api_key)
            else:
                cycling_time_setup_dialog(clubs, "public")
        show_public_surface = st.button(
            "Court surface info",
            key="public_court_surface_info",
        )
        if saved_credentials:
            if st.button(
                "Update credentials",
                key="update_booking_credentials",
            ):
                available_clubs = [
                    item for item in clubs if item["name"] in BROWSER_CHECK_CLUBS
                ]
                availability_credentials_dialog(
                    available_clubs,
                    selected_date,
                    selected_time,
                    int(duration_minutes),
                )
            if st.button(
                "Forget saved credentials",
                key="forget_booking_credentials",
            ):
                st.session_state.pop("availability_portal_credentials", None)
                st.rerun()

    if check_availability_clicked:
        available_clubs = [
            item for item in clubs if item["name"] in BROWSER_CHECK_CLUBS
        ]
        if saved_credentials:
            st.session_state["availability_check_started"] = True
            try:
                with st.spinner("Checking all public (non-member) clubs..."):
                    run_availability_checks(
                        available_clubs,
                        selected_date,
                        selected_time,
                        int(duration_minutes),
                        saved_credentials,
                    )
            except (
                OSError,
                RuntimeError,
                TimeoutError,
                subprocess.TimeoutExpired,
            ) as error:
                st.session_state["availability_check_failures"] = {
                    "All configured clubs": str(error)
                }
            st.rerun()
        else:
            availability_credentials_dialog(
                available_clubs,
                selected_date,
                selected_time,
                int(duration_minutes),
            )

    for club_name, error in st.session_state.pop(
        "availability_check_failures", {}
    ).items():
        st.error(f"Could not check {club_name}: {error}")
    with st.container(
        horizontal=True,
        gap="small",
        horizontal_alignment="left",
    ):
        if st.session_state.get("home_address", "").strip():
            if st.button(
                "Forget street address",
                key="forget_home_address",
            ):
                st.session_state["home_address"] = ""
                st.session_state.pop("home_address_input", None)
                st.session_state["route_origin"] = ""
                st.session_state["route_results"] = {}
                st.session_state["route_calculated_groups"] = []
                st.session_state["route_group_feedback"] = {}
                st.session_state["route_calculation_completed"] = False
                st.session_state["route_address_consent"] = False
                st.rerun()
    if saved_credentials:
        st.caption("Booking-portal credentials are available for this app session.")

    requested_slot = booking_slot_key(
        selected_date,
        selected_time,
        int(duration_minutes),
    )
    comparison = display_clubs(
        clubs,
        st.session_state["route_results"],
        st.session_state["home_address"].strip(),
        st.session_state["route_origin"],
        st.session_state["availability_results"],
        requested_slot,
    )
    public_clubs = comparison[
        comparison["Booking access"] != "Members only"
    ].drop(
        columns=[
            "Booking access",
            "Membership price",
            "Club site",
            "Introducé allowed?",
            "Introducé price",
            "Waiting list",
        ]
    )[
        [
            "Club",
            "Neighbourhood",
            "Cycling time",
            "Availability",
            "Available type",
            "Price / court / hour (€)",
            "Court surface",
            "Booking page",
            "Other info",
        ]
    ]
    members_only_clubs = comparison[
        comparison["Booking access"] == "Members only"
    ][
        [
            "Club",
            "Neighbourhood",
            "Cycling time",
            "Membership price",
            "Waiting list",
            "Court surface",
            "Introducé allowed?",
            "Introducé price",
            "Other info",
            "Club site",
        ]
    ]
    members_only_clubs.insert(1, "Booking access", "🔒Member only")
    public_member_clubs = comparison[
        comparison["Booking access"] != "Members only"
    ][
        [
            "Club",
            "Neighbourhood",
            "Cycling time",
            "Membership price",
            "Waiting list",
            "Court surface",
            "Introducé allowed?",
            "Introducé price",
            "Other info",
            "Club site",
        ]
    ].copy()
    public_member_clubs.insert(1, "Booking access", "🔒Member+🔓Non-Member")
    public_member_clubs["Introducé allowed?"] = "Not applicable"
    public_member_clubs["Introducé price"] = "Not applicable"
    members_only_clubs = pd.concat(
        [members_only_clubs, public_member_clubs],
        ignore_index=True,
    )
    members_only_clubs["Other info"] = members_only_clubs.apply(
        lambda row: membership_table_other_info(
            row["Club"],
            row["Other info"],
        ),
        axis=1,
    )
    capacity_info = members_only_clubs["Club"].map(MEMBERSHIP_CAPACITY_INFO)
    insertion_index = members_only_clubs.columns.get_loc("Membership price") + 1
    members_only_clubs.insert(
        insertion_index,
        "Members (approx.)",
        capacity_info.map(lambda info: membership_capacity_value(info, "members")),
    )
    members_only_clubs.insert(
        insertion_index + 1,
        "Courts",
        capacity_info.map(lambda info: membership_capacity_value(info, "courts")),
    )
    members_only_clubs.insert(
        insertion_index + 2,
        "Ratio (members/court)",
        capacity_info.map(lambda info: membership_capacity_value(info, "ratio")),
    )
    if show_public_surface:
        show_court_surface_info(public_clubs)

    public_feedback = st.session_state["route_group_feedback"].get("public")
    if public_feedback:
        if public_feedback["kind"] == "success":
            st.success(public_feedback["message"])
        else:
            st.error(public_feedback["message"], title="Cycling-time calculation failed")
        for failure in public_feedback["failures"]:
            st.warning(failure)
    st.dataframe(
        style_club_rows(public_clubs, recommended_environment),
        hide_index=True,
        alt="Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information",
        column_config={
            "Available type": st.column_config.TextColumn(
                "Available type",
                help="Types of court available for the selected time, including outdoor, indoor, or covered.",
            ),
            "Booking page": st.column_config.LinkColumn(
                "Booking page", display_text="Open booking page"
            ),
        },
    )
    availability_search_explanation()

    st.subheader("🔒 Membership options")
    st.write(
        "Looking for a longer-term commitment? Explore these club membership "
        "options below."
    )
    with st.container(horizontal=True, gap="small", vertical_alignment="bottom"):
        if st.button(
            "Calculate cycling times",
            key="calculate_members_routes",
        ):
            origin = st.session_state.get("home_address", "").strip()
            api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
            if origin and st.session_state.get("route_address_consent") and api_key:
                with st.spinner("Calculating cycling times for both tables..."):
                    calculate_route_group(
                        clubs,
                        "membership_options",
                        origin,
                        api_key,
                    )
            else:
                cycling_time_setup_dialog(clubs, "membership_options")
        if st.button(
            "Court surface info",
            key="membership_court_surface_info",
        ):
            show_court_surface_info(members_only_clubs)

    if any(
        group in st.session_state["route_calculated_groups"]
        for group in ("members", "membership_options")
    ):
        members_only_clubs = members_only_clubs.assign(
            _cycling_minutes=members_only_clubs["Cycling time"].map(
                lambda value: int(match.group(1))
                if (match := re.match(r"(\d+)\s+min\b", str(value)))
                else float("inf")
            ),
            _membership_price=members_only_clubs["Membership price"].map(
                lambda value: float(match.group(1).replace(",", "."))
                if (
                    match := re.search(
                        r"€\s*(\d+(?:[.,]\d{1,2})?)",
                        str(value),
                    )
                )
                else float("inf")
            ),
        ).sort_values(
            ["_cycling_minutes", "_membership_price"],
            kind="stable",
        ).drop(columns=["_cycling_minutes", "_membership_price"])
    else:
        members_only_clubs = members_only_clubs.assign(
            _membership_price=members_only_clubs["Membership price"].map(
                lambda value: float(match.group(1).replace(",", "."))
                if (
                    match := re.search(
                        r"€\s*(\d+(?:[.,]\d{1,2})?)",
                        str(value),
                    )
                )
                else float("inf")
            )
        ).sort_values("_membership_price", kind="stable").drop(
            columns="_membership_price"
        )
    members_feedback = st.session_state["route_group_feedback"].get(
        "membership_options"
    ) or st.session_state["route_group_feedback"].get("members")
    if members_feedback:
        if members_feedback["kind"] == "success":
            st.success(members_feedback["message"])
        else:
            st.error(
                members_feedback["message"],
                title="Cycling-time calculation failed",
            )
        for failure in members_feedback["failures"]:
            st.warning(failure)
    st.caption(
        "Row background: green = no waiting list; red = waiting list. "
        "Membership-price text: green ≤ €200, amber €201–€275, red > €275; "
        "cycling-time text retains its travel-time color coding."
    )
    st.caption(
        "Members per court: green ≤75, yellow 76–150, red >150. "
        "Club membership and court figures are approximate where noted."
    )
    st.dataframe(
        style_club_rows(members_only_clubs),
        hide_index=True,
        alt="Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites",
        column_config={
            "Club site": st.column_config.LinkColumn(
                "Club site", display_text="Open club site"
            ),
            "Ratio (members/court)": st.column_config.TextColumn(
                "Ratio (members/court)",
                help=(
                    "Approximate members per tennis court. Green ≤75, yellow "
                    "76–150, red >150; ranges use their lower value for coloring."
                ),
            ),
        },
    )


    st.subheader("Stand-alone courts")
    st.write(
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. "
        "These courts cannot be booked in advance."
    )
    if st.button(
        "Calculate cycling times",
        key="calculate_single_court_routes",
    ):
        origin = st.session_state.get("home_address", "").strip()
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
        if origin and st.session_state.get("route_address_consent") and api_key:
            with st.spinner("Calculating cycling times for single courts..."):
                calculate_route_group(
                    list(SINGLE_NOT_FOR_RENT_COURTS),
                    "single_courts",
                    origin,
                    api_key,
                )
        else:
            cycling_time_setup_dialog(
                list(SINGLE_NOT_FOR_RENT_COURTS),
                "single_courts",
            )

    single_court_feedback = st.session_state["route_group_feedback"].get(
        "single_courts"
    )
    if single_court_feedback:
        if single_court_feedback["kind"] == "success":
            st.success(single_court_feedback["message"])
        else:
            st.error(
                single_court_feedback["message"],
                title="Cycling-time calculation failed",
            )
        for failure in single_court_feedback["failures"]:
            st.warning(failure)

    current_origin = st.session_state.get("home_address", "").strip()
    current_routes = (
        st.session_state["route_results"]
        if current_origin == st.session_state["route_origin"].strip()
        else {}
    )
    single_court_rows = []
    for court in SINGLE_NOT_FOR_RENT_COURTS:
        route = current_routes.get(court["name"], {})
        route_minutes = (
            float(route["minutes"])
            if route.get("address") == court["address"]
            and route.get("minutes") is not None
            else float("inf")
        )
        minutes = (
            f"{route_minutes:.0f} min"
            if math.isfinite(route_minutes)
            else "Not calculated"
        )
        single_court_rows.append(
            {
                "Court": court["name"],
                "Neighbourhood": court["neighborhood"],
                "Address": court["address"],
                "Court surface": court["court_surface"],
                "Cycling time": minutes,
                "_cycling_minutes": route_minutes,
            }
        )
    single_courts = (
        pd.DataFrame(single_court_rows)
        .sort_values("_cycling_minutes", kind="stable")
        .drop(columns="_cycling_minutes")
    )
    st.dataframe(
        style_club_rows(single_courts),
        hide_index=True,
        alt="Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times",
    )


if __name__ == "__main__":
    main()
