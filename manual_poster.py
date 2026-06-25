#!/usr/bin/env python3
"""
SteamDealBot Manual Poster
A simple script to get deals and make them easy to copy for manual posting.

Android (Termux) quick start:
  1) Install Termux + Termux:API from F‑Droid
  2) In Termux run:
       pkg update -y && pkg install -y python termux-api
       cd ~/storage/downloads/steamdealbot   # or git clone then cd
       pip install requests beautifulsoup4 pyperclip
       python manual_poster.py
  Clipboard: If pyperclip is missing or fails, this script falls back to
  `termux-clipboard-set` automatically when available.
"""

from steam_deals import SteamDealDetector, TWEET_MAX_LENGTH
import time
import sys
import os
import shutil
import subprocess
from typing import Dict, List

# Try to import pyperclip optionally; we provide fallbacks below
try:
    import pyperclip  # type: ignore
    _HAS_PYPERCLIP = True
except Exception:
    pyperclip = None  # type: ignore
    _HAS_PYPERCLIP = False

BANNER = (
    "   ____________________    __  ___ \n"
    "  / ___/_  __/ ____/   |  /  |/  / \n"
    "  \\__ \\ / / / __/ / /| | / /|_/ /  \n"
    " ___/ // / / /___/ ___ |/ /  / /   \n"
    "/_______/ _________  |___/  /_/    \n"
    "   / __ \\/ ____/   |  / /          \n"
    "  / / / / __/ / /| | / /           \n"
    " / /_/ / /___/ ___ |/ /___         \n"
    "/_____________/ _________/         \n"
    "   / __ )/ __ \\/_  __/             \n"
    "  / __  / / / / / /                \n"
    " / /_/ / /_/ / / /                 \n"
    "/_____/\\____/ /_/  ©RFNco           \n"
)

SEPARATOR = "=" * 45
BULK_COPY_COUNT = 5

def print_banner() -> None:
    print(BANNER)
    print()
    print(SEPARATOR)
    print("Manual Poster")
    print(SEPARATOR)


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to the system clipboard using the best available method.

    Order of attempts:
    1) pyperclip (if installed)
    2) Termux (Android): termux-clipboard-set
    3) macOS: pbcopy
    4) Windows: clip
    Returns True if successful, False otherwise.
    """

    # 1) pyperclip
    if _HAS_PYPERCLIP:
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            pass

    # 2) Termux (Android)
    if shutil.which("termux-clipboard-set"):
        try:
            subprocess.run(["termux-clipboard-set"], input=text, text=True, check=True)
            return True
        except Exception:
            pass

    # 3) macOS pbcopy
    if sys.platform == "darwin" and shutil.which("pbcopy"):
        try:
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return True
        except Exception:
            pass

    # 4) Windows clip
    if os.name == "nt" and shutil.which("clip"):
        try:
            subprocess.run(["clip"], input=text, text=True, check=True)
            return True
        except Exception:
            pass

    return False


def format_bulk_tweets(detector: SteamDealDetector, deals: List[Dict]) -> str:
    """Format multiple deal tweets as one clipboard-friendly batch."""
    tweets = []
    for deal in deals:
        tweets.append(detector.format_deal_tweet(deal))

    return ("\n\n" + "-" * 30 + "\n\n").join(tweets)

def main():
    print_banner()

    detector = SteamDealDetector()
    
    while True:
        print("Fetching latest Steam deals...")
        deals = detector.get_all_deals()
        
        if not deals:
            print("No deals found. Try again later.")
            continue
        
        print(f"Found {len(deals)} deals!")
        print("\n" + "=" * 50)
        
        deal_index = 0
        refresh_requested = False

        while deal_index < len(deals):
            deal = deals[deal_index]
            deal_number = deal_index + 1

            print(f"\nDeal #{deal_number}: {deal['name']}")
            print(f"Price: {deal['price']} ({deal['discount']})")
            print(f"Source: {deal['source']}")
            
            # Format the tweet
            tweet = detector.format_deal_tweet(deal)
            
            print(f"\nTweet ({len(tweet)}/{TWEET_MAX_LENGTH} characters):")
            print("-" * 30)
            print(tweet)
            print("-" * 30)
            
            # Ask user what to do
            choice = input("\nWhat would you like to do?\n"
                          "1. Copy this tweet to clipboard\n"
                          "2. Show next deal\n"
                          f"3. Copy next {BULK_COPY_COUNT} deals to clipboard\n"
                          "4. Refresh all deals\n"
                          "5. Exit\n"
                          "Choice (1-5): ").strip()
            
            if choice == '1':
                if copy_to_clipboard(tweet):
                    print("Tweet copied to clipboard! You can now paste it on 𝕏.")
                else:
                    print("Could not copy to clipboard automatically.")
                    if not _HAS_PYPERCLIP:
                        print("Tip: Install pyperclip with: pip install pyperclip")
                    if shutil.which("termux-clipboard-set"):
                        print("You can also run: echo \"<tweet>\" | termux-clipboard-set")
                    print("Please manually copy the tweet above if needed.")
                
                input("\nPress Enter to continue...")
                deal_index += 1
                
            elif choice == '2':
                deal_index += 1
                continue
                
            elif choice == '3':
                bulk_deals = deals[deal_index:deal_index + BULK_COPY_COUNT]
                bulk_tweets = format_bulk_tweets(detector, bulk_deals)

                if copy_to_clipboard(bulk_tweets):
                    print(f"{len(bulk_deals)} deal tweets copied to clipboard! You can now paste them on 𝕏.")
                else:
                    print("Could not copy the deal tweets to clipboard automatically.")
                    if not _HAS_PYPERCLIP:
                        print("Tip: Install pyperclip with: pip install pyperclip")
                    print("Please manually copy the deal tweets below if needed.")
                    print(bulk_tweets)

                input("\nPress Enter to continue...")
                deal_index += len(bulk_deals)

            elif choice == '4':
                refresh_requested = True
                break
                
            elif choice == '5':
                print("Goodbye!")
                return
                
            else:
                print("Invalid choice. Please try again.")
                continue
        
        if refresh_requested:
            continue

        # Ask if user wants to refresh
        if len(deals) > 0:
            refresh = input("\nRefresh deals? (y/n): ").strip().lower()
            if refresh != 'y':
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        print("Please check your internet connection and try again.")
