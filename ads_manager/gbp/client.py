"""Google Business Profile API client.

Handles authentication and provides methods for managing GBP posts.
Credentials are read from config/credentials.yaml — the same file
used for Google Ads, with an additional gbp section.
"""

import json
from pathlib import Path

import requests
import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.yaml"

GBP_API_BASE = "https://mybusiness.googleapis.com/v4"


class GBPClientError(Exception):
    pass


def _load_gbp_config() -> dict:
    """Load GBP credentials from config/credentials.yaml."""
    if not CREDENTIALS_PATH.exists():
        raise GBPClientError(f"Credentials not found at {CREDENTIALS_PATH}")
    with open(CREDENTIALS_PATH) as f:
        config = yaml.safe_load(f)
    gbp = config.get("gbp") or config.get("google_business_profile")
    if not gbp:
        raise GBPClientError(
            "No 'gbp' section in credentials.yaml. Add your GBP account_id, "
            "location_id, and refresh_token."
        )
    return gbp


def _get_access_token() -> str:
    """Get a fresh access token using the refresh token."""
    with open(CREDENTIALS_PATH) as f:
        config = yaml.safe_load(f)

    # Use the same OAuth client as Google Ads
    ads_creds = config.get("google_ads", {})
    gbp_config = config.get("gbp", config.get("google_business_profile", {}))

    client_id = ads_creds.get("client_id")
    client_secret = ads_creds.get("client_secret")
    refresh_token = gbp_config.get("refresh_token")

    if not all([client_id, client_secret, refresh_token]):
        raise GBPClientError(
            "Missing OAuth credentials. Need client_id, client_secret "
            "from google_ads section and refresh_token from gbp section."
        )

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    if response.status_code != 200:
        raise GBPClientError(f"Token refresh failed: {response.text}")

    return response.json()["access_token"]


def _headers() -> dict:
    """Get authenticated headers for API requests."""
    token = _get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def get_account_and_location() -> tuple[str, str]:
    """Return (account_id, location_id) from config."""
    gbp = _load_gbp_config()
    account_id = gbp.get("account_id")
    location_id = gbp.get("location_id")
    if not account_id or not location_id:
        raise GBPClientError(
            "GBP config needs 'account_id' and 'location_id'. "
            "Find these at business.google.com or via the API."
        )
    return account_id, location_id


def _location_path() -> str:
    """Build the API path for the location."""
    account_id, location_id = get_account_and_location()
    return f"{GBP_API_BASE}/accounts/{account_id}/locations/{location_id}"


def create_event_post(
    title: str,
    summary: str,
    start_date: dict,
    start_time: dict,
    end_date: dict,
    end_time: dict,
    cta_url: str,
    cta_action: str = "BOOK",
    photo_url: str = None,
) -> dict:
    """Create an event post on Google Business Profile.

    Args:
        title: Event title (e.g., "Dale Jones — Live Comedy")
        summary: Description text (max 1500 chars)
        start_date: {"year": 2026, "month": 4, "day": 17}
        start_time: {"hours": 19, "minutes": 0}
        end_date: {"year": 2026, "month": 4, "day": 17}
        end_time: {"hours": 22, "minutes": 0}
        cta_url: URL for the CTA button
        cta_action: One of BOOK, ORDER, SHOP, LEARN_MORE, SIGN_UP, CALL
        photo_url: Optional URL to a photo for the post

    Returns:
        API response dict
    """
    body = {
        "languageCode": "en-US",
        "topicType": "EVENT",
        "summary": summary,
        "event": {
            "title": title,
            "schedule": {
                "startDate": start_date,
                "startTime": start_time,
                "endDate": end_date,
                "endTime": end_time,
            },
        },
        "callToAction": {
            "actionType": cta_action,
            "url": cta_url,
        },
    }

    if photo_url:
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": photo_url}]

    url = f"{_location_path()}/localPosts"
    response = requests.post(url, headers=_headers(), json=body)

    if response.status_code not in (200, 201):
        raise GBPClientError(
            f"Failed to create post: {response.status_code} {response.text}"
        )

    result = response.json()
    print(f"Created GBP event post: {title}")
    return result


def create_update_post(
    summary: str,
    cta_url: str = None,
    cta_action: str = "LEARN_MORE",
    photo_url: str = None,
) -> dict:
    """Create a standard update post (non-event).

    Args:
        summary: Post text (max 1500 chars)
        cta_url: Optional URL for CTA button
        cta_action: CTA type if cta_url provided
        photo_url: Optional photo URL

    Returns:
        API response dict
    """
    body = {
        "languageCode": "en-US",
        "topicType": "STANDARD",
        "summary": summary,
    }

    if cta_url:
        body["callToAction"] = {"actionType": cta_action, "url": cta_url}

    if photo_url:
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": photo_url}]

    url = f"{_location_path()}/localPosts"
    response = requests.post(url, headers=_headers(), json=body)

    if response.status_code not in (200, 201):
        raise GBPClientError(
            f"Failed to create post: {response.status_code} {response.text}"
        )

    result = response.json()
    print(f"Created GBP update post")
    return result


def list_posts(page_size: int = 10) -> list[dict]:
    """List recent local posts."""
    url = f"{_location_path()}/localPosts?pageSize={page_size}"
    response = requests.get(url, headers=_headers())

    if response.status_code != 200:
        raise GBPClientError(f"Failed to list posts: {response.status_code} {response.text}")

    data = response.json()
    return data.get("localPosts", [])


def delete_post(post_name: str) -> None:
    """Delete a local post by its resource name."""
    url = f"{GBP_API_BASE}/{post_name}"
    response = requests.delete(url, headers=_headers())

    if response.status_code not in (200, 204):
        raise GBPClientError(f"Failed to delete post: {response.status_code} {response.text}")

    print(f"Deleted post: {post_name}")


def is_gbp_available() -> bool:
    """Check if GBP credentials are configured."""
    try:
        _load_gbp_config()
        return True
    except GBPClientError:
        return False
