"""Assemble full audit reports from performance data.

Orchestrates the template functions to produce a complete Markdown report.
Account name and ID are read from config. Generates two reports:
  1. Technical audit (existing format) — for marketers or deep dives
  2. Business summary (new) — for non-technical owners
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from ads_manager.api.client import load_account_config, get_account_id, get_account_name
from ads_manager.history import (
    save_snapshot, load_previous_snapshot, compare_totals,
    get_changes_since, _compute_totals,
)
from .templates import (
    report_header, campaign_summary_table, keyword_performance_table,
    benchmark_flags, recommendations_section,
)
from .human_readable import (
    business_summary, trend_summary, change_attribution,
    plain_english_flags, plain_english_recommendations, glossary,
    organic_summary, organic_opportunities, paid_organic_overlap_summary,
    search_terms_summary, negative_keyword_recommendations,
)

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


def generate_audit_report(
    campaigns: list[dict], keywords: list[dict],
    benchmarks: dict, recommendations: list[str],
    days: int = 7, title: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a full Markdown audit report (technical format).

    Account name and ID are read from config/account.yaml.
    Also saves a historical snapshot for future trend comparisons.
    """
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    account_name = get_account_name()
    account_id = get_account_id(hyphenated=True)
    report_title = title or f"{account_name} — Campaign Audit"

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    date_range = f"{start.isoformat()} to {end.isoformat()}"

    sections = [
        report_header(report_title, date_range, account_name, account_id),
        campaign_summary_table(campaigns),
        keyword_performance_table(keywords),
        benchmark_flags(campaigns, benchmarks),
        recommendations_section(recommendations),
    ]

    content = "\n".join(sections)
    filename = f"audit_{date.today().isoformat()}.md"
    filepath = out / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Save snapshot for historical tracking
    save_snapshot(campaigns, keywords, days, recommendations)

    print(f"Report written to {filepath}")
    return filepath


def generate_business_report(
    campaigns: list[dict], keywords: list[dict],
    benchmarks: dict, recommendations: list[str],
    days: int = 7, output_dir: Optional[Path] = None,
    organic_queries: Optional[list[dict]] = None,
    organic_pages: Optional[list[dict]] = None,
    paid_organic_overlaps: Optional[list[dict]] = None,
    search_term_analysis: Optional[dict] = None,
    negative_candidates: Optional[list[dict]] = None,
) -> Path:
    """Generate a plain-English business report for non-technical users.

    Includes week-over-week trends, change attribution, search term analysis,
    organic search data (if available), paid/organic overlap, and a glossary.
    Saves a snapshot and compares against the previous one automatically.
    """
    config = load_account_config()
    out = output_dir or REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    account_name = get_account_name()
    brand = config.get("brand", {}).get("short_name", account_name)

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    date_range = f"{start.isoformat()} to {end.isoformat()}"

    # Current totals
    current_totals = _compute_totals(campaigns)

    # Build report sections
    sections = [
        f"# {brand} Marketing Report\n",
        f"**{date_range}** ({days} days)\n",
        "---\n",
        business_summary(current_totals, config, days),
    ]

    # Week-over-week comparison
    previous = load_previous_snapshot(days=days)
    if previous:
        comparison = compare_totals(current_totals, previous["totals"])
        sections.append(trend_summary(comparison, previous["date"]))

        # Show what changes were made since the last audit
        changes = get_changes_since(previous["date"])
        if changes:
            sections.append(change_attribution(changes))

    # Search term analysis (what people actually typed)
    if search_term_analysis:
        sections.append(search_terms_summary(search_term_analysis))
        if negative_candidates:
            sections.append(negative_keyword_recommendations(negative_candidates))

    # Organic search data (from GSC)
    if organic_queries or organic_pages:
        sections.append(organic_summary(organic_queries or [], organic_pages or [], days))
        if organic_queries:
            sections.append(organic_opportunities(organic_queries))

    # Paid/organic overlap
    if paid_organic_overlaps:
        sections.append(paid_organic_overlap_summary(paid_organic_overlaps))

    # Issues and recommendations in plain English
    sections.append(plain_english_flags(campaigns, benchmarks, config))
    sections.append(plain_english_recommendations(recommendations))
    sections.append(glossary())

    content = "\n".join(sections)
    filename = f"report_{date.today().isoformat()}.md"
    filepath = out / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Save snapshot for next comparison
    save_snapshot(campaigns, keywords, days, recommendations)

    print(f"Business report written to {filepath}")
    return filepath
