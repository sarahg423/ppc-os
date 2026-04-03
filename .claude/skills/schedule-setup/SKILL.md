---
name: schedule-setup
description: "Set up automated audit schedules for ppc-os. Creates a ramp-up schedule (weekly audits for the first 30 days) followed by a maintenance schedule (bi-weekly full audits with critical-issues-only checks on off-weeks). Use when users mention 'schedule', 'automate', 'recurring audit', 'set it and forget it', or ask to run audits automatically."
---

# Schedule Setup — Automated Audit Cadence

You are setting up recurring campaign audits for ppc-os. This skill creates scheduled tasks that run automatically, following a two-phase approach: an intensive ramp-up period, then a lighter maintenance cadence.

## Prerequisites

Before scheduling anything, confirm:

1. **Config exists** — `config/account.yaml` must be present. If not, tell the user to run the getting-started skill first.
2. **At least one audit has been run** — Check for any files in `reports/`. If empty, recommend running one manual audit first so the user knows what to expect.

## The Two-Phase Schedule

### Phase 1: Ramp-Up (First 30 Days)

New accounts need close attention. Budgets may be off, keywords may be wasteful, ad copy may underperform. Weekly audits catch problems fast.

- **Frequency:** Every Monday at 9:00 AM (local time)
- **Duration:** 30 days from today
- **Task:** Full audit — pull performance, compare to benchmarks, generate report, recommend changes
- **Task name:** `ppc-os-weekly-audit`

### Phase 2: Maintenance (After 30 Days)

Once the account stabilizes, shift to a lighter cadence:

- **Full audit** every other Monday at 9:00 AM (local time)
  - Same as ramp-up: pull performance, benchmark comparison, full report
  - **Task name:** `ppc-os-biweekly-audit`

- **Critical-issues check** on off-weeks, same day and time
  - Quick scan for: budget pacing problems, campaigns that stopped serving, cost/conversion spikes above 2× benchmark, Quality Score drops below minimum threshold
  - Only generates a report if something is wrong
  - **Task name:** `ppc-os-critical-check`

## Interview Flow

Walk the user through these questions before creating tasks. Use sensible defaults and keep it quick.

### 1. Confirm the schedule pattern

> I'll set up a two-phase audit schedule:
>
> **First 30 days (ramp-up):** Full audit every Monday at 9:00 AM
> **After that (maintenance):** Full audit every other Monday, with a quick critical-issues check on off-weeks
>
> Does that cadence work, or would you like to adjust the day, time, or frequency?

If the user wants changes, adapt. Common adjustments:
- Different day of week (e.g., Friday instead of Monday)
- Different time
- Different ramp-up length (e.g., 60 days instead of 30)
- Skip the ramp-up entirely and go straight to maintenance

### 2. Confirm the audit scope

> Your audits will cover all campaigns listed in `config/campaigns.md`. Should the scheduled audits also attempt to push recommended changes automatically, or just generate reports for your review?

Two modes:
- **Report only** (default, safer) — Generates report and recommendations. User reviews and pushes manually.
- **Auto-apply safe changes** — Automatically pauses keywords with zero conversions and excessive spend, adjusts budgets within ±15% of current. Still generates report. Flags anything bigger for manual review.

### 3. Create the scheduled tasks

Use the `create_scheduled_task` tool to create each task. Build the prompt for each task so it is fully self-contained — future runs will NOT have access to this conversation.

#### Ramp-Up Task Prompt

```
You are running a weekly ppc-os campaign audit. Follow these steps:

1. Read config/account.yaml to load account settings and benchmarks.
2. Read config/campaigns.md to determine which campaigns are in scope.
3. Read config/brand-voice.md for context on the account.
4. Pull performance data for the last 7 days using the get-performance skill approach:
   - Try API mode first (ads_manager/api/performance.py functions).
   - If API unavailable, check data/exports/ for recent CSV exports and parse them.
5. Compare all metrics against benchmarks defined in config/account.yaml.
6. Generate a full audit report and save it to reports/audit_YYYY-MM-DD.md.
7. Summarize the top 3 findings and any recommended changes.
{AUTO_APPLY_BLOCK}
This is a ramp-up audit (first 30 days). Pay extra attention to:
- Keywords with high spend but zero conversions
- Ad groups with CTR below benchmark floor
- Budget pacing (are campaigns hitting daily caps too early?)
- Quality Score issues on high-volume keywords
```

#### Maintenance Full-Audit Task Prompt

Same as ramp-up but without the "pay extra attention" block — by this point the account should be stable. Replace with:

```
This is a maintenance audit. Focus on:
- Week-over-week trends (is performance improving or declining?)
- Seasonal or competitive shifts
- New keyword opportunities based on search term reports
- Ad copy fatigue (same ads running too long without refresh)
```

#### Critical-Issues Check Prompt

```
You are running a quick critical-issues check for ppc-os. This is NOT a full audit — only flag urgent problems.

1. Read config/account.yaml to load account settings and benchmarks.
2. Read config/campaigns.md to determine which campaigns are in scope.
3. Pull performance data for the last 7 days.
4. Check ONLY for these critical issues:
   - Any campaign that stopped serving impressions entirely
   - Budget pacing: campaigns exhausting daily budget before 2 PM
   - Cost per conversion more than 2× the benchmark ceiling
   - Quality Score dropped below the minimum threshold on any keyword with >100 impressions
   - Spend anomalies: daily spend more than 50% above or below the 30-day average

If NO critical issues are found, output a single line: "✓ No critical issues detected — [date]"

If issues ARE found, save a report to reports/critical_YYYY-MM-DD.md with specifics and recommended immediate actions.
```

### 4. Set the transition

After creating the ramp-up task, tell the user:

> Your weekly audits are scheduled. In 30 days (on [DATE]), I recommend switching to the maintenance schedule. I'll create a one-time reminder for that date so you don't forget.

Create a one-time `fireAt` task for 30 days from now:

```
Reminder: Your ppc-os ramp-up period ends today. Time to transition to the maintenance schedule.

To switch, run: claude "Switch to maintenance audit schedule"

This will:
1. Remove the weekly audit task
2. Create bi-weekly full audits
3. Create off-week critical-issues checks
```

**Task name:** `ppc-os-schedule-transition-reminder`

### 5. Handle the transition

When the user comes back to switch schedules (triggered by the reminder or whenever they're ready):

1. Delete or disable the `ppc-os-weekly-audit` ramp-up task
2. Create the `ppc-os-biweekly-audit` task (every other Monday)
3. Create the `ppc-os-critical-check` task (alternating Mondays)

For bi-weekly cron expressions:
- Use two separate weekly tasks on alternating weeks. The simplest approach: schedule both as weekly (`0 9 * * 1`) but include logic in the prompt to check the week number and decide whether to run a full audit or critical check.
- Alternatively, create a single weekly task whose prompt says: "Check the current ISO week number. If even, run a full audit. If odd, run a critical-issues check only."

The single-task approach is cleaner. Use it by default:

**Task name:** `ppc-os-maintenance-audit`
**Cron:** `0 9 * * 1` (every Monday at 9 AM)
**Prompt:**
```
You are running a scheduled ppc-os maintenance check. Determine which type of check to run:

1. Get today's ISO week number.
2. If the week number is EVEN, run a FULL AUDIT (see full audit steps below).
3. If the week number is ODD, run a CRITICAL-ISSUES CHECK ONLY (see critical check steps below).

## Full Audit Steps
[Include the full maintenance audit prompt from above]

## Critical-Issues Check Steps
[Include the critical-issues check prompt from above]
```

## Auto-Apply Block

If the user opted into auto-apply, insert this into the audit prompts:

```
After generating recommendations, automatically apply these SAFE changes:
- Pause keywords with zero conversions and more than $100 in spend (last 30 days)
- Adjust campaign budgets by up to ±15% if pacing analysis supports it
- Add obvious negative keywords (irrelevant search terms with >5 clicks and 0 conversions)

For all other recommendations (new ad copy, bid strategy changes, adding keywords, budget changes >15%), include them in the report for manual review. Do NOT auto-apply these.

Log all auto-applied changes to reports/change_log.md with timestamps.
```

If report-only mode, insert:
```
Do NOT make any changes automatically. Present all recommendations in the report for manual review.
```

## Recap

After everything is created, give the user a clean summary:

> **Schedule created!** Here's what's set up:
>
> **Now through [DATE]:** Full audit every [DAY] at [TIME]
> **After [DATE]:** Full audit every other [DAY], critical-issues check on off-weeks
> **Mode:** [Report only / Auto-apply safe changes]
>
> You'll get a reminder on [DATE] to make the switch. Or just say "Switch to maintenance audit schedule" whenever you're ready.
