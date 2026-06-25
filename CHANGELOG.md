# Changelog

All notable changes to SteamDealBot will be documented in this file.

## [Unreleased]

- Add future changes here before tagging a new version.

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

- Shifted refresh and exit menu options down to keep the original single-tweet copy option unchanged.
- Tightened tweet price/source separator spacing from two spaces around `|` to one space.
- Increased the tweet length limit from 232 to 280 characters to allow longer descriptions.
- Kept bulk copied tweet text in the same format as single copied tweets, separated only by dividers.
- Renamed the refresh menu option to make it clear that refreshed deals also refresh tweet idea sources.
