import requests
import json
import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import urllib.parse
import os
import itertools

try:
    from nintendeals import noa as nintendo_noa  # type: ignore[import-not-found]
    from nintendeals.api import prices as nintendo_prices  # type: ignore[import-not-found]
    _HAS_NINTENDO_DEALS_LIB = True
except Exception:
    nintendo_noa = None  # type: ignore
    nintendo_prices = None  # type: ignore
    _HAS_NINTENDO_DEALS_LIB = False

TWEET_MAX_LENGTH = 280
STEAMDEALBOT_COLOR_ENABLED = os.environ.get("STEAMDEALBOT_NO_COLOR") != "1"
MUTED_COLOR = "\033[90m"
RESET_COLOR = "\033[0m"


def print_progress(message):
    if STEAMDEALBOT_COLOR_ENABLED:
        print(f"{MUTED_COLOR}{message}{RESET_COLOR}")
    else:
        print(message)

# Steam's "infinite scroll" search results endpoint returns clean JSON and
# supports pagination, which lets us sample a different slice of specials on
# every refresh (thousands of deals are available, not just the curated ~10).
STEAM_SEARCH_RESULTS_URL = "https://store.steampowered.com/search/results/"
NINTENDO_US_SALES_URL = "https://ec.nintendo.com/api/US/en/search/sales"
STEAM_DEAL_COUNT = 35
NINTENDO_DEAL_COUNT = 10
# How many descriptions to enrich per refresh (each one is an extra page load).
DESCRIPTION_ENRICH_LIMIT = 12
# Keep most manual-poster results near Steam's high-signal pages so the feed
# includes recognizable games and well-reviewed/viral indies, not only deep
# catalog items with little public traction.
POPULAR_SEARCH_PAGES = [
    ("Reviews_DESC", 0),
    ("Reviews_DESC", 50),
    ("Reviews_DESC", 100),
    ("", 0),
    ("", 50),
]
DISCOVERY_SEARCH_SORTS = ["Reviews_DESC", "", "Released_DESC"]
DISCOVERY_OFFSET_LIMIT = 1000
COLLECTION_DEAL_COUNT = 25
DEAL_MODE_CONFIGS = {
    "big_names": {
        "label": "Big names on sale",
        "blurb": "Top-reviewed blockbuster discounts",
    },
    "popular_indies": {
        "label": "Popular indies",
        "blurb": "Well-reviewed indie discounts",
    },
    "hidden_gems": {
        "label": "Hidden gems",
        "blurb": "Lesser-known discounted games",
    },
    "deep_discounts": {
        "label": "Deep discounts",
        "blurb": "Highest discount percentages",
    },
}
DEAL_CATEGORY_CONFIGS = {
    "rpg": {
        "label": "RPG",
        "blurb": "Role-playing games on sale",
        "tags": "122",
    },
    "horror": {
        "label": "Horror",
        "blurb": "Horror games on sale",
        "tags": "1667",
    },
    "coop": {
        "label": "Co-op",
        "blurb": "Co-op games on sale",
        "tags": "1685",
    },
    "cozy": {
        "label": "Cozy",
        "blurb": "Cozy games on sale",
        "tags": "1716",
    },
    "strategy": {
        "label": "Strategy",
        "blurb": "Strategy games on sale",
        "tags": "9",
    },
    "under_5": {
        "label": "Under $5",
        "blurb": "Discounted games priced at $5 or less",
        "max_price_usd": 5.0,
    },
}

# Default source label when no seasonal Steam-wide sale is detected.
DEFAULT_SOURCE_LABEL = "Steam Specials"
# Matches Steam's recurring seasonal/event sales on the store homepage.
SEASONAL_SALE_PATTERN = re.compile(
    r'\b('
    r'Summer|Winter|Autumn|Fall|Spring|Lunar New Year|Halloween|'
    r'Spring Cleaning|Next Fest|Golden Week|Black Friday|Cyber Monday'
    r')\s+(?:Sale|Fest|Festival)\b',
    re.I,
)
# How many game-specific (genre/tag) hashtags to add per tweet.
RELEVANT_HASHTAG_COUNT = 2
# Generic tags that don't help discovery (skipped when picking hashtags).
GENERIC_TAGS = {
    'indie', 'casual', 'singleplayer', 'multiplayer', 'free to play',
    'early access', 'great soundtrack', 'family friendly', 'classic',
}

# Sentinel so we can cache "no sale detected" distinctly from "not fetched yet".
_UNSET = object()


class SteamDealDetector:
    """Steam deal detector using multiple methods including API calls."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        # Bypass Steam's age-check interstitial so store pages return full
        # content (descriptions and user tags) instead of the age gate.
        self.session.cookies.set('birthtime', '568022401')
        self.session.cookies.set('mature_content', '1')
        self.session.cookies.set('wants_mature_content', '1')
        # Cached total number of specials so we know the valid random offset range.
        self._total_specials_count = None
        # Cached active seasonal sale name (e.g. "Steam Summer Sale"), fetched once.
        self._active_sale_name = _UNSET
        
    def get_steam_api_deals(self):
        """Get deals using Steam's API."""
        try:
            # Steam API endpoint for specials
            url = "https://store.steampowered.com/api/featuredcategories/?cc=us&l=english"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            deals = []
            
            # Look for specials in the API response
            if 'specials' in data and 'items' in data['specials']:
                for item in data['specials']['items'][:10]:
                    try:
                        game_name = item.get('name', 'Unknown Game')
                        discount_percent = item.get('discount_percent', 0)
                        final_price = item.get('final_price', 0)
                        original_price = item.get('original_price', 0)
                        
                        if discount_percent and discount_percent > 0:
                            # Convert price from cents to dollars
                            final_price_dollars = final_price / 100
                            original_price_dollars = original_price / 100
                            
                            # Get game description (with fallback)
                            steam_url = f"https://store.steampowered.com/app/{item.get('id', '')}/"
                            try:
                                game_info = self.get_game_info(game_name, steam_url)
                                description = game_info['description']
                            except:
                                description = f"An amazing game with {discount_percent}% off! Don't miss this deal!"
                            
                            deal = {
                                'name': game_name,
                                'discount': f"-{discount_percent}%",
                                'price': f"${final_price_dollars:.2f}",
                                'original_price': f"${original_price_dollars:.2f}",
                                'time_left': self._time_left_from_unix(item.get('discount_expiration')),
                                'source': 'Steam Popular Deals',
                                'description': description,
                                'steam_url': steam_url
                            }
                            deals.append(deal)
                    except Exception as e:
                        continue
                        
            return deals
            
        except Exception as e:
            print(f"Error fetching Steam API deals: {e}")
            return []
    
    def get_game_info(self, game_name, steam_url):
        """Get game information from Steam store page."""
        try:
            response = self.session.get(steam_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find game description in multiple ways
            description = None
            
            # Method 1: Look for the game description snippet (most reliable)
            desc_elem = soup.select_one('div.game_description_snippet')
            if desc_elem:
                description = desc_elem.get_text().strip()
            
            # Method 2: Look for meta description
            if not description:
                meta_desc = soup.select_one('meta[name="description"]')
                if meta_desc and meta_desc.get('content'):
                    description = meta_desc.get('content').strip()
            
            # Method 3: Look for game area description
            if not description:
                desc_elem = soup.select_one('div.game_area_description')
                if desc_elem:
                    description = desc_elem.get_text().strip()
            
            # Method 4: Look for any paragraph with game info
            if not description:
                paragraphs = soup.select('div.game_area_description p')
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 50 and len(text) < 300:
                        description = text
                        break
            
            # Clean up description
            if description:
                # Remove extra whitespace and newlines
                description = ' '.join(description.split())
                
                # Truncate if too long
                if len(description) > 200:
                    description = description[:200].rsplit(' ', 1)[0] + "..."
                
                # Ensure it ends with proper punctuation
                if not description.endswith(('.', '!', '?')):
                    description += "."
            else:
                # Fallback description based on game name
                description = f"Experience {game_name} - an exciting game now on sale!"

            # Extract the most relevant user tags/genres for hashtags.
            tags = [t.get_text(strip=True) for t in soup.select('a.app_tag')]
            if not tags:
                tags = [g.get_text(strip=True) for g in soup.select('a[href*="/genre/"]')]
            tags = [t for t in tags if t]

            return {
                'description': description,
                'steam_url': steam_url,
                'tags': tags,
            }
            
        except Exception as e:
            # Fallback description based on game name
            return {
                'description': f"Experience {game_name} - an exciting game now on sale!",
                'steam_url': steam_url,
                'tags': [],
            }
    
    def get_steam_specials_page(self):
        """Get deals from Steam's specials page with better parsing."""
        try:
            url = "https://store.steampowered.com/specials/?cc=us"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            deals = []
            
            # Look for game containers with more specific selectors
            game_containers = soup.find_all('div', class_=re.compile(r'.*game.*|.*item.*|.*discount.*', re.I))
            
            for container in game_containers[:30]:
                try:
                    text_content = container.get_text()
                    
                    # Look for discount pattern
                    discount_match = re.search(r'(-\d+%)', text_content)
                    if not discount_match:
                        continue
                    
                    discount = discount_match.group(1)
                    
                    # Look for USD price
                    price_match = re.search(r'(\$\d+\.?\d*)', text_content)
                    if not price_match:
                        continue
                    
                    price = price_match.group(1)
                    
                    # Look for game name and link
                    game_link = container.find('a', href=re.compile(r'/app/\d+/'))
                    if game_link:
                        game_name = game_link.get_text(strip=True)
                        steam_url = game_link['href']
                        if not steam_url.startswith('http'):
                            steam_url = 'https://store.steampowered.com' + steam_url
                    else:
                        # Try to extract from text content
                        lines = text_content.split('\n')
                        game_name = None
                        for line in lines:
                            line = line.strip()
                            if len(line) > 5 and len(line) < 100 and not re.match(r'^\$\d+', line) and not re.match(r'^-\d+%', line):
                                game_name = line
                                break
                        
                        if not game_name:
                            continue
                        
                        steam_url = f"https://store.steampowered.com/search/?term={urllib.parse.quote(game_name)}"
                    
                    if not game_name or len(game_name) < 3:
                        continue
                    
                    # Clean up game name
                    game_name = self._clean_game_name(game_name)
                    
                    if len(game_name) < 3:
                        continue
                    
                    # Get game description
                    game_info = self.get_game_info(game_name, steam_url)
                    
                    deal = {
                        'name': game_name,
                        'discount': discount,
                        'price': price,
                        'original_price': None,
                        'source': 'Steam Daily Deals',
                        'description': game_info['description'],
                        'steam_url': steam_url
                    }
                    deals.append(deal)
                    
                except Exception as e:
                    continue
                    
            return deals
            
        except Exception as e:
            print(f"Error fetching Steam specials: {e}")
            return []
    
    def get_steam_search_deals(self):
        """Get deals from Steam search with better parsing."""
        try:
            url = "https://store.steampowered.com/search/?sort_by=Reviews_DESC&specials=1&cc=us"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            deals = []
            
            # Look for game containers with more specific selectors
            game_containers = soup.find_all('div', class_=re.compile(r'.*search.*result.*|.*game.*|.*item.*', re.I))
            
            for container in game_containers[:20]:
                try:
                    text_content = container.get_text()
                    
                    # Look for discount pattern
                    discount_match = re.search(r'(-\d+%)', text_content)
                    if not discount_match:
                        continue
                    
                    discount = discount_match.group(1)
                    
                    # Look for USD price
                    price_match = re.search(r'(\$\d+\.?\d*)', text_content)
                    if not price_match:
                        continue
                    
                    price = price_match.group(1)
                    
                    # Look for game name and link
                    game_link = container.find('a', href=re.compile(r'/app/\d+/'))
                    if game_link:
                        game_name = game_link.get_text(strip=True)
                        steam_url = game_link['href']
                        if not steam_url.startswith('http'):
                            steam_url = 'https://store.steampowered.com' + steam_url
                    else:
                        continue
                    
                    if not game_name or len(game_name) < 3:
                        continue
                    
                    # Clean up game name
                    game_name = self._clean_game_name(game_name)
                    
                    if len(game_name) < 3:
                        continue
                    
                    # Get game description
                    game_info = self.get_game_info(game_name, steam_url)
                    
                    deal = {
                        'name': game_name,
                        'discount': discount,
                        'price': price,
                        'original_price': None,
                        'source': 'Steam Featured Deals',
                        'description': game_info['description'],
                        'steam_url': steam_url
                    }
                    deals.append(deal)
                    
                except Exception as e:
                    continue
                    
            return deals
            
        except Exception as e:
            print(f"Error fetching Steam search deals: {e}")
            return []
    
    def get_active_sale_name(self):
        """Best-effort detection of an active Steam-wide seasonal sale.

        Fetches the store homepage once and looks for a seasonal sale title
        (e.g. "Summer Sale"). Returns a label like "Steam Summer Sale", or
        None if no seasonal sale is detected. Cached for the run.
        """
        if self._active_sale_name is not _UNSET:
            return self._active_sale_name

        self._active_sale_name = None
        try:
            response = self.session.get(
                "https://store.steampowered.com/", timeout=10
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Prefer prominent banner/title text over generic body text.
            candidates = []
            for sel in ('title', 'h1', 'h2', '.salepage_header', '[class*="sale_"]'):
                candidates.extend(e.get_text(' ', strip=True) for e in soup.select(sel))
            candidates.append(soup.get_text(' ', strip=True))

            for text in candidates:
                match = SEASONAL_SALE_PATTERN.search(text or '')
                if match:
                    phrase = match.group(0).strip()
                    phrase = re.sub(r'\s+', ' ', phrase).title()
                    label = phrase if phrase.lower().startswith('steam') else f"Steam {phrase}"
                    self._active_sale_name = label
                    print_progress(f"Active sale detected: {label}")
                    break
        except Exception as e:
            print(f"Could not check for active sale: {e}")

        return self._active_sale_name

    @staticmethod
    def _tag_to_hashtag(tag):
        """Turn a Steam tag/genre into a CamelCase hashtag token (no '#').

        Preserves acronyms and intentional casing (e.g. RPG, FPS, PvP, 2D).
        """
        cleaned = re.sub(r"[^0-9A-Za-z ]", "", tag).strip()
        if not cleaned:
            return None

        def case_word(word):
            # Keep acronyms ("RPG", "2D") and mixed-case tags ("PvP") as-is.
            if word.isupper() or not word.islower():
                return word
            return word.capitalize()

        return "".join(case_word(word) for word in cleaned.split())

    def _relevant_hashtags(self, deal, count=RELEVANT_HASHTAG_COUNT):
        """Build up to `count` game-specific hashtags from the deal's tags."""
        hashtags = []
        seen = set()
        for tag in deal.get('tags', []) or []:
            if tag.lower() in GENERIC_TAGS:
                continue
            token = self._tag_to_hashtag(tag)
            if not token or token.lower() in seen:
                continue
            seen.add(token.lower())
            hashtags.append(f"#{token}")
            if len(hashtags) >= count:
                break
        return hashtags

    def _fetch_search_results_json(self, start=0, count=50, sort_by="", query="", tags=""):
        """Call Steam's paginated search-results JSON endpoint.

        Returns the parsed JSON dict (with 'total_count' and 'results_html'),
        or None on failure.
        """
        params = {
            'term': query,
            'start': start,
            'count': count,
            'specials': 1,
            'infinite': 1,
            'json': 1,
            'cc': 'us',
            'l': 'english',
        }
        if sort_by:
            params['sort_by'] = sort_by
        if tags:
            params['tags'] = tags
        try:
            response = self.session.get(
                STEAM_SEARCH_RESULTS_URL, params=params, timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Steam search results JSON: {e}")
            return None

    def get_total_specials_count(self):
        """Return (and cache) how many specials Steam currently lists."""
        if self._total_specials_count:
            return self._total_specials_count
        data = self._fetch_search_results_json(start=0, count=1)
        if data and isinstance(data.get('total_count'), int):
            self._total_specials_count = data['total_count']
        return self._total_specials_count or 0

    def _parse_search_results_html(self, results_html, source_label=DEFAULT_SOURCE_LABEL):
        """Parse the 'results_html' fragment into deal dicts (no description)."""
        soup = BeautifulSoup(results_html, 'html.parser')
        deals = []

        for row in soup.select('a.search_result_row'):
            try:
                title_elem = row.select_one('span.title')
                if not title_elem:
                    continue
                game_name = self._clean_game_name(title_elem.get_text(strip=True))
                if len(game_name) < 3:
                    continue

                discount_elem = row.select_one('div.discount_pct')
                discount = discount_elem.get_text(strip=True) if discount_elem else None
                if not discount or not re.search(r'-\d+%', discount):
                    continue
                discount = re.search(r'(-\d+%)', discount).group(1)

                price_elem = row.select_one('div.discount_final_price')
                price_match = re.search(r'(\$\d[\d,]*\.?\d*)', price_elem.get_text()) if price_elem else None
                if not price_match:
                    continue
                price = price_match.group(1)

                orig_elem = row.select_one('div.discount_original_price')
                orig_match = re.search(r'(\$\d[\d,]*\.?\d*)', orig_elem.get_text()) if orig_elem else None
                original_price = orig_match.group(1) if orig_match else None

                steam_url = (row.get('href') or '').split('?')[0]
                appid = row.get('data-ds-appid')
                if appid and '/app/' not in steam_url:
                    steam_url = f"https://store.steampowered.com/app/{appid}/"
                if not steam_url:
                    continue

                deals.append({
                    'name': game_name,
                    'discount': discount,
                    'price': price,
                    'original_price': original_price,
                    'source': source_label,
                    'description': None,
                    'steam_url': steam_url,
                    'tags': [],
                })
            except Exception:
                continue

        return deals

    def _get_specials_page(self, start=0, count=50, sort_by=""):
        data = self._fetch_search_results_json(start=start, count=count, sort_by=sort_by)
        if not data or not data.get('results_html'):
            return []

        source_label = self.get_active_sale_name() or DEFAULT_SOURCE_LABEL
        return self._parse_search_results_html(data['results_html'], source_label=source_label)

    def search_discounted_games(self, keyword, count=10):
        """Search Steam specials for discounted games matching a keyword."""
        keyword = (keyword or "").strip()
        if not keyword:
            return []

        all_deals = []
        for sort_by in ("Reviews_DESC", ""):
            data = self._fetch_search_results_json(
                start=0,
                count=count,
                sort_by=sort_by,
                query=keyword,
            )
            if not data or not data.get('results_html'):
                continue

            source_label = self.get_active_sale_name() or DEFAULT_SOURCE_LABEL
            all_deals.extend(
                self._parse_search_results_html(data['results_html'], source_label=source_label)
            )

        unique_deals = []
        seen_names = set()
        for deal in all_deals:
            key = deal['name'].lower()
            if key in seen_names:
                continue
            unique_deals.append(deal)
            seen_names.add(key)

        keyword_lower = keyword.lower()
        unique_deals.sort(
            key=lambda deal: (
                0 if deal['name'].lower().startswith(keyword_lower) else 1,
                0 if keyword_lower in deal['name'].lower() else 1,
                deal['name'].lower(),
            )
        )
        self._enrich_descriptions(unique_deals, limit=min(count, DESCRIPTION_ENRICH_LIMIT))
        print_progress(f"Found {len(unique_deals)} discounted search results for \"{keyword}\"")
        return unique_deals[:count]

    def _parse_nintendo_sales_items(self, items):
        deals = []
        for item in items:
            if not isinstance(item, dict):
                continue

            name = (
                item.get("formal_name")
                or item.get("title")
                or item.get("name")
                or ""
            ).strip()
            if len(name) < 2:
                continue

            url = item.get("url") or item.get("deep_link") or item.get("product_url") or ""
            if url.startswith("/"):
                url = f"https://www.nintendo.com{url}"
            if not url:
                slug = item.get("slug")
                if slug:
                    url = f"https://www.nintendo.com/us/store/products/{slug}/"
            if not url:
                continue

            regular = item.get("regular_price")
            sale = item.get("discount_price")
            sale_end_text = None
            regular_value = None
            sale_value = None
            if isinstance(regular, dict):
                try:
                    regular_value = float(regular.get("raw_value") or regular.get("amount"))
                except Exception:
                    regular_value = None
            if isinstance(sale, dict):
                try:
                    sale_value = float(sale.get("raw_value") or sale.get("amount"))
                except Exception:
                    sale_value = None
                sale_end_text = (
                    sale.get("end_datetime")
                    or sale.get("endDate")
                    or sale.get("sale_end")
                )
            if sale_value is None:
                try:
                    sale_value = float(item.get("sale_price") or item.get("price"))
                except Exception:
                    sale_value = None
            if not sale_end_text:
                sale_end_text = (
                    item.get("sale_end")
                    or item.get("sale_end_datetime")
                    or item.get("discount_end_datetime")
                )
            if sale_value is None:
                continue

            price = f"${sale_value:.2f}"
            original_price = None
            discount = "-0%"
            if regular_value and regular_value > sale_value:
                original_price = f"${regular_value:.2f}"
                discount_pct = round((1 - (sale_value / regular_value)) * 100)
                discount = f"-{discount_pct}%"

            description = (
                item.get("description")
                or item.get("catch_copy")
                or item.get("excerpt")
                or f"{name} is currently discounted on Nintendo eShop US."
            )
            description = " ".join(str(description).split())

            nsuid = str(item.get("nsuid") or item.get("ns_uid") or "").strip()

            deals.append(
                {
                    "name": name,
                    "discount": discount,
                    "price": price,
                    "original_price": original_price,
                    "source": "Nintendo eShop US",
                    "time_left": self._nintendo_time_left_text(sale_end_text),
                    "description": description,
                    "steam_url": url,
                    "nsuid": nsuid,
                    "tags": ["NintendoSwitch", "Nintendo"],
                }
            )
        return deals

    def _finalize_nintendo_deal_list(self, deals, count=NINTENDO_DEAL_COUNT, keyword=""):
        deals = self._dedupe_deals_by_name(deals)
        if not keyword and len(deals) > 1:
            random.shuffle(deals)
        print_progress(
            f"Found {len(deals[:count])} Nintendo US discounted games"
            + (f" for \"{keyword}\"" if keyword else "")
        )
        return deals[:count]

    def _nintendo_deal_from_library_game(self, game, price):
        sale_value = getattr(price, "sale_value", None)
        regular_value = getattr(price, "value", None)
        if sale_value is None:
            return None

        # Prefer price math over nintendeals' sale_discount — that field is often wrong
        # (e.g. DISTRAINT Deluxe: library says 33%, storefront is ~66% from $5.99 → $1.99).
        discount_pct = 0
        try:
            if regular_value and float(regular_value) > float(sale_value) > 0:
                discount_pct = int(
                    ((float(regular_value) - float(sale_value)) / float(regular_value)) * 100
                )
        except (TypeError, ValueError, ZeroDivisionError):
            discount_pct = 0
        if discount_pct <= 0:
            discount_pct = int(getattr(price, "sale_discount", 0) or 0)

        slug = getattr(game, "slug", "") or ""
        nsuid = str(getattr(game, "nsuid", "") or "").strip()
        url = f"https://www.nintendo.com/us/store/products/{slug}/" if slug else ""
        if not url:
            return None

        sale_end = getattr(price, "sale_end", None)
        title = getattr(game, "title", "Nintendo Deal")
        return {
            "name": title,
            "discount": f"-{discount_pct}%",
            "price": f"${sale_value:.2f}",
            "original_price": f"${regular_value:.2f}" if regular_value else None,
            "source": "Nintendo eShop US",
            "time_left": self._nintendo_time_left_text(sale_end),
            "description": (
                " ".join(str(getattr(game, "description", "") or "").split())
                or f"{title} is discounted on Nintendo eShop US."
            ),
            "steam_url": url,
            "nsuid": nsuid,
            "tags": ["NintendoSwitch", "Nintendo"],
        }

    def get_nintendo_us_deals(self, keyword="", count=NINTENDO_DEAL_COUNT):
        """Get discounted Nintendo eShop US deals (separate from Steam)."""
        if _HAS_NINTENDO_DEALS_LIB:
            return self._get_nintendo_us_deals_from_library(keyword=keyword, count=count)
        return self._get_nintendo_us_deals_from_api(keyword=keyword, count=count)

    def _get_nintendo_us_deals_from_api(self, keyword="", count=NINTENDO_DEAL_COUNT):
        """Legacy Nintendo sales API (often unavailable). Used only without nintendeals."""
        keyword = (keyword or "").strip()
        pool_count = max(count * 4, 80)
        fetch_count = min(100, pool_count)

        if keyword:
            params = {
                "count": fetch_count,
                "offset": 0,
                "q": keyword,
                "query": keyword,
            }
            offsets = [0]
        else:
            offsets = sorted({random.randint(0, offset) for offset in (0, 40, 120, 200, 320)})
            params = {"count": fetch_count, "offset": 0}

        all_items = []
        try:
            for offset in offsets:
                request_params = dict(params)
                request_params["offset"] = offset
                response = self.session.get(
                    NINTENDO_US_SALES_URL, params=request_params, timeout=5
                )
                response.raise_for_status()
                data = response.json()
                items = []
                if isinstance(data, dict):
                    items = data.get("items") or data.get("contents") or data.get("results") or []
                if isinstance(items, list):
                    all_items.extend(items)
        except Exception as e:
            print_progress(f"Nintendo US deals endpoint unavailable: {e}")
            return []

        deals = self._parse_nintendo_sales_items(all_items)

        if keyword:
            keyword_lower = keyword.lower()
            deals = [deal for deal in deals if keyword_lower in deal["name"].lower()]

        deals = self._dedupe_deals_by_name(deals)
        if not deals:
            return []
        return self._finalize_nintendo_deal_list(deals, count=count, keyword=keyword)

    def _get_nintendo_us_deals_from_library(self, keyword="", count=NINTENDO_DEAL_COUNT):
        """Nintendo US deals via the nintendeals library (primary source)."""
        if not _HAS_NINTENDO_DEALS_LIB:
            print_progress("Nintendo library unavailable (install `nintendeals`).")
            return []

        try:
            keyword = (keyword or "").strip()
            deals = []
            target_pool = max(count * 2, count + 12)

            if keyword:
                games = list(itertools.islice(
                    nintendo_noa.search.search_switch_games(keyword), max(count * 4, 60)
                ))
                if not games:
                    return []
                prices_by_nsuid = dict(nintendo_prices.get_prices(games, country="US"))
                for game in games:
                    nsuid = str(getattr(game, "nsuid", "") or "")
                    price = prices_by_nsuid.get(nsuid)
                    if not price or not getattr(price, "on_sale", False):
                        continue
                    deal = self._nintendo_deal_from_library_game(game, price)
                    if deal:
                        deals.append(deal)
            else:
                games_iter = nintendo_noa.list_switch_games()
                skip = random.randint(0, 60)
                games_iter = itertools.islice(games_iter, skip, None)
                batch_size = 40

                while len(deals) < target_pool:
                    batch = list(itertools.islice(games_iter, batch_size))
                    if not batch:
                        break
                    prices_by_nsuid = dict(nintendo_prices.get_prices(batch, country="US"))
                    for game in batch:
                        nsuid = str(getattr(game, "nsuid", "") or "")
                        price = prices_by_nsuid.get(nsuid)
                        if not price or not getattr(price, "on_sale", False):
                            continue
                        deal = self._nintendo_deal_from_library_game(game, price)
                        if deal:
                            deals.append(deal)

            deals = self._dedupe_deals_by_name(deals)
            return self._finalize_nintendo_deal_list(
                deals,
                count=count,
                keyword=keyword,
            )
        except Exception as e:
            print_progress(f"Nintendo library lookup failed: {e}")
            return []

    @staticmethod
    def _time_left_text_from_datetime(end_dt):
        if end_dt.tzinfo is None:
            now = datetime.now()
        else:
            now = datetime.now(end_dt.tzinfo)
        remaining = end_dt - now
        if remaining.total_seconds() <= 0:
            return "ended"

        total_hours = int(remaining.total_seconds() // 3600)
        total_days = total_hours // 24
        if total_days >= 1:
            return f"{total_days}d left"
        if total_hours >= 2:
            return f"{total_hours} hours left"
        total_minutes = int(remaining.total_seconds() // 60)
        if total_minutes >= 2:
            return f"{total_minutes} minutes left"
        return "ending soon"

    @classmethod
    def _time_left_from_unix(cls, unix_seconds):
        if not unix_seconds:
            return None
        try:
            end_dt = datetime.fromtimestamp(int(unix_seconds))
        except Exception:
            return None
        return cls._time_left_text_from_datetime(end_dt)

    @classmethod
    def _nintendo_time_left_text(cls, sale_end):
        if not sale_end:
            return None

        end_dt = None
        if isinstance(sale_end, datetime):
            end_dt = sale_end
        elif isinstance(sale_end, str):
            text = sale_end.strip()
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                end_dt = datetime.fromisoformat(text)
            except Exception:
                return None
        else:
            return None

        return cls._time_left_text_from_datetime(end_dt)

    def format_nintendo_deal_tweet(self, deal, max_length: int = TWEET_MAX_LENGTH) -> str:
        name = deal["name"]
        discount = deal["discount"]
        price = deal["price"]
        original_price = deal.get("original_price")
        source = deal.get("source", "Nintendo eShop US")
        time_left = deal.get("time_left")
        description = deal.get("description", "")
        url = self._trim_nintendo_url(deal["steam_url"], deal.get("nsuid"))

        price_line = price
        if original_price and original_price != price:
            price_line = f"{self._strikethrough(original_price)} {price}"

        source_line = f"{price_line} | {source}"
        if time_left:
            source_line = f"{price_line} | {time_left} | {source}"

        tags = "#NintendoDeals #NintendoSwitch #Gaming"
        head = f"🎮{name} {discount} off!\n{source_line}\n\n"
        tail = f"{url}\n{tags}"
        room = max_length - len(head) - len(tail) - 2
        if room > 0 and description:
            description = self._truncate_words(description, room)
            tweet = f"{head}{description}\n\n{tail}"
        else:
            tweet = f"{head}{tail}"
        return self._fit_to_max_length(tweet, max_length)

    @staticmethod
    def _discount_percent_from_deal(deal):
        match = re.search(r'(\d+)', deal.get('discount', '') or '')
        return int(match.group(1)) if match else 0

    @staticmethod
    def _price_usd_from_deal(deal):
        match = re.search(r'(\d[\d,]*\.?\d*)', deal.get('price', '') or '')
        if not match:
            return None
        return float(match.group(1).replace(',', ''))

    def _dedupe_deals_by_name(self, deals):
        unique_deals = []
        seen_names = set()
        for deal in deals:
            key = deal['name'].lower()
            if key in seen_names:
                continue
            unique_deals.append(deal)
            seen_names.add(key)
        return unique_deals

    def _finalize_collection_deals(self, deals, collection_label, count=COLLECTION_DEAL_COUNT):
        deals = self._dedupe_deals_by_name(deals)
        random.shuffle(deals)
        deals = deals[:count]
        # Keep tweet source on the usual sale label (active sale / Steam Specials),
        # not collection names like "Big Names" or "Hidden Gems".
        usual_source = self.get_active_sale_name() or DEFAULT_SOURCE_LABEL
        for deal in deals:
            deal['source'] = usual_source
        self._enrich_descriptions(deals)
        print_progress(f"Found {len(deals)} deals for {collection_label}")
        return deals

    def _filter_deals_by_max_price(self, deals, max_price_usd):
        filtered = []
        for deal in deals:
            price = self._price_usd_from_deal(deal)
            if price is not None and price <= max_price_usd:
                filtered.append(deal)
        return filtered

    def _sample_deals_across_price_buckets(self, deals, max_price_usd, count=COLLECTION_DEAL_COUNT):
        """Pick a varied mix across the full under-$X range, not only the cheapest games."""
        deals = self._dedupe_deals_by_name(deals)
        filtered = self._filter_deals_by_max_price(deals, max_price_usd)
        if not filtered:
            return []

        bucket_edges = [0.0, 1.25, 2.5, 4.0, max_price_usd + 0.01]
        buckets = [[] for _ in range(len(bucket_edges) - 1)]
        for deal in filtered:
            price = self._price_usd_from_deal(deal)
            for index in range(len(buckets)):
                low = bucket_edges[index]
                high = bucket_edges[index + 1]
                if low <= price < high:
                    buckets[index].append(deal)
                    break

        per_bucket = max(1, count // len(buckets))
        selected = []
        selected_keys = set()
        for bucket in buckets:
            random.shuffle(bucket)
            for deal in bucket[:per_bucket]:
                key = deal['name'].lower()
                if key in selected_keys:
                    continue
                selected_keys.add(key)
                selected.append(deal)

        if len(selected) < count:
            remaining = [
                deal for deal in filtered
                if deal['name'].lower() not in selected_keys
            ]
            random.shuffle(remaining)
            for deal in remaining:
                selected.append(deal)
                if len(selected) >= count:
                    break

        random.shuffle(selected)
        return selected[:count]

    def get_deal_mode_deals(self, mode_key, count=COLLECTION_DEAL_COUNT):
        config = DEAL_MODE_CONFIGS.get(mode_key)
        if not config:
            return []

        print_progress(f"Loading {config['label']}...")
        deals = []

        if mode_key == "big_names":
            for sort_by, start in POPULAR_SEARCH_PAGES[:3]:
                deals.extend(self._get_specials_page(start=start, count=20, sort_by=sort_by))
        elif mode_key == "popular_indies":
            data = self._fetch_search_results_json(
                start=0,
                count=max(count * 2, 50),
                sort_by="Reviews_DESC",
                tags="492",
            )
            if data and data.get('results_html'):
                source_label = self.get_active_sale_name() or DEFAULT_SOURCE_LABEL
                deals = self._parse_search_results_html(data['results_html'], source_label)
        elif mode_key == "hidden_gems":
            sort_by = random.choice(["Released_DESC", "Reviews_DESC"])
            total = self.get_total_specials_count()
            page_count = max(count, 25)
            if total and total > page_count:
                min_start = 150
                max_start = min(max(0, total - page_count), 2500)
                start = random.randint(min_start, max_start) if max_start > min_start else min_start
            else:
                start = 150
            deals = self._get_specials_page(start=start, count=page_count, sort_by=sort_by)
        elif mode_key == "deep_discounts":
            for start in (0, 50, 100, 150):
                deals.extend(self._get_specials_page(start=start, count=30, sort_by="Reviews_DESC"))
            deals = [
                deal for deal in deals
                if self._discount_percent_from_deal(deal) >= 70
            ]
            deals.sort(key=self._discount_percent_from_deal, reverse=True)

        return self._finalize_collection_deals(deals, config['label'], count=count)

    def get_category_deals(self, category_key, count=COLLECTION_DEAL_COUNT):
        config = DEAL_CATEGORY_CONFIGS.get(category_key)
        if not config:
            return []

        print_progress(f"Loading {config['label']} deals...")
        deals = []

        if category_key == "under_5":
            max_price = config['max_price_usd']
            for sort_by, start in POPULAR_SEARCH_PAGES:
                deals.extend(self._get_specials_page(start=start, count=25, sort_by=sort_by))

            total = self.get_total_specials_count()
            max_start = min(max(0, (total or 1000) - 50), 1200)
            for _ in range(3):
                start = random.randint(0, max_start) if max_start > 0 else 0
                sort_by = random.choice(["Reviews_DESC", "", "Released_DESC"])
                deals.extend(self._get_specials_page(start=start, count=50, sort_by=sort_by))

            deals = self._sample_deals_across_price_buckets(deals, max_price, count=count)
            if not deals:
                return []
            usual_source = self.get_active_sale_name() or DEFAULT_SOURCE_LABEL
            for deal in deals:
                deal['source'] = usual_source
            self._enrich_descriptions(deals)
            print_progress(f"Found {len(deals)} deals for {config['label']}")
            return deals
        else:
            data = self._fetch_search_results_json(
                start=0,
                count=max(count * 2, 50),
                sort_by="Reviews_DESC",
                tags=config['tags'],
            )
            if data and data.get('results_html'):
                source_label = self.get_active_sale_name() or DEFAULT_SOURCE_LABEL
                deals = self._parse_search_results_html(data['results_html'], source_label)

        return self._finalize_collection_deals(deals, config['label'], count=count)

    def get_random_specials(self, count=STEAM_DEAL_COUNT):
        """Get a balanced set of specials favoring reviewed/popular games.

        Most samples come from Steam's top review/relevance pages. A smaller
        discovery page still keeps room for under-the-radar games.
        """
        total = self.get_total_specials_count()
        page_count = max(20, count // 2)
        all_deals = []
        sampled_pages = []

        popular_pages = random.sample(POPULAR_SEARCH_PAGES, k=min(3, len(POPULAR_SEARCH_PAGES)))
        for sort_by, start in popular_pages:
            deals = self._get_specials_page(start=start, count=page_count, sort_by=sort_by)
            all_deals.extend(deals)
            sampled_pages.append(f"{sort_by or 'default'}@{start}:{len(deals)}")

        sort_by = random.choice(DISCOVERY_SEARCH_SORTS)
        if total and total > page_count:
            max_start = min(max(0, total - page_count), DISCOVERY_OFFSET_LIMIT)
            start = random.randint(0, max_start)
        else:
            start = 0
        deals = self._get_specials_page(start=start, count=page_count, sort_by=sort_by)
        all_deals.extend(deals)
        sampled_pages.append(f"{sort_by or 'default'}@{start}:{len(deals)}")

        # Dedupe while preserving the blended popular/discovery order.
        unique_deals = []
        seen_names = set()
        for deal in all_deals:
            key = deal['name'].lower()
            if key in seen_names:
                continue
            unique_deals.append(deal)
            seen_names.add(key)

        print_progress(f"Sampled {len(unique_deals)} specials ({', '.join(sampled_pages)})")
        return unique_deals[:count]

    def _generated_description(self, deal):
        return (
            f"{deal['name']} is now {deal['discount']} off on Steam. "
            "Grab it before the deal ends!"
        )

    def _ensure_real_description(self, deal):
        """Fetch a real Steam description for a single deal if it only has a
        generated/empty one (used for the deal we actually tweet)."""
        if deal.get('description') and deal['description'] != self._generated_description(deal):
            return deal
        try:
            info = self.get_game_info(deal['name'], deal['steam_url'])
            if info.get('description'):
                deal['description'] = info['description']
            if info.get('tags'):
                deal['tags'] = info['tags']
        except Exception:
            if not deal.get('description'):
                deal['description'] = self._generated_description(deal)
        return deal

    def _enrich_descriptions(self, deals, limit=DESCRIPTION_ENRICH_LIMIT):
        """Fetch real Steam descriptions for the first `limit` deals.

        The rest get a generated fallback so refreshes stay fast (each real
        description is an extra page request).
        """
        for i, deal in enumerate(deals):
            if deal.get('description'):
                continue
            if i < limit:
                try:
                    info = self.get_game_info(deal['name'], deal['steam_url'])
                    deal['description'] = info['description']
                    if info.get('tags'):
                        deal['tags'] = info['tags']
                    continue
                except Exception:
                    pass
            deal['description'] = self._generated_description(deal)
        return deals

    def get_fallback_deals(self):
        """Get some fallback deals if no real deals are found."""
        return [
            {
                'name': 'Steam Summer Sale',
                'discount': '-50%',
                'price': '$9.99',
                'original_price': '$19.99',
                'source': 'Steam Popular Deals',
                'description': 'Massive discounts on thousands of games during Steam\'s biggest sale event!',
                'steam_url': 'https://store.steampowered.com/specials/'
            },
            {
                'name': 'Indie Game Bundle',
                'discount': '-75%',
                'price': '$4.99',
                'original_price': '$19.99',
                'source': 'Steam Popular Deals',
                'description': 'Amazing collection of indie games at an incredible discount!',
                'steam_url': 'https://store.steampowered.com/specials/'
            },
            {
                'name': 'AAA Game Sale',
                'discount': '-30%',
                'price': '$34.99',
                'original_price': '$49.99',
                'source': 'Steam Popular Deals',
                'description': 'Popular AAA titles at discounted prices!',
                'steam_url': 'https://store.steampowered.com/specials/'
            }
        ]
    
    def _clean_game_name(self, game_name):
        """Clean up game name by removing extra text."""
        game_name = re.sub(r'\s+', ' ', game_name).strip()
        game_name = re.sub(r'\s*\d{1,2}\s+\w{3,9},?\s+\d{4}.*$', '', game_name)
        game_name = re.sub(r'\s*-\d+%.*$', '', game_name)
        game_name = re.sub(r'\s*Rp\s*\d+.*$', '', game_name)
        game_name = game_name.strip()
        return game_name
    
    def get_all_deals(self, sample_size=STEAM_DEAL_COUNT):
        """Get a varied set of Steam deals.

        Primary source is Steam's paginated search-results JSON with a random
        offset, so every refresh samples a different slice of the thousands of
        available specials. The curated featured API and the legacy scrapers
        are used only as fallbacks if the JSON endpoint returns nothing.
        """
        print_progress("Searching for Steam deals...")

        all_deals = list(self.get_random_specials(count=sample_size))

        # Fallback chain if the paginated endpoint returned nothing.
        if not all_deals:
            print_progress("Paginated search returned nothing, trying other sources...")
            all_deals.extend(self.get_steam_api_deals())
            all_deals.extend(self.get_steam_specials_page())
            all_deals.extend(self.get_steam_search_deals())

        if not all_deals:
            print_progress("No real deals found, using fallback examples...")
            all_deals = self.get_fallback_deals()

        # Remove duplicates based on game name.
        unique_deals = []
        seen_names = set()
        for deal in all_deals:
            if deal['name'].lower() not in seen_names:
                unique_deals.append(deal)
                seen_names.add(deal['name'].lower())

        # Keep the higher-signal popular/reviewed pages near the front, but
        # shuffle enough to avoid showing the exact same order every refresh.
        high_signal_count = max(1, (sample_size * 3) // 5)
        high_signal_deals = unique_deals[:high_signal_count]
        discovery_deals = unique_deals[high_signal_count:]
        random.shuffle(high_signal_deals)
        random.shuffle(discovery_deals)
        unique_deals = high_signal_deals + discovery_deals

        # Enrich main Steam list with sale countdown when we can map app IDs
        # to Steam's featured-categories discount expiration timestamps.
        self._attach_time_left_from_featured_api(unique_deals)

        # Fill in descriptions (real for the first few, generated for the rest).
        self._enrich_descriptions(unique_deals)

        print_progress(f"Found {len(unique_deals)} unique deals")
        return unique_deals

    @staticmethod
    def _truncate_words(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        if max_len <= 3:
            return text[:max_len]
        cut = text[: max_len - 3].rstrip()
        if ' ' in cut:
            cut = cut.rsplit(' ', 1)[0]
        return cut.rstrip() + '...'

    def _fit_to_max_length(self, text: str, max_len: int = TWEET_MAX_LENGTH) -> str:
        if len(text) <= max_len:
            return text
        return self._truncate_words(text, max_len)

    @staticmethod
    def _strikethrough(text: str) -> str:
        return ''.join(char + '\u0336' for char in text)

    @staticmethod
    def _trim_steam_url(url: str) -> str:
        app_match = re.search(r'store\.steampowered\.com/app/(\d+)', url)
        if app_match:
            return f"https://store.steampowered.com/app/{app_match.group(1)}/"
        return url

    @staticmethod
    def _trim_nintendo_url(url: str, nsuid=None) -> str:
        """Build a Nintendo storefront URL for tweets.

        Base-game NSUIDs (700100...) resolve cleanly via short eShop title links.
        DLC / bundle / AOC IDs (commonly 700700...) often fail on that path with
        error 9001-1630, so keep the storefront product URL for those instead.
        """
        nsuid_text = str(nsuid or "").strip()
        if not nsuid_text:
            match = re.search(r"ec\.nintendo\.com/[^/]+/[^/]+/titles/(\d+)", url or "")
            if match:
                nsuid_text = match.group(1)

        storefront_url = (url or "").split("?")[0]
        if nsuid_text.isdigit() and nsuid_text.startswith("700100"):
            return f"https://ec.nintendo.com/US/en/titles/{nsuid_text}"
        if storefront_url:
            return storefront_url
        if nsuid_text.isdigit():
            return f"https://ec.nintendo.com/US/en/titles/{nsuid_text}"
        return storefront_url

    @staticmethod
    def _steam_app_id_from_url(url: str):
        match = re.search(r'store\.steampowered\.com/app/(\d+)', url or '')
        return int(match.group(1)) if match else None

    def _attach_time_left_from_featured_api(self, deals):
        try:
            response = self.session.get(
                "https://store.steampowered.com/api/featuredcategories/?cc=us&l=english",
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            return

        expiration_by_app_id = {}
        for item in ((data.get("specials") or {}).get("items") or []):
            app_id = item.get("id")
            expiration = item.get("discount_expiration")
            if app_id and expiration:
                expiration_by_app_id[int(app_id)] = expiration

        for deal in deals:
            if deal.get("time_left"):
                continue
            app_id = self._steam_app_id_from_url(deal.get("steam_url"))
            if not app_id:
                continue
            expiration = expiration_by_app_id.get(app_id)
            if not expiration:
                continue
            deal["time_left"] = self._time_left_from_unix(expiration)

    def format_deal_tweet(self, deal, max_length: int = TWEET_MAX_LENGTH) -> str:
        """Format a single deal into a tweet (max 280 characters by default)."""
        name = deal['name']
        discount = deal['discount']
        price = deal['price']
        original_price = deal.get('original_price')
        time_left = deal.get('time_left')
        source = deal['source']
        description = deal.get('description', '')
        steam_url = self._trim_steam_url(deal['steam_url'])
        extra_hashtags = self._relevant_hashtags(deal)
        price_line = price
        if original_price and original_price != price:
            price_line = f"{self._strikethrough(original_price)} {price}"
        source_line = f"{price_line} | {source}"
        if time_left:
            source_line = f"{price_line} | {time_left} | {source}"

        def assemble(display_name: str, desc: str, extras) -> str:
            tags = "#SteamDeals #Gaming #Deals"
            if extras:
                tags += " " + " ".join(extras)
            head = f"🏷️{display_name} {discount} off!\n{source_line}\n\n"
            tail = f"{steam_url}\n{tags}"
            room = max_length - len(head) - len(tail) - 2
            if room > 0 and desc:
                desc = self._truncate_words(desc, room)
                return f"{head}{desc}\n\n{tail}"
            return f"{head}{tail}"

        display_name = name
        tweet = assemble(display_name, description, extra_hashtags)

        # If adding the relevant hashtags pushed us over, drop them one at a time
        # (keep the description readable rather than crammed).
        while len(tweet) > max_length and extra_hashtags:
            extra_hashtags = extra_hashtags[:-1]
            tweet = assemble(display_name, description, extra_hashtags)

        while len(tweet) > max_length and len(display_name) > 12:
            display_name = self._truncate_words(display_name, len(display_name) - 4)
            tweet = assemble(display_name, description, extra_hashtags)

        return self._fit_to_max_length(tweet, max_length)
    
    def get_best_deal_tweet(self):
        """Get the best deal formatted for tweeting."""
        deals = self.get_all_deals()
        
        if not deals:
            return self._fit_to_max_length(
                "🎮 No Steam deals found right now. Check back later! #SteamDeals #Gaming"
            )
        
        # Sort deals by discount percentage (highest first)
        def extract_discount_percent(deal):
            try:
                discount_text = deal['discount']
                if '-' in discount_text and '%' in discount_text:
                    return int(discount_text.replace('-', '').replace('%', ''))
                return 0
            except:
                return 0
        
        deals.sort(key=extract_discount_percent, reverse=True)
        best_deal = self._ensure_real_description(deals[0])
        
        return self.format_deal_tweet(best_deal)
    
    def get_multiple_deals_tweet(self, max_deals=3):
        """Get multiple deals in one tweet."""
        deals = self.get_all_deals()
        
        if not deals:
            return self._fit_to_max_length(
                "🎮 No Steam deals found right now. Check back later! #SteamDeals #Gaming"
            )
        
        # Sort deals by discount percentage
        def extract_discount_percent(deal):
            try:
                discount_text = deal['discount']
                if '-' in discount_text and '%' in discount_text:
                    return int(discount_text.replace('-', '').replace('%', ''))
                return 0
            except:
                return 0
        
        deals.sort(key=extract_discount_percent, reverse=True)
        top_deals = deals[:max_deals]
        for deal in top_deals:
            self._ensure_real_description(deal)
        
        intro = "🎮 Top Steam Deals:\n\n"
        outro = "\n#SteamDeals #Gaming #Deals"
        budget = TWEET_MAX_LENGTH - len(intro) - len(outro)

        deals_to_show = list(top_deals)
        name_limit = 40

        while True:
            lines = []
            for i, deal in enumerate(deals_to_show, 1):
                game_name = deal['name']
                if len(game_name) > name_limit:
                    game_name = game_name[: name_limit - 3] + '...'
                lines.append(f"{i}. {game_name} - {deal['price']} ({deal['discount']})\n")
            body = ''.join(lines)
            if len(body) <= budget:
                break
            if name_limit > 12:
                name_limit -= 6
            elif len(deals_to_show) > 1:
                deals_to_show = deals_to_show[:-1]
                name_limit = 40
            else:
                body = self._truncate_words(body, budget)
                break

        tweet = intro + body + outro
        return self._fit_to_max_length(tweet)

def main():
    """Test the Steam deal detector with API."""
    detector = SteamDealDetector()
    
    print("🚀 Testing Steam Deal Detector with API...")
    
    # Test single best deal
    print("\n📝 Best Deal Tweet:")
    best_tweet = detector.get_best_deal_tweet()
    print(best_tweet)
    print(f"Length: {len(best_tweet)} characters")
    
    # Test multiple deals
    print("\n📝 Multiple Deals Tweet:")
    multi_tweet = detector.get_multiple_deals_tweet()
    print(multi_tweet)
    print(f"Length: {len(multi_tweet)} characters")
    
    # Test raw deals
    print("\n📊 Raw Deals Data:")
    all_deals = detector.get_all_deals()
    for i, deal in enumerate(all_deals[:5], 1):
        print(f"{i}. {deal['name']} - {deal['price']} ({deal['discount']}) - {deal['source']}")
        print(f"   Description: {deal['description'][:100]}...")
        print(f"   URL: {deal['steam_url']}")

if __name__ == "__main__":
    main()
