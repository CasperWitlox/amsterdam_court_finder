"""Localization and filtering helpers for the Amsterdam Court Finder UI."""

from __future__ import annotations

import re
from typing import Any


DUTCH_TRANSLATIONS = {
    "Language / Taal": "Taal / Language",
    "English": "Engels",
    "Nederlands": "Nederlands",
    "ascending": "oplopend",
    "descending": "aflopend",
    "court": "baan",
    "Court": "Baan",
    "Available courts": "Beschikbare banen",
    "Booking platform": "Boekingsplatform",
    "Privacy & data": "Privacy en gegevens",
    "Sponsored": "Gesponsord",
    "Visit sponsor": "Bekijk sponsor",
    "Browse directory": "Bekijk de gids",
    "Advertise with us": "Adverteer bij ons",
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

SUPPORTED_LANGUAGES = (
    "English",
    "Nederlands",
    "中文 (简体)",
    "हिन्दी",
    "Español",
    "Français",
    "العربية",
    "বাংলা",
    "Português",
    "Русский",
)

ADDITIONAL_TRANSLATIONS = {
    "中文 (简体)": {
        "Booking date": "预订日期",
        "Start time": "开始时间",
        "Duration": "时长",
        "minutes": "分钟",
        "Requested slot": "所选时段",
        "court": "球场",
        "Check availability": "查看空位",
        "Availability": "可订状态",
        "Cycling time": "骑行时间",
        "Available type": "可用球场类型",
        "Booking access": "预订权限",
        "Price / court / hour (€)": "每小时每片球场价格 (€)",
        "Court surface": "场地类型",
        "Booking page": "预订页面",
        "Other info": "其他信息",
        "Membership price": "会员费用",
        "Senior membership price": "高级会员费用",
        "Waiting list": "候补名单",
        "Club site": "俱乐部网站",
        "Members (approx.)": "会员人数（约）",
        "Courts": "球场数",
        "Ratio (members/court)": "每片球场会员数",
        "Stand-alone courts": "公共网球场",
        "Address": "地址",
        "Privacy & data": "隐私与数据",
        "Club profiles": "俱乐部简介",
        "Choose a club": "选择俱乐部",
        "Filter clubs": "筛选俱乐部",
        "Neighbourhoods": "街区",
        "Court surfaces": "场地类型",
        "Availability filter": "可订状态",
        "Maximum cycling time (minutes)": "最长骑行时间（分钟）",
        "All availability": "所有状态",
        "Available": "有空位",
        "Unavailable": "无空位",
        "Could not verify": "无法确认",
        "Too early to check": "尚未开放查询",
        "Not checked": "尚未检查",
        "Other status": "其他状态",
        "Showing {shown} of {total} clubs.": "显示 {total} 家俱乐部中的 {shown} 家。",
        "No clubs match these filters.": "没有符合这些筛选条件的俱乐部。",
        "Available courts": "可用球场",
        "Booking platform": "预订平台",
        "Last checked": "上次检查",
        "Open booking page": "打开预订页面",
        "Official club website": "俱乐部官方网站",
        "Availability can change; confirm the slot on the club's booking page.": "空位可能随时变化，请在俱乐部预订页面确认。",
        "Amsterdam weather forecast": "阿姆斯特丹天气预报",
        "Temperature": "气温",
        "Precipitation chance": "降水概率",
        "Wind": "风速",
        "Expected rainfall": "预计降雨量",
        "Indoor": "室内",
        "Outdoor": "室外",
        "Recommended court:": "建议球场：",
        "Membership options": "会员选项",
        "🔒 Membership options": "🔒 会员选项",
        "Sort table by": "排序方式",
        "Sort order": "排序顺序",
        "Calculate cycling times": "计算骑行时间",
        "Court surface info": "场地类型说明",
        "Update credentials": "更新登录信息",
        "Forget saved credentials": "清除已保存的登录信息",
        "Forget street address": "清除起始地址",
        "How availability is checked": "空位查询方式",
        "Public (non-members)": "对非会员开放",
        "Members only": "仅限会员",
        "Not specified": "未注明",
        "Not listed": "未列出",
        "Not calculated": "未计算",
        "Available - selectable on the booking page": "有空位 - 可在预订页面选择",
        "✅ Available": "✅ 有空位",
        "Not checked for this slot": "尚未检查此时段",
        "Could not verify - ": "无法确认 - ",
        "☀️ Outdoor": "☀️ 室外",
        "🏠 Indoor": "🏠 室内",
        "⛱️ Covered": "⛱️ 有顶棚",
        "Club": "俱乐部",
        "Neighbourhood": "街区",
    },
    "हिन्दी": {
        "Booking date": "बुकिंग की तारीख",
        "Start time": "शुरू होने का समय",
        "Duration": "अवधि",
        "minutes": "मिनट",
        "Requested slot": "चुना हुआ समय",
        "court": "कोर्ट",
        "Check availability": "उपलब्धता देखें",
        "Availability": "उपलब्धता",
        "Cycling time": "साइकिल से समय",
        "Available type": "उपलब्ध कोर्ट का प्रकार",
        "Booking access": "बुकिंग की सुविधा",
        "Price / court / hour (€)": "प्रति कोर्ट प्रति घंटे का शुल्क (€)",
        "Court surface": "कोर्ट की सतह",
        "Booking page": "बुकिंग पेज",
        "Other info": "अन्य जानकारी",
        "Membership price": "सदस्यता शुल्क",
        "Senior membership price": "वरिष्ठ सदस्यता शुल्क",
        "Waiting list": "प्रतीक्षा सूची",
        "Club site": "क्लब की वेबसाइट",
        "Members (approx.)": "सदस्य (लगभग)",
        "Courts": "कोर्ट",
        "Ratio (members/court)": "प्रति कोर्ट सदस्य",
        "Stand-alone courts": "सार्वजनिक टेनिस कोर्ट",
        "Address": "पता",
        "Privacy & data": "गोपनीयता और डेटा",
        "Club profiles": "क्लब प्रोफ़ाइल",
        "Choose a club": "क्लब चुनें",
        "Filter clubs": "क्लब फ़िल्टर करें",
        "Neighbourhoods": "इलाके",
        "Court surfaces": "कोर्ट की सतह",
        "Availability filter": "उपलब्धता",
        "Maximum cycling time (minutes)": "अधिकतम साइकिल समय (मिनट)",
        "All availability": "सभी स्थितियाँ",
        "Available": "उपलब्ध",
        "Unavailable": "उपलब्ध नहीं",
        "Could not verify": "पुष्टि नहीं हो सकी",
        "Too early to check": "जाँच के लिए अभी जल्दी है",
        "Not checked": "जाँच नहीं हुई",
        "Other status": "अन्य स्थिति",
        "Showing {shown} of {total} clubs.": "{total} में से {shown} क्लब दिखाए जा रहे हैं।",
        "No clubs match these filters.": "इन फ़िल्टर से कोई क्लब मेल नहीं खाता।",
        "Available courts": "उपलब्ध कोर्ट",
        "Booking platform": "बुकिंग प्लेटफ़ॉर्म",
        "Last checked": "अंतिम जाँच",
        "Open booking page": "बुकिंग पेज खोलें",
        "Official club website": "क्लब की आधिकारिक वेबसाइट",
        "Availability can change; confirm the slot on the club's booking page.": "उपलब्धता बदल सकती है; क्लब के बुकिंग पेज पर समय की पुष्टि करें।",
        "Amsterdam weather forecast": "एम्स्टर्डम का मौसम पूर्वानुमान",
        "Temperature": "तापमान",
        "Precipitation chance": "बारिश की संभावना",
        "Wind": "हवा",
        "Expected rainfall": "अनुमानित बारिश",
        "Indoor": "इनडोर",
        "Outdoor": "आउटडोर",
        "Recommended court:": "अनुशंसित कोर्ट:",
        "Membership options": "सदस्यता विकल्प",
        "🔒 Membership options": "🔒 सदस्यता विकल्प",
        "Sort table by": "तालिका क्रमबद्ध करें",
        "Sort order": "क्रम",
        "Calculate cycling times": "साइकिल समय की गणना करें",
        "Court surface info": "कोर्ट की सतह की जानकारी",
        "Update credentials": "लॉगिन जानकारी बदलें",
        "Forget saved credentials": "सहेजी गई लॉगिन जानकारी मिटाएँ",
        "Forget street address": "शुरुआती पता मिटाएँ",
        "How availability is checked": "उपलब्धता की जाँच कैसे होती है",
        "Public (non-members)": "गैर-सदस्यों के लिए खुला",
        "Members only": "केवल सदस्य",
        "Not specified": "निर्दिष्ट नहीं",
        "Not listed": "सूचीबद्ध नहीं",
        "Not calculated": "गणना नहीं हुई",
        "Available - selectable on the booking page": "उपलब्ध - बुकिंग पेज पर चुना जा सकता है",
        "✅ Available": "✅ उपलब्ध",
        "Not checked for this slot": "इस समय की जाँच नहीं हुई",
        "Could not verify - ": "पुष्टि नहीं हो सकी - ",
        "☀️ Outdoor": "☀️ आउटडोर",
        "🏠 Indoor": "🏠 इनडोर",
        "⛱️ Covered": "⛱️ ढका हुआ",
        "Club": "क्लब",
        "Neighbourhood": "इलाका",
    },
    "Español": {
        "Booking date": "Fecha de reserva",
        "Start time": "Hora de inicio",
        "Duration": "Duración",
        "minutes": "minutos",
        "Requested slot": "Horario elegido",
        "court": "pista",
        "Check availability": "Consultar disponibilidad",
        "Availability": "Disponibilidad",
        "Cycling time": "Tiempo en bicicleta",
        "Available type": "Tipo de pista disponible",
        "Booking access": "Acceso a reservas",
        "Price / court / hour (€)": "Precio por pista y hora (€)",
        "Court surface": "Superficie de la pista",
        "Booking page": "Página de reservas",
        "Other info": "Otra información",
        "Membership price": "Precio de la membresía",
        "Senior membership price": "Precio de membresía sénior",
        "Waiting list": "Lista de espera",
        "Club site": "Web del club",
        "Members (approx.)": "Socios (aprox.)",
        "Courts": "Pistas",
        "Ratio (members/court)": "Socios por pista",
        "Stand-alone courts": "Pistas públicas de tenis",
        "Address": "Dirección",
        "Privacy & data": "Privacidad y datos",
        "Club profiles": "Perfiles de clubes",
        "Choose a club": "Elige un club",
        "Filter clubs": "Filtrar clubes",
        "Neighbourhoods": "Barrios",
        "Court surfaces": "Superficies",
        "Availability filter": "Disponibilidad",
        "Maximum cycling time (minutes)": "Tiempo máximo en bicicleta (minutos)",
        "All availability": "Todos los estados",
        "Available": "Disponible",
        "Unavailable": "No disponible",
        "Could not verify": "No se pudo verificar",
        "Too early to check": "Aún no se puede consultar",
        "Not checked": "Sin consultar",
        "Other status": "Otro estado",
        "Showing {shown} of {total} clubs.": "Se muestran {shown} de {total} clubes.",
        "No clubs match these filters.": "Ningún club coincide con estos filtros.",
        "Available courts": "Pistas disponibles",
        "Booking platform": "Plataforma de reservas",
        "Last checked": "Última consulta",
        "Open booking page": "Abrir página de reservas",
        "Official club website": "Web oficial del club",
        "Availability can change; confirm the slot on the club's booking page.": "La disponibilidad puede cambiar; confirma la pista en la página de reservas.",
        "Amsterdam weather forecast": "Previsión meteorológica de Ámsterdam",
        "Temperature": "Temperatura",
        "Precipitation chance": "Probabilidad de lluvia",
        "Wind": "Viento",
        "Expected rainfall": "Lluvia prevista",
        "Indoor": "Interior",
        "Outdoor": "Exterior",
        "Recommended court:": "Pista recomendada:",
        "Membership options": "Opciones de membresía",
        "🔒 Membership options": "🔒 Opciones de membresía",
        "Sort table by": "Ordenar tabla por",
        "Sort order": "Orden",
        "Calculate cycling times": "Calcular tiempos en bicicleta",
        "Court surface info": "Información sobre superficies",
        "Update credentials": "Actualizar credenciales",
        "Forget saved credentials": "Borrar credenciales guardadas",
        "Forget street address": "Borrar dirección de origen",
        "How availability is checked": "Cómo se consulta la disponibilidad",
        "Public (non-members)": "Abierto a no socios",
        "Members only": "Solo socios",
        "Not specified": "No especificado",
        "Not listed": "No indicado",
        "Not calculated": "Sin calcular",
        "Available - selectable on the booking page": "Disponible - seleccionable en la página de reservas",
        "✅ Available": "✅ Disponible",
        "Not checked for this slot": "No consultado para este horario",
        "Could not verify - ": "No se pudo verificar - ",
        "☀️ Outdoor": "☀️ Exterior",
        "🏠 Indoor": "🏠 Interior",
        "⛱️ Covered": "⛱️ Cubierta",
        "Club": "Club",
        "Neighbourhood": "Barrio",
    },
    "Français": {
        "Booking date": "Date de réservation",
        "Start time": "Heure de début",
        "Duration": "Durée",
        "minutes": "minutes",
        "Requested slot": "Créneau choisi",
        "court": "court",
        "Check availability": "Vérifier les disponibilités",
        "Availability": "Disponibilité",
        "Cycling time": "Temps à vélo",
        "Available type": "Type de court disponible",
        "Booking access": "Accès à la réservation",
        "Price / court / hour (€)": "Prix par court et par heure (€)",
        "Court surface": "Surface du court",
        "Booking page": "Page de réservation",
        "Other info": "Autres informations",
        "Membership price": "Prix de l'adhésion",
        "Senior membership price": "Tarif d'adhésion senior",
        "Waiting list": "Liste d'attente",
        "Club site": "Site du club",
        "Members (approx.)": "Membres (approx.)",
        "Courts": "Courts",
        "Ratio (members/court)": "Membres par court",
        "Stand-alone courts": "Courts de tennis publics",
        "Address": "Adresse",
        "Privacy & data": "Confidentialité et données",
        "Club profiles": "Profils des clubs",
        "Choose a club": "Choisir un club",
        "Filter clubs": "Filtrer les clubs",
        "Neighbourhoods": "Quartiers",
        "Court surfaces": "Surfaces des courts",
        "Availability filter": "Disponibilité",
        "Maximum cycling time (minutes)": "Temps de trajet à vélo maximal (minutes)",
        "All availability": "Tous les statuts",
        "Available": "Disponible",
        "Unavailable": "Indisponible",
        "Could not verify": "Vérification impossible",
        "Too early to check": "Consultation pas encore ouverte",
        "Not checked": "Non vérifié",
        "Other status": "Autre statut",
        "Showing {shown} of {total} clubs.": "{shown} clubs affichés sur {total}.",
        "No clubs match these filters.": "Aucun club ne correspond à ces filtres.",
        "Available courts": "Courts disponibles",
        "Booking platform": "Plateforme de réservation",
        "Last checked": "Dernière vérification",
        "Open booking page": "Ouvrir la page de réservation",
        "Official club website": "Site officiel du club",
        "Availability can change; confirm the slot on the club's booking page.": "Les disponibilités peuvent changer ; confirmez le créneau sur la page du club.",
        "Amsterdam weather forecast": "Prévisions météo d'Amsterdam",
        "Temperature": "Température",
        "Precipitation chance": "Risque de précipitations",
        "Wind": "Vent",
        "Expected rainfall": "Pluie prévue",
        "Indoor": "Intérieur",
        "Outdoor": "Extérieur",
        "Recommended court:": "Court recommandé :",
        "Membership options": "Options d'adhésion",
        "🔒 Membership options": "🔒 Options d'adhésion",
        "Sort table by": "Trier le tableau par",
        "Sort order": "Ordre de tri",
        "Calculate cycling times": "Calculer les temps à vélo",
        "Court surface info": "Informations sur les surfaces",
        "Update credentials": "Modifier les identifiants",
        "Forget saved credentials": "Effacer les identifiants enregistrés",
        "Forget street address": "Effacer l'adresse de départ",
        "How availability is checked": "Comment la disponibilité est vérifiée",
        "Public (non-members)": "Ouvert aux non-membres",
        "Members only": "Membres uniquement",
        "Not specified": "Non précisé",
        "Not listed": "Non renseigné",
        "Not calculated": "Non calculé",
        "Available - selectable on the booking page": "Disponible - sélectionnable sur la page de réservation",
        "✅ Available": "✅ Disponible",
        "Not checked for this slot": "Non vérifié pour ce créneau",
        "Could not verify - ": "Vérification impossible - ",
        "☀️ Outdoor": "☀️ Extérieur",
        "🏠 Indoor": "🏠 Intérieur",
        "⛱️ Covered": "⛱️ Couvert",
        "Club": "Club",
        "Neighbourhood": "Quartier",
    },
    "العربية": {
        "Booking date": "تاريخ الحجز",
        "Start time": "وقت البدء",
        "Duration": "المدة",
        "minutes": "دقائق",
        "Requested slot": "الفترة المختارة",
        "court": "ملعب",
        "Check availability": "تحقق من التوفر",
        "Availability": "التوفر",
        "Cycling time": "مدة ركوب الدراجة",
        "Available type": "نوع الملعب المتاح",
        "Booking access": "إمكانية الحجز",
        "Price / court / hour (€)": "السعر لكل ملعب في الساعة (€)",
        "Court surface": "نوع أرضية الملعب",
        "Booking page": "صفحة الحجز",
        "Other info": "معلومات أخرى",
        "Membership price": "رسوم العضوية",
        "Senior membership price": "رسوم عضوية كبار السن",
        "Waiting list": "قائمة الانتظار",
        "Club site": "موقع النادي",
        "Members (approx.)": "الأعضاء (تقريباً)",
        "Courts": "الملاعب",
        "Ratio (members/court)": "الأعضاء لكل ملعب",
        "Stand-alone courts": "ملاعب تنس عامة",
        "Address": "العنوان",
        "Privacy & data": "الخصوصية والبيانات",
        "Club profiles": "ملفات الأندية",
        "Choose a club": "اختر نادياً",
        "Filter clubs": "تصفية الأندية",
        "Neighbourhoods": "الأحياء",
        "Court surfaces": "أنواع الأرضيات",
        "Availability filter": "التوفر",
        "Maximum cycling time (minutes)": "أقصى مدة لركوب الدراجة (دقائق)",
        "All availability": "كل الحالات",
        "Available": "متاح",
        "Unavailable": "غير متاح",
        "Could not verify": "تعذّر التحقق",
        "Too early to check": "لم يحن وقت التحقق بعد",
        "Not checked": "لم يتم التحقق",
        "Other status": "حالة أخرى",
        "Showing {shown} of {total} clubs.": "عرض {shown} من أصل {total} نادياً.",
        "No clubs match these filters.": "لا توجد أندية تطابق عوامل التصفية.",
        "Available courts": "الملاعب المتاحة",
        "Booking platform": "منصة الحجز",
        "Last checked": "آخر تحقق",
        "Open booking page": "افتح صفحة الحجز",
        "Official club website": "الموقع الرسمي للنادي",
        "Availability can change; confirm the slot on the club's booking page.": "قد يتغير التوفر؛ يرجى تأكيد الفترة في صفحة الحجز الخاصة بالنادي.",
        "Amsterdam weather forecast": "توقعات الطقس في أمستردام",
        "Temperature": "درجة الحرارة",
        "Precipitation chance": "احتمال هطول الأمطار",
        "Wind": "الرياح",
        "Expected rainfall": "الأمطار المتوقعة",
        "Indoor": "داخلي",
        "Outdoor": "خارجي",
        "Recommended court:": "الملعب الموصى به:",
        "Membership options": "خيارات العضوية",
        "🔒 Membership options": "🔒 خيارات العضوية",
        "Sort table by": "ترتيب الجدول حسب",
        "Sort order": "اتجاه الترتيب",
        "Calculate cycling times": "احسب أوقات ركوب الدراجة",
        "Court surface info": "معلومات عن أرضية الملعب",
        "Update credentials": "تحديث بيانات الدخول",
        "Forget saved credentials": "حذف بيانات الدخول المحفوظة",
        "Forget street address": "حذف عنوان الانطلاق",
        "How availability is checked": "كيفية التحقق من التوفر",
        "Public (non-members)": "متاح لغير الأعضاء",
        "Members only": "للأعضاء فقط",
        "Not specified": "غير محدد",
        "Not listed": "غير مدرج",
        "Not calculated": "لم يتم الحساب",
        "Available - selectable on the booking page": "متاح - يمكن اختياره في صفحة الحجز",
        "✅ Available": "✅ متاح",
        "Not checked for this slot": "لم يتم التحقق من هذه الفترة",
        "Could not verify - ": "تعذّر التحقق - ",
        "☀️ Outdoor": "☀️ خارجي",
        "🏠 Indoor": "🏠 داخلي",
        "⛱️ Covered": "⛱️ مغطى",
        "Club": "النادي",
        "Neighbourhood": "الحي",
    },
    "বাংলা": {
        "Booking date": "বুকিংয়ের তারিখ",
        "Start time": "শুরুর সময়",
        "Duration": "সময়কাল",
        "minutes": "মিনিট",
        "Requested slot": "নির্বাচিত সময়",
        "court": "কোর্ট",
        "Check availability": "উপলভ্যতা দেখুন",
        "Availability": "উপলভ্যতা",
        "Cycling time": "সাইকেলে যাওয়ার সময়",
        "Available type": "উপলভ্য কোর্টের ধরন",
        "Booking access": "বুকিংয়ের সুযোগ",
        "Price / court / hour (€)": "প্রতি কোর্টে প্রতি ঘণ্টার দাম (€)",
        "Court surface": "কোর্টের পৃষ্ঠ",
        "Booking page": "বুকিং পৃষ্ঠা",
        "Other info": "অন্যান্য তথ্য",
        "Membership price": "সদস্যতার মূল্য",
        "Senior membership price": "সিনিয়র সদস্যতার মূল্য",
        "Waiting list": "অপেক্ষমাণ তালিকা",
        "Club site": "ক্লাবের ওয়েবসাইট",
        "Members (approx.)": "সদস্য (প্রায়)",
        "Courts": "কোর্ট",
        "Ratio (members/court)": "প্রতি কোর্টে সদস্য",
        "Stand-alone courts": "সর্বসাধারণের টেনিস কোর্ট",
        "Address": "ঠিকানা",
        "Privacy & data": "গোপনীয়তা ও ডেটা",
        "Club profiles": "ক্লাবের পরিচিতি",
        "Choose a club": "একটি ক্লাব বেছে নিন",
        "Filter clubs": "ক্লাব ফিল্টার করুন",
        "Neighbourhoods": "এলাকা",
        "Court surfaces": "কোর্টের পৃষ্ঠ",
        "Availability filter": "উপলভ্যতা",
        "Maximum cycling time (minutes)": "সর্বোচ্চ সাইকেল সময় (মিনিট)",
        "All availability": "সব অবস্থা",
        "Available": "উপলভ্য",
        "Unavailable": "উপলভ্য নয়",
        "Could not verify": "যাচাই করা যায়নি",
        "Too early to check": "যাচাই করার সময় এখনও হয়নি",
        "Not checked": "যাচাই করা হয়নি",
        "Other status": "অন্যান্য অবস্থা",
        "Showing {shown} of {total} clubs.": "{total}টির মধ্যে {shown}টি ক্লাব দেখানো হচ্ছে।",
        "No clubs match these filters.": "এই ফিল্টারে কোনো ক্লাব মেলেনি।",
        "Available courts": "উপলভ্য কোর্ট",
        "Booking platform": "বুকিং প্ল্যাটফর্ম",
        "Last checked": "শেষ যাচাই",
        "Open booking page": "বুকিং পৃষ্ঠা খুলুন",
        "Official club website": "ক্লাবের অফিসিয়াল ওয়েবসাইট",
        "Availability can change; confirm the slot on the club's booking page.": "উপলভ্যতা বদলাতে পারে; ক্লাবের বুকিং পৃষ্ঠায় সময়টি নিশ্চিত করুন।",
        "Amsterdam weather forecast": "আমস্টারডামের আবহাওয়ার পূর্বাভাস",
        "Temperature": "তাপমাত্রা",
        "Precipitation chance": "বৃষ্টির সম্ভাবনা",
        "Wind": "বাতাস",
        "Expected rainfall": "সম্ভাব্য বৃষ্টিপাত",
        "Indoor": "ইনডোর",
        "Outdoor": "আউটডোর",
        "Recommended court:": "প্রস্তাবিত কোর্ট:",
        "Membership options": "সদস্যতার বিকল্প",
        "🔒 Membership options": "🔒 সদস্যতার বিকল্প",
        "Sort table by": "সারণি সাজান",
        "Sort order": "সাজানোর ক্রম",
        "Calculate cycling times": "সাইকেল সময় হিসাব করুন",
        "Court surface info": "কোর্টের পৃষ্ঠের তথ্য",
        "Update credentials": "লগইন তথ্য হালনাগাদ করুন",
        "Forget saved credentials": "সংরক্ষিত লগইন তথ্য মুছুন",
        "Forget street address": "শুরুর ঠিকানা মুছুন",
        "How availability is checked": "উপলভ্যতা কীভাবে যাচাই হয়",
        "Public (non-members)": "সদস্য নন এমনদের জন্য উন্মুক্ত",
        "Members only": "শুধু সদস্যদের জন্য",
        "Not specified": "উল্লেখ করা নেই",
        "Not listed": "তালিকাভুক্ত নয়",
        "Not calculated": "হিসাব করা হয়নি",
        "Available - selectable on the booking page": "উপলভ্য - বুকিং পৃষ্ঠায় বেছে নেওয়া যাবে",
        "✅ Available": "✅ উপলভ্য",
        "Not checked for this slot": "এই সময়ের জন্য যাচাই করা হয়নি",
        "Could not verify - ": "যাচাই করা যায়নি - ",
        "☀️ Outdoor": "☀️ আউটডোর",
        "🏠 Indoor": "🏠 ইনডোর",
        "⛱️ Covered": "⛱️ ছাউনিযুক্ত",
        "Club": "ক্লাব",
        "Neighbourhood": "এলাকা",
    },
    "Português": {
        "Booking date": "Data da reserva",
        "Start time": "Hora de início",
        "Duration": "Duração",
        "minutes": "minutos",
        "Requested slot": "Horário escolhido",
        "court": "campo",
        "Check availability": "Verificar disponibilidade",
        "Availability": "Disponibilidade",
        "Cycling time": "Tempo de bicicleta",
        "Available type": "Tipo de campo disponível",
        "Booking access": "Acesso à reserva",
        "Price / court / hour (€)": "Preço por campo e por hora (€)",
        "Court surface": "Piso do campo",
        "Booking page": "Página de reservas",
        "Other info": "Outras informações",
        "Membership price": "Preço da inscrição",
        "Senior membership price": "Preço da inscrição sénior",
        "Waiting list": "Lista de espera",
        "Club site": "Site do clube",
        "Members (approx.)": "Sócios (aprox.)",
        "Courts": "Campos",
        "Ratio (members/court)": "Sócios por campo",
        "Stand-alone courts": "Campos de ténis públicos",
        "Address": "Morada",
        "Privacy & data": "Privacidade e dados",
        "Club profiles": "Perfis dos clubes",
        "Choose a club": "Escolha um clube",
        "Filter clubs": "Filtrar clubes",
        "Neighbourhoods": "Bairros",
        "Court surfaces": "Pisos dos campos",
        "Availability filter": "Disponibilidade",
        "Maximum cycling time (minutes)": "Tempo máximo de bicicleta (minutos)",
        "All availability": "Todos os estados",
        "Available": "Disponível",
        "Unavailable": "Indisponível",
        "Could not verify": "Não foi possível verificar",
        "Too early to check": "Ainda é cedo para verificar",
        "Not checked": "Não verificado",
        "Other status": "Outro estado",
        "Showing {shown} of {total} clubs.": "A mostrar {shown} de {total} clubes.",
        "No clubs match these filters.": "Nenhum clube corresponde a estes filtros.",
        "Available courts": "Campos disponíveis",
        "Booking platform": "Plataforma de reservas",
        "Last checked": "Última verificação",
        "Open booking page": "Abrir página de reservas",
        "Official club website": "Site oficial do clube",
        "Availability can change; confirm the slot on the club's booking page.": "A disponibilidade pode mudar; confirme o horário na página de reservas do clube.",
        "Amsterdam weather forecast": "Previsão meteorológica de Amesterdão",
        "Temperature": "Temperatura",
        "Precipitation chance": "Probabilidade de precipitação",
        "Wind": "Vento",
        "Expected rainfall": "Chuva prevista",
        "Indoor": "Interior",
        "Outdoor": "Exterior",
        "Recommended court:": "Campo recomendado:",
        "Membership options": "Opções de adesão",
        "🔒 Membership options": "🔒 Opções de adesão",
        "Sort table by": "Ordenar tabela por",
        "Sort order": "Ordem",
        "Calculate cycling times": "Calcular tempos de bicicleta",
        "Court surface info": "Informação sobre os pisos",
        "Update credentials": "Atualizar credenciais",
        "Forget saved credentials": "Apagar credenciais guardadas",
        "Forget street address": "Apagar morada de partida",
        "How availability is checked": "Como a disponibilidade é verificada",
        "Public (non-members)": "Aberto a não sócios",
        "Members only": "Apenas sócios",
        "Not specified": "Não especificado",
        "Not listed": "Não indicado",
        "Not calculated": "Não calculado",
        "Available - selectable on the booking page": "Disponível - selecionável na página de reservas",
        "✅ Available": "✅ Disponível",
        "Not checked for this slot": "Não verificado para este horário",
        "Could not verify - ": "Não foi possível verificar - ",
        "☀️ Outdoor": "☀️ Exterior",
        "🏠 Indoor": "🏠 Interior",
        "⛱️ Covered": "⛱️ Coberto",
        "Club": "Clube",
        "Neighbourhood": "Bairro",
    },
    "Русский": {
        "Booking date": "Дата бронирования",
        "Start time": "Время начала",
        "Duration": "Длительность",
        "minutes": "минут",
        "Requested slot": "Выбранное время",
        "court": "корт",
        "Check availability": "Проверить наличие мест",
        "Availability": "Наличие мест",
        "Cycling time": "Время на велосипеде",
        "Available type": "Доступный тип корта",
        "Booking access": "Условия бронирования",
        "Price / court / hour (€)": "Цена за корт в час (€)",
        "Court surface": "Покрытие корта",
        "Booking page": "Страница бронирования",
        "Other info": "Другая информация",
        "Membership price": "Стоимость членства",
        "Senior membership price": "Стоимость членства для старших",
        "Waiting list": "Лист ожидания",
        "Club site": "Сайт клуба",
        "Members (approx.)": "Участники (примерно)",
        "Courts": "Корты",
        "Ratio (members/court)": "Участников на корт",
        "Stand-alone courts": "Общественные теннисные корты",
        "Address": "Адрес",
        "Privacy & data": "Конфиденциальность и данные",
        "Club profiles": "Профили клубов",
        "Choose a club": "Выберите клуб",
        "Filter clubs": "Фильтр клубов",
        "Neighbourhoods": "Районы",
        "Court surfaces": "Покрытия кортов",
        "Availability filter": "Наличие мест",
        "Maximum cycling time (minutes)": "Максимальное время на велосипеде (минуты)",
        "All availability": "Все статусы",
        "Available": "Доступно",
        "Unavailable": "Недоступно",
        "Could not verify": "Не удалось проверить",
        "Too early to check": "Проверять пока рано",
        "Not checked": "Не проверено",
        "Other status": "Другой статус",
        "Showing {shown} of {total} clubs.": "Показано клубов: {shown} из {total}.",
        "No clubs match these filters.": "Клубы по этим фильтрам не найдены.",
        "Available courts": "Доступные корты",
        "Booking platform": "Платформа бронирования",
        "Last checked": "Последняя проверка",
        "Open booking page": "Открыть страницу бронирования",
        "Official club website": "Официальный сайт клуба",
        "Availability can change; confirm the slot on the club's booking page.": "Наличие мест может измениться; подтвердите время на странице бронирования клуба.",
        "Amsterdam weather forecast": "Прогноз погоды в Амстердаме",
        "Temperature": "Температура",
        "Precipitation chance": "Вероятность осадков",
        "Wind": "Ветер",
        "Expected rainfall": "Ожидаемые осадки",
        "Indoor": "В помещении",
        "Outdoor": "На открытом воздухе",
        "Recommended court:": "Рекомендуемый корт:",
        "Membership options": "Варианты членства",
        "🔒 Membership options": "🔒 Варианты членства",
        "Sort table by": "Сортировать таблицу по",
        "Sort order": "Порядок сортировки",
        "Calculate cycling times": "Рассчитать время на велосипеде",
        "Court surface info": "Информация о покрытии корта",
        "Update credentials": "Обновить данные для входа",
        "Forget saved credentials": "Удалить сохранённые данные для входа",
        "Forget street address": "Удалить начальный адрес",
        "How availability is checked": "Как проверяется наличие мест",
        "Public (non-members)": "Доступно неучастникам",
        "Members only": "Только для участников",
        "Not specified": "Не указано",
        "Not listed": "Не указано",
        "Not calculated": "Не рассчитано",
        "Available - selectable on the booking page": "Доступно - можно выбрать на странице бронирования",
        "✅ Available": "✅ Доступно",
        "Not checked for this slot": "Это время не проверялось",
        "Could not verify - ": "Не удалось проверить - ",
        "☀️ Outdoor": "☀️ На открытом воздухе",
        "🏠 Indoor": "🏠 В помещении",
        "⛱️ Covered": "⛱️ Под навесом",
        "Club": "Клуб",
        "Neighbourhood": "Район",
    },
}

ADDITIONAL_TRANSLATION_EXTENSIONS = {
    "中文 (简体)": {
        "ascending": "升序",
        "descending": "降序",
        "Cushioned hard court": "缓冲硬地",
        "Clay": "红土",
        "Hard court": "硬地",
        "Synthetic grass": "人造草",
        "Indoor synthetic tennis floor": "室内合成网球地面",
        "Unspecified all-weather": "未指定全天候场地",
        "Surface type not specified": "未注明场地类型",
        "Public seasonally; members can invite guests": "季节性向公众开放；会员可邀请访客",
        "Indoor is preferable for ": "以下情况建议选择室内球场：",
        "cold (": "寒冷（",
        "strong wind (": "强风（",
        "rain forecast (": "预计降雨（",
        "rain likely (": "可能下雨（",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "室外条件尚可；如果难以判断，室外球场通常更便宜。",
        "A forecast is not available for a past date.": "无法提供过去日期的天气预报。",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "该时段暂时没有天气预报。请选择未来时间或稍后再试。",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "该时段没有天气预报。Open-Meteo 最多提供未来 16 天的预报，备用服务覆盖时间更短。",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "每片球场的估算会员数。绿色 ≤75，黄色 76–150，红色 >150；范围按较低值着色。使用“排序方式”进行数值排序。",
        "Booking-portal credentials are available for this app session.": "本次应用会话可使用预订平台登录信息。",
        "Calculate cycling times to enable the cycling-time filter.": "计算骑行时间后即可使用骑行时间筛选。",
        "Calculating cycling times for both tables...": "正在计算两张表的骑行时间……",
        "Calculating cycling times for single courts...": "正在计算独立球场的骑行时间……",
        "Calculating public-club cycling times...": "正在计算公共俱乐部的骑行时间……",
        "Checking all public (non-member) clubs...": "正在检查所有对非会员开放的俱乐部……",
        "Club names and source-provided notes are shown in their original wording.": "俱乐部名称和来源提供的说明保留原文。",
        "Could not load the Amsterdam weather forecast:": "无法加载阿姆斯特丹天气预报：",
        "Cycling-time calculation failed": "骑行时间计算失败",
        "Forecast rainfall for the selected hour or forecast period.": "所选时段或预报周期的预计降雨量。",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "在公共俱乐部列表和空位查询中包含 USC、Frans Otten Stadion 和 Amstelpark Tennisclub。",
        "Include sign-in-required clubs": "包含需要登录的俱乐部",
        "Introducé price": "访客费用",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "临时想打球？可以试试阿姆斯特丹的独立球场。这些球场不能提前预订。",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "想长期加入俱乐部？请查看下方的高级会员选项。",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "每片球场的会员数：绿色 ≤75，黄色 76–150，红色 >150。标注为估算的会员和球场数据并非精确值。荷兰网球联合会 (KNLTB) 建议每片有灯光的室外球场配备 60 至 90 名会员。",
        "Open club site": "打开俱乐部网站",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "查看公共网球俱乐部的空位、骑行时间、价格、场地类型、预订页面及其他信息",
        "Ranges use their lower value, and entries without a number are placed last.": "范围按较低值排序，没有数字的条目排在最后。",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "行背景：绿色表示没有候补名单，红色表示有候补名单。高级会员费用文字：绿色 ≤ €200，琥珀色 €201–€275，红色 > €275；骑行时间沿用原有颜色标记。",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "公共独立网球场的街区、地址、场地类型和骑行时间",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "提供会员资格、价格、骑行时间、访客政策、候补名单及俱乐部网站的网球俱乐部",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "天气服务最多提供未来 16 天的预报，目前还没有该日期的预报。",
        "This summary describes how the app currently handles data.": "本摘要说明应用目前如何处理数据。",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "还没找到合适的网球俱乐部？在这里浏览阿姆斯特丹各地的俱乐部，无论是偶尔打球还是长期加入。比较地点、骑行时间和价格，了解会员选项，并一次查看所选日期、时间和时长的空位。",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "所选时段可用的球场类型，包括室外、室内或有顶棚球场。",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "使用“排序方式”进行数值排序；价格范围按较低金额排序。",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "使用“排序方式”控件进行数值排序；范围按较低值排序。",
        "🔓 Public (non-member) clubs": "🔓 对非会员开放的俱乐部",
    },
    "हिन्दी": {
        "ascending": "आरोही",
        "descending": "अवरोही",
        "Cushioned hard court": "कुशन वाला हार्ड कोर्ट",
        "Clay": "क्ले कोर्ट",
        "Hard court": "हार्ड कोर्ट",
        "Synthetic grass": "सिंथेटिक घास",
        "Indoor synthetic tennis floor": "इनडोर सिंथेटिक टेनिस सतह",
        "Unspecified all-weather": "अनिर्दिष्ट हर मौसम वाला कोर्ट",
        "Surface type not specified": "कोर्ट की सतह निर्दिष्ट नहीं",
        "Public seasonally; members can invite guests": "मौसमी रूप से सार्वजनिक; सदस्य मेहमान बुला सकते हैं",
        "Indoor is preferable for ": "इन कारणों से इनडोर कोर्ट बेहतर है: ",
        "cold (": "ठंड (",
        "strong wind (": "तेज़ हवा (",
        "rain forecast (": "बारिश का पूर्वानुमान (",
        "rain likely (": "बारिश की संभावना (",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "बाहरी परिस्थितियाँ ठीक लगती हैं; यदि निर्णय स्पष्ट न हो, तो आउटडोर कोर्ट आमतौर पर सस्ते होते हैं।",
        "A forecast is not available for a past date.": "बीती तारीख के लिए मौसम पूर्वानुमान उपलब्ध नहीं है।",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "उस समय का पूर्वानुमान अभी उपलब्ध नहीं है। भविष्य का समय चुनें या बाद में फिर देखें।",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "उस समय का पूर्वानुमान उपलब्ध नहीं है। Open-Meteo 16 दिन तक और वैकल्पिक सेवाएँ उससे कम दिनों तक पूर्वानुमान देती हैं।",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "प्रति टेनिस कोर्ट अनुमानित सदस्य। हरा ≤75, पीला 76–150, लाल >150; रंग के लिए सीमा का निचला मान लिया जाता है। संख्यात्मक क्रम के लिए तालिका क्रमबद्ध करें।",
        "Booking-portal credentials are available for this app session.": "बुकिंग पोर्टल की लॉगिन जानकारी इस ऐप सत्र में उपलब्ध है।",
        "Calculate cycling times to enable the cycling-time filter.": "साइकिल समय फ़िल्टर चालू करने के लिए पहले साइकिल समय की गणना करें।",
        "Calculating cycling times for both tables...": "दोनों तालिकाओं के लिए साइकिल समय की गणना हो रही है...",
        "Calculating cycling times for single courts...": "अलग-अलग कोर्ट के लिए साइकिल समय की गणना हो रही है...",
        "Calculating public-club cycling times...": "सार्वजनिक क्लबों के लिए साइकिल समय की गणना हो रही है...",
        "Checking all public (non-member) clubs...": "सभी सार्वजनिक (गैर-सदस्य) क्लबों की जाँच हो रही है...",
        "Club names and source-provided notes are shown in their original wording.": "क्लब के नाम और स्रोत से मिली टिप्पणियाँ मूल भाषा में दिखाई जाती हैं।",
        "Could not load the Amsterdam weather forecast:": "एम्स्टर्डम का मौसम पूर्वानुमान लोड नहीं हो सका:",
        "Cycling-time calculation failed": "साइकिल समय की गणना विफल हुई",
        "Forecast rainfall for the selected hour or forecast period.": "चुने हुए घंटे या पूर्वानुमान अवधि में संभावित बारिश।",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "सार्वजनिक क्लबों की तालिका और उपलब्धता जाँच में USC, Frans Otten Stadion और Amstelpark Tennisclub शामिल करें।",
        "Include sign-in-required clubs": "लॉगिन आवश्यक क्लब शामिल करें",
        "Introducé price": "मेहमान का शुल्क",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "अचानक खेलने का मन है? एम्स्टर्डम के अलग-अलग सार्वजनिक कोर्ट आज़माएँ। इन कोर्ट को पहले से बुक नहीं किया जा सकता।",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "लंबे समय तक क्लब से जुड़ना चाहते हैं? नीचे वरिष्ठ सदस्यता के विकल्प देखें।",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "प्रति कोर्ट सदस्य: हरा ≤75, पीला 76–150, लाल >150। जहाँ अनुमान लिखा है वहाँ सदस्य और कोर्ट की संख्या अनुमानित है। डच टेनिस महासंघ (KNLTB) रोशनी वाले बाहरी कोर्ट पर 60 से 90 सदस्यों को उचित मानता है।",
        "Open club site": "क्लब की वेबसाइट खोलें",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "सार्वजनिक टेनिस क्लबों की उपलब्धता, साइकिल समय, कीमतें, कोर्ट की सतह, बुकिंग पेज और अन्य जानकारी",
        "Ranges use their lower value, and entries without a number are placed last.": "सीमा वाले मानों में निचले मान का उपयोग होता है; बिना संख्या वाली प्रविष्टियाँ अंत में आती हैं।",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "पंक्ति का रंग: हरा = प्रतीक्षा सूची नहीं; लाल = प्रतीक्षा सूची है। वरिष्ठ सदस्यता शुल्क: हरा ≤ €200, पीला €201–€275, लाल > €275; साइकिल समय के रंग यथावत रहते हैं।",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "सार्वजनिक कोर्ट के इलाके, पते, सतह और साइकिल समय",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "सदस्यता, कीमतें, साइकिल समय, मेहमान नीति, प्रतीक्षा सूची और वेबसाइट वाले टेनिस क्लब",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "मौसम सेवा 16 दिन तक का पूर्वानुमान देती है। इस तारीख का पूर्वानुमान अभी उपलब्ध नहीं है।",
        "This summary describes how the app currently handles data.": "यह सारांश बताता है कि ऐप फिलहाल डेटा को कैसे संभालता है।",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "अपने लिए सही टेनिस क्लब ढूँढ़ना मुश्किल है? एम्स्टर्डम के क्लब देखें—चाहे कभी-कभार खेलने के लिए या लंबे समय की सदस्यता के लिए। एक ही जगह पर स्थान, साइकिल समय और कीमतों की तुलना करें, सदस्यता विकल्प देखें और चुनी तारीख, समय तथा अवधि की उपलब्धता जाँचें।",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "चुने हुए समय पर उपलब्ध कोर्ट के प्रकार, जैसे आउटडोर, इनडोर या ढका हुआ।",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "संख्यात्मक क्रम के लिए तालिका क्रमबद्ध करें; कीमत की सीमा में निचली कीमत ली जाती है।",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "संख्यात्मक क्रम के लिए तालिका क्रमबद्ध करें; सीमा में निचला मान लिया जाता है।",
        "🔓 Public (non-member) clubs": "🔓 सार्वजनिक (गैर-सदस्य) क्लब",
    },
    "Español": {
        "ascending": "ascendente",
        "descending": "descendente",
        "Cushioned hard court": "Pista dura acolchada",
        "Clay": "Tierra batida",
        "Hard court": "Pista dura",
        "Synthetic grass": "Hierba sintética",
        "Indoor synthetic tennis floor": "Pavimento sintético de tenis interior",
        "Unspecified all-weather": "Todo tiempo sin especificar",
        "Surface type not specified": "Superficie no especificada",
        "Public seasonally; members can invite guests": "Abierto al público por temporada; los socios pueden invitar",
        "Indoor is preferable for ": "Es preferible jugar en interior por ",
        "cold (": "frío (",
        "strong wind (": "viento fuerte (",
        "rain forecast (": "lluvia prevista (",
        "rain likely (": "probabilidad de lluvia (",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "Las condiciones exteriores parecen aceptables; si no está claro, las pistas exteriores suelen ser más baratas.",
        "A forecast is not available for a past date.": "No hay previsión meteorológica para una fecha pasada.",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "Todavía no hay previsión para esa hora. Elige una hora futura o vuelve a consultarlo más tarde.",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "No hay previsión para esa hora. Open-Meteo cubre hasta 16 días; las fuentes alternativas cubren menos.",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "Socios aproximados por pista. Verde ≤75, amarillo 76–150, rojo >150; los rangos se colorean según su valor menor. Usa «Ordenar tabla por» para ordenar numéricamente.",
        "Booking-portal credentials are available for this app session.": "Las credenciales del portal de reservas están disponibles durante esta sesión.",
        "Calculate cycling times to enable the cycling-time filter.": "Calcula los tiempos en bicicleta para activar este filtro.",
        "Calculating cycling times for both tables...": "Calculando los tiempos en bicicleta para ambas tablas...",
        "Calculating cycling times for single courts...": "Calculando los tiempos en bicicleta para las pistas públicas...",
        "Calculating public-club cycling times...": "Calculando los tiempos en bicicleta para los clubes públicos...",
        "Checking all public (non-member) clubs...": "Consultando todos los clubes abiertos a no socios...",
        "Club names and source-provided notes are shown in their original wording.": "Los nombres de los clubes y las notas de las fuentes se muestran en su idioma original.",
        "Could not load the Amsterdam weather forecast:": "No se pudo cargar la previsión meteorológica de Ámsterdam:",
        "Cycling-time calculation failed": "Error al calcular el tiempo en bicicleta",
        "Forecast rainfall for the selected hour or forecast period.": "Lluvia prevista para la hora o el periodo seleccionado.",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "Incluir USC, Frans Otten Stadion y Amstelpark Tennisclub en la tabla y en las consultas de clubes públicos.",
        "Include sign-in-required clubs": "Incluir clubes que requieren iniciar sesión",
        "Introducé price": "Precio para invitados",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "¿Un plan de última hora? Prueba las pistas públicas de Ámsterdam. No se pueden reservar con antelación.",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "¿Buscas una opción a más largo plazo? Consulta las cuotas de membresía sénior de estos clubes.",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "Socios por pista: verde ≤75, amarillo 76–150, rojo >150. Las cifras señaladas son aproximadas. La federación neerlandesa KNLTB recomienda entre 60 y 90 socios por pista exterior iluminada.",
        "Open club site": "Abrir web del club",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "Clubes públicos con disponibilidad, tiempo en bicicleta, precios, superficies, páginas de reservas y más información",
        "Ranges use their lower value, and entries without a number are placed last.": "Los rangos usan el valor inferior; las entradas sin cifra aparecen al final.",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "Fondo de fila: verde = sin lista de espera; rojo = con lista. Cuota sénior: verde ≤ 200 €, ámbar 201–275 €, rojo >275 €; los colores del tiempo en bicicleta indican el trayecto.",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "Pistas públicas independientes con barrios, direcciones, superficies y tiempos en bicicleta",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "Clubes con información sobre membresía, precios, trayectos en bicicleta, invitados, listas de espera y sus sitios web",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "El servicio meteorológico ofrece previsiones para hasta 16 días. Aún no hay previsión para esta fecha.",
        "This summary describes how the app currently handles data.": "Este resumen explica cómo gestiona actualmente los datos la aplicación.",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "¿Te cuesta encontrar el club adecuado? Explora clubes de Ámsterdam para jugar ocasionalmente o hacerte socio. Compara ubicaciones, tiempos en bicicleta y precios, consulta las opciones de membresía y comprueba la disponibilidad para la fecha, hora y duración que elijas, todo en un mismo lugar.",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "Tipos de pista disponibles para la hora elegida: exterior, interior o cubierta.",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "Usa «Ordenar tabla por» para ordenar numéricamente; los rangos de precios usan el importe menor.",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "Usa «Ordenar tabla por» para ordenar numéricamente; los rangos usan el valor inferior.",
        "🔓 Public (non-member) clubs": "🔓 Clubes abiertos a no socios",
    },
    "Français": {
        "ascending": "croissant",
        "descending": "décroissant",
        "Cushioned hard court": "Court dur amortissant",
        "Clay": "Terre battue",
        "Hard court": "Court en dur",
        "Synthetic grass": "Gazon synthétique",
        "Indoor synthetic tennis floor": "Revêtement synthétique intérieur",
        "Unspecified all-weather": "Toutes saisons non précisé",
        "Surface type not specified": "Surface non précisée",
        "Public seasonally; members can invite guests": "Ouvert au public en saison ; les membres peuvent inviter",
        "Indoor is preferable for ": "Le court intérieur est préférable en raison de ",
        "cold (": "froid (",
        "strong wind (": "vent fort (",
        "rain forecast (": "pluie prévue (",
        "rain likely (": "risque de pluie (",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "Les conditions extérieures semblent acceptables ; en cas d'hésitation, les courts extérieurs sont généralement moins chers.",
        "A forecast is not available for a past date.": "Aucune prévision météo n'est disponible pour une date passée.",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "Aucune prévision n'est encore disponible pour cette heure. Choisissez une heure future ou réessayez plus tard.",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "Aucune prévision n'est disponible pour cette heure. Open-Meteo couvre jusqu'à 16 jours ; les services de secours couvrent une période plus courte.",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "Nombre approximatif de membres par court. Vert ≤75, jaune 76–150, rouge >150 ; la borne inférieure détermine la couleur. Utilisez « Trier le tableau par » pour le tri numérique.",
        "Booking-portal credentials are available for this app session.": "Les identifiants du portail de réservation sont disponibles pour cette session.",
        "Calculate cycling times to enable the cycling-time filter.": "Calculez les temps à vélo pour activer ce filtre.",
        "Calculating cycling times for both tables...": "Calcul des temps à vélo pour les deux tableaux…",
        "Calculating cycling times for single courts...": "Calcul des temps à vélo vers les courts publics…",
        "Calculating public-club cycling times...": "Calcul des temps à vélo vers les clubs publics…",
        "Checking all public (non-member) clubs...": "Vérification de tous les clubs ouverts aux non-membres…",
        "Club names and source-provided notes are shown in their original wording.": "Les noms des clubs et les notes issues des sources restent dans leur langue d'origine.",
        "Could not load the Amsterdam weather forecast:": "Impossible de charger les prévisions météo d'Amsterdam :",
        "Cycling-time calculation failed": "Échec du calcul du temps à vélo",
        "Forecast rainfall for the selected hour or forecast period.": "Pluie prévue pour l'heure ou la période sélectionnée.",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "Inclure USC, Frans Otten Stadion et Amstelpark Tennisclub dans le tableau et les vérifications des clubs publics.",
        "Include sign-in-required clubs": "Inclure les clubs nécessitant une connexion",
        "Introducé price": "Tarif invité",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "Envie de jouer à la dernière minute ? Essayez les courts publics d'Amsterdam, qui ne se réservent pas à l'avance.",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "Pour un engagement à plus long terme, consultez ci-dessous les tarifs d'adhésion senior.",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "Membres par court : vert ≤75, jaune 76–150, rouge >150. Les chiffres indiqués comme approximatifs le sont réellement. La fédération néerlandaise KNLTB recommande 60 à 90 membres par court extérieur éclairé.",
        "Open club site": "Ouvrir le site du club",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "Clubs publics : disponibilités, temps à vélo, prix, surfaces, pages de réservation et autres informations",
        "Ranges use their lower value, and entries without a number are placed last.": "Les fourchettes utilisent leur valeur basse ; les entrées sans nombre sont classées à la fin.",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "Fond de ligne : vert = pas de liste d'attente ; rouge = liste d'attente. Tarif senior : vert ≤ 200 €, orange 201–275 €, rouge >275 € ; les couleurs du temps à vélo restent inchangées.",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "Courts publics indépendants avec quartiers, adresses, surfaces et temps à vélo",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "Clubs de tennis : adhésion, prix, temps à vélo, règles pour les invités, listes d'attente et sites web",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "Le service météo fournit des prévisions jusqu'à 16 jours à l'avance. Celle de cette date n'est pas encore disponible.",
        "This summary describes how the app currently handles data.": "Ce résumé décrit la manière dont l'application traite actuellement les données.",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "Vous cherchez le club de tennis qui vous convient ? Découvrez les clubs d'Amsterdam pour jouer occasionnellement ou vous engager sur la durée. Comparez les lieux, les temps à vélo et les prix, explorez les adhésions et vérifiez les disponibilités à la date, à l'heure et pour la durée souhaitées, au même endroit.",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "Types de courts disponibles au créneau choisi : extérieur, intérieur ou couvert.",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "Utilisez « Trier le tableau par » pour un tri numérique ; les fourchettes de prix utilisent le montant le plus bas.",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "Utilisez « Trier le tableau par » pour un tri numérique ; les fourchettes utilisent leur valeur basse.",
        "🔓 Public (non-member) clubs": "🔓 Clubs ouverts aux non-membres",
    },
    "العربية": {
        "ascending": "تصاعدي",
        "descending": "تنازلي",
        "Cushioned hard court": "ملعب صلب مبطن",
        "Clay": "ترابي",
        "Hard court": "ملعب صلب",
        "Synthetic grass": "عشب صناعي",
        "Indoor synthetic tennis floor": "أرضية تنس صناعية داخلية",
        "Unspecified all-weather": "ملعب لجميع الأحوال الجوية غير محدد",
        "Surface type not specified": "نوع الأرضية غير محدد",
        "Public seasonally; members can invite guests": "متاح للعامة موسمياً؛ ويمكن للأعضاء دعوة الضيوف",
        "Indoor is preferable for ": "يُفضّل الملعب الداخلي بسبب ",
        "cold (": "البرد (",
        "strong wind (": "الرياح القوية (",
        "rain forecast (": "الأمطار المتوقعة (",
        "rain likely (": "احتمال المطر (",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "تبدو الظروف الخارجية مناسبة؛ وعند عدم وضوح الاختيار تكون الملاعب الخارجية أقل تكلفة عادةً.",
        "A forecast is not available for a past date.": "لا تتوفر توقعات الطقس لتاريخ مضى.",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "لا يتوفر التوقع لهذه الساعة بعد. اختر وقتاً في المستقبل أو أعد المحاولة لاحقاً.",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "لا يتوفر توقع لهذا الوقت. تغطي Open-Meteo ما يصل إلى 16 يوماً، بينما تغطي الخدمات البديلة مدة أقصر.",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "عدد تقريبي للأعضاء لكل ملعب: أخضر ≤75، أصفر 76–150، أحمر >150؛ تُحدد ألوان النطاقات بقيمتها الأدنى. استخدم «ترتيب الجدول حسب» للترتيب الرقمي.",
        "Booking-portal credentials are available for this app session.": "بيانات الدخول إلى بوابة الحجز متاحة خلال جلسة التطبيق هذه.",
        "Calculate cycling times to enable the cycling-time filter.": "احسب أوقات ركوب الدراجة لتفعيل عامل التصفية هذا.",
        "Calculating cycling times for both tables...": "جارٍ حساب أوقات ركوب الدراجة للجدولين...",
        "Calculating cycling times for single courts...": "جارٍ حساب أوقات ركوب الدراجة إلى الملاعب العامة...",
        "Calculating public-club cycling times...": "جارٍ حساب أوقات ركوب الدراجة إلى الأندية العامة...",
        "Checking all public (non-member) clubs...": "جارٍ التحقق من جميع الأندية المتاحة لغير الأعضاء...",
        "Club names and source-provided notes are shown in their original wording.": "تُعرض أسماء الأندية والملاحظات الواردة من المصادر بلغتها الأصلية.",
        "Could not load the Amsterdam weather forecast:": "تعذّر تحميل توقعات الطقس في أمستردام:",
        "Cycling-time calculation failed": "فشل حساب وقت ركوب الدراجة",
        "Forecast rainfall for the selected hour or forecast period.": "الأمطار المتوقعة للساعة أو للفترة المحددة.",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "أدرج USC وFrans Otten Stadion وAmstelpark Tennisclub في جدول الأندية العامة وفحوصات التوفر.",
        "Include sign-in-required clubs": "تضمين الأندية التي تتطلب تسجيل الدخول",
        "Introducé price": "سعر الضيف",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "هل تريد اللعب في اللحظة الأخيرة؟ جرّب ملاعب أمستردام العامة المستقلة؛ لا يمكن حجزها مسبقاً.",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "هل تبحث عن عضوية طويلة الأمد؟ اطّلع أدناه على خيارات العضوية السنوية للأندية.",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "الأعضاء لكل ملعب: أخضر ≤75، أصفر 76–150، أحمر >150. الأرقام المشار إليها كتقديرية تقريبية. توصي رابطة التنس الهولندية (KNLTB) بـ60 إلى 90 عضواً لكل ملعب خارجي مضاء.",
        "Open club site": "افتح موقع النادي",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "أندية التنس العامة: التوفر، ووقت ركوب الدراجة، والأسعار، وأرضية الملعب، وصفحات الحجز ومعلومات أخرى",
        "Ranges use their lower value, and entries without a number are placed last.": "تُستخدم القيمة الأدنى للنطاقات، وتظهر الإدخالات التي لا تتضمن رقماً في النهاية.",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "لون الصف: الأخضر يعني عدم وجود قائمة انتظار، والأحمر يعني وجودها. رسوم العضوية السنوية: أخضر ≤ €200، كهرماني €201–€275، أحمر > €275؛ وتبقى ألوان وقت ركوب الدراجة كما هي.",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "ملاعب تنس عامة مستقلة مع الأحياء والعناوين والأرضيات وأوقات ركوب الدراجة",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "أندية تنس مع معلومات العضوية والأسعار وأوقات ركوب الدراجة وسياسات الضيوف وقوائم الانتظار ومواقع الأندية",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "تقدم خدمة الطقس توقعات تصل إلى 16 يوماً؛ ولا يتوفر توقع لهذا التاريخ بعد.",
        "This summary describes how the app currently handles data.": "يلخص هذا البيان كيفية تعامل التطبيق مع البيانات حالياً.",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "هل تبحث عن نادي التنس المناسب؟ استكشف أندية أمستردام للعب من حين لآخر أو للانضمام على المدى الطويل. قارن المواقع وأوقات ركوب الدراجة والأسعار، واستكشف العضويات وتحقق من التوفر للتاريخ والوقت والمدة التي تختارها، كل ذلك في مكان واحد.",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "أنواع الملاعب المتاحة في الوقت المختار، بما فيها الخارجية والداخلية والمغطاة.",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "استخدم «ترتيب الجدول حسب» للترتيب الرقمي؛ وتُرتب نطاقات الأسعار حسب قيمتها الأدنى.",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "استخدم خيار «ترتيب الجدول حسب» للترتيب الرقمي؛ وتُستخدم القيمة الأدنى للنطاقات.",
        "🔓 Public (non-member) clubs": "🔓 أندية عامة (لغير الأعضاء)",
    },
    "বাংলা": {
        "ascending": "ঊর্ধ্বক্রম",
        "descending": "নিম্নক্রম",
        "Cushioned hard court": "কুশনযুক্ত হার্ড কোর্ট",
        "Clay": "ক্লে কোর্ট",
        "Hard court": "হার্ড কোর্ট",
        "Synthetic grass": "সিনথেটিক ঘাস",
        "Indoor synthetic tennis floor": "ইনডোর সিনথেটিক টেনিস পৃষ্ঠ",
        "Unspecified all-weather": "অনির্দিষ্ট সর্ব-আবহাওয়ার কোর্ট",
        "Surface type not specified": "কোর্টের পৃষ্ঠ উল্লেখ নেই",
        "Public seasonally; members can invite guests": "মৌসুমে সবার জন্য উন্মুক্ত; সদস্যরা অতিথি আনতে পারেন",
        "Indoor is preferable for ": "এই কারণে ইনডোর কোর্ট ভালো: ",
        "cold (": "ঠান্ডা (",
        "strong wind (": "জোর বাতাস (",
        "rain forecast (": "বৃষ্টির পূর্বাভাস (",
        "rain likely (": "বৃষ্টির সম্ভাবনা (",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "বাইরের আবহাওয়া মোটামুটি ভালো; সিদ্ধান্ত স্পষ্ট না হলে আউটডোর কোর্ট সাধারণত সস্তা হয়।",
        "A forecast is not available for a past date.": "অতীতের তারিখের আবহাওয়ার পূর্বাভাস পাওয়া যায় না।",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "ওই সময়ের পূর্বাভাস এখনও পাওয়া যায়নি। ভবিষ্যতের সময় বেছে নিন অথবা পরে আবার দেখুন।",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "ওই সময়ের পূর্বাভাস নেই। Open-Meteo ১৬ দিন পর্যন্ত এবং বিকল্প পরিষেবাগুলো তার চেয়ে কম দিনের পূর্বাভাস দেয়।",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "প্রতি টেনিস কোর্টে আনুমানিক সদস্য। সবুজ ≤৭৫, হলুদ ৭৬–১৫০, লাল >১৫০; সীমার নিম্ন মান দিয়ে রং নির্ধারিত হয়। সংখ্যার ক্রম সাজাতে সারণি সাজান ব্যবহার করুন।",
        "Booking-portal credentials are available for this app session.": "এই অ্যাপ সেশনে বুকিং পোর্টালের লগইন তথ্য পাওয়া যাচ্ছে।",
        "Calculate cycling times to enable the cycling-time filter.": "সাইকেল সময়ের ফিল্টার চালু করতে আগে সময় গণনা করুন।",
        "Calculating cycling times for both tables...": "দুটি সারণির জন্য সাইকেল সময় গণনা হচ্ছে...",
        "Calculating cycling times for single courts...": "পৃথক কোর্টে সাইকেল সময় গণনা হচ্ছে...",
        "Calculating public-club cycling times...": "সর্বসাধারণের ক্লাবের সাইকেল সময় গণনা হচ্ছে...",
        "Checking all public (non-member) clubs...": "সদস্য নন এমনদের জন্য খোলা সব ক্লাব যাচাই হচ্ছে...",
        "Club names and source-provided notes are shown in their original wording.": "ক্লাবের নাম ও উৎস থেকে পাওয়া নোট মূল ভাষাতেই দেখানো হয়।",
        "Could not load the Amsterdam weather forecast:": "আমস্টারডামের আবহাওয়ার পূর্বাভাস লোড করা যায়নি:",
        "Cycling-time calculation failed": "সাইকেল সময় গণনা ব্যর্থ হয়েছে",
        "Forecast rainfall for the selected hour or forecast period.": "নির্বাচিত ঘণ্টা বা পূর্বাভাসের সময়ে সম্ভাব্য বৃষ্টি।",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "সর্বসাধারণের ক্লাবের সারণি ও উপলভ্যতা যাচাইয়ে USC, Frans Otten Stadion এবং Amstelpark Tennisclub অন্তর্ভুক্ত করুন।",
        "Include sign-in-required clubs": "লগইন প্রয়োজন এমন ক্লাব অন্তর্ভুক্ত করুন",
        "Introducé price": "অতিথির মূল্য",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "হঠাৎ খেলতে চান? আমস্টারডামের পৃথক পাবলিক কোর্ট দেখতে পারেন। এগুলো আগাম বুক করা যায় না।",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "দীর্ঘমেয়াদি সদস্যতা চাইলে নিচে ক্লাবগুলোর সিনিয়র সদস্যতার বিকল্প দেখুন।",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "প্রতি কোর্টে সদস্য: সবুজ ≤৭৫, হলুদ ৭৬–১৫০, লাল >১৫০। চিহ্নিত সদস্য ও কোর্টের সংখ্যা আনুমানিক। ডাচ টেনিস ফেডারেশন (KNLTB) আলোকিত আউটডোর কোর্টে ৬০–৯০ জন সদস্যকে স্বাস্থ্যকর নির্দেশক ধরে।",
        "Open club site": "ক্লাবের ওয়েবসাইট খুলুন",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "সর্বসাধারণের টেনিস ক্লাবের উপলভ্যতা, সাইকেল সময়, দাম, কোর্টের পৃষ্ঠ, বুকিং পৃষ্ঠা ও অন্যান্য তথ্য",
        "Ranges use their lower value, and entries without a number are placed last.": "সীমার নিম্ন মান ব্যবহার করা হয়; সংখ্যা নেই এমন তথ্য শেষে দেখানো হয়।",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "সারির পটভূমি: সবুজ = অপেক্ষমাণ তালিকা নেই; লাল = তালিকা আছে। সিনিয়র সদস্যতার দাম: সবুজ ≤ €২০০, অ্যাম্বার €২০১–€২৭৫, লাল > €২৭৫; সাইকেল সময়ের রং অপরিবর্তিত থাকে।",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "এলাকা, ঠিকানা, কোর্টের পৃষ্ঠ ও সাইকেল সময়সহ পৃথক পাবলিক টেনিস কোর্ট",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "সদস্যতা, দাম, সাইকেল সময়, অতিথি নীতি, অপেক্ষমাণ তালিকা ও ওয়েবসাইটসহ টেনিস ক্লাব",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "আবহাওয়া পরিষেবা ১৬ দিন পর্যন্ত পূর্বাভাস দেয়। এই তারিখের পূর্বাভাস এখনও পাওয়া যায়নি।",
        "This summary describes how the app currently handles data.": "অ্যাপটি বর্তমানে কীভাবে ডেটা ব্যবহার করে, এই সারাংশে তা বলা হয়েছে।",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "সঠিক টেনিস ক্লাব খুঁজছেন? আমস্টারডামের ক্লাবগুলো দেখুন—মাঝে মাঝে খেলুন বা দীর্ঘমেয়াদি সদস্য হন। একই জায়গায় অবস্থান, সাইকেল সময় ও দাম তুলনা করুন, সদস্যতার বিকল্প দেখুন এবং পছন্দের তারিখ, সময় ও মেয়াদের উপলভ্যতা যাচাই করুন।",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "নির্বাচিত সময়ে উপলভ্য আউটডোর, ইনডোর বা ছাউনিযুক্ত কোর্টের ধরন।",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "সংখ্যার ক্রম সাজাতে সারণি সাজান ব্যবহার করুন; দামের সীমায় নিম্ন দামটি ধরা হয়।",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "সংখ্যার ক্রম সাজাতে সারণি সাজান ব্যবহার করুন; সীমার নিম্ন মানটি ধরা হয়।",
        "🔓 Public (non-member) clubs": "🔓 সর্বসাধারণের জন্য খোলা ক্লাব",
    },
    "Português": {
        "ascending": "crescente",
        "descending": "decrescente",
        "Cushioned hard court": "Campo duro amortecido",
        "Clay": "Terra batida",
        "Hard court": "Campo duro",
        "Synthetic grass": "Relva sintética",
        "Indoor synthetic tennis floor": "Piso sintético de ténis interior",
        "Unspecified all-weather": "Piso para todo o tempo não especificado",
        "Surface type not specified": "Piso não especificado",
        "Public seasonally; members can invite guests": "Aberto ao público sazonalmente; os sócios podem convidar",
        "Indoor is preferable for ": "É preferível jogar no interior devido a ",
        "cold (": "frio (",
        "strong wind (": "vento forte (",
        "rain forecast (": "chuva prevista (",
        "rain likely (": "probabilidade de chuva (",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "As condições exteriores parecem aceitáveis; em caso de dúvida, os campos exteriores costumam ser mais baratos.",
        "A forecast is not available for a past date.": "Não há previsão meteorológica para uma data passada.",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "Ainda não há previsão para essa hora. Escolha um horário futuro ou volte a consultar mais tarde.",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "Não há previsão para esse horário. O Open-Meteo abrange até 16 dias; os serviços alternativos abrangem menos.",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "Sócios aproximados por campo. Verde ≤75, amarelo 76–150, vermelho >150; os intervalos usam o valor inferior para a cor. Use «Ordenar tabela por» para ordenar numericamente.",
        "Booking-portal credentials are available for this app session.": "As credenciais do portal de reservas estão disponíveis nesta sessão.",
        "Calculate cycling times to enable the cycling-time filter.": "Calcule os tempos de bicicleta para ativar este filtro.",
        "Calculating cycling times for both tables...": "A calcular os tempos de bicicleta para ambas as tabelas...",
        "Calculating cycling times for single courts...": "A calcular os tempos de bicicleta para os campos públicos...",
        "Calculating public-club cycling times...": "A calcular os tempos de bicicleta para os clubes públicos...",
        "Checking all public (non-member) clubs...": "A verificar todos os clubes abertos a não sócios...",
        "Club names and source-provided notes are shown in their original wording.": "Os nomes dos clubes e as notas das fontes são apresentados no idioma original.",
        "Could not load the Amsterdam weather forecast:": "Não foi possível carregar a previsão meteorológica de Amesterdão:",
        "Cycling-time calculation failed": "Falha ao calcular o tempo de bicicleta",
        "Forecast rainfall for the selected hour or forecast period.": "Chuva prevista para a hora ou período selecionado.",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "Incluir o USC, o Frans Otten Stadion e o Amstelpark Tennisclub na tabela e nas verificações dos clubes públicos.",
        "Include sign-in-required clubs": "Incluir clubes que exigem autenticação",
        "Introducé price": "Preço para convidados",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "Quer jogar à última hora? Experimente os campos públicos de Amesterdão. Não é possível reservá-los antecipadamente.",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "Procura um compromisso a longo prazo? Consulte abaixo os preços de adesão sénior destes clubes.",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "Sócios por campo: verde ≤75, amarelo 76–150, vermelho >150. Os valores assinalados são aproximados. A federação neerlandesa KNLTB recomenda 60 a 90 sócios por campo exterior iluminado.",
        "Open club site": "Abrir site do clube",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "Clubes públicos com disponibilidade, tempo de bicicleta, preços, pisos, páginas de reserva e outras informações",
        "Ranges use their lower value, and entries without a number are placed last.": "Os intervalos usam o valor inferior e as entradas sem número aparecem no fim.",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "Fundo da linha: verde = sem lista de espera; vermelho = com lista. Adesão sénior: verde ≤ 200 €, âmbar 201–275 €, vermelho >275 €; as cores do tempo de bicicleta mantêm-se.",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "Campos de ténis públicos independentes com bairros, moradas, pisos e tempos de bicicleta",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "Clubes de ténis com informações sobre adesão, preços, tempos de bicicleta, convidados, listas de espera e sites",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "O serviço meteorológico fornece previsões até 16 dias. Ainda não há previsão para esta data.",
        "This summary describes how the app currently handles data.": "Este resumo explica como a aplicação trata atualmente os dados.",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "Está à procura do clube de ténis ideal? Explore clubes em Amesterdão para jogar ocasionalmente ou aderir a longo prazo. Compare localizações, tempos de bicicleta e preços, consulte opções de adesão e verifique a disponibilidade para a data, hora e duração pretendidas, tudo num só lugar.",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "Tipos de campo disponíveis no horário escolhido: exterior, interior ou coberto.",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "Use «Ordenar tabela por» para ordenar numericamente; os intervalos de preços usam o valor inferior.",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "Use «Ordenar tabela por» para ordenar numericamente; os intervalos usam o valor inferior.",
        "🔓 Public (non-member) clubs": "🔓 Clubes abertos a não sócios",
    },
    "Русский": {
        "ascending": "по возрастанию",
        "descending": "по убыванию",
        "Cushioned hard court": "Амортизирующий хард",
        "Clay": "Грунт",
        "Hard court": "Хард",
        "Synthetic grass": "Искусственная трава",
        "Indoor synthetic tennis floor": "Крытое синтетическое теннисное покрытие",
        "Unspecified all-weather": "Покрытие для любой погоды не указано",
        "Surface type not specified": "Тип покрытия не указан",
        "Public seasonally; members can invite guests": "Сезонно открыт для всех; участники могут приглашать гостей",
        "Indoor is preferable for ": "Предпочтителен крытый корт из-за ",
        "cold (": "холод (",
        "strong wind (": "сильный ветер (",
        "rain forecast (": "прогноз дождя (",
        "rain likely (": "вероятность дождя (",
        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.": "Погодные условия на улице приемлемы; если выбор неочевиден, открытые корты обычно дешевле.",
        "A forecast is not available for a past date.": "Прогноз погоды для прошедшей даты недоступен.",
        "A forecast is not available for that hour yet. Choose a future time or check again later.": "Прогноз на это время пока недоступен. Выберите будущее время или попробуйте позже.",
        "A forecast is not available for that time. Open-Meteo covers up to 16 days; the fallback forecasts cover fewer days.": "Прогноз на это время недоступен. Open-Meteo предоставляет прогноз до 16 дней, запасные сервисы — на меньший срок.",
        "Approximate members per tennis court. Green ≤75, yellow 76–150, red >150; ranges use their lower value for coloring. Use Sort table by for numeric sorting.": "Примерное число участников на корт: зелёный ≤75, жёлтый 76–150, красный >150; для диапазона цвет определяется по нижней границе. Для сортировки используйте «Сортировать таблицу по».",
        "Booking-portal credentials are available for this app session.": "Данные для входа в систему бронирования доступны в этом сеансе приложения.",
        "Calculate cycling times to enable the cycling-time filter.": "Рассчитайте время на велосипеде, чтобы включить этот фильтр.",
        "Calculating cycling times for both tables...": "Рассчитывается время на велосипеде для обеих таблиц...",
        "Calculating cycling times for single courts...": "Рассчитывается время на велосипеде до общественных кортов...",
        "Calculating public-club cycling times...": "Рассчитывается время на велосипеде до открытых клубов...",
        "Checking all public (non-member) clubs...": "Проверяются все клубы, открытые для неучастников...",
        "Club names and source-provided notes are shown in their original wording.": "Названия клубов и примечания из источников отображаются в исходном виде.",
        "Could not load the Amsterdam weather forecast:": "Не удалось загрузить прогноз погоды в Амстердаме:",
        "Cycling-time calculation failed": "Не удалось рассчитать время на велосипеде",
        "Forecast rainfall for the selected hour or forecast period.": "Ожидаемые осадки за выбранный час или период прогноза.",
        "Include USC, Frans Otten Stadion, and Amstelpark Tennisclub in the public-club table and availability checks.": "Включить USC, Frans Otten Stadion и Amstelpark Tennisclub в таблицу открытых клубов и проверку доступности.",
        "Include sign-in-required clubs": "Включить клубы с обязательным входом",
        "Introducé price": "Цена для гостей",
        "Last-minute plans? Try one of Amsterdam's stand-alone courts. These courts cannot be booked in advance.": "Хотите сыграть в последний момент? Попробуйте общественные корты Амстердама. Их нельзя бронировать заранее.",
        "Looking for a longer-term commitment? Explore these club senior membership options below.": "Ищете клуб на долгий срок? Ниже представлены варианты годового членства.",
        "Members per court: green ≤75, yellow 76–150, red >150. Club membership and court figures are approximate where noted. The Dutch tennis federation (KNLTB) uses 60 to 90 members per lit outdoor court as a healthy guideline.": "Участников на корт: зелёный ≤75, жёлтый 76–150, красный >150. Отмеченные данные приблизительны. Федерация тенниса Нидерландов (KNLTB) считает нормой 60–90 участников на освещённый открытый корт.",
        "Open club site": "Открыть сайт клуба",
        "Public tennis clubs with availability, cycling time, prices, court surface, booking pages, and other information": "Открытые теннисные клубы: доступность, время на велосипеде, цены, покрытие кортов, страницы бронирования и другие сведения",
        "Ranges use their lower value, and entries without a number are placed last.": "Для диапазонов используется нижнее значение, записи без чисел размещаются в конце.",
        "Row background: green = no waiting list; red = waiting list. Senior membership-price text: green ≤ €200, amber €201–€275, red > €275; cycling-time text retains its travel-time color coding.": "Цвет строки: зелёный — списка ожидания нет, красный — есть. Годовой взнос: зелёный ≤ €200, жёлтый €201–€275, красный > €275; цвета времени на велосипеде сохраняют прежнее значение.",
        "Stand-alone public tennis courts with neighbourhoods, addresses, surfaces, and cycling times": "Общественные теннисные корты с районами, адресами, покрытием и временем на велосипеде",
        "Tennis clubs with membership access, prices, cycling times, guest policies, waiting lists, and club websites": "Теннисные клубы: членство, цены, время на велосипеде, правила для гостей, списки ожидания и сайты",
        "The weather service provides forecasts up to 16 days ahead. A forecast for this date is not available yet.": "Сервис предоставляет прогноз до 16 дней. Прогноз на эту дату пока недоступен.",
        "This summary describes how the app currently handles data.": "В этом кратком описании указано, как приложение обрабатывает данные.",
        "Trouble finding the right tennis club for you? No worries, we've got your back. Explore clubs across Amsterdam, whether you're looking for an occasional match or a longer-term commitment. Compare locations, cycling times and prices, explore membership options, and check availability for your chosen date, time and session length—all in one place.": "Не можете найти подходящий теннисный клуб? Изучите клубы Амстердама для разовых игр или долгосрочного членства. Сравните расположение, время на велосипеде и цены, посмотрите варианты членства и проверьте доступность на выбранные дату, время и длительность — всё в одном месте.",
        "Types of court available for the selected time, including outdoor, indoor, or covered.": "Типы кортов, доступных в выбранное время: открытые, крытые или под навесом.",
        "Use Sort table by for numeric sorting; price ranges use their lower amount.": "Для числовой сортировки используйте «Сортировать таблицу по»; в диапазонах цен учитывается нижняя граница.",
        "Use the Sort table by control for numeric sorting; ranges use their lower value.": "Для числовой сортировки используйте «Сортировать таблицу по»; в диапазонах учитывается нижняя граница.",
        "🔓 Public (non-member) clubs": "🔓 Клубы, открытые для неучастников",
    },
}


def _translations_for_language(language: str) -> dict[str, str]:
    if language in {"nl", "Nederlands"}:
        return DUTCH_TRANSLATIONS
    return {
        **ADDITIONAL_TRANSLATIONS.get(language, {}),
        **ADDITIONAL_TRANSLATION_EXTENSIONS.get(language, {}),
    }


def translate_text(value: Any, language: str) -> Any:
    if not isinstance(value, str) or language == "English":
        return value
    translations = _translations_for_language(language)
    translated = translations.get(value)
    if translated is not None:
        return translated
    if value.startswith("Could not verify - "):
        prefix = translations.get("Could not verify - ")
        if prefix:
            return prefix + value.removeprefix("Could not verify - ")
    if value.startswith("Not checked"):
        prefix = translations.get("Not checked")
        if prefix:
            return prefix + value.removeprefix("Not checked")
    if value.startswith("✅ Available"):
        prefix = translations.get("✅ Available")
        if prefix:
            return prefix + value.removeprefix("✅ Available")
    if value.startswith("Indoor is preferable for "):
        prefix = translations.get("Indoor is preferable for ")
        if prefix:
            reasons = value.removeprefix("Indoor is preferable for ")
            for source_prefix in (
                "cold (",
                "strong wind (",
                "rain forecast (",
                "rain likely (",
            ):
                reasons = reasons.replace(
                    source_prefix,
                    translations.get(source_prefix, source_prefix),
                )
            return prefix + reasons
    for source_prefix in ("☀️ Outdoor", "🏠 Indoor", "⛱️ Covered"):
        if value.startswith(source_prefix):
            translated_prefix = translations.get(source_prefix)
            if translated_prefix:
                return translated_prefix + value.removeprefix(source_prefix)
    return value


def translate_to_english(value: Any, language: str) -> Any:
    if not isinstance(value, str):
        return value
    normalized_language = "Nederlands" if language == "nl" else language
    all_translations = [(normalized_language, _translations_for_language(language))]
    all_translations.extend(
        (label, _translations_for_language(label))
        for label in ("Nederlands", *ADDITIONAL_TRANSLATIONS)
        if label != normalized_language
    )
    for _label, translations in all_translations:
        reverse = {translated: source for source, translated in translations.items()}
        if value in reverse:
            return reverse[value]
        for source_prefix in (
            "Could not verify - ",
            "Not checked",
            "✅ Available",
            "☀️ Outdoor",
            "🏠 Indoor",
            "⛱️ Covered",
        ):
            translated_prefix = translations.get(source_prefix)
            if translated_prefix and value.startswith(translated_prefix):
                return source_prefix + value.removeprefix(translated_prefix)
    return value


def translate_sort_option(value: str, language: str) -> str:
    for suffix, separator, closing in (
        (" (ascending)", " (", ")"),
        (" (descending)", " (", ")"),
        (" - ascending", " - ", ""),
        (" - descending", " - ", ""),
    ):
        if value.endswith(suffix):
            direction = suffix.strip(" ()-")
            field = value[: -len(suffix)]
            return (
                f"{translate_text(field, language)}{separator}"
                f"{translate_text(direction, language)}{closing}"
            )
    return str(translate_text(value, language))


def localize_frame(frame: Any, language: str) -> Any:
    if language not in {"nl", "Nederlands", *ADDITIONAL_TRANSLATIONS}:
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


ADDITIONAL_PRIVACY_STATEMENTS = {
    "中文 (简体)": """
**数据负责人：** Casper Witlox / Amsterdam Court Finder<br>
**隐私联系邮箱：** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### 应用使用的数据
- **起始地址和骑行路线：** 只有在你同意并请求计算路线后，起始地址和所选俱乐部地址才会发送给 Google Routes。地址和路线结果保留在当前应用会话中；运营者也可能预设起始地址。
- **预订平台登录信息：** 登录信息通过应用发送到服务器，暂存在当前 Streamlit 会话内存中，并在开始查询时转发给相应预订平台。应用不会将其写入俱乐部数据文件。会话结束或应用重启时会清除；预订平台依其自身隐私政策处理这些信息。
- **空位查询：** 所选日期、时间、时长和公开预订页面会发送给 Meet & Play 或其他相关预订服务。应用不会替你预订。
- **天气：** 天气查询使用阿姆斯特丹固定位置，不会向天气服务提供你的起始地址。日期和时间在本地与天气预报匹配。
- **俱乐部信息：** 俱乐部信息由应用本地维护，可能过时。

### 存储和外部服务
起始地址、路线结果和预订登录信息保存在当前应用会话中，不会添加到俱乐部数据文件。应用托管在 [Render](https://render.com/privacy)，其可能为托管和安全处理技术连接信息。[Google](https://policies.google.com/privacy)、天气服务和预订平台会按各自政策处理你使用其功能时提供的数据。

如需访问、更正或删除数据，或有隐私问题，请联系 [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)。空位和价格是查询时的快照，预订前请向俱乐部确认。
""",
    "हिन्दी": """
**डेटा नियंत्रक:** Casper Witlox / Amsterdam Court Finder<br>
**गोपनीयता संपर्क:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### ऐप द्वारा उपयोग किया जाने वाला डेटा
- **शुरुआती पता और साइकिल मार्ग:** आपकी सहमति और मार्ग गणना के अनुरोध के बाद ही पता और चुने हुए क्लबों के पते Google Routes को भेजे जाते हैं। पता और मार्ग परिणाम मौजूदा ऐप सत्र में रहते हैं; संचालक डिफ़ॉल्ट शुरुआती पता भी सेट कर सकता है।
- **बुकिंग पोर्टल लॉगिन जानकारी:** यह ऐप के माध्यम से सर्वर पर भेजी जाती है, मौजूदा Streamlit सत्र की मेमोरी में रखी जाती है और जाँच शुरू होने पर संबंधित पोर्टल को भेजी जाती है। ऐप इसे क्लब डेटा फ़ाइल में नहीं लिखता। सत्र समाप्त होने या ऐप फिर शुरू होने पर यह हट जाती है; पोर्टल अपने नियमों के अनुसार इसे संभालते हैं।
- **उपलब्धता जाँच:** चुनी गई तारीख, समय, अवधि और सार्वजनिक बुकिंग पेज Meet & Play या संबंधित बुकिंग सेवाओं से अनुरोध किए जाते हैं। ऐप कोई बुकिंग नहीं करता।
- **मौसम:** मौसम की जानकारी एम्स्टर्डम के निश्चित स्थान के लिए ली जाती है। आपका शुरुआती पता मौसम सेवाओं के साथ साझा नहीं होता।
- **क्लब की जानकारी:** क्लब का डेटा ऐप में स्थानीय रूप से रखा जाता है और पुराना हो सकता है।

### संग्रहण और बाहरी सेवाएँ
शुरुआती पता, मार्ग परिणाम और बुकिंग लॉगिन जानकारी सक्रिय ऐप सत्र में रखी जाती है, क्लब डेटा फ़ाइल में नहीं। ऐप [Render](https://render.com/privacy) पर होस्ट है, जो होस्टिंग और सुरक्षा के लिए तकनीकी जानकारी संसाधित कर सकता है। [Google](https://policies.google.com/privacy), मौसम सेवाएँ और बुकिंग पोर्टल अपने नियमों के अनुसार डेटा संसाधित करते हैं।

डेटा देखने, सुधारने या हटाने तथा गोपनीयता संबंधी प्रश्नों के लिए [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl) पर संपर्क करें। उपलब्धता और कीमतें केवल जाँच के समय की स्थिति हैं; बुकिंग से पहले क्लब से पुष्टि करें।
""",
    "Español": """
**Responsable:** Casper Witlox / Amsterdam Court Finder<br>
**Contacto de privacidad:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### Datos que utiliza la aplicación
- **Dirección de origen y rutas en bicicleta:** la dirección de origen y las direcciones de los clubes seleccionados solo se envían a Google Routes cuando das tu consentimiento y solicitas calcular rutas. Los datos permanecen en la sesión actual; el operador también puede configurar una dirección predeterminada.
- **Credenciales de reservas:** se envían al servidor a través de la aplicación, se mantienen en la memoria de la sesión actual de Streamlit y se envían al portal correspondiente al iniciar una consulta. La aplicación no las guarda en el archivo de clubes. Se eliminan al terminar la sesión o reiniciar la aplicación; cada portal las trata según su propia política.
- **Consultas de disponibilidad:** la fecha, hora y duración elegidas, junto con las páginas públicas de reservas, se consultan en Meet & Play y otros servicios pertinentes. La aplicación no realiza reservas.
- **Meteorología:** se consulta para una ubicación fija en Ámsterdam. Tu dirección de origen no se comparte con los proveedores meteorológicos.
- **Información de clubes:** se mantiene localmente en la aplicación y puede quedar desactualizada.

### Almacenamiento y servicios externos
La dirección de origen, los resultados de rutas y las credenciales se conservan en la sesión activa, no en el archivo de clubes. La aplicación está alojada en [Render](https://render.com/privacy), que puede procesar datos técnicos para prestar el servicio y protegerlo. [Google](https://policies.google.com/privacy), los proveedores meteorológicos y los servicios de reservas tratan los datos conforme a sus propias políticas.

Para solicitar acceso, rectificación o eliminación, o plantear dudas sobre privacidad, escribe a [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl). La disponibilidad y los precios son una instantánea; confírmalos con el club antes de reservar.
""",
    "Français": """
**Responsable :** Casper Witlox / Amsterdam Court Finder<br>
**Contact vie privée :** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### Données utilisées par l'application
- **Adresse de départ et itinéraires à vélo :** l'adresse de départ et celles des clubs sélectionnés ne sont envoyées à Google Routes qu'après votre accord et une demande de calcul. Elles restent dans la session en cours ; l'exploitant peut aussi définir une adresse par défaut.
- **Identifiants des portails de réservation :** ils transitent par l'application vers le serveur, sont conservés dans la mémoire de la session Streamlit en cours et transmis au portail concerné lors d'une vérification. L'application ne les écrit pas dans le fichier des clubs. Ils sont supprimés à la fin de la session ou au redémarrage ; les portails les traitent selon leurs propres règles.
- **Vérification des disponibilités :** la date, l'heure et la durée choisies ainsi que les pages publiques de réservation sont consultées auprès de Meet & Play et des services concernés. L'application ne réserve aucun court.
- **Météo :** les prévisions concernent un emplacement fixe à Amsterdam. Votre adresse de départ n'est pas communiquée aux services météo.
- **Informations sur les clubs :** elles sont gérées localement et peuvent devenir obsolètes.

### Stockage et services externes
L'adresse de départ, les résultats d'itinéraires et les identifiants restent dans la session active, pas dans le fichier des clubs. L'application est hébergée par [Render](https://render.com/privacy), qui peut traiter des données techniques pour l'hébergement et la sécurité. [Google](https://policies.google.com/privacy), les services météo et les portails de réservation traitent les données selon leurs propres politiques.

Pour demander l'accès, la rectification ou la suppression de données, ou pour toute question, écrivez à [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl). Les disponibilités et prix sont des instantanés ; confirmez-les auprès du club avant de réserver.
""",
    "العربية": """
**مسؤول البيانات:** Casper Witlox / Amsterdam Court Finder<br>
**للتواصل بشأن الخصوصية:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### البيانات التي يستخدمها التطبيق
- **عنوان الانطلاق ومسارات ركوب الدراجة:** لا يُرسل عنوانك وعناوين الأندية المختارة إلى Google Routes إلا بعد موافقتك وطلب حساب المسارات. تبقى البيانات في جلسة التطبيق الحالية؛ وقد يحدد المشغّل عنوان انطلاق افتراضياً.
- **بيانات الدخول إلى بوابات الحجز:** تمر عبر التطبيق إلى الخادم، وتُحفظ في ذاكرة جلسة Streamlit الحالية، ثم تُرسل إلى بوابة الحجز المعنية عند بدء التحقق. لا يكتبها التطبيق في ملف بيانات الأندية. تُحذف عند انتهاء الجلسة أو إعادة تشغيل التطبيق، وتعالجها البوابات وفق سياساتها.
- **التحقق من التوفر:** يُطلب التاريخ والوقت والمدة المختارة وصفحات الحجز العامة من Meet & Play وخدمات الحجز ذات الصلة. لا يجري التطبيق أي حجز.
- **الطقس:** تُطلب بيانات الطقس لموقع ثابت في أمستردام، ولا يُشارك عنوان انطلاقك مع خدمات الطقس.
- **معلومات الأندية:** تُدار محلياً في التطبيق وقد تصبح قديمة.

### التخزين والخدمات الخارجية
يُحتفظ بعنوان الانطلاق ونتائج المسارات وبيانات الدخول في جلسة التطبيق النشطة، ولا تُضاف إلى ملف بيانات الأندية. يستضيف [Render](https://render.com/privacy) التطبيق وقد يعالج معلومات تقنية لأغراض الاستضافة والأمان. وتعالج [Google](https://policies.google.com/privacy) ومزودو الطقس والحجز البيانات وفق سياساتهم الخاصة.

لطلب الاطلاع على البيانات أو تصحيحها أو حذفها، أو لأي استفسار عن الخصوصية، راسل [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl). التوفر والأسعار لقطة وقت الاستعلام؛ يرجى تأكيدها مع النادي قبل الحجز.
""",
    "বাংলা": """
**ডেটার দায়িত্বে:** Casper Witlox / Amsterdam Court Finder<br>
**গোপনীয়তা যোগাযোগ:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### অ্যাপ যে ডেটা ব্যবহার করে
- **শুরুর ঠিকানা ও সাইকেল রুট:** আপনার সম্মতি এবং রুট গণনার অনুরোধের পরেই শুরুর ঠিকানা ও নির্বাচিত ক্লাবের ঠিকানা Google Routes-এ পাঠানো হয়। এগুলো বর্তমান অ্যাপ সেশনেই থাকে; পরিচালনাকারী একটি ডিফল্ট ঠিকানাও নির্ধারণ করতে পারেন।
- **বুকিং পোর্টালের লগইন তথ্য:** অ্যাপের মাধ্যমে সার্ভারে পাঠানো হয়, বর্তমান Streamlit সেশনের মেমোরিতে রাখা হয় এবং যাচাই শুরু হলে সংশ্লিষ্ট পোর্টালে পাঠানো হয়। অ্যাপ এগুলো ক্লাবের ডেটা ফাইলে লেখে না। সেশন শেষ হলে বা অ্যাপ পুনরায় চালু হলে মুছে যায়; পোর্টালগুলো তাদের নিজস্ব নীতি অনুসারে তথ্য প্রক্রিয়া করে।
- **উপলভ্যতা যাচাই:** নির্বাচিত তারিখ, সময় ও মেয়াদ এবং প্রকাশ্য বুকিং পৃষ্ঠা Meet & Play ও অন্যান্য প্রাসঙ্গিক বুকিং পরিষেবায় অনুরোধ করা হয়। অ্যাপ কোনো বুকিং সম্পন্ন করে না।
- **আবহাওয়া:** আমস্টারডামের একটি নির্দিষ্ট অবস্থানের পূর্বাভাস নেওয়া হয়। আপনার শুরুর ঠিকানা আবহাওয়া পরিষেবার সঙ্গে ভাগ করা হয় না।
- **ক্লাবের তথ্য:** অ্যাপে স্থানীয়ভাবে রাখা হয় এবং পুরোনো হতে পারে।

### সংরক্ষণ ও বাহ্যিক পরিষেবা
শুরুর ঠিকানা, রুটের ফলাফল ও লগইন তথ্য সক্রিয় অ্যাপ সেশনে থাকে, ক্লাবের ডেটা ফাইলে নয়। অ্যাপটি [Render](https://render.com/privacy)-এ হোস্ট করা; হোস্টিং ও নিরাপত্তার জন্য Render প্রযুক্তিগত তথ্য প্রক্রিয়া করতে পারে। [Google](https://policies.google.com/privacy), আবহাওয়া পরিষেবা ও বুকিং পোর্টালগুলো নিজ নিজ নীতি অনুসারে তথ্য প্রক্রিয়া করে।

তথ্য দেখা, সংশোধন বা মুছে ফেলার অনুরোধ এবং গোপনীয়তা-সংক্রান্ত প্রশ্নের জন্য [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)-এ যোগাযোগ করুন। উপলভ্যতা ও দাম যাচাইয়ের সময়কার তথ্য; বুকিংয়ের আগে ক্লাবের সঙ্গে নিশ্চিত করুন।
""",
    "Português": """
**Responsável pelos dados:** Casper Witlox / Amsterdam Court Finder<br>
**Contacto de privacidade:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### Dados utilizados pela aplicação
- **Morada de partida e percursos de bicicleta:** a sua morada e as moradas dos clubes selecionados só são enviadas ao Google Routes após o seu consentimento e pedido de cálculo. Os dados ficam na sessão atual; o operador também pode definir uma morada predefinida.
- **Credenciais dos portais de reserva:** são enviadas ao servidor através da aplicação, mantidas na memória da sessão Streamlit atual e encaminhadas para o portal relevante quando inicia uma consulta. A aplicação não as grava no ficheiro de clubes. São removidas quando a sessão termina ou a aplicação reinicia; os portais tratam-nas segundo as suas próprias políticas.
- **Verificação de disponibilidade:** a data, hora e duração escolhidas e as páginas públicas de reserva são consultadas no Meet & Play e noutros serviços relevantes. A aplicação não efetua reservas.
- **Meteorologia:** os dados são consultados para uma localização fixa em Amesterdão. A sua morada de partida não é partilhada com os fornecedores meteorológicos.
- **Informações dos clubes:** são mantidas localmente na aplicação e podem ficar desatualizadas.

### Armazenamento e serviços externos
A morada de partida, os resultados dos percursos e as credenciais ficam na sessão ativa, não no ficheiro de clubes. A aplicação está alojada na [Render](https://render.com/privacy), que pode tratar dados técnicos para alojamento e segurança. [Google](https://policies.google.com/privacy), serviços meteorológicos e portais de reserva tratam os dados segundo as respetivas políticas.

Para pedir acesso, correção ou eliminação de dados, ou colocar questões de privacidade, contacte [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl). A disponibilidade e os preços são uma fotografia do momento; confirme-os com o clube antes de reservar.
""",
    "Русский": """
**Ответственный за данные:** Casper Witlox / Amsterdam Court Finder<br>
**Контакт по вопросам конфиденциальности:** [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl)

### Какие данные использует приложение
- **Начальный адрес и велосипедные маршруты:** начальный адрес и адреса выбранных клубов отправляются в Google Routes только после вашего согласия и запроса расчёта. Данные остаются в текущем сеансе приложения; оператор также может задать адрес по умолчанию.
- **Данные входа в системы бронирования:** проходят через приложение на сервер, хранятся в памяти текущего сеанса Streamlit и передаются соответствующему сервису при запуске проверки. Приложение не записывает их в файл с данными клубов. Они удаляются при завершении сеанса или перезапуске приложения; сервисы обрабатывают их по собственным правилам.
- **Проверка доступности:** выбранные дата, время и длительность, а также открытые страницы бронирования запрашиваются у Meet & Play и других соответствующих сервисов. Приложение не оформляет бронирования.
- **Погода:** прогноз запрашивается для фиксированного местоположения в Амстердаме. Начальный адрес не передаётся поставщикам погоды.
- **Информация о клубах:** хранится локально в приложении и может устареть.

### Хранение и внешние сервисы
Начальный адрес, результаты расчёта маршрутов и данные входа хранятся в активном сеансе, а не в файле клубов. Приложение размещено на [Render](https://render.com/privacy); сервис может обрабатывать технические данные для хостинга и безопасности. [Google](https://policies.google.com/privacy), погодные службы и сервисы бронирования обрабатывают данные согласно собственным политикам.

Чтобы запросить доступ к данным, их исправление или удаление, либо задать вопрос о конфиденциальности, напишите на [info@amsterdamcourtfinder.nl](mailto:info@amsterdamcourtfinder.nl). Доступность и цены отражают момент проверки; перед бронированием уточните их у клуба.
""",
}


def privacy_statement(
    language: str,
    analytics_enabled: bool = False,
    sponsor_enabled: bool = False,
) -> str:
    if language in ADDITIONAL_PRIVACY_STATEMENTS:
        statement = ADDITIONAL_PRIVACY_STATEMENTS[language]
    elif language in {"nl", "Nederlands"}:
        statement = """
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
    else:
        statement = """
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
    if analytics_enabled:
        statement = (
            statement.rstrip()
            + "\n\n### Analytics\n"
            + cloudflare_analytics_notice(language)
        )
    if sponsor_enabled:
        statement = (
            statement.rstrip()
            + "\n\n### Sponsored links\n"
            + sponsor_link_notice(language)
        )
    return statement


_CLOUDFLARE_ANALYTICS_NOTICES = {
    "English": (
        "[Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/) "
        "is enabled on this site. It reports page views, visits, and performance; "
        "Cloudflare states it does not collect or use visitors' personal data. "
        "It does not report sponsor-link conversions."
    ),
    "Nederlands": (
        "[Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/) "
        "is op deze site actief. Het rapporteert paginaweergaven, bezoeken en "
        "prestaties; Cloudflare geeft aan geen persoonsgegevens van bezoekers "
        "te verzamelen of te gebruiken. Het rapporteert geen conversies via "
        "sponsorlinks."
    ),
    "中文 (简体)": (
        "本网站启用了 [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/)，"
        "用于报告页面浏览量、访问量和性能。Cloudflare 表示该服务不会收集或使用访客的个人数据，"
        "也不会报告赞助链接的转化情况。"
    ),
    "हिन्दी": (
        "इस साइट पर [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/) "
        "सक्रिय है। यह पेज व्यू, विज़िट और प्रदर्शन की रिपोर्ट करता है। Cloudflare के अनुसार यह "
        "आगंतुकों का व्यक्तिगत डेटा एकत्र या उपयोग नहीं करता और प्रायोजक लिंक के रूपांतरण नहीं बताता।"
    ),
    "Español": (
        "En este sitio está activado [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/). "
        "Informa de visitas, páginas vistas y rendimiento; Cloudflare indica que no recopila ni utiliza "
        "datos personales de los visitantes. No informa de conversiones en enlaces patrocinados."
    ),
    "Français": (
        "[Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/) "
        "est activé sur ce site. Il mesure les visites, les pages vues et les performances ; "
        "Cloudflare indique ne pas collecter ni utiliser les données personnelles des visiteurs. "
        "Il ne mesure pas les conversions des liens sponsorisés."
    ),
    "العربية": (
        "تم تفعيل [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/) "
        "على هذا الموقع لعرض الزيارات ومشاهدات الصفحات والأداء. وتذكر Cloudflare أنها لا تجمع البيانات "
        "الشخصية للزوار ولا تستخدمها، كما أنها لا تعرض تحويلات روابط الرعاية."
    ),
    "বাংলা": (
        "এই সাইটে [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/) "
        "চালু আছে। এটি পৃষ্ঠা দেখা, ভিজিট এবং পারফরম্যান্সের তথ্য দেয়। Cloudflare জানায়, এটি "
        "দর্শকদের ব্যক্তিগত তথ্য সংগ্রহ বা ব্যবহার করে না এবং স্পনসর লিংকের রূপান্তর জানায় না।"
    ),
    "Português": (
        "O [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/) "
        "está ativo neste site. Ele informa visitas, visualizações de página e desempenho; "
        "a Cloudflare afirma que não coleta nem usa dados pessoais dos visitantes. "
        "Ele não informa conversões de links patrocinados."
    ),
    "Русский": (
        "На сайте включена служба [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/). "
        "Она сообщает о посещениях, просмотрах страниц и производительности. Cloudflare заявляет, "
        "что не собирает и не использует персональные данные посетителей; конверсии по спонсорским ссылкам "
        "не отслеживаются."
    ),
}


def cloudflare_analytics_notice(language: str) -> str:
    normalized_language = "Nederlands" if language == "nl" else language
    return _CLOUDFLARE_ANALYTICS_NOTICES.get(
        normalized_language,
        _CLOUDFLARE_ANALYTICS_NOTICES["English"],
    )


_SPONSOR_LINK_NOTICES = {
    "English": (
        "When a sponsor is configured, its links include generic UTM source, "
        "medium, and campaign parameters so the sponsor can recognize referrals "
        "in its own analytics. This app does not add personal identifiers or "
        "record individual sponsor clicks."
    ),
    "Nederlands": (
        "Als er een sponsor is ingesteld, bevatten de links algemene UTM-bron-, "
        "medium- en campagneparameters zodat de sponsor verwijzingen in de "
        "eigen analytics kan herkennen. Deze app voegt geen persoonlijke "
        "identificatie toe en registreert geen individuele sponsor-kliks."
    ),
    "中文 (简体)": (
        "配置赞助商后，赞助链接会包含通用的 UTM 来源、媒介和活动参数，供赞助商在自己的分析工具中识别引荐流量。"
        "本应用不会添加个人标识，也不会记录个人赞助链接点击。"
    ),
    "हिन्दी": (
        "प्रायोजक सेट होने पर उसके लिंक में सामान्य UTM स्रोत, माध्यम और अभियान पैरामीटर होते हैं, "
        "ताकि प्रायोजक अपने विश्लेषण में रेफ़रल पहचान सके। यह ऐप व्यक्तिगत पहचानकर्ता नहीं जोड़ता "
        "और अलग-अलग प्रायोजक क्लिक दर्ज नहीं करता।"
    ),
    "Español": (
        "Cuando hay un patrocinador, sus enlaces incluyen parámetros UTM genéricos de origen, "
        "medio y campaña para que pueda reconocer las visitas referidas en sus propias analíticas. "
        "Esta aplicación no añade identificadores personales ni registra clics individuales."
    ),
    "Français": (
        "Lorsqu’un sponsor est configuré, ses liens comportent des paramètres UTM génériques "
        "de source, de support et de campagne afin qu’il puisse reconnaître les visites référées "
        "dans ses propres outils d’analyse. L’application n’ajoute aucun identifiant personnel "
        "et n’enregistre pas les clics individuels."
    ),
    "العربية": (
        "عند إعداد راعٍ، تتضمن روابطه معاملات UTM عامة للمصدر والوسيط والحملة، لكي يتمكن الراعي من "
        "تمييز الزيارات المُحالة في أدوات التحليل الخاصة به. لا يضيف التطبيق معرّفات شخصية ولا يسجل "
        "نقرات الرعاية الفردية."
    ),
    "বাংলা": (
        "স্পনসর সেট করা থাকলে তার লিংকে সাধারণ UTM উৎস, মাধ্যম ও ক্যাম্পেইন প্যারামিটার থাকে, "
        "যাতে স্পনসর নিজের অ্যানালিটিক্সে রেফারেল চিনতে পারে। এই অ্যাপ ব্যক্তিগত শনাক্তকারী যোগ করে না "
        "এবং আলাদা স্পনসর ক্লিক রেকর্ড করে না।"
    ),
    "Português": (
        "Quando há um patrocinador, os links incluem parâmetros UTM genéricos de origem, meio e campanha "
        "para que ele identifique visitas encaminhadas nas próprias ferramentas de análise. "
        "Este aplicativo não adiciona identificadores pessoais nem registra cliques individuais."
    ),
    "Русский": (
        "Если настроен спонсор, его ссылки содержат общие параметры UTM источника, канала и кампании, "
        "чтобы спонсор мог распознавать переходы в своей аналитике. Приложение не добавляет личные "
        "идентификаторы и не записывает отдельные клики по спонсорским ссылкам."
    ),
}


def sponsor_link_notice(language: str) -> str:
    normalized_language = "Nederlands" if language == "nl" else language
    return _SPONSOR_LINK_NOTICES.get(
        normalized_language,
        _SPONSOR_LINK_NOTICES["English"],
    )
