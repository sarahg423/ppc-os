# ppc-os

An open-source operating system for your PPC campaigns, powered by [Claude Code](https://claude.com/claude-code). Pull performance data, audit campaigns against your benchmarks, write ad copy with your brand voice, and push changes — all from the command line.

Works with any Google Ads account. All account-specific configuration (brand name, voice rules, benchmarks) lives in a single YAML file you customize for your business.

## What It Does

- **Pulls performance data** from Google Ads (API or CSV export from Ads Editor)
- **Audits campaigns** against configurable benchmarks
- **Suggests edits** to ad copy, budgets, bids, and keywords
- **Generates Markdown reports** with findings and recommendations
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

- `config/account.yaml` — Account ID, products, benchmarks, ad copy rules
- `config/brand-voice.md` — Tone guidelines, writing samples, do/don't lists
- `config/campaigns.md` — Which campaigns to manage and what's allowed to change

You choose whether to manage all your campaigns, a subset, or start building new ones from scratch.

### 3. Configure credentials (optional, for API mode)

```bash
cp config/credentials.example.yaml config/credentials.yaml
# Edit with your Google Ads API credentials
```

If you skip this step, the tool works in **CSV mode** — you export data from the Google Ads Editor desktop app, place CSVs in `data/exports/`, and the tool generates import-ready CSVs in `data/imports/`.

### 4. Run with Claude Code

```bash
# Full weekly audit
claude "Run a full campaign audit for the last 7 days"

# Check specific campaign performance
claude "How is the Brand Search campaign performing this month?"

# Write new ad copy
claude "Write 3 new RSA variants for the Product Launch campaign"

# Adjust budgets
claude "The Brand campaign is budget-constrained — recommend a new budget"

# Push changes
claude "Push the budget and keyword changes we discussed"

# Set up automated audits
claude "Set up a recurring audit schedule"
```

### 5. Run the audit script directly

```bash
# Via API
python scripts/audit.py --days 7

# Via CSV export
python scripts/audit.py --csv data/exports/campaign_report.csv
```

## Claude Code Skills

This repo includes four skills that Claude Code picks up automatically:

| Skill | Purpose |
|-------|---------|
| `getting-started` | Onboarding interview — configures everything for your account |
| `get-performance` | Pull metrics from API or parse CSV exports |
| `ad-creation` | Write RSA ad copy enforcing your brand voice |
| `budget-management` | Adjust budgets, bids, and analyze pacing |
| `push-changes` | Apply changes via API or generate Ads Editor CSVs |
| `schedule-setup` | Set up automated recurring audits (ramp-up → maintenance) |

## Configuration

The `getting-started` skill generates three config files. You can also create or edit them by hand:

| File | What it controls | How it's created |
|------|-----------------|-----------------|
| `config/account.yaml` | Account ID, products, benchmarks, ad copy rules | Getting-started interview or copy from `account.example.yaml` |
| `config/brand-voice.md` | Tone, writing samples, do/don't lists | Getting-started interview |
| `config/campaigns.md` | Which campaigns to manage, scope of changes | Getting-started interview |

All three are gitignored — they contain your specific business details and shouldn't be committed to a public repo. Fork the repo for your own use and keep these files locally, or add them to a private repo.

## Two Modes

| Mode | How it works | Needs API credentials? |
|------|-------------|----------------------|
| **API** | Reads and writes directly to Google Ads | Yes |
| **CSV** | Parses Ads Editor exports, generates import-ready CSVs | No |

The tool tries API mode first. If credentials aren't configured, it falls back to CSV mode automatically.

## Project Structure

```
├── CLAUDE.md                    # Claude Code instructions
├── config/
│   ├── account.example.yaml     # Account config template (customize this)
│   └── credentials.example.yaml # API credentials template
├── ads_manager/
│   ├── api/                     # Google Ads API wrappers
│   ├── csv/                     # Ads Editor CSV tools
│   └── reports/                 # Markdown report generation
├── .claude/skills/              # Claude Code skills
├── reports/                     # Generated audit reports
├── data/                        # CSV import/export staging
└── scripts/                     # Standalone audit script
```

## License

MIT
