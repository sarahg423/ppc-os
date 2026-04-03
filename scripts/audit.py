#!/usr/bin/env python3
"""Full campaign audit workflow.

Pulls performance data, analyzes against benchmarks from config,
and generates a Markdown report. Works with any Google Ads account.

Usage:
    python scripts/audit.py [--days 7] [--csv path/to/export.csv]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from ads_manager.api.client import is_api_available, load_account_config
from ads_manager.reports.generator import generate_audit_report


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

    recommendations = analyze(campaigns, keywords, benchmarks)
    report_path = generate_audit_report(
        campaigns=campaigns, keywords=keywords,
        benchmarks=benchmarks, recommendations=recommendations, days=args.days)
    print(f"\nAudit complete. Report: {report_path}")
    print(f"Found {len(recommendations)} recommendation(s).")


if __name__ == "__main__":
    main()
