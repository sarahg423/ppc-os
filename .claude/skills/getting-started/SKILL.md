---
name: getting-started
description: >
  Onboarding interview that configures this Google Ads manager for a new user.
  Use this skill whenever someone says "get started", "set up", "configure",
  "onboard", "I'm new", or any time config/account.yaml doesn't exist yet.
  Also trigger when the user says "reconfigure", "update my settings", or
  "change my brand voice." This skill MUST run before any other skill can
  work properly — it generates the config files everything else depends on.
---

# Getting Started

This skill walks a new user through an interview about their business, ad strategy, and brand voice, then generates three config files that power every other skill in this repo:

1. **`config/account.yaml`** — Account ID, brand rules, benchmarks, ad copy guidelines
2. **`config/brand-voice.md`** — Tone guidelines, writing samples, do/don't examples
3. **`config/campaigns.md`** — Which campaigns this tool manages and what it's allowed to change

If any of these files already exist, offer to update them rather than starting from scratch. Read the existing files first and pre-fill answers so the user only has to confirm or change what's different.

## The Interview

Work through these seven sections in order. Be conversational — this isn't a form, it's a strategy discussion. Ask follow-up questions when answers are vague. If the user doesn't know something (like benchmark numbers), suggest reasonable defaults and explain why.

Between sections, briefly summarize what you've captured so far so the user can correct misunderstandings early.

---

### Section 1: Your Business

Goal: Understand what you're advertising and how to talk about it.

Ask about:
- **Company name** — the full name AND the short version for tight headlines
- **Names to never use** — old brand names, common misspellings, abbreviations that are wrong (e.g., "ScoutAPM" when the brand is "Scout Monitoring")
- **Product lines** — what do you sell? List each product with a one-line description. This matters because ad copy should reference the specific product being advertised, not generic umbrella language.
- **Website URL** — base domain and key landing pages per product
- **What makes you different** — in one or two sentences, why should someone pick you over the alternatives? This becomes the core value prop for ad copy.

---

### Section 2: Your Ad Account

Goal: Connect to the right Google Ads account and understand what already exists.

Ask about:
- **Google Ads customer ID** — the XXX-XXX-XXXX number from the top of Google Ads
- **Are campaigns already running?** Three paths:
  - **"Yes, manage everything"** — the tool will pull all active campaigns and manage the full account
  - **"Yes, but only some"** — ask which campaigns or campaign name patterns to include. Everything else is hands-off.
  - **"No, starting fresh"** — the tool will help build campaigns from scratch

If campaigns already exist, try to pull them via the API or ask the user to export from Ads Editor:
```python
from ads_manager.api.client import is_api_available
if is_api_available():
    from ads_manager.api.performance import get_campaign_performance
    campaigns = get_campaign_performance(days=30)
    # Show the user what's there and let them pick
```

If the API isn't set up yet, ask the user to list their campaign names manually or paste an export.

For each managed campaign, note:
- Campaign name
- What product/service it advertises
- Current daily budget
- What the tool is allowed to change (ad copy, bids, budgets, keywords, all of the above)

---

### Section 3: Who You're Selling To

Goal: Build an ICP profile that shapes ad copy tone and keyword strategy.

Ask about:
- **Who is the buyer?** — Job title, day-to-day role. Are they the decision-maker or do they need to convince someone else? (e.g., "hands-on developer debugging at 2am" vs. "VP Engineering evaluating tools for the team" vs. "small business owner wearing every hat")
- **What pain are they feeling?** — What problem drives them to search? Be specific. "My Rails app is slow" is better than "needs monitoring."
- **How technical are they?** — This drives tone: jargon-friendly vs. plain-language
- **Where are they in the buying journey?** — Searching for your product category? Comparing specific tools? Don't know the category exists yet?
- **Who are your competitors?** — Name them. This informs negative keywords, comparison campaigns, and positioning. Ask if they want to run competitor campaigns.

---

### Section 4: Tone & Voice

Goal: Capture how the brand sounds so ad copy feels authentic.

Ask about:
- **How would you describe your voice in 3 words?** — (e.g., "direct, technical, friendly" or "warm, professional, approachable")
- **Words and phrases to NEVER use** — these become `forbidden_phrases` in config. Probe for:
  - Enterprise buzzwords they hate ("solutions", "leverage", "synergy")
  - Competitor names they don't want in their ads
  - Misleading claims ("free trial" when it's actually a free tier)
  - Anything that doesn't match their brand
- **Words and phrases that feel right** — CTAs they like, phrases they use on their website
- **Writing samples** — Ask for 2-3 examples of copy they love. Could be:
  - Existing ad headlines/descriptions that performed well
  - Landing page copy they're proud of
  - Email subject lines, tweets, taglines
  - Even competitor copy they admire (and want to riff on)

Tell the user: "These samples help me understand your voice so I can write ad copy that sounds like you, not like a generic ad generator. Paste anything that feels representative — even a few sentences from your homepage works."

Store the samples and analysis in `config/brand-voice.md`.

---

### Section 5: Offer & Pricing

Goal: Understand the signup flow so CTAs and descriptions are accurate.

Ask about:
- **Pricing model** — Free tier? Free trial? How long? Freemium? Enterprise-only?
- **Signup friction** — Credit card required? Demo required? Self-serve signup? This determines which CTAs are honest (don't say "Start free — no credit card" if a credit card IS required)
- **What should the CTA be?** — Based on their model, suggest options and let them pick:
  - Self-serve free tier: "Start free", "Try it free", "Get started"
  - Free trial: "Start your free trial", "Try free for X days"
  - Demo-required: "See a demo", "Book a walkthrough"
  - No free option: "See pricing", "Learn more"
- **Key landing pages** — Where should ads send people? Product pages, pricing page, signup page? Different landing pages per product?

---

### Section 6: Budget & Goals

Goal: Set the financial frame for all budget recommendations.

Ask about:
- **Total monthly ad budget** — or daily if they think in daily terms. If they say monthly, convert: monthly / 30.4 = daily. Note: Google can spend up to 2x daily on any given day but averages to daily over the month.
- **Primary objective** — What does success look like?
  - Signups/conversions (most common)
  - Brand awareness / traffic
  - Specific ROAS target
  - Lead generation (demos, form fills)
- **Target CPA** — What's the most they'd pay per conversion? If they don't know, help them calculate: "If your product costs $X/month and the average customer stays Y months, your LTV is $Z. Spending up to Z * 20-30% to acquire a customer is a common starting point."
- **Are there campaigns that should get more budget?** — Top performers to scale, or new products to push?
- **Budget guardrails** — Any hard limits? ("Never spend more than $X/day on any single campaign")

---

### Section 7: Location Targeting

Goal: Determine whether ads need geotargeting and capture the details.

Ask about:
- **Should your ads be location-targeted?** If you're a brick-and-mortar business, local service, or only serve a specific region, the answer is almost certainly yes. For online-only businesses serving a whole country, it might be no.
- **If yes, what area?** Two options:
  - **Radius targeting**: Pick a center point (your business address or city center) and a radius in miles. Best for single-location businesses.
  - **Named locations**: Target specific cities, states, or DMAs. Best for multi-location or regional businesses.
- **How big is your radius?** For most local businesses, 25-50 miles is a good start. Restaurants and bars might want 10-15 miles. A destination venue might want 50-100 miles.
- **Location intent**: Default to **"People in or regularly in your targeted locations"** (PRESENCE). This means only people physically in the area see your ads. The alternative — "people interested in" — would show ads to someone in NYC googling "things to do in Bristol" which wastes budget for local businesses.

Store in `config/account.yaml` under a `geotargeting` key:

```yaml
geotargeting:
  enabled: true
  intent: "PRESENCE"  # or "PRESENCE_OR_INTEREST"
  radius:
    label: "Bristol, TN"
    lat: 36.5951
    lng: -82.1887
    miles: 50
  locations: []  # Alternative: named locations like ["Bristol, Tennessee"]
```

For businesses that don't need geotargeting:

```yaml
geotargeting:
  enabled: false
```

Tell the user: "Geotargeting is applied via the Google Ads API. If you don't have API credentials set up yet, we'll save the config and apply it when credentials are available. You can also set this manually in the Google Ads UI."

---

### Section 8: Benchmarks & Guardrails

Goal: Set the thresholds the audit system uses to flag problems.

For each metric, suggest a default based on what you've learned about their business and let them adjust:

| Metric | Suggested Default | Why |
|--------|-------------------|-----|
| CTR floor | 3% | Below this, ads aren't resonating |
| CPC ceiling | Based on their budget & target CPA | Keeps individual clicks affordable |
| Conv. rate floor | 2% | Below this, landing pages need work |
| Quality Score floor | 6 | Below this, Google is penalizing relevance |
| Impression Share floor | 60% | Below this, they're missing too much traffic |
| Cost/Conv. ceiling | Their stated target CPA | The whole point |

Explain that these drive the weekly audit reports: "Anything outside these ranges gets flagged with a specific recommendation. You can adjust them anytime by editing `config/account.yaml`."

---

## After the Interview

### Generate config/account.yaml

Build the full config from the interview answers. Use `config/account.example.yaml` as the template structure. Read it first:

```python
import yaml
from pathlib import Path

example = Path("config/account.example.yaml")
with open(example) as f:
    template = yaml.safe_load(f)
```

Fill in every field from the interview. Write to `config/account.yaml`.

### Generate config/brand-voice.md

Create a Markdown reference document that the `ad-creation` skill reads before writing any copy. Structure it like this:

```markdown
# Brand Voice Guide — [Company Name]

## Voice in Three Words
[Their three words]

## Who We're Talking To
[ICP description — their role, their pain, their technical level]

## How We Sound
[2-3 paragraphs synthesizing their voice. Draw on the writing samples
to describe the patterns: sentence length, technical depth, humor level,
formality. Be specific — "we use sentence fragments for emphasis" is
better than "we're casual."]

## Writing Samples
[Paste their samples here with brief annotations about what makes each
one representative of the brand voice]

## Do This
- [Specific patterns from their samples and preferences]
- [e.g., "Lead with the technical problem, not the product category"]
- [e.g., "Use sentence fragments for punch: 'Traces to the line of code.'"]

## Don't Do This
- [Every forbidden phrase, with brief explanation of why]
- [e.g., "Never say 'free trial' — we have a free tier, not a trial"]
- [e.g., "Avoid 'enterprise-grade' — our buyer is a developer, not a CTO"]

## CTAs That Work
[Their preferred CTAs with context on when to use each]

## Product-Specific Language
[For each product line, brief notes on how to talk about it:
what it does, what pain it solves, what language resonates]
```

### Generate config/campaigns.md

Create a Markdown file that documents which campaigns this tool manages and what it's allowed to do. This is the "scope" file — other skills check it before making changes.

```markdown
# Managed Campaigns

## Scope
[One of: "All active campaigns", "Selected campaigns only", "No existing campaigns — building from scratch"]

## Campaigns

### [Campaign Name]
- **Product**: [What this campaign advertises]
- **Daily Budget**: $[amount]
- **Management scope**: [What the tool can change]
  - [ ] Ad copy (headlines, descriptions)
  - [ ] Keyword bids
  - [ ] Campaign budget
  - [ ] Add/pause keywords
  - [ ] Add negative keywords
  - [ ] Create new ad groups
- **Notes**: [Any special instructions for this campaign]

### [Next Campaign...]
[Repeat for each managed campaign]

## Off-Limits
[Campaigns or areas the tool should NOT touch]

## New Campaign Ideas
[If discussed during onboarding, capture ideas for new campaigns
to build later — products without campaigns, competitor campaigns,
new keyword themes, etc.]
```

### Present the Results

After generating all three files, show the user a summary:

1. Quick recap of their brand voice and ICP
2. The benchmark thresholds that will drive audits
3. Which campaigns are being managed and what the tool can change
4. What to do next: "Run `claude 'audit my campaigns'` to get your first performance report, or `claude 'write new ads for [campaign]'` to create ad copy."

Read back the key config values so they can catch any mistakes before the first audit runs.

### If reconfiguring

When updating existing config rather than creating from scratch:
1. Read all three existing files first
2. Show the user what's currently configured
3. Ask what they want to change
4. Only modify the relevant sections — don't regenerate everything
