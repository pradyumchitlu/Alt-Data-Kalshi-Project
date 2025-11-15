"""
Apple Music data collection from kworb.net
Scrapes Apple Music streaming data from kworb.net
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, date, timedelta
import re
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppleMusicCollector:
    """Collects streaming data from kworb.net Apple Music charts"""
    
    def __init__(self):
        self.base_url = "https://kworb.net/apple_songs/"
        self.archive_url = "https://kworb.net/apple_songs/archive/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def parse_number(self, text):
        """Parse number from text (handles commas)"""
        if not text:
            return 0
        cleaned = re.sub(r'[,\s]', '', text)
        try:
            return int(cleaned)
        except ValueError:
            return 0
    
    def get_latest_archive_date(self):
        """Get the most recent date from the archive"""
        yesterday = date.today() - timedelta(days=1)
        return yesterday.strftime('%Y%m%d')
    
    def scrape_apple_music_chart(self, chart_date=None):
        """
        Scrape Apple Music chart from kworb.net
        chart_date: string in format YYYYMMDD or None for current
        """
        if chart_date:
            url = f"{self.archive_url}{chart_date}.html"
            logger.info(f"Scraping Apple Music chart for date: {chart_date}")
        else:
            url = f"{self.base_url}index.html"
            logger.info(f"Scraping current Apple Music chart")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the main table
            table = soup.find('table')
            if not table:
                logger.error("Could not find data table")
                return []
            
            data = []
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for idx, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                
                try:
                    # Extract position (column 0)
                    position = self.parse_number(cols[0].get_text(strip=True))
                    
                    # Extract artist and title from column 2 (column 1 is movement indicator)
                    if len(cols) < 3:
                        continue
                        
                    artist_title = cols[2].get_text(strip=True)
                    
                    # Split on " - " to separate artist from title
                    if ' - ' in artist_title:
                        parts = artist_title.split(' - ', 1)
                        artist_name = parts[0].strip()
                        song_name = parts[1].strip()
                    else:
                        # Fallback: try to extract from links
                        links = cols[2].find_all('a')
                        if len(links) >= 2:
                            artist_name = links[0].get_text(strip=True)
                            song_name = links[1].get_text(strip=True)
                        else:
                            artist_name = "Unknown"
                            song_name = artist_title
                    
                    # Extract streams/points
                    streams = 0
                    for col in cols[2:]:
                        text = col.get_text(strip=True)
                        num = self.parse_number(text)
                        if num > streams:
                            streams = num
                    
                    # Generate song_id
                    song_id = f"am_{artist_name}_{song_name}".replace(' ', '_').lower()[:100]
                    
                    data.append({
                        'song_id': song_id,
                        'song_name': song_name,
                        'artist_name': artist_name,
                        'streams': streams,
                        'position': position or idx
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing row {idx}: {e}")
                    continue
            
            logger.info(f"Scraped {len(data)} songs from Apple Music chart")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping Apple Music chart: {e}")
            return []
    
    def collect_daily_data(self):
        """Collect daily Apple Music streaming data"""
        logger.info("Starting Apple Music data collection")
        
        # Try current chart first
        apple_data = self.scrape_apple_music_chart()
        
        # If current fails, try yesterday's archive
        if not apple_data:
            logger.info("Current chart failed, trying archive")
            chart_date = self.get_latest_archive_date()
            apple_data = self.scrape_apple_music_chart(chart_date)
        
        if not apple_data:
            logger.error("Failed to collect Apple Music data")
            return False
        
        # Prepare data for database insertion
        # We'll store Apple Music data in a similar table structure
        # For now, we can reuse spotify_streams table or create a new one
        data_to_insert = []
        today = date.today()
        
        for song in apple_data[:200]:  # Top 200 songs
            data_to_insert.append((
                song['song_id'],
                song['song_name'],
                song['artist_name'],
                song['streams'],
                0,  # playlist_adds
                song['position'],
                today
            ))
        
        # Insert into database (using Spotify table structure for now)
        db = DatabaseManager()
        if db.connect():
            success = db.insert_spotify_data(data_to_insert)
            db.close()
            
            if success:
                logger.info(f"Successfully collected data for {len(data_to_insert)} songs")
                return True
        
        return False
    
    def collect_historical_data(self, start_date, end_date):
        """
        Collect historical Apple Music data for a date range
        start_date, end_date: datetime.date objects
        """
        logger.info(f"Collecting historical Apple Music data from {start_date} to {end_date}")
        
        current_date = start_date
        success_count = 0
        
        while current_date <= end_date:
            chart_date = current_date.strftime('%Y%m%d')
            apple_data = self.scrape_apple_music_chart(chart_date)
            
            if apple_data:
                data_to_insert = []
                for song in apple_data[:200]:
                    data_to_insert.append((
                        song['song_id'],
                        song['song_name'],
                        song['artist_name'],
                        song['streams'],
                        0,
                        song['position'],
                        current_date
                    ))
                
                db = DatabaseManager()
                if db.connect():
                    try:
                        query = """
                            INSERT INTO spotify_streams 
                            (song_id, song_name, artist_name, streams, playlist_adds, chart_position, collection_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (song_id, collection_date) DO UPDATE SET
                                streams = EXCLUDED.streams,
                                chart_position = EXCLUDED.chart_position
                        """
                        for data in data_to_insert:
                            db.cursor.execute(query, data)
                        db.conn.commit()
                        logger.info(f"Collected data for {chart_date}: {len(data_to_insert)} songs")
                        success_count += 1
                        db.close()
                    except Exception as e:
                        logger.error(f"Error inserting data for {chart_date}: {e}")
                        db.conn.rollback()
                        db.close()
            
            current_date += timedelta(days=1)
        
        logger.info(f"Historical collection complete: {success_count} days collected")
        return success_count > 0


def main():
    """Main execution function"""
    collector = AppleMusicCollector()
    collector.collect_daily_data()


if __name__ == "__main__":
    main()

