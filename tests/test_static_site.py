import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_static_site


class StaticSiteTests(unittest.TestCase):
    def test_current_catalog_marks_only_source_backed_padel_venues(self):
        venues = build_static_site.build_catalog(
            build_static_site.STATIC_ROOT / "catalog_import.json"
        )
        by_name = {venue["name"]: venue for venue in venues}

        self.assertIn("padel", by_name["Tennisclub Gaasperpark"]["sports"])
        self.assertIn(
            "padel",
            by_name["Tennis- en padelvereniging Badhoevedorp"]["sports"],
        )
        self.assertEqual(len(venues), 51)
        for name in ("A.L.T.C. DDV", "L.T.C. Festina"):
            self.assertTrue(by_name[name]["source_url"])
            self.assertEqual(by_name[name]["last_verified"], "2026-11-21")
        self.assertIn("only members", by_name["A.L.T.C. DDV"]["access_notes"])
        self.assertTrue(all("tennis" in venue["sports"] for venue in venues))
        self.assertFalse(any("pickleball" in venue["sports"] for venue in venues))

    def test_import_rejects_unsafe_urls_and_unsupported_fields(self):
        base = {
            "name": "New club",
            "city": "Amsterdam",
            "sports": ["tennis"],
            "source_url": "https://example.nl",
        }

        with self.assertRaisesRegex(ValueError, "HTTP or HTTPS URL"):
            build_static_site._validate_imported_venue(
                {**base, "booking_url": "javascript:alert(1)"},
                1,
            )
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            build_static_site._validate_imported_venue(
                {**base, "verified": True},
                1,
            )

    def test_build_writes_searchable_profiles_sponsor_links_and_sitemap(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "dist"
            environment = {
                "ACF_SPONSOR_NAME": "Local racket shop",
                "ACF_SPONSOR_MESSAGE": "Equipment for Amsterdam players.",
                "ACF_SPONSOR_URL": "https://example.nl/shop",
                "CLOUDFLARE_WEB_ANALYTICS_TOKEN": "",
            }
            with (
                patch.object(build_static_site, "OUTPUT", output),
                patch.dict(os.environ, environment, clear=False),
            ):
                venue_count = build_static_site.build_site()

            index = (output / "index.html").read_text(encoding="utf-8")
            advertise = (
                output / "advertise" / "index.html"
            ).read_text(encoding="utf-8")
            sitemap = (output / "sitemap.xml").read_text(encoding="utf-8")

            self.assertEqual(venue_count, 51)
            self.assertIn('id="venue-search"', index)
            self.assertIn('id="sport-filter"', index)
            self.assertIn('aria-labelledby="area-heading"', index)
            self.assertIn('href="locations/amsterdam/index.html"', index)
            self.assertIn("37 listings", index)
            self.assertIn("37 locaties", index)
            self.assertIn("Local racket shop", index)
            self.assertIn("google.com/maps/search/", index)
            self.assertIn("utm_campaign=local-racket-shop", index)
            self.assertIn("listing counts, not visitor or impression counts", advertise)
            self.assertIn("/venues/", sitemap)
            self.assertNotIn("Lepelstraat", index)
            self.assertNotIn("GOOGLE_MAPS_API_KEY", index)
            self.assertTrue((output / "privacy" / "index.html").is_file())
            self.assertTrue((output / "assets" / "site.js").is_file())
            self.assertFalse(
                (output / "locations" / "amsterdam-area" / "padel" / "index.html").exists()
            )

    def test_import_file_must_be_a_json_list(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "catalog.json"
            path.write_text(json.dumps({"venues": []}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must be a JSON list"):
                build_static_site.load_catalog_import(path)


if __name__ == "__main__":
    unittest.main()
