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
import random
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
TWEET_IDEA_COUNT = 5
TWEET_IDEA_SEPARATOR = "\n\n" + "-" * 30 + "\n\n"

TWEET_IDEA_THEMES = {
    "1": (
        "Steam",
        [
            "My Steam backlog keeps growing, but honestly, finding a good deal is part of the fun. What are you playing next? #Steam #Gaming",
            "Steam sales always turn 'just browsing' into a new game in the library. What deal got you recently? #SteamDeals #Gaming",
            "There is always one game on Steam that looks too good to ignore when the discount hits. What's on your wishlist? #Steam #PCGaming",
            "A good Steam deal can change the whole weekend plan. Any hidden gems worth checking out today? #SteamDeals #Gaming",
            "The best Steam finds are the games you almost skipped, then end up playing for hours. What surprised you lately? #Steam #Gaming",
            "Steam wishlist check: what game are you waiting to grab when the price drops? #Steam #GameDeals",
            "PC gaming is dangerous when the discount is good and the reviews are glowing. What should players not miss? #SteamDeals #PCGaming",
        ],
    ),
    "2": (
        "Nintendo",
        [
            "Nintendo games have a way of turning simple ideas into unforgettable sessions. What's your comfort game? #Nintendo #Gaming",
            "Nothing beats a good Nintendo night: couch, controller, and one more round. What are you playing? #NintendoSwitch #Gaming",
            "Some Nintendo games stay fun for years because the gameplay does the heavy lifting. Which one still holds up for you? #Nintendo",
            "Nintendo fans, what's the one game you always recommend to someone new? #NintendoSwitch #Gaming",
            "A great Nintendo game does not need to be complicated to be addictive. What's your latest favorite? #Nintendo #Gaming",
            "Handheld gaming hits different when the game is easy to pick up and hard to put down. What's in your rotation? #NintendoSwitch",
            "Nintendo classics and new releases both have that 'one more level' energy. What are you replaying lately? #Nintendo #Gaming",
        ],
    ),
    "3": (
        "Gaming",
        [
            "A good game deal is dangerous for the backlog. One click and suddenly the weekend has plans. #Gaming #GameDeals",
            "Sometimes the best games are the ones you try with no expectations. What game surprised you the most? #Gaming",
            "Gaming question of the day: do you chase new releases, deep discounts, or replay old favorites? #GamingCommunity",
            "There is no such thing as 'just one more mission' when the game is really good. What kept you up late recently? #Gaming",
            "Backlog check: are you finishing games this month or adding more to the pile? #Gaming #GameDeals",
            "The best gaming moments are the ones you did not see coming. What game gave you that recently? #GamingCommunity",
            "Every gamer has that one title they recommend every chance they get. What's yours? #Gaming",
        ],
    ),
}

TWEET_IDEA_THEME_EXTRAS = {
    "1": [
        "Steam has a way of making the wishlist look like a shopping cart. What are you watching today? #SteamDeals #PCGaming",
        "Today's Steam mood: check one deal, discover five more, pretend the backlog is under control. #Steam #Gaming",
        "A deep discount is basically a side quest for your wallet. What Steam deal is tempting you right now? #SteamDeals",
        "Steam discovery question: are you more likely to buy because of price, reviews, trailer, or genre? #PCGaming",
        "Some Steam deals feel like a sign to finally try something outside your usual genre. What should players try next? #Steam",
        "Nothing tests discipline like a Steam sale and a wishlist full of games. What are you holding out for? #SteamDeals",
        "Steam hidden gem check: what game deserves more attention while it is on sale? #PCGaming #GameDeals",
        "When a Steam game drops under impulse-buy price, the backlog starts negotiating. What's your limit? #SteamDeals",
        "Steam players, what is the best cheap game you bought and ended up loving? #Steam #Gaming",
        "The dangerous part of Steam deals is when the screenshots, reviews, and price all line up. #PCGaming #SteamDeals",
        "Wishlist strategy: buy now, wait for a deeper discount, or clear the backlog first? #Steam #GameDeals",
        "Every Steam sale has one game that makes you say 'okay, maybe just this one.' Which one is yours? #SteamDeals",
        "PC gaming check-in: are you hunting discounts today or actually playing what you already bought? #Steam #Gaming",
        "A good Steam deal can make an older game feel brand new again. What classic is still worth grabbing? #PCGaming",
        "Steam weekend plan: one new deal, one old favorite, and zero promises about the backlog. #SteamDeals #Gaming",
        "The best Steam recommendations usually come from players, not algorithms. What should people check out? #Steam",
        "Deal hunters, what makes a Steam discount an instant buy for you? #SteamDeals #PCGaming",
        "Steam sale math is different: if it is 80% off, it almost feels responsible. Almost. #SteamDeals #Gaming",
    ],
    "2": [
        "Nintendo-style fun is all about games you can pick up anytime and still smile. What has that energy for you? #Nintendo",
        "Switch players, what game do you always keep installed because it just feels right? #NintendoSwitch #Gaming",
        "Nintendo nights hit different when the game is simple to start and hard to stop. What's your go-to? #Nintendo",
        "Cozy handheld session or full TV mode adventure? Nintendo fans, what are you choosing tonight? #NintendoSwitch",
        "Some games feel made for handheld play even when they are not on Switch. What would you port instantly? #Nintendo",
        "Nintendo question: do you replay comfort classics or chase new releases first? #NintendoSwitch #Gaming",
        "The best Nintendo games make losing feel like part of the fun. Which game nails that feeling? #Nintendo",
        "Party game, platformer, RPG, or cozy sim: what's the perfect Nintendo weekend genre? #NintendoSwitch",
        "Nintendo fans, what game has the best 'just one more try' loop? #Nintendo #Gaming",
        "Handheld gaming is perfect for small sessions that accidentally become two hours. What game does that to you? #NintendoSwitch",
        "Some games do not need huge graphics to be unforgettable. Nintendo has proved that for years. #Nintendo #Gaming",
        "Nintendo wishlist check: what game are you waiting to grab next? #NintendoSwitch",
        "A good Nintendo-style game is easy to learn, hard to master, and impossible to put down. What fits that? #Nintendo",
        "What is your favorite game to recommend for someone who just wants pure fun? #NintendoSwitch #Gaming",
        "Nintendo fans, are you team cozy, competitive, adventure, or chaos? #Nintendo #Gaming",
        "The best couch gaming memories usually start with 'one quick round.' What game owns that category? #NintendoSwitch",
        "Portable gaming question: what game is perfect for playing in short breaks? #Nintendo #Gaming",
        "Nintendo energy is when a game makes you smile before you even realize you played for an hour. #NintendoSwitch",
    ],
    "3": [
        "Gaming backlog status: organized library or beautiful chaos? #Gaming #GameDeals",
        "What makes you try a new game first: the trailer, the discount, the reviews, or a friend's recommendation? #Gaming",
        "A great game deal is only dangerous if you were pretending not to want it already. #GameDeals #Gaming",
        "Today's gaming question: finish one game or start three new ones? #GamingCommunity",
        "Some games become favorites because you bought them randomly on sale. What was yours? #Gaming #GameDeals",
        "The best gaming sessions are the ones that start as 'just testing it' and end hours later. #Gaming",
        "Backlog confession: are you playing your newest purchase or still returning to the same favorite? #GamingCommunity",
        "Game deals are fun because every discount feels like a new possibility. What genre are you watching? #GameDeals",
        "What is your instant-buy price for a game you have wanted for months? #Gaming #GameDeals",
        "Gaming mood check: competitive, cozy, story-heavy, or chaos with friends? #GamingCommunity",
        "A game does not need to be new to be worth discovering today. What older title still deserves love? #Gaming",
        "Sometimes the best recommendation is 'go in blind.' What game is better with no spoilers? #GamingCommunity",
        "One game, one weekend, no regrets. What are you choosing? #Gaming",
        "What is the most replayable game in your library? #GamingCommunity",
        "Deal hunters know the feeling: you came for one game and left with three. #GameDeals #Gaming",
        "The best games make time disappear. Which one did that for you recently? #Gaming",
        "Gaming hot take: a short great game can be better than a huge unfinished one. Agree? #GamingCommunity",
        "What game deserves more attention than it gets? #Gaming #GameDeals",
    ],
}

for theme_key, extra_templates in TWEET_IDEA_THEME_EXTRAS.items():
    TWEET_IDEA_THEMES[theme_key][1].extend(extra_templates)

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


def fit_tweet_text(text: str) -> str:
    if len(text) <= TWEET_MAX_LENGTH:
        return text

    trimmed = text[:TWEET_MAX_LENGTH - 3].rstrip()
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0]
    return trimmed.rstrip() + "..."


def get_deal_value(deal: Dict, key: str, fallback: str = "") -> str:
    value = deal.get(key) or fallback
    return str(value)


def generate_deal_based_ideas(theme_choice: str, deals: List[Dict]) -> List[str]:
    if theme_choice == "2":
        return []

    if not deals:
        return []

    sampled_deals = random.sample(deals, min(TWEET_IDEA_COUNT, len(deals)))
    ideas = []

    for deal in sampled_deals:
        name = get_deal_value(deal, "name", "this game")
        price = get_deal_value(deal, "price", "a new low price")
        discount = get_deal_value(deal, "discount", "on sale")
        source = get_deal_value(deal, "source", "Steam")
        steam_url = SteamDealDetector._trim_steam_url(get_deal_value(deal, "steam_url"))

        if theme_choice == "1":
            templates = [
                f"{name} is sitting at {price} with {discount} off on Steam. Backlog risk: very high.\n{steam_url}\n#SteamDeals #Gaming",
                f"Steam deal watch: {name} is {discount} off right now. Grab now or wishlist later?\n{steam_url}\n#Steam #PCGaming",
                f"{source} has {name} at {price}. Anyone played this one yet?\n{steam_url}\n#SteamDeals #Gaming",
                f"Wishlist alert: {name} dropped to {price}. This might be the sign.\n{steam_url}\n#SteamDeals #PCGaming",
                f"If you were waiting for a discount on {name}, it is now {discount} off.\n{steam_url}\n#Steam #GameDeals",
                f"Steam find of the moment: {name} at {price}. Worth adding to the weekend plan?\n{steam_url}\n#SteamDeals",
                f"{name} is on sale through {source}. Who has this one in their library already?\n{steam_url}\n#Steam #Gaming",
                f"Deal hunters, {name} is now {discount} off. Is it backlog fuel or a must-play?\n{steam_url}\n#SteamDeals #Gaming",
            ]
        elif theme_choice == "2":
            templates = [
                f"Nintendo fans, if {name} had that pick-up-and-play Switch energy, would it be on your list?\n{steam_url}\n#NintendoSwitch #Gaming",
                f"{name} feels like the kind of game that would be perfect for handheld sessions.\n{steam_url}\n#Nintendo #Gaming",
                f"Switch-style question: quick cozy sessions or long adventure nights like {name} seems built for?\n{steam_url}\n#NintendoSwitch",
                f"If {name} came to Switch, would you play it handheld or docked first?\n{steam_url}\n#NintendoSwitch #Gaming",
                f"{name} has that 'one more session' energy. Nintendo fans, would this fit your rotation?\n{steam_url}\n#Nintendo #Gaming",
                f"Portable gaming thought: {name} at {price} sounds like a solid weekend pickup.\n{steam_url}\n#NintendoSwitch",
                f"Nintendo-style question: is {name} more couch game, travel game, or late-night game?\n{steam_url}\n#Nintendo #Gaming",
                f"Imagine {name} in your handheld backlog. Instant play or wait for later?\n{steam_url}\n#NintendoSwitch",
            ]
        else:
            templates = [
                f"{name} is {discount} off at {price}. Good deal, backlog problem, or both?\n{steam_url}\n#Gaming #GameDeals",
                f"Deal question: would you try {name} because of the discount, reviews, or genre first?\n{steam_url}\n#GamingCommunity",
                f"Current gaming temptation: {name} for {price}. What game deal got your attention today?\n{steam_url}\n#Gaming #GameDeals",
                f"{name} is on sale now. Is this the kind of deal you grab fast or research first?\n{steam_url}\n#Gaming #GameDeals",
                f"Backlog test: {name} at {price}. Are you adding it or staying disciplined?\n{steam_url}\n#GamingCommunity",
                f"Game deal spotlight: {name} is {discount} off. Who should check this one out?\n{steam_url}\n#GameDeals",
                f"Would you rather jump into {name} tonight or save it for the weekend?\n{steam_url}\n#Gaming",
                f"{name} caught my eye at {price}. What sale game is calling your name today?\n{steam_url}\n#Gaming #GameDeals",
            ]

        ideas.append(random.choice(templates))

    if len(sampled_deals) >= 2:
        first, second = random.sample(sampled_deals, 2)
        first_name = get_deal_value(first, "name", "Game 1")
        second_name = get_deal_value(second, "name", "Game 2")
        first_url = SteamDealDetector._trim_steam_url(get_deal_value(first, "steam_url"))
        second_url = SteamDealDetector._trim_steam_url(get_deal_value(second, "steam_url"))
        ideas.append(
            f"Quick pick: would you rather grab {first_name} or {second_name} while both are on sale?\n{first_url}\n{second_url}\n#Gaming #GameDeals"
        )

    return ideas


def generate_tweet_ideas(theme_choice: str, deals: List[Dict]) -> List[str]:
    _, templates = TWEET_IDEA_THEMES[theme_choice]
    ideas = generate_deal_based_ideas(theme_choice, deals)
    fallback_ideas = random.sample(templates, min(TWEET_IDEA_COUNT, len(templates)))
    ideas.extend(fallback_ideas)
    random.shuffle(ideas)
    return [fit_tweet_text(idea) for idea in ideas[:TWEET_IDEA_COUNT]]


def show_tweet_ideas_menu(deals: List[Dict]) -> None:
    print("\nChoose a tweet idea theme:")
    for theme_key, (theme_name, _) in TWEET_IDEA_THEMES.items():
        print(f"{theme_key}. {theme_name}")

    theme_choice = input("Theme choice: ").strip()
    if theme_choice not in TWEET_IDEA_THEMES:
        print("Invalid theme choice.")
        return

    theme_name, _ = TWEET_IDEA_THEMES[theme_choice]
    ideas = generate_tweet_ideas(theme_choice, deals)

    print(f"\n{theme_name} tweet ideas:")
    print("Using current Steam deal data plus reusable templates.")
    print("-" * 30)
    for index, idea in enumerate(ideas, 1):
        print(f"\nIdea #{index} ({len(idea)}/{TWEET_MAX_LENGTH} characters):")
        print(idea)

    copy_choice = input("\nCopy all ideas to clipboard? (y/n): ").strip().lower()
    if copy_choice != "y":
        return

    ideas_text = TWEET_IDEA_SEPARATOR.join(ideas)
    if copy_to_clipboard(ideas_text):
        print("Tweet ideas copied to clipboard!")
    else:
        print("Could not copy tweet ideas to clipboard automatically.")
        print("Please manually copy the ideas above if needed.")

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
                          "4. Generate themed tweet ideas\n"
                          "5. Refresh deals and idea sources\n"
                          "6. Exit\n"
                          "Choice (1-6): ").strip()
            
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
                show_tweet_ideas_menu(deals)
                input("\nPress Enter to continue...")
                continue

            elif choice == '5':
                refresh_requested = True
                break
                
            elif choice == '6':
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
