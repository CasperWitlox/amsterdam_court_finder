import unittest

import pandas as pd

from tennis_ui import (
    filter_club_rows,
    localize_frame,
    privacy_statement,
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


if __name__ == "__main__":
    unittest.main()
