import unittest
from unittest.mock import Mock, mock_open, patch

import readme_freshness
import update_readme


CURRENT_DAY = "Thursday"
CURRENT_DATE = "September 03, 2026"
CURRENT_CONTENT = f"""# Profile

<!-- DAILY_CONTENT_START -->
### 📅 Today is **{CURRENT_DAY}, {CURRENT_DATE}**
Current content
<!-- DAILY_CONTENT_END -->
"""


class DailyContentFreshnessTests(unittest.TestCase):
    def test_current_date_inside_generated_block_is_fresh(self):
        self.assertTrue(
            readme_freshness.has_current_daily_content(
                CURRENT_CONTENT, CURRENT_DAY, CURRENT_DATE
            )
        )

    def test_previous_date_is_stale(self):
        self.assertFalse(
            readme_freshness.has_current_daily_content(
                CURRENT_CONTENT, "Friday", "September 04, 2026"
            )
        )

    def test_current_date_outside_generated_block_is_stale(self):
        content = f"""### 📅 Today is **{CURRENT_DAY}, {CURRENT_DATE}**
<!-- DAILY_CONTENT_START -->
Old content
<!-- DAILY_CONTENT_END -->
"""

        self.assertFalse(
            readme_freshness.has_current_daily_content(
                content, CURRENT_DAY, CURRENT_DATE
            )
        )

    def test_fresh_readme_skips_network_and_write(self):
        readme = mock_open(read_data=CURRENT_CONTENT)

        with (
            patch("builtins.open", readme),
            patch.object(
                update_readme,
                "get_current_datetime",
                return_value=(CURRENT_DAY, CURRENT_DATE),
            ),
            patch.object(update_readme.requests, "get") as request_get,
        ):
            update_readme.update_readme()

        request_get.assert_not_called()
        readme().write.assert_not_called()

    def test_stale_readme_fetches_and_updates(self):
        stale_content = """# Profile

<!-- DAILY_CONTENT_START -->
Old content
<!-- DAILY_CONTENT_END -->
"""
        readme = mock_open(read_data=stale_content)
        quote = Mock(return_value=("A quote", "An author"))

        with (
            patch("builtins.open", readme),
            patch.object(
                update_readme,
                "get_current_datetime",
                return_value=(CURRENT_DAY, CURRENT_DATE),
            ),
            patch.object(update_readme, "get_random_quote", quote),
            patch.object(update_readme, "get_weather", return_value="Weather"),
            patch.object(update_readme, "get_joke", return_value=("Setup", "Punchline")),
            patch.object(update_readme, "get_tech_news", return_value="News"),
            patch.object(update_readme, "get_nasa_apod", return_value=""),
            patch.object(update_readme, "get_on_this_day", return_value="History"),
            patch.object(update_readme, "get_useless_fact", return_value="Fact"),
        ):
            update_readme.update_readme()

        quote.assert_called_once_with()
        written_content = readme().write.call_args.args[0]
        self.assertIn(
            f"### 📅 Today is **{CURRENT_DAY}, {CURRENT_DATE}**",
            written_content,
        )


if __name__ == "__main__":
    unittest.main()
