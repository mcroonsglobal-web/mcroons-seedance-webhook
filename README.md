# MCROONS Seedance Webhook

Production webhook endpoint for Seedance API generation events (images/videos) deployed on Vercel.

## Events Handled
- `image.generation.complete` → Posts to Meta (Instagram) + Updates Shopify product
- `image.generation.failed` → Logs error
- `video.generation.complete` → Posts to Meta (Instagram)
- `video.generation.failed` → Logs error

## Deployment

Deployed to: `https://mcroons-seedance-webhook.vercel.app/api/seedance`

### Prerequisites
- GitHub repository: `mcroonsglobal-web/mcroons-seedance-webhook`
- Vercel project linked to GitHub
- Environment variables configured in Vercel dashboard

### Environment Variables (set in Vercel)
```
SEEDANCE_WEBHOOK_SECRET = [from Seedance API settings]
META_ACCESS_TOKEN = [from Meta Business Platform]
SHOPIFY_ACCESS_TOKEN = [from Shopify Admin]
SHOPIFY_STORE_DOMAIN = [your-store.myshopify.com]
```

### Register Webhook with Seedance API
```bash
curl -X POST https://api.seedance.ai/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://mcroons-seedance-webhook.vercel.app/api/seedance",
    "events": ["image.generation.complete", "image.generation.failed", "video.generation.complete", "video.generation.failed"]
  }'
```

## Testing
```bash
# Health check
curl https://mcroons-seedance-webhook.vercel.app/api/seedance

# Test webhook (requires valid signature)
curl -X POST https://mcroons-seedance-webhook.vercel.app/api/seedance \
  -H "Content-Type: application/json" \
  -H "X-Seedance-Signature: $(echo -n '{"event_type":"image.generation.complete"}' | openssl dgst -sha256 -hmac 'YOUR_SECRET')" \
  -d '{"event_type":"image.generation.complete","generation_id":"test123"}'
```

## Architecture
- **Runtime:** Python 3.9 (Vercel serverless)
- **Framework:** Native HTTP handler (no Flask/async needed for Vercel)
- **Logging:** CloudWatch via Vercel logs
- **Timeout:** 30 seconds (standard Vercel limit)

## Related
- TikTok OAuth catcher: `mcroons-oauth-catcher.vercel.app` (similar deployment)
- Infrastructure: Vercel team `mcroonsglobal-2791`

## Claude Code Skills

This repo has [`sergebulaev/linkedin-skills`](https://github.com/sergebulaev/linkedin-skills) installed as project-scoped Claude Code skills under `.claude/`, for drafting and scheduling LinkedIn posts to accompany generated Seedance content.

- **Location:** `.claude/skills/` (11 skills: post writer, comment drafter, reply handler, humanizer, hook extractor, content planner, engagement monitor, profile optimizer, employee advocacy, repurposer, thread monitor), with shared code in `.claude/lib/` and docs in `.claude/references/`.
- **Setup (optional):** copy `.claude/.env.example` to `.claude/.env` and fill in `PUBLORA_API_KEY` (auto-publish), `APIFY_TOKEN` (read LinkedIn posts/comments), and/or `PIXFARO_TOKEN` (illustrations). Skills work in draft-only mode with no keys set. Then `pip install -r .claude/requirements.txt`.
- **License:** MIT, see `.claude/LICENSE`.

**Try it:** ask Claude things like "write a LinkedIn post about \[this Seedance drop], I'm a founder" or "audit and humanize this draft: \[paste]". The right skill activates automatically.

**Suggested weekly workflow:**
1. **Monday — plan:** ask `linkedin-content-planner` for 7 days of topics tied to what's shipping.
2. **Per post — draft:** give `linkedin-post-writer` one audience, one idea, and one proof point.
3. **Before publishing — audit + humanize:** run the draft through `linkedin-humanizer --mode audit`, then the rewrite pass. Read it aloud before approving.
4. **After publishing — engage:** `linkedin-comment-drafter` for comments on relevant posts, `linkedin-reply-handler` for replies under your own.
5. **End of week — review:** check which hooks drove comments/DMs from the right people, not just impressions.

Every skill drafts and waits for approval before publishing anything.
