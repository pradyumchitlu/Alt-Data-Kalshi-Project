"""
iTunes data collection from kworb.net
Scrapes iTunes worldwide sales data from kworb.net
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, date, timedelta
import re
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class iTunesCollector:
    """Collects sales data from kworb.net iTunes charts"""
    
    def __init__(self):
        self.base_url = "https://kworb.net/ww/"
        self.archive_url = "https://kworb.net/ww/archive/"
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
        # Use yesterday's date as kworb updates with a delay
        yesterday = date.today() - timedelta(days=1)
        return yesterday.strftime('%Y%m%d')
    
    def scrape_itunes_chart(self, chart_date=None):
        """
        Scrape iTunes chart from kworb.net
        chart_date: string in format YYYYMMDD or None for current
        """
        if chart_date:
            url = f"{self.archive_url}{chart_date}.html"
            logger.info(f"Scraping iTunes chart for date: {chart_date}")
        else:
            url = f"{self.base_url}index.html"
            logger.info(f"Scraping current iTunes chart")
        
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
                    
                    # Extract sales data
                    # iTunes tracks digital sales, usually shown in points or sales
                    digital_sales = 0
                    for col in cols[2:]:
                        text = col.get_text(strip=True)
                        num = self.parse_number(text)
                        if num > 0:
                            digital_sales = num
                            break
                    
                    data.append({
                        'song_name': song_name,
                        'artist_name': artist_name,
                        'digital_sales': digital_sales,
                        'position': position or idx
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing row {idx}: {e}")
                    continue
            
            logger.info(f"Scraped {len(data)} songs from iTunes chart")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping iTunes chart: {e}")
            return []
    
    def collect_daily_data(self):
        """Collect daily iTunes sales data"""
        logger.info("Starting iTunes data collection")
        
        # Try current chart first
        itunes_data = self.scrape_itunes_chart()
        
        # If current fails, try yesterday's archive
        if not itunes_data:
            logger.info("Current chart failed, trying archive")
            chart_date = self.get_latest_archive_date()
            itunes_data = self.scrape_itunes_chart(chart_date)
        
        if not itunes_data:
            logger.error("Failed to collect iTunes data")
            return False
        
        # Prepare data for database insertion
        data_to_insert = []
        today = date.today()
        
        for song in itunes_data[:200]:  # Top 200 songs
            data_to_insert.append((
                song['song_name'],
                song['artist_name'],
                song['digital_sales'],
                0,  # physical_sales (iTunes is digital only)
                song['digital_sales'],  # total_sales
                today
            ))
        
        # Insert into database
        db = DatabaseManager()
        if db.connect():
            try:
                query = """
                    INSERT INTO sales_data 
                    (song_name, artist_name, digital_sales, physical_sales, total_sales, collection_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (song_name, artist_name, collection_date) DO UPDATE SET
                        digital_sales = EXCLUDED.digital_sales,
                        total_sales = EXCLUDED.total_sales
                """
                for data in data_to_insert:
                    db.cursor.execute(query, data)
                db.conn.commit()
                logger.info(f"Successfully collected data for {len(data_to_insert)} songs")
                db.close()
                return True
            except Exception as e:
                logger.error(f"Error inserting iTunes data: {e}")
                db.conn.rollback()
                db.close()
        
        return False
    
    def collect_historical_data(self, start_date, end_date):
        """
        Collect historical iTunes data for a date range
        start_date, end_date: datetime.date objects
        """
        logger.info(f"Collecting historical iTunes data from {start_date} to {end_date}")
        
        current_date = start_date
        success_count = 0
        
        while current_date <= end_date:
            chart_date = current_date.strftime('%Y%m%d')
            itunes_data = self.scrape_itunes_chart(chart_date)
            
            if itunes_data:
                # Insert data with the historical date
                data_to_insert = []
                for song in itunes_data[:200]:
                    data_to_insert.append((
                        song['song_name'],
                        song['artist_name'],
                        song['digital_sales'],
                        0,
                        song['digital_sales'],
                        current_date
                    ))
                
                db = DatabaseManager()
                if db.connect():
                    try:
                        query = """
                            INSERT INTO sales_data 
                            (song_name, artist_name, digital_sales, physical_sales, total_sales, collection_date)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (song_name, artist_name, collection_date) DO UPDATE SET
                                digital_sales = EXCLUDED.digital_sales,
                                total_sales = EXCLUDED.total_sales
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
            
            # Move to next day
            current_date += timedelta(days=1)
        
        logger.info(f"Historical collection complete: {success_count} days collected")
        return success_count > 0


def main():
    """Main execution function"""
    collector = iTunesCollector()
    collector.collect_daily_data()


if __name__ == "__main__":
    main()

