# SteamDealBot 🚀

A Twitter (X) bot that automatically finds and posts Steam game deals with detailed descriptions and store links. This bot runs every 6 hours using GitHub Actions to keep your followers updated with the latest gaming discounts.

## Features

- 🎮 **Real Steam Deal Detection**: Automatically scrapes Steam for current game discounts
- 📝 **Rich Tweet Format**: Posts engaging tweets with game descriptions and Steam store links
- 🤖 **Automated Posting**: Runs every 6 hours via GitHub Actions
- 🔍 **Smart Deal Selection**: Finds the best deals with highest discount percentages
- 🔐 **Secure Credential Management**: Uses GitHub Secrets for production, .env for local development
- 📦 **Easy Setup**: Simple installation and deployment process
- 🏷️ **Professional Formatting**: Clean, engaging tweet format with hashtags and links

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

If everything is set up correctly, you should see:
```
🚀 Starting SteamDealBot...
🎮 Fetching Steam deals...
🔍 Searching for Steam deals...
✅ Found 1 unique deals
📝 Deal tweet prepared: 🏷️A Castle Full of Cats -20% off!
Rp 44  |  Steam Popular Deals

A Castle Full of Cats is a catvania hidden object game where you need to find all the cursed cats in the castle. Save each and every cat and unleash the power of love! ♡ 

https://store.steampowered.com/app/2070550/A_Castle_Full_of_Cats/?snr=1_7_7_2300_150_1
#SteamDeals #Gaming #Deals #ACastleFullofCats
📏 Tweet length: 368 characters
✅ Twitter API credentials verified successfully!
⚠️  Could not post tweet (API access limitation): 403 Forbidden
📝 Tweet content that would be posted:
==================================================
🏷️A Castle Full of Cats -20% off!
Rp 44  |  Steam Popular Deals

A Castle Full of Cats is a catvania hidden object game where you need to find all the cursed cats in the castle. Save each and every cat and unleash the power of love! ♡ 

https://store.steampowered.com/app/2070550/A_Castle_Full_of_Cats/?snr=1_7_7_2300_150_1
#SteamDeals #Gaming #Deals #ACastleFullofCats
==================================================
🎉 Bot execution completed successfully!
```

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
├── steam_deals_enhanced.py      # Enhanced Steam deal detection
├── steam_deals_simple.py        # Simple Steam deal detection
├── steam_deals.py               # Original Steam deal detection
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## How It Works

1. **Deal Detection**: The bot scrapes Steam's specials page to find current game discounts
2. **Data Processing**: Extracts game names, prices, discount percentages, descriptions, and Steam store URLs
3. **Tweet Formatting**: Creates engaging tweets with the format:
   ```
   🏷️Game Name -XX% off!
   $XX.XX  |  Steam Popular Deals
   
   Game description here...
   
   https://store.steampowered.com/app/XXXXXX/Game_Name/
   #SteamDeals #Gaming #Deals #GameName
   ```
4. **Posting**: Attempts to post the tweet via Twitter API (requires Basic/Pro access level)
5. **Scheduling**: Runs every 6 hours using cron syntax in GitHub Actions
6. **Authentication**: Uses Tweepy with OAuth 1.0a for secure Twitter API access

## Tweet Format

The bot creates engaging tweets in this format:

```
🏷️Palworld -25% off!
$22.49  |  Steam Popular Deals

Fight, farm, build, and work alongside mysterious creatures called "Pals" in this completely new multiplayer, open-world survival and crafting game!

https://store.steampowered.com/app/1623730/Palworld/
#SteamDeals #Gaming #Deals #Palworld
```

### Features:
- **Game name with discount percentage**
- **Current price and source information**
- **Full game description from Steam**
- **Direct Steam store link**
- **Relevant hashtags including game name**

## Customization

To customize the bot for your needs:

1. **Change the tweet format**: Modify the `format_deal_tweet()` function in `steam_deals_enhanced.py`
2. **Adjust the schedule**: Edit the cron expression in `.github/workflows/bot.yml`
3. **Add more deal sources**: Extend the `get_all_deals()` function in `steam_deals_enhanced.py`
4. **Modify deal selection**: Change the sorting logic in `get_best_deal_tweet()`
5. **Add filtering**: Implement price or discount percentage filters

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
   - This can happen if Steam's page structure changes
   - The bot will fall back to showing a generic message
   - Check the deal detection logic in `steam_deals_enhanced.py`

## Current Status

### ✅ Working Features:
- **Deal Detection**: Successfully finds Steam game deals
- **Tweet Formatting**: Creates professional, engaging tweets
- **Steam Integration**: Gets game descriptions and store links
- **GitHub Actions**: Runs automatically every 6 hours
- **API Connection**: Connects to Twitter successfully

### ⚠️ Limitations:
- **Tweet Posting**: Requires Twitter API Basic/Pro access ($100+/month)
- **Free Tier**: Can only verify credentials, not post tweets
- **Deal Sources**: Currently only scrapes Steam (can be extended)

### 🚀 Next Steps:
1. **Upgrade Twitter API**: Get Basic or Pro access to enable posting
2. **Add More Sources**: Integrate other game stores (Epic, GOG, etc.)
3. **Image Support**: Add game screenshots to tweets
4. **Advanced Filtering**: Filter by game genre, price range, etc.

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

**Happy tweeting! 🐦✨**

