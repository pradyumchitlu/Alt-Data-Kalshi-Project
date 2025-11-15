"""
Main data collection orchestrator
Runs all data collectors and manages the data pipeline
"""
import logging
import sys
from datetime import datetime, date, timedelta
import time

# Import all collectors
from spotify import SpotifyCollector
from youtube import YouTubeCollector
from itunes import iTunesCollector
from apple_music import AppleMusicCollector
from radio_airplay import RadioAirplayCollector
from tiktok import TikTokCollector
from google_trends import GoogleTrendsCollector
from kalshi_market import KalshiCollector
from database import DatabaseManager, initialize_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataCollectionOrchestrator:
    """Orchestrates all data collection activities"""
    
    def __init__(self):
        self.collectors = {
            'spotify': SpotifyCollector(),
            'youtube': YouTubeCollector(),
            'itunes': iTunesCollector(),
            'apple_music': AppleMusicCollector(),
            'radio': RadioAirplayCollector(),
            'tiktok': TikTokCollector(),
            'google_trends': GoogleTrendsCollector(),
            'kalshi': KalshiCollector()
        }
        self.results = {}
    
    def run_daily_collection(self):
        """Run daily data collection from all sources"""
        logger.info("=" * 80)
        logger.info("Starting daily data collection")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # 1. Collect Spotify data (kworb.net)
        logger.info("\n[1/8] Collecting Spotify data...")
        try:
            self.results['spotify'] = self.collectors['spotify'].collect_daily_data()
            logger.info(f"✓ Spotify collection: {'SUCCESS' if self.results['spotify'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ Spotify collection failed: {e}")
            self.results['spotify'] = False
        
        time.sleep(2)  # Rate limiting
        
        # 2. Collect YouTube data (kworb.net)
        logger.info("\n[2/8] Collecting YouTube data...")
        try:
            self.results['youtube'] = self.collectors['youtube'].collect_daily_data()
            logger.info(f"✓ YouTube collection: {'SUCCESS' if self.results['youtube'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ YouTube collection failed: {e}")
            self.results['youtube'] = False
        
        time.sleep(2)
        
        # 3. Collect iTunes sales data (kworb.net)
        logger.info("\n[3/8] Collecting iTunes data...")
        try:
            self.results['itunes'] = self.collectors['itunes'].collect_daily_data()
            logger.info(f"✓ iTunes collection: {'SUCCESS' if self.results['itunes'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ iTunes collection failed: {e}")
            self.results['itunes'] = False
        
        time.sleep(2)
        
        # 4. Collect Apple Music data (kworb.net)
        logger.info("\n[4/8] Collecting Apple Music data...")
        try:
            self.results['apple_music'] = self.collectors['apple_music'].collect_daily_data()
            logger.info(f"✓ Apple Music collection: {'SUCCESS' if self.results['apple_music'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ Apple Music collection failed: {e}")
            self.results['apple_music'] = False
        
        time.sleep(2)
        
        # 5. Collect radio airplay data (kworb.net)
        logger.info("\n[5/8] Collecting radio airplay data...")
        try:
            self.results['radio'] = self.collectors['radio'].collect_daily_data()
            logger.info(f"✓ Radio collection: {'SUCCESS' if self.results['radio'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ Radio collection failed: {e}")
            self.results['radio'] = False
        
        time.sleep(2)
        
        # 6. Collect TikTok data (API/scraping)
        logger.info("\n[6/8] Collecting TikTok data...")
        try:
            self.results['tiktok'] = self.collectors['tiktok'].collect_daily_data()
            logger.info(f"✓ TikTok collection: {'SUCCESS' if self.results['tiktok'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ TikTok collection failed: {e}")
            self.results['tiktok'] = False
        
        time.sleep(2)
        
        # 7. Collect Google Trends data
        # Get top songs from Spotify data to track in Google Trends
        logger.info("\n[7/8] Collecting Google Trends data...")
        try:
            # Get top songs from database
            top_songs = self.get_top_songs_for_trends()
            if top_songs:
                self.results['google_trends'] = self.collectors['google_trends'].collect_daily_data(top_songs)
                logger.info(f"✓ Google Trends collection: {'SUCCESS' if self.results['google_trends'] else 'FAILED'}")
            else:
                logger.warning("No top songs available for Google Trends")
                self.results['google_trends'] = False
        except Exception as e:
            logger.error(f"✗ Google Trends collection failed: {e}")
            self.results['google_trends'] = False
        
        time.sleep(2)
        
        # 8. Collect Kalshi market data
        logger.info("\n[8/8] Collecting Kalshi market data...")
        try:
            self.results['kalshi'] = self.collectors['kalshi'].collect_daily_data()
            logger.info(f"✓ Kalshi collection: {'SUCCESS' if self.results['kalshi'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ Kalshi collection failed: {e}")
            self.results['kalshi'] = False
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("Data Collection Summary")
        logger.info("=" * 80)
        
        successful = sum(1 for result in self.results.values() if result)
        total = len(self.results)
        
        for source, result in self.results.items():
            status = "✓ SUCCESS" if result else "✗ FAILED"
            logger.info(f"{source.upper()}: {status}")
        
        logger.info(f"\nTotal: {successful}/{total} sources collected successfully")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("=" * 80)
        
        return successful == total
    
    def get_top_songs_for_trends(self, limit=50):
        """Get top songs from database for Google Trends tracking"""
        db = DatabaseManager()
        if not db.connect():
            return []
        
        try:
            # Get most recent Spotify data
            query = """
                SELECT DISTINCT song_name, artist_name
                FROM spotify_streams
                WHERE collection_date = (SELECT MAX(collection_date) FROM spotify_streams)
                ORDER BY chart_position
                LIMIT %s
            """
            db.cursor.execute(query, (limit,))
            results = db.cursor.fetchall()
            
            songs = [(row[0], row[1]) for row in results]
            db.close()
            return songs
        except Exception as e:
            logger.error(f"Error fetching top songs: {e}")
            db.close()
            return []
    
    def run_historical_collection(self, start_date, end_date):
        """Run historical data collection for a date range"""
        logger.info(f"Starting historical collection from {start_date} to {end_date}")
        
        # Historical collection for sources that support it
        sources_with_historical = ['itunes', 'apple_music', 'radio']
        
        for source in sources_with_historical:
            logger.info(f"\nCollecting historical {source} data...")
            try:
                collector = self.collectors[source]
                collector.collect_historical_data(start_date, end_date)
            except Exception as e:
                logger.error(f"Historical collection failed for {source}: {e}")
        
        logger.info("Historical collection complete")


def main():
    """Main execution function"""
    # Initialize database
    logger.info("Initializing database...")
    initialize_database()
    
    # Create orchestrator
    orchestrator = DataCollectionOrchestrator()
    
    # Run daily collection
    orchestrator.run_daily_collection()
    
    # Optional: Run historical collection
    # Uncomment to collect historical data
    # start_date = date(2024, 9, 1)
    # end_date = date.today()
    # orchestrator.run_historical_collection(start_date, end_date)


if __name__ == "__main__":
    main()

