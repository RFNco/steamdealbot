# SteamDealBot

A Twitter (𝕏) bot that automatically finds and posts Steam game deals with detailed descriptions and store links. This bot runs every 6 hours using GitHub Actions to keep your followers updated with the latest gaming discounts.

## Features

- **Real Steam Deal Detection**: Pulls live discounts from Steam's specials catalog
- **Balanced Deals Every Refresh**: Favors reviewed/popular discounted games while keeping some discovery space for lesser-known indies
- **Dynamic Source Label**: Shows the active seasonal sale name (e.g. "Steam Summer Sale") when one is running, otherwise "Steam Specials"
- **Relevant Game Hashtags**: Adds genre/tag hashtags (e.g. `#OpenWorld #RPG`) per game for better reach
- **Rich Tweet Format**: Posts engaging tweets with game descriptions and Steam store links
- **Keyword Deal Search**: Search discounted Steam games by keyword and copy one or more matching tweets
- **Deal Collections**: Browse deal modes and category collections for thread-style posting (RPG, under $5, deep discounts, and more)
- **Posted-Game Memory**: Manual poster remembers copied games and surfaces fresher picks on refresh
- **Automated Posting**: Runs every 6 hours via GitHub Actions
- **Smart Deal Selection**: Finds the best deals with highest discount percentages
- **Secure Credential Management**: Uses GitHub Secrets for production, .env for local development
- **Easy Setup**: Simple installation and deployment process
- **280-Character Tweets**: Each deal tweet is auto-fitted to 280 characters (configurable in `steam_deals.py`)
- **Manual Poster CLI**: Terminal tool (v2.1.4) with ASCII banner, collections, posted-game memory, and copy-to-clipboard for 𝕏

## Prerequisites

Before you begin, you'll need:

1. A Twitter Developer Account
2. Twitter API credentials (API Key, API Secret, Access Token, Access Token Secret, Bearer Token)
3. Python 3.7+ installed locally (for testing)

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/steamdealbot.git
cd steamdealbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory with your Twitter API credentials:

```env
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

**⚠️ Important:** Never commit your `.env` file to version control. It's already included in `.gitignore`.

### 4. Test the Bot Locally

```bash
python bot.py
```

If everything is set up correctly, you should see output similar to:
```
Starting SteamDealBot...
Fetching Steam deals...
Searching for Steam deals...
Sampled 49 specials (offset 6551, sort 'default')
Found 49 unique deals
Deal tweet prepared: 🏷️It Takes Two -75% off!
$̶1̶9̶.̶9̶9̶ $9.99 | Steam Specials

A great co-op adventure on sale - grab a friend and dive in!

https://store.steampowered.com/app/1426210/
#SteamDeals #Gaming #Deals #CoOp #Adventure
Tweet length: 242 characters (max 280 when formatted via steam_deals.py)
Twitter API credentials verified successfully!
Could not post tweet (API access limitation): 403 Forbidden
Tweet content that would be posted:
==================================================
🏷️It Takes Two -75% off!
$̶1̶9̶.̶9̶9̶ $9.99 | Steam Specials

A great co-op adventure on sale - grab a friend and dive in!

https://store.steampowered.com/app/1426210/
#SteamDeals #Gaming #Deals #CoOp #Adventure
==================================================
Bot execution completed successfully!
```

## Manual Usage (Free API Tier)

Since the free Twitter API tier doesn't allow posting tweets, you can use these manual methods:

### Method 1: Interactive Manual Poster (Recommended)

```bash
python manual_poster.py
```

On launch you get an ASCII **STEAM DEAL BOT** banner, a **Manual Poster - v2.1.4** header, then an interactive loop to browse deals.

**Features:**
- ASCII banner on startup (©RFNco) with manual poster version label
- Plain-text terminal UI (no decorative emoji in prompts)
- Shows real Steam deals with USD prices
- Different games on every refresh (random sampling of Steam's specials)
- Posted-game memory: copied tweets are saved locally and recently copied games move to the end for more variety
- Amber `Posted` label on deal headers for recently copied games
- Copy one tweet or bulk copy the next 5 deal tweets for faster posting
- Generate 5 themed tweet ideas, browse deal modes, or browse category collections under **Collections & ideas**
- Search discounted Steam games by keyword, then copy one or more matching tweets without re-searching
- Open a separate Nintendo US deals menu (optional keyword) and copy one selected Nintendo tweet
- Steam and general gaming ideas can use current Steam deal data; Nintendo ideas stay template-only for now
- Character count per tweet shown as `242/280` (see [Tweet length limit](#tweet-length-limit))
- Menu: copy tweet, next deal, bulk copy, collections & ideas, refresh, Steam keyword search, Nintendo US deals, or exit
- Clipboard fallbacks: pyperclip, Termux, macOS `pbcopy`, Windows `clip`

### Method 2: Desktop Shortcut (Windows)

1. **Double-click** `SteamDealBot.bat`
2. **Follow the prompts** to get deals
3. **Press 1** to copy tweet to clipboard
4. **Paste on 𝕏** and post!

### Method 3: Web Interface

```bash
python web_interface.py
```

Then open: http://localhost:5000

**Features:**
- Web interface for browsing deals
- Click to copy tweets
- One-click "Open Twitter" button
- Mobile-friendly layout

### Method 4: Android (Termux)

Run the manual poster on Android using Termux:

```bash
# Install Termux + Termux:API from F-Droid first
pkg update -y && pkg install -y python termux-api git
# Get the code
git clone https://github.com/yourusername/steamdealbot.git
cd steamdealbot
# Install minimal deps (skip requirements.txt to avoid lxml build issues)
pip install requests beautifulsoup4 pyperclip
# Run
python manual_poster.py
```

- Clipboard: With Termux:API installed, the script auto-uses `termux-clipboard-set` if `pyperclip` isn’t available.
- You can also copy the folder via file manager and `cd` into it instead of cloning.

## GitHub Actions Setup

The bot runs automatically every 6 hours using GitHub Actions. To set this up:

### 1. Fork or Clone This Repository

### 2. Set Up GitHub Secrets

Go to your repository on GitHub → Settings → Secrets and variables → Actions, then add the following secrets:

- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`
- `TWITTER_BEARER_TOKEN`

### 3. Enable GitHub Actions

The workflow file (`.github/workflows/bot.yml`) is already configured. GitHub Actions will automatically run the bot every 6 hours.

## Project Structure

```
steamdealbot/
├── .github/
│   └── workflows/
│       └── bot.yml              # GitHub Actions workflow
├── .gitignore                   # Git ignore file
├── bot.py                       # Main bot script
├── manual_poster.py             # Interactive manual poster
├── steam_deals.py               # Steam deal detection (latest version)
├── web_interface.py             # Web interface for manual posting
├── SteamDealBot.bat             # Desktop shortcut for Windows
├── CHANGELOG.md                 # Versioned change history
├── ROADMAP.md                   # Future improvement checklist
├── .manual_poster_posted.json   # Local copied-game history (created at runtime, gitignored)
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## How It Works

1. **Deal Detection (balanced)**: Uses Steam's paginated search-results JSON endpoint (`store.steampowered.com/search/results/?infinite=1&json=1`) with a blend of top reviewed/relevant sale pages plus a capped discovery sample. This keeps recognizable games and well-reviewed indies near the front without removing lesser-known discoveries entirely. The legacy featured API and HTML scrapers remain as fallbacks.
2. **Sale Detection**: Checks the Steam homepage once per run for an active seasonal sale (Summer, Winter, etc.) and uses its name as the deal `source`; falls back to "Steam Specials".
3. **Data Processing**: Extracts game names, USD prices, discount percentages, Steam store URLs, and the game's top user tags (used for hashtags). Descriptions are fetched for the first few deals (the rest get a generated line) to keep refreshes fast.
4. **Tweet Formatting**: Builds each tweet (max **280 characters**), keeping title, original/sale price, clean Steam app link, and hashtags; shortens the description when needed (see [Tweet Format](#tweet-format)).
5. **Posting**: 
   - **Automated**: Posts via Twitter API (requires Basic/Pro access level)
   - **Manual**: Copy-paste method for free API tier users
6. **Scheduling**: Runs every 6 hours using cron syntax in GitHub Actions
7. **Authentication**: Uses Tweepy with OAuth 1.0a for secure Twitter API access

## Tweet Format

Each deal is formatted like this (one 🏷️ prefix in the tweet body):

```
🏷️Palworld -25% off!
$̶2̶9̶.̶9̶9̶ $22.49 | Steam Specials

Fight, farm, build, and work alongside mysterious creatures called "Pals" in this new multiplayer, open-world survival game!

https://store.steampowered.com/app/1623730/
#SteamDeals #Gaming #Deals #OpenWorld #Survival
```

During a seasonal sale, the source line becomes the sale name, e.g. `$̶2̶9̶.̶9̶9̶ $22.49 | Steam Summer Sale`.

### Tweet length limit

| Setting | Value |
|--------|--------|
| Constant | `TWEET_MAX_LENGTH` in `steam_deals.py` |
| Default | **280 characters** per tweet |

`format_deal_tweet()` trims the description (and, if still too long, drops the genre hashtags and then shortens the title) so every tweet stays at or under the limit. The manual poster prints `Tweet (242/280 characters)` so you can see usage before copying.

𝕏 allows up to **280** characters per post; this project uses **280** by default. Change `TWEET_MAX_LENGTH` to adjust.

### Tweet contents
- Game name with discount percentage
- Strikethrough original price, current price, and deal source (seasonal sale name when one is active)
- Short description from Steam (truncated to fit the limit)
- Clean direct Steam app link (`https://store.steampowered.com/app/<id>/`)
- Hashtags: `#SteamDeals #Gaming #Deals` plus up to **2 game-specific genre/tag hashtags** (e.g. `#OpenWorld #RPG`). The game-name hashtag was removed to give the description more room.

### Themed tweet ideas

The manual poster can also generate 5 non-AI tweet ideas:

- **Steam**: mixes reusable Steam templates with current Steam deal names, prices, discounts, and clean links
- **Nintendo**: template-only Nintendo-related ideas for now, with no Steam game links
- **Gaming**: mixes reusable gaming templates with current Steam deal data when useful

Use **Refresh** to fetch a fresh deal set before generating more ideas.

### Collections & ideas

Option **4. Collections & ideas** opens a second menu for thread-style content:

- **Themed tweet ideas**: Steam, Nintendo, or general gaming idea batches
- **Deal modes**: big names, popular indies, hidden gems, deep discounts
- **Categories**: RPG, horror, co-op, cozy, strategy, under $5

Each collection shows a numbered list with discount and price, supports multi-pick copy (`3`, `3,7`, or `3-5`), and uses collection-specific source labels such as `Steam RPG Deals` or `Steam Under $5`.

### Posted-game memory

When you copy a deal tweet, the manual poster saves it to a local `.manual_poster_posted.json` file (gitignored). For the next 14 days:

- Recently copied games are moved to the end of the list on refresh/restart
- Deal headers show an amber `Posted` label when that game appears again

### Keyword deal search

The manual poster can search discounted Steam games directly by keyword:

```text
Search discounted Steam games by keyword: Baldur
```

The search uses Steam's specials endpoint with the keyword and only returns discounted matches. Results are shown as a compact numbered list with game title, discount, and price. You can copy one or more picks (`3`, `3,7`, or `3-5`) and stay in the same search to copy more before going back.

### Nintendo US deals menu

The manual poster includes a separate Nintendo menu so Nintendo deals are not mixed into the main Steam feed.

```text
7. Nintendo US deals
```

You can browse Nintendo deals one-by-one with a dedicated submenu:

- Copy current Nintendo tweet
- Show next Nintendo deal
- Search Nintendo keyword
- Refresh Nintendo deals
- Back to Steam menu

Nintendo keyword search uses the same pick syntax as Steam search for copying: single (`3`), list (`3,7`), or range (`3-5`).

If Nintendo's legacy US sales endpoint is unavailable, the bot falls back to the free `nintendeals` provider for US deal lookup.

## Customization

To customize the bot for your needs:

1. **Change the tweet format**: Modify `format_deal_tweet()` in `steam_deals.py`
2. **Change max tweet length**: Set `TWEET_MAX_LENGTH` in `steam_deals.py` (default `280`)
3. **Change number of genre hashtags**: Set `RELEVANT_HASHTAG_COUNT` (default `2`); skip noisy tags via `GENERIC_TAGS`
4. **Tune deal variety**: Adjust `POPULAR_SEARCH_PAGES`, `DISCOVERY_SEARCH_SORTS`, `DISCOVERY_OFFSET_LIMIT`, or `sample_size` in `steam_deals.py`
5. **Tune sale detection**: Edit `SEASONAL_SALE_PATTERN` / `DEFAULT_SOURCE_LABEL`
6. **Limit description fetches**: Set `DESCRIPTION_ENRICH_LIMIT` (more = richer but slower refresh)
7. **Adjust the schedule**: Edit the cron expression in `.github/workflows/bot.yml`
8. **Modify deal selection**: Change the sorting logic in `get_best_deal_tweet()`
9. **Customize manual poster**: Edit `BANNER`, prompts, bulk copy count, or tweet idea templates in `manual_poster.py`
10. **Modify web interface**: Update the HTML template in `web_interface.py`

## Troubleshooting

### Common Issues

1. **"Missing required Twitter API credentials"**
   - Make sure all environment variables are set correctly
   - Check that your `.env` file is in the root directory

2. **"Error posting tweet" / "403 Forbidden"**
   - This is expected with the free Twitter API tier
   - You need to upgrade to Basic ($100/month) or Pro access level
   - Visit: https://developer.x.com/en/portal/product
   - The bot will still detect deals and show what would be posted

3. **GitHub Actions failing**
   - Double-check that all secrets are set in GitHub
   - Make sure the secret names match exactly (case-sensitive)

4. **"No Steam deals found"**
   - This can happen if Steam's API is down or changes
   - The bot will fall back to showing example deals
   - Check the deal detection logic in `steam_deals.py`

5. **Same games repeating on refresh**
   - Deals are blended from popular/reviewed pages plus a capped discovery sample, so some high-signal games may appear more often by design
   - Copied games are also saved locally and deprioritized for 14 days to keep refreshes fresher
   - If you still see repeats, the paginated endpoint may have failed and the code fell back to the curated featured list — check the console for fetch errors

6. **Missing descriptions or genre hashtags**
   - The session sets `birthtime`/`mature_content` cookies to bypass Steam's age gate; without them age-gated pages return no description/tags
   - Only the first `DESCRIPTION_ENRICH_LIMIT` deals get full descriptions/tags per refresh (others use a generated line); the deal actually tweeted is always enriched

7. **Tweet looks cut off**
   - Tweets are limited to `TWEET_MAX_LENGTH` (280 by default)
   - Shorten templates/descriptions if you want more room for manual edits

8. **© symbol shows as a box in the manual poster banner**
   - Use Windows Terminal or run `chcp 65001` before `python manual_poster.py` for UTF-8 output

## Current Status

### Working features
- **Balanced Deal Detection**: Review/relevance-weighted sampling with a smaller discovery slice
- **Dynamic Source Label**: Seasonal sale name when active, else "Steam Specials"
- **Genre Hashtags**: Up to 2 relevant game tags per tweet for reach
- **Tweet Formatting**: 280-character cap, strikethrough original prices, clean Steam app URLs, and smart truncation
- **Manual Posting**: ASCII banner CLI (v2.1.4), posted-game memory, collections, single/bulk clipboard copy, `current/280` length display
- **Tweet Ideas**: 5 themed non-AI ideas using templates plus current deal data for Steam/general gaming
- **Collections**: Deal modes and category browsing for thread-style posting
- **Keyword Search**: Search discounted Steam games by keyword and copy one or more matching tweets
- **Desktop Shortcut**: Easy one-click access on Windows
- **Web Interface**: Web UI for deal browsing
- **GitHub Actions**: Runs automatically every 6 hours
- **API Connection**: Connects to Twitter successfully

### Limitations
- **Tweet Posting**: Requires Twitter API Basic/Pro access ($100+/month)
- **Free Tier**: Can only verify credentials, not post tweets
- **Manual Required**: Free users must copy-paste tweets manually

### Next steps
1. **Upgrade Twitter API**: Get Basic or Pro access to enable automated posting
2. **Add More Sources**: Integrate other game stores (Epic, GOG, etc.)
3. **Image Support**: Add game screenshots to tweets
4. **Advanced Filtering**: More deal modes, categories, and posted-history controls
5. **Mobile App**: Create mobile app for easier manual posting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Happy tweeting!**

