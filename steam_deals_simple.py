import requests
import json
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

class SteamDealDetector:
    """Detects and formats Steam game deals for posting."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
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
                    
                    # Look for game name (usually in a link or title)
                    name_elem = container.find('a') or container.find('div', class_=re.compile(r'.*title.*|.*name.*', re.I))
                    if not name_elem:
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
                    else:
                        game_name = name_elem.get_text(strip=True)
                    
                    if not game_name or len(game_name) < 3:
                        continue
                    
                    # Clean up game name
                    game_name = re.sub(r'\s+', ' ', game_name).strip()
                    
                    deal = {
                        'name': game_name,
                        'discount': discount,
                        'price': price,
                        'original_price': None,
                        'source': 'Steam Daily Deals'
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
                    
                    # Look for game name
                    name_elem = container.find('a') or container.find('div', class_=re.compile(r'.*title.*|.*name.*', re.I))
                    if not name_elem:
                        continue
                    
                    game_name = name_elem.get_text(strip=True)
                    if not game_name or len(game_name) < 3:
                        continue
                    
                    # Clean up game name
                    game_name = re.sub(r'\s+', ' ', game_name).strip()
                    
                    deal = {
                        'name': game_name,
                        'discount': discount,
                        'price': price,
                        'original_price': None,
                        'source': 'Steam Popular Deals'
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
        """Format a single deal into a tweet."""
        # Truncate game name if too long
        game_name = deal['name']
        if len(game_name) > 50:
            game_name = game_name[:47] + "..."
        
        # Format the tweet
        tweet = f"🎮 {game_name}\n"
        tweet += f"💰 {deal['price']} ({deal['discount']} off!)\n"
        tweet += f"🏷️ {deal['source']}\n"
        tweet += f"#SteamDeals #Gaming #Deals"
        
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
    """Test the Steam deal detector."""
    detector = SteamDealDetector()
    
    print("🚀 Testing Steam Deal Detector...")
    
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

if __name__ == "__main__":
    main()
