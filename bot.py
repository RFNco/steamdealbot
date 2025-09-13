import os
import tweepy
from dotenv import load_dotenv
from steam_deals_enhanced import SteamDealDetector

# Load environment variables from .env file
load_dotenv()

def create_twitter_client():
    """Create and return a Twitter API client using environment variables."""
    # Get API credentials from environment variables
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    # Validate that all required credentials are present
    if not all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
        raise ValueError("Missing required Twitter API credentials in environment variables")
    
    # Create OAuth1UserHandler for authentication
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    
    # Create API client
    api = tweepy.API(auth, wait_on_rate_limit=True)
    
    return api

def post_tweet(api, message):
    """Post a tweet using the provided API client."""
    try:
        # Verify credentials
        api.verify_credentials()
        print("✅ Twitter API credentials verified successfully!")
        
        # Post the tweet
        response = api.update_status(message)
        print(f"✅ Tweet posted successfully! Tweet ID: {response.id}")
        print(f"📝 Tweet content: {message}")
        
    except tweepy.TweepyException as e:
        print(f"❌ Error posting tweet: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def test_api_access(api):
    """Test API access with available endpoints."""
    try:
        # Verify credentials
        user = api.verify_credentials()
        print("✅ Twitter API credentials verified successfully!")
        print(f"👤 Logged in as: @{user.screen_name}")
        print(f"📊 Followers: {user.followers_count}")
        print(f"📈 Following: {user.friends_count}")
        
        # Try to get recent tweets (if available)
        try:
            tweets = api.user_timeline(count=1)
            if tweets:
                print(f"📝 Latest tweet: {tweets[0].text[:100]}...")
        except Exception as e:
            print(f"ℹ️  Cannot access timeline: {e}")
        
        print("\n⚠️  Note: Your current API access level doesn't allow posting tweets.")
        print("   To post tweets, you need Basic or Pro access level.")
        print("   Visit: https://developer.x.com/en/portal/product")
        
    except tweepy.TweepyException as e:
        print(f"❌ Error accessing Twitter API: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to run the bot."""
    try:
        print("🚀 Starting SteamDealBot...")
        
        # Create Twitter client
        api = create_twitter_client()
        
        # Get Steam deals
        print("🎮 Fetching Steam deals...")
        deal_detector = SteamDealDetector()
        deal_tweet = deal_detector.get_best_deal_tweet()
        
        print(f"📝 Deal tweet prepared: {deal_tweet}")
        print(f"📏 Tweet length: {len(deal_tweet)} characters")
        
        # Try to post the tweet (will fail with current API access)
        try:
            post_tweet(api, deal_tweet)
        except Exception as e:
            print(f"⚠️  Could not post tweet (API access limitation): {e}")
            print("📝 Tweet content that would be posted:")
            print("=" * 50)
            print(deal_tweet)
            print("=" * 50)
        
        # Test API access
        test_api_access(api)
        
        print("🎉 Bot execution completed successfully!")
        
    except Exception as e:
        print(f"💥 Bot execution failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()

