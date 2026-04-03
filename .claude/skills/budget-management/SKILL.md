---
name: budget-management
description: >
  Manage campaign budgets, keyword bids, and spend pacing for Google Ads.
  Use this skill when the user asks to change budgets, adjust bids, review
  spend pacing, reallocate budget between campaigns, or optimize for cost
  efficiency. Reads all thresholds from config/account.yaml.
---

# Budget Management Skill

Adjust campaign budgets, keyword bids, and monitor spend pacing.

## Workflow

### Step 1: Get Current State

Always start by pulling current performance. Use the `get-performance` skill or call directly:

```python
from ads_manager.api.client import is_api_available, load_account_config

if is_api_available():
    from ads_manager.api.performance import get_campaign_performance, get_keyword_performance
    campaigns = get_campaign_performance(days=7)
    keywords = get_keyword_performance(days=7)
else:
    from ads_manager.csv.parser import list_exports, parse_campaign_export, parse_keyword_export
    # Parse most recent export
```

Load benchmarks from config:
```python
config = load_account_config()
benchmarks = config["benchmarks"]
```

### Step 2: Analyze Spend Efficiency

For each campaign, evaluate:

1. **Budget utilization**: Is the campaign spending its full daily budget?
   - If impression share is low AND budget_lost_impression_share is high → budget is the constraint
   - If impression share is low BUT budget_lost_is is low → it's a bid/relevance problem

2. **Cost per conversion**: Compare against `benchmarks.cost_per_conversion_max`
   - Below threshold → healthy, consider scaling
   - Above threshold → needs intervention

3. **Keyword-level efficiency**: Which keywords are worth the spend?
   - High spend + low conversions → reduce bid or pause
   - Low spend + good conversion rate → increase bid
   - High quality score + low impression share → increase bid (good opportunity)

### Step 3: Make Recommendations

Present recommendations as a structured table:

```
| Change | Entity | Current | Proposed | Rationale |
|--------|--------|---------|----------|-----------|
| Budget | Campaign A | $25/d | $35/d | 85% utilization, good CPA |
| Bid | "keyword" [Broad] | $5.50 | $3.50 | 0 conv in 30d |
| Pause | "keyword" [Broad] | Active | Paused | QS 3, low CTR, 0 conv |
```

### Step 4: Apply Changes

**ALWAYS confirm with the user before pushing changes.**

**API mode:**
```python
from ads_manager.api.mutate import update_campaign_budget, update_keyword_bid, update_keyword_status

update_campaign_budget(campaign_id=123, new_daily_budget=35.00)
update_keyword_bid(ad_group_id=123, criterion_id=456, new_cpc=3.50)
update_keyword_status(ad_group_id=123, criterion_id=789, status="PAUSED")
```

**CSV mode:**
```python
from ads_manager.csv.generator import write_budget_csv, write_keyword_csv

write_budget_csv([{"Campaign": "Campaign A", "Budget": "35.00"}])
write_keyword_csv([{"Campaign": "Campaign A", "Ad Group": "Group 1",
                     "Keyword": "keyword", "Match Type": "Broad",
                     "Max CPC": "3.50", "Status": "Active"}])
```

### Step 5: Document Changes

After applying, generate a brief change log entry.

## Budget Rules of Thumb

1. **Never increase budget more than 30% at once** — Google's algorithm needs time to adjust
2. **Don't change bids on keywords with < 50 clicks** — insufficient data
3. **Pause keywords with 0 conversions and > $100 spend** — they've had their chance
4. **Increase bids on keywords with QS >= quality_score_min and low impression share**
5. **Review budget pacing weekly** — daily fluctuations are normal

## Monthly Budget Planning

- Daily budget x 30.4 = approximate monthly spend
- Google can spend up to 2x daily budget on any given day but averages to daily over the month
