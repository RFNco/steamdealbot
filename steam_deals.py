import requests
import json
import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import urllib.parse

TWEET_MAX_LENGTH = 280

# Steam's "infinite scroll" search results endpoint returns clean JSON and
# supports pagination, which lets us sample a different slice of specials on
# every refresh (thousands of deals are available, not just the curated ~10).
STEAM_SEARCH_RESULTS_URL = "https://store.steampowered.com/search/results/"
# How many descriptions to enrich per refresh (each one is an extra page load).
DESCRIPTION_ENRICH_LIMIT = 12
# Rotate sort orders for extra variety between refreshes.
SEARCH_SORT_ORDERS = ["", "Reviews_DESC", "Released_DESC", "_ASC", "_DESC"]

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
                    print(f"Active sale detected: {label}")
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

    def _fetch_search_results_json(self, start=0, count=50, sort_by=""):
        """Call Steam's paginated search-results JSON endpoint.

        Returns the parsed JSON dict (with 'total_count' and 'results_html'),
        or None on failure.
        """
        params = {
            'query': '',
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

    def get_random_specials(self, count=50):
        """Get a randomly-offset page of specials for variety on each refresh."""
        total = self.get_total_specials_count()

        sort_by = random.choice(SEARCH_SORT_ORDERS)

        if total and total > count:
            max_start = max(0, total - count)
            start = random.randint(0, max_start)
        else:
            start = 0

        data = self._fetch_search_results_json(start=start, count=count, sort_by=sort_by)
        if not data or not data.get('results_html'):
            return []

        source_label = self.get_active_sale_name() or DEFAULT_SOURCE_LABEL
        deals = self._parse_search_results_html(data['results_html'], source_label=source_label)
        print(f"Sampled {len(deals)} specials (offset {start}, sort '{sort_by or 'default'}')")
        return deals

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
        game_name = re.sub(r'\s*\d+.*$', '', game_name)
        game_name = game_name.strip()
        return game_name
    
    def get_all_deals(self, sample_size=50):
        """Get a varied set of Steam deals.

        Primary source is Steam's paginated search-results JSON with a random
        offset, so every refresh samples a different slice of the thousands of
        available specials. The curated featured API and the legacy scrapers
        are used only as fallbacks if the JSON endpoint returns nothing.
        """
        print("Searching for Steam deals...")

        all_deals = list(self.get_random_specials(count=sample_size))

        # Fallback chain if the paginated endpoint returned nothing.
        if not all_deals:
            print("Paginated search returned nothing, trying other sources...")
            all_deals.extend(self.get_steam_api_deals())
            all_deals.extend(self.get_steam_specials_page())
            all_deals.extend(self.get_steam_search_deals())

        if not all_deals:
            print("No real deals found, using fallback examples...")
            all_deals = self.get_fallback_deals()

        # Remove duplicates based on game name.
        unique_deals = []
        seen_names = set()
        for deal in all_deals:
            if deal['name'].lower() not in seen_names:
                unique_deals.append(deal)
                seen_names.add(deal['name'].lower())

        # Shuffle so the displayed order also varies between refreshes.
        random.shuffle(unique_deals)

        # Fill in descriptions (real for the first few, generated for the rest).
        self._enrich_descriptions(unique_deals)

        print(f"Found {len(unique_deals)} unique deals")
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

    def format_deal_tweet(self, deal, max_length: int = TWEET_MAX_LENGTH) -> str:
        """Format a single deal into a tweet (max 280 characters by default)."""
        name = deal['name']
        discount = deal['discount']
        price = deal['price']
        original_price = deal.get('original_price')
        source = deal['source']
        description = deal.get('description', '')
        steam_url = self._trim_steam_url(deal['steam_url'])
        extra_hashtags = self._relevant_hashtags(deal)
        price_line = price
        if original_price and original_price != price:
            price_line = f"{self._strikethrough(original_price)} {price}"

        def assemble(display_name: str, desc: str, extras) -> str:
            tags = "#SteamDeals #Gaming #Deals"
            if extras:
                tags += " " + " ".join(extras)
            head = f"🏷️{display_name} {discount} off!\n{price_line} | {source}\n\n"
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
