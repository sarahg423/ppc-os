# ppc-os

An open-source operating system for your paid and organic search marketing, powered by [Claude Code](https://claude.com/claude-code). Pull performance data, audit campaigns, analyze search terms, track organic rankings, write ad copy, manage your Google Business Profile, and push changes — all from the command line.

Works with any Google Ads account. All account-specific configuration (brand name, voice rules, benchmarks) lives in a single YAML file you customize for your business.

## What It Does

- **Pulls performance data** from Google Ads and Google Search Console (API or CSV)
- **Audits campaigns** against configurable benchmarks
- **Analyzes search terms** to find wasted spend and keyword opportunities
- **Tracks organic search** rankings, click-through rates, and paid/organic overlap
- **Generates plain-English reports** a non-marketer can understand, with week-over-week trends
- **Suggests edits** to ad copy, budgets, bids, and keywords
- **Posts to Google Business Profile** for local search visibility
- **Pushes changes** via the Google Ads API or generates Ads Editor CSV files

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-org/ppc-os.git
cd ppc-os
pip install -r requirements.txt
```

### 2. Run the getting-started interview

```bash
claude "Help me get started"
```

Claude will walk you through a conversation about your business, brand voice, target audience, budget, and goals. It asks for writing samples so it can match your tone when creating ad copy. At the end, it generates three config files:

- `config/account.yaml` — Account ID, products, benchmarks, ad copy rules, budget, GSC settings
- `config/brand-voice.md` — Tone guidelines, writing samples, do/don't lists
- `config/campaigns.md` — Which campaigns to manage and what's allowed to change

You choose whether to manage all your campaigns, a subset, or start building new ones from scratch.

### 3. Configure credentials (optional, for API mode)

```bash
cp config/credentials.example.yaml config/credentials.yaml
# Edit with your Google Ads, Search Console, and/or GBP credentials
```

If you skip this step, the tool works in **CSV mode** — you export data from the Google Ads Editor or Search Console web interface, place CSVs in `data/exports/`, and the tool generates import-ready CSVs in `data/imports/`.

### 4. Run with Claude Code

```bash
# Full weekly audit (paid + organic + search terms)
claude "Run a full campaign audit for the last 7 days"

# Check how marketing is doing (plain English)
claude "How's my marketing doing?"

# Check specific campaign performance
claude "How is the Brand Search campaign performing this month?"

# Write new ad copy
claude "Write 3 new RSA variants for the Product Launch campaign"

# Analyze search terms for waste
claude "What are people searching that's wasting my budget?"

# Post to Google Business Profile
claude "Post our upcoming event to GBP"

# Adjust budgets
claude "The Brand campaign is budget-constrained — recommend a new budget"

# Push changes
claude "Push the budget and keyword changes we discussed"

# Set up automated audits
claude "Set up a recurring audit schedule"
```

### 5. Run the audit script directly

```bash
# Full audit via API (generates both technical and business reports)
python scripts/audit.py --days 7

# Business report only (plain English)
python scripts/audit.py --days 7 --business-only

# Via CSV export
python scripts/audit.py --csv data/exports/campaign_report.csv
```

## Claude Code Skills

This repo includes eight skills that Claude Code picks up automatically:

| Skill | Purpose |
|-------|---------|
| `getting-started` | Onboarding interview — configures everything for your account |
| `get-performance` | Pull paid and organic metrics, generate audit reports |
| `ad-creation` | Write RSA ad copy enforcing your brand voice |
| `budget-management` | Adjust budgets, bids, and analyze pacing |
| `keyword-strategy` | Optimize keywords, analyze search terms, find waste |
| `gbp-posting` | Create and manage Google Business Profile posts |
| `push-changes` | Apply changes via API or generate Ads Editor CSVs |
| `schedule-setup` | Set up automated recurring audits (ramp-up then maintenance) |

## Reports

The audit generates two reports:

| Report | Audience | File |
|--------|----------|------|
| **Business report** | Non-technical users | `reports/report_YYYY-MM-DD.md` |
| **Technical report** | Marketers, deep dives | `reports/audit_YYYY-MM-DD.md` |

The business report translates everything into plain English:
- "47 people visited your site, 3 bought tickets, you spent $22"
- Week-over-week trends with good/needs-attention indicators
- Change attribution: "Since you paused keyword X, cost per customer dropped 18%"
- Search term analysis: waste and opportunities in plain language
- Organic search performance and paid/organic overlap
- A glossary of marketing terms at the bottom

Historical snapshots are saved to `data/history/` so each report can compare against the previous one.

## Configuration

The `getting-started` skill generates three config files. You can also create or edit them by hand:

| File | What it controls | How it's created |
|------|-----------------|-----------------|
| `config/account.yaml` | Account ID, products, benchmarks, budget, ad copy rules | Getting-started interview or copy from `account.example.yaml` |
| `config/brand-voice.md` | Tone, writing samples, do/don't lists | Getting-started interview |
| `config/campaigns.md` | Which campaigns to manage, scope of changes | Getting-started interview |

All three are gitignored — they contain your specific business details and shouldn't be committed to a public repo.

## Two Modes

| Mode | How it works | Needs API credentials? |
|------|-------------|----------------------|
| **API** | Reads and writes directly to Google Ads, Search Console, and GBP | Yes |
| **CSV** | Parses exports from Google Ads Editor and Search Console, generates import-ready CSVs | No |

The tool tries API mode first. If credentials aren't configured, it falls back to CSV mode automatically. GBP posting also works in manual mode (drafts post text for copy/paste into the GBP dashboard).

## Project Structure

```
├── CLAUDE.md                    # Claude Code instructions
├── config/
│   ├── account.example.yaml     # Account config template (customize this)
│   └── credentials.example.yaml # API credentials template (Google Ads, GSC, GBP)
├── ads_manager/
│   ├── api/                     # Google Ads, Search Console API wrappers
│   ├── csv/                     # CSV generation and parsing (Ads Editor, GSC)
│   ├── gbp/                     # Google Business Profile client
│   ├── reports/                 # Report generation (technical + business)
│   ├── history.py               # Historical snapshots and change tracking
│   └── search_terms.py          # Search term waste/opportunity analysis
├── .claude/skills/              # Claude Code skills (8 skills)
├── reports/                     # Generated audit reports
├── data/
│   ├── imports/                 # CSVs ready for Ads Editor import
│   ├── exports/                 # CSVs exported from Ads Editor or GSC
│   └── history/                 # Audit snapshots and change log
└── scripts/
    └── audit.py                 # Standalone audit script
```

## License

MIT
