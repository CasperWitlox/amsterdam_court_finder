# Amsterdam Court Finder

A Streamlit dashboard for comparing tennis clubs in Amsterdam and checking court availability for a selected date and time. It can also show cycling distances, prices, and other club information.

## Repository files

- [`tennis_court_finder_app.py`](./tennis_court_finder_app.py) — The main Streamlit application: displays the dashboard, club information, route and price details, and availability-check controls.
- [`tennis_browser_worker.py`](./tennis_browser_worker.py) — Runs the browser-based checks that visit booking websites and report court availability.
- [`requirements.txt`](./requirements.txt) — Lists the Python packages required to run the application.
- [`packages.txt`](./packages.txt) — Lists Linux system packages needed by Chromium when the app is deployed on Streamlit Community Cloud.
- [`tennis_hero.svg`](./tennis_hero.svg) — SVG illustration used in the app’s header.
- [`tennis_court_background.svg`](./tennis_court_background.svg) — SVG artwork used as a court-themed background.
- [`.gitignore`](./.gitignore) — Lists files Git should leave out of the repository, such as local or generated files.
- [`README.md`](./README.md) — This file; explains the project and its repository files.

## Configuration and privacy

Configure API keys and any booking credentials through the deployment platform’s secrets settings or your local environment. **Do not add private keys, passwords, or other credentials to the repository.**
