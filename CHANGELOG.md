# Changelog

All notable changes to SteamDealBot will be documented in this file.

## [Unreleased]

---

## [v2.1.8] - 21-07-2026

### Added

- Deal modes: **Under $10** and **50%+ off favorites**.
- Categories: **Action** and **Open world**.
- Expanded Gaming news RSS sources: Eurogamer, Polygon, Xbox Wire, PlayStation Blog, Gematsu, VG247, IGN, GameSpot, Stathetic Blog (pool size 80).
- Gaming news posted memory: `.manual_poster_posted_news.json`, magenta **Posted** tag before the source, deprioritized for 14 days.
- Gaming news copy flow: ask **Buffer** first; only offer **save image** when Buffer is skipped or unavailable.
- News image save detects Cloudflare blocks (e.g. Nintendo Life): copy image URL / open in browser instead of saving HTML.
- Moved **Gaming news** to the main menu (replaces **Copy 5 deals**): **7** without Buffer, **8** with Buffer.

### Changed

- Deal modes and Categories sample randomized Steam pages / offsets (larger pool, then shuffle) for more variety each open.
- Removed main-menu **Copy 5 deals** bulk copy; Gaming news removed from Collections & ideas.
- Deal **Posted** label moved in front of the game name (same pattern as news); uses `THEME["posted"]` (magenta) so it is distinct from yellow source labels.
- Rolled a few tweet-idea extras and news opener lines for v2.1.8.

### Docs

- README / ROADMAP updated for main-menu Gaming news, new modes/categories, Stathetic Blog rules, and Posted styling.

---

## [v2.1.7] - 16-07-2026

### Added

- **Gaming news** under Collections & ideas → **Gaming news** (`news_feeds.py` + `feedparser`):
  - RSS/Atom from Steam, Steam Client, PC Gamer, Nintendo Life, and Rock Paper Shotgun
  - Normalized fields (source, title, URL, published, summary) plus optional feed `image` / `video`
  - Browse 10 headlines per page from a ~50-item pool; **0** = next batch (re-fetches when the pool ends)
  - Copy Headline / Question / Hype drafts; Question/Hype openers rotate from phrase pools
  - Optional media: `[img]` / `[vid]` badges; save images to `images/news/` (`s` or after copy)

### Changed

- Keyword search (Steam and Nintendo): **0 results** skips confirmation and prompts for another keyword immediately; empty Enter still exits.
- News tweet fitting uses X’s weighted URL length (each link ≈ 23 chars) so headlines stay long and engaging.
- Bumped `lxml` to `>=5.3.0` for Python 3.13 installs (`4.9.3` failed to build).
- Rolled a few tweet-idea extras and news opener lines for v2.1.7.

### Docs

- README: macOS `python`/`pip` vs `python3`/`pip3`, project `.venv` setup, news feature notes, troubleshooting for missing deps.
- ROADMAP: marked shipped News & Trends items (pipeline, normalize, submenu, templates, optional media).

---

## [v2.1.6] - 14-07-2026

### Added

- Added `0 = Search again` for Steam and Nintendo keyword search after zero results or while viewing a result list, so another search does not require returning to the home menu first.
- Added optional Buffer queue integration for the manual poster (`BUFFER_API_KEY` in `.env`, `buffer_client.py`): **Add to Buffer queue** as menu option **2** on Steam/Nintendo (same color as Copy), plus an optional prompt after copying a tweet (deals, bulk copy, collections, and themed tweet ideas).
- Nintendo themed tweet ideas now use live Nintendo eShop US deals (with real storefront links), not template-only placeholders.
- Prefixed the main menu Copy action with `📋 Copy tweet` for clearer scanning.
- Rolled a few new reusable lines into `TWEET_IDEA_THEME_EXTRAS` for Steam, Nintendo, and Gaming.
- Documented Termux Buffer setup: local `.env` with `BUFFER_API_KEY`, `python-dotenv`, and `nano` save/exit (`Ctrl+O` / `Ctrl+X`).

### Changed

- Collection deal modes and categories now use the usual tweet source label (active Steam sale name, or `Steam Specials`) instead of collection-specific names like `Steam Big Names` or `Steam Hidden Gems`.
- Nintendo tweet links now use short `ec.nintendo.com/.../titles/<nsuid>` URLs for base games (`700100…`), and fall back to storefront product pages for DLC/bundles (`700700…`) that hit eShop error **9001-1630** on the short title path.
- Nintendo discount percentages are computed from regular vs sale price instead of trusting `nintendeals`' often-wrong `sale_discount` field.

---

## [v2.1.5] - 10-07-2026

### Added

- Added `ANSI_COLORS` named palette in `manual_poster.py` so terminal colors are easier to pick by name instead of raw ANSI codes.
- Added centralized `MENU_STYLES` for all manual poster menus, with separate Steam and Nintendo highlight maps.
- Added `python manual_poster.py --preview-colors` to preview the palette and sample menus without fetching deals.
- Added `STEAM_DEAL_COUNT` (default `35`) to tune how many Steam deals load in the main manual poster browse list.
- Added short Nintendo eShop tweet links via regional NSUID (`https://ec.nintendo.com/US/en/titles/<nsuid>`), similar to trimmed Steam app URLs.

### Changed

- Reorganized the main manual poster menu: `3` Search, `4` Refresh, `5` Collections & ideas, `6` Nintendo US deals, `7` Copy 5 deals, `8` Exit.
- Shortened menu labels to `Copy tweet`, `Show next`, and `Copy 5 deals` (Steam and Nintendo menus aligned).
- Made `nintendeals` the primary Nintendo US deals source when installed, skipping the slow dead official sales API.
- Reduced default Nintendo deal batch size (`NINTENDO_DEAL_COUNT`) for faster loads.
- Reduced default Steam main browse list from 50 to 35 deals for a shorter, faster refresh.
- Improved Nintendo refresh variety with batched `nintendeals` fetch and shuffled on-sale results.
- Fixed Nintendo keyword search so the main browse list stays on the default feed after copying search picks.
- Posted-game memory for Nintendo deals now keys by NSUID when available for more reliable **Posted** tracking.
- Updated README with per-package `pip install` explanations, menu layout, Nintendo notes, terminal color customization, and keeping `.manual_poster_posted.json` when updating the manual poster.

## [v2.1.4] - 07-07-2026

### Added

- Added a separate Nintendo US deals menu in the manual poster (`7. Nintendo US deals`) with optional keyword search.
- Added `nintendeals` fallback integration so Nintendo US deals still work when the legacy Nintendo endpoint returns 404.
- Added Nintendo deal countdown text (for example `2d left` / `40 hours left`) in tweet price/source lines when sale end data is available.
- Added Steam deal countdown text in tweet price/source lines when sale end data is available from Steam APIs.

### Changed

- Moved `Exit` to option `8` so Nintendo deals can live on the main menu without mixing into Steam flows.
- Changed Nintendo menu flow from one-shot pick list to an interactive browse menu (copy/next/search/refresh/back).
- Aligned Nintendo keyword search copy flow with Steam search (supports `3`, `3,7`, and `3-5` pick patterns).

## [v2.1.3] - 04-07-2026

### Added

- Added manual poster version label in the banner (`Manual Poster - v2.1.3`).
- Added posted-game history for the manual poster: copied tweets are saved locally and recently posted games are deprioritized on refresh/restart.
- Added amber `Posted` status on deal headers for recently copied games.
- Added multi-pick keyword search copy (`3`, `3,7`, or `3-5`) with a stay-open search loop.
- Added `Collections & ideas` submenu with themed tweet ideas, deal modes, and category collections.
- Added deal mode collections: big names, popular indies, hidden gems, and deep discounts.
- Added category collections: RPG, horror, co-op, cozy, strategy, and under $5.
- Added balanced under-$5 sampling across multiple price buckets so results are not only the cheapest games.

### Changed

- Renamed main manual poster menu options to `Copy this tweet`, `Copy next 5 deals`, and `Refresh`.
- Moved themed tweet ideas under the new `Collections & ideas` menu to keep the main menu compact.
- Updated README and ROADMAP for v2.1.3 manual poster workflow changes.

## [v2.1.2] - 30-06-2026

### Added

- Added `ROADMAP.md` for future improvement ideas and checklist tracking.
- Added a terminal-palette ANSI color theme for manual poster headings, separators, labels, values, menus, statuses, and tweet previews.
- Added manual poster keyword search for discounted Steam games, with one-result copy support.

### Changed

- Changed themed tweet ideas to copy one selected idea instead of copying all 5 ideas at once.
- Changed keyword search results to show a compact numbered title/discount list before copying the selected full tweet.
- Show the selected keyword search tweet preview after copying it.
- Rebalanced Steam deal sampling toward reviewed/popular games while keeping a smaller discovery sample for lesser-known indies.
- Preserved numbered game titles such as `Baldur's Gate 3` when cleaning Steam result names.
- Updated README documentation for v2.1.2 manual poster colors, selected idea copying, balanced deal sampling, and keyword search.

## [v2.1.1] - 25-06-2026

### Added

- Added a manual poster menu option to bulk copy 5 Steam deal tweets at once.
- Added automatic skipping for deals that were already included in a bulk copy.
- Added a non-AI themed tweet idea generator that mixes current Steam deal data with Steam and general gaming templates, while keeping Nintendo ideas template-only.
- Added clean Steam game links to deal-based tweet ideas.
- Added a larger tweet idea template bank while keeping each generated batch to 5 ideas.
- Added strikethrough original prices before discounted prices when original price data is available.
- Added Steam app URL trimming so copied tweets use clean `https://store.steampowered.com/app/<id>/` links.

### Changed

- Updated README documentation for v2.1.1 manual poster, tweet formatting, themed ideas, and changelog workflow..
- Shifted refresh and exit menu options down to keep the original single-tweet copy option unchanged.
- Tightened tweet price/source separator spacing from two spaces around `|` to one space.
- Increased the tweet length limit from 232 to 280 characters to allow longer descriptions.
- Kept bulk copied tweet text in the same format as single copied tweets, separated only by dividers.
- Renamed the refresh menu option to make it clear that refreshed deals also refresh tweet idea sources.
