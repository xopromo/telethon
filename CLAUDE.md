# Project: Telegram AI Agent

Personal Telegram agent that monitors subscribed channels, rewrites posts via AI, and publishes them to Saved Messages.

## Architecture

Two independent agents:
- **content_agent.py** — manual run, fetches latest posts per channel, rewrites singles, merges similar into mini-digests
- **digest_agent.py** — runs every 6h via cron, collects posts from last 24h, writes full articles for groups of 3+

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
| CHANNELS_LIMIT | 10 | both |
| LOOKBACK_HOURS | 24 | digest_agent.py |
| MIN_POSTS_FOR_DIGEST | 3 | digest_agent.py |

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
