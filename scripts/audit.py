#!/usr/bin/env python3
"""Full campaign audit workflow.

Pulls performance data from Google Ads and Google Search Console,
analyzes against benchmarks from config, and generates both a technical
audit report and a plain-English business report.

Usage:
    python scripts/audit.py [--days 7] [--csv path/to/export.csv] [--business-only]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from ads_manager.api.client import is_api_available, load_account_config
from ads_manager.reports.generator import generate_audit_report, generate_business_report


def load_config():
    return load_account_config()


def pull_data_api(days: int):
    from ads_manager.api.performance import get_campaign_performance, get_keyword_performance
    print(f"Pulling {days} days of data via Google Ads API...")
    campaigns = get_campaign_performance(days=days)
    keywords = get_keyword_performance(days=days)
    print(f"  Found {len(campaigns)} campaigns, {len(keywords)} keywords")
    return campaigns, keywords


def pull_data_csv(csv_path: str):
    from ads_manager.csv.parser import parse_campaign_export, parse_keyword_export
    path = Path(csv_path)
    print(f"Parsing CSV export: {path}")
    campaigns = parse_campaign_export(path)
    keyword_files = list(path.parent.glob("*keyword*"))
    keywords = []
    if keyword_files:
        keywords = parse_keyword_export(keyword_files[0])
    print(f"  Found {len(campaigns)} campaigns, {len(keywords)} keywords")
    return campaigns, keywords


def pull_organic_data(days: int, keywords: list[dict]):
    """Pull organic search data from GSC (API first, CSV fallback).

    Returns (queries, pages, overlaps) — any or all may be None.
    """
    from ads_manager.api.search_console import is_gsc_available, find_paid_organic_overlap

    organic_queries = None
    organic_pages = None
    paid_organic_overlaps = None

    if is_gsc_available():
        from ads_manager.api.search_console import get_query_performance, get_page_performance
        print(f"Pulling {days} days of organic data via Search Console API...")
        try:
            organic_queries = get_query_performance(days=days)
            organic_pages = get_page_performance(days=days)
            print(f"  Found {len(organic_queries)} queries, {len(organic_pages)} pages")
        except Exception as e:
            print(f"  Warning: GSC API call failed: {e}")
    else:
        from ads_manager.csv.search_console_parser import list_gsc_exports, parse_gsc_queries_export, parse_gsc_pages_export
        gsc_exports = list_gsc_exports()
        if gsc_exports:
            print(f"Parsing GSC CSV exports...")
            for export in gsc_exports:
                name = export.name.lower()
                if "quer" in name and organic_queries is None:
                    organic_queries = parse_gsc_queries_export(export)
                    print(f"  Queries: {len(organic_queries)} from {export.name}")
                elif "page" in name and organic_pages is None:
                    organic_pages = parse_gsc_pages_export(export)
                    print(f"  Pages: {len(organic_pages)} from {export.name}")

    if not organic_queries and not organic_pages:
        print("  No GSC data available (API not configured, no CSV exports found)")
        print("  Tip: Set up Search Console for organic search insights in future reports")

    if organic_queries and keywords:
        paid_organic_overlaps = find_paid_organic_overlap(organic_queries, keywords)
        if paid_organic_overlaps:
            print(f"  Found {len(paid_organic_overlaps)} paid/organic keyword overlaps")

    return organic_queries, organic_pages, paid_organic_overlaps


def analyze(campaigns, keywords, benchmarks):
    recommendations = []
    for c in campaigns:
        name = c.get("campaign_name", "Unknown")
        ctr = c.get("ctr")
        if ctr is not None and ctr < benchmarks.get("ctr_min", 0.03):
            recommendations.append(
                f"**{name}**: CTR is {ctr*100:.1f}% (target >{benchmarks['ctr_min']*100:.0f}%). "
                f"Review ad copy relevance and consider adding more specific headlines.")
        cpc = c.get("avg_cpc")
        if cpc is not None and cpc > benchmarks.get("cpc_max", 8.0):
            recommendations.append(
                f"**{name}**: Avg CPC ${cpc:.2f} exceeds ${benchmarks['cpc_max']:.2f} cap. "
                f"Review bid strategy and consider reducing bids on low-QS keywords.")
        cpa = c.get("cost_per_conversion")
        if cpa is not None and cpa > benchmarks.get("cost_per_conversion_max", 50.0):
            recommendations.append(
                f"**{name}**: Cost/conversion ${cpa:.2f} exceeds ${benchmarks['cost_per_conversion_max']:.2f}. "
                f"Identify and pause underperforming keywords.")
        imp_share = c.get("impression_share")
        if imp_share is not None and imp_share < benchmarks.get("impression_share_min", 0.6):
            budget_lost = c.get("budget_lost_is", 0) or 0
            if budget_lost > 0.1:
                recommendations.append(
                    f"**{name}**: Losing {budget_lost*100:.0f}% impression share to budget. "
                    f"Consider increasing daily budget.")
    for kw in keywords:
        qs = kw.get("quality_score")
        if qs is not None and qs < benchmarks.get("quality_score_min", 6):
            cost = kw.get("cost", 0) or 0
            if cost > 20:
                recommendations.append(
                    f"Keyword '{kw['keyword']}' has QS {qs} with ${cost:.2f} spend. "
                    f"Improve ad relevance or consider pausing.")
    if not recommendations:
        recommendations.append("All campaigns are performing within benchmark ranges.")
    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Run a full campaign audit")
    parser.add_argument("--days", type=int, default=7, help="Lookback period in days")
    parser.add_argument("--csv", type=str, help="Path to a campaign export CSV")
    parser.add_argument(
        "--business-only", action="store_true",
        help="Generate only the plain-English business report (skip technical audit)"
    )
    args = parser.parse_args()

    config = load_config()
    benchmarks = config["benchmarks"]
    account_name = config["account"].get("name", "Unknown")
    print(f"Auditing account: {account_name} ({config['account']['id']})")

    if args.csv:
        campaigns, keywords = pull_data_csv(args.csv)
    elif is_api_available():
        campaigns, keywords = pull_data_api(args.days)
    else:
        print("ERROR: No API credentials and no CSV path provided.")
        print("  Either set up config/credentials.yaml or pass --csv path/to/export.csv")
        sys.exit(1)

    # Pull organic data (optional — never blocks the audit)
    organic_queries, organic_pages, paid_organic_overlaps = pull_organic_data(args.days, keywords)

    recommendations = analyze(campaigns, keywords, benchmarks)

    if args.business_only:
        report_path = generate_business_report(
            campaigns=campaigns, keywords=keywords,
            benchmarks=benchmarks, recommendations=recommendations, days=args.days,
            organic_queries=organic_queries, organic_pages=organic_pages,
            paid_organic_overlaps=paid_organic_overlaps)
        print(f"\nAudit complete. Business report: {report_path}")
    else:
        audit_path = generate_audit_report(
            campaigns=campaigns, keywords=keywords,
            benchmarks=benchmarks, recommendations=recommendations, days=args.days)
        business_path = generate_business_report(
            campaigns=campaigns, keywords=keywords,
            benchmarks=benchmarks, recommendations=recommendations, days=args.days,
            organic_queries=organic_queries, organic_pages=organic_pages,
            paid_organic_overlaps=paid_organic_overlaps)
        print(f"\nAudit complete.")
        print(f"  Technical report: {audit_path}")
        print(f"  Business report:  {business_path}")

    print(f"Found {len(recommendations)} recommendation(s).")


if __name__ == "__main__":
    main()
