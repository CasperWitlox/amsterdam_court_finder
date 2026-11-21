import unittest
from urllib.parse import parse_qs, urlsplit

from monetization import (
    Sponsor,
    cloudflare_analytics_markup,
    load_sponsor,
    sponsor_click_url,
)


class MonetizationTests(unittest.TestCase):
    def test_sponsor_is_optional_but_requires_complete_valid_configuration(self):
        self.assertIsNone(load_sponsor({}))

        with self.assertRaisesRegex(ValueError, "configuration is incomplete"):
            load_sponsor({"ACF_SPONSOR_NAME": "Local shop"})

        with self.assertRaisesRegex(ValueError, "HTTPS URL"):
            load_sponsor(
                {
                    "ACF_SPONSOR_NAME": "Local shop",
                    "ACF_SPONSOR_MESSAGE": "Tennis gear in Amsterdam.",
                    "ACF_SPONSOR_URL": "http://example.nl",
                }
            )

    def test_sponsor_url_keeps_existing_query_and_replaces_campaign_tags(self):
        sponsor = Sponsor(
            name="Racket Shop Amsterdam",
            message="Local tennis equipment.",
            url="https://example.nl/shop?ref=acf&utm_source=old#offers",
        )

        result = urlsplit(sponsor_click_url(sponsor))

        self.assertEqual(result.scheme, "https")
        self.assertEqual(result.fragment, "offers")
        self.assertEqual(
            parse_qs(result.query),
            {
                "ref": ["acf"],
                "utm_source": ["amsterdamcourtfinder"],
                "utm_medium": ["sponsored"],
                "utm_campaign": ["racket-shop-amsterdam"],
            },
        )

    def test_cloudflare_beacon_is_optional_and_rejects_markup_in_tokens(self):
        self.assertIsNone(cloudflare_analytics_markup({}))
        markup = cloudflare_analytics_markup(
            {"CLOUDFLARE_WEB_ANALYTICS_TOKEN": "12345678-90ab"}
        )
        self.assertIn("https://static.cloudflareinsights.com/beacon.min.js", markup)
        self.assertIn("12345678-90ab", markup)
        self.assertNotIn("<script>alert", markup)

        with self.assertRaisesRegex(ValueError, "must contain"):
            cloudflare_analytics_markup(
                {"CLOUDFLARE_WEB_ANALYTICS_TOKEN": '"><script>alert(1)'}
            )


if __name__ == "__main__":
    unittest.main()
