# Quick Start Guide

Get the Billboard Hot 100 data collection system running in 5 minutes.

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Internet connection

## Quick Setup (5 Steps)

### 1. Install Dependencies
```bash
cd "Billboard Line/Data Collection"
pip install -r requirements.txt
```

### 2. Setup PostgreSQL
```bash
# Install PostgreSQL (if not installed)
# macOS:
brew install postgresql && brew services start postgresql

# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib

# Create database
createdb billboard_data
```

### 3. Configure Environment
Create a `.env` file:
```bash
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=billboard_data
DB_USER=postgres
DB_PASSWORD=
TOP_N_SONGS=200
COLLECTION_INTERVAL_HOURS=24
EOF
```

### 4. Initialize Database
```bash
python database.py
```

### 5. Run Data Collection
```bash
# Single run
python main_collector.py

# OR automated (runs continuously)
python scheduler.py
```

## What Gets Collected

✅ **Spotify** streaming data (kworb.net)  
✅ **YouTube** views and engagement (kworb.net)  
✅ **iTunes** sales data (kworb.net)  
✅ **Apple Music** streaming (kworb.net)  
✅ **Radio Airplay** spins and impressions (kworb.net)  
✅ **TikTok** viral momentum (optional API)  
✅ **Google Trends** search interest  
✅ **Kalshi** market prices (optional API)  
✅ **Billboard Hot 100** actual chart positions  

## Data Sources

All primary data comes from **[kworb.net](https://kworb.net)** via web scraping:

- [Spotify Daily](https://kworb.net/spotify/country/global_daily.html)
- [Spotify Weekly](https://kworb.net/spotify/country/global_weekly.html)
- [YouTube Charts](https://kworb.net/youtube/)
- [iTunes Sales](https://kworb.net/ww/)
- [Apple Music](https://kworb.net/apple_songs/)
- [Pop Radio](https://kworb.net/pop/)

**No API keys required** for basic functionality! 🎉

## Verify It's Working

### Check Database
```bash
psql billboard_data

# Check tables
\dt

# Check Spotify data
SELECT COUNT(*) FROM spotify_streams;

# Check Billboard data
SELECT * FROM billboard_hot100 ORDER BY chart_position LIMIT 10;
```

### Check Logs
```bash
tail -f logs/data_collection.log
```

### Test Individual Collector
```bash
python spotify.py
# Should see: "Successfully collected data for X tracks"
```

## Collection Schedule

**Automatic (with scheduler.py):**
- Every 24 hours: All streaming/social data
- Every Saturday 2PM ET: Billboard Hot 100 update

**Manual:**
```bash
python main_collector.py  # Run anytime
```

## Historical Data

Collect past data for model training:

```python
from itunes import iTunesCollector
from datetime import date

collector = iTunesCollector()
collector.collect_historical_data(
    start_date=date(2024, 9, 1),
    end_date=date.today()
)
```

Repeat for: `apple_music.py`, `radio_airplay.py`, `billboard_scraper.py`

## Troubleshooting

### "Can't connect to database"
```bash
# Check PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Check credentials in .env match PostgreSQL
psql -U postgres -d billboard_data
```

### "No data collected"
- Check internet connection
- Verify kworb.net is accessible: https://kworb.net/spotify/
- Check logs: `cat logs/data_collection.log`

### "Import errors"
```bash
pip install -r requirements.txt --upgrade
```

## What's Next?

1. ✅ **Let it collect for 2-4 weeks** (or collect historical data)
2. 📊 **Feature Engineering** - Transform raw data into predictive features
3. 🤖 **Model Training** - Build ML models to predict Billboard positions
4. 💰 **Trading Strategy** - Generate Kalshi trading signals

See `README.md` for detailed documentation.

## Optional: API Keys

For enhanced data collection, add to `.env`:

```bash
# TikTok (RapidAPI)
TIKTOK_API_KEY=your_rapidapi_key

# Kalshi Trading
KALSHI_API_KEY=your_email
KALSHI_API_SECRET=your_password
```

## File Overview

```
spotify.py          → Spotify streaming (kworb.net)
youtube.py          → YouTube views (kworb.net)
itunes.py           → iTunes sales (kworb.net)
apple_music.py      → Apple Music (kworb.net)
radio_airplay.py    → Radio spins (kworb.net)
tiktok.py           → TikTok trends (API)
google_trends.py    → Search interest (pytrends)
kalshi_market.py    → Market prices (Kalshi API)
billboard_scraper.py → Billboard Hot 100 (billboard.com)

main_collector.py   → Run all collectors
scheduler.py        → Automated collection
database.py         → DB setup & management
config.py           → Configuration
```

## Support

- 📖 Full docs: `README.md`
- 🐛 Issues: Check `logs/` directory
- 💡 Questions: Review database schema in `database.py`

**Good luck with your Billboard predictions! 🎵📈**

