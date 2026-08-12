---
name: Ads Editor CSV requires real campaign names
description: Never use "All campaigns" or other placeholder values in the Campaign column of an Ads Editor import CSV — it must be the literal campaign name
---

In Ads Editor import CSVs, the Campaign column must contain the **exact, literal campaign name** for every row. Placeholders like "All campaigns" cause Ads Editor to silently skip those rows on import.

**Why:** Found this when an attempted import of 200+ negative keywords for Scout only imported the 44 rows that had real campaign names — all "All campaigns" rows failed silently.

**How to apply:**
- For shared/universal negatives that should apply to multiple campaigns, generate one row per campaign with the negative repeated
- Or use a Negative Keyword List in the Google Ads UI (Tools → Shared Library) and apply it to multiple campaigns — that's a separate workflow from CSV import
- Same rule likely applies to other shared resources (audience targets, location targets, etc.)
- Always validate generated CSVs include real campaign names before sending to user
