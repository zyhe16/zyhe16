"""Check whether README.md already contains today's generated UTC content."""

import datetime
import re
import sys
from pathlib import Path


DAILY_CONTENT_PATTERN = r"<!-- DAILY_CONTENT_START -->.*?<!-- DAILY_CONTENT_END -->"


def get_current_utc_day_and_date():
    """Return the current UTC weekday and formatted date."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%A"), now.strftime("%B %d, %Y")


def has_current_daily_content(readme_content, day_name, date_str):
    """Return whether the generated block contains the supplied date."""
    match = re.search(DAILY_CONTENT_PATTERN, readme_content, re.DOTALL)
    if not match:
        return False

    expected_heading = f"### 📅 Today is **{day_name}, {date_str}**"
    return expected_heading in match.group(0)


def main():
    """Exit successfully when README.md is already current."""
    try:
        readme_content = Path("README.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        print("README.md is missing and needs an update.")
        return 1

    day_name, date_str = get_current_utc_day_and_date()
    if has_current_daily_content(readme_content, day_name, date_str):
        print("README already contains today's daily content.")
        return 0

    print("README needs today's daily content.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
