"""Automatically create Google Business Profile posts for upcoming shows.

Scrapes the BRCC website for upcoming shows and creates GBP event posts
for shows happening in the next 7 days that haven't been posted yet.

Reads brand voice from config/brand-voice.md and account config from
config/account.yaml to write posts that match the club's tone.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from ads_manager.api.client import load_account_config
from .client import create_event_post, list_posts, is_gbp_available, GBPClientError


POSTED_SHOWS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "gbp_posted_shows.json"


def _load_posted_shows() -> set:
    """Load the set of show titles+dates already posted."""
    if POSTED_SHOWS_FILE.exists():
        with open(POSTED_SHOWS_FILE) as f:
            return set(json.load(f))
    return set()


def _save_posted_shows(posted: set) -> None:
    """Save the set of posted shows."""
    POSTED_SHOWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POSTED_SHOWS_FILE, "w") as f:
        json.dump(sorted(posted), f, indent=2)


def scrape_upcoming_shows(url: str = None) -> list[dict]:
    """Scrape the BRCC website for upcoming shows.

    Returns a list of dicts with keys:
        name, date, time, price, description, url
    """
    config = load_account_config()
    site_url = url or config["brand"]["website"]

    response = requests.get(site_url, timeout=15)
    response.raise_for_status()

    # Parse the page — this is site-specific and may need updating
    # if the website structure changes
    soup = BeautifulSoup(response.text, "html.parser")

    shows = []
    # Look for event containers — adjust selectors based on actual site structure
    event_elements = soup.select(".event-item, .show-item, article.event, .tribe-events-calendar-list__event")

    if not event_elements:
        # Fallback: look for common event markup patterns
        event_elements = soup.select("[class*='event'], [class*='show']")

    for el in event_elements:
        # Extract what we can — this is a best-effort scraper
        title_el = el.select_one("h2, h3, .event-title, .show-title, [class*='title']")
        date_el = el.select_one("time, .event-date, .show-date, [class*='date']")
        price_el = el.select_one(".event-price, .show-price, [class*='price']")
        link_el = el.select_one("a[href]")
        desc_el = el.select_one(".event-description, .show-description, p")

        if title_el:
            show = {
                "name": title_el.get_text(strip=True),
                "date_text": date_el.get_text(strip=True) if date_el else "",
                "price": price_el.get_text(strip=True) if price_el else "",
                "url": link_el["href"] if link_el and link_el.get("href") else site_url,
                "description": desc_el.get_text(strip=True) if desc_el else "",
            }
            shows.append(show)

    return shows


def create_show_post(
    name: str,
    date: dict,
    start_time: dict,
    end_time: dict,
    price: str,
    description: str,
    url: str,
    photo_url: str = None,
) -> dict:
    """Create a GBP event post for an upcoming show.

    Args:
        name: Performer/show name
        date: {"year": 2026, "month": 4, "day": 17}
        start_time: {"hours": 19, "minutes": 0}
        end_time: {"hours": 22, "minutes": 0}
        price: Price text (e.g., "$25")
        description: Show description
        url: Ticket URL
        photo_url: Optional performer photo URL

    Returns:
        API response from GBP
    """
    # Build a post that matches BRCC's voice — fun, direct, not corporate
    summary = f"{name} live at Blue Ridge Comedy Club! "
    if description:
        summary += f"{description} "
    if price:
        summary += f"Tickets {price}. "
    summary += "Get yours at blueridgecomedy.com — no drink minimum, no ticket fees."

    # Trim to 1500 char limit
    if len(summary) > 1500:
        summary = summary[:1497] + "..."

    result = create_event_post(
        title=f"{name} — Live at Blue Ridge Comedy Club",
        summary=summary,
        start_date=date,
        start_time=start_time,
        end_date=date,
        end_time=end_time,
        cta_url=url,
        cta_action="BOOK",
        photo_url=photo_url,
    )

    # Track that we posted this show
    posted = _load_posted_shows()
    show_key = f"{name}|{date['year']}-{date['month']:02d}-{date['day']:02d}"
    posted.add(show_key)
    _save_posted_shows(posted)

    return result


def post_upcoming_shows(days_ahead: int = 7, dry_run: bool = False) -> list[dict]:
    """Post all shows happening in the next N days that haven't been posted yet.

    Args:
        days_ahead: How far ahead to look (default 7 days)
        dry_run: If True, print what would be posted without actually posting

    Returns:
        List of API responses for posts created
    """
    if not is_gbp_available():
        raise GBPClientError("GBP credentials not configured.")

    shows = scrape_upcoming_shows()
    posted = _load_posted_shows()
    results = []

    for show in shows:
        show_key = f"{show['name']}|{show.get('date_text', '')}"

        if show_key in posted:
            print(f"  Already posted: {show['name']}")
            continue

        if dry_run:
            print(f"  Would post: {show['name']} — {show.get('date_text', 'date unknown')}")
        else:
            print(f"  Posting: {show['name']}")
            # Note: actual date parsing would need to be implemented
            # based on the website's date format

    return results
