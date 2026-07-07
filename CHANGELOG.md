# Changelog

All notable changes to SteamDealBot will be documented in this file.

## [Unreleased]

- Add future changes here before tagging a new version.

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
