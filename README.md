# SteamDealBot

A Twitter (𝕏) bot that automatically finds and posts Steam game deals with detailed descriptions and store links. This bot runs every 6 hours using GitHub Actions to keep your followers updated with the latest gaming discounts.

## Features

- **Real Steam Deal Detection**: Automatically scrapes Steam for current game discounts
- **Rich Tweet Format**: Posts engaging tweets with game descriptions and Steam store links
- **Automated Posting**: Runs every 6 hours via GitHub Actions
- **Smart Deal Selection**: Finds the best deals with highest discount percentages
- **Secure Credential Management**: Uses GitHub Secrets for production, .env for local development
- **Easy Setup**: Simple installation and deployment process
- **Professional Formatting**: Clean tweet format with hashtags and Steam store links
- **232-Character Tweets**: Each deal tweet is auto-fitted to 232 characters (configurable in `steam_deals.py`)
- **Manual Poster CLI**: Terminal tool with ASCII banner, plain-text prompts, and copy-to-clipboard for 𝕏

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
Found 11 unique deals
Deal tweet prepared: 🏷️It Takes Two -75% off!
$9.99  |  Steam Popular Deals

A great game on sale!

https://store.steampowered.com/app/1426210/
#SteamDeals #Gaming #Deals #ItTakesTwo
Tweet length: 161 characters (max 232 when formatted via steam_deals.py)
Twitter API credentials verified successfully!
Could not post tweet (API access limitation): 403 Forbidden
Tweet content that would be posted:
==================================================
🏷️It Takes Two -75% off!
$9.99  |  Steam Popular Deals

A great game on sale!

https://store.steampowered.com/app/1426210/
#SteamDeals #Gaming #Deals #ItTakesTwo
==================================================
Bot execution completed successfully!
```

## Manual Usage (Free API Tier)

Since the free Twitter API tier doesn't allow posting tweets, you can use these manual methods:

### Method 1: Interactive Manual Poster (Recommended)

```bash
python manual_poster.py
```

On launch you get an ASCII **STEAM DEAL BOT** banner, a **Manual Poster** header, then an interactive loop to browse deals.

**Features:**
- ASCII banner on startup (©RFNco)
- Plain-text terminal UI (no decorative emoji in prompts)
- Shows real Steam deals with USD prices
- Copy tweet to clipboard for posting on 𝕏
- Character count per tweet shown as `187/232` (see [Tweet length limit](#tweet-length-limit))
- Menu: copy tweet, next deal, refresh, or exit
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
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## How It Works

1. **Deal Detection**: Uses Steam's API to find real game discounts (finds 11+ deals)
2. **Data Processing**: Extracts game names, USD prices, discount percentages, and Steam store URLs
3. **Tweet Formatting**: Builds each tweet (max **232 characters**), keeping title, price, link, and hashtags; shortens the description when needed (see [Tweet Format](#tweet-format))
4. **Posting**: 
   - **Automated**: Posts via Twitter API (requires Basic/Pro access level)
   - **Manual**: Copy-paste method for free API tier users
5. **Scheduling**: Runs every 6 hours using cron syntax in GitHub Actions
6. **Authentication**: Uses Tweepy with OAuth 1.0a for secure Twitter API access

## Tweet Format

Each deal is formatted like this (one 🏷️ prefix in the tweet body):

```
🏷️Palworld -25% off!
$22.49  |  Steam Popular Deals

Fight, farm, build, and work alongside mysterious creatures called "Pals" in this completely new multiplayer, open-world survival game!

https://store.steampowered.com/app/1623730/Palworld/
#SteamDeals #Gaming #Deals #Palworld
```

### Tweet length limit

| Setting | Value |
|--------|--------|
| Constant | `TWEET_MAX_LENGTH` in `steam_deals.py` |
| Default | **232 characters** per tweet |

`format_deal_tweet()` trims long descriptions (and shortens the title or hashtag if needed) so every tweet stays at or under the limit. The manual poster prints `Tweet (187/232 characters)` so you can see usage before copying.

𝕏 allows up to **280** characters per post; this project uses **232** by default to leave room for edits or platform quirks. Change `TWEET_MAX_LENGTH` to adjust.

### Tweet contents
- Game name with discount percentage
- Current price and deal source
- Short description from Steam (truncated to fit the limit)
- Direct Steam store link
- Hashtags: `#SteamDeals #Gaming #Deals` plus a game-specific tag

## Customization

To customize the bot for your needs:

1. **Change the tweet format**: Modify `format_deal_tweet()` in `steam_deals.py`
2. **Change max tweet length**: Set `TWEET_MAX_LENGTH` in `steam_deals.py` (default `232`)
3. **Adjust the schedule**: Edit the cron expression in `.github/workflows/bot.yml`
4. **Add more deal sources**: Extend `get_all_deals()` in `steam_deals.py`
5. **Modify deal selection**: Change the sorting logic in `get_best_deal_tweet()`
6. **Add filtering**: Implement price or discount percentage filters
7. **Customize manual poster**: Edit `BANNER` or prompts in `manual_poster.py`
8. **Modify web interface**: Update the HTML template in `web_interface.py`

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

5. **Tweet looks cut off**
   - Tweets are limited to `TWEET_MAX_LENGTH` (232 by default)
   - Increase the constant in `steam_deals.py` if you need longer posts (𝕏 max is 280)

6. **© symbol shows as a box in the manual poster banner**
   - Use Windows Terminal or run `chcp 65001` before `python manual_poster.py` for UTF-8 output

## Current Status

### Working features
- **Deal Detection**: Finds 11+ real Steam deals with USD prices
- **Tweet Formatting**: 232-character cap with smart truncation
- **Steam API Integration**: Uses official Steam API for reliable data
- **Manual Posting**: ASCII banner CLI, clipboard copy, `current/232` length display
- **Desktop Shortcut**: Easy one-click access on Windows
- **Web Interface**: Beautiful web UI for deal browsing
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
4. **Advanced Filtering**: Filter by game genre, price range, etc.
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

