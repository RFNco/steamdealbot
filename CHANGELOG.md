# Changelog

All notable changes to SteamDealBot will be documented in this file.

## [Unreleased]

- Add future changes here before tagging a new version.

## [2.1.2] - 2026-06-30

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

## [2.1.1] - 2026-06-25

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
