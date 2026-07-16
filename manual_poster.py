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

from steam_deals import (
    SteamDealDetector,
    TWEET_MAX_LENGTH,
    DEAL_MODE_CONFIGS,
    DEAL_CATEGORY_CONFIGS,
)
from buffer_client import BufferClient
from news_feeds import (
    DEFAULT_NEWS_LIMIT,
    fetch_news_pool,
    format_news_tweets,
    format_published_age,
    media_badge,
    save_news_image,
)
import json
import re
import time
import sys
import os
import random
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

# Try to import pyperclip optionally; we provide fallbacks below
try:
    import pyperclip  # type: ignore
    _HAS_PYPERCLIP = True
except Exception:
    pyperclip = None  # type: ignore
    _HAS_PYPERCLIP = False

VERSION = "v2.1.7"

# Lazily created when BUFFER_API_KEY is set in .env
_BUFFER_CLIENT: Optional[BufferClient] = None
_BUFFER_CHECKED = False

POSTED_HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".manual_poster_posted.json",
)
POSTED_DEPRIORITIZE_DAYS = 14
POSTED_HISTORY_MAX_ENTRIES = 300

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
COLOR_ENABLED = os.environ.get("STEAMDEALBOT_NO_COLOR") != "1"

# Named ANSI foreground colors — pick from here when editing THEME below.
# Codes follow the standard 16-color terminal palette (actual shade depends on your theme).
ANSI_COLORS = {
  # 30-37: normal
    "black": "\033[30m",          # black
    "red": "\033[31m",            # red
    "green": "\033[32m",          # green
    "yellow": "\033[33m",         # yellow / amber
    "blue": "\033[34m",           # blue
    "magenta": "\033[35m",        # magenta / purple
    "cyan": "\033[36m",           # cyan
    "white": "\033[37m",          # white
  # 90-97: bright (common in modern terminals)
    "gray": "\033[90m",           # bright black → usually gray
    "bright_red": "\033[91m",    # bright red
    "bright_green": "\033[92m",   # bright green
    "bright_yellow": "\033[93m",  # bright yellow
    "bright_blue": "\033[94m",    # bright blue
    "bright_magenta": "\033[95m", # bright magenta
    "bright_cyan": "\033[96m",    # bright cyan
    "bright_white": "\033[97m",   # bright white
    "reset": "\033[0m",            # reset to default
}

THEME = {
    # UI role → ANSI_COLORS name (change the value to any key from ANSI_COLORS above)
    "banner": ANSI_COLORS["bright_yellow"],   # ASCII banner lines
    "title": ANSI_COLORS["bright_cyan"],      # section titles, Manual Poster header
    "label": ANSI_COLORS["bright_yellow"],    # input prompts
    "value": ANSI_COLORS["bright_white"],     # main body text, game names
    "muted": ANSI_COLORS["gray"],             # hints, separators, deal numbers
    "tweet": ANSI_COLORS["bright_yellow"],    # tweet preview first line
    "success": ANSI_COLORS["bright_green"],   # copied / OK messages
    "warning": ANSI_COLORS["yellow"],         # Posted tag, soft warnings
    "error": ANSI_COLORS["bright_red"],       # errors
    "reset": ANSI_COLORS["reset"],
}

# Menu colors and highlights — change styles here for every manual poster menu.
# Values must be keys from THEME above (which point at ANSI_COLORS names).
MENU_STYLES = {
    "header": "muted",       # e.g. "What would you like to do?" → gray
    "prompt": "label",       # e.g. "Choice (1-8...)" → bright yellow
    "number": "muted",       # e.g. "1. " → gray
    "option": "value",       # default option label → bright white
    "description": "muted",  # trailing hints → gray
    # Per-menu option colors (THEME role names — see ANSI_COLORS for the actual shade)
    "highlights": {
        "steam": {
            1: "warning",    # Copy tweet
            3: "title",      # Search by keyword
            4: "success",    # Refresh
        },
        "steam_buffer": {
            1: "warning",    # Copy tweet
            2: "warning",    # Add to Buffer queue
            4: "title",      # Search by keyword
            5: "success",    # Refresh
        },
        "nintendo": {
            1: "warning",    # Copy tweet
            3: "title",      # Search by keyword
            4: "success",    # Refresh
            5: "muted",      # Back to Steam
        },
        "nintendo_buffer": {
            1: "warning",    # Copy tweet
            2: "warning",    # Add to Buffer queue
            4: "title",      # Search by keyword
            5: "success",    # Refresh
            6: "muted",      # Back to Steam
        },
    },
}

# Reusable themed tweet ideas (Collections & ideas). Before each version tag, add or
# swap a few lines in TWEET_IDEA_THEME_EXTRAS, then bump TWEET_IDEA_LAST_ROLLED_VERSION
# (and the matching version on ROADMAP.md) to match the release you are tagging.
TWEET_IDEA_LAST_ROLLED_VERSION = "v2.1.7"
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
        "New week, new Steam deals: are you hunting discounts or finally clearing the backlog? #Steam #PCGaming",
        "That moment when a wishlisted game finally hits the price you wanted. What are you waiting on? #SteamDeals",
        "Steam players: buy the comfort replay or gamble on something totally new? #Steam #Gaming",
        "Buffer-ready Steam question: which deal on your wishlist actually deserves a queue slot today? #SteamDeals",
        "Steam check: is the best find the big-name discount or the under-$10 surprise? #Steam #PCGaming",
        "Sale-day honesty: did you open Steam to play, or to browse deals again? #SteamDeals #Gaming",
        "One wishlisted game is on a real discount — grab it, or keep waiting for 'even lower'? #Steam #GameDeals",
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
        "Rainy day, cozy game, no plans to leave the couch. What is your perfect Switch combo? #Nintendo #Gaming",
        "Some Switch games are worth keeping installed forever. What never gets deleted from yours? #NintendoSwitch",
        "Nintendo fans: quick arcade session or settle in for a long RPG night? #Nintendo #Gaming",
        "eShop temptation check: grab the discount now or wait for an even deeper cut? #NintendoDeals #NintendoSwitch",
        "Switch deal night: one sale game, one comfort install, and no promises about sleep. #Nintendo #Gaming",
        "eShop scroll tip: if the trailer makes you smile twice, it might be worth the sale price. #NintendoDeals",
        "Handheld check: what Switch game still earns a permanent home-screen slot? #NintendoSwitch #Gaming",
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
        "Weekend gaming plan: one new pickup, one old favorite, and zero guilt about the backlog. #Gaming",
        "What discount percentage makes you stop thinking and start buying? #GameDeals #GamingCommunity",
        "Gaming check-in: what are you playing tonight and why did you pick it? #Gaming",
        "Queue vs backlog: schedule one post-worthy deal or keep hunting for a better find? #GameDeals #Gaming",
        "Honest gaming mood: hype post, chill rec, or 'would you buy this?' poll energy tonight? #GamingCommunity",
        "Timeline mix idea: one deal, one news take, one 'what are you playing?' — what wins today? #Gaming",
        "If your feed only showed one game recommendation today, what should it be? #GamingCommunity #GameDeals",
    ],
}
for theme_key, extra_templates in TWEET_IDEA_THEME_EXTRAS.items():
    TWEET_IDEA_THEMES[theme_key][1].extend(extra_templates)


def color_text(text: str, style: str) -> str:
    if not COLOR_ENABLED:
        return text
    return f"{THEME[style]}{text}{THEME['reset']}"


def themed_print(text: str, style: str = "value") -> None:
    print(color_text(text, style))


def themed_input(prompt: str, style: str = "label") -> str:
    return input(color_text(prompt, style))


def print_separator(length: int = 45) -> None:
    themed_print("=" * length, "muted")


def print_label_value(label: str, value: str) -> None:
    print(color_text(f"{label}: ", "label") + color_text(value, "value"))


def print_muted_label_value(label: str, value: str) -> None:
    print(color_text(f"{label}: {value}", "muted"))


def menu_option_style(
    number: int,
    menu_type: str = "default",
    style: Optional[str] = None,
) -> str:
    if style:
        return style

    highlights = MENU_STYLES["highlights"]
    if menu_type in highlights:
        return highlights[menu_type].get(number, MENU_STYLES["option"])
    return highlights.get(number, MENU_STYLES["option"])


def format_menu_option(
    number: int,
    text: str,
    description: str = "",
    style: Optional[str] = None,
    menu_type: str = "default",
) -> str:
    option_style = menu_option_style(number, menu_type=menu_type, style=style)
    line = (
        color_text(f"{number}. ", MENU_STYLES["number"])
        + color_text(text, option_style)
    )
    if description:
        line += color_text(f" - {description}", MENU_STYLES["description"])
    return line


def prompt_menu_choice(
    header: str,
    options: List[tuple],
    prompt: str,
    menu_type: str = "default",
) -> str:
    """Build a numbered menu from (number, label) or (number, label, description) tuples."""
    message = "\n" + color_text(header, MENU_STYLES["header"])
    for option in options:
        if len(option) == 2:
            number, text = option
            message += "\n" + format_menu_option(number, text, menu_type=menu_type)
        else:
            number, text, description = option
            message += "\n" + format_menu_option(
                number, text, description=description, menu_type=menu_type
            )
    message += "\n" + color_text(prompt, MENU_STYLES["prompt"])
    return input(message).strip()


def print_menu_section_header(title: str, subtitle: str = "") -> None:
    themed_print(f"\n{title}", "title")
    if subtitle:
        themed_print(subtitle, MENU_STYLES["description"])
    themed_print("-" * 30, "muted")

def print_banner() -> None:
    signature = "©RFNco"
    for line in BANNER.splitlines():
        if signature in line:
            before, after = line.split(signature, 1)
            print(
                color_text(before, "banner")
                + color_text(signature, "title")
                + color_text(after, "banner")
            )
        else:
            themed_print(line, "banner")
    print()
    print_separator(len(SEPARATOR))
    themed_print(f"Manual Poster - {VERSION}", "title")
    if get_buffer_client():
        themed_print("Buffer queue: ready (API key loaded)", "muted")
    print_separator(len(SEPARATOR))


def get_buffer_client() -> Optional[BufferClient]:
    """Return a shared Buffer client when BUFFER_API_KEY is configured."""
    global _BUFFER_CLIENT, _BUFFER_CHECKED
    if _BUFFER_CHECKED:
        return _BUFFER_CLIENT
    _BUFFER_CHECKED = True
    _BUFFER_CLIENT = BufferClient.from_env()
    return _BUFFER_CLIENT


def send_tweet_to_buffer(text: str) -> bool:
    """Queue one tweet in Buffer. Returns True on success."""
    client = get_buffer_client()
    if client is None:
        themed_print(
            "Buffer is not configured. Add BUFFER_API_KEY to your .env file.",
            "warning",
        )
        return False

    themed_print("Sending to Buffer queue...", "muted")
    result = client.add_text_to_queue(text)
    if result.ok:
        themed_print(result.message, "success")
        return True
    themed_print(f"Buffer queue failed: {result.message}", "error")
    if "queue" in result.message.lower() and "full" in result.message.lower():
        themed_print(
            "Your Buffer queue may be full (free plans are often capped at 10).",
            "warning",
        )
    return False


def prompt_buffer_after_copy(texts: List[str]) -> None:
    """Optional follow-up: send copied tweet(s) to Buffer after clipboard copy."""
    if not get_buffer_client() or not texts:
        return
    if len(texts) == 1:
        prompt = "\nAdd this tweet to Buffer queue too? (y/Enter=skip): "
    else:
        prompt = (
            f"\nAdd these {len(texts)} tweets to Buffer queue too? "
            f"(y/Enter=skip, uses {len(texts)} queue slots): "
        )
    choice = themed_input(prompt, "muted").strip().lower()
    if choice not in ("y", "yes"):
        return
    ok_count = 0
    for index, text in enumerate(texts, 1):
        if len(texts) > 1:
            themed_print(f"Buffering tweet {index}/{len(texts)}...", "muted")
        if send_tweet_to_buffer(text):
            ok_count += 1
        else:
            break
    if len(texts) > 1 and ok_count:
        themed_print(
            f"Queued {ok_count}/{len(texts)} tweet(s) in Buffer.",
            "success" if ok_count == len(texts) else "warning",
        )


def print_tweet_preview(tweet: str) -> None:
    lines = tweet.splitlines()
    for index, line in enumerate(lines):
        if not line:
            print()
        elif index == 0:
            themed_print(line, "tweet")
        elif index == 1:
            themed_print(line, "value")
        elif line.startswith("http://") or line.startswith("https://"):
            themed_print(line, "value")
        elif line.startswith("#"):
            themed_print(line, "value")
        else:
            themed_print(line, "value")


def print_tweet_idea(index: int, idea: str) -> None:
    print(
        color_text(f"\nIdea #{index}: ", "title")
        + color_text(f"{len(idea)}/{TWEET_MAX_LENGTH} characters", "muted")
    )
    for line in idea.splitlines():
        if line:
            themed_print(line, "value")
        else:
            print()


def _deal_key(deal: Dict) -> str:
    nsuid = str(deal.get("nsuid") or "").strip()
    if nsuid.isdigit():
        return f"nintendo:{nsuid}"
    steam_url = deal.get("steam_url", "")
    match = re.search(r"/app/(\d+)", steam_url)
    if match:
        return match.group(1)
    return deal.get("name", "").strip().lower()


def load_posted_history() -> Dict[str, Dict]:
    if not os.path.exists(POSTED_HISTORY_FILE):
        return {}

    try:
        with open(POSTED_HISTORY_FILE, encoding="utf-8") as history_file:
            data = json.load(history_file)
    except (OSError, json.JSONDecodeError):
        return {}

    entries = data.get("entries", {})
    if isinstance(entries, list):
        entries = {
            _deal_key(entry): entry
            for entry in entries
            if isinstance(entry, dict)
        }
    return entries if isinstance(entries, dict) else {}


def save_posted_history(history: Dict[str, Dict]) -> None:
    sorted_entries = sorted(
        history.values(),
        key=lambda entry: entry.get("posted_at", 0),
        reverse=True,
    )[:POSTED_HISTORY_MAX_ENTRIES]
    trimmed_history = {_deal_key(entry): entry for entry in sorted_entries}

    with open(POSTED_HISTORY_FILE, "w", encoding="utf-8") as history_file:
        json.dump({"entries": trimmed_history}, history_file, indent=2)


def mark_deal_posted(deal: Dict) -> None:
    history = load_posted_history()
    history[_deal_key(deal)] = {
        "name": deal.get("name", ""),
        "steam_url": deal.get("steam_url", ""),
        "price": deal.get("price", ""),
        "posted_at": time.time(),
    }
    save_posted_history(history)


def mark_deals_posted(deals: List[Dict]) -> None:
    if not deals:
        return

    history = load_posted_history()
    posted_at = time.time()
    for deal in deals:
        history[_deal_key(deal)] = {
            "name": deal.get("name", ""),
            "steam_url": deal.get("steam_url", ""),
            "price": deal.get("price", ""),
            "posted_at": posted_at,
        }
    save_posted_history(history)


def deprioritize_posted_deals(deals: List[Dict]) -> Tuple[List[Dict], int]:
    history = load_posted_history()
    if not history:
        return deals, 0

    cutoff = time.time() - (POSTED_DEPRIORITIZE_DAYS * 86400)
    fresh_deals = []
    posted_deals = []

    for deal in deals:
        entry = history.get(_deal_key(deal))
        if entry and entry.get("posted_at", 0) >= cutoff:
            posted_deals.append(deal)
        else:
            fresh_deals.append(deal)

    if posted_deals:
        random.shuffle(posted_deals)

    return fresh_deals + posted_deals, len(posted_deals)


def is_recently_posted(deal: Dict) -> bool:
    history = load_posted_history()
    entry = history.get(_deal_key(deal))
    if not entry:
        return False

    cutoff = time.time() - (POSTED_DEPRIORITIZE_DAYS * 86400)
    return entry.get("posted_at", 0) >= cutoff


def print_deal_header(deal_number: int, deal: Dict) -> None:
    header = color_text(f"\nDeal #{deal_number}", "muted")
    if is_recently_posted(deal):
        header += color_text(" Posted", "warning")
    print(header)
    themed_print(deal["name"], "value")


def parse_result_selection(text: str, max_index: int) -> List[int]:
    """Parse selections like 3, 3,7,12, 3 7, or 3-5 into valid result numbers."""
    indices: List[int] = []

    for part in re.split(r"[,\s]+", text.strip()):
        if not part:
            continue

        if "-" in part:
            range_parts = part.split("-", 1)
            if len(range_parts) != 2:
                return []
            try:
                start_index = int(range_parts[0])
                end_index = int(range_parts[1])
            except ValueError:
                return []

            if start_index > end_index:
                start_index, end_index = end_index, start_index
            indices.extend(range(start_index, end_index + 1))
            continue

        try:
            indices.append(int(part))
        except ValueError:
            return []

    unique_indices: List[int] = []
    seen_indices = set()
    for index in indices:
        if index < 1 or index > max_index:
            return []
        if index not in seen_indices:
            seen_indices.add(index)
            unique_indices.append(index)

    return unique_indices


def print_collection_results(title: str, results: List[Dict]) -> None:
    themed_print(f"\n{title}:", "title")
    themed_print("-" * 30, "muted")
    for index, deal in enumerate(results, 1):
        posted_tag = color_text(" Posted", "warning") if is_recently_posted(deal) else ""
        price_text = deal.get("price")
        price_suffix = color_text(f" {price_text}", "muted") if price_text else ""
        print(
            color_text(f"{index}. ", "muted")
            + color_text(deal["name"], "value")
            + color_text(f" {deal['discount']}", "muted")
            + price_suffix
            + posted_tag
        )


def copy_collection_results(
    detector: SteamDealDetector,
    results: List[Dict],
    indices: List[int],
    tweet_formatter=None,
    track_posted: bool = True,
) -> bool:
    if tweet_formatter is None:
        tweet_formatter = detector.format_deal_tweet

    selected_deals = [results[index - 1] for index in indices]

    if len(selected_deals) == 1:
        selected_tweet = tweet_formatter(selected_deals[0])
        copied = copy_to_clipboard(selected_tweet)
        preview_text = selected_tweet
        success_message = f"Pick #{indices[0]} copied to clipboard!"
    else:
        preview_text = ("\n\n" + "-" * 30 + "\n\n").join(
            tweet_formatter(deal) for deal in selected_deals
        )
        copied = copy_to_clipboard(preview_text)
        index_list = ", ".join(str(index) for index in indices)
        success_message = (
            f"Picks {index_list} copied to clipboard ({len(selected_deals)} tweets)!"
        )

    if copied:
        if track_posted:
            mark_deals_posted(selected_deals)
        themed_print(success_message, "success")
        if track_posted:
            themed_print("Marked as posted for more variety on future refreshes.", "muted")
        tweets = [tweet_formatter(deal) for deal in selected_deals]
        prompt_buffer_after_copy(tweets)
    else:
        themed_print("Could not copy the selected pick(s) automatically.", "error")
        themed_print("Please manually copy the selected tweet(s) above if needed.", "warning")

    print()
    themed_print("-" * 30, "muted")
    print_tweet_preview(preview_text)
    themed_print("-" * 30, "muted")
    return copied


def show_collection_copy_loop(
    detector: SteamDealDetector,
    title: str,
    results: List[Dict],
    tweet_formatter=None,
    track_posted: bool = True,
    allow_search_again: bool = False,
) -> str:
    """Show ranked results and copy tweets.

    Returns "search_again" when the user chooses 0 (only if allow_search_again),
    otherwise "back".
    """
    if tweet_formatter is None:
        tweet_formatter = detector.format_deal_tweet

    posted_count = 0
    if track_posted:
        results, posted_count = deprioritize_posted_deals(results)
    if not results:
        themed_print(f"No deals found for {title}.", "warning")
        return "back"

    if posted_count:
        themed_print(
            f"Moved {posted_count} recently copied game"
            f"{'s' if posted_count != 1 else ''} to the end for more variety.",
            "muted",
        )

    print_collection_results(title, results)

    while True:
        prompt = (
            f"\nCopy which pick(s)? (1-{len(results)}, e.g. 3,7 / 3-5"
        )
        if allow_search_again:
            prompt += ", 0=new search"
        prompt += ", Enter=back): "
        copy_choice = themed_input(prompt).strip()
        if not copy_choice:
            return "back"
        if allow_search_again and copy_choice == "0":
            return "search_again"

        indices = parse_result_selection(copy_choice, len(results))
        if not indices:
            themed_print("Invalid selection. Use numbers like 3, 3,7, or 3-5.", "error")
            continue

        copy_collection_results(
            detector,
            results,
            indices,
            tweet_formatter=tweet_formatter,
            track_posted=track_posted,
        )
        if allow_search_again:
            themed_print(
                "Copy more from this list, 0 = search again, or press Enter to go back.",
                "muted",
            )
        else:
            themed_print("Copy more from this collection, or press Enter to go back.", "muted")


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


def format_tweet_idea_spacing(idea: str) -> str:
    lines = idea.splitlines()
    formatted_lines = []

    for line in lines:
        is_link = line.startswith("http://") or line.startswith("https://")
        is_hashtag = line.startswith("#")
        previous_line = formatted_lines[-1] if formatted_lines else ""
        previous_is_link = previous_line.startswith("http://") or previous_line.startswith("https://")
        needs_spacing = (is_hashtag and not previous_is_link) or (is_link and not previous_is_link)
        if needs_spacing and previous_line != "":
            formatted_lines.append("")
        formatted_lines.append(line)

    return "\n".join(formatted_lines)


def get_deal_value(deal: Dict, key: str, fallback: str = "") -> str:
    value = deal.get(key) or fallback
    return str(value)


def deal_share_url(deal: Dict) -> str:
    """Prefer a trimmed Nintendo storefront URL when the deal is from eShop."""
    url = get_deal_value(deal, "steam_url")
    nsuid = deal.get("nsuid")
    source = get_deal_value(deal, "source").lower()
    if nsuid or "nintendo" in source or "nintendo.com" in url or "ec.nintendo.com" in url:
        return SteamDealDetector._trim_nintendo_url(url, nsuid)
    return SteamDealDetector._trim_steam_url(url)


def generate_deal_based_ideas(theme_choice: str, deals: List[Dict]) -> List[str]:
    if not deals:
        return []

    sampled_deals = random.sample(deals, min(TWEET_IDEA_COUNT, len(deals)))
    ideas = []

    for deal in sampled_deals:
        name = get_deal_value(deal, "name", "this game")
        price = get_deal_value(deal, "price", "a new low price")
        discount = get_deal_value(deal, "discount", "on sale")
        source = get_deal_value(deal, "source", "Steam")
        share_url = deal_share_url(deal)

        if theme_choice == "1":
            templates = [
                f"{name} is sitting at {price} with {discount} off on Steam. Backlog risk: very high.\n{share_url}\n#SteamDeals #Gaming",
                f"Steam deal watch: {name} is {discount} off right now. Grab now or wishlist later?\n{share_url}\n#Steam #PCGaming",
                f"{source} has {name} at {price}. Anyone played this one yet?\n{share_url}\n#SteamDeals #Gaming",
                f"Wishlist alert: {name} dropped to {price}. This might be the sign.\n{share_url}\n#SteamDeals #PCGaming",
                f"If you were waiting for a discount on {name}, it is now {discount} off.\n{share_url}\n#Steam #GameDeals",
                f"Steam find of the moment: {name} at {price}. Worth adding to the weekend plan?\n{share_url}\n#SteamDeals",
                f"{name} is on sale through {source}. Who has this one in their library already?\n{share_url}\n#Steam #Gaming",
                f"Deal hunters, {name} is now {discount} off. Is it backlog fuel or a must-play?\n{share_url}\n#SteamDeals #Gaming",
            ]
        elif theme_choice == "2":
            templates = [
                f"{name} is {discount} on Nintendo eShop US at {price}. Instant buy or wait for the next sale?\n{share_url}\n#NintendoDeals #NintendoSwitch",
                f"Switch deal watch: {name} dropped to {price}. Who is grabbing this one?\n{share_url}\n#NintendoSwitch #Gaming",
                f"{name} is on sale right now ({discount}). Handheld sessions incoming?\n{share_url}\n#NintendoDeals #Nintendo",
                f"eShop find: {name} for {price}. Quick cozy night or long adventure save?\n{share_url}\n#NintendoSwitch #Gaming",
                f"If {name} was on your wishlist, {discount} off at {price} is hard to ignore.\n{share_url}\n#NintendoDeals #NintendoSwitch",
                f"Portable gaming temptation: {name} is {discount} on the eShop. Add it or stay disciplined?\n{share_url}\n#NintendoSwitch",
                f"{source} has {name} at {price}. Docked first or handheld first?\n{share_url}\n#Nintendo #Gaming",
                f"Nintendo deal spotlight: {name} is {discount} off. Who should check this one out?\n{share_url}\n#NintendoDeals #Gaming",
            ]
        else:
            templates = [
                f"{name} is {discount} off at {price}. Good deal, backlog problem, or both?\n{share_url}\n#Gaming #GameDeals",
                f"Deal question: would you try {name} because of the discount, reviews, or genre first?\n{share_url}\n#GamingCommunity",
                f"Current gaming temptation: {name} for {price}. What game deal got your attention today?\n{share_url}\n#Gaming #GameDeals",
                f"{name} is on sale now. Is this the kind of deal you grab fast or research first?\n{share_url}\n#Gaming #GameDeals",
                f"Backlog test: {name} at {price}. Are you adding it or staying disciplined?\n{share_url}\n#GamingCommunity",
                f"Game deal spotlight: {name} is {discount} off. Who should check this one out?\n{share_url}\n#GameDeals",
                f"Would you rather jump into {name} tonight or save it for the weekend?\n{share_url}\n#Gaming",
                f"{name} caught my eye at {price}. What sale game is calling your name today?\n{share_url}\n#Gaming #GameDeals",
            ]

        ideas.append(random.choice(templates))

    if len(sampled_deals) >= 2:
        first, second = random.sample(sampled_deals, 2)
        first_name = get_deal_value(first, "name", "Game 1")
        second_name = get_deal_value(second, "name", "Game 2")
        first_url = deal_share_url(first)
        second_url = deal_share_url(second)
        if theme_choice == "2":
            ideas.append(
                f"Quick Switch pick: {first_name} or {second_name} while both are on sale?\n{first_url}\n{second_url}\n#NintendoDeals #NintendoSwitch"
            )
        else:
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
    return [
        fit_tweet_text(format_tweet_idea_spacing(idea))
        for idea in ideas[:TWEET_IDEA_COUNT]
    ]


def show_tweet_ideas_menu(detector: SteamDealDetector, deals: List[Dict]) -> None:
    themed_print("\nChoose a tweet idea theme:", "value")
    for theme_key, (theme_name, _) in TWEET_IDEA_THEMES.items():
        print(color_text(f"{theme_key}. ", "muted") + color_text(theme_name, "value"))

    theme_choice = themed_input("Theme choice: ").strip()
    if theme_choice not in TWEET_IDEA_THEMES:
        themed_print("Invalid theme choice.", "error")
        return

    theme_name, _ = TWEET_IDEA_THEMES[theme_choice]
    idea_deals = deals
    status_line = "Using current Steam deal data plus reusable templates."

    if theme_choice == "2":
        themed_print("Fetching Nintendo eShop US deals for tweet ideas...", "muted")
        idea_deals = detector.get_nintendo_us_deals(count=max(TWEET_IDEA_COUNT * 2, 10))
        if idea_deals:
            status_line = "Using current Nintendo eShop deals plus reusable templates."
        else:
            themed_print(
                "No Nintendo deals right now — falling back to reusable templates only.",
                "warning",
            )
            status_line = "Using reusable Nintendo templates only."

    ideas = generate_tweet_ideas(theme_choice, idea_deals)

    themed_print(f"\n{theme_name} tweet ideas:", "title")
    themed_print(status_line, "value")
    themed_print("-" * 30, "muted")
    for index, idea in enumerate(ideas, 1):
        print_tweet_idea(index, idea)

    copy_choice = themed_input("\nCopy which idea? (1-5, Enter=cancel): ").strip()
    if not copy_choice:
        return

    try:
        idea_index = int(copy_choice)
    except ValueError:
        themed_print("Invalid idea number.", "error")
        return

    if idea_index < 1 or idea_index > len(ideas):
        themed_print("Invalid idea number.", "error")
        return

    selected_idea = ideas[idea_index - 1]
    if copy_to_clipboard(selected_idea):
        themed_print(f"Idea #{idea_index} copied to clipboard!", "success")
        prompt_buffer_after_copy([selected_idea])
    else:
        themed_print("Could not copy that tweet idea to clipboard automatically.", "error")
        themed_print("Please manually copy the selected idea above if needed.", "warning")


def show_deal_modes_menu(detector: SteamDealDetector) -> None:
    mode_keys = list(DEAL_MODE_CONFIGS.keys())

    while True:
        print_menu_section_header(
            "Deal modes",
            "Build a thread from a focused sale slice.",
        )
        for index, mode_key in enumerate(mode_keys, 1):
            config = DEAL_MODE_CONFIGS[mode_key]
            print(format_menu_option(index, config["label"], description=config["blurb"]))

        choice = themed_input("\nChoose a deal mode (Enter=back): ", MENU_STYLES["prompt"]).strip()
        if not choice:
            return

        try:
            mode_index = int(choice)
        except ValueError:
            themed_print("Invalid deal mode number.", "error")
            continue

        if mode_index < 1 or mode_index > len(mode_keys):
            themed_print("Invalid deal mode number.", "error")
            continue

        mode_key = mode_keys[mode_index - 1]
        config = DEAL_MODE_CONFIGS[mode_key]
        deals = detector.get_deal_mode_deals(mode_key)
        show_collection_copy_loop(detector, config["label"], deals)


def show_deal_categories_menu(detector: SteamDealDetector) -> None:
    category_keys = list(DEAL_CATEGORY_CONFIGS.keys())

    while True:
        print_menu_section_header(
            "Categories",
            "Browse discounted games by genre or price.",
        )
        for index, category_key in enumerate(category_keys, 1):
            config = DEAL_CATEGORY_CONFIGS[category_key]
            print(format_menu_option(index, config["label"], description=config["blurb"]))

        choice = themed_input("\nChoose a category (Enter=back): ", MENU_STYLES["prompt"]).strip()
        if not choice:
            return

        try:
            category_index = int(choice)
        except ValueError:
            themed_print("Invalid category number.", "error")
            continue

        if category_index < 1 or category_index > len(category_keys):
            themed_print("Invalid category number.", "error")
            continue

        category_key = category_keys[category_index - 1]
        config = DEAL_CATEGORY_CONFIGS[category_key]
        deals = detector.get_category_deals(category_key)
        show_collection_copy_loop(detector, config["label"], deals)


def show_news_menu() -> None:
    """Browse RSS/Atom gaming headlines and copy a news tweet draft."""
    pool: List[Dict] = []
    fetch_errors: List[str] = []
    offset = 0

    def load_pool(force: bool = False) -> bool:
        nonlocal pool, fetch_errors, offset
        if pool and not force:
            return True
        themed_print("\nFetching gaming news from RSS feeds...", "muted")
        try:
            pool, fetch_errors = fetch_news_pool()
        except Exception as exc:  # noqa: BLE001
            themed_print(f"Could not load news feeds: {exc}", "error")
            themed_input("\nPress Enter to go back...", "muted")
            pool = []
            return False
        offset = 0
        if not pool:
            themed_print("No news items found right now.", "warning")
            themed_input("\nPress Enter to go back...", "muted")
            return False
        return True

    if not load_pool(force=True):
        return

    while True:
        if not pool and not load_pool(force=True):
            return

        if offset >= len(pool):
            offset = 0

        items = pool[offset : offset + DEFAULT_NEWS_LIMIT]
        if not items:
            themed_print("No news items on this page.", "warning")
            offset = 0
            continue

        page_start = offset + 1
        page_end = offset + len(items)
        print_menu_section_header(
            "Gaming news",
            f"Showing {page_start}-{page_end} of {len(pool)}. 0 = next batch.",
        )
        themed_print(
            "X counts each link as 23 chars — drafts keep the full headline when possible.",
            "muted",
        )
        if fetch_errors:
            themed_print(
                f"Note: {len(fetch_errors)} feed(s) failed; showing what loaded.",
                "warning",
            )

        for index, item in enumerate(items, 1):
            age = format_published_age(item.get("published"))
            badge = media_badge(item)
            badge_text = f" {badge}" if badge else ""
            line = (
                color_text(f"{index}. ", "muted")
                + color_text(f"[{item['source']}] ", "label")
                + color_text(item["title"], "value")
                + color_text(f"{badge_text}  ({age})", "muted")
            )
            print(line)

        pick = themed_input(
            f"\nPick a headline (1-{len(items)}, 0=next batch, Enter=back): ",
            MENU_STYLES["prompt"],
        ).strip()
        if not pick:
            return
        if pick == "0":
            next_offset = offset + DEFAULT_NEWS_LIMIT
            if next_offset >= len(pool):
                themed_print(
                    "Reached the end of this pool — fetching a fresh batch...",
                    "muted",
                )
                if not load_pool(force=True):
                    return
            else:
                offset = next_offset
                themed_print(
                    f"Next batch ({offset + 1}-{min(offset + DEFAULT_NEWS_LIMIT, len(pool))} of {len(pool)}).",
                    "muted",
                )
            continue

        try:
            item_index = int(pick)
        except ValueError:
            themed_print("Invalid headline number.", "error")
            continue
        if item_index < 1 or item_index > len(items):
            themed_print("Invalid headline number.", "error")
            continue

        item = items[item_index - 1]
        drafts = format_news_tweets(item)

        themed_print(f"\n[{item['source']}] {item['title']}", "title")
        themed_print(item["url"], "muted")
        if item.get("summary"):
            summary = item["summary"]
            themed_print(
                summary[:160] + ("..." if len(summary) > 160 else ""),
                "value",
            )
        if item.get("image_url"):
            themed_print(f"Image: {item['image_url']}", "muted")
        if item.get("video_url"):
            themed_print(f"Video: {item['video_url']}", "muted")
        if not item.get("image_url") and not item.get("video_url"):
            themed_print("No image/video in this feed item.", "muted")
        themed_print("-" * 30, "muted")

        for draft_index, draft in enumerate(drafts, 1):
            weighted = draft.get("weighted_length", len(draft["text"]))
            themed_print(
                f"{draft_index}. {draft['label']} ({weighted}/{TWEET_MAX_LENGTH} on X)",
                "label",
            )
            print_tweet_preview(draft["text"])
            themed_print("-" * 30, "muted")

        save_hint = ", s=save image" if item.get("image_url") else ""
        draft_pick = themed_input(
            f"Copy which draft? (1-{len(drafts)}{save_hint}, Enter=back to list): ",
            MENU_STYLES["prompt"],
        ).strip().lower()
        if not draft_pick:
            continue

        if draft_pick == "s":
            if not item.get("image_url"):
                themed_print("No image available for this headline.", "warning")
            else:
                try:
                    saved = save_news_image(item)
                    if saved:
                        themed_print(f"Image saved: {saved}", "success")
                        themed_print(
                            "Attach it manually when posting on X (optional).",
                            "muted",
                        )
                except Exception as exc:  # noqa: BLE001
                    themed_print(f"Could not save image: {exc}", "error")
            themed_input("\nPress Enter to continue...", "muted")
            continue

        try:
            draft_index = int(draft_pick)
        except ValueError:
            themed_print("Invalid draft number.", "error")
            continue
        if draft_index < 1 or draft_index > len(drafts):
            themed_print("Invalid draft number.", "error")
            continue

        selected = drafts[draft_index - 1]["text"]
        if copy_to_clipboard(selected):
            themed_print(f"{drafts[draft_index - 1]['label']} draft copied!", "success")
            if item.get("image_url"):
                save_now = themed_input(
                    "Also save image for this post? (y/N): ",
                    MENU_STYLES["prompt"],
                ).strip().lower()
                if save_now in {"y", "yes"}:
                    try:
                        saved = save_news_image(item)
                        if saved:
                            themed_print(f"Image saved: {saved}", "success")
                    except Exception as exc:  # noqa: BLE001
                        themed_print(f"Could not save image: {exc}", "error")
            prompt_buffer_after_copy([selected])
        else:
            themed_print("Could not copy that draft automatically.", "error")
            themed_print("Please manually copy the selected draft above if needed.", "warning")
        themed_input("\nPress Enter to continue...", "muted")


def show_collections_menu(detector: SteamDealDetector, deals: List[Dict]) -> None:
    collections_options = [
        (1, "Themed tweet ideas", "engagement posts using current deals"),
        (2, "Deal modes", "big names, indies, hidden gems, deep discounts"),
        (3, "Categories", "RPG, horror, co-op, cozy, strategy, under $5"),
        (4, "Gaming news", "RSS headlines → tweet drafts"),
    ]

    while True:
        print_menu_section_header("Collections & ideas")
        for number, text, description in collections_options:
            print(format_menu_option(number, text, description=description))

        choice = themed_input("\nChoose an option (Enter=back): ", MENU_STYLES["prompt"]).strip()
        if not choice:
            return

        if choice == "1":
            show_tweet_ideas_menu(detector, deals)
        elif choice == "2":
            show_deal_modes_menu(detector)
        elif choice == "3":
            show_deal_categories_menu(detector)
        elif choice == "4":
            show_news_menu()
        else:
            themed_print("Invalid choice. Please try again.", "error")


def show_keyword_search_menu(detector: SteamDealDetector) -> None:
    while True:
        keyword = themed_input("\nSearch discounted Steam games by keyword: ").strip()
        if not keyword:
            return

        themed_print(f"Searching discounted Steam games for \"{keyword}\"...", "muted")
        results = detector.search_discounted_games(keyword)
        if not results:
            themed_print(f"No discounted games found for \"{keyword}\" right now.", "warning")
            continue

        action = show_collection_copy_loop(
            detector,
            f'Search results for "{keyword}"',
            results,
            allow_search_again=True,
        )
        if action == "search_again":
            continue
        return


def show_nintendo_deals_menu(detector: SteamDealDetector) -> None:
    def fetch_nintendo_deals(active_keyword: str):
        themed_print("Fetching Nintendo eShop US discounted games...", "muted")
        return detector.get_nintendo_us_deals(keyword=active_keyword)

    results = fetch_nintendo_deals("")
    if not results:
        themed_print("No Nintendo discounted games found right now.", "warning")
        return

    deal_index = 0
    while True:
        deal = results[deal_index]
        tweet = detector.format_nintendo_deal_tweet(deal)

        print_muted_label_value(f"\nNintendo Deal #{deal_index + 1}", deal["name"])
        print_muted_label_value("Tweet", f"{len(tweet)}/{TWEET_MAX_LENGTH} characters")
        print()
        themed_print("-" * 30, "muted")
        print_tweet_preview(tweet)
        themed_print("-" * 30, "muted")

        buffer_ready = bool(get_buffer_client())
        buffer_offset = 1 if buffer_ready else 0
        nintendo_options = [(1, "📋 Copy tweet")]
        if buffer_ready:
            nintendo_options.append((2, "Add to Buffer queue"))
        nintendo_options.extend(
            [
                (2 + buffer_offset, "Show next"),
                (3 + buffer_offset, "Search by keyword"),
                (4 + buffer_offset, "Refresh"),
                (5 + buffer_offset, "Back to Steam"),
            ]
        )
        max_choice = 5 + buffer_offset
        nintendo_prompt = f"Choice (1-{max_choice}, Enter=next): "
        nintendo_menu_type = "nintendo_buffer" if buffer_ready else "nintendo"

        choice = prompt_menu_choice(
            "Nintendo menu:",
            nintendo_options,
            nintendo_prompt,
            menu_type=nintendo_menu_type,
        )

        if choice == "1":
            if copy_to_clipboard(tweet):
                themed_print("Nintendo tweet copied to clipboard!", "success")
                prompt_buffer_after_copy([tweet])
            else:
                themed_print("Could not copy that Nintendo tweet automatically.", "error")
                themed_print("Please manually copy the selected tweet above if needed.", "warning")
            themed_input("\nPress Enter to continue...", "muted")
            if deal_index < len(results) - 1:
                deal_index += 1
            continue

        if buffer_ready and choice == "2":
            if send_tweet_to_buffer(tweet):
                if deal_index < len(results) - 1:
                    deal_index += 1
            themed_input("\nPress Enter to continue...", "muted")
            continue

        if choice == "" or choice == str(2 + buffer_offset):
            if deal_index < len(results) - 1:
                deal_index += 1
            else:
                themed_print("Reached the last Nintendo deal in this list.", "warning")
            continue

        if choice == str(3 + buffer_offset):
            while True:
                new_keyword = themed_input(
                    "\nSearch Nintendo deals by keyword (Enter = back): "
                ).strip()
                if not new_keyword:
                    break

                new_results = fetch_nintendo_deals(new_keyword)
                if not new_results:
                    themed_print(
                        "No Nintendo discounted games found for that search.",
                        "warning",
                    )
                    continue

                search_title = f'Nintendo US discounted deals for "{new_keyword}"'
                action = show_collection_copy_loop(
                    detector,
                    search_title,
                    new_results,
                    tweet_formatter=detector.format_nintendo_deal_tweet,
                    track_posted=False,
                    allow_search_again=True,
                )
                if action == "search_again":
                    continue
                break
            continue

        if choice == str(4 + buffer_offset):
            refreshed_results = fetch_nintendo_deals("")
            if not refreshed_results:
                themed_print("No Nintendo discounted games found on refresh.", "warning")
                continue
            results = refreshed_results
            deal_index = 0
            continue

        if choice == str(5 + buffer_offset):
            return

        themed_print("Invalid choice. Please try again.", "error")

def preview_theme_colors() -> None:
    """Print palette + sample menus — fast way to check color edits without fetching deals."""
    themed_print("ANSI color palette", "title")
    themed_print("-" * 30, "muted")
    for name in ANSI_COLORS:
        if name == "reset":
            continue
        print(f"{ANSI_COLORS[name]}{name:16}{ANSI_COLORS['reset']}")

    themed_print("\nTHEME roles", "title")
    themed_print("-" * 30, "muted")
    for role in THEME:
        if role == "reset":
            continue
        themed_print(f"  {role}", role)

    themed_print("\nSample Steam menu", "title")
    themed_print("-" * 30, "muted")
    print(color_text("What would you like to do?", MENU_STYLES["header"]))
    for number, text in (
        (1, "📋 Copy tweet"),
        (2, "Add to Buffer queue"),
        (3, "Show next"),
        (4, "Search by keyword"),
        (5, "Refresh"),
        (6, "Collections & ideas"),
        (7, "Nintendo US deals"),
        (8, "Copy 5 deals"),
        (9, "Exit"),
    ):
        print(format_menu_option(number, text, menu_type="steam_buffer"))

    themed_print("\nSample Nintendo menu", "title")
    themed_print("-" * 30, "muted")
    print(color_text("Nintendo menu:", MENU_STYLES["header"]))
    for number, text in (
        (1, "📋 Copy tweet"),
        (2, "Add to Buffer queue"),
        (3, "Show next"),
        (4, "Search by keyword"),
        (5, "Refresh"),
        (6, "Back to Steam"),
    ):
        print(format_menu_option(number, text, menu_type="nintendo_buffer"))

    print()
    themed_print(
        "Edit ANSI_COLORS / THEME / MENU_STYLES, save, then run this preview again.",
        "muted",
    )
    themed_print("Command: python manual_poster.py --preview-colors", "muted")


def main():
    print_banner()

    detector = SteamDealDetector()
    
    while True:
        themed_print("Fetching latest Steam deals...", "muted")
        deals = detector.get_all_deals()
        deals, posted_count = deprioritize_posted_deals(deals)
        
        if not deals:
            themed_print("No deals found. Try again later.", "warning")
            continue
        
        themed_print(f"Found {len(deals)} deals!", "success")
        if posted_count:
            themed_print(
                f"Moved {posted_count} recently copied game"
                f"{'s' if posted_count != 1 else ''} to the end for more variety.",
                "muted",
            )
        print()
        print_separator(50)
        
        deal_index = 0
        refresh_requested = False

        while deal_index < len(deals):
            deal = deals[deal_index]
            deal_number = deal_index + 1

            print_deal_header(deal_number, deal)
            
            # Format the tweet
            tweet = detector.format_deal_tweet(deal)
            
            print_muted_label_value("Tweet", f"{len(tweet)}/{TWEET_MAX_LENGTH} characters")
            print()
            themed_print("-" * 30, "muted")
            print_tweet_preview(tweet)
            themed_print("-" * 30, "muted")
            
            # Ask user what to do
            buffer_ready = bool(get_buffer_client())
            buffer_offset = 1 if buffer_ready else 0
            steam_options = [(1, "📋 Copy tweet")]
            if buffer_ready:
                steam_options.append((2, "Add to Buffer queue"))
            steam_options.extend(
                [
                    (2 + buffer_offset, "Show next"),
                    (3 + buffer_offset, "Search by keyword"),
                    (4 + buffer_offset, "Refresh"),
                    (5 + buffer_offset, "Collections & ideas"),
                    (6 + buffer_offset, "Nintendo US deals"),
                    (7 + buffer_offset, f"Copy {BULK_COPY_COUNT} deals"),
                    (8 + buffer_offset, "Exit"),
                ]
            )
            max_choice = 8 + buffer_offset
            steam_prompt = f"Choice (1-{max_choice}, Enter=next): "
            steam_menu_type = "steam_buffer" if buffer_ready else "steam"

            choice = prompt_menu_choice(
                "What would you like to do?",
                steam_options,
                steam_prompt,
                menu_type=steam_menu_type,
            )
            
            if choice == '1':
                if copy_to_clipboard(tweet):
                    mark_deal_posted(deal)
                    themed_print("Tweet copied to clipboard! You can now paste it on 𝕏.", "success")
                    themed_print("Marked as posted for more variety on future refreshes.", "muted")
                    prompt_buffer_after_copy([tweet])
                else:
                    themed_print("Could not copy to clipboard automatically.", "error")
                    if not _HAS_PYPERCLIP:
                        themed_print("Tip: Install pyperclip with: pip install pyperclip", "warning")
                    if shutil.which("termux-clipboard-set"):
                        themed_print("You can also run: echo \"<tweet>\" | termux-clipboard-set", "warning")
                    themed_print("Please manually copy the tweet above if needed.", "warning")
                
                themed_input("\nPress Enter to continue...", "muted")
                deal_index += 1
                
            elif buffer_ready and choice == '2':
                if send_tweet_to_buffer(tweet):
                    mark_deal_posted(deal)
                    themed_print("Marked as posted for more variety on future refreshes.", "muted")
                    deal_index += 1
                themed_input("\nPress Enter to continue...", "muted")

            elif choice == '' or choice == str(2 + buffer_offset):
                deal_index += 1
                continue
                
            elif choice == str(3 + buffer_offset):
                show_keyword_search_menu(detector)
                themed_input("\nPress Enter to continue...", "muted")
                continue

            elif choice == str(4 + buffer_offset):
                refresh_requested = True
                break
                
            elif choice == str(5 + buffer_offset):
                show_collections_menu(detector, deals)
                themed_input("\nPress Enter to continue...", "muted")
                continue

            elif choice == str(6 + buffer_offset):
                show_nintendo_deals_menu(detector)
                themed_input("\nPress Enter to continue...", "muted")
                continue

            elif choice == str(7 + buffer_offset):
                bulk_deals = deals[deal_index:deal_index + BULK_COPY_COUNT]
                bulk_tweet_list = [
                    detector.format_deal_tweet(bulk_deal) for bulk_deal in bulk_deals
                ]
                bulk_tweets = format_bulk_tweets(detector, bulk_deals)

                if copy_to_clipboard(bulk_tweets):
                    mark_deals_posted(bulk_deals)
                    themed_print(f"{len(bulk_deals)} deal tweets copied to clipboard! You can now paste them on 𝕏.", "success")
                    themed_print("Marked those games as posted for more variety on future refreshes.", "muted")
                    prompt_buffer_after_copy(bulk_tweet_list)
                else:
                    themed_print("Could not copy the deal tweets to clipboard automatically.", "error")
                    if not _HAS_PYPERCLIP:
                        themed_print("Tip: Install pyperclip with: pip install pyperclip", "warning")
                    themed_print("Please manually copy the deal tweets below if needed.", "warning")
                    print_tweet_preview(bulk_tweets)

                themed_input("\nPress Enter to continue...", "muted")
                deal_index += len(bulk_deals)

            elif choice == str(8 + buffer_offset):
                themed_print("Goodbye!", "success")
                return
                
            else:
                themed_print("Invalid choice. Please try again.", "error")
                continue
        
        if refresh_requested:
            continue

        # Ask if user wants to refresh
        if len(deals) > 0:
            refresh = themed_input("\nRefresh deals? (y/n): ").strip().lower()
            if refresh != 'y':
                break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--preview-colors", "--preview-theme"):
        try:
            preview_theme_colors()
        except KeyboardInterrupt:
            themed_print("\n", "muted")
    else:
        try:
            main()
        except KeyboardInterrupt:
            themed_print("\n\nGoodbye!", "success")
        except Exception as e:
            themed_print(f"\nError: {e}", "error")
            themed_print("Please check your internet connection and try again.", "warning")
