#!/usr/bin/env python3
"""
Simple data collection runner - Works WITHOUT PostgreSQL!
Saves all data to CSV files instead of database
"""
from datetime import date
import logging
from pathlib import Path
from file_storage import FileStorage

# Import collectors
from spotify import SpotifyCollector
from youtube import YouTubeCollector
from itunes import iTunesCollector
from apple_music import AppleMusicCollector
from billboard_scraper import BillboardScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def collect_all_today():
    """Collect today's data from all sources"""
    
    # Create logs and data dirs
    Path('logs').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("STARTING DATA COLLECTION (FILE STORAGE MODE)")
    logger.info("=" * 80)
    logger.info("No database required - saving to CSV files!")
    logger.info("=" * 80)
    
    storage = FileStorage()
    today = date.today()
    results = {}
    
    # 1. Spotify
    logger.info("\n[1/5] Collecting Spotify data...")
    try:
        collector = SpotifyCollector()
        data = collector.scrape_daily_chart()
        if data:
            data_to_save = []
            for song in data[:200]:
                data_to_save.append((
                    song['song_id'], song['song_name'], song['artist_name'],
                    song['streams'], 0, song['position'], today
                ))
            results['spotify'] = storage.save_spotify_data(data_to_save)
        else:
            results['spotify'] = False
    except Exception as e:
        logger.error(f"Spotify failed: {e}")
        results['spotify'] = False
    
    # 2. YouTube
    logger.info("\n[2/5] Collecting YouTube data...")
    try:
        collector = YouTubeCollector()
        data = collector.scrape_youtube_chart()
        if data:
            data_to_save = []
            for video in data[:200]:
                data_to_save.append((
                    video['video_id'], video['song_name'], video['artist_name'],
                    video['views'], video['likes'], video['comments'], video['position'], today
                ))
            results['youtube'] = storage.save_youtube_data(data_to_save)
        else:
            results['youtube'] = False
    except Exception as e:
        logger.error(f"YouTube failed: {e}")
        results['youtube'] = False
    
    # 3. iTunes
    logger.info("\n[3/5] Collecting iTunes data...")
    try:
        collector = iTunesCollector()
        data = collector.scrape_itunes_chart()
        if data:
            data_to_save = []
            for song in data[:200]:
                data_to_save.append((
                    song['song_name'], song['artist_name'],
                    song['digital_sales'], 0, song['digital_sales'], today
                ))
            results['itunes'] = storage.save_itunes_data(data_to_save)
        else:
            results['itunes'] = False
    except Exception as e:
        logger.error(f"iTunes failed: {e}")
        results['itunes'] = False
    
    # 4. Apple Music
    logger.info("\n[4/5] Collecting Apple Music data...")
    try:
        collector = AppleMusicCollector()
        data = collector.scrape_apple_music_chart()
        if data:
            data_to_save = []
            for song in data[:200]:
                data_to_save.append((
                    song['song_id'], song['song_name'], song['artist_name'],
                    song['streams'], 0, song['position'], today
                ))
            results['apple_music'] = storage.save_apple_music_data(data_to_save)
        else:
            results['apple_music'] = False
    except Exception as e:
        logger.error(f"Apple Music failed: {e}")
        results['apple_music'] = False
    
    # 5. Billboard (if it's Saturday)
    logger.info("\n[5/5] Collecting Billboard data...")
    try:
        if today.weekday() == 5:  # Saturday
            collector = BillboardScraper()
            data = collector.scrape_chart(today)
            if data:
                data_to_save = []
                for song in data:
                    data_to_save.append((
                        song['song_name'], song['artist_name'],
                        song['position'], song['weeks_on_chart'], today
                    ))
                results['billboard'] = storage.save_billboard_data(data_to_save)
            else:
                results['billboard'] = False
        else:
            logger.info("Skipping Billboard (only collected on Saturdays)")
            results['billboard'] = None
    except Exception as e:
        logger.error(f"Billboard failed: {e}")
        results['billboard'] = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("COLLECTION SUMMARY")
    logger.info("=" * 80)
    
    for source, result in results.items():
        if result is None:
            status = "SKIPPED"
        elif result:
            status = "✓ SUCCESS"
        else:
            status = "✗ FAILED"
        logger.info(f"{source.upper()}: {status}")
    
    successful = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    logger.info(f"\nTotal: {successful}/{total} sources collected successfully")
    logger.info(f"Data saved to: data/ directory")
    logger.info("=" * 80)


if __name__ == "__main__":
    collect_all_today()

