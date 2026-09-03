"""
Update README.md with current day, date, weather, joke, tech news, NASA APOD, history, and facts.
Runs via GitHub Actions daily.
"""

import datetime
import re
import random
import requests

from readme_freshness import (
    DAILY_CONTENT_PATTERN,
    get_current_utc_day_and_date,
    has_current_daily_content,
)


def get_random_quote():
    """Fetch a random quote from ZenQuotes API."""
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            quote = data[0].get("q", "Stay curious!")
            author = data[0].get("a", "Unknown")
            return quote, author
    except Exception as e:
        print(f"Error fetching quote: {e}")
    
    fallback_quotes = [
        ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
        ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ]
    return random.choice(fallback_quotes)

def get_weather():
    """Fetch current weather for Eindhoven (latitude=51.44, longitude=5.47)."""
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=51.44&longitude=5.47&current=temperature_2m,weather_code&timezone=Europe%2FAmsterdam"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        code = current.get("weather_code", 0)
        
        # WMO Weather interpretation codes
        weather_icons = {
            0: "☀️ Clear sky",
            1: "🌤️ Mainly clear",
            2: "⛅ Partly cloudy",
            3: "☁️ Overcast",
            45: "🌫️ Fog", 48: "🌫️ Depositing rime fog",
            51: "🌧️ Drizzle", 53: "🌧️ Drizzle", 55: "🌧️ Drizzle",
            61: "🌧️ Rain", 63: "🌧️ Rain", 65: "🌧️ Rain",
            71: "🌨️ Snow", 73: "🌨️ Snow", 75: "🌨️ Snow",
            80: "🌧️ Rain showers", 81: "🌧️ Rain showers", 82: "🌧️ Rain showers",
            95: "⛈️ Thunderstorm", 96: "⛈️ Thunderstorm", 99: "⛈️ Thunderstorm"
        }
        condition = weather_icons.get(code, "Unknown")
        return f"{temp}°C - {condition}"
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return "Weather unavailable"

def get_joke():
    """Fetch a random programming joke."""
    try:
        response = requests.get("https://official-joke-api.appspot.com/jokes/programming/random", timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            data = data[0]
        return data.get("setup", ""), data.get("punchline", "")
    except Exception as e:
        print(f"Error fetching joke: {e}")
        return "Why do programmers prefer dark mode?", "Because light attracts bugs."

def get_tech_news():
    """Fetch top 8 tech stories from Hacker News."""
    try:
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        ids = response.json()[:8]
        
        stories = []
        for id in ids:
            item_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json", timeout=5)
            item = item_resp.json()
            title = item.get("title", "No title")
            url = item.get("url", f"https://news.ycombinator.com/item?id={id}")
            stories.append(f"- [{title}]({url})")
        return "\n".join(stories)
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "- Failed to fetch news"

def get_nasa_apod():
    """Fetch NASA Astronomy Picture of the Day (with random fallback)."""
    def format_apod(data):
        title = data.get("title", "Space Image")
        url = data.get("url")
        media_type = data.get("media_type", "")
        copyright_text = data.get("copyright", "NASA / APOD").strip().replace("\n", " ")
        
        if not url: 
            return None
        
        # Format: Title as Header, Source line, then Media
        header = f"### 🌌 {title}"
        source = f"> Source: {copyright_text}"
        
        if media_type == "image":
            return f"{header}\n\n{source}\n<img src='{url}' width='100%' style='border-radius: 8px;'>"
        elif media_type == "video":
            return f"{header}\n\n{source}\n[Watch Video]({url})"
        return None

    # 1. Try Today's Picture
    try:
        response = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", timeout=10)
        response.raise_for_status()
        data = response.json()
        content = format_apod(data)
        if content and "img" in content: # Prefer images for the dashboard
            return content
    except Exception as e:
        print(f"Error fetching today's APOD: {e}")

    # 2. Fallback to Random Image if today is not an image or failed
    try:
        print("Falling back to random APOD...")
        response = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&count=1", timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            data = data[0]
        content = format_apod(data)
        if content:
            return content
    except Exception as e:
        print(f"Error fetching random APOD: {e}")

    return ""

def get_on_this_day():
    """Fetch historical events for today."""
    try:
        now = datetime.datetime.now()
        month = now.month
        day = now.day
        url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; GitHubReadmeBot/1.0; +https://github.com/)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        events = data.get("events", [])
        # Get 3 random events from the top 15 most recent/relevant
        selected_events = random.sample(events[:15], min(3, len(events)))
        sorted_events = sorted(selected_events, key=lambda x: x.get("year", 0), reverse=True)
        
        formatted_events = []
        for event in sorted_events:
            year = event.get("year")
            text = event.get("text")
            formatted_events.append(f"- **{year}**: {text}")
            
        return "\n".join(formatted_events)
    except Exception as e:
        print(f"Error fetching history: {e}")
        return "- History data unavailable"

def get_useless_fact():
    """Fetch a random cat fact (since useless facts API is flaky)."""
    try:
        response = requests.get("https://catfact.ninja/fact", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("fact", "Cats are amazing.")
    except Exception as e:
        print(f"Error fetching fact: {e}")
        return "Did you know? Python is named after Monty Python."

def get_current_datetime():
    """Get current day name and formatted date."""
    return get_current_utc_day_and_date()

def get_daily_message(day_name):
    """Return a specific message based on the day of the week."""
    messages = {
        "Monday": "Monday again. Coffee is mandatory. ☕",
        "Tuesday": "It's barely Tuesday? Okay. 😑",
        "Wednesday": "Wednesday. Halfway there, I guess. 🐫",
        "Thursday": "Thursday is just Friday Jr. 🤷‍♂️",
        "Friday": "Friday. We made it. 🎉",
        "Saturday": "Saturday. Do not disturb. 😴",
        "Sunday": "Sunday. Trying not to think about Monday. 🌅"
    }
    return messages.get(day_name, "Have a good one.")

def update_readme():
    """Update README.md with dynamic dashboard content."""
    day_name, date_str = get_current_datetime()

    # Read and check the current README before calling any external APIs. This
    # makes later workflow attempts a no-op after the first successful update.
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("README.md not found.")
        return

    if has_current_daily_content(readme_content, day_name, date_str):
        print("README already contains today's daily content; skipping update.")
        return

    quote, author = get_random_quote()
    weather_info = get_weather()
    joke_setup, joke_punchline = get_joke()
    news_content = get_tech_news()
    daily_message = get_daily_message(day_name)
    nasa_content = get_nasa_apod()
    history_content = get_on_this_day()
    useless_fact = get_useless_fact()

    # Format NASA content as a separate section if it exists
    nasa_section = ""
    if nasa_content:
        nasa_section = f"<br>\n\n{nasa_content}"

    # Create the dynamic dashboard - SPLIT LAYOUT
    dynamic_content = f"""<!-- DAILY_CONTENT_START -->
### 📅 Today is **{day_name}, {date_str}**
*{daily_message}*

<table>
<tr>
<td width="50%" valign="top">
<!-- LEFT COLUMN -->
<br>

**🌤️ Eindhoven Weather**<br>
{weather_info}

<br>

**💥 On This Day**<br>
{history_content}

<br>

**💬 Quote**<br>
> "{quote}"<br>
> — **{author}**

<br>
</td>
<td width="50%" valign="top">
<!-- RIGHT COLUMN -->
<br>

**🤣 Daily Joke**<br>
*{joke_setup}*<br>
**{joke_punchline}**

<br>

**🧠 Random Fact**<br>
*{useless_fact}*

<br>

**📰 Daily Tech News**
{news_content}

<br>
</td>
</tr>
</table>
{nasa_section}

<!-- DAILY_CONTENT_END -->"""

    # Replace content between markers
    if re.search(DAILY_CONTENT_PATTERN, readme_content, re.DOTALL):
        new_content = re.sub(
            DAILY_CONTENT_PATTERN,
            lambda m: dynamic_content,
            readme_content,
            flags=re.DOTALL,
        )
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ README updated successfully with new layout!")
    else:
        print("❌ Could not find content markers in README.md")

if __name__ == "__main__":
    update_readme()
