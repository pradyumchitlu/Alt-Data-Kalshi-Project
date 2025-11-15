"""
YouTube data collection from kworb.net
Scrapes video views and statistics from kworb.net YouTube charts
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, date
import re
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeCollector:
    """Collects data from kworb.net YouTube charts"""
    
    def __init__(self):
        self.base_url = "https://kworb.net/youtube/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def parse_number(self, text):
        """Parse number from text (handles commas, K, M, B suffixes)"""
        if not text:
            return 0
        
        text = text.strip().upper()
        
        # Remove commas
        text = text.replace(',', '')
        
        # Handle K, M, B suffixes
        multiplier = 1
        if 'B' in text:
            multiplier = 1000000000
            text = text.replace('B', '')
        elif 'M' in text:
            multiplier = 1000000
            text = text.replace('M', '')
        elif 'K' in text:
            multiplier = 1000
            text = text.replace('K', '')
        
        try:
            return int(float(text) * multiplier)
        except ValueError:
            return 0
    
    def scrape_youtube_chart(self):
        """Scrape main YouTube music chart from kworb.net"""
        logger.info(f"Scraping YouTube chart: {self.base_url}")
        
        try:
            response = requests.get(self.base_url, headers=self.headers)
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
                if len(cols) < 4:
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
                    
                    # Extract video ID if available (from link in column 2)
                    video_id = ""
                    link = cols[2].find('a')
                    if link and 'href' in link.attrs:
                        href = link['href']
                        if '/video/' in href:
                            video_id = href.split('/video/')[-1].replace('.html', '')
                    
                    if not video_id:
                        video_id = f"yt_{artist_name}_{song_name}".replace(' ', '_').lower()[:100]
                    
                    # Extract views (usually the largest number in the row)
                    views = 0
                    likes = 0
                    comments = 0
                    
                    for col_idx, col in enumerate(cols[2:], 2):
                        text = col.get_text(strip=True)
                        num = self.parse_number(text)
                        if num > views:
                            views = num
                    
                    data.append({
                        'video_id': video_id,
                        'song_name': song_name,
                        'artist_name': artist_name,
                        'views': views,
                        'likes': likes,
                        'comments': comments,
                        'position': position or idx
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing row {idx}: {e}")
                    continue
            
            logger.info(f"Scraped {len(data)} videos from YouTube chart")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping YouTube chart: {e}")
            return []
    
    def collect_daily_data(self):
        """Collect daily YouTube data"""
        logger.info("Starting YouTube data collection")
        
        # Scrape YouTube chart
        youtube_data = self.scrape_youtube_chart()
        
        if not youtube_data:
            logger.error("Failed to collect YouTube data")
            return False
        
        # Prepare data for database insertion
        data_to_insert = []
        today = date.today()
        
        for video in youtube_data[:200]:  # Top 200 videos
            data_to_insert.append((
                video['video_id'],
                video['song_name'],
                video['artist_name'],
                video['views'],
                video['likes'],
                video['comments'],
                video['position'],
                today
            ))
        
        # Insert into database
        db = DatabaseManager()
        if db.connect():
            success = db.insert_youtube_data(data_to_insert)
            db.close()
            
            if success:
                logger.info(f"Successfully collected data for {len(data_to_insert)} videos")
                return True
        
        return False


def main():
    """Main execution function"""
    collector = YouTubeCollector()
    collector.collect_daily_data()


if __name__ == "__main__":
    main()
