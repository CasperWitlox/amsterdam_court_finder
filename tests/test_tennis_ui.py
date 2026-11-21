import unittest

import pandas as pd

from tennis_ui import (
    SUPPORTED_LANGUAGES,
    filter_club_rows,
    localize_frame,
    privacy_statement,
    translate_sort_option,
    translate_text,
    translate_to_english,
)


class TennisUiTests(unittest.TestCase):
    def test_dutch_table_labels_and_statuses_preserve_comparison_values(self):
        frame = pd.DataFrame(
            [
                {
                    "Club": "Tennisclub",
                    "Availability": "✅ Available",
                    "Booking access": "Public (non-members)",
                }
            ]
        )

        localized = localize_frame(frame, "Nederlands")

        self.assertIn("Beschikbaarheid", localized.columns)
        self.assertEqual(localized.iloc[0]["Beschikbaarheid"], "✅ Beschikbaar")
        self.assertEqual(
            translate_to_english(
                localized.iloc[0]["Toegang"],
                "Nederlands",
            ),
            "Public (non-members)",
        )

    def test_filters_combine_and_exclude_clubs_without_calculated_routes(self):
        rows = [
            {
                "Club": "Nearby",
                "Neighbourhood": "West",
                "Booking access": "Public (non-members)",
                "Availability": "✅ Available",
                "Cycling time": "12 min",
            },
            {
                "Club": "No route",
                "Neighbourhood": "West",
                "Booking access": "Public (non-members)",
                "Availability": "✅ Available",
                "Cycling time": "Not calculated",
            },
            {
                "Club": "Far",
                "Neighbourhood": "East",
                "Booking access": "Members only",
                "Availability": "Unavailable",
                "Cycling time": "25 min",
            },
        ]

        filtered = filter_club_rows(
            rows,
            neighborhoods={"West"},
            booking_access={"Public (non-members)"},
            court_surfaces={"Clay"},
            surface_categories_by_club={
                "Nearby": {"Clay"},
                "No route": {"Clay"},
                "Far": {"Hard court"},
            },
            availability="Available",
            max_cycling_minutes=15,
        )

        self.assertEqual([row["Club"] for row in filtered], ["Nearby"])

    def test_privacy_disclosure_uses_supplied_contact_and_booking_limit(self):
        statement = privacy_statement("Nederlands")

        self.assertIn("Casper Witlox / Amsterdam Court Finder", statement)
        self.assertIn("info@amsterdamcourtfinder.nl", statement)
        self.assertIn("plaatst geen reserveringen", statement)

    def test_cloudflare_analytics_disclosure_is_available_in_each_language(self):
        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                statement = privacy_statement(language, analytics_enabled=True)
                self.assertIn("developers.cloudflare.com/web-analytics/about/", statement)
                self.assertNotEqual(statement, privacy_statement(language))

    def test_sponsor_link_disclosure_is_available_in_each_language(self):
        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                statement = privacy_statement(language, sponsor_enabled=True)
                self.assertIn("### Sponsored links", statement)
                self.assertNotEqual(statement, privacy_statement(language))

    def test_added_languages_translate_and_round_trip_interface_statuses(self):
        expected_languages = {
            "中文 (简体)",
            "हिन्दी",
            "Español",
            "Français",
            "العربية",
            "বাংলা",
            "Português",
            "Русский",
        }
        self.assertTrue(expected_languages.issubset(SUPPORTED_LANGUAGES))

        for language in expected_languages:
            with self.subTest(language=language):
                availability = translate_text("Availability", language)
                self.assertNotEqual(availability, "Availability")
                localized_status = translate_text(
                    "Could not verify - Meet & Play HTTP 403",
                    language,
                )
                self.assertNotEqual(localized_status, "Could not verify - Meet & Play HTTP 403")
                self.assertEqual(
                    translate_to_english(localized_status, language),
                    "Could not verify - Meet & Play HTTP 403",
                )
                self.assertNotEqual(
                    translate_sort_option("Courts - ascending", language),
                    "Courts - ascending",
                )
                translated_recommendation = translate_text(
                    "Indoor is preferable for cold (5°C), strong wind (38 km/h).",
                    language,
                )
                self.assertNotIn(
                    "Indoor is preferable for",
                    translated_recommendation,
                )
                self.assertIn("5°C", translated_recommendation)
                self.assertNotEqual(
                    translate_text(
                        "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.",
                        language,
                    ),
                    "Outdoor conditions look manageable; when the choice is unclear, outdoor courts are usually cheaper.",
                )
                self.assertIn(
                    "info@amsterdamcourtfinder.nl",
                    privacy_statement(language),
                )

    def test_filter_value_can_be_normalized_after_switching_languages(self):
        spanish_available = translate_text("Available", "Español")

        self.assertEqual(
            translate_to_english(spanish_available, "Français"),
            "Available",
        )

    def test_localize_frame_translates_additional_language_table_labels(self):
        frame = pd.DataFrame(
            [{"Club": "Test club", "Availability": "✅ Available"}]
        )

        localized = localize_frame(frame, "Español")

        self.assertIn("Disponibilidad", localized.columns)
        self.assertEqual(localized.iloc[0]["Disponibilidad"], "✅ Disponible")


if __name__ == "__main__":
    unittest.main()
