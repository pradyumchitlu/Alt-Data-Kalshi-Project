#!/usr/bin/env python3
"""Debug script to see what's actually being scraped"""
import requests
from bs4 import BeautifulSoup

# Test Spotify
print("=" * 80)
print("DEBUGGING SPOTIFY SCRAPER")
print("=" * 80)

url = "https://kworb.net/spotify/country/global_daily.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

table = soup.find('table')
if table:
    rows = table.find_all('tr')[1:6]  # Get first 5 data rows
    
    for idx, row in enumerate(rows, 1):
        cols = row.find_all('td')
        print(f"\nRow {idx}:")
        print(f"  Number of columns: {len(cols)}")
        for i, col in enumerate(cols[:5]):  # Show first 5 columns
            text = col.get_text(strip=True)
            print(f"  Col {i}: '{text[:50]}'")  # Truncate long text
else:
    print("NO TABLE FOUND!")

print("\n" + "=" * 80)
print("DEBUGGING YOUTUBE SCRAPER")
print("=" * 80)

url = "https://kworb.net/youtube/"
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

table = soup.find('table')
if table:
    rows = table.find_all('tr')[1:6]
    
    for idx, row in enumerate(rows, 1):
        cols = row.find_all('td')
        print(f"\nRow {idx}:")
        print(f"  Number of columns: {len(cols)}")
        for i, col in enumerate(cols[:5]):
            text = col.get_text(strip=True)
            print(f"  Col {i}: '{text[:50]}'")
else:
    print("NO TABLE FOUND!")

print("\n" + "=" * 80)

