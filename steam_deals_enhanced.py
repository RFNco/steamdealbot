import requests
import json
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import urllib.parse

class SteamDealDetector:
    """Enhanced Steam deal detector with descriptions and store links."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_game_info(self, game_name, steam_url=None):
        """Get detailed game information including description and store link."""
        try:
            # If we have a Steam URL, use it directly
            if steam_url and 'steampowered.com' in steam_url:
                return self._scrape_game_page(steam_url, game_name)
            
            # Otherwise, try to find the game on Steam
            search_url = f"https://store.steampowered.com/search/?term={urllib.parse.quote(game_name)}"
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the first game result
            game_link = soup.find('a', href=re.compile(r'/app/\d+/'))
            if game_link:
                steam_url = game_link['href']
                if not steam_url.startswith('http'):
                    steam_url = 'https://store.steampowered.com' + steam_url
                return self._scrape_game_page(steam_url, game_name)
            
            return {
                'name': game_name,
                'description': 'A great game on sale!',
                'steam_url': f"https://store.steampowered.com/search/?term={urllib.parse.quote(game_name)}"
            }
            
        except Exception as e:
            print(f"Error getting game info for {game_name}: {e}")
            return {
                'name': game_name,
                'description': 'A great game on sale!',
                'steam_url': f"https://store.steampowered.com/search/?term={urllib.parse.quote(game_name)}"
            }
    
    def _scrape_game_page(self, steam_url, game_name):
        """Scrape a specific Steam game page for details."""
        try:
            response = self.session.get(steam_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract game description
            description_elem = soup.find('div', class_=re.compile(r'.*game.*description.*', re.I))
            if not description_elem:
                description_elem = soup.find('div', class_=re.compile(r'.*short.*description.*', re.I))
            if not description_elem:
                description_elem = soup.find('div', class_=re.compile(r'.*summary.*', re.I))
            
            description = "A great game on sale!"
            if description_elem:
                description = description_elem.get_text(strip=True)
                # Clean up description
                description = re.sub(r'\s+', ' ', description)
                if len(description) > 200:
                    description = description[:197] + "..."
            
            return {
                'name': game_name,
                'description': description,
                'steam_url': steam_url
            }
            
        except Exception as e:
            print(f"Error scraping game page {steam_url}: {e}")
            return {
                'name': game_name,
                'description': 'A great game on sale!',
                'steam_url': steam_url
            }
    
    def get_daily_deals(self):
        """Get daily deals from Steam's specials page."""
        try:
            url = "https://store.steampowered.com/specials"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            deals = []
            
            # Look for game containers in the specials page
            game_containers = soup.find_all('div', class_=re.compile(r'.*game.*|.*item.*', re.I))
            
            for container in game_containers[:10]:  # Check more containers
                try:
                    # Get all text content
                    text_content = container.get_text()
                    
                    # Look for discount pattern in the text
                    discount_match = re.search(r'(-\d+%)', text_content)
                    if not discount_match:
                        continue
                    
                    discount = discount_match.group(1)
                    
                    # Look for price pattern
                    price_match = re.search(r'([\$€£]\d+\.?\d*|Rp\s*\d+)', text_content)
                    if not price_match:
                        continue
                    
                    price = price_match.group(1)
                    
                    # Look for game name and Steam link
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
                            if len(line) > 5 and len(line) < 100 and not re.match(r'^[\$€£]\d+', line) and not re.match(r'^-\d+%', line):
                                game_name = line
                                break
                        
                        if not game_name:
                            continue
                        
                        steam_url = f"https://store.steampowered.com/search/?term={urllib.parse.quote(game_name)}"
                    
                    if not game_name or len(game_name) < 3:
                        continue
                    
                    # Clean up game name - remove extra text and dates
                    game_name = re.sub(r'\s+', ' ', game_name).strip()
                    # Remove common extra text patterns - more aggressive cleaning
                    game_name = re.sub(r'\s*\d{1,2}\s+\w{3,9},?\s+\d{4}.*$', '', game_name)  # Remove dates
                    game_name = re.sub(r'\s*-\d+%.*$', '', game_name)  # Remove discount text
                    game_name = re.sub(r'\s*Rp\s*\d+.*$', '', game_name)  # Remove price text
                    game_name = re.sub(r'\s*\d+.*$', '', game_name)  # Remove any trailing numbers
                    game_name = game_name.strip()
                    
                    # Get additional game info
                    game_info = self.get_game_info(game_name, steam_url)
                    
                    deal = {
                        'name': game_name,
                        'discount': discount,
                        'price': price,
                        'original_price': None,
                        'source': 'Steam Daily Deals',
                        'description': game_info['description'],
                        'steam_url': game_info['steam_url']
                    }
                    deals.append(deal)
                    
                except Exception as e:
                    continue
                    
            return deals
            
        except Exception as e:
            print(f"Error fetching daily deals: {e}")
            return []
    
    def get_popular_deals(self):
        """Get popular discounted games from Steam search."""
        try:
            # Use Steam's search for discounted games
            url = "https://store.steampowered.com/search/?sort_by=Reviews_DESC&specials=1&page=1"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            deals = []
            
            # Look for game containers in search results
            game_containers = soup.find_all('div', class_=re.compile(r'.*search.*result.*', re.I))
            
            for container in game_containers[:5]:  # Limit to top 5
                try:
                    # Get all text content
                    text_content = container.get_text()
                    
                    # Look for discount pattern
                    discount_match = re.search(r'(-\d+%)', text_content)
                    if not discount_match:
                        continue
                    
                    discount = discount_match.group(1)
                    
                    # Look for price pattern
                    price_match = re.search(r'([\$€£]\d+\.?\d*|Rp\s*\d+)', text_content)
                    if not price_match:
                        continue
                    
                    price = price_match.group(1)
                    
                    # Look for game name and Steam link
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
                    
                    # Clean up game name - remove extra text and dates
                    game_name = re.sub(r'\s+', ' ', game_name).strip()
                    # Remove common extra text patterns - more aggressive cleaning
                    game_name = re.sub(r'\s*\d{1,2}\s+\w{3,9},?\s+\d{4}.*$', '', game_name)  # Remove dates
                    game_name = re.sub(r'\s*-\d+%.*$', '', game_name)  # Remove discount text
                    game_name = re.sub(r'\s*Rp\s*\d+.*$', '', game_name)  # Remove price text
                    game_name = re.sub(r'\s*\d+.*$', '', game_name)  # Remove any trailing numbers
                    game_name = game_name.strip()
                    
                    # Get additional game info
                    game_info = self.get_game_info(game_name, steam_url)
                    
                    deal = {
                        'name': game_name,
                        'discount': discount,
                        'price': price,
                        'original_price': None,
                        'source': 'Steam Popular Deals',
                        'description': game_info['description'],
                        'steam_url': game_info['steam_url']
                    }
                    deals.append(deal)
                    
                except Exception as e:
                    continue
                    
            return deals
            
        except Exception as e:
            print(f"Error fetching popular deals: {e}")
            return []
    
    def get_all_deals(self):
        """Get all available deals from different sources."""
        print("🔍 Searching for Steam deals...")
        
        all_deals = []
        
        # Get deals from different sources
        daily_deals = self.get_daily_deals()
        popular_deals = self.get_popular_deals()
        
        all_deals.extend(daily_deals)
        all_deals.extend(popular_deals)
        
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
        """Format a single deal into a tweet in the requested format."""
        # Extract discount percentage for hashtag
        discount_percent = deal['discount'].replace('-', '').replace('%', '')
        
        # Format the tweet in the requested style
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
    """Test the enhanced Steam deal detector."""
    detector = SteamDealDetector()
    
    print("🚀 Testing Enhanced Steam Deal Detector...")
    
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
    for i, deal in enumerate(all_deals[:3], 1):
        print(f"{i}. {deal['name']} - {deal['price']} ({deal['discount']}) - {deal['source']}")
        print(f"   Description: {deal['description'][:100]}...")
        print(f"   URL: {deal['steam_url']}")

if __name__ == "__main__":
    main()
