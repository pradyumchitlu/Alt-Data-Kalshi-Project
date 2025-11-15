"""
Spotify data collection from kworb.net
Scrapes daily and weekly streaming numbers from kworb.net Spotify charts
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, date
import re
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpotifyCollector:
    """Collects streaming data from kworb.net Spotify charts"""
    
    def __init__(self):
        self.daily_url = "https://kworb.net/spotify/country/global_daily.html"
        self.weekly_url = "https://kworb.net/spotify/country/global_weekly.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def parse_number(self, text):
        """Parse number from text (handles commas and + signs)"""
        if not text:
            return 0
        # Remove commas and + signs
        cleaned = re.sub(r'[,+\s]', '', text)
        try:
            return int(cleaned)
        except ValueError:
            return 0
    
    def scrape_daily_chart(self):
        """Scrape daily Spotify chart from kworb.net"""
        logger.info(f"Scraping Spotify daily chart: {self.daily_url}")
        
        try:
            response = requests.get(self.daily_url, headers=self.headers)
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
                if len(cols) < 6:
                    continue
                
                try:
                    # Extract position (column 0)
                    position = self.parse_number(cols[0].get_text(strip=True))
                    
                    # Extract artist and title from column 2 (column 1 is movement indicator like "=" or "+2")
                    # Format on kworb.net: "Artist - Title" with both being links
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
                    
                    # Extract streams from the streams column (usually column 5 or 6)
                    # Find the column with the largest number - that's likely streams
                    streams = 0
                    for col in cols[3:]:  # Start from column 3 onwards
                        text = col.get_text(strip=True)
                        num = self.parse_number(text)
                        # Streams are typically in millions/billions
                        if num > 100000:  # Filter out small numbers like weeks/position
                            if num > streams:
                                streams = num
                    
                    # Generate a simple song_id
                    song_id = f"{artist_name}_{song_name}".replace(' ', '_').lower()[:100]
                    
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
            
            logger.info(f"Scraped {len(data)} songs from daily chart")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping daily chart: {e}")
            return []
    
    def scrape_weekly_chart(self):
        """Scrape weekly Spotify chart from kworb.net"""
        logger.info(f"Scraping Spotify weekly chart: {self.weekly_url}")
        
        try:
            response = requests.get(self.weekly_url, headers=self.headers)
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
                if len(cols) < 6:
                    continue
                
                try:
                    # Extract position
                    position = self.parse_number(cols[0].get_text(strip=True))
                    
                    # Extract artist and title
                    artist_title = cols[1].get_text(strip=True)
                    if ' - ' in artist_title:
                        parts = artist_title.split(' - ', 1)
                        artist_name = parts[0].strip()
                        song_name = parts[1].strip()
                    else:
                        artist_name = "Unknown"
                        song_name = artist_title
                    
                    # Extract streams
                    streams = 0
                    for col in cols[2:]:
                        text = col.get_text(strip=True)
                        num = self.parse_number(text)
                        if num > streams:
                            streams = num
                    
                    # Extract weeks on chart (usually labeled "Wks")
                    weeks_on_chart = 0
                    for col in cols[2:5]:
                        text = col.get_text(strip=True)
                        if text.isdigit():
                            weeks_on_chart = int(text)
                            break
                    
                    song_id = f"{artist_name}_{song_name}".replace(' ', '_').lower()[:100]
                    
                    data.append({
                        'song_id': song_id,
                        'song_name': song_name,
                        'artist_name': artist_name,
                        'streams': streams,
                        'position': position or idx,
                        'weeks_on_chart': weeks_on_chart
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing row {idx}: {e}")
                    continue
            
            logger.info(f"Scraped {len(data)} songs from weekly chart")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping weekly chart: {e}")
            return []
    
    def collect_daily_data(self):
        """Collect daily Spotify data"""
        logger.info("Starting Spotify data collection")
        
        # Scrape daily chart
        daily_data = self.scrape_daily_chart()
        
        if not daily_data:
            logger.warning("No daily data collected, trying weekly chart")
            daily_data = self.scrape_weekly_chart()
        
        if not daily_data:
            logger.error("Failed to collect any Spotify data")
            return False
        
        # Prepare data for database insertion
        data_to_insert = []
        today = date.today()
        
        for song in daily_data[:200]:  # Top 200 songs
            data_to_insert.append((
                song['song_id'],
                song['song_name'],
                song['artist_name'],
                song['streams'],
                0,  # playlist_adds (not available from kworb)
                song['position'],
                today
            ))
        
        # Insert into database
        db = DatabaseManager()
        if db.connect():
            success = db.insert_spotify_data(data_to_insert)
            db.close()
            
            if success:
                logger.info(f"Successfully collected data for {len(data_to_insert)} tracks")
                return True
        
        return False


def main():
    """Main execution function"""
    collector = SpotifyCollector()
    collector.collect_daily_data()


if __name__ == "__main__":
    main()
