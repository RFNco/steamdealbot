# SteamDealBot 🚀

A Twitter (X) bot that posts updates about video game discounts. This bot runs automatically every 6 hours using GitHub Actions.

## Features

- 🤖 Automated Twitter posting
- ⏰ Runs every 6 hours via GitHub Actions
- 🔐 Secure credential management
- 📦 Easy setup and deployment

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
✅ Twitter API credentials verified successfully!
✅ Tweet posted successfully! Tweet ID: 1234567890
📝 Tweet content: Hello world from SteamDealBot 🚀
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
│       └── bot.yml          # GitHub Actions workflow
├── .gitignore               # Git ignore file
├── bot.py                   # Main bot script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## How It Works

1. **Local Development**: The bot uses `python-dotenv` to load credentials from a `.env` file
2. **Production**: GitHub Actions uses the secrets you've configured to run the bot automatically
3. **Authentication**: Uses Tweepy with OAuth 1.0a for secure Twitter API access
4. **Scheduling**: Runs every 6 hours using cron syntax in GitHub Actions

## Customization

To customize the bot for your needs:

1. **Change the tweet content**: Modify the `message` variable in `bot.py`
2. **Adjust the schedule**: Edit the cron expression in `.github/workflows/bot.yml`
3. **Add more functionality**: Extend the `main()` function in `bot.py`

## Troubleshooting

### Common Issues

1. **"Missing required Twitter API credentials"**
   - Make sure all environment variables are set correctly
   - Check that your `.env` file is in the root directory

2. **"Error posting tweet"**
   - Verify your Twitter API credentials are correct
   - Check if your Twitter app has the necessary permissions
   - Ensure you're not hitting rate limits

3. **GitHub Actions failing**
   - Double-check that all secrets are set in GitHub
   - Make sure the secret names match exactly (case-sensitive)

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

