---
name: get-performance
description: >
  Pull Google Ads campaign performance data and generate analysis. Use this
  skill whenever the user asks to check performance, run an audit, see how
  campaigns are doing, or pull metrics. Handles both API mode and CSV fallback.
---

# Get Performance Skill

Pull campaign, ad group, keyword, and ad-level performance data from Google Ads.

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

### Step 5: Generate Report

```python
from ads_manager.reports.generator import generate_audit_report

report_path = generate_audit_report(
    campaigns=campaigns, keywords=keywords,
    benchmarks=benchmarks, recommendations=recommendations,
    days=7,
)
```

The report is written to `reports/audit_YYYY-MM-DD.md`. Account name and ID are read from config automatically.

### Step 6: Present Findings

After generating the report, present a concise summary:
- Overall account spend and key metrics
- Any campaigns flagged by benchmarks
- Top 3-5 actionable recommendations
- Path to the full report

## Date Range Options

- `days=7` — Last 7 days (default, good for weekly audits)
- `days=14` — Last 14 days (good for trend analysis)
- `days=30` — Last 30 days (good for monthly reviews)
- `days=90` — Last quarter
