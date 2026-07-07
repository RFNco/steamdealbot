# SteamDealBot Roadmap

Future ideas and improvements to consider after v2.1.4.

## Content Quality

- [x] Add deal modes: big names only, popular indies, hidden gems, deep discounts.
- [ ] Add filters for minimum discount, maximum price, and minimum review signal.
- [ ] Skip DLC, soundtracks, demos, and adult-only content unless explicitly enabled.
- [x] Add category searches such as RPG, horror, co-op, cozy, strategy, and under $5.
- [x] Add posted-game history so the same game does not repeat too soon.

## Tweet Writing

- [ ] Add selectable tweet styles: short hype, informative, question/poll, indie spotlight, big discount alert.
- [ ] Add optional engagement lines like "Would you grab this?" or "Backlog problem or instant buy?"
- [ ] Add more reusable templates for Steam, Nintendo, and general gaming posts.
- [ ] Add optional AI rewrite mode for fresh wording while keeping the app usable without AI.

## Manual Poster Workflow

- [x] Add "mark as posted" after copying a tweet.
- [x] Save copied/posted tweets with date, game name, price, and URL.
- [ ] Add a daily posting mix suggestion, for example 2 popular games, 2 indie games, and 1 engagement tweet.
- [ ] Add a queue view for prepared tweets.
- [ ] Add export to a text file for scheduled posting.

## Images And Media

- [ ] Add "save game image" for the current selected deal.
- [ ] Download Steam header/capsule image into an `images/` folder.
- [ ] Show the saved image path after copying tweet text.
- [ ] Add image support for keyword search results.
- [ ] Consider browser automation later for opening the X composer, while keeping image upload manual.

## New Sources

- [x] Add Nintendo/eShop deal support when a reliable API or source is chosen.
- [ ] Explore Epic Games Store, GOG, and Humble Bundle deal sources.
- [ ] Add source-specific tweet templates.

## News & Trends

- [ ] Add a gaming news pipeline using reliable RSS/Atom sources (official blogs + major outlets).
- [ ] Normalize fetched news fields (source, title, URL, published date, summary).
- [ ] Add dedupe + cache for news items to avoid reposting the same headline too often.
- [ ] Add a manual poster submenu for browsing and copying news-based tweet ideas.
- [ ] Add non-AI headline-to-tweet templates with engagement variants (question, recap, hype).
- [ ] Add source filters (official-only, platform-specific, all sources).
- [ ] Add recency filters (last 6h, 24h, 3d) for timely posts.

## Reliability

- [ ] Add tests for tweet formatting, URL trimming, keyword search parsing, and title cleanup.
- [ ] Add config file support for preferences like filters, tweet styles, and blocked tags.
- [ ] Improve Steam parser resilience if Steam changes HTML structure.
