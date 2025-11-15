#!/usr/bin/env python3
"""Quick test to verify parsing works"""
from spotify import SpotifyCollector

print("Testing Spotify scraper...")
collector = SpotifyCollector()
data = collector.scrape_daily_chart()

if data:
    print(f"\n✓ SUCCESS: Scraped {len(data)} songs\n")
    print("First 5 songs:")
    for i, song in enumerate(data[:5], 1):
        print(f"{i}. '{song['song_name']}' by '{song['artist_name']}'")
        print(f"   Streams: {song['streams']:,} | Position: {song['position']}\n")
else:
    print("✗ FAILED")

