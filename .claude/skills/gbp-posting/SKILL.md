---
name: gbp-posting
description: >
  Create and manage Google Business Profile posts. Use this skill when the user
  wants to post updates, events, or promotions to their Google Business Profile.
  Also use when they ask about GBP, local search presence, or promoting events.
  Handles both manual post creation and automated event posting from their website.
---

# GBP Posting Skill

Create, list, and manage Google Business Profile posts to improve local search visibility.

## Why GBP Posts Matter

For local businesses, an active Google Business Profile is one of the most effective free marketing tools. Posts show up in Google Maps and local search results, telling potential customers what's happening now. A business with recent posts looks active and trustworthy. One with no posts looks like it might be closed.

## How It Works

### Check Availability

```python
from ads_manager.gbp.client import is_gbp_available

if is_gbp_available():
    mode = "api"
else:
    mode = "manual"
    # Tell the user: GBP API credentials aren't set up yet.
    # They can still draft posts — you'll write the text and they copy/paste
    # it into the GBP dashboard at business.google.com.
```

If GBP is not configured, **still help the user**. Draft post text they can copy into the GBP web interface. Don't gate the entire skill behind API access.

### Post Types

#### 1. Event Posts

For time-bound events (shows, sales, classes, grand openings):

```python
from ads_manager.gbp.show_poster import create_event_gbp_post

result = create_event_gbp_post(
    name="Event Name",
    date={"year": 2026, "month": 8, "day": 15},
    start_time={"hours": 19, "minutes": 0},
    end_time={"hours": 22, "minutes": 0},
    price="$25",
    description="Brief event description",
    url="https://example.com/tickets",
    photo_url=None,  # Optional
    summary_override=None,  # Optional — if set, uses this text instead of auto-generating
)
```

#### 2. Update Posts

For announcements, news, seasonal content, or promotions:

```python
from ads_manager.gbp.client import create_update_post

result = create_update_post(
    summary="Your post text here (max 1500 chars)",
    cta_url="https://example.com",  # Optional
    cta_action="LEARN_MORE",  # BOOK, ORDER, SHOP, LEARN_MORE, SIGN_UP, CALL
    photo_url=None,  # Optional
)
```

#### 3. Automated Event Posting

For businesses with events listed on their website, scrape and auto-post:

```python
from ads_manager.gbp.show_poster import scrape_upcoming_events, post_upcoming_events

# Preview what would be posted
events = scrape_upcoming_events()
for event in events:
    print(f"{event['name']} — {event['date_text']}")

# Dry run (shows what would happen without posting)
post_upcoming_events(days_ahead=7, dry_run=True)

# Actually post
post_upcoming_events(days_ahead=7, dry_run=False)
```

**Important**: The scraper returns raw date text from the website. You (Claude) must parse the date into structured format before calling `create_event_gbp_post`. Use your judgment based on the text format.

### Listing and Managing Posts

```python
from ads_manager.gbp.client import list_posts, delete_post

# See recent posts
posts = list_posts(page_size=10)
for post in posts:
    print(f"{post.get('topicType')}: {post.get('summary', '')[:80]}")

# Delete a post by its resource name
delete_post(post["name"])
```

## Writing Post Copy

**Always read `config/brand-voice.md` before writing any post text.** The post should sound like the business, not like a generic marketing template.

Guidelines:
- **Max 1500 characters** for post text (Google's limit)
- **First 100 characters matter most** — that's what shows in the preview
- **Include a CTA** — tell people what to do next (get tickets, visit the site, call)
- **Be specific** — "This Saturday at 8pm" beats "coming soon"
- **Use the configured brand name** from `config/account.yaml`, never hardcode it

### Post Ideas by Business Type

When the user asks "what should I post?", suggest based on their business:

- **Events-based business**: Upcoming events, performer spotlights, behind-the-scenes, last night's highlights
- **Retail**: New arrivals, seasonal specials, customer favorites, holiday hours
- **Services**: Tips related to your service, before/after showcases, team spotlights, seasonal reminders
- **Restaurant/bar**: Daily specials, new menu items, events, happy hour reminders

### Posting Frequency

Recommend posting **1-2 times per week** minimum. GBP posts expire after 7 days (events last until the event date), so consistency matters. A good cadence:

- **Monday**: Announce the week's events or specials
- **Thursday/Friday**: Reminder for the weekend, last-minute push

## Workflow

### When the user says "post to GBP" or "promote [event]":

1. Read `config/brand-voice.md` and `config/account.yaml`
2. Draft the post text using the brand's voice
3. Present the draft to the user for approval
4. If API is available, post via the API
5. If API is unavailable, format the text for copy/paste into the GBP dashboard

### When the user says "auto-post upcoming events":

1. Scrape the website for upcoming events
2. Show the user what was found
3. Let them pick which events to post (or post all)
4. Parse dates from text into structured format
5. Create event posts (or dry run first)

### When the user says "what's on my GBP?":

1. Call `list_posts()` to see current posts
2. Summarize in plain English: "You have 3 active posts. The most recent is from 2 days ago about [topic]. Your oldest post expires tomorrow."
3. Suggest what to post next based on gaps

## Manual Mode (No API)

If `is_gbp_available()` returns False, operate in manual mode:

1. Draft the post text as normal
2. Format it clearly for the user to copy
3. Give them step-by-step instructions:
   - Go to business.google.com
   - Click "Add update" or "Add event"
   - Paste the text
   - Add a photo if available
   - Click "Publish"
4. Remind them to set up API credentials if they want automated posting
