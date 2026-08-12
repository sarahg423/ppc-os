---
name: Scout content publishing rules
description: Rules for blog post attribution, dates, language-specific CTAs, and author selection for Scout APM content
type: feedback
---

When creating or updating Scout APM blog posts:

1. **Updated posts must show both dates.** Add a line at the beginning: "*Originally published [original date]. Updated [update date].*"

2. **Language-specific CTAs.** Footer CTAs must match the post's language:
   - Rails/Ruby posts: link to `/rails-apm` and `/ruby-monitoring-tools`
   - Django/Python posts: link to `/python-monitoring` (or equivalent when it exists)
   - Elixir posts: link to `/elixir-phoenix-monitoring` (or equivalent)
   - Framework-agnostic posts: don't mention any specific language in the CTA, just link to the homepage or generic signup

3. **Author must be specified by Sarah.** Never assume an author. Ask who should be listed. Don't default to "scout-apm" or "sarah-morgan" without asking.

4. **Tagline at the bottom:** "For application monitoring with errors, logs, and traces, Scout Monitoring provides the fastest insights without the bloat."

**Why:** Sarah flagged these during the N+1 content series review. Django posts were linking to /rails-apm, new posts didn't have author attribution, and updated posts didn't show both dates.

**How to apply:** Check every blog post before committing. Verify the footer CTA matches the post language, the author is set correctly, and updated posts show both dates.
