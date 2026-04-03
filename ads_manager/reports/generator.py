"""Assemble full audit reports from performance data.

Orchestrates the template functions to produce a complete Markdown report.
Account name and ID are read from config.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from ads_manager.api.client import load_account_config, get_account_id, get_account_name
from .templates import (
    report_header, campaign_summary_table, keyword_performance_table,
    benchmark_flags, recommendations_section,
)

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


def generate_audit_report(
    campaigns: list[dict], keywords: list[dict],
    benchmarks: dict, recommendations: list[str],
    days: int = 7, title: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a full Markdown audit report.

    Account name and ID are read from config/account.yaml.
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

    print(f"Report written to {filepath}")
    return filepath
