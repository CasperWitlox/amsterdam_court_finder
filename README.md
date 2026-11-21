# Amsterdam Court Finder

A Streamlit dashboard for comparing tennis clubs in Amsterdam and checking court availability for a selected date and time. It can also show cycling distances, prices, and other club information.

## Repository files

- [`tennis_court_finder_app.py`](./tennis_court_finder_app.py) — The main Streamlit application: displays the dashboard, club information, route and price details, and availability-check controls.
- [`tennis_browser_worker.py`](./tennis_browser_worker.py) — Runs the browser-based checks that visit booking websites and report court availability.
- [`tennis_ui.py`](./tennis_ui.py) — Contains UI translations, club filtering helpers, and the in-app privacy disclosure.
- [`monetization.py`](./monetization.py) — Validates optional sponsor and Cloudflare Web Analytics configuration.
- [`scripts/build_static_site.py`](./scripts/build_static_site.py) — Generates a separate searchable static directory, sport/location pages, profiles, and advertiser information from the public app data.
- [`static_site/catalog_import.example.json`](./static_site/catalog_import.example.json) — Schema example for adding source-backed venues and sports; it is not included in the live directory.
- [`static_site/catalog_import.json`](./static_site/catalog_import.json) — Additional verified venue entries to publish in the static directory.
- [`docs/advertiser-outreach.md`](./docs/advertiser-outreach.md) — Sponsorship pilot email and a permission-aware prospecting checklist.
- [`requirements.txt`](./requirements.txt) — Lists the Python packages required to run the application.
- [`requirements-static.txt`](./requirements-static.txt) — Build-only dependencies for generating the static pages.
- [`packages.txt`](./packages.txt) — Lists Linux system packages needed by Chromium when the app is deployed on Streamlit Community Cloud.
- [`Dockerfile`](./Dockerfile) — Builds the Render image, including Playwright's headless Chromium shell.
- [`.dockerignore`](./.dockerignore) — Excludes local files and secrets from the Docker build context.
- [`tennis_hero.svg`](./tennis_hero.svg) — SVG illustration used in the app’s header.
- [`tennis_court_background.svg`](./tennis_court_background.svg) — SVG artwork used as a court-themed background.
- [`.gitignore`](./.gitignore) — Lists files Git should leave out of the repository, such as local or generated files.
- [`README.md`](./README.md) — This file; explains the project and its repository files.

## Configuration and privacy

Configure API keys and any booking credentials through the deployment platform’s secrets settings or your local environment. **Do not add private keys, passwords, or other credentials to the repository.**

The weather widget uses Open-Meteo when available. To show precipitation
probability when that service is rate-limited, optionally create a free
[WeatherAPI.com](https://www.weatherapi.com/signup.aspx) key and set
`WEATHERAPI_API_KEY` in Render's environment variables. Its free plan provides
hourly forecasts with rain chance for up to three days; MET Norway remains the
no-key fallback for later dates.

## Dashboard features

The dashboard offers English and Dutch, plus Mandarin Chinese, Hindi, Spanish,
French, Arabic, Bengali, Portuguese, and Russian. Club names and
source-provided notes remain in their original wording; some detailed
provider-supplied text may also remain in English. Shared club filters cover
neighbourhood, booking access, court surface, availability, and cycling time
when routes have been calculated. Club profiles summarize the current
availability result, prices, access details, and links to booking and club
websites. The in-app **Privacy & data** disclosure explains session handling
and the external services contacted by the dashboard, and appears at the
bottom of the page.

## Static directory and sponsorship

The static site is a lightweight, search-first venue directory for tennis and
padel in the Amsterdam area. It generates sport, location, and venue-profile
pages from the app's existing public club data, plus any source-backed entries
in `static_site/catalog_import.json`. The importer accepts tennis, padel,
pickleball, and squash. Each imported venue must include a city, sports, and a
public HTTP(S) `source_url`; use `static_site/catalog_import.example.json` as
the field template. Do not copy another directory's listings without a
permitted source. The current import file is empty, so no additional or
nationwide listings are implied. The build uses source-controlled defaults and
does not export a user's local `TENNIS_FINDER_DATA` file.

Static pages do not run availability checks or call Google Routes. They link
to the existing Streamlit checker, official club booking pages, and Google
Maps search results without embedding a map or requiring a Maps API key. This
keeps directory traffic and SEO pages off the Render service; availability
remains on-demand in the existing app.

Build locally on Windows after installing the project requirements:

```powershell
.\.venv\Scripts\python.exe scripts\build_static_site.py
```

The generated site is written to the ignored `static_site/dist` directory.
For Cloudflare Pages, connect the repository, use the repository root as the
project root, set the build command to
`python -m pip install -r requirements-static.txt && python scripts/build_static_site.py`,
and set the output directory to `static_site/dist`. Attach a subdomain such as
`directory.amsterdamcourtfinder.nl` so the current Render root domain remains
unchanged. Set `DIRECTORY_SITE_URL` to the final HTTPS URL at build time. After
the Pages site is deployed, set the same variable in Render so the checker
shows a directory link.

Enable Cloudflare Web Analytics under the Pages project's **Metrics** tab for
the static pages. For the Render checker, add its hostname as a separate
Cloudflare Web Analytics site, then set the token from Cloudflare's snippet as
`CLOUDFLARE_WEB_ANALYTICS_TOKEN` in Render. The app only loads the beacon when a
valid token is configured and then adds a translated disclosure to **Privacy
& data**. Do not enable both automatic Pages injection and a manual token on
the same static hostname. Cloudflare reports visits and page performance; it
does not provide sponsor-click conversion counts. Sponsor URLs carry generic
UTM campaign tags so the advertiser can measure referred visits in its own
analytics.

The optional direct-sponsor card appears only when all three of these
environment variables are configured in Render and in the static build
environment:

- `ACF_SPONSOR_NAME`
- `ACF_SPONSOR_MESSAGE`
- `ACF_SPONSOR_URL` (HTTPS only)

Leave them unset when there is no sponsor. Paid placements are labelled and
do not change venue ordering. No audience figures are published until actual
analytics data exists. The advertiser page offers a fixed-fee 30-day pilot
without promising bookings.

For Netherlands business email outreach, see
[`docs/advertiser-outreach.md`](./docs/advertiser-outreach.md). In particular,
do not treat every publicly visible business email address as permission for
commercial outreach; follow the address's stated purpose, identify the sender,
include a valid postal address, and honor objections.

## Deploy to Render with a custom domain

The app uses Playwright with Chromium, so deploy it to Render as a Docker web
service:

1. Push this repository to GitHub and create a **New > Web Service** in the
   [Render Dashboard](https://dashboard.render.com/), connected to this repo.
2. Select **Docker** as the runtime and use the root `Dockerfile`. The image
   installs the app dependencies and Chromium.
3. Set the health check path to `/_stcore/health`. Meet & Play calendars are
   checked directly from their date-specific server-rendered pages, one
   lightweight HTTP request at a time and at least one second apart. Pages that
   cannot be interpreted fall back to the browser checker. Rate-limited or
   failed HTTP responses are reported without a slow browser retry. Other
   browser checks reuse one Chromium process and run sequentially, with portal
   contexts closed after each check to limit memory use. The free plan's 512 MB
   can still be tight; if the service restarts or checks fail, consider a plan
   with at least 2 GB of RAM.
4. Add required secrets, such as `GOOGLE_MAPS_API_KEY`, and the optional
   `WEATHERAPI_API_KEY` under the service's **Environment** settings. Do not add
   them to the Dockerfile or repository.
5. After the first successful deploy, open the service's **Settings >
   Custom Domains**, add `amsterdamcourtfinder.nl`, and follow the DNS records
   shown by Render for your domain provider. Render can also redirect the `www`
   hostname to the root domain.
6. Verify the domain in Render. Render provisions HTTPS after DNS is correct.

See Render's [Docker deployment](https://render.com/docs/docker) and
[custom domain](https://render.com/docs/custom-domains) guides for current
dashboard and DNS instructions. Do not remove the existing Streamlit Community
Cloud deployment until the Render service and custom domain have been verified.
