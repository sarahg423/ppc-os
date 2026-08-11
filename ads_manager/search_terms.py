"""Search term analysis — find waste and opportunities in actual search queries.

Keywords are what you target. Search terms are what people actually typed.
The gap between these reveals:
  - Waste: irrelevant searches costing money with no conversions
  - Opportunities: converting searches you haven't added as keywords
  - Cannibalization: one search term matching multiple keywords
"""

from ads_manager.api.client import load_account_config


def analyze_search_terms(
    search_terms: list[dict],
    keywords: list[dict],
) -> dict:
    """Categorize search terms into waste, opportunities, and working.

    Returns a dict with:
        waste: terms with clicks/cost but no conversions (negative keyword candidates)
        opportunities: terms with conversions that aren't exact-match keywords yet
        working: terms that are converting well
        stats: summary numbers
    """
    config = load_account_config()
    benchmarks = config.get("benchmarks", {})
    max_cpa = config.get("budget", {}).get("max_cpa") or benchmarks.get("cost_per_conversion_max", 50)

    # Build a set of existing keywords for matching
    existing_keywords = set()
    for kw in keywords:
        text = kw.get("keyword", "").lower().strip()
        if text:
            existing_keywords.add(text)

    waste = []
    opportunities = []
    working = []

    for st in search_terms:
        term = st.get("search_term", "")
        clicks = st.get("clicks", 0) or 0
        cost = st.get("cost", 0) or 0
        conversions = st.get("conversions", 0) or 0
        cpa = st.get("cost_per_conversion")

        if clicks == 0:
            continue

        # Waste: clicks and cost but no conversions
        if conversions == 0 and cost > 0:
            waste.append({
                **st,
                "reason": _waste_reason(st, benchmarks),
            })

        # Opportunity: converting but not an exact-match keyword
        elif conversions > 0:
            term_lower = term.lower().strip()
            if term_lower not in existing_keywords:
                opportunities.append({
                    **st,
                    "reason": f"Converting ({conversions:.0f} conversions at ${cpa:.2f} each) but not an exact-match keyword yet",
                })
            else:
                working.append(st)

    # Sort waste by cost descending (biggest money drain first)
    waste.sort(key=lambda x: x.get("cost", 0), reverse=True)
    # Sort opportunities by conversions descending
    opportunities.sort(key=lambda x: x.get("conversions", 0), reverse=True)

    total_waste_cost = sum(w.get("cost", 0) for w in waste)
    total_waste_clicks = sum(w.get("clicks", 0) for w in waste)

    return {
        "waste": waste,
        "opportunities": opportunities,
        "working": working,
        "stats": {
            "total_search_terms": len(search_terms),
            "waste_count": len(waste),
            "waste_cost": total_waste_cost,
            "waste_clicks": total_waste_clicks,
            "opportunity_count": len(opportunities),
            "working_count": len(working),
        },
    }


def _waste_reason(st: dict, benchmarks: dict) -> str:
    """Generate a human-readable reason why a search term is wasteful."""
    cost = st.get("cost", 0) or 0
    clicks = st.get("clicks", 0) or 0
    term = st.get("search_term", "")
    matched = st.get("matched_keyword", "")

    parts = []

    if cost > 5:
        parts.append(f"${cost:.2f} spent with zero conversions")
    elif clicks > 3:
        parts.append(f"{clicks} clicks with zero conversions")

    if matched and term.lower() != matched.lower():
        parts.append(f"broad-matched from '{matched}'")

    return "; ".join(parts) if parts else "Clicks with no conversions"


def generate_negative_candidates(waste: list[dict], max_candidates: int = 20) -> list[dict]:
    """Pick the best negative keyword candidates from waste terms.

    Prioritizes by cost, then groups related terms to suggest phrase-level
    negatives where possible.
    """
    candidates = []
    seen_roots = set()

    for w in waste[:max_candidates * 2]:
        term = w.get("search_term", "").lower().strip()
        if not term:
            continue

        # Check if a similar term is already a candidate
        words = set(term.split())
        if words & seen_roots and len(words) <= 3:
            continue

        candidates.append({
            "term": w.get("search_term", ""),
            "match_type": _suggest_negative_match_type(w),
            "cost": w.get("cost", 0),
            "clicks": w.get("clicks", 0),
            "reason": w.get("reason", ""),
        })

        seen_roots.update(term.split())

        if len(candidates) >= max_candidates:
            break

    return candidates


def _suggest_negative_match_type(waste_term: dict) -> str:
    """Suggest whether a negative keyword should be exact, phrase, or broad.

    - Exact: if the term is specific and the exact query is the problem
    - Phrase: if the term contains a problematic phrase that appears in variations
    - Broad: rarely — only for single words that are clearly irrelevant
    """
    term = waste_term.get("search_term", "")
    words = term.split()

    if len(words) == 1:
        return "Negative broad"
    elif len(words) <= 3:
        return "Negative phrase"
    else:
        return "Negative exact"
