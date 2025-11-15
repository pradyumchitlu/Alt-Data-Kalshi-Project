"""
Billboard Hot 100 historical data collection
Scrapes actual Billboard Hot 100 chart data for model training
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, date, timedelta
import re
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BillboardScraper:
    """Scrapes Billboard Hot 100 chart data"""
    
    def __init__(self):
        self.base_url = "https://www.billboard.com/charts/hot-100"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_chart(self, chart_date=None):
        """
        Scrape Billboard Hot 100 for a specific date
        chart_date: date object or None for current chart
        """
        if chart_date:
            url = f"{self.base_url}/{chart_date.strftime('%Y-%m-%d')}"
            logger.info(f"Scraping Billboard Hot 100 for {chart_date}")
        else:
            url = self.base_url
            logger.info("Scraping current Billboard Hot 100")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Billboard's HTML structure - this may need adjustment based on actual structure
            # Looking for chart entries
            chart_items = soup.find_all('div', class_=re.compile('chart-element'))
            
            if not chart_items:
                # Try alternative selectors
                chart_items = soup.find_all('li', class_=re.compile('chart-list__element'))
            
            if not chart_items:
                logger.error("Could not find chart items on page")
                return []
            
            data = []
            
            for item in chart_items[:100]:  # Hot 100 has 100 songs
                try:
                    # Extract position
                    position_elem = item.find(class_=re.compile('chart-element__rank'))
                    if not position_elem:
                        position_elem = item.find('span', class_='chart-element__rank__number')
                    position = int(position_elem.get_text(strip=True)) if position_elem else 0
                    
                    # Extract song title
                    title_elem = item.find(class_=re.compile('chart-element__information__song'))
                    if not title_elem:
                        title_elem = item.find('span', class_='chart-element__information__song text--truncate')
                    song_name = title_elem.get_text(strip=True) if title_elem else "Unknown"
                    
                    # Extract artist
                    artist_elem = item.find(class_=re.compile('chart-element__information__artist'))
                    if not artist_elem:
                        artist_elem = item.find('span', class_='chart-element__information__artist text--truncate')
                    artist_name = artist_elem.get_text(strip=True) if artist_elem else "Unknown"
                    
                    # Extract weeks on chart
                    weeks_elem = item.find('span', class_='chart-element__information__delta__text text--last')
                    weeks_on_chart = 1
                    if weeks_elem:
                        weeks_text = weeks_elem.get_text(strip=True)
                        weeks_match = re.search(r'(\d+)', weeks_text)
                        if weeks_match:
                            weeks_on_chart = int(weeks_match.group(1))
                    
                    data.append({
                        'song_name': song_name,
                        'artist_name': artist_name,
                        'position': position,
                        'weeks_on_chart': weeks_on_chart
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing chart item: {e}")
                    continue
            
            logger.info(f"Scraped {len(data)} songs from Billboard Hot 100")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping Billboard chart: {e}")
            return []
    
    def collect_chart_data(self, chart_date=None):
        """Collect and store Billboard Hot 100 chart data"""
        if not chart_date:
            chart_date = date.today()
        
        logger.info(f"Collecting Billboard Hot 100 data for {chart_date}")
        
        chart_data = self.scrape_chart(chart_date)
        
        if not chart_data:
            logger.error("Failed to collect Billboard data")
            return False
        
        # Prepare data for database insertion
        data_to_insert = []
        
        for song in chart_data:
            data_to_insert.append((
                song['song_name'],
                song['artist_name'],
                song['position'],
                song['weeks_on_chart'],
                chart_date
            ))
        
        # Insert into database
        db = DatabaseManager()
        if db.connect():
            try:
                query = """
                    INSERT INTO billboard_hot100 
                    (song_name, artist_name, chart_position, week_on_chart, chart_date)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (song_name, artist_name, chart_date) DO UPDATE SET
                        chart_position = EXCLUDED.chart_position,
                        week_on_chart = EXCLUDED.week_on_chart
                """
                for data in data_to_insert:
                    db.cursor.execute(query, data)
                db.conn.commit()
                logger.info(f"Successfully stored {len(data_to_insert)} songs")
                db.close()
                return True
            except Exception as e:
                logger.error(f"Error inserting Billboard data: {e}")
                db.conn.rollback()
                db.close()
        
        return False
    
    def collect_historical_data(self, start_date, end_date):
        """
        Collect historical Billboard Hot 100 data
        Billboard updates weekly on Saturdays
        """
        logger.info(f"Collecting historical Billboard data from {start_date} to {end_date}")
        
        # Billboard Hot 100 is updated weekly on Saturdays
        # Find the first Saturday on or after start_date
        current_date = start_date
        while current_date.weekday() != 5:  # 5 = Saturday
            current_date += timedelta(days=1)
        
        success_count = 0
        
        while current_date <= end_date:
            try:
                if self.collect_chart_data(current_date):
                    success_count += 1
                    logger.info(f"✓ Collected chart for {current_date}")
                else:
                    logger.warning(f"✗ Failed to collect chart for {current_date}")
                
                # Move to next Saturday
                current_date += timedelta(weeks=1)
                
                # Rate limiting - be respectful to Billboard's servers
                import time
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error collecting chart for {current_date}: {e}")
                current_date += timedelta(weeks=1)
                continue
        
        logger.info(f"Historical collection complete: {success_count} weeks collected")
        return success_count > 0


def main():
    """Main execution function"""
    scraper = BillboardScraper()
    
    # Collect current week's chart
    scraper.collect_chart_data()
    
    # Optional: Collect historical data
    # Uncomment to collect past charts
    # start_date = date(2024, 1, 1)
    # end_date = date.today()
    # scraper.collect_historical_data(start_date, end_date)


if __name__ == "__main__":
    main()

