"""
Kalshi market data collection
Collects real-time trading data for Billboard Hot 100 #1 song contracts
"""
import requests
import logging
from datetime import datetime
import json
from config import KALSHI_API_KEY, KALSHI_API_SECRET
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KalshiCollector:
    """Collects market data from Kalshi API"""
    
    def __init__(self):
        self.api_key = KALSHI_API_KEY
        self.api_secret = KALSHI_API_SECRET
        self.base_url = "https://trading-api.kalshi.com/trade-api/v2"
        self.demo_base_url = "https://demo-api.kalshi.co/trade-api/v2"
        self.access_token = None
        
    def authenticate(self):
        """Authenticate with Kalshi API"""
        # Kalshi uses email/password or API key authentication
        # This is a placeholder - actual implementation depends on Kalshi's auth method
        
        if not self.api_key:
            logger.warning("Kalshi API credentials not configured")
            return False
        
        try:
            # Using demo API endpoint for authentication
            url = f"{self.demo_base_url}/login"
            
            # Kalshi typically uses email/password for authentication
            # You'll need to adjust this based on actual Kalshi API requirements
            headers = {
                "Content-Type": "application/json"
            }
            
            # Note: Replace with actual authentication method
            # This is just a template
            payload = {
                "email": self.api_key,  # Or however Kalshi expects credentials
                "password": self.api_secret
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get('token')
            logger.info("Kalshi authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Kalshi authentication failed: {e}")
            return False
    
    def get_billboard_markets(self):
        """Get all active Billboard Hot 100 related markets"""
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            url = f"{self.demo_base_url}/markets"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Search for Billboard-related markets
            params = {
                "series_ticker": "BILLBOARD",  # Adjust based on actual Kalshi naming
                "status": "open"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching Billboard markets: {e}")
            return None
    
    def get_market_data(self, market_ticker):
        """Get detailed market data for a specific ticker"""
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            url = f"{self.demo_base_url}/markets/{market_ticker}"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching market data for {market_ticker}: {e}")
            return None
    
    def get_orderbook(self, market_ticker):
        """Get order book for a specific market"""
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            url = f"{self.demo_base_url}/markets/{market_ticker}/orderbook"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching orderbook for {market_ticker}: {e}")
            return None
    
    def collect_daily_data(self):
        """Collect current Kalshi market data for Billboard contracts"""
        logger.info("Starting Kalshi market data collection")
        
        # Get all Billboard markets
        markets = self.get_billboard_markets()
        
        if not markets:
            logger.error("Failed to fetch Billboard markets")
            return False
        
        data_to_insert = []
        current_time = datetime.now()
        
        # Process each market
        market_list = markets.get('markets', [])
        
        for market in market_list:
            try:
                ticker = market.get('ticker', '')
                title = market.get('title', '')
                
                # Extract song/artist info from market title
                # Format might be: "Will [Song] by [Artist] be #1 on Billboard Hot 100?"
                song_name, artist_name = self.parse_market_title(title)
                
                # Get current prices
                yes_price = market.get('yes_bid', 0) / 100  # Convert cents to dollars
                no_price = market.get('no_bid', 0) / 100
                
                # Get volume and open interest
                volume = market.get('volume', 0)
                open_interest = market.get('open_interest', 0)
                
                # Calculate implied probability from yes price
                implied_prob = yes_price
                
                data_to_insert.append((
                    ticker,
                    song_name,
                    artist_name,
                    yes_price,
                    no_price,
                    volume,
                    open_interest,
                    implied_prob,
                    current_time
                ))
                
            except Exception as e:
                logger.warning(f"Error processing market {ticker}: {e}")
                continue
        
        # Insert into database
        if data_to_insert:
            db = DatabaseManager()
            if db.connect():
                success = db.insert_kalshi_data(data_to_insert)
                db.close()
                
                if success:
                    logger.info(f"Successfully collected data for {len(data_to_insert)} markets")
                    return True
        
        return False
    
    def parse_market_title(self, title):
        """
        Parse song and artist from market title
        Example: "Will 'Paint The Town Red' by Doja Cat be #1?"
        """
        song_name = "Unknown"
        artist_name = "Unknown"
        
        try:
            # Look for pattern: 'Song Title' by Artist Name
            if "'" in title and " by " in title:
                song_part = title.split("'")[1]
                artist_part = title.split(" by ")[1].split(" be")[0]
                song_name = song_part.strip()
                artist_name = artist_part.strip()
            elif '"' in title and " by " in title:
                song_part = title.split('"')[1]
                artist_part = title.split(" by ")[1].split(" be")[0]
                song_name = song_part.strip()
                artist_name = artist_part.strip()
        except Exception as e:
            logger.warning(f"Could not parse market title: {title}")
        
        return song_name, artist_name


def main():
    """Main execution function"""
    collector = KalshiCollector()
    
    logger.info("Kalshi collector initialized")
    logger.info("Note: Requires valid Kalshi API credentials in .env file")
    logger.info("Configure KALSHI_API_KEY and KALSHI_API_SECRET to use this collector")
    
    # collector.collect_daily_data()


if __name__ == "__main__":
    main()

