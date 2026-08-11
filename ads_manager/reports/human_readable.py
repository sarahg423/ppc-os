"""Translate marketing metrics into business language.

A small business owner doesn't need to know what CTR is. They need to know
how many people saw their ad, how many clicked, how many became customers,
and what it cost. This module bridges that gap.
"""

from typing import Optional


def business_summary(totals: dict, config: dict, days: int) -> str:
    """One-paragraph summary a non-marketer can understand."""
    clicks = totals.get("clicks", 0)
    impressions = totals.get("impressions", 0)
    cost = totals.get("cost", 0)
    conversions = totals.get("conversions", 0)
    cpa = totals.get("cost_per_conversion")

    brand = config.get("brand", {}).get("short_name", "Your business")

    lines = [f"## How {brand} Did This Week\n"]

    # Build a conversion description from the configured CTAs
    products = config.get("brand", {}).get("products", [])
    if products:
        ctas = list({p.get("cta", "").lower() for p in products if p.get("cta")})
        conversion_desc = ", ".join(ctas[:3]) if ctas else "took action"
    else:
        conversion_desc = "took action"

    # The main story: people, actions, money
    lines.append(
        f"Over the last {days} days, your ads were shown to "
        f"**{impressions:,} people**. "
        f"**{clicks:,}** clicked through to your website"
        + (f", and **{conversions:.0f}** converted ({conversion_desc})." if conversions else ".")
    )

    lines.append(f"You spent **${cost:.2f}** total on ads.")

    if conversions and cpa:
        lines.append(
            f"Each customer action cost you about **${cpa:.2f}**."
        )

    # Budget context
    monthly = config.get("budget", {}).get("monthly")
    if monthly:
        pct_used = (cost / monthly) * 100 if monthly > 0 else 0
        lines.append(
            f"That's **{pct_used:.0f}%** of your ${monthly:.0f}/month budget."
        )

    lines.append("")
    return "\n".join(lines) + "\n"


def trend_summary(comparison: dict, previous_date: str) -> str:
    """Plain-English week-over-week comparison."""
    lines = ["## Compared to Last Report\n"]
    lines.append(f"Your previous audit was **{previous_date}**. Here's what changed:\n")

    changes = []
    for key, label, good_direction, unit in [
        ("clicks", "website visits", "up", ""),
        ("impressions", "people who saw your ads", "up", ""),
        ("conversions", "customer actions", "up", ""),
        ("cost", "ad spend", None, "$"),
        ("cost_per_conversion", "cost per customer action", "down", "$"),
    ]:
        data = comparison.get(key, {})
        delta = data.get("delta")
        pct = data.get("pct")
        current = data.get("current")
        previous = data.get("previous")

        if delta is None or pct is None:
            continue
        if current is None or previous is None:
            continue

        direction = "up" if delta > 0 else "down"
        abs_pct = abs(pct) * 100

        if abs_pct < 3:
            changes.append(f"- **{label.capitalize()}**: Roughly the same ({_fmt(current, unit)} vs {_fmt(previous, unit)})")
            continue

        arrow = _arrow(direction, good_direction)

        changes.append(
            f"- **{label.capitalize()}**: {arrow} {direction} {abs_pct:.0f}% "
            f"({_fmt(previous, unit)} to {_fmt(current, unit)})"
        )

    if not changes:
        lines.append("Not enough data to compare yet. Check back after the next audit.\n")
    else:
        lines.extend(changes)
        lines.append("")

    return "\n".join(lines) + "\n"


def change_attribution(changes: list[dict]) -> str:
    """Show what changes were made since the last audit."""
    if not changes:
        return ""

    lines = ["## Changes You Made\n"]
    lines.append("Since the last audit, here's what was changed:\n")

    for change in changes:
        detail = change.get("details", "")
        change_date = change.get("date", "")
        lines.append(f"- **{change_date}**: {detail}")

    lines.append("")
    lines.append("The trends above reflect the impact of these changes.\n")
    return "\n".join(lines) + "\n"


def plain_english_flags(campaigns: list[dict], benchmarks: dict, config: dict) -> str:
    """Translate benchmark violations into actionable advice for non-marketers."""
    lines = ["## What Needs Attention\n"]
    flags = []

    target_cpa = config.get("budget", {}).get("target_cpa")
    max_cpa = config.get("budget", {}).get("max_cpa")

    for c in campaigns:
        name = c.get("campaign_name", "your campaign")
        ctr = c.get("ctr")
        cpc = c.get("avg_cpc")
        cpa = c.get("cost_per_conversion")
        imp_share = c.get("impression_share")
        clicks = c.get("clicks", 0)
        impressions = c.get("impressions", 0)

        if ctr is not None and ctr < benchmarks.get("ctr_min", 0.03):
            flags.append(
                f"- **People see your ad but don't click.** "
                f"Out of {impressions:,} people who saw your ad, only {clicks:,} clicked. "
                f"Your headlines might not be grabbing attention. "
                f"Consider testing new headlines that mention what makes you different."
            )

        if cpc is not None and cpc > benchmarks.get("cpc_max", 8.0):
            flags.append(
                f"- **Each click is expensive.** "
                f"You're paying ${cpc:.2f} per click, but your target is under "
                f"${benchmarks.get('cpc_max', 8.0):.2f}. "
                f"You might be competing for broad search terms. "
                f"More specific keywords (like 'comedy show bristol' instead of 'things to do') "
                f"are usually cheaper."
            )

        if cpa is not None and max_cpa and cpa > max_cpa:
            flags.append(
                f"- **It's costing too much to get each customer.** "
                f"You're spending ${cpa:.2f} per conversion, but your max is ${max_cpa:.2f}. "
                f"Some keywords might be attracting clicks from people who aren't actually interested."
            )
        elif cpa is not None and target_cpa and cpa > target_cpa:
            flags.append(
                f"- **Customer acquisition cost is above your ideal.** "
                f"At ${cpa:.2f} per customer action (target: ${target_cpa:.2f}), it's working "
                f"but you could do better. Not urgent, but worth watching."
            )

        if imp_share is not None and imp_share < benchmarks.get("impression_share_min", 0.6):
            budget_lost = c.get("budget_lost_is", 0) or 0
            if budget_lost > 0.1:
                flags.append(
                    f"- **Your budget is running out before the day is over.** "
                    f"Your ads stop showing partway through the day because the daily budget "
                    f"is used up. You're missing {budget_lost*100:.0f}% of potential customers. "
                    f"If results are good, consider increasing your monthly budget."
                )
            else:
                flags.append(
                    f"- **Your ads aren't showing as often as they could.** "
                    f"Only {imp_share*100:.0f}% of possible searches show your ad. "
                    f"Improving your ad quality (better headlines, relevant keywords) "
                    f"can help you show up more without spending more."
                )

    if not flags:
        lines.append("Everything looks healthy. No issues need attention right now.\n")
    else:
        lines.extend(flags)
        lines.append("")

    return "\n".join(lines) + "\n"


def plain_english_recommendations(recommendations: list[str]) -> str:
    """Wrap raw recommendations with a human-friendly header."""
    if not recommendations:
        return ""

    lines = ["## Suggested Next Steps\n"]
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")
    return "\n".join(lines) + "\n"


def organic_summary(queries: list[dict], pages: list[dict], days: int) -> str:
    """Plain-English summary of organic search performance from GSC."""
    lines = ["## Organic Search (Free Traffic)\n"]

    total_clicks = sum(q.get("clicks", 0) or 0 for q in queries)
    total_impressions = sum(q.get("impressions", 0) or 0 for q in queries)

    lines.append(
        f"Over the last {days} days, your website appeared in "
        f"**{total_impressions:,} Google searches** and "
        f"**{total_clicks:,} people** clicked through, all without paying for ads.\n"
    )

    # Top queries in plain English
    if queries:
        lines.append("**What people searched to find you:**\n")
        for q in queries[:10]:
            pos = q.get("position", 0)
            clicks = q.get("clicks", 0)
            pos_desc = _position_description(pos)
            lines.append(f"- \"{q['query']}\" — {clicks:,} clicks, {pos_desc}")
        lines.append("")

    # Top pages
    if pages:
        lines.append("**Your most-visited pages from search:**\n")
        for p in pages[:5]:
            clicks = p.get("clicks", 0)
            # Show just the path, not the full URL
            page_url = p.get("page", "")
            path = page_url.split("//", 1)[-1].split("/", 1)[-1] if "//" in page_url else page_url
            display = f"/{path}" if path and not path.startswith("/") else (path or "homepage")
            lines.append(f"- **{display}** — {clicks:,} clicks")
        lines.append("")

    return "\n".join(lines) + "\n"


def organic_opportunities(queries: list[dict]) -> str:
    """Identify organic search opportunities in plain English."""
    lines = ["## Organic Opportunities\n"]
    opportunities = []

    for q in queries:
        pos = q.get("position", 0)
        impressions = q.get("impressions", 0) or 0
        ctr = q.get("ctr", 0) or 0
        clicks = q.get("clicks", 0) or 0

        # High impressions, low CTR, decent position = title/description needs work
        if impressions > 50 and ctr < 0.03 and pos <= 20:
            opportunities.append(
                f"- **\"{q['query']}\"** shows up in {impressions:,} searches but "
                f"almost nobody clicks. Your page title or description might not be "
                f"compelling enough for this search."
            )

        # Position 4-10 with good impressions = close to page 1 top
        elif 4 <= pos <= 10 and impressions > 30:
            opportunities.append(
                f"- **\"{q['query']}\"** — you're on page 1 but near the bottom "
                f"(position {pos:.0f}). Improving your content for this topic "
                f"could move you up and get more clicks for free."
            )

        # Position 11-20 = page 2, worth pushing to page 1
        elif 11 <= pos <= 20 and impressions > 20:
            opportunities.append(
                f"- **\"{q['query']}\"** — you're on page 2 of Google (position {pos:.0f}). "
                f"Most people never go past page 1. Adding content about this topic "
                f"could push you onto page 1."
            )

    if not opportunities:
        lines.append("No obvious quick wins right now. Your organic presence looks solid.\n")
    else:
        lines.append("These are searches where small improvements could get you more free traffic:\n")
        lines.extend(opportunities[:5])
        lines.append("")

    return "\n".join(lines) + "\n"


def paid_organic_overlap_summary(overlaps: list[dict]) -> str:
    """Plain-English summary of keywords where you're paying AND ranking organically."""
    if not overlaps:
        return ""

    lines = ["## Paid vs. Organic Overlap\n"]
    lines.append(
        "You're paying for ads on some searches where you also show up "
        "in organic results for free. That might be intentional (dominating "
        "the page) or wasteful (paying for clicks you'd get anyway).\n"
    )

    for o in overlaps[:5]:
        org_pos = o.get("organic_position", 0)
        paid_cost = o.get("paid_cost", 0)
        org_clicks = o.get("organic_clicks", 0)
        paid_clicks = o.get("paid_clicks", 0)

        if org_pos <= 3:
            advice = "You already rank near the top organically. Consider pausing the paid keyword to save money."
        elif org_pos <= 7:
            advice = "You rank on page 1 but not at the top. The paid ad gives you double visibility."
        else:
            advice = "Your organic ranking is low, so the paid ad is doing the heavy lifting here."

        lines.append(
            f"- **\"{o['keyword']}\"** — Organic position {org_pos:.0f}, "
            f"{org_clicks:,} free clicks vs {paid_clicks:,} paid clicks (${paid_cost:.2f} spent). "
            f"{advice}"
        )

    lines.append("")
    return "\n".join(lines) + "\n"


def search_terms_summary(analysis: dict) -> str:
    """Plain-English summary of what people actually searched."""
    stats = analysis.get("stats", {})
    waste = analysis.get("waste", [])
    opportunities = analysis.get("opportunities", [])

    lines = ["## What People Actually Searched\n"]

    total = stats.get("total_search_terms", 0)
    waste_cost = stats.get("waste_cost", 0)
    waste_count = stats.get("waste_count", 0)
    opp_count = stats.get("opportunity_count", 0)

    lines.append(
        f"Your ads were triggered by **{total} different searches** this period. "
        f"Here's what stood out:\n"
    )

    # Waste section
    if waste:
        lines.append(
            f"### Money being wasted ({waste_count} searches, ${waste_cost:.2f} total)\n"
        )
        lines.append(
            "These searches triggered your ads but nobody converted. "
            "Adding them as negative keywords stops your ads from showing "
            "for these searches, saving money.\n"
        )
        for w in waste[:7]:
            term = w.get("search_term", "")
            cost = w.get("cost", 0)
            clicks = w.get("clicks", 0)
            lines.append(
                f"- **\"{term}\"** — {clicks} clicks, ${cost:.2f} spent, zero conversions"
            )
        if len(waste) > 7:
            remaining_cost = sum(w.get("cost", 0) for w in waste[7:])
            lines.append(
                f"- ...and {len(waste) - 7} more wasted searches (${remaining_cost:.2f} total)"
            )
        lines.append("")

    # Opportunities section
    if opportunities:
        lines.append(
            f"### Searches worth adding as keywords ({opp_count} found)\n"
        )
        lines.append(
            "These searches led to actual conversions but aren't in your keyword "
            "list as exact matches yet. Adding them gives you more control over "
            "bids and helps Google show your ads for these specific searches.\n"
        )
        for o in opportunities[:5]:
            term = o.get("search_term", "")
            convs = o.get("conversions", 0)
            cost = o.get("cost", 0)
            cpa = o.get("cost_per_conversion")
            cpa_str = f" at ${cpa:.2f} each" if cpa else ""
            lines.append(
                f"- **\"{term}\"** — {convs:.0f} conversions{cpa_str}, ${cost:.2f} spent"
            )
        lines.append("")

    if not waste and not opportunities:
        lines.append(
            "Your search terms look clean. No obvious waste or missed opportunities.\n"
        )

    return "\n".join(lines) + "\n"


def negative_keyword_recommendations(candidates: list[dict]) -> str:
    """Format negative keyword candidates as actionable recommendations."""
    if not candidates:
        return ""

    total_savings = sum(c.get("cost", 0) for c in candidates)

    lines = ["## Recommended Negative Keywords\n"]
    lines.append(
        f"Adding these negative keywords could save approximately "
        f"**${total_savings:.2f}** per period by blocking irrelevant searches.\n"
    )

    lines.append("| Search term | Clicks | Cost | Suggested action |")
    lines.append("|-------------|--------|------|------------------|")

    for c in candidates:
        term = c.get("term", "")
        clicks = c.get("clicks", 0)
        cost = c.get("cost", 0)
        match = c.get("match_type", "Negative exact")
        lines.append(f"| \"{term}\" | {clicks} | ${cost:.2f} | Add as {match} |")

    lines.append("")
    lines.append(
        "Say \"add these negative keywords\" to apply them, or pick specific ones to add.\n"
    )
    return "\n".join(lines) + "\n"


def _position_description(pos: float) -> str:
    """Convert a GSC average position to plain English."""
    if pos <= 1:
        return "top of Google"
    elif pos <= 3:
        return f"position {pos:.0f} (near the top of page 1)"
    elif pos <= 7:
        return f"position {pos:.0f} (middle of page 1)"
    elif pos <= 10:
        return f"position {pos:.0f} (bottom of page 1)"
    elif pos <= 20:
        return f"position {pos:.0f} (page 2)"
    else:
        return f"position {pos:.0f} (page {int(pos // 10) + 1})"


def glossary() -> str:
    """Short glossary at the bottom for the curious."""
    return """## Quick Glossary

| Term | What it means |
|------|---------------|
| Impressions | How many times your ad or page was shown to someone |
| Clicks | How many people clicked to visit your site |
| CTR (click-through rate) | % of people who saw your listing and clicked it |
| CPC (cost per click) | What you pay each time someone clicks an ad |
| Conversions | When someone takes action: buys something, signs up, calls |
| Cost per conversion | How much you spent in ads to get one customer action |
| Impression share | % of available searches where your ad actually showed up |
| Quality Score | Google's 1-10 rating of your ad relevance (higher is better and cheaper) |
| Organic search | Free traffic from Google search results (not ads) |
| Position | Where your page appears in Google results (1 = top, 10 = bottom of page 1) |
| Search terms | The actual words people typed into Google before clicking your ad |
| Negative keywords | Words you block so your ad won't show for irrelevant searches |
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(value, unit: str = "") -> str:
    """Format a number with optional unit prefix."""
    if value is None:
        return "n/a"
    if unit == "$":
        return f"${value:,.2f}"
    if isinstance(value, float) and value < 1:
        return f"{value*100:.1f}%"
    return f"{value:,.0f}"


def _arrow(direction: str, good_direction: Optional[str]) -> str:
    """Return a simple text indicator of good/bad/neutral trend."""
    if good_direction is None:
        return ""
    if direction == good_direction:
        return "(good)"
    return "(needs attention)"
