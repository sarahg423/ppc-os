---
name: ad-creation
description: >
  Create and edit responsive search ad (RSA) copy for Google Ads campaigns.
  Use this skill whenever the user asks to write ads, create new ad copy,
  improve existing ads, or test new headlines/descriptions. Enforces brand
  voice rules and character limits from config/account.yaml.
---

# Ad Creation Skill

Write, edit, and validate responsive search ad copy.

## FIRST: Load Brand Rules

Before writing ANY ad copy, load two things:

1. **Brand voice guide** — Read `config/brand-voice.md` if it exists. This has tone guidelines, writing samples, do/don't lists, and product-specific language. It's the soul of the brand voice. If it doesn't exist, tell the user to run the `getting-started` skill first.

2. **Config rules** — Load the structured rules from account.yaml:

```python
from ads_manager.api.client import load_account_config

config = load_account_config()
brand = config["brand"]
ad_rules = config["ad_copy"]

brand_name = brand["name"]
short_name = brand.get("short_name", brand_name)
forbidden_names = brand.get("forbidden_names", [])
products = brand.get("products", [])
forbidden_phrases = ad_rules.get("forbidden_phrases", [])
preferred_ctas = ad_rules.get("preferred_ctas", [])
required_mentions = ad_rules.get("required_mentions", [])
```

Apply these rules to ALL copy you write. Never hardcode brand-specific rules.

## Character Limits (Google Ads universal — also in config)

| Field | Max Characters |
|-------|---------------|
| Headline 1–15 | **30** |
| Description 1–4 | **90** |
| Path 1, Path 2 | **15** |

## RSA Requirements

- Minimum 3 headlines, maximum 15
- Minimum 2 descriptions, maximum 4
- At least 1 Final URL

## Workflow

### Step 1: Understand the Campaign Context

Before writing copy, determine:
- Which **product** is being advertised? (check `config.brand.products`)
- What **audience** is the campaign targeting?
- What **pain point** are we addressing?
- What **ad group** will this ad live in?

### Step 2: Write Headlines

Write headlines that:
1. Lead with the pain point the audience faces
2. Name the specific product or technology
3. State the value proposition concisely
4. Include CTAs from the `preferred_ctas` list in config
5. Include any `required_mentions` from config where space allows

**Always count characters.** If a headline exceeds 30, rewrite shorter. Don't truncate.

### Step 3: Write Descriptions

Write descriptions that:
1. Complete a thought in under 90 characters — draft SHORT first, then expand
2. Include a CTA from the config's preferred list
3. Include `required_mentions` from config if room allows
4. Be specific about what the user gets

### Step 4: Validate Copy

Check every piece of copy against the brand rules from config:

```python
# Check forbidden phrases
for phrase in forbidden_phrases:
    for headline in headlines:
        if phrase.lower() in headline.lower():
            print(f"VIOLATION: '{headline}' contains forbidden phrase '{phrase}'")

# Check forbidden brand names
for name in forbidden_names:
    for headline in headlines:
        if name.lower() in headline.lower():
            print(f"VIOLATION: '{headline}' uses forbidden name '{name}'")

# Verify character limits
for i, h in enumerate(headlines):
    if len(h) > 30:
        print(f"OVER LIMIT: Headline {i+1} is {len(h)} chars: '{h}'")
```

### Step 5: Generate CSV or Push via API

**To create a CSV for Ads Editor review:**

```python
from ads_manager.csv.generator import write_rsa_csv

rows = [{
    "Campaign": "Your Campaign Name",
    "Ad Group": "Your Ad Group",
    "Headline 1": "...",
    "Headline 2": "...",
    "Headline 3": "...",
    "Description 1": "...",
    "Description 2": "...",
    "Final URL": "https://yoursite.com/landing-page",
    "Path 1": "path1",
    "Path 2": "path2",
}]

csv_path = write_rsa_csv(rows, filename="new_rsa_ads.csv")
```

**To push directly via API (ad starts PAUSED for review):**

```python
from ads_manager.api.mutate import create_responsive_search_ad

result = create_responsive_search_ad(
    ad_group_id=123456789,
    headlines=["Headline 1", "Headline 2", "Headline 3"],
    descriptions=["Description 1", "Description 2"],
    final_url="https://yoursite.com/landing-page",
    path1="path1", path2="path2",
)
```

### Step 6: Present to User

Always show the user:
1. A formatted table of all headlines with character counts
2. A formatted table of all descriptions with character counts
3. Any brand voice violations detected
4. The campaign/ad group the ad will go into
5. Whether it will be pushed via API or CSV

## Copy Testing Tips

When the user wants to A/B test ad copy:
- Create 2-3 RSA variants per ad group
- Vary the headline approach (problem-led vs. feature-led vs. CTA-led)
- Keep descriptions relatively consistent to isolate headline impact
- Run for at least 2 weeks before drawing conclusions
- Need minimum ~100 clicks per variant for statistical significance
