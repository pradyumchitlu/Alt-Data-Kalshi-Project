"""
Database setup and connection management for Billboard Hot 100 data collection
"""
import psycopg2
from psycopg2.extras import execute_values
import logging
from datetime import datetime
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def create_tables(self):
        """Create all necessary tables for data storage"""
        
        tables = [
            # Spotify streaming data
            """
            CREATE TABLE IF NOT EXISTS spotify_streams (
                id SERIAL PRIMARY KEY,
                song_id VARCHAR(100),
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                streams BIGINT,
                playlist_adds INTEGER,
                chart_position INTEGER,
                collection_date DATE,
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_id, collection_date)
            )
            """,
            
            # YouTube data
            """
            CREATE TABLE IF NOT EXISTS youtube_data (
                id SERIAL PRIMARY KEY,
                video_id VARCHAR(100),
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                views BIGINT,
                likes INTEGER,
                comments INTEGER,
                chart_position INTEGER,
                collection_date DATE,
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(video_id, collection_date)
            )
            """,
            
            # TikTok viral data
            """
            CREATE TABLE IF NOT EXISTS tiktok_data (
                id SERIAL PRIMARY KEY,
                song_id VARCHAR(100),
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                video_count INTEGER,
                views BIGINT,
                trending_rank INTEGER,
                collection_date DATE,
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_id, collection_date)
            )
            """,
            
            # Google Trends data
            """
            CREATE TABLE IF NOT EXISTS google_trends (
                id SERIAL PRIMARY KEY,
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                search_interest INTEGER,
                trend_direction VARCHAR(20),
                collection_date DATE,
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_name, artist_name, collection_date)
            )
            """,
            
            # Shazam data
            """
            CREATE TABLE IF NOT EXISTS shazam_data (
                id SERIAL PRIMARY KEY,
                song_id VARCHAR(100),
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                shazams INTEGER,
                chart_position INTEGER,
                collection_date DATE,
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_id, collection_date)
            )
            """,
            
            # Radio airplay data
            """
            CREATE TABLE IF NOT EXISTS radio_airplay (
                id SERIAL PRIMARY KEY,
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                spins INTEGER,
                audience_impressions BIGINT,
                radio_format VARCHAR(100),
                collection_date DATE,
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_name, artist_name, radio_format, collection_date)
            )
            """,
            
            # Sales data
            """
            CREATE TABLE IF NOT EXISTS sales_data (
                id SERIAL PRIMARY KEY,
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                digital_sales INTEGER,
                physical_sales INTEGER,
                total_sales INTEGER,
                collection_date DATE,
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_name, artist_name, collection_date)
            )
            """,
            
            # Kalshi market data
            """
            CREATE TABLE IF NOT EXISTS kalshi_market (
                id SERIAL PRIMARY KEY,
                contract_id VARCHAR(100),
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                yes_price DECIMAL(10, 4),
                no_price DECIMAL(10, 4),
                volume INTEGER,
                open_interest INTEGER,
                implied_probability DECIMAL(5, 4),
                collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contract_id, collection_timestamp)
            )
            """,
            
            # Billboard Hot 100 historical data
            """
            CREATE TABLE IF NOT EXISTS billboard_hot100 (
                id SERIAL PRIMARY KEY,
                song_name VARCHAR(500),
                artist_name VARCHAR(500),
                chart_position INTEGER,
                week_on_chart INTEGER,
                chart_date DATE,
                UNIQUE(song_name, artist_name, chart_date)
            )
            """
        ]
        
        try:
            for table_sql in tables:
                self.cursor.execute(table_sql)
            self.conn.commit()
            logger.info("All tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.conn.rollback()
            return False
    
    def insert_spotify_data(self, data_list):
        """Insert Spotify streaming data"""
        query = """
            INSERT INTO spotify_streams 
            (song_id, song_name, artist_name, streams, playlist_adds, chart_position, collection_date)
            VALUES %s
            ON CONFLICT (song_id, collection_date) DO UPDATE SET
                streams = EXCLUDED.streams,
                playlist_adds = EXCLUDED.playlist_adds,
                chart_position = EXCLUDED.chart_position
        """
        try:
            execute_values(self.cursor, query, data_list)
            self.conn.commit()
            logger.info(f"Inserted {len(data_list)} Spotify records")
            return True
        except Exception as e:
            logger.error(f"Error inserting Spotify data: {e}")
            self.conn.rollback()
            return False
    
    def insert_youtube_data(self, data_list):
        """Insert YouTube data"""
        query = """
            INSERT INTO youtube_data 
            (video_id, song_name, artist_name, views, likes, comments, chart_position, collection_date)
            VALUES %s
            ON CONFLICT (video_id, collection_date) DO UPDATE SET
                views = EXCLUDED.views,
                likes = EXCLUDED.likes,
                comments = EXCLUDED.comments,
                chart_position = EXCLUDED.chart_position
        """
        try:
            execute_values(self.cursor, query, data_list)
            self.conn.commit()
            logger.info(f"Inserted {len(data_list)} YouTube records")
            return True
        except Exception as e:
            logger.error(f"Error inserting YouTube data: {e}")
            self.conn.rollback()
            return False
    
    def insert_kalshi_data(self, data_list):
        """Insert Kalshi market data"""
        query = """
            INSERT INTO kalshi_market 
            (contract_id, song_name, artist_name, yes_price, no_price, volume, 
             open_interest, implied_probability, collection_timestamp)
            VALUES %s
        """
        try:
            execute_values(self.cursor, query, data_list)
            self.conn.commit()
            logger.info(f"Inserted {len(data_list)} Kalshi market records")
            return True
        except Exception as e:
            logger.error(f"Error inserting Kalshi data: {e}")
            self.conn.rollback()
            return False


def initialize_database():
    """Initialize database with all required tables"""
    db = DatabaseManager()
    if db.connect():
        db.create_tables()
        db.close()
        logger.info("Database initialization complete")
    else:
        logger.error("Failed to initialize database")


if __name__ == "__main__":
    initialize_database()

