#!/usr/bin/env python3
"""
Test script to verify all scrapers are working
Run this to check that data collection is functioning
"""
from spotify import SpotifyCollector
from youtube import YouTubeCollector
from itunes import iTunesCollector
from apple_music import AppleMusicCollector
from billboard_scraper import BillboardScraper
from datetime import date, timedelta

print("=" * 80)
print("TESTING ALL SCRAPERS")
print("=" * 80)
print()

# Test Spotify
print("[1/5] Testing Spotify scraper...")
try:
    spotify = SpotifyCollector()
    data = spotify.scrape_daily_chart()
    if data:
        print(f"✓ SUCCESS: Scraped {len(data)} songs from Spotify")
        print("\n  First 5 songs:")
        for i, song in enumerate(data[:5], 1):
            print(f"  {i}. {song['song_name']} by {song['artist_name']}")
            print(f"     Streams: {song['streams']:,} | Position: {song['position']}")
    else:
        print("✗ FAILED: No data returned")
except Exception as e:
    print(f"✗ ERROR: {e}")

print()

# Test YouTube
print("[2/5] Testing YouTube scraper...")
try:
    youtube = YouTubeCollector()
    data = youtube.scrape_youtube_chart()
    if data:
        print(f"✓ SUCCESS: Scraped {len(data)} videos from YouTube")
        print("\n  First 5 videos:")
        for i, video in enumerate(data[:5], 1):
            print(f"  {i}. {video['song_name']} by {video['artist_name']}")
            print(f"     Views: {video['views']:,} | Position: {video['position']}")
    else:
        print("✗ FAILED: No data returned")
except Exception as e:
    print(f"✗ ERROR: {e}")

print()

# Test iTunes
print("[3/5] Testing iTunes scraper...")
try:
    itunes = iTunesCollector()
    data = itunes.scrape_itunes_chart()
    if data:
        print(f"✓ SUCCESS: Scraped {len(data)} songs from iTunes")
        print("\n  First 5 songs:")
        for i, song in enumerate(data[:5], 1):
            print(f"  {i}. {song['song_name']} by {song['artist_name']}")
            print(f"     Sales: {song['digital_sales']} | Position: {song['position']}")
    else:
        print("✗ FAILED: No data returned")
except Exception as e:
    print(f"✗ ERROR: {e}")

print()

# Test Apple Music
print("[4/5] Testing Apple Music scraper...")
try:
    apple = AppleMusicCollector()
    data = apple.scrape_apple_music_chart()
    if data:
        print(f"✓ SUCCESS: Scraped {len(data)} songs from Apple Music")
        print("\n  First 5 songs:")
        for i, song in enumerate(data[:5], 1):
            print(f"  {i}. {song['song_name']} by {song['artist_name']}")
            print(f"     Streams: {song['streams']} | Position: {song['position']}")
    else:
        print("✗ FAILED: No data returned")
except Exception as e:
    print(f"✗ ERROR: {e}")

print()

print("=" * 80)
print("CURRENT DATA TEST COMPLETE")
print("=" * 80)
print()

# Test Historical Data Collection (for building training dataset)
print("=" * 80)
print("TESTING HISTORICAL DATA COLLECTION")
print("=" * 80)
print("This shows how to collect past data for training your model\n")

# Test iTunes historical (has archive from Sept 2024+)
print("[1/3] Testing iTunes Historical Archive...")
try:
    itunes = iTunesCollector()
    # Test a specific historical date
    test_date = "20241101"  # November 1, 2024
    data = itunes.scrape_itunes_chart(test_date)
    if data:
        print(f"✓ SUCCESS: Scraped {len(data)} songs from iTunes archive (Nov 1, 2024)")
        print("\n  First 3 songs from that date:")
        for i, song in enumerate(data[:3], 1):
            print(f"  {i}. {song['song_name']} by {song['artist_name']}")
    else:
        print("✗ FAILED: No historical data returned")
except Exception as e:
    print(f"✗ ERROR: {e}")

print()

# Test Apple Music historical
print("[2/3] Testing Apple Music Historical Archive...")
try:
    apple = AppleMusicCollector()
    test_date = "20241101"
    data = apple.scrape_apple_music_chart(test_date)
    if data:
        print(f"✓ SUCCESS: Scraped {len(data)} songs from Apple Music archive (Nov 1, 2024)")
        print("\n  First 3 songs from that date:")
        for i, song in enumerate(data[:3], 1):
            print(f"  {i}. {song['song_name']} by {song['artist_name']}")
    else:
        print("✗ FAILED: No historical data returned")
except Exception as e:
    print(f"✗ ERROR: {e}")

print()

# Test Billboard Hot 100 historical (from CSV file)
print("[3/3] Testing Billboard Hot 100 Historical (from CSV)...")
try:
    import pandas as pd
    from pathlib import Path
    
    csv_path = Path('Historical-100.csv')
    if csv_path.exists():
        billboard_df = pd.read_csv(csv_path)
        print(f"✓ SUCCESS: Loaded {len(billboard_df):,} records from Historical-100.csv")
        print(f"\n  Columns: {list(billboard_df.columns)}")
        
        # Find date column
        date_col = next((col for col in billboard_df.columns if 'date' in col.lower()), None)
        if date_col:
            billboard_df[date_col] = pd.to_datetime(billboard_df[date_col])
            print(f"  Date range: {billboard_df[date_col].min()} to {billboard_df[date_col].max()}")
            print(f"  Total weeks: {billboard_df[date_col].nunique():,}")
        
        print(f"\n  First 3 #1 songs:")
        
        # Try to find #1 songs (adjust column name as needed)
        pos_col = next((col for col in billboard_df.columns if 'position' in col.lower() or 'rank' in col.lower()), None)
        if pos_col:
            number_ones = billboard_df[billboard_df[pos_col] == 1].head(3)
            for i, row in number_ones.iterrows():
                song_col = next((col for col in row.index if 'song' in col.lower() and 'id' not in col.lower()), None)
                artist_col = next((col for col in row.index if 'artist' in col.lower() or 'performer' in col.lower()), None)
                if song_col and artist_col:
                    date_str = row[date_col].strftime('%Y-%m-%d') if date_col else 'N/A'
                    print(f"  • {row[song_col]} by {row[artist_col]} ({date_str})")
    else:
        print(f"⚠ Historical-100.csv not found in current directory")
        print(f"  Place the CSV in: {Path.cwd()}")
        print(f"  Then run: python3 load_billboard_csv.py")
except Exception as e:
    print(f"✗ ERROR: {e}")

print()
print("=" * 80)
print("ALL TESTS COMPLETE")
print("=" * 80)
print()
print("NEXT STEPS:")
print()
print("1. Collect today's data:")
print("   python3 run_collection.py")
print()
print("2. Load Billboard historical data:")
print("   python3 load_billboard_csv.py")
print()
print("3. Collect historical streaming/sales data (June 2017 - today):")
print("   python3 collect_historical.py")
print()
print("3. This gives you:")
print("   - Daily streaming/sales data going back months")
print("   - Billboard Hot 100 positions (ground truth)")
print("   - Calculate MAs, deltas, momentum for features")
print("   - Train model to predict #1 positions")
print()
print("Historical archives available from:")
print("  • iTunes: June 2017+ (kworb.net goes back to 20170628.html)")
print("  • Apple Music: Oct 2024+")
print("  • Billboard: Use Historical-100.csv (all historical data)")
print()
print("To load Billboard data:")
print("  python3 load_billboard_csv.py")
print("=" * 80)

