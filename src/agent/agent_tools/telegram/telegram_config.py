import os

class TelegramConfig:
    def __init__(self):
        # Bot behavior settings
        self.RESPONSE_DELAY = 1.0  
        self.MAX_MESSAGE_LENGTH = 4096  # Telegram's maximum message length
        
        # Crypto-specific keywords
        self.CRYPTO_KEYWORDS = [
            "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", 
            "price", "trending", "market", "trading", "drophunting", "airdrop", "rewards",
            "yield", "farming", "staking", "protocol", "token", "coin", "altcoin", "funds", "investors"
        ]
        
        # CryptoRank API settings
        self.CRYPTO_API_TIMEOUT = 30  # Timeout for CryptoRank API calls in seconds
        self.CRYPTO_API_MAX_RETRIES = 3  # Maximum retries for failed API calls
        self.CRYPTO_CACHE_DURATION = 60  # Cache duration for price data in seconds
        self.CRYPTO_API_BASE_URL = "https://api.cryptorank.io/v2"  # CryptoRank v2 API base URL
        
        # API Key configuration - users should set this via environment variable
        # Users can set CRYPTORANK_API_KEY environment variable
        self.CRYPTO_API_KEY = os.getenv('CRYPTORANK_API_KEY')
              
        # Price alert settings
        self.PRICE_ALERT_ENABLED = True
        self.PRICE_ALERT_THRESHOLD = 0.05  # 5% change threshold for alerts
                
        # Trending settings
        self.TRENDING_MAX_CRYPTOS = 10  # Maximum cryptocurrencies to show
        self.TRENDING_MIN_MARKET_CAP = 10000000  # Minimum market cap (10M)
        
        # Logging settings
        self.LOG_LEVEL = "INFO"
        self.LOG_USER_MESSAGES = False  
        
        # Bot personality settings
        self.BOT_NAME = "DobbyXBT Bot"
        self.BOT_PERSONALITY = "crypto-savvy and helpful"
        
        # Rate limiting (messages per minute per user)
        self.RATE_LIMIT_PER_USER = 20  # Increased for DobbyXBT Bot
        self.RATE_LIMIT_WINDOW = 60  # seconds
        
        # Crypto-specific emojis
        self.CRYPTO_EMOJIS = {
            'bitcoin': '₿',
            'ethereum': 'Ξ',
            'price_up': '📈',
            'price_down': '📉',
            'drophunting': '🎯',
            'airdrop': '🪂',
            'rewards': '🎁',
            'funds': '💰',
            'investors': '🏦',
            'trending': '🔥',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        }
