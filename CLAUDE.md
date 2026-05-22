# Project: Telegram AI Agent

Personal Telegram agent that monitors subscribed channels, rewrites posts via AI, and publishes them to Saved Messages.

## Architecture

Three independent agents:
- **content_agent.py** — manual run, fetches latest posts per channel, rewrites singles, merges similar into mini-digests
- **digest_agent.py** — runs every 6h via cron, collects posts from last 24h, writes full articles for groups of 3+
- **insights_agent.py** — CLI tool, reads historical posts from a channel/topic (newest→oldest in batches), filters valuable insights via AI, publishes to a private group

Shared helpers:
- **ai_providers.py** — AIProviderChain (failover) + AdaptiveDelay
- **config.py** — loads .env variables
- **session.py** — one-time local auth to generate SESSION_BASE64

## AI Providers

Order is fixed: **Mistral → Gemini → Cerebras**. Do NOT change this order without an explicit reason from the user.

- On 429 rate limit: AdaptiveDelay doubles the wait, provider raises exception so failover triggers
- On success: delay shrinks by 15% toward a new baseline
- Providers must `raise` in their except blocks — never return an error string

## Telegram

- Uses Telethon 1.43.2 (user account, not a bot)
- API credentials: Telegram Desktop public keys (API_ID=2040)
- Session stored as SESSION_BASE64 secret in GitHub Actions
- Publishes everything to **Saved Messages** ("me")

## Deduplication

Two layers:
1. `processed_ids.json` — skips already-processed message IDs (per channel, keeps last 100)
2. `all_seen_posts.json` — cross-channel sentence-hash dedup (keeps last 300 per channel)

Threshold logic (both agents):
- **2+ of 3 sentence hashes match** → exact duplicate, skip entirely
- **1 of 3 sentence hashes match** → partial match (`partial=True`), include in AI grouping only, do not publish alone
- **0 matches** → new post, publish normally

## Output format

Each published item is **two messages**:
1. Rewritten/digest post (clean text, no emoji, no hashtags, no t.me links, external links kept)
2. Original post(s) for reference

## GitHub Actions

- `.github/workflows/telegram-bot.yml` — `workflow_dispatch` only, runs content_agent.py
- `.github/workflows/digest.yml` — `schedule: cron '0 */6 * * *'` + `workflow_dispatch`, runs digest_agent.py
- Both workflows: `permissions: contents: write`, restore session from SECRET, save tracking JSONs back to repo after run
- Branch: `claude/telethon-telegram-ai-agent-BEWcw`

## Key constants

| Constant | Value | File |
|---|---|---|
| POSTS_PER_CHANNEL | 3 | content_agent.py |
| CHANNELS_LIMIT | 20 | content_agent.py, digest_agent.py |
| LOOKBACK_HOURS | 24 | digest_agent.py |
| MIN_POSTS_FOR_DIGEST | 3 | digest_agent.py |
| DEFAULT_BATCH | 1000 | insights_agent.py |
| FILTER_CHUNK | 50 | insights_agent.py |

## insights_agent.py

CLI usage:
```
python insights_agent.py --channel VelesCommunityRu --topic-id 230358
python insights_agent.py --channel VelesCommunityRu --topic-id 230358 --batch 500
python insights_agent.py --channel VelesCommunityRu --topic-id 230358 --redetect-topic
```

**Auto-topic detection:** On first run, reads last 50 posts from channel/topic and asks AI to detect 1-3 main themes. Themes are saved and reused for all subsequent filtering and insight generation, making them contextual and relevant.

State stored in `insights_state.json` per channel:
- `freeze_id` — max message ID at first run; newer posts are ignored
- `cursor_id` — current position (going backwards); 0 = exhausted
- `topic_id` — cached forum topic ID
- `topics` — auto-detected channel themes (1-3 items); regenerated on `--redetect-topic`
- `output_group_id` — auto-created private megagroup
- `total_processed` / `total_published` — cumulative counters

Flow per run:
1. Detect channel topics (AI reads 50 posts, determines themes)
2. Collect batch from history
3. Filter posts relevant to detected topics
4. Generate insights (AI is aware of topics)
5. Publish (insight + original + link + media)

## Text cleanup (clean_text)

Applied to all AI output before sending:
- Strip emoji (unicode ranges)
- Remove t.me links and @mentions (5+ chars)
- Remove hashtags (#word)
- Collapse 3+ newlines → 2, collapse multiple spaces → 1

## What not to do

- Do not change provider order (Mistral is primary, user explicitly chose this)
- Do not add `--no-verify` or skip git hooks
- Do not push to main/master
- Do not create pull requests unless explicitly asked
- Do not add error handling for scenarios that cannot happen
- Do not add comments explaining what code does — only why if non-obvious
