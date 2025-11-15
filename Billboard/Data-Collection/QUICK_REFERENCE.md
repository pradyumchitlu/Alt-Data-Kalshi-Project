# 📋 Quick Reference Card

## Three Commands to Know

```bash
# 1. Test that everything works
python3 TEST_SCRAPING.py

# 2. Collect today's data
python3 run_collection.py

# 3. View collected data
ls -lh data/*/
```

## What Gets Collected

| File | Songs/Videos | Source |
|------|--------------|--------|
| `data/spotify/spotify_YYYYMMDD.csv` | 200 | [kworb.net](https://kworb.net/spotify/) |
| `data/youtube/youtube_YYYYMMDD.csv` | 500 | [kworb.net](https://kworb.net/youtube/) |
| `data/itunes/itunes_YYYYMMDD.csv` | 200 | [kworb.net](https://kworb.net/ww/) |
| `data/apple_music/apple_music_YYYYMMDD.csv` | 200 | [kworb.net](https://kworb.net/apple_songs/) |
| `data/radio/radio_YYYYMMDD.csv` | 200 | [kworb.net](https://kworb.net/pop/) |
| `data/billboard/billboard_YYYYMMDD.csv` | 100 | [billboard.com](https://billboard.com) |

## CSV Format

**Spotify**:
```csv
song_id,song_name,artist_name,streams,playlist_adds,chart_position,collection_date
```

**YouTube**:
```csv
video_id,song_name,artist_name,views,likes,comments,chart_position,collection_date
```

**iTunes**:
```csv
song_name,artist_name,digital_sales,physical_sales,total_sales,collection_date
```

**Billboard**:
```csv
song_name,artist_name,chart_position,weeks_on_chart,chart_date
```

## Import in Python

```python
import pandas as pd

# Load today's data
spotify = pd.read_csv('data/spotify/spotify_20251115.csv')
youtube = pd.read_csv('data/youtube/youtube_20251115.csv')
billboard = pd.read_csv('data/billboard/billboard_20251109.csv')

# Merge on song/artist
merged = spotify.merge(youtube, on=['song_name', 'artist_name'])
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | `pip3 install -r requirements.txt` |
| No data collected | Check internet, verify kworb.net accessible |
| Want historical data | Use `collect_historical.py` or methods in scrapers |
| Need database | Optional - see `database.py` |

## File Locations

**Main folder**: `Billboard/Data-Collection/`  
**Collected data**: `Billboard/Data-Collection/data/`  
**Logs**: `Billboard/Data-Collection/logs/`

## Key Files

- `TEST_SCRAPING.py` - Verify scrapers work
- `run_collection.py` - Run collection
- `file_storage.py` - CSV saving logic
- `spotify.py` - Spotify scraper
- `youtube.py` - YouTube scraper
- `itunes.py` - iTunes scraper
- `apple_music.py` - Apple Music scraper
- `radio_airplay.py` - Radio scraper
- `billboard_scraper.py` - Billboard scraper

## Historical Data

Archives available from **Sept 2024** onwards:

```python
from itunes import iTunesCollector
from datetime import date

collector = iTunesCollector()
collector.collect_historical_data(
    start_date=date(2024, 9, 1),
    end_date=date.today()
)
```

Do same for: `AppleMusicCollector`, `RadioAirplayCollector`, `BillboardScraper`

## Next Steps Workflow

```
1. Test Scrapers
   python3 TEST_SCRAPING.py

2. Collect Data
   python3 run_collection.py
   (Run daily or use scheduler.py)

3. Load in Python
   import pandas as pd
   df = pd.read_csv('data/spotify/spotify_20251115.csv')

4. Build Features
   - Moving averages
   - Growth rates
   - Cross-platform metrics

5. Train Model
   - XGBoost/LightGBM
   - Target: Billboard #1 position
   - Features: All collected metrics

6. Make Predictions
   - Probability of reaching #1

7. Compare to Kalshi
   - Model: 65% probability
   - Kalshi: $0.45 (45% implied)
   - Edge: 20%

8. Trade!
   - Buy YES if edge > threshold
```

## Quick Stats

- **Total data sources**: 6 (Spotify, YouTube, iTunes, Apple Music, Radio, Billboard)
- **Songs tracked**: 200 per source  
- **Historical data**: Sept 2024 - present
- **Update frequency**: Daily
- **Storage format**: CSV files
- **Database required**: No
- **API keys required**: No (for kworb.net sources)

## Contact / Support

- Full docs: `README.md`
- Quick start: `START_HERE.md`  
- Complete summary: `FINAL_SUMMARY.md`
- Setup guide: `QUICKSTART.md`

---

**Print this card and keep it handy!** 📋

