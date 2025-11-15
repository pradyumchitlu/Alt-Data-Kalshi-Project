# 🚀 Billboard Hot 100 Data Collection - START HERE

## Quick Start (2 Commands)

```bash
cd "/Users/pradyumchitlu/kalshi project/Alt-Data-Kalshi-Project/Billboard/Data-Collection"

# Test that scraping works
python3 TEST_SCRAPING.py

# If tests pass, run data collection
python3 run_collection.py
```

## ✅ Fixed Issues

1. **Two folders problem**: FIXED - Now only ONE folder: `Data-Collection/`
2. **PostgreSQL requirement**: FIXED - No database needed, saves to CSV files
3. **Scraping verification**: Run `TEST_SCRAPING.py` to verify all scrapers work

## What You Get

This system collects data from [kworb.net](https://kworb.net) which tracks ALL music charts:

| Source | URL | Data Points | Count |
|--------|-----|-------------|-------|
| Spotify | [Daily](https://kworb.net/spotify/country/global_daily.html) / [Weekly](https://kworb.net/spotify/country/global_weekly.html) | Streams, positions | 200 songs |
| YouTube | [Charts](https://kworb.net/youtube/) | Views, likes, comments | 500 videos |
| iTunes | [Worldwide](https://kworb.net/ww/) | Digital sales | 200 songs |
| Apple Music | [Charts](https://kworb.net/apple_songs/) | Streams, positions | 200 songs |
| Radio | [Pop Airplay](https://kworb.net/pop/) | Spins, impressions | 200 songs |
| Billboard | [Hot 100](https://www.billboard.com/charts/hot-100) | Chart positions | 100 songs |

## File Structure (ONE folder!)

```
Data-Collection/               ← ONLY folder you need
├── START_HERE.md              ← You are here
├── TEST_SCRAPING.py           ← ⭐ Test scrapers work
├── run_collection.py          ← ⭐ Run daily collection
├── file_storage.py            ← Saves to CSV files
│
├── spotify.py                 ← Scrapes Spotify charts
├── youtube.py                 ← Scrapes YouTube charts
├── itunes.py                  ← Scrapes iTunes sales
├── apple_music.py             ← Scrapes Apple Music
├── radio_airplay.py           ← Scrapes radio airplay
├── billboard_scraper.py       ← Scrapes Billboard Hot 100
│
├── requirements.txt           ← Python dependencies
├── README.md                  ← Full documentation
└── data/                      ← Your collected data (CSV files)
    ├── spotify/
    ├── youtube/
    ├── itunes/
    ├── apple_music/
    ├── radio/
    └── billboard/
```

## Installation

```bash
pip3 install -r requirements.txt
```

That's it! No database setup required.

## Usage

### 1. Test Scrapers

```bash
python3 TEST_SCRAPING.py
```

This will test each scraper and show you examples of collected data.

### 2. Collect Today's Data

```bash
python3 run_collection.py
```

Saves data to `data/` as CSV files.

### 3. Verify Data Was Saved

```bash
ls -lh data/spotify/
ls -lh data/youtube/
head data/spotify/*.csv
```

## Data Format

All files are CSV with consistent structure:

**Spotify** (`data/spotify/spotify_YYYYMMDD.csv`):
```csv
song_id,song_name,artist_name,streams,playlist_adds,chart_position,collection_date
taylor_swift_cruel_summer,Cruel Summer,Taylor Swift,5000000,0,1,2025-11-15
```

**YouTube** (`data/youtube/youtube_YYYYMMDD.csv`):
```csv
video_id,song_name,artist_name,views,likes,comments,chart_position,collection_date
```

And so on for each source.

## Historical Data Collection

kworb.net has archives going back to Sept 2024! To collect historical data:

```python
from itunes import iTunesCollector
from datetime import date

collector = iTunesCollector()
collector.collect_historical_data(
    start_date=date(2024, 9, 1),
    end_date=date.today()
)
```

Do this for iTunes, Apple Music, and Radio to get training data!

## What's Working (From Your Terminal)

Your scrapers ARE working! From your previous run:
```
INFO:spotify:Scraped 200 songs from daily chart          ✓
INFO:youtube:Scraped 500 videos from YouTube chart       ✓
INFO:itunes:Scraped 200 songs from iTunes chart          ✓
INFO:apple_music:Scraped 200 songs from Apple Music      ✓
INFO:radio:Scraped 127 songs from radio chart            ✓
```

The ONLY issue was PostgreSQL. Now we save to CSV instead!

## Next Steps

1. **Test scrapers**: `python3 TEST_SCRAPING.py`
2. **Collect data**: `python3 run_collection.py`
3. **Verify files**: `ls data/*/`
4. **Build features**: Transform data for ML model
5. **Train model**: Predict Billboard Hot 100 positions
6. **Trade on Kalshi**: Find edge vs market prices

## Support Files

- `START_HERE.md` ← You are here
- `README.md` - Comprehensive documentation
- `QUICKSTART.md` - 5-minute setup guide
- `requirements.txt` - Python dependencies

## Advantages

✅ **No database required** - Pure Python + CSV  
✅ **Easy to inspect** - Open CSV files in Excel  
✅ **Historical archives** - Sept 2024+ available  
✅ **Ready for ML** - Standard format for pandas  
✅ **Portable** - Copy data/ folder anywhere  

## Troubleshooting

**Problem**: Import errors  
**Solution**: `pip3 install -r requirements.txt`

**Problem**: No data collected  
**Solution**: Check internet, verify kworb.net is accessible

**Problem**: Want PostgreSQL  
**Solution**: See `database.py` for DB setup (optional)

## Success Metrics

You'll see:
```
✓ SUCCESS: Scraped 200 songs from Spotify
✓ SUCCESS: Scraped 500 videos from YouTube  
✓ SUCCESS: Scraped 200 songs from iTunes
✓ SUCCESS: Scraped 200 songs from Apple Music
✓ SUCCESS: Scraped 127 songs from Radio

Total: 5/5 sources collected successfully
Data saved to: data/ directory
```

Files in `data/`:
```
data/spotify/spotify_20251115.csv
data/youtube/youtube_20251115.csv
data/itunes/itunes_20251115.csv
data/apple_music/apple_music_20251115.csv
data/radio/radio_20251115.csv
```

## You're Ready!

🎉 **Everything is fixed and consolidated into ONE folder!**

Run `python3 TEST_SCRAPING.py` to verify, then start collecting data with `python3 run_collection.py`.

Good luck predicting the Billboard Hot 100! 🎵📈💰

