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
- **Nintendo US Deals (manual poster)**: Separate eShop US discount menu (requires `nintendeals`; see [Nintendo US deals menu](#nintendo-us-deals-menu))
- **Buffer Queue (optional)**: With `BUFFER_API_KEY` in `.env`, send tweets from the manual poster straight into your Buffer X queue
- **Automated Posting**: Runs every 6 hours via GitHub Actions
- **Smart Deal Selection**: Finds the best deals with highest discount percentages
- **Secure Credential Management**: Uses GitHub Secrets for production, .env for local development
- **Easy Setup**: Simple installation and deployment process
- **280-Character Tweets**: Each deal tweet is auto-fitted to 280 characters (configurable in `steam_deals.py`)
- **Manual Poster CLI**: Terminal tool (v2.1.8) with ASCII banner, collections, posted-game memory, Buffer queue support, Gaming news (RSS), and copy-to-clipboard for 𝕏
- **Gaming News (manual poster)**: RSS/Atom headlines via main menu **Gaming news** (optional images; needs `feedparser`)

## Prerequisites

Before you begin, you'll need:

1. A Twitter Developer Account
2. Twitter API credentials (API Key, API Secret, Access Token, Access Token Secret, Bearer Token)
3. Python 3.7+ installed locally (for testing)
4. **`nintendeals`** (included in `requirements.txt`) if you want the manual poster **Nintendo US deals** menu
5. **`feedparser`** (included in `requirements.txt`) if you want **Gaming news** on the main menu

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/steamdealbot.git
cd steamdealbot
```

### 2. Install Dependencies

**Full install (bot + manual poster + web UI + Nintendo):**

```bash
pip install -r requirements.txt
```

**macOS tip:** system shells often have `python3` / `pip3`, not `python` / `pip`. Prefer a project venv so both names work after activate:

```bash
python3 -m venv .venv
source .venv/bin/activate   # prompt shows (.venv)
pip install -r requirements.txt
python manual_poster.py
```

On Windows, `python` and `pip` usually work if Python was installed with “Add to PATH”; activate with `.\.venv\Scripts\activate` if you use a venv.

**What each package in `requirements.txt` does:**

| Package | Install command | Used for |
|--------|-----------------|----------|
| `tweepy` | `pip install tweepy` | Posting tweets and verifying Twitter API credentials in `bot.py` |
| `requests` | `pip install requests` | Fetching Steam deal pages, Nintendo data, and other HTTP requests |
| `python-dotenv` | `pip install python-dotenv` | Loading Twitter API keys from your local `.env` file |
| `beautifulsoup4` | `pip install beautifulsoup4` | Parsing Steam HTML (descriptions, tags, search results) |
| `lxml` | `pip install lxml` | Faster HTML parser backend for BeautifulSoup (used by `bot.py` / full install) |
| `flask` | `pip install flask` | Running the optional web interface (`web_interface.py`) |
| `nintendeals` | `pip install nintendeals` | **Nintendo US deals** in the manual poster (primary working source) |
| `feedparser` | `pip install feedparser` | **Gaming news** RSS/Atom feeds on the main menu |

**Manual poster extras (not in `requirements.txt`, but recommended):**

| Package | Install command | Used for |
|--------|-----------------|----------|
| `pyperclip` | `pip install pyperclip` | One-key copy to clipboard in `manual_poster.py` (falls back to `clip` / `pbcopy` / Termux if missing) |

**Steam-only manual poster (smaller install, no Twitter bot / web UI / Nintendo):**

```bash
pip install requests beautifulsoup4 pyperclip
```

- `requests` — load Steam deal/search JSON and store pages
- `beautifulsoup4` — parse Steam result HTML
- `pyperclip` — copy formatted tweets to your clipboard

**Add Nintendo US deals** (install on top of the Steam-only set, or use full `requirements.txt`):

```bash
pip install nintendeals
```

- `nintendeals` — discounted US eShop games for **Nintendo US deals** (main menu **6** without Buffer, **7** with Buffer)

When `nintendeals` is installed, the manual poster uses it **directly** and skips Nintendo’s often-dead official sales API (faster loads).

### 3. Set Up Environment Variables

Create a `.env` file in the root directory with your Twitter API credentials:

```env
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Optional: send manual poster tweets straight to your Buffer X queue
BUFFER_API_KEY=your_buffer_personal_api_key_here
# Optional overrides (auto-detected when omitted):
# BUFFER_ORGANIZATION_ID=
# BUFFER_CHANNEL_ID=
```

**⚠️ Important:** Never commit your `.env` file to version control. It's already included in `.gitignore`. Never paste API keys into chat.

With `BUFFER_API_KEY` set, the manual poster shows **Add to Buffer queue** as option **2** on Steam and Nintendo (other items shift down one), and can also ask after a normal copy whether to queue the tweet. Posts use Buffer `mode: addToQueue` (next free slot). Free Buffer plans often cap the queue at 10 posts.

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

On launch you get an ASCII **STEAM DEAL BOT** banner, a **Manual Poster - v2.1.8** header, then an interactive loop to browse deals.

**Features:**
- ASCII banner on startup (©RFNco) with manual poster version label
- Plain-text terminal UI (menus stay light; Copy is labeled `📋 Copy tweet`)
- Shows real Steam deals with USD prices
- Different games on every refresh (random sampling of Steam's specials)
- Posted-game memory: copied tweets are saved locally and recently copied games move to the end for more variety
- Magenta `Posted` label before the game name for recently copied deals (same pattern as Gaming news)
- Copy one tweet for posting
- Optional Buffer queue: menu option **2** when `BUFFER_API_KEY` is set, plus an optional prompt after copy
- Generate 5 themed tweet ideas, browse deal modes, or categories under **Collections & ideas**
- Search discounted Steam games by keyword, then copy one or more matching tweets; empty results retry immediately, press **0** from a result list to search again
- Open a separate Nintendo US deals menu (optional keyword) and copy Nintendo tweets — **requires `nintendeals`**
- Open **Gaming news** (RSS) from the main menu for faster headline access
- Steam, Nintendo, and general gaming ideas can all use live deal data (Steam for themes 1/3, Nintendo eShop for theme 2)
- Character count per tweet shown as `242/280` (see [Tweet length limit](#tweet-length-limit))
- Clipboard fallbacks: pyperclip, Termux, macOS `pbcopy`, Windows `clip`
- Customizable terminal colors via `ANSI_COLORS`, `THEME`, and `MENU_STYLES`; preview with `--preview-colors`

**Main menu** (with Buffer configured):

```text
1. 📋 Copy tweet
2. Add to Buffer queue
3. Show next
4. Search by keyword
5. Refresh
6. Collections & ideas
7. Nintendo US deals
8. Gaming news
9. Exit
```

Without Buffer, option 2 is omitted and the rest keep their original numbers (Search=`3`, Refresh=`4`, Gaming news=`7`, Exit=`8`). Steam and Nintendo stay aligned.

**Preview terminal colors** (no deal fetch — useful while tuning `ANSI_COLORS` / `THEME` / `MENU_STYLES`):

```bash
python manual_poster.py --preview-colors
```

Save your edits, re-run the preview, then launch `python manual_poster.py` when it looks right. Colors load at startup only (not live while the poster is already running).

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
# Minimal manual poster (Steam browse + clipboard)
pip install requests beautifulsoup4 pyperclip python-dotenv
# Optional: Nintendo US deals menu
pip install nintendeals
# Run
python manual_poster.py
```

- Clipboard: With Termux:API installed, the script auto-uses `termux-clipboard-set` if `pyperclip` isn’t available.
- You can also copy the folder via file manager and `cd` into it instead of cloning.

**Buffer on Termux:** Buffer only appears if `.env` exists **in the same folder** as `manual_poster.py` and includes `BUFFER_API_KEY`. Cloning or copying just the `.py` files is not enough — `.env` is gitignored, so it is not included in git clone. Without it, Steam/Nintendo still work; you just will not see **Add to Buffer queue**.

Create or edit `.env` with `nano`:

```bash
cd ~/path/to/steamdealbot   # your project folder
nano .env
```

Type (or paste) at least:

```env
BUFFER_API_KEY=your_buffer_personal_api_key_here
```

In `nano` on Termux:

1. Edit the file as needed.
2. **Save:** `Ctrl+O`, then press **Enter** to confirm the filename.
3. **Exit:** `Ctrl+X`.

Then install dotenv if needed and run again:

```bash
pip install python-dotenv
python manual_poster.py
```

Startup should show `Buffer queue: ready (API key loaded)`, and option **2** becomes **Add to Buffer queue**. Needs internet when queuing. Never commit `.env` or share the key.

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
├── news_feeds.py                # RSS/Atom gaming news for the main-menu Gaming news option
├── buffer_client.py             # Optional Buffer queue helper
├── web_interface.py             # Web interface for manual posting
├── SteamDealBot.bat             # Desktop shortcut for Windows
├── CHANGELOG.md                 # Versioned change history
├── ROADMAP.md                   # Future improvement checklist
├── .manual_poster_posted.json   # Local copied-game history (created at runtime, gitignored)
├── images/news/                 # Optional saved news images (gitignored)
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
- **Nintendo**: mixes reusable Nintendo templates with current Nintendo eShop US deals and storefront links
- **Gaming**: mixes reusable gaming templates with current Steam deal data when useful

Use **Refresh** to fetch a fresh deal set before generating more ideas.

### Collections & ideas

**Collections & ideas** opens a second menu for thread-style content (main-menu number is **5** without Buffer, **6** with Buffer):

- **Themed tweet ideas**: Steam, Nintendo, or general gaming idea batches
- **Deal modes**: big names, popular indies, hidden gems, deep discounts, under $10, 50%+ off favorites
- **Categories**: RPG, horror, co-op, cozy, strategy, action, open world, under $5

Deal collections show a numbered list with discount and price, support multi-pick copy (`3`, `3,7`, or `3-5`), and use the same tweet source labels as regular Steam deals (active sale name, or `Steam Specials`). After copy, Buffer-ready sessions can optionally queue the tweet(s).

### Gaming news

Open from the main menu: **Gaming news** (**7** without Buffer, **8** with Buffer).

RSS/Atom headlines (Stathetic Blog, Steam, PC Gamer, Nintendo Life, Rock Paper Shotgun, Eurogamer, Polygon, Xbox Wire, PlayStation Blog, Gematsu, VG247, IGN, GameSpot, …) → pick one → copy a Headline / Question / Hype tweet draft (`news_feeds.py`, needs `feedparser`). 10 headlines per page (**0** = next batch; re-fetches at end of pool). Your **Stathetic Blog** posts only appear when newer than **2 days**; up to 3 fresh ones are lightly pinned near the top. Question/Hype openers rotate across a phrase pool. Drafts use X’s weighted link length so headlines stay readable. Optional `[img]`/`[vid]` from the feed; save images to `images/news/` for manual attach on X (Cloudflare-blocked CDNs fall back to URL/browser). After copy, Buffer is offered first; save-image is only asked if Buffer is skipped. Copied headlines are marked **Posted** for 14 days (`.manual_poster_posted_news.json`) and moved to the end of the pool.

### Posted-game memory

When you copy a deal tweet, the manual poster saves it to a local `.manual_poster_posted.json` file next to `manual_poster.py` (gitignored). For the next 14 days:

- Recently copied games are moved to the end of the list on refresh/restart
- Deal headers and collection lists show a magenta `Posted` label **before** the game name when that game appears again

Gaming news uses a separate `.manual_poster_posted_news.json` file with the same 14-day window and a `Posted` tag before the source name.

**Updating the manual poster (phone, Termux, or desktop):** keep those JSON files. Replace `manual_poster.py` (and `steam_deals.py` / `news_feeds.py` if you use them), but do not delete `.manual_poster_posted.json` or `.manual_poster_posted_news.json` in the same folder. If you move the project to a new directory, copy the JSON into the new folder beside the script — the poster does not read history from anywhere else.

Quick check after an update:

```bash
ls -la .manual_poster_posted.json .manual_poster_posted_news.json
python manual_poster.py
```

If **Posted** tags are missing, the JSON is probably in a different folder than the new script, the folder was wiped and only `.py` files were copied back, or the entries are older than 14 days. Back up both posted JSON files before major updates if you want a safety copy.

### Keyword deal search

The manual poster can search discounted Steam games directly by keyword:

```text
Search discounted Steam games by keyword: Baldur
```

The search uses Steam's specials endpoint with the keyword and only returns discounted matches. Results are shown as a compact numbered list with game title, discount, and price. You can copy one or more picks (`3`, `3,7`, or `3-5`) and stay in the same search to copy more. If nothing matches, you are prompted for a new keyword right away (no confirmation). Press **0** while viewing results to search again, or **Enter** on an empty keyword prompt to go back.

### Nintendo US deals menu

The manual poster includes a separate Nintendo menu so Nintendo deals are not mixed into the main Steam feed.

**Requirement:** install `nintendeals` (`pip install nintendeals` or `pip install -r requirements.txt`). Without it, **Nintendo US deals** will show no results.

When `nintendeals` is installed, the manual poster **uses it directly** and skips Nintendo’s often-dead official sales API (faster loads). Each load fetches **15** discounted games by default (`NINTENDO_DEAL_COUNT` in `steam_deals.py`). Discount % is computed from regular vs sale price. Tweet links use short `ec.nintendo.com/.../titles/<nsuid>` URLs for base games, and storefront product pages for DLC/bundles that fail on the short title path.

Open from the main menu: **Nintendo US deals** (**6** without Buffer, **7** with Buffer).
**Nintendo submenu** (with Buffer configured):

```text
1. 📋 Copy tweet
2. Add to Buffer queue
3. Show next
4. Search by keyword
5. Refresh
6. Back to Steam
```

Without Buffer, option 2 is omitted and Search/Refresh stay at **3** / **4**.

You can browse Nintendo deals one-by-one, or use **Search by keyword** for a temporary pick list. Copy syntax matches Steam: single (`3`), list (`3,7`), or range (`3-5`). Press **0** to search again (including after zero results), or **Enter** to return to the Nintendo browse menu. **Refresh** loads a new shuffled batch of on-sale games.

**Install check:**

```bash
python -c "import nintendeals; print('nintendeals OK')"
```

## Customization

To customize the bot for your needs:

1. **Change the tweet format**: Modify `format_deal_tweet()` in `steam_deals.py`
2. **Change max tweet length**: Set `TWEET_MAX_LENGTH` in `steam_deals.py` (default `280`)
3. **Change number of genre hashtags**: Set `RELEVANT_HASHTAG_COUNT` (default `2`); skip noisy tags via `GENERIC_TAGS`
4. **Tune deal variety**: Adjust `POPULAR_SEARCH_PAGES`, `DISCOVERY_SEARCH_SORTS`, `DISCOVERY_OFFSET_LIMIT`, or `sample_size` in `steam_deals.py`
5. **Tune Nintendo batch size**: Set `NINTENDO_DEAL_COUNT` in `steam_deals.py` (default `15`)
6. **Tune sale detection**: Edit `SEASONAL_SALE_PATTERN` / `DEFAULT_SOURCE_LABEL`
7. **Limit description fetches**: Set `DESCRIPTION_ENRICH_LIMIT` (more = richer but slower refresh)
8. **Adjust the schedule**: Edit the cron expression in `.github/workflows/bot.yml`
9. **Modify deal selection**: Change the sorting logic in `get_best_deal_tweet()`
10. **Customize manual poster colors**: Edit `ANSI_COLORS`, `THEME`, and `MENU_STYLES` at the top of `manual_poster.py` (preview with `python manual_poster.py --preview-colors`)
11. **Customize manual poster content**: Edit `BANNER`, prompts, or tweet idea templates in `manual_poster.py` (`TWEET_IDEA_THEME_EXTRAS` — refresh a few lines each release and bump `TWEET_IDEA_LAST_ROLLED_VERSION` + the version on `ROADMAP.md`)
12. **Modify web interface**: Update the HTML template in `web_interface.py`

### Manual poster terminal colors

All menu colors flow through three blocks near the top of `manual_poster.py`:

| Block | What it controls |
|-------|------------------|
| `ANSI_COLORS` | Named palette (`bright_cyan`, `gray`, `bright_yellow`, etc.) |
| `THEME` | UI roles (`title`, `value`, `warning`, `tweet`, …) mapped to palette names |
| `MENU_STYLES` | Menu layout: headers, prompts, option defaults, and per-menu highlights (`steam` / `nintendo`) |

Examples:

- Change **Search** color (no Buffer) → `MENU_STYLES["highlights"]["steam"][3]`
- Change **Add to Buffer** color → `MENU_STYLES["highlights"]["steam_buffer"][2]` (same maps exist for `nintendo` / `nintendo_buffer`)
- Change **Back to Steam** color (with Buffer) → `MENU_STYLES["highlights"]["nintendo_buffer"][6]`
- Change the actual shade → pick a different key in `ANSI_COLORS`, then point a `THEME` role at it

Preview after each save:

```bash
python manual_poster.py --preview-colors
```

Disable all colors: set environment variable `STEAMDEALBOT_NO_COLOR=1`.

## Troubleshooting

### Common Issues

1. **"command not found: python" / "command not found: pip" (especially macOS)**
   - On Mac, use `python3` and `pip3`, or activate a project venv first (`source .venv/bin/activate`) so `python` / `pip` point at that environment
   - Create/refresh the venv if needed: `python3 -m venv .venv`, then `source .venv/bin/activate`, then `pip install -r requirements.txt`
   - Cursor’s integrated terminal only “works” if that session already has the venv activated and deps installed — a regular Terminal window will not until you do the same
   - Windows usually provides `python` / `pip` when Python is on PATH; still use `.\.venv\Scripts\activate` if you rely on a venv

2. **"ModuleNotFoundError: No module named 'requests'" (or similar)**
   - Dependencies are not installed for the Python you are running. With the venv active: `pip install -r requirements.txt`
   - If install fails on `lxml` under Python 3.13, use current `requirements.txt` (`lxml>=5.3.0`)

3. **"Missing required Twitter API credentials"**
   - Make sure all environment variables are set correctly
   - Check that your `.env` file is in the root directory

4. **"Error posting tweet" / "403 Forbidden"**
   - This is expected with the free Twitter API tier
   - You need to upgrade to Basic ($100/month) or Pro access level
   - Visit: https://developer.x.com/en/portal/product
   - The bot will still detect deals and show what would be posted

5. **GitHub Actions failing**
   - Double-check that all secrets are set in GitHub
   - Make sure the secret names match exactly (case-sensitive)

6. **"No Steam deals found"**
   - This can happen if Steam's API is down or changes
   - The bot will fall back to showing example deals
   - Check the deal detection logic in `steam_deals.py`

7. **Same games repeating on refresh**
   - Deals are blended from popular/reviewed pages plus a capped discovery sample, so some high-signal games may appear more often by design
   - Copied games are also saved locally and deprioritized for 14 days to keep refreshes fresher
   - If you still see repeats, the paginated endpoint may have failed and the code fell back to the curated featured list — check the console for fetch errors

8. **Missing descriptions or genre hashtags**
   - The session sets `birthtime`/`mature_content` cookies to bypass Steam's age gate; without them age-gated pages return no description/tags
   - Only the first `DESCRIPTION_ENRICH_LIMIT` deals get full descriptions/tags per refresh (others use a generated line); the deal actually tweeted is always enriched

9. **Tweet looks cut off**
   - Tweets are limited to `TWEET_MAX_LENGTH` (280 by default)
   - Shorten templates/descriptions if you want more room for manual edits

10. **© symbol shows as a box in the manual poster banner**
   - Use Windows Terminal or run `chcp 65001` before `python manual_poster.py` for UTF-8 output

11. **"Nintendo US deals endpoint unavailable" / no Nintendo deals found**
   - If `nintendeals` is installed, the manual poster uses it directly and should not wait on the dead official API
   - Without `nintendeals`, install it: `pip install nintendeals`
   - Verify with: `python -c "import nintendeals; print('nintendeals OK')"`
   - If it still fails, reinstall from `requirements.txt` and try **Refresh** in the Nintendo menu again

12. **Buffer queue not showing / failed to queue**
   - Confirm `BUFFER_API_KEY` is set in `.env` next to the scripts, then restart `python manual_poster.py`
   - Startup should show `Buffer queue: ready (API key loaded)`
   - Free Buffer plans often cap the queue at 10 posts — clear a slot in Buffer if you get a queue-full error
   - Needs internet; personal API key scopes should include `account:read` and `posts:write`

13. **Tweaking manual poster colors**
   - Edit `ANSI_COLORS`, `THEME`, and `MENU_STYLES` in `manual_poster.py`, save, then run `python manual_poster.py --preview-colors`
   - Restart `python manual_poster.py` to see colors in the full app (colors do not hot-reload mid-session)

## Current Status

### Working features
- **Balanced Deal Detection**: Review/relevance-weighted sampling with a smaller discovery slice
- **Dynamic Source Label**: Seasonal sale name when active, else "Steam Specials"
- **Genre Hashtags**: Up to 2 relevant game tags per tweet for reach
- **Tweet Formatting**: 280-character cap, strikethrough original prices, clean Steam app URLs, and smart truncation
- **Manual Posting**: ASCII banner CLI (v2.1.8), posted-game memory, collections, clipboard copy, `current/280` length display
- **Buffer Queue**: Optional manual-poster → Buffer X queue via `BUFFER_API_KEY` (menu option **2** + after-copy prompt)
- **Tweet Ideas**: 5 themed non-AI ideas using templates plus live deal data for Steam, Nintendo eShop, and general gaming
- **Collections**: Deal modes and category browsing for thread-style posting
- **Gaming News**: Main-menu RSS/Atom headlines (10/page, next-batch refresh), Headline/Question/Hype drafts, Stathetic Blog freshness pin, optional `[img]` save to `images/news/`
- **Keyword Search**: Search discounted Steam games by keyword and copy one or more matching tweets (empty results retry immediately; **0** = search again from a result list)
- **Nintendo US Deals**: Manual poster eShop US menu via `nintendeals` (15 deals per load, install required; discount % and storefront links fixed for accuracy)
- **Terminal Color Preview**: `python manual_poster.py --preview-colors` for palette and menu samples
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

