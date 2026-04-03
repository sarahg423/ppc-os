"""Generate Google Ads Editor-compatible CSV files.

All CSVs are written with:
- Account as the first column (value read from config)
- UTF-8 encoding, no BOM
- Python csv.writer for proper quoting

Always validates data before writing. Raises ValidationError if invalid.
"""

import csv
from pathlib import Path
from typing import Optional

from ads_manager.api.client import get_account_id
from .validator import (
    ValidationError,
    validate_campaigns,
    validate_keywords,
    validate_negative_keywords,
    validate_rsa,
    validate_budgets,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "imports"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _account_id() -> str:
    """Get the account ID from config for CSV output."""
    return get_account_id(hyphenated=True)


def write_keyword_csv(
    rows: list[dict], filename: str = "keywords.csv",
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a keyword CSV for Ads Editor import."""
    errors = validate_keywords(rows)
    if errors:
        raise ValidationError(errors)

    out = output_dir or OUTPUT_DIR
    _ensure_dir(out)
    filepath = out / filename
    account = _account_id()

    headers = ["Account", "Campaign", "Ad Group", "Keyword", "Match Type", "Max CPC", "Status"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([
                account, row["Campaign"], row.get("Ad Group", ""),
                row["Keyword"], row.get("Match Type", "Phrase"),
                row.get("Max CPC", ""), row.get("Status", "Active"),
            ])
    print(f"Wrote {len(rows)} keyword(s) to {filepath}")
    return filepath


def write_negative_keyword_csv(
    rows: list[dict], filename: str = "negative_keywords.csv",
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a negative keyword CSV for Ads Editor import."""
    errors = validate_negative_keywords(rows)
    if errors:
        raise ValidationError(errors)

    out = output_dir or OUTPUT_DIR
    _ensure_dir(out)
    filepath = out / filename
    account = _account_id()
    has_ad_group = any(row.get("Ad Group") for row in rows)

    if has_ad_group:
        headers = ["Account", "Campaign", "Ad Group", "Keyword", "Criterion Type"]
    else:
        headers = ["Account", "Campaign", "Keyword", "Criterion Type"]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            if has_ad_group:
                writer.writerow([account, row["Campaign"], row.get("Ad Group", ""),
                                 row["Keyword"], row.get("Criterion Type", "Negative phrase")])
            else:
                writer.writerow([account, row["Campaign"], row["Keyword"],
                                 row.get("Criterion Type", "Negative phrase")])
    print(f"Wrote {len(rows)} negative keyword(s) to {filepath}")
    return filepath


def write_rsa_csv(
    rows: list[dict], filename: str = "rsa_ads.csv",
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a responsive search ad CSV for Ads Editor import."""
    errors = validate_rsa(rows)
    if errors:
        raise ValidationError(errors)

    out = output_dir or OUTPUT_DIR
    _ensure_dir(out)
    filepath = out / filename
    account = _account_id()

    headers = ["Account", "Campaign", "Ad Group", "Ad type"]
    headers += [f"Headline {i}" for i in range(1, 16)]
    headers += [f"Description {i}" for i in range(1, 5)]
    headers += ["Final URL", "Path 1", "Path 2"]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            values = [account, row["Campaign"], row["Ad Group"], "Responsive search ad"]
            values += [row.get(f"Headline {i}", "") for i in range(1, 16)]
            values += [row.get(f"Description {i}", "") for i in range(1, 5)]
            values += [row.get("Final URL", ""), row.get("Path 1", ""), row.get("Path 2", "")]
            writer.writerow(values)
    print(f"Wrote {len(rows)} RSA ad(s) to {filepath}")
    return filepath


def write_campaign_csv(
    rows: list[dict], filename: str = "campaigns.csv",
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a campaign + ad group CSV for Ads Editor import.

    Each row creates either a campaign-level or ad-group-level entry.
    Campaigns get a bid strategy; ad groups get a default Max CPC.

    Expected row keys:
        Campaign, Ad Group (optional), Bid Strategy Type,
        Max CPC, Campaign Status, Ad Group Status, Network
    """
    errors = validate_campaigns(rows)
    if errors:
        raise ValidationError(errors)

    out = output_dir or OUTPUT_DIR
    _ensure_dir(out)
    filepath = out / filename
    account = _account_id()

    headers = [
        "Account", "Campaign", "Campaign Status", "Bid Strategy Type",
        "Ad Group", "Ad Group Status", "Max CPC", "Network",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([
                account,
                row["Campaign"],
                row.get("Campaign Status", "Active"),
                row.get("Bid Strategy Type", ""),
                row.get("Ad Group", ""),
                row.get("Ad Group Status", "Active"),
                row.get("Max CPC", ""),
                row.get("Network", "Google search"),
            ])
    print(f"Wrote {len(rows)} campaign/ad group row(s) to {filepath}")
    return filepath


def write_budget_csv(
    rows: list[dict], filename: str = "budgets.csv",
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a campaign budget CSV for Ads Editor import."""
    errors = validate_budgets(rows)
    if errors:
        raise ValidationError(errors)

    out = output_dir or OUTPUT_DIR
    _ensure_dir(out)
    filepath = out / filename
    account = _account_id()

    headers = ["Account", "Campaign", "Budget", "Budget type"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([account, row["Campaign"], row["Budget"],
                             row.get("Budget type", "Daily")])
    print(f"Wrote {len(rows)} budget change(s) to {filepath}")
    return filepath
