---
name: push-changes
description: >
  Push campaign changes to Google Ads via the API or generate Ads Editor CSV
  files for manual import. Use this skill when the user is ready to apply
  changes — budget adjustments, new ads, keyword modifications, bid changes,
  or negative keywords. Always confirms before pushing.
---

# Push Changes Skill

Apply campaign changes via the Google Ads API or generate CSV files for Ads Editor import.

## Critical Rules

1. **ALWAYS present the full change set and get explicit user confirmation before pushing anything.** Never auto-apply changes.
2. **Check campaign scope first.** If `config/campaigns.md` exists, read it before making any changes. Only modify campaigns listed as managed, and only make the types of changes that are checked as allowed for each campaign. If a change would touch an off-limits campaign, warn the user and ask for explicit permission.

## Workflow

### Step 0: Check Campaign Scope

```python
from pathlib import Path
scope_file = Path("config/campaigns.md")
if scope_file.exists():
    # Read and respect the management scope for each campaign
    # Only proceed with changes to campaigns listed as managed
    pass
```

### Step 1: Determine Push Method

```python
from ads_manager.api.client import is_api_available

if is_api_available():
    push_mode = "api"
    print("API credentials found — changes will be pushed directly.")
else:
    push_mode = "csv"
    print("No API credentials — generating CSV files for Ads Editor import.")
```

Ask the user which mode they prefer, even if the API is available.

### Step 2: Collect and Validate All Changes

Before pushing, compile every pending change into a summary table:

```markdown
## Pending Changes

### Budget Changes
| Campaign | Current | New | Change |
|----------|---------|-----|--------|

### Keyword Changes
| Campaign | Ad Group | Keyword | Match | Action | Details |
|----------|----------|---------|-------|--------|---------|

### New Ads
| Campaign | Ad Group | Headlines | Descriptions |
|----------|----------|-----------|--------------|

### New Negative Keywords
| Campaign | Keyword | Type |
|----------|---------|------|

### Geotargeting Changes
| Campaign | Type | Details | Intent |
|----------|------|---------|--------|
```

### Step 3: Get User Confirmation

Present the summary and ask: "Ready to push these changes?" Do NOT proceed without a clear "yes."

### Step 4: Push Changes

#### API Mode

Execute mutations in order: budgets → geotargeting → keywords → ads → negatives.

```python
from ads_manager.api.mutate import (
    update_campaign_budget, update_keyword_bid,
    update_keyword_status, create_responsive_search_ad,
)
from ads_manager.api.geotargeting import (
    apply_geotargeting_from_config,
    set_location_targets, set_radius_target, set_location_intent,
)
```

#### CSV Mode

Generate separate CSV files for each entity type:

```python
from ads_manager.csv.generator import (
    write_budget_csv, write_keyword_csv,
    write_negative_keyword_csv, write_rsa_csv,
)
```

Tell the user to import in this order:
1. Budget changes
2. Keyword changes
3. Negative keywords
4. New ads

Then review in Ads Editor and post.

### Step 5: Verify and Log

**API mode**: Pull fresh data to confirm changes took effect.

**CSV mode**: Remind the user of Ads Editor import steps.

Append to `reports/change_log.md` so there's a record of what was changed.

## CSV Formatting Reminders

- **Account column**: First column, value from `config/account.yaml` (ALWAYS)
- **UTF-8 encoding**, no BOM
- **No dollar signs** in numeric fields (Budget, Max CPC)
- **Match Type**: `Broad`, `Phrase`, `Exact` (capitalized, no brackets)
- **Criterion Type** for negatives: `Negative broad`, `Negative phrase`, `Negative exact`
- **Ad type** for RSAs: `Responsive search ad`
- Use Python `csv.writer` — never manually quote fields

## Rollback

If something goes wrong after pushing via API:
1. Check the change log for what was changed
2. Reverse each change
3. Document the rollback in the change log

For CSV mode, changes haven't been applied until the user posts in Ads Editor.
