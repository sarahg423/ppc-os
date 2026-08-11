---
name: get-performance
description: >
  Pull Google Ads and organic search performance data and generate analysis.
  Use this skill whenever the user asks to check performance, run an audit,
  see how campaigns are doing, pull metrics, or check organic search traffic.
  Handles both API mode and CSV fallback for Google Ads and Google Search Console.
---

# Get Performance Skill

Pull paid (Google Ads) and organic (Google Search Console) performance data.

## How It Works

1. **Try the API first.** Import and call the API performance module:

```python
from ads_manager.api.client import is_api_available, load_account_config
from ads_manager.api.performance import (
    get_campaign_performance, get_ad_group_performance,
    get_keyword_performance, get_ad_performance,
)
```

2. **If the API is unavailable, fall back to CSV parsing.** Check for exported CSVs in `data/exports/` and parse them:

```python
from ads_manager.csv.parser import (
    list_exports, parse_campaign_export,
    parse_keyword_export, parse_ad_export,
)
```

3. **If no exports exist either**, tell the user to either:
   - Set up API credentials in `config/credentials.yaml`
   - Export data from Google Ads Editor and save CSVs to `data/exports/`

## Workflow

### Step 1: Determine Data Source

```python
from ads_manager.api.client import is_api_available

if is_api_available():
    mode = "api"
else:
    from ads_manager.csv.parser import list_exports
    exports = list_exports()
    mode = "csv" if exports else "none"
```

### Step 2: Pull Data

**API mode** — specify the lookback period (default 7 days):
```python
campaigns = get_campaign_performance(days=7)
keywords = get_keyword_performance(days=7)
ads = get_ad_performance(days=7)
```

**CSV mode** — ask the user which export file to use, or use the most recent:
```python
exports = list_exports()
campaigns = parse_campaign_export(exports[0])
```

### Step 3: Load Benchmarks

```python
config = load_account_config()
benchmarks = config["benchmarks"]
```

### Step 4: Analyze Against Benchmarks

Compare each campaign's metrics against the thresholds in `config/account.yaml`. The specific thresholds are user-configurable — always read them from config rather than using hardcoded values.

Key comparisons:
- CTR vs. `benchmarks.ctr_min`
- Avg CPC vs. `benchmarks.cpc_max`
- Conversion rate vs. `benchmarks.conversion_rate_min`
- Quality score vs. `benchmarks.quality_score_min`
- Impression share vs. `benchmarks.impression_share_min`
- Cost per conversion vs. `benchmarks.cost_per_conversion_max`

### Step 4b: Pull Search Term Data

Pull what people actually searched (not just what keywords you're targeting). This is the most actionable data in the audit — it reveals waste and opportunities.

```python
from ads_manager.api.performance import get_search_terms_performance
from ads_manager.search_terms import analyze_search_terms, generate_negative_candidates

search_term_analysis = None
negative_candidates = None

if is_api_available():
    search_terms = get_search_terms_performance(days=7)
    search_term_analysis = analyze_search_terms(search_terms, keywords)
    negative_candidates = generate_negative_candidates(search_term_analysis["waste"])
else:
    # Check for search terms CSV export
    from ads_manager.csv.parser import parse_search_terms_export
    # Look for files with "search" and "term" in the name in data/exports/
```

The analysis categorizes every search term:
- **Waste**: Clicks and cost with zero conversions (negative keyword candidates)
- **Opportunities**: Converting searches not yet in the keyword list as exact matches
- **Working**: Converting searches that match existing keywords

### Step 4c: Pull Organic Search Data (if available)

Check if Google Search Console is configured, and pull organic data using the same API-first, CSV-fallback pattern:

```python
from ads_manager.api.search_console import is_gsc_available, get_query_performance, get_page_performance, find_paid_organic_overlap

organic_queries = None
organic_pages = None
paid_organic_overlaps = None

if is_gsc_available():
    organic_queries = get_query_performance(days=7)
    organic_pages = get_page_performance(days=7)
    # Find keywords where the user pays for ads but also ranks organically
    paid_organic_overlaps = find_paid_organic_overlap(organic_queries, keywords)
else:
    # Check for GSC CSV exports
    from ads_manager.csv.search_console_parser import list_gsc_exports, parse_gsc_queries_export, parse_gsc_pages_export
    gsc_exports = list_gsc_exports()
    if gsc_exports:
        for export in gsc_exports:
            name = export.name.lower()
            if "quer" in name:
                organic_queries = parse_gsc_queries_export(export)
            elif "page" in name:
                organic_pages = parse_gsc_pages_export(export)
        if organic_queries and keywords:
            paid_organic_overlaps = find_paid_organic_overlap(organic_queries, keywords)
```

If neither API nor CSV data is available for GSC, skip the organic sections. Don't error — organic data is optional. Mention to the user that setting up GSC would make future reports more complete.

### Step 5: Generate Reports

Generate both a technical audit and a plain-English business report:

```python
from ads_manager.reports.generator import generate_audit_report, generate_business_report

# Technical report — detailed tables, benchmark flags
audit_path = generate_audit_report(
    campaigns=campaigns, keywords=keywords,
    benchmarks=benchmarks, recommendations=recommendations,
    days=7,
)

# Business report — plain English, search terms, organic data, trends
business_path = generate_business_report(
    campaigns=campaigns, keywords=keywords,
    benchmarks=benchmarks, recommendations=recommendations,
    days=7,
    organic_queries=organic_queries,
    organic_pages=organic_pages,
    paid_organic_overlaps=paid_organic_overlaps,
    search_term_analysis=search_term_analysis,
    negative_candidates=negative_candidates,
)
```

The business report (`reports/report_YYYY-MM-DD.md`) is written for non-technical users. It:
- Translates metrics into business language ("47 people visited your site, 3 bought tickets")
- Shows week-over-week trends compared to the previous audit snapshot
- Attributes changes ("since you paused keyword X, cost per customer dropped 18%")
- Explains issues in plain English with specific advice
- Includes a glossary of marketing terms

The technical report (`reports/audit_YYYY-MM-DD.md`) keeps the full metric tables for deeper analysis.

Both reports save a historical snapshot to `data/history/` automatically. This powers future trend comparisons.

**Default to the business report** unless the user asks for detailed metrics or is clearly comfortable with marketing terminology.

### Step 6: Present Findings

After generating the report, present the business summary directly in the conversation:
- How many people saw ads, clicked, and took action
- What it cost and how that compares to last time
- What needs attention, in plain English
- Suggested next steps
- Path to both reports

## Date Range Options

- `days=7` — Last 7 days (default, good for weekly audits)
- `days=14` — Last 14 days (good for trend analysis)
- `days=30` — Last 30 days (good for monthly reviews)
- `days=90` — Last quarter
