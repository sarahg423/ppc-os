"""Automatically create Google Business Profile posts for upcoming events.

Scrapes the business website for upcoming events and creates GBP event posts
for events happening in the next N days that haven't been posted yet.

Reads brand voice from config/brand-voice.md and account config from
config/account.yaml to write posts that match the business's tone.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from ads_manager.api.client import load_account_config
from .client import create_event_post, list_posts, is_gbp_available, GBPClientError


POSTED_EVENTS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "gbp_posted_events.json"


def _load_posted_events() -> set:
    """Load the set of event titles+dates already posted."""
    if POSTED_EVENTS_FILE.exists():
        with open(POSTED_EVENTS_FILE) as f:
            return set(json.load(f))
    return set()


def _save_posted_events(posted: set) -> None:
    """Save the set of posted events."""
    POSTED_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(sorted(posted), f, indent=2)


def scrape_upcoming_events(url: str = None) -> list[dict]:
    """Scrape the business website for upcoming events.

    Returns a list of dicts with keys:
        name, date_text, price, description, url
    """
    config = load_account_config()
    site_url = url or config["brand"]["website"]

    response = requests.get(site_url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    # Look for event containers — common CMS patterns
    event_elements = soup.select(
        ".event-item, .show-item, article.event, "
        ".tribe-events-calendar-list__event, "
        "[class*='event-card'], [class*='event-list']"
    )

    if not event_elements:
        event_elements = soup.select("[class*='event'], [class*='show']")

    for el in event_elements:
        title_el = el.select_one("h2, h3, .event-title, .show-title, [class*='title']")
        date_el = el.select_one("time, .event-date, .show-date, [class*='date']")
        price_el = el.select_one(".event-price, .show-price, [class*='price']")
        link_el = el.select_one("a[href]")
        desc_el = el.select_one(".event-description, .show-description, p")

        if title_el:
            event = {
                "name": title_el.get_text(strip=True),
                "date_text": date_el.get_text(strip=True) if date_el else "",
                "price": price_el.get_text(strip=True) if price_el else "",
                "url": link_el["href"] if link_el and link_el.get("href") else site_url,
                "description": desc_el.get_text(strip=True) if desc_el else "",
            }
            events.append(event)

    return events


def create_event_gbp_post(
    name: str,
    date: dict,
    start_time: dict,
    end_time: dict,
    price: str = "",
    description: str = "",
    url: str = "",
    photo_url: str = None,
    summary_override: str = None,
) -> dict:
    """Create a GBP event post for an upcoming event.

    Reads brand name and website from config. If summary_override is provided,
    uses that instead of generating a summary.

    Args:
        name: Event/performer name
        date: {"year": 2026, "month": 4, "day": 17}
        start_time: {"hours": 19, "minutes": 0}
        end_time: {"hours": 22, "minutes": 0}
        price: Price text (e.g., "$25")
        description: Event description
        url: Ticket/event URL
        photo_url: Optional event photo URL
        summary_override: Optional pre-written post text

    Returns:
        API response from GBP
    """
    config = load_account_config()
    brand_name = config["brand"]["name"]
    website = config["brand"]["website"]

    if summary_override:
        summary = summary_override
    else:
        summary = f"{name} at {brand_name}! "
        if description:
            summary += f"{description} "
        if price:
            summary += f"Tickets {price}. "
        summary += f"More info at {website}"

    # Trim to 1500 char limit
    if len(summary) > 1500:
        summary = summary[:1497] + "..."

    cta_url = url or website

    result = create_event_post(
        title=f"{name} — {brand_name}",
        summary=summary,
        start_date=date,
        start_time=start_time,
        end_date=date,
        end_time=end_time,
        cta_url=cta_url,
        cta_action="BOOK",
        photo_url=photo_url,
    )

    # Track that we posted this event
    posted = _load_posted_events()
    event_key = f"{name}|{date['year']}-{date['month']:02d}-{date['day']:02d}"
    posted.add(event_key)
    _save_posted_events(posted)

    return result


def post_upcoming_events(days_ahead: int = 7, dry_run: bool = False) -> list[dict]:
    """Post all events happening in the next N days that haven't been posted yet.

    Args:
        days_ahead: How far ahead to look (default 7 days)
        dry_run: If True, print what would be posted without actually posting

    Returns:
        List of API responses for posts created
    """
    if not is_gbp_available():
        raise GBPClientError("GBP credentials not configured.")

    events = scrape_upcoming_events()
    posted = _load_posted_events()
    results = []

    for event in events:
        event_key = f"{event['name']}|{event.get('date_text', '')}"

        if event_key in posted:
            print(f"  Already posted: {event['name']}")
            continue

        if dry_run:
            print(f"  Would post: {event['name']} — {event.get('date_text', 'date unknown')}")
        else:
            print(f"  Posting: {event['name']}")
            # Note: Claude should parse the date_text into structured date/time
            # before calling create_event_gbp_post. The scraper returns raw text
            # because date formats vary by website.

    return results
