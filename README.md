# Amsterdam Court Finder

A Streamlit dashboard for comparing tennis clubs in Amsterdam and checking court availability for a selected date and time. It can also show cycling distances, prices, and other club information.

## Repository files

- [`tennis_court_finder_app.py`](./tennis_court_finder_app.py) — The main Streamlit application: displays the dashboard, club information, route and price details, and availability-check controls.
- [`tennis_browser_worker.py`](./tennis_browser_worker.py) — Runs the browser-based checks that visit booking websites and report court availability.
- [`requirements.txt`](./requirements.txt) — Lists the Python packages required to run the application.
- [`packages.txt`](./packages.txt) — Lists Linux system packages needed by Chromium when the app is deployed on Streamlit Community Cloud.
- [`Dockerfile`](./Dockerfile) — Builds the Render image, including Playwright's headless Chromium shell.
- [`.dockerignore`](./.dockerignore) — Excludes local files and secrets from the Docker build context.
- [`tennis_hero.svg`](./tennis_hero.svg) — SVG illustration used in the app’s header.
- [`tennis_court_background.svg`](./tennis_court_background.svg) — SVG artwork used as a court-themed background.
- [`.gitignore`](./.gitignore) — Lists files Git should leave out of the repository, such as local or generated files.
- [`README.md`](./README.md) — This file; explains the project and its repository files.

## Configuration and privacy

Configure API keys and any booking credentials through the deployment platform’s secrets settings or your local environment. **Do not add private keys, passwords, or other credentials to the repository.**

## Deploy to Render with a custom domain

The app uses Playwright with Chromium, so deploy it to Render as a Docker web
service:

1. Push this repository to GitHub and create a **New > Web Service** in the
   [Render Dashboard](https://dashboard.render.com/), connected to this repo.
2. Select **Docker** as the runtime and use the root `Dockerfile`. The image
   installs the app dependencies and Chromium.
3. Set the health check path to `/_stcore/health`. Choose a service plan with
   enough memory for Streamlit and Chromium; the free plan may be constrained
   during browser checks.
4. Add required secrets, such as `GOOGLE_MAPS_API_KEY`, under the service's
   **Environment** settings. Do not add them to the Dockerfile or repository.
5. After the first successful deploy, open the service's **Settings >
   Custom Domains**, add `amsterdamcourtfinder.nl`, and follow the DNS records
   shown by Render for your domain provider. Render can also redirect the `www`
   hostname to the root domain.
6. Verify the domain in Render. Render provisions HTTPS after DNS is correct.

See Render's [Docker deployment](https://render.com/docs/docker) and
[custom domain](https://render.com/docs/custom-domains) guides for current
dashboard and DNS instructions. Do not remove the existing Streamlit Community
Cloud deployment until the Render service and custom domain have been verified.
