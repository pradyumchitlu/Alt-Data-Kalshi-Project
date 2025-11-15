"""
Google Trends data collection for Billboard Hot 100 prediction
Collects search interest data for songs and artists
"""
from pytrends.request import TrendReq
import logging
from datetime import datetime, date, timedelta
import time
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleTrendsCollector:
    """Collects search interest data from Google Trends"""
    
    def __init__(self):
        # Initialize pytrends
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.region = 'US'
        
    def get_interest_over_time(self, keywords, timeframe='now 7-d'):
        """Get search interest over time for keywords"""
        try:
            # Build payload
            self.pytrends.build_payload(
                keywords,
                cat=0,  # All categories
                timeframe=timeframe,
                geo=self.region,
                gprop=''  # Web search
            )
            
            # Get interest over time
            interest_df = self.pytrends.interest_over_time()
            
            if not interest_df.empty:
                # Remove 'isPartial' column if present
                if 'isPartial' in interest_df.columns:
                    interest_df = interest_df.drop(columns=['isPartial'])
                return interest_df
            
            return None
        except Exception as e:
            logger.error(f"Error fetching Google Trends data: {e}")
            return None
    
    def get_trending_searches(self, country='united_states'):
        """Get currently trending searches"""
        try:
            trending_df = self.pytrends.trending_searches(pn=country)
            return trending_df
        except Exception as e:
            logger.error(f"Error fetching trending searches: {e}")
            return None
    
    def get_related_queries(self, keyword):
        """Get related queries for a keyword"""
        try:
            self.pytrends.build_payload([keyword], timeframe='now 7-d', geo=self.region)
            related_queries = self.pytrends.related_queries()
            return related_queries
        except Exception as e:
            logger.error(f"Error fetching related queries: {e}")
            return None
    
    def calculate_momentum(self, interest_df):
        """Calculate search momentum from interest over time data"""
        if interest_df is None or interest_df.empty:
            return 0
        
        # Get last 7 days average vs previous 7 days average
        recent_avg = interest_df.iloc[-7:].mean().values[0] if len(interest_df) >= 7 else 0
        previous_avg = interest_df.iloc[-14:-7].mean().values[0] if len(interest_df) >= 14 else recent_avg
        
        if previous_avg == 0:
            return 0
        
        momentum = ((recent_avg - previous_avg) / previous_avg) * 100
        return momentum
    
    def collect_song_data(self, song_list):
        """
        Collect Google Trends data for a list of songs
        song_list: List of tuples (song_name, artist_name)
        """
        logger.info(f"Starting Google Trends collection for {len(song_list)} songs")
        
        data_to_insert = []
        today = date.today()
        
        # Process songs in batches (Google Trends allows max 5 keywords at once)
        batch_size = 5
        
        for i in range(0, len(song_list), batch_size):
            batch = song_list[i:i+batch_size]
            keywords = [f"{song} {artist}" for song, artist in batch]
            
            try:
                # Get interest over time
                interest_df = self.get_interest_over_time(keywords, timeframe='now 7-d')
                
                if interest_df is not None:
                    # Process each song in the batch
                    for idx, (song, artist) in enumerate(batch):
                        keyword = f"{song} {artist}"
                        
                        if keyword in interest_df.columns:
                            # Get current interest level (last value)
                            current_interest = interest_df[keyword].iloc[-1]
                            
                            # Calculate momentum
                            momentum = self.calculate_momentum(interest_df[[keyword]])
                            
                            # Determine trend direction
                            if momentum > 10:
                                trend_direction = "rising"
                            elif momentum < -10:
                                trend_direction = "falling"
                            else:
                                trend_direction = "stable"
                            
                            data_to_insert.append((
                                song,
                                artist,
                                int(current_interest),
                                trend_direction,
                                today
                            ))
                
                # Rate limiting - Google may block excessive requests
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                time.sleep(5)  # Longer wait on error
                continue
        
        # Insert into database
        if data_to_insert:
            db = DatabaseManager()
            if db.connect():
                # Note: Would need to add insert_google_trends_data method
                try:
                    query = """
                        INSERT INTO google_trends 
                        (song_name, artist_name, search_interest, trend_direction, collection_date)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (song_name, artist_name, collection_date) DO UPDATE SET
                            search_interest = EXCLUDED.search_interest,
                            trend_direction = EXCLUDED.trend_direction
                    """
                    for data in data_to_insert:
                        db.cursor.execute(query, data)
                    db.conn.commit()
                    logger.info(f"Successfully collected Google Trends data for {len(data_to_insert)} songs")
                    db.close()
                    return True
                except Exception as e:
                    logger.error(f"Error inserting Google Trends data: {e}")
                    db.conn.rollback()
                    db.close()
        
        return False
    
    def collect_daily_data(self, top_songs):
        """
        Main method to collect daily Google Trends data
        top_songs: List of tuples (song_name, artist_name)
        """
        logger.info("Starting Google Trends data collection")
        
        if not top_songs:
            logger.warning("No songs provided for Google Trends collection")
            return False
        
        return self.collect_song_data(top_songs)


def main():
    """Main execution function"""
    collector = GoogleTrendsCollector()
    
    # Example: Collect data for sample songs
    sample_songs = [
        ("Paint The Town Red", "Doja Cat"),
        ("Cruel Summer", "Taylor Swift"),
        ("greedy", "Tate McRae"),
        ("Is It Over Now?", "Taylor Swift"),
        ("Strangers", "Kenya Grace")
    ]
    
    collector.collect_daily_data(sample_songs)


if __name__ == "__main__":
    main()

