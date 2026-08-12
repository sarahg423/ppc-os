"""Google Search Console API client.

Pulls organic search performance data: queries, pages, click-through rates,
and average positions. Uses the same OAuth credentials as the Google Ads
client (same client_id/secret, different API scope). Falls back gracefully
when credentials or the API package aren't available.
"""

import yaml
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from ads_manager import get_project_root

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    HAS_GSC_API = True
except ImportError:
    HAS_GSC_API = False


def _config_path(filename: str) -> Path:
    return get_project_root() / "config" / filename


class GSCClientError(Exception):
    """Raised when the Search Console API client can't be initialized."""
    pass


def _load_gsc_config() -> dict:
    """Load GSC-specific config from credentials.yaml."""
    path = _config_path("credentials.yaml")
    if not path.exists():
        raise GSCClientError(
            f"Credentials file not found at {path}. "
            f"Add a 'search_console' section to config/credentials.yaml."
        )
    with open(path) as f:
        config = yaml.safe_load(f)

    if not config or "search_console" not in config:
        raise GSCClientError(
            "credentials.yaml must contain a 'search_console' section. "
            "See credentials.example.yaml for the required fields."
        )
    return config["search_console"]


def _get_site_url() -> str:
    """Get the GSC site URL from account.yaml."""
    path = _config_path("account.yaml")
    if not path.exists():
        raise GSCClientError("account.yaml not found. Run the getting-started skill first.")
    with open(path) as f:
        config = yaml.safe_load(f)
    site_url = config.get("search_console", {}).get("site_url")
    if not site_url:
        raise GSCClientError(
            "No search_console.site_url in account.yaml. "
            "Add your GSC property URL (e.g., 'https://www.example.com' or 'sc-domain:example.com')."
        )
    return site_url


def get_gsc_client():
    """Create and return an authenticated Search Console API service."""
    if not HAS_GSC_API:
        raise GSCClientError(
            "google-api-python-client and google-auth are not installed. "
            "Install with: pip install google-api-python-client google-auth"
        )
    gsc_config = _load_gsc_config()

    # GSC can share OAuth credentials with Google Ads — same client_id/secret,
    # just needs a refresh token with Search Console scope
    creds = Credentials(
        token=None,
        refresh_token=gsc_config["refresh_token"],
        client_id=gsc_config["client_id"],
        client_secret=gsc_config["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("searchconsole", "v1", credentials=creds)


def is_gsc_available() -> bool:
    """Check whether the Search Console API can be used.

    Returns True if the package is installed, credentials exist, and
    a site_url is configured. Does not make a network call.
    """
    if not HAS_GSC_API:
        return False
    try:
        _load_gsc_config()
        _get_site_url()
        return True
    except GSCClientError:
        return False


def get_query_performance(days: int = 7, row_limit: int = 50) -> list[dict]:
    """Pull top organic search queries with clicks, impressions, CTR, position.

    Returns a list of dicts sorted by clicks descending.
    """
    service = get_gsc_client()
    site_url = _get_site_url()

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)

    response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["query"],
            "rowLimit": row_limit,
        },
    ).execute()

    queries = []
    for row in response.get("rows", []):
        queries.append({
            "query": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0),
            "position": round(row.get("position", 0), 1),
        })

    return sorted(queries, key=lambda q: q["clicks"], reverse=True)


def get_page_performance(days: int = 7, row_limit: int = 25) -> list[dict]:
    """Pull top pages by organic clicks."""
    service = get_gsc_client()
    site_url = _get_site_url()

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)

    response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["page"],
            "rowLimit": row_limit,
        },
    ).execute()

    pages = []
    for row in response.get("rows", []):
        pages.append({
            "page": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0),
            "position": round(row.get("position", 0), 1),
        })

    return sorted(pages, key=lambda p: p["clicks"], reverse=True)


def get_query_page_performance(days: int = 7, row_limit: int = 100) -> list[dict]:
    """Pull query + page combos. Useful for finding which pages rank for which queries."""
    service = get_gsc_client()
    site_url = _get_site_url()

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)

    response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["query", "page"],
            "rowLimit": row_limit,
        },
    ).execute()

    results = []
    for row in response.get("rows", []):
        results.append({
            "query": row["keys"][0],
            "page": row["keys"][1],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0),
            "position": round(row.get("position", 0), 1),
        })

    return sorted(results, key=lambda r: r["clicks"], reverse=True)


def find_paid_organic_overlap(
    organic_queries: list[dict],
    paid_keywords: list[dict],
) -> list[dict]:
    """Find keywords where you're paying for clicks but also ranking organically.

    Returns overlapping keywords with both paid and organic data so the user
    can decide whether to keep paying for them.
    """
    # Normalize organic queries for matching
    organic_map = {}
    for q in organic_queries:
        key = q["query"].lower().strip()
        organic_map[key] = q

    overlaps = []
    for kw in paid_keywords:
        keyword = kw.get("keyword", "").lower().strip()
        # Strip match type brackets/quotes for comparison
        keyword_clean = keyword.strip("[]\"+'")
        if keyword_clean in organic_map:
            org = organic_map[keyword_clean]
            overlaps.append({
                "keyword": kw.get("keyword", ""),
                "organic_clicks": org["clicks"],
                "organic_impressions": org["impressions"],
                "organic_ctr": org["ctr"],
                "organic_position": org["position"],
                "paid_clicks": kw.get("clicks", 0),
                "paid_cost": kw.get("cost", 0),
                "paid_cpc": kw.get("avg_cpc", 0),
            })

    return sorted(overlaps, key=lambda o: o["paid_cost"], reverse=True)
