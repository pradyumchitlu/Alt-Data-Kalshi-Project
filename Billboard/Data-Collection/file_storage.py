"""
File-based storage alternative to PostgreSQL
Saves data to CSV/JSON files for when database is not available
"""
import json
import csv
import os
import logging
from datetime import datetime, date
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileStorage:
    """Saves collected data to CSV files"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for each data type
        self.subdirs = {
            'spotify': self.data_dir / 'spotify',
            'youtube': self.data_dir / 'youtube',
            'itunes': self.data_dir / 'itunes',
            'apple_music': self.data_dir / 'apple_music',
            'tiktok': self.data_dir / 'tiktok',
            'trends': self.data_dir / 'trends',
            'kalshi': self.data_dir / 'kalshi',
            'billboard': self.data_dir / 'billboard'
        }
        
        for subdir in self.subdirs.values():
            subdir.mkdir(exist_ok=True)
    
    def save_spotify_data(self, data_list, collection_date=None):
        """Save Spotify data to CSV"""
        if not collection_date:
            collection_date = date.today()
        
        filename = self.subdirs['spotify'] / f"spotify_{collection_date.strftime('%Y%m%d')}.csv"
        
        fieldnames = ['song_id', 'song_name', 'artist_name', 'streams', 'playlist_adds', 'chart_position', 'collection_date']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data_list:
                writer.writerow({
                    'song_id': row[0],
                    'song_name': row[1],
                    'artist_name': row[2],
                    'streams': row[3],
                    'playlist_adds': row[4],
                    'chart_position': row[5],
                    'collection_date': row[6]
                })
        
        logger.info(f"Saved {len(data_list)} Spotify records to {filename}")
        return True
    
    def save_youtube_data(self, data_list, collection_date=None):
        """Save YouTube data to CSV"""
        if not collection_date:
            collection_date = date.today()
        
        filename = self.subdirs['youtube'] / f"youtube_{collection_date.strftime('%Y%m%d')}.csv"
        
        fieldnames = ['video_id', 'song_name', 'artist_name', 'views', 'likes', 'comments', 'chart_position', 'collection_date']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data_list:
                writer.writerow({
                    'video_id': row[0],
                    'song_name': row[1],
                    'artist_name': row[2],
                    'views': row[3],
                    'likes': row[4],
                    'comments': row[5],
                    'chart_position': row[6],
                    'collection_date': row[7]
                })
        
        logger.info(f"Saved {len(data_list)} YouTube records to {filename}")
        return True
    
    def save_itunes_data(self, data_list, collection_date=None):
        """Save iTunes data to CSV"""
        if not collection_date:
            collection_date = date.today()
        
        filename = self.subdirs['itunes'] / f"itunes_{collection_date.strftime('%Y%m%d')}.csv"
        
        fieldnames = ['song_name', 'artist_name', 'digital_sales', 'physical_sales', 'total_sales', 'collection_date']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data_list:
                writer.writerow({
                    'song_name': row[0],
                    'artist_name': row[1],
                    'digital_sales': row[2],
                    'physical_sales': row[3],
                    'total_sales': row[4],
                    'collection_date': row[5]
                })
        
        logger.info(f"Saved {len(data_list)} iTunes records to {filename}")
        return True
    
    def save_apple_music_data(self, data_list, collection_date=None):
        """Save Apple Music data to CSV"""
        if not collection_date:
            collection_date = date.today()
        
        filename = self.subdirs['apple_music'] / f"apple_music_{collection_date.strftime('%Y%m%d')}.csv"
        
        fieldnames = ['song_id', 'song_name', 'artist_name', 'streams', 'playlist_adds', 'chart_position', 'collection_date']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data_list:
                writer.writerow({
                    'song_id': row[0],
                    'song_name': row[1],
                    'artist_name': row[2],
                    'streams': row[3],
                    'playlist_adds': row[4],
                    'chart_position': row[5],
                    'collection_date': row[6]
                })
        
        logger.info(f"Saved {len(data_list)} Apple Music records to {filename}")
        return True
    
    def save_billboard_data(self, data_list, collection_date=None):
        """Save Billboard Hot 100 data to CSV"""
        if not collection_date:
            collection_date = date.today()
        
        filename = self.subdirs['billboard'] / f"billboard_{collection_date.strftime('%Y%m%d')}.csv"
        
        fieldnames = ['song_name', 'artist_name', 'chart_position', 'weeks_on_chart', 'chart_date']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data_list:
                writer.writerow({
                    'song_name': row[0],
                    'artist_name': row[1],
                    'chart_position': row[2],
                    'weeks_on_chart': row[3],
                    'chart_date': row[4]
                })
        
        logger.info(f"Saved {len(data_list)} Billboard records to {filename}")
        return True

