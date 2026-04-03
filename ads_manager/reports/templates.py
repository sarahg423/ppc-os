"""Markdown templates for report sections.

Each function returns a string of Markdown. The report generator
assembles these into a complete audit report. Account name and ID
are passed in — nothing is hardcoded.
"""

from datetime import date


def report_header(title: str, date_range: str, account_name: str, account_id: str) -> str:
    return f"""# {title}

**Generated**: {date.today().isoformat()}
**Period**: {date_range}
**Account**: {account_name} ({account_id})

---
"""


def campaign_summary_table(campaigns: list[dict]) -> str:
    if not campaigns:
        return "## Campaign Summary\n\nNo campaign data available.\n"

    lines = ["## Campaign Summary\n"]
    lines.append("| Campaign | Status | Budget | Impressions | Clicks | CTR | Avg CPC | Cost | Conv. | Cost/Conv. | Impr. Share |")
    lines.append("|----------|--------|--------|-------------|--------|-----|---------|------|-------|------------|-------------|")

    for c in campaigns:
        ctr = f"{c.get('ctr', 0) * 100:.1f}%" if c.get('ctr') else "—"
        cpc = f"${c.get('avg_cpc', 0):.2f}" if c.get('avg_cpc') else "—"
        cost = f"${c.get('cost', 0):.2f}" if c.get('cost') is not None else "—"
        conv = f"{c.get('conversions', 0):.0f}" if c.get('conversions') is not None else "—"
        cpa = f"${c.get('cost_per_conversion', 0):.2f}" if c.get('cost_per_conversion') else "—"
        imp_share = f"{c.get('impression_share', 0) * 100:.0f}%" if c.get('impression_share') else "—"
        budget = f"${c.get('daily_budget', 0):.2f}/d" if c.get('daily_budget') else "—"

        lines.append(
            f"| {c.get('campaign_name', '?')} | {c.get('status', '?')} | {budget} "
            f"| {c.get('impressions', 0):,} | {c.get('clicks', 0):,} | {ctr} "
            f"| {cpc} | {cost} | {conv} | {cpa} | {imp_share} |"
        )
    return "\n".join(lines) + "\n"


def keyword_performance_table(keywords: list[dict], top_n: int = 20) -> str:
    if not keywords:
        return "## Top Keywords\n\nNo keyword data available.\n"

    lines = ["## Top Keywords (by spend)\n"]
    lines.append("| Keyword | Match | QS | Impressions | Clicks | CTR | CPC | Cost | Conv. |")
    lines.append("|---------|-------|----|-------------|--------|-----|-----|------|-------|")

    for kw in keywords[:top_n]:
        ctr = f"{kw.get('ctr', 0) * 100:.1f}%" if kw.get('ctr') else "—"
        cpc = f"${kw.get('avg_cpc', 0):.2f}" if kw.get('avg_cpc') else "—"
        cost = f"${kw.get('cost', 0):.2f}" if kw.get('cost') is not None else "—"
        qs = str(kw.get('quality_score', '—')) if kw.get('quality_score') else "—"

        lines.append(
            f"| {kw.get('keyword', '?')} | {kw.get('match_type', '?')} | {qs} "
            f"| {kw.get('impressions', 0):,} | {kw.get('clicks', 0):,} | {ctr} "
            f"| {cpc} | {cost} | {kw.get('conversions', 0):.0f} |"
        )
    return "\n".join(lines) + "\n"


def benchmark_flags(campaigns: list[dict], benchmarks: dict) -> str:
    lines = ["## Benchmark Flags\n"]
    flags = []

    for c in campaigns:
        name = c.get("campaign_name", "Unknown")

        ctr = c.get("ctr")
        if ctr is not None and ctr < benchmarks.get("ctr_min", 0.03):
            flags.append(f"- **{name}**: CTR {ctr*100:.1f}% is below {benchmarks['ctr_min']*100:.0f}% threshold")

        cpc = c.get("avg_cpc")
        if cpc is not None and cpc > benchmarks.get("cpc_max", 8.0):
            flags.append(f"- **{name}**: Avg CPC ${cpc:.2f} exceeds ${benchmarks['cpc_max']:.2f} cap")

        cpa = c.get("cost_per_conversion")
        if cpa is not None and cpa > benchmarks.get("cost_per_conversion_max", 50.0):
            flags.append(f"- **{name}**: Cost/conv ${cpa:.2f} exceeds ${benchmarks['cost_per_conversion_max']:.2f}")

        imp_share = c.get("impression_share")
        if imp_share is not None and imp_share < benchmarks.get("impression_share_min", 0.6):
            flags.append(f"- **{name}**: Impression share {imp_share*100:.0f}% below {benchmarks['impression_share_min']*100:.0f}%")

    if not flags:
        lines.append("All campaigns within benchmark ranges.\n")
    else:
        lines.extend(flags)
        lines.append("")
    return "\n".join(lines) + "\n"


def recommendations_section(recommendations: list[str]) -> str:
    if not recommendations:
        return "## Recommendations\n\nNo recommendations at this time.\n"
    lines = ["## Recommendations\n"]
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")
    return "\n".join(lines) + "\n"
