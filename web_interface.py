from flask import Flask, render_template_string, jsonify
from steam_deals_enhanced import SteamDealDetector
import json

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SteamDealBot - Manual Posting</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1da1f2;
            text-align: center;
            margin-bottom: 30px;
        }
        .deal-card {
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            background: #fafafa;
        }
        .deal-tweet {
            background: #1da1f2;
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            white-space: pre-wrap;
            margin: 10px 0;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .deal-tweet:hover {
            background: #0d8bd9;
        }
        .copy-btn {
            background: #17bf63;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px;
            font-size: 14px;
        }
        .copy-btn:hover {
            background: #14a855;
        }
        .refresh-btn {
            background: #1da1f2;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 20px 0;
        }
        .refresh-btn:hover {
            background: #0d8bd9;
        }
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 SteamDealBot - Manual Posting</h1>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="refreshDeals()">🔄 Refresh Deals</button>
        </div>
        
        <div id="status" class="status info">
            Click "Refresh Deals" to get the latest Steam deals!
        </div>
        
        <div id="deals-container">
            <!-- Deals will be loaded here -->
        </div>
    </div>

    <script>
        function refreshDeals() {
            document.getElementById('status').innerHTML = '🔄 Loading deals...';
            document.getElementById('status').className = 'status info';
            
            fetch('/api/deals')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayDeals(data.deals);
                        document.getElementById('status').innerHTML = `✅ Found ${data.deals.length} deals!`;
                        document.getElementById('status').className = 'status success';
                    } else {
                        document.getElementById('status').innerHTML = `❌ Error: ${data.error}`;
                        document.getElementById('status').className = 'status error';
                    }
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = `❌ Error: ${error.message}`;
                    document.getElementById('status').className = 'status error';
                });
        }
        
        function displayDeals(deals) {
            const container = document.getElementById('deals-container');
            container.innerHTML = '';
            
            deals.forEach((deal, index) => {
                const dealCard = document.createElement('div');
                dealCard.className = 'deal-card';
                dealCard.innerHTML = `
                    <h3>🎮 ${deal.name}</h3>
                    <p><strong>Price:</strong> ${deal.price} (${deal.discount})</p>
                    <p><strong>Source:</strong> ${deal.source}</p>
                    <p><strong>Description:</strong> ${deal.description}</p>
                    <p><strong>Steam URL:</strong> <a href="${deal.steam_url}" target="_blank">${deal.steam_url}</a></p>
                    
                    <div class="deal-tweet" onclick="copyToClipboard('tweet-${index}')">
                        ${deal.tweet}
                    </div>
                    
                    <button class="copy-btn" onclick="copyToClipboard('tweet-${index}')">
                        📋 Copy Tweet
                    </button>
                    <button class="copy-btn" onclick="openTwitter('${deal.tweet}')">
                        🐦 Open Twitter
                    </button>
                `;
                container.appendChild(dealCard);
            });
        }
        
        function copyToClipboard(tweetId) {
            const tweetElement = document.querySelector(`[onclick="copyToClipboard('${tweetId}')"]`);
            const tweetText = tweetElement.textContent;
            
            navigator.clipboard.writeText(tweetText).then(() => {
                alert('✅ Tweet copied to clipboard!');
            }).catch(err => {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = tweetText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('✅ Tweet copied to clipboard!');
            });
        }
        
        function openTwitter(tweetText) {
            const encodedTweet = encodeURIComponent(tweetText);
            window.open(`https://twitter.com/intent/tweet?text=${encodedTweet}`, '_blank');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/deals')
def get_deals():
    try:
        detector = SteamDealDetector()
        deals = detector.get_all_deals()
        
        # Format deals for the web interface
        formatted_deals = []
        for deal in deals:
            tweet = detector.format_deal_tweet(deal)
            formatted_deals.append({
                'name': deal['name'],
                'price': deal['price'],
                'discount': deal['discount'],
                'source': deal['source'],
                'description': deal['description'],
                'steam_url': deal['steam_url'],
                'tweet': tweet
            })
        
        return jsonify({
            'success': True,
            'deals': formatted_deals
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🌐 Starting SteamDealBot Web Interface...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🔄 Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)
