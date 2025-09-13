#!/usr/bin/env python3
"""
SteamDealBot Manual Poster
A simple script to get deals and make them easy to copy for manual posting.
"""

from steam_deals import SteamDealDetector
import pyperclip
import time

def main():
    print("🎮 SteamDealBot Manual Poster")
    print("=" * 50)
    
    detector = SteamDealDetector()
    
    while True:
        print("\n🔄 Fetching latest Steam deals...")
        deals = detector.get_all_deals()
        
        if not deals:
            print("❌ No deals found. Try again later.")
            continue
        
        print(f"\n✅ Found {len(deals)} deals!")
        print("\n" + "=" * 50)
        
        for i, deal in enumerate(deals, 1):
            print(f"\n🎮 Deal #{i}: {deal['name']}")
            print(f"💰 Price: {deal['price']} ({deal['discount']})")
            print(f"🏷️ Source: {deal['source']}")
            
            # Format the tweet
            tweet = detector.format_deal_tweet(deal)
            
            print(f"\n📝 Tweet ({len(tweet)} characters):")
            print("-" * 30)
            print(tweet)
            print("-" * 30)
            
            # Ask user what to do
            choice = input("\nWhat would you like to do?\n"
                          "1. Copy this tweet to clipboard\n"
                          "2. Show next deal\n"
                          "3. Refresh all deals\n"
                          "4. Exit\n"
                          "Choice (1-4): ").strip()
            
            if choice == '1':
                try:
                    pyperclip.copy(tweet)
                    print("✅ Tweet copied to clipboard! You can now paste it on Twitter.")
                except ImportError:
                    print("❌ pyperclip not installed. Install it with: pip install pyperclip")
                    print("Or manually copy the tweet above.")
                except Exception as e:
                    print(f"❌ Error copying to clipboard: {e}")
                    print("Please manually copy the tweet above.")
                
                input("\nPress Enter to continue...")
                
            elif choice == '2':
                continue
                
            elif choice == '3':
                break
                
            elif choice == '4':
                print("👋 Goodbye!")
                return
                
            else:
                print("❌ Invalid choice. Please try again.")
        
        # Ask if user wants to refresh
        if len(deals) > 0:
            refresh = input("\n🔄 Refresh deals? (y/n): ").strip().lower()
            if refresh != 'y':
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your internet connection and try again.")
