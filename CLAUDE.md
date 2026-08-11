# ppc-os — Claude Code Instructions

You are managing paid and organic search marketing. All account-specific configuration — account ID, brand name, voice rules, benchmarks, and ad copy guidelines — lives in `config/account.yaml`. **Always read that file before doing any work.** Never hardcode account IDs, brand names, or URLs.

## Quick Start

**New user?** Just run this — the getting-started skill will interview you and generate all config files:

```bash
pip install -r requirements.txt
claude "Help me get started"
```

That interview generates three files: `config/account.yaml` (account settings and benchmarks), `config/brand-voice.md` (tone and writing guidelines), and `config/campaigns.md` (which campaigns to manage and what to change). All other skills read from these files.

**Already configured?** Jump straight to work:

```bash
claude "Run a full campaign audit for the last 7 days"
```

## Architecture

This repo has two modes for interacting with Google Ads and Google Search Console:

1. **API mode** (primary) — Uses the `google-ads` Python SDK and `google-api-python-client` to pull performance data and push changes programmatically. Requires credentials in `config/credentials.yaml`.
2. **CSV mode** (fallback) — Generates properly formatted CSVs for import into the Google Ads Editor desktop app, and parses exported CSVs for performance data. For GSC, parses CSV exports from the Search Console web interface. Use this when API credentials aren't available.

Always try API mode first. If it fails (missing credentials, auth errors), fall back to CSV mode and tell the user. Organic search (GSC) data is optional — audits work without it, but are more useful with it.

## Project Structure

```
├── CLAUDE.md                    # You are here
├── config/
│   ├── credentials.example.yaml # Template for API credentials
│   ├── credentials.yaml         # Actual credentials (gitignored)
│   ├── account.example.yaml     # Example account config (committed)
│   ├── account.yaml             # Your account config (gitignored)
│   ├── brand-voice.md           # Tone guidelines and writing samples (gitignored)
│   └── campaigns.md             # Which campaigns are managed (gitignored)
├── ads_manager/
│   ├── api/                     # API client wrappers
│   │   ├── client.py            # Google Ads auth and client initialization
│   │   ├── performance.py       # Pull campaign/ad group/keyword metrics
│   │   ├── mutate.py            # Push changes (budgets, bids, ads, keywords)
│   │   └── search_console.py    # Google Search Console organic data
│   ├── csv/                     # CSV generation and parsing
│   │   ├── generator.py         # Generate import-ready CSVs for Ads Editor
│   │   ├── parser.py            # Parse exported CSVs from Ads Editor
│   │   ├── validator.py         # Validate CSV format before export
│   │   └── search_console_parser.py  # Parse GSC CSV exports
│   ├── history.py               # Historical snapshots and change tracking
│   └── reports/                 # Markdown report generation
│       ├── templates.py         # Technical report templates
│       ├── human_readable.py    # Business-language report sections
│       └── generator.py         # Assemble full audit reports
├── .claude/
│   └── skills/                  # Claude Code skills
│       ├── getting-started/     # Onboarding interview — run this first
│       ├── get-performance/     # Pull and analyze performance data (paid + organic)
│       ├── ad-creation/         # Create and edit RSA ad copy
│       ├── budget-management/   # Adjust budgets and bids
│       ├── keyword-strategy/    # Keyword optimization and search term analysis
│       ├── gbp-posting/         # Google Business Profile posts and events
│       ├── push-changes/        # Push changes via API or CSV
│       └── schedule-setup/      # Set up automated audit schedules
├── reports/                     # Generated reports land here
├── data/
│   ├── imports/                 # CSVs ready for Ads Editor import
│   ├── exports/                 # CSVs exported from Ads Editor or GSC
│   └── history/                 # Audit snapshots and change log (gitignored)
└── scripts/
    └── audit.py                 # Full audit workflow script
```

## How Configuration Works

Everything account-specific is in `config/account.yaml`. The code reads this file at runtime — nothing is hardcoded. When writing ad copy, generating CSVs, or making recommendations, always reference this config:

```python
from ads_manager.api.client import load_account_config
config = load_account_config()

account_id   = config["account"]["id"]           # e.g. "123-456-7890"
brand_name   = config["brand"]["name"]            # e.g. "Acme Corp"
benchmarks   = config["benchmarks"]               # CTR, CPC thresholds, etc.
ad_rules     = config["ad_copy"]                  # char limits, forbidden phrases, CTAs
```

## Ad Copy Character Limits (Google Ads universal)

| Field | Max |
|-------|-----|
| Headline 1–15 | 30 |
| Description 1–4 | 90 |
| Path 1, Path 2 | 15 |

## CSV Rules (for Ads Editor compatibility)

- Every CSV MUST have `Account` as the first column with the account ID from config
- UTF-8 encoding, no BOM
- Use Python's `csv.writer` for proper quoting — never manually quote fields
- Always validate character limits before writing CSVs
- Match Type values: `Broad`, `Phrase`, `Exact` (capitalized)
- Status values: `Active`, `Paused`, `Removed`
- Budget/CPC: plain numbers, no dollar signs (e.g., `3.50` not `$3.50`)

## Performance Benchmarks

Benchmarks are defined in `config/account.yaml` under the `benchmarks` key. When auditing campaigns, load them from config and flag anything outside the defined ranges. Default actions:

| Metric | Action if Outside Range |
|--------|------------------------|
| CTR | Review ad copy, check keyword relevance |
| CPC | Review bid strategy, check competition |
| Conv. Rate | Review landing pages, check audience targeting |
| Quality Score | Improve ad relevance, landing page experience |
| Impression Share | Consider budget increase or bid adjustment |
| Cost/Conv. | Review keyword performance, pause underperformers |

## Brand Voice

Brand voice rules (forbidden phrases, preferred CTAs, tone guidelines) are all in `config/account.yaml` under `brand` and `ad_copy`. Always check these before writing any ad copy. Never assume brand rules — read the config.

## Workflow: Weekly Audit

1. **Pull performance** → Use `get-performance` skill for last 7 days (paid + organic)
2. **Analyze** → Compare against benchmarks from config, identify underperformers
3. **Recommend changes** → Generate specific, actionable recommendations
4. **Generate reports** → Business report (plain English) + technical report in `reports/`
5. **Prepare changes** → Use appropriate skills to create change sets
6. **Review** → Present changes to user before pushing
7. **Push** → Use `push-changes` skill to apply (API or CSV)

The business report is the default for non-technical users. It uses plain English, shows week-over-week trends, attributes changes to actions taken, and includes organic search data when available. The technical report has the full metric tables for deeper analysis.

## Reports and History

Audit snapshots are saved to `data/history/` as JSON files. Each snapshot records campaign metrics, keyword data, and recommendations. The business report automatically compares against the previous snapshot to show trends.

Changes made via `push-changes` are logged in `data/history/change_log.json` so the next audit can attribute results: "Since you paused keyword X on Monday, cost per customer dropped 18%."
