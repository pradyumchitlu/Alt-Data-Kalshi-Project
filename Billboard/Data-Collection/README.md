# Billboard Hot 100 Data Collection System

This data collection system gathers comprehensive music industry data to predict Billboard Hot 100 chart positions and identify trading opportunities on Kalshi.

## Data Sources

The system collects data from multiple sources using web scraping (primarily from [kworb.net](https://kworb.net)):

### 1. **Streaming Data**
- **Spotify** ([kworb.net/spotify](https://kworb.net/spotify/country/global_daily.html)): Daily and weekly streaming numbers
- **Apple Music** ([kworb.net/apple_songs](https://kworb.net/apple_songs/)): Apple Music streaming data
- **YouTube** ([kworb.net/youtube](https://kworb.net/youtube/)): Video views and engagement

### 2. **Sales Data**
- **iTunes** ([kworb.net/ww](https://kworb.net/ww/)): Digital sales data

### 3. **Radio Airplay**
- **Pop Radio** ([kworb.net/pop](https://kworb.net/pop/)): Radio spins and audience impressions

### 4. **Social/Viral Data**
- **TikTok**: Trending sounds and video counts (API/scraping)
- **Google Trends**: Search interest and momentum

### 5. **Market Data**
- **Kalshi**: Real-time contract prices and implied probabilities

### 6. **Ground Truth**
- **Billboard Hot 100**: Historical chart positions (training labels)

## Setup Instructions

### 1. Install Dependencies

```bash
cd "Billboard Line/Data Collection"
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

Install PostgreSQL if you haven't already:
```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

Create the database:
```bash
createdb billboard_data
```

### 3. Configure Environment Variables

Create a `.env` file in the `Data Collection` directory:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=billboard_data
DB_USER=postgres
DB_PASSWORD=your_password_here

# Optional API Keys (most collection uses web scraping)
TIKTOK_API_KEY=your_rapidapi_key_here
KALSHI_API_KEY=your_kalshi_email
KALSHI_API_SECRET=your_kalshi_password

# Collection Settings
TOP_N_SONGS=200
COLLECTION_INTERVAL_HOURS=24
```

### 4. Initialize Database

Run the database setup script to create all necessary tables:

```bash
python database.py
```

This will create tables for:
- `spotify_streams`
- `youtube_data`
- `tiktok_data`
- `google_trends`
- `sales_data` (iTunes)
- `radio_airplay`
- `kalshi_market`
- `billboard_hot100`

### 5. Create Required Directories

```bash
mkdir -p data logs
```

## Usage

### Manual Data Collection

Run a single collection cycle:

```bash
python main_collector.py
```

This will collect data from all sources and store it in the database.

### Automated Collection (Recommended)

Use the scheduler to run automated collection:

```bash
python scheduler.py
```

The scheduler will:
- Run data collection every 24 hours (configurable)
- Collect Billboard Hot 100 data every Saturday at 2 PM ET
- Log all activities to `logs/scheduler.log`

### Individual Collectors

You can also run individual collectors:

```bash
# Spotify
python spotify.py

# YouTube
python youtube.py

# iTunes
python itunes.py

# Apple Music
python apple_music.py

# Radio Airplay
python radio_airplay.py

# Google Trends
python google_trends.py

# TikTok
python tiktok.py

# Kalshi Market Data
python kalshi_market.py

# Billboard Hot 100
python billboard_scraper.py
```

### Historical Data Collection

To collect historical data (recommended for model training):

```python
from itunes import iTunesCollector
from apple_music import AppleMusicCollector
from radio_airplay import RadioAirplayCollector
from billboard_scraper import BillboardScraper
from datetime import date

# Set date range (kworb.net has archives going back to ~2024)
start_date = date(2024, 9, 1)
end_date = date.today()

# Collect historical data
itunes = iTunesCollector()
itunes.collect_historical_data(start_date, end_date)

apple = AppleMusicCollector()
apple.collect_historical_data(start_date, end_date)

radio = RadioAirplayCollector()
radio.collect_historical_data(start_date, end_date)

# Billboard Hot 100 (weekly data, Saturdays only)
billboard = BillboardScraper()
billboard.collect_historical_data(start_date, end_date)
```

## Data Collection Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Data Collection System                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌──────────────────┐                    ┌────────────────────┐
│   Web Scrapers   │                    │    API Clients     │
│   (kworb.net)    │                    │                    │
└──────────────────┘                    └────────────────────┘
        │                                           │
        │  • Spotify Charts                         │  • TikTok API
        │  • YouTube Charts                         │  • Google Trends
        │  • iTunes Sales                           │  • Kalshi API
        │  • Apple Music                            │
        │  • Radio Airplay                          │
        │  • Billboard Hot 100                      │
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │  PostgreSQL Database  │
                   │                       │
                   │  • spotify_streams    │
                   │  • youtube_data       │
                   │  • sales_data         │
                   │  • radio_airplay      │
                   │  • tiktok_data        │
                   │  • google_trends      │
                   │  • kalshi_market      │
                   │  • billboard_hot100   │
                   └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │   Feature Enginering │
                   │   & Model Training   │
                   │   (Next Phase)       │
                   └──────────────────────┘
```

## File Structure

```
Data Collection/
├── config.py                 # Configuration and environment variables
├── database.py              # Database setup and connection management
├── spotify.py               # Spotify data collector (kworb.net)
├── youtube.py               # YouTube data collector (kworb.net)
├── itunes.py                # iTunes sales collector (kworb.net)
├── apple_music.py           # Apple Music collector (kworb.net)
├── radio_airplay.py         # Radio airplay collector (kworb.net)
├── tiktok.py                # TikTok viral data collector
├── google_trends.py         # Google Trends search interest
├── kalshi_market.py         # Kalshi market data collector
├── billboard_scraper.py     # Billboard Hot 100 scraper
├── main_collector.py        # Main orchestrator
├── scheduler.py             # Automated scheduling
├── requirements.txt         # Python dependencies
└── README.md               # This file

Generated:
├── data/                    # Raw data storage (optional)
├── logs/                    # Collection logs
└── .env                     # Environment variables (create this)
```

## Important Notes

### Rate Limiting
- Be respectful of source websites
- Default delays between requests: 2-5 seconds
- Kworb.net updates daily, so collecting more frequently isn't useful

### Data Quality
- kworb.net provides historical archives for most sources
- iTunes, Apple Music, and Radio data have archives going back to ~2024
- Spotify weekly data is available with historical charts
- Billboard Hot 100 updates every Saturday

### API Requirements
- Most data collection uses **web scraping** (no API keys needed)
- **TikTok**: Optional, requires RapidAPI subscription
- **Google Trends**: No API key required (uses `pytrends`)
- **Kalshi**: Required for market data (needs account)

### Legal Considerations
- Web scraping should comply with websites' Terms of Service
- Use data responsibly and for educational/research purposes
- Consider rate limiting and robots.txt guidelines

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Test connection
psql -U postgres -d billboard_data
```

### Import Errors
```bash
# Make sure you're in the correct directory
cd "Billboard Line/Data Collection"

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Scraping Failures
- HTML structure may change - update selectors in respective collectors
- Check if kworb.net is accessible
- Verify User-Agent headers are set correctly

## Next Steps

After data collection is set up:

1. **Let it run for 2-4 weeks** to build a good dataset
2. **Collect historical data** using the archive functions
3. **Move to Part 2**: Feature engineering and model training
4. **Part 3**: Build trading signals and Kalshi integration

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review database contents to verify collection
- Test individual collectors before running main orchestrator

