import requests
import json
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import urllib.parse

class SteamDealDetector:
    """Steam deal detector using multiple methods including API calls."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        
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
            
            return {
                'description': description,
                'steam_url': steam_url
            }
            
        except Exception as e:
            # Fallback description based on game name
            return {
                'description': f"Experience {game_name} - an exciting game now on sale!",
                'steam_url': steam_url
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
    
    def get_all_deals(self):
        """Get all available deals from different sources."""
        print("🔍 Searching for Steam deals...")
        
        all_deals = []
        
        # Try different methods
        api_deals = self.get_steam_api_deals()
        specials_deals = self.get_steam_specials_page()
        search_deals = self.get_steam_search_deals()
        
        all_deals.extend(api_deals)
        all_deals.extend(specials_deals)
        all_deals.extend(search_deals)
        
        # If no real deals found, use fallback
        if not all_deals:
            print("⚠️ No real deals found, using fallback examples...")
            all_deals = self.get_fallback_deals()
        
        # Remove duplicates based on game name
        unique_deals = []
        seen_names = set()
        
        for deal in all_deals:
            if deal['name'].lower() not in seen_names:
                unique_deals.append(deal)
                seen_names.add(deal['name'].lower())
        
        print(f"✅ Found {len(unique_deals)} unique deals")
        return unique_deals
    
    def format_deal_tweet(self, deal):
        """Format a single deal into a tweet."""
        tweet = f"🏷️{deal['name']} {deal['discount']} off!\n"
        tweet += f"{deal['price']}  |  {deal['source']}\n\n"
        tweet += f"{deal['description']}\n\n"
        tweet += f"{deal['steam_url']}\n"
        tweet += f"#SteamDeals #Gaming #Deals #{deal['name'].replace(' ', '').replace('-', '').replace(':', '')[:20]}"
        
        return tweet
    
    def get_best_deal_tweet(self):
        """Get the best deal formatted for tweeting."""
        deals = self.get_all_deals()
        
        if not deals:
            return "🎮 No Steam deals found right now. Check back later! #SteamDeals #Gaming"
        
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
        best_deal = deals[0]
        
        return self.format_deal_tweet(best_deal)
    
    def get_multiple_deals_tweet(self, max_deals=3):
        """Get multiple deals in one tweet."""
        deals = self.get_all_deals()
        
        if not deals:
            return "🎮 No Steam deals found right now. Check back later! #SteamDeals #Gaming"
        
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
        
        tweet = "🎮 Top Steam Deals:\n\n"
        
        for i, deal in enumerate(top_deals, 1):
            game_name = deal['name']
            if len(game_name) > 30:
                game_name = game_name[:27] + "..."
            
            tweet += f"{i}. {game_name} - {deal['price']} ({deal['discount']})\n"
        
        tweet += "\n#SteamDeals #Gaming #Deals"
        
        return tweet

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
