"""Parse CSV files exported from Google Ads Editor or Google Ads UI.

Reads exported CSVs and returns structured data for analysis.
This is the fallback path when the API is unavailable.
"""

import csv
from pathlib import Path
from typing import Optional

EXPORT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "exports"


def parse_csv(filepath: str | Path) -> list[dict]:
    """Parse any Google Ads CSV export into a list of dicts."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV not found: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_campaign_export(filepath: str | Path) -> list[dict]:
    """Parse a campaign-level export. Normalizes column names and converts numeric fields."""
    rows = parse_csv(filepath)
    campaigns = []
    for row in rows:
        campaigns.append({
            "campaign_name": row.get("Campaign", ""),
            "status": row.get("Campaign status", row.get("Status", "")),
            "daily_budget": _to_float(row.get("Budget", row.get("Daily budget", ""))),
            "impressions": _to_int(row.get("Impressions", "")),
            "clicks": _to_int(row.get("Clicks", "")),
            "ctr": _to_pct(row.get("CTR", row.get("Click-through rate", ""))),
            "avg_cpc": _to_float(row.get("Avg. CPC", row.get("Average CPC", ""))),
            "cost": _to_float(row.get("Cost", "")),
            "conversions": _to_float(row.get("Conversions", "")),
            "cost_per_conversion": _to_float(row.get("Cost / conv.", row.get("Cost per conversion", ""))),
            "impression_share": _to_pct(row.get("Search impr. share", row.get("Impression share", ""))),
        })
    return campaigns


def parse_keyword_export(filepath: str | Path) -> list[dict]:
    """Parse a keyword-level export."""
    rows = parse_csv(filepath)
    keywords = []
    for row in rows:
        keywords.append({
            "campaign_name": row.get("Campaign", ""),
            "ad_group_name": row.get("Ad group", row.get("Ad Group", "")),
            "keyword": row.get("Keyword", ""),
            "match_type": row.get("Match type", row.get("Match Type", "")),
            "status": row.get("Status", row.get("Keyword status", "")),
            "quality_score": _to_int(row.get("Quality score", row.get("Quality Score", ""))),
            "max_cpc": _to_float(row.get("Max. CPC", row.get("Max CPC", ""))),
            "impressions": _to_int(row.get("Impressions", "")),
            "clicks": _to_int(row.get("Clicks", "")),
            "ctr": _to_pct(row.get("CTR", "")),
            "avg_cpc": _to_float(row.get("Avg. CPC", "")),
            "cost": _to_float(row.get("Cost", "")),
            "conversions": _to_float(row.get("Conversions", "")),
        })
    return keywords


def parse_ad_export(filepath: str | Path) -> list[dict]:
    """Parse an ad-level export."""
    rows = parse_csv(filepath)
    ads = []
    for row in rows:
        headlines = [row.get(f"Headline {i}", "") for i in range(1, 16) if row.get(f"Headline {i}", "")]
        descriptions = [row.get(f"Description {i}", row.get(f"Description line {i}", ""))
                        for i in range(1, 5) if row.get(f"Description {i}", row.get(f"Description line {i}", ""))]
        ads.append({
            "campaign_name": row.get("Campaign", ""),
            "ad_group_name": row.get("Ad group", row.get("Ad Group", "")),
            "headlines": headlines, "descriptions": descriptions,
            "final_url": row.get("Final URL", ""),
            "status": row.get("Status", row.get("Ad status", "")),
            "impressions": _to_int(row.get("Impressions", "")),
            "clicks": _to_int(row.get("Clicks", "")),
            "ctr": _to_pct(row.get("CTR", "")),
            "cost": _to_float(row.get("Cost", "")),
        })
    return ads


def list_exports() -> list[Path]:
    """List all CSV files in the exports directory."""
    if not EXPORT_DIR.exists():
        return []
    return sorted(EXPORT_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)


def _to_float(val: str) -> Optional[float]:
    if not val: return None
    val = str(val).replace("$", "").replace(",", "").replace("%", "").strip()
    try: return float(val)
    except ValueError: return None

def _to_int(val: str) -> Optional[int]:
    f = _to_float(val)
    return int(f) if f is not None else None

def _to_pct(val: str) -> Optional[float]:
    if not val: return None
    val = str(val).strip()
    if val.endswith("%"):
        f = _to_float(val.replace("%", ""))
        return f / 100 if f is not None else None
    f = _to_float(val)
    if f is not None and f > 1: return f / 100
    return f
