"""Validate Google Ads Editor CSV data before writing.

Catches common errors that would cause Ads Editor to reject the import.
All account-specific values (account ID, char limits) are read from config.
"""

from typing import Optional
from ads_manager.api.client import load_account_config


VALID_MATCH_TYPES = {"Broad", "Phrase", "Exact"}
VALID_STATUSES = {"Active", "Paused", "Removed"}
VALID_CRITERION_TYPES = {"Negative broad", "Negative phrase", "Negative exact"}
VALID_BUDGET_TYPES = {"Daily"}
VALID_BID_STRATEGIES = {"Maximize clicks", "Maximize conversions", "Target CPA", "Target ROAS", "Manual CPC"}
VALID_NETWORKS = {"Google search", "Search partners", "Google search;Search partners"}


def _get_ad_limits() -> dict:
    """Load ad copy character limits from config."""
    try:
        config = load_account_config()
        return config.get("ad_copy", {})
    except FileNotFoundError:
        return {"headline_max_chars": 30, "description_max_chars": 90, "path_max_chars": 15}


class ValidationError(Exception):
    """Raised when CSV data fails validation."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"CSV validation failed with {len(errors)} error(s):\n" +
                         "\n".join(f"  - {e}" for e in errors))


def validate_campaigns(rows: list[dict]) -> list[str]:
    """Validate campaign/ad group CSV rows."""
    errors = []
    for i, row in enumerate(rows, 1):
        if not row.get("Campaign"):
            errors.append(f"Row {i}: Missing Campaign")
        bid_strategy = row.get("Bid Strategy Type", "")
        if bid_strategy and bid_strategy not in VALID_BID_STRATEGIES:
            errors.append(f"Row {i}: Invalid Bid Strategy Type '{bid_strategy}'. Must be one of: {VALID_BID_STRATEGIES}")
        cpc = row.get("Max CPC", "")
        if cpc:
            if str(cpc).startswith("$"):
                errors.append(f"Row {i}: Max CPC should not have '$' — use plain number")
            try:
                float(str(cpc).replace("$", ""))
            except ValueError:
                errors.append(f"Row {i}: Max CPC '{cpc}' is not a valid number")
        status = row.get("Campaign Status", "")
        if status and status not in VALID_STATUSES:
            errors.append(f"Row {i}: Invalid Campaign Status '{status}'. Must be one of: {VALID_STATUSES}")
        ag_status = row.get("Ad Group Status", "")
        if ag_status and ag_status not in VALID_STATUSES:
            errors.append(f"Row {i}: Invalid Ad Group Status '{ag_status}'. Must be one of: {VALID_STATUSES}")
        network = row.get("Network", "")
        if network and network not in VALID_NETWORKS:
            errors.append(f"Row {i}: Invalid Network '{network}'. Must be one of: {VALID_NETWORKS}")
    return errors


def validate_keywords(rows: list[dict]) -> list[str]:
    """Validate keyword CSV rows."""
    errors = []
    for i, row in enumerate(rows, 1):
        if not row.get("Campaign"):
            errors.append(f"Row {i}: Missing Campaign")
        if not row.get("Keyword"):
            errors.append(f"Row {i}: Missing Keyword")
        mt = row.get("Match Type", "")
        if mt and mt not in VALID_MATCH_TYPES:
            errors.append(f"Row {i}: Invalid Match Type '{mt}'. Must be one of: {VALID_MATCH_TYPES}")
        status = row.get("Status", "")
        if status and status not in VALID_STATUSES:
            errors.append(f"Row {i}: Invalid Status '{status}'. Must be one of: {VALID_STATUSES}")
        cpc = row.get("Max CPC", "")
        if cpc:
            if str(cpc).startswith("$"):
                errors.append(f"Row {i}: Max CPC should not have '$' — use plain number")
            try:
                float(str(cpc).replace("$", ""))
            except ValueError:
                errors.append(f"Row {i}: Max CPC '{cpc}' is not a valid number")
    return errors


def validate_negative_keywords(rows: list[dict]) -> list[str]:
    """Validate negative keyword CSV rows."""
    errors = []
    for i, row in enumerate(rows, 1):
        if not row.get("Campaign"):
            errors.append(f"Row {i}: Missing Campaign")
        if not row.get("Keyword"):
            errors.append(f"Row {i}: Missing Keyword")
        ct = row.get("Criterion Type", "")
        if ct and ct not in VALID_CRITERION_TYPES:
            errors.append(f"Row {i}: Invalid Criterion Type '{ct}'. Must be one of: {VALID_CRITERION_TYPES}")
    return errors


def validate_rsa(rows: list[dict]) -> list[str]:
    """Validate responsive search ad CSV rows."""
    limits = _get_ad_limits()
    hl_max = limits.get("headline_max_chars", 30)
    desc_max = limits.get("description_max_chars", 90)
    path_max = limits.get("path_max_chars", 15)

    errors = []
    for i, row in enumerate(rows, 1):
        if not row.get("Campaign"):
            errors.append(f"Row {i}: Missing Campaign")
        if not row.get("Ad Group"):
            errors.append(f"Row {i}: Missing Ad Group")

        headline_count = 0
        for h in range(1, 16):
            val = row.get(f"Headline {h}", "")
            if val:
                headline_count += 1
                if len(val) > hl_max:
                    errors.append(f"Row {i}: Headline {h} is {len(val)} chars (max {hl_max}): '{val}'")
        if headline_count < 3:
            errors.append(f"Row {i}: Need at least 3 headlines, found {headline_count}")

        desc_count = 0
        for d in range(1, 5):
            val = row.get(f"Description {d}", "")
            if val:
                desc_count += 1
                if len(val) > desc_max:
                    errors.append(f"Row {i}: Description {d} is {len(val)} chars (max {desc_max}): '{val}'")
        if desc_count < 2:
            errors.append(f"Row {i}: Need at least 2 descriptions, found {desc_count}")

        for p in ["Path 1", "Path 2"]:
            val = row.get(p, "")
            if val and len(val) > path_max:
                errors.append(f"Row {i}: {p} is {len(val)} chars (max {path_max}): '{val}'")

        if not row.get("Final URL"):
            errors.append(f"Row {i}: Missing Final URL")
    return errors


def validate_budgets(rows: list[dict]) -> list[str]:
    """Validate campaign budget CSV rows."""
    errors = []
    for i, row in enumerate(rows, 1):
        if not row.get("Campaign"):
            errors.append(f"Row {i}: Missing Campaign")
        budget = row.get("Budget", "")
        if budget:
            if str(budget).startswith("$"):
                errors.append(f"Row {i}: Budget should not have '$' — use plain number")
            try:
                float(str(budget).replace("$", ""))
            except ValueError:
                errors.append(f"Row {i}: Budget '{budget}' is not a valid number")
        bt = row.get("Budget type", "")
        if bt and bt not in VALID_BUDGET_TYPES:
            errors.append(f"Row {i}: Invalid Budget type '{bt}'. Must be 'Daily'")
    return errors
