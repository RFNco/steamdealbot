# SteamDealBot Roadmap

**Latest tagged release:** v2.1.7

Future ideas and improvements to consider after v2.1.7. (See **CHANGELOG [Unreleased]** for work in progress toward the next tag.)

## Content Quality

- [x] Add deal modes: big names only, popular indies, hidden gems, deep discounts.
- [ ] Add filters for minimum discount, maximum price, and minimum review signal.
- [ ] Skip DLC, soundtracks, demos, and adult-only content unless explicitly enabled.
- [x] Add category searches such as RPG, horror, co-op, cozy, strategy, and under $5.
- [x] Add posted-game history so the same game does not repeat too soon.

## Tweet Writing

- [ ] Add selectable tweet styles: short hype, informative, question/poll, indie spotlight, big discount alert.
- [ ] Add optional engagement lines like "Would you grab this?" or "Backlog problem or instant buy?"
- [x] Add more reusable templates for Steam, Nintendo, and general gaming posts (`TWEET_IDEA_THEMES` / `TWEET_IDEA_THEME_EXTRAS` in `manual_poster.py`). **Tweet ideas last rolled: v2.1.7**
- [x] Nintendo themed tweet ideas use live eShop US deals (prices, discounts, storefront links), not template-only placeholders.
- [ ] Add optional AI rewrite mode for fresh wording while keeping the app usable without AI.

**Per-release habit:** before tagging a new version, add, update, or swap a few tweet idea lines in `TWEET_IDEA_THEME_EXTRAS`, then bump **Tweet ideas last rolled** above (and `TWEET_IDEA_LAST_ROLLED_VERSION` in `manual_poster.py`) to match the version you are tagging.

## Manual Poster Workflow

- [x] Add "mark as posted" after copying a tweet.
- [x] Save copied/posted tweets with date, game name, price, and URL.
- [x] Centralize manual poster terminal/menu colors (`ANSI_COLORS`, `THEME`, `MENU_STYLES`) and add `--preview-colors`.
- [x] Keyword search: **0** = search again while viewing results; empty results auto-retry without confirmation (Steam + Nintendo).
- [ ] Add a daily posting mix suggestion, for example 2 popular games, 2 indie games, and 1 engagement tweet.
- [ ] Add a queue view for prepared tweets.
- [x] Optional Buffer API queue from the manual poster (`BUFFER_API_KEY`, add-to-queue as option **2**, optional prompt after copy).
- [ ] Add export to a text file for scheduled posting.

## Images And Media

- [ ] Add "save game image" for the current selected deal.
- [ ] Download Steam header/capsule image into an `images/` folder.
- [ ] Show the saved image path after copying tweet text.
- [ ] Add image support for keyword search results.
- [x] Optional news image/video from RSS media (`images/news/`; manual attach on X).
- [ ] Optional download for news video enclosures (when the feed provides a real file URL).
- [ ] Open Steam store page / image URL from the manual poster (browser), or reveal saved `images/` in Finder/Explorer.
- [ ] Consider browser automation later for opening the X composer, while keeping image upload manual.

## New Sources

- [x] Add Nintendo/eShop deal support when a reliable API or source is chosen.
- [x] Use short Nintendo eShop links in tweets (`ec.nintendo.com/.../titles/<nsuid>` for base games; storefront product URLs for DLC/bundles that fail with **9001-1630**).
- [x] Fix Nintendo discount % using regular vs sale price (do not trust `nintendeals` `sale_discount` alone).
- [ ] Quiet Nintendo fetch noise (e.g. hide dead official API 404s when `nintendeals` fallback succeeds).
- [ ] Explore Epic Games Store, GOG, and Humble Bundle deal sources.
- [ ] Add source-specific tweet templates.

## News & Trends

- [x] Add a gaming news pipeline using reliable RSS/Atom sources (official blogs + major outlets).
- [x] Normalize fetched news fields (source, title, URL, published date, summary).
- [x] Manual poster submenu under Collections & ideas → Gaming news (10/page, **0** = next batch / re-fetch at end of pool).
- [x] Non-AI headline-to-tweet templates (Headline / Question / Hype) with rotating opener pools and X-weighted URL length.
- [x] Optional image/video from feed media (`[img]`/`[vid]`; save image to `images/news/`).
- [ ] Add dedupe + cache for news items to avoid reposting the same headline too often (posted-news memory, similar to deals).
- [ ] Configurable / expandable feed list (add/remove outlets without code edits; e.g. Eurogamer, Polygon, Xbox Wire).
- [ ] Add source filters (official-only, platform-specific, all sources).
- [ ] Add recency filters (last 6h, 24h, 3d) for timely posts.
- [x] Per-release habit: refresh a few `QUESTION_OPENERS` / `HYPE_OPENERS` lines when tagging (same idea as tweet-idea rolls).
- [ ] Buffer for news: queue hot headlines to X (`addToQueue` / optional `customScheduled`), and save uncertain items as Buffer Ideas so they don’t burn limited queue slots.

## Reliability

- [ ] Add tests for tweet formatting, URL trimming, keyword search parsing, news tweet weighted length, and title cleanup.
- [ ] Add config file support for preferences like filters, tweet styles, blocked tags, and news feeds.
- [ ] Improve Steam parser resilience if Steam changes HTML structure.
- [ ] Optional macOS helper so `python` / `pip` work outside Cursor (alias, wrapper script, or clearer launcher docs only).
