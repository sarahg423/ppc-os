---
name: keyword-strategy
description: >
  Review and optimize keyword strategy for budget efficiency. Use this skill
  when the user asks to review keywords, optimize match types, check search
  terms, tighten keyword strategy, reduce waste, or improve keyword performance.
  Also use when building keywords for a new campaign — this skill handles
  match type selection and bid recommendations based on budget constraints.
---

# Keyword Strategy Skill

Analyze, optimize, and manage keywords for maximum efficiency on any budget.

## FIRST: Load Context

Before making any keyword recommendations, load:

1. **Account config** — budget constraints and benchmarks drive everything:

```python
from ads_manager.api.client import load_account_config

config = load_account_config()
budget = config["budget"]
benchmarks = config["benchmarks"]

daily_budget = budget["daily"]
target_cpa = budget.get("target_cpa")
max_cpa = budget.get("max_cpa")
max_cpc = benchmarks.get("cpc_max")
```

2. **Campaign scope** — read `config/campaigns.md` to know what's managed
3. **Brand voice** — read `config/brand-voice.md` for product context and audience

## Core Principles

### Budget-Aware Keyword Management

The keyword strategy MUST be driven by the budget:

| Monthly Budget | Max Keywords | Recommended Approach |
|---------------|-------------|---------------------|
| Under $200 | 10–20 | Mostly Exact match, 3–5 Phrase match for discovery |
| $200–$500 | 20–40 | Mix of Exact and Phrase, limited Broad |
| $500–$2000 | 40–100 | Phrase-heavy with Exact on top converters |
| $2000+ | 100+ | Full funnel with Broad, Phrase, and Exact |

**Never recommend more keywords than the budget can support.** A keyword that gets 1 click per month isn't worth tracking.

### Match Type Ladder

Keywords should move through match types based on performance data:

```
Phrase match (testing) → high CTR + conversions → Exact match (scaling)
                       → low CTR or no conversions → pause or negate
```

- **Exact match** — Use for proven, high-intent keywords. Higher bids justified because conversion rate is higher.
- **Phrase match** — Use for discovery and testing. Lower bids to control spend while learning.
- **Broad match** — Only with Smart Bidding and sufficient conversion data (50+ conversions/month). Almost never appropriate for budgets under $500/month.

### Bid Strategy by Match Type

Bid inversely to match breadth — tighter match = higher bid:

| Match Type | Bid Recommendation |
|-----------|-------------------|
| Exact | Up to max CPC from config |
| Phrase | 65–80% of max CPC |
| Broad | 50–65% of max CPC (rarely used on small budgets) |

## Workflows

### 1. New Campaign Keyword Build

When building keywords for a new campaign:

1. **Understand the business** — What do they sell? Who's searching? What terms would a customer use?
2. **Map search intent** — Group keywords by intent:
   - **High intent**: Searching for exactly what you offer (e.g., "comedy show bristol")
   - **Medium intent**: Searching for the category (e.g., "live entertainment near me")
   - **Low intent**: Broad discovery (e.g., "things to do tonight")
3. **Select match types based on budget** — Use the budget table above
4. **Set bids based on match type** — Use the bid strategy table above
5. **Add negatives proactively** — Block obvious waste (jobs, DIY, streaming, etc.)
6. **Generate CSV** — Use `write_keyword_csv()` from `ads_manager/csv/generator`

### 2. Keyword Performance Review

When reviewing existing keyword performance:

1. **Pull performance data**:

```python
from ads_manager.api.client import is_api_available
if is_api_available():
    from ads_manager.api.performance import get_keyword_performance
    keywords = get_keyword_performance(days=30)
```

If API isn't available, ask the user to export keyword performance from Google Ads or Ads Editor.

2. **Categorize each keyword**:

| Category | Criteria | Action |
|----------|----------|--------|
| Star | High CTR, converting, CPA below target | Increase bid, ensure Exact match |
| Potential | Decent CTR, few or no conversions yet | Keep running, monitor for 2 more weeks |
| Money pit | Spending but not converting | Lower bid or pause |
| Dead weight | Few impressions, no clicks | Pause — it's not matching searches |
| Expensive | CPC above max, eating budget | Lower bid or switch to Exact match |

3. **Generate recommendations** — Be specific:
   - "Pause keyword X — spent $15 with 0 conversions in 30 days"
   - "Switch keyword Y to Exact — it's converting at 5% but Phrase match is triggering irrelevant searches"
   - "Add 'Z' as a negative — showing up in search terms but irrelevant"

### 3. Search Terms Analysis

When the user has search terms data (from API or exported CSV):

1. **Find converting search terms** not already keywords → recommend adding as Exact match
2. **Find irrelevant search terms** eating budget → recommend as negative keywords
3. **Find search terms with high impressions but low CTR** → the ad copy doesn't match the intent, consider a new ad group
4. **Calculate waste** — What percentage of spend went to irrelevant terms?

### 4. Match Type Optimization

When reviewing match types across the account:

1. **Check for Broad match on small budgets** → recommend switching to Phrase or Exact
2. **Check for Phrase match keywords with enough data** → if converting well, create Exact match version at higher bid
3. **Check for duplicate coverage** → same keyword in Phrase and Exact wastes budget competing with yourself
4. **Check for keyword cannibalization** → multiple ad groups targeting the same searches

## Generating Output

### Keyword CSV

```python
from ads_manager.csv.generator import write_keyword_csv

rows = [
    {
        "Campaign": "Campaign Name",
        "Ad Group": "Ad Group Name",
        "Keyword": "the keyword",
        "Match Type": "Exact",  # Exact, Phrase, or Broad
        "Max CPC": "1.50",     # No dollar sign
        "Status": "Active",    # Active, Paused, or Removed
    },
]
write_keyword_csv(rows, filename="optimized_keywords.csv")
```

### Negative Keyword CSV

```python
from ads_manager.csv.generator import write_negative_keyword_csv

rows = [
    {
        "Campaign": "Campaign Name",
        "Keyword": "irrelevant term",
        "Criterion Type": "Negative phrase",  # Negative broad, Negative phrase, Negative exact
    },
]
write_negative_keyword_csv(rows, filename="new_negatives.csv")
```

## Presenting Recommendations

Always present keyword changes as a clear table before generating CSVs:

```markdown
### Keyword Changes

| Action | Ad Group | Keyword | Current Match | New Match | Current Bid | New Bid | Why |
|--------|----------|---------|---------------|-----------|-------------|---------|-----|
| Change | ... | ... | Phrase | Exact | $1.00 | $1.50 | Converting at 4%, lock in the match |
| Pause | ... | ... | Phrase | — | $1.00 | — | $12 spent, 0 conversions |
| Add | ... | ... | — | Exact | — | $1.50 | Found in search terms, 3 conversions |

### New Negatives

| Keyword | Type | Why |
|---------|------|-----|
| ... | Negative phrase | Showed 45 times, 0 clicks, irrelevant |
```

Get user confirmation before generating CSVs or pushing changes.
