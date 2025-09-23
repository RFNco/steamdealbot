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

from steam_deals import SteamDealDetector
import time
import sys
import os
import shutil
import subprocess

# Try to import pyperclip optionally; we provide fallbacks below
try:
    import pyperclip  # type: ignore
    _HAS_PYPERCLIP = True
except Exception:
    pyperclip = None  # type: ignore
    _HAS_PYPERCLIP = False


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
                if copy_to_clipboard(tweet):
                    print("✅ Tweet copied to clipboard! You can now paste it on Twitter.")
                else:
                    print("❌ Could not copy to clipboard automatically.")
                    if not _HAS_PYPERCLIP:
                        print("Tip: Install pyperclip with: pip install pyperclip")
                    if shutil.which("termux-clipboard-set"):
                        print("You can also run: echo \"<tweet>\" | termux-clipboard-set")
                    print("Please manually copy the tweet above if needed.")
                
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
