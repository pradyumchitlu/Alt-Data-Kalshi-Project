#!/usr/bin/env python3
"""
Historical data collection for building training dataset
Collects data from kworb.net archives (Sept 2024+)
"""
import logging
from datetime import date, timedelta
import time
from pathlib import Path
from file_storage import FileStorage

# Import collectors
from itunes import iTunesCollector
from apple_music import AppleMusicCollector
from billboard_scraper import BillboardScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def collect_itunes_historical(start_date, end_date):
    """Collect historical iTunes data"""
    logger.info(f"\n{'='*80}")
    logger.info(f"COLLECTING ITUNES HISTORICAL DATA")
    logger.info(f"From: {start_date} To: {end_date}")
    logger.info(f"{'='*80}\n")
    
    storage = FileStorage()
    collector = iTunesCollector()
    current_date = start_date
    success_count = 0
    
    while current_date <= end_date:
        chart_date = current_date.strftime('%Y%m%d')
        
        try:
            data = collector.scrape_itunes_chart(chart_date)
            
            if data:
                data_to_save = []
                for song in data[:200]:
                    data_to_save.append((
                        song['song_name'],
                        song['artist_name'],
                        song['digital_sales'],
                        0,  # physical_sales
                        song['digital_sales'],  # total_sales
                        current_date
                    ))
                
                storage.save_itunes_data(data_to_save, current_date)
                success_count += 1
                if success_count % 30 == 0:  # Log every 30 days
                    logger.info(f"✓ Progress: {success_count} days collected ({chart_date})")
                elif success_count % 7 == 0:  # Brief update every week
                    logger.info(f"  ... {chart_date}")
            else:
                logger.warning(f"✗ {chart_date}: No data")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"✗ {chart_date}: Error - {e}")
        
        current_date += timedelta(days=1)
    
    logger.info(f"\n✓ iTunes complete: {success_count} days collected")
    return success_count


def collect_apple_music_historical(start_date, end_date):
    """Collect historical Apple Music data"""
    logger.info(f"\n{'='*80}")
    logger.info(f"COLLECTING APPLE MUSIC HISTORICAL DATA")
    logger.info(f"From: {start_date} To: {end_date}")
    logger.info(f"{'='*80}\n")
    
    storage = FileStorage()
    collector = AppleMusicCollector()
    current_date = start_date
    success_count = 0
    
    while current_date <= end_date:
        chart_date = current_date.strftime('%Y%m%d')
        
        try:
            data = collector.scrape_apple_music_chart(chart_date)
            
            if data:
                data_to_save = []
                for song in data[:200]:
                    data_to_save.append((
                        song['song_id'],
                        song['song_name'],
                        song['artist_name'],
                        song['streams'],
                        0,  # playlist_adds
                        song['position'],
                        current_date
                    ))
                
                storage.save_apple_music_data(data_to_save, current_date)
                success_count += 1
                if success_count % 30 == 0:  # Log every 30 days
                    logger.info(f"✓ Progress: {success_count} days collected ({chart_date})")
                elif success_count % 7 == 0:  # Brief update every week
                    logger.info(f"  ... {chart_date}")
            else:
                logger.warning(f"✗ {chart_date}: No data")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"✗ {chart_date}: Error - {e}")
        
        current_date += timedelta(days=1)
    
    logger.info(f"\n✓ Apple Music complete: {success_count} days collected")
    return success_count


def collect_billboard_historical(start_date, end_date):
    """Collect historical Billboard Hot 100 (Saturdays only)"""
    logger.info(f"\n{'='*80}")
    logger.info(f"COLLECTING BILLBOARD HOT 100 HISTORICAL DATA")
    logger.info(f"From: {start_date} To: {end_date}")
    logger.info(f"{'='*80}\n")
    
    storage = FileStorage()
    collector = BillboardScraper()
    
    # Find first Saturday on or after start_date
    current_date = start_date
    while current_date.weekday() != 5:  # 5 = Saturday
        current_date += timedelta(days=1)
    
    success_count = 0
    
    while current_date <= end_date:
        try:
            data = collector.scrape_chart(current_date)
            
            if data:
                data_to_save = []
                for song in data:
                    data_to_save.append((
                        song['song_name'],
                        song['artist_name'],
                        song['position'],
                        song['weeks_on_chart'],
                        current_date
                    ))
                
                storage.save_billboard_data(data_to_save, current_date)
                success_count += 1
                logger.info(f"✓ {current_date}: Saved {len(data_to_save)} songs (Top {song['position']})")
            else:
                logger.warning(f"✗ {current_date}: No data")
            
            time.sleep(5)  # Longer delay for Billboard
            
        except Exception as e:
            logger.error(f"✗ {current_date}: Error - {e}")
        
        # Move to next Saturday
        current_date += timedelta(weeks=1)
    
    logger.info(f"\n✓ Billboard complete: {success_count} weeks collected")
    return success_count


def main():
    """Main execution"""
    Path('logs').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    
    logger.info("\n" + "=" * 80)
    logger.info("BILLBOARD HOT 100 PREDICTION - HISTORICAL DATA COLLECTION")
    logger.info("=" * 80)
    logger.info("\nThis collects historical data for building your training dataset")
    logger.info("You'll be able to calculate MAs, deltas, and momentum features\n")
    
    # Set date range (archives available from June 2017!)
    # kworb.net archives go back to 20170628.html
    start_date = date(2017, 6, 28)
    end_date = date.today() - timedelta(days=1)  # Yesterday
    
    logger.info(f"Date range: {start_date} to {end_date}")
    logger.info(f"Total days: {(end_date - start_date).days}\n")
    
    # Collect from all sources
    results = {}
    
    # 1. iTunes (has daily archives from June 2017!)
    logger.info("NOTE: iTunes archive goes back to June 28, 2017")
    logger.info("This will take a while - collecting ~2,700 days of data\n")
    
    # Ask user if they want to collect all or just recent
    logger.info("Options:")
    logger.info("  1. Collect ALL data (June 2017 - today) - RECOMMENDED for best model")
    logger.info("  2. Collect recent data only (last 6 months)")
    logger.info("\nDefaulting to last 6 months. Edit script to collect all.\n")
    
    # Default: last 6 months (faster for testing)
    # Change this to start_date to collect all data from 2017
    itunes_start = date.today() - timedelta(days=180)  # Last 6 months
    results['itunes'] = collect_itunes_historical(itunes_start, end_date)
    
    # 2. Apple Music (has daily archives from Oct 2024)
    apple_start = max(start_date, date(2024, 10, 1))
    results['apple_music'] = collect_apple_music_historical(apple_start, end_date)
    
    # 3. Billboard Hot 100 - DO NOT SCRAPE
    # User has Historical-100.csv with all historical data
    logger.info("\n" + "=" * 80)
    logger.info("BILLBOARD HOT 100 HISTORICAL DATA")
    logger.info("=" * 80)
    logger.info("\nNOTE: Billboard historical data should be loaded from:")
    logger.info("      Historical-100.csv")
    logger.info("\nThis CSV contains all Billboard Hot 100 winners up to 3 months ago.")
    logger.info("No scraping needed - use the CSV file directly!")
    results['billboard'] = 'Use Historical-100.csv'
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("HISTORICAL COLLECTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\niTunes: {results['itunes']} days")
    logger.info(f"Apple Music: {results['apple_music']} days")
    logger.info(f"Billboard Hot 100: {results['billboard']}")
    logger.info(f"\nData saved to: data/ directory")
    logger.info("\nIMPORTANT: Load Billboard data from Historical-100.csv")
    logger.info("\n" + "=" * 80)
    logger.info("NEXT STEPS")
    logger.info("=" * 80)
    logger.info("\n1. Load the data in Python:")
    logger.info("   import pandas as pd")
    logger.info("   from pathlib import Path")
    logger.info("")
    logger.info("   # Load all iTunes data")
    logger.info("   itunes_files = Path('data/itunes').glob('*.csv')")
    logger.info("   itunes_df = pd.concat([pd.read_csv(f) for f in itunes_files])")
    logger.info("")
    logger.info("   # Load Billboard (ground truth)")
    logger.info("   billboard_files = Path('data/billboard').glob('*.csv')")
    logger.info("   billboard_df = pd.concat([pd.read_csv(f) for f in billboard_files])")
    logger.info("")
    logger.info("2. Calculate features:")
    logger.info("   # 7-day moving average")
    logger.info("   itunes_df['sales_7day_ma'] = itunes_df.groupby('song_id')['digital_sales'].rolling(7).mean()")
    logger.info("")
    logger.info("   # Week-over-week delta")
    logger.info("   itunes_df['sales_delta'] = itunes_df.groupby('song_id')['digital_sales'].diff()")
    logger.info("")
    logger.info("   # Growth rate")
    logger.info("   itunes_df['sales_growth'] = itunes_df.groupby('song_id')['digital_sales'].pct_change()")
    logger.info("")
    logger.info("3. Create target variable:")
    logger.info("   billboard_df['reached_number_1'] = (billboard_df['chart_position'] == 1).astype(int)")
    logger.info("")
    logger.info("4. Train your model!")
    logger.info("   from xgboost import XGBClassifier")
    logger.info("   model = XGBClassifier()")
    logger.info("   model.fit(X_train, y_train)")
    logger.info("")
    logger.info("5. Make predictions and trade on Kalshi!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

