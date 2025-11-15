# 📖 Complete Usage Guide

## Quick Start

```bash
cd "/Users/pradyumchitlu/kalshi project/Alt-Data-Kalshi-Project/Billboard/Data-Collection"

# Test everything works (current + historical data)
python3 TEST_SCRAPING.py

# Collect today's data
python3 run_collection.py

# Collect all historical data (Sept 2024 - today)
python3 collect_historical.py
```

## What You Get

### 4 Data Sources

| Source | Daily | Historical Archive | Data Points |
|--------|-------|-------------------|-------------|
| **Spotify** | ✅ Yes | ❌ No | Streams, positions (200 songs) |
| **YouTube** | ✅ Yes | ❌ No | Views, likes, comments (500 videos) |
| **iTunes** | ✅ Yes | ✅ **Sept 2024+** | Digital sales (200 songs) |
| **Apple Music** | ✅ Yes | ✅ **Oct 2024+** | Streams, positions (200 songs) |
| **Billboard Hot 100** | ✅ Yes (Sat) | ✅ **All time** | Chart positions, weeks on chart (100 songs) |

### Why Historical Data Matters

To predict Billboard Hot 100, you need:

1. **Moving Averages** - 7-day, 14-day, 30-day trends
2. **Deltas** - Week-over-week changes
3. **Momentum** - Growth rates and acceleration
4. **Historical labels** - Which songs actually reached #1 (from Billboard)

**You can only calculate these with historical data!**

## File Structure

```
Data-Collection/
├── data/                          ← Your collected data (CSV)
│   ├── spotify/
│   │   ├── spotify_20241101.csv   ← Daily files
│   │   ├── spotify_20241102.csv
│   │   └── spotify_20241115.csv
│   ├── youtube/
│   │   └── youtube_*.csv
│   ├── itunes/
│   │   └── itunes_*.csv          ← Historical from Sept 2024+
│   ├── apple_music/
│   │   └── apple_music_*.csv     ← Historical from Oct 2024+
│   └── billboard/
│       └── billboard_*.csv        ← Weekly (Saturdays only)
│
└── logs/
    ├── collection.log             ← Daily collection logs
    └── historical_collection.log  ← Historical collection logs
```

## Step-by-Step Workflow

### Step 1: Test Scrapers

```bash
python3 TEST_SCRAPING.py
```

**What this does:**
- Tests current data collection (Spotify, YouTube, iTunes, Apple Music)
- Tests historical archives (iTunes Nov 1, Apple Music Nov 1, Billboard Nov 9)
- Shows you exactly what data looks like
- Confirms everything is working

**Expected output:**
```
[1/4] Testing Spotify scraper...
✓ SUCCESS: Scraped 200 songs from Spotify

  First 5 songs:
  1. 'The Fate of Ophelia' by 'Taylor Swift'
     Streams: 51,503,538 | Position: 1
  ...

[1/3] Testing iTunes Historical Archive...
✓ SUCCESS: Scraped 200 songs from iTunes archive (Nov 1, 2024)

  First 3 songs from that date:
  1. A Bar Song (Tipsy) by Shaboozey
  2. Die With A Smile by Lady Gaga
  3. Birds Of A Feather by Billie Eilish
```

### Step 2: Collect Current Data

```bash
python3 run_collection.py
```

**What this does:**
- Collects today's data from Spotify, YouTube, iTunes, Apple Music
- Collects Billboard Hot 100 (if today is Saturday)
- Saves everything to CSV files

**When to run:** Daily (automate with cron/scheduler)

### Step 3: Collect Historical Data

```bash
python3 collect_historical.py
```

**What this does:**
- Collects **iTunes** data from Sept 1, 2024 to yesterday (every day)
- Collects **Apple Music** data from Oct 1, 2024 to yesterday (every day)
- Collects **Billboard Hot 100** from Sept 1, 2024 to last Saturday (weekly)

**This is CRUCIAL for training!** It gives you:
- ~75 days of iTunes data
- ~45 days of Apple Music data  
- ~11 weeks of Billboard Hot 100 data

**How long it takes:** 
- iTunes: ~2 minutes (75 days × 1 sec delay)
- Apple Music: ~1 minute (45 days × 1 sec delay)
- Billboard: ~1 minute (11 weeks × 5 sec delay)
- **Total: ~4-5 minutes**

**When to run:** Once to build initial dataset, then daily to add new data

## Using the Data

### Load in Python

```python
import pandas as pd
from pathlib import Path

# Load all iTunes data (historical + current)
itunes_files = Path('data/itunes').glob('*.csv')
itunes_df = pd.concat([pd.read_csv(f) for f in itunes_files], ignore_index=True)

# Load all Apple Music data
apple_files = Path('data/apple_music').glob('*.csv')
apple_df = pd.concat([pd.read_csv(f) for f in apple_files], ignore_index=True)

# Load Billboard Hot 100 (ground truth labels)
billboard_files = Path('data/billboard').glob('*.csv')
billboard_df = pd.concat([pd.read_csv(f) for f in billboard_files], ignore_index=True)

print(f"iTunes: {len(itunes_df)} rows")
print(f"Apple Music: {len(apple_df)} rows")
print(f"Billboard: {len(billboard_df)} rows")
```

### Calculate Features (MAs, Deltas, Momentum)

```python
# Convert date column
itunes_df['collection_date'] = pd.to_datetime(itunes_df['collection_date'])
itunes_df = itunes_df.sort_values(['song_name', 'artist_name', 'collection_date'])

# 7-day moving average
itunes_df['sales_7day_ma'] = (
    itunes_df
    .groupby(['song_name', 'artist_name'])['digital_sales']
    .rolling(window=7, min_periods=1)
    .mean()
    .reset_index(level=[0,1], drop=True)
)

# 14-day moving average
itunes_df['sales_14day_ma'] = (
    itunes_df
    .groupby(['song_name', 'artist_name'])['digital_sales']
    .rolling(window=14, min_periods=1)
    .mean()
    .reset_index(level=[0,1], drop=True)
)

# Week-over-week delta (7 days ago)
itunes_df['sales_delta_7d'] = (
    itunes_df
    .groupby(['song_name', 'artist_name'])['digital_sales']
    .diff(periods=7)
)

# Growth rate
itunes_df['sales_growth_7d'] = (
    itunes_df
    .groupby(['song_name', 'artist_name'])['digital_sales']
    .pct_change(periods=7)
)

# Momentum (acceleration)
itunes_df['sales_momentum'] = (
    itunes_df
    .groupby(['song_name', 'artist_name'])['sales_growth_7d']
    .diff()
)
```

### Create Target Variable

```python
# Billboard Hot 100: 1 if song reached #1, 0 otherwise
billboard_df['reached_number_1'] = (billboard_df['chart_position'] == 1).astype(int)

# Also useful: Top 10, Top 40
billboard_df['reached_top10'] = (billboard_df['chart_position'] <= 10).astype(int)
billboard_df['reached_top40'] = (billboard_df['chart_position'] <= 40).astype(int)
```

### Merge Data Sources

```python
# Merge iTunes + Billboard on song/artist/date
# Note: Billboard is weekly (Saturdays), so need to align dates

# Get the Saturday for each date
def get_saturday(dt):
    """Get the Saturday of the week containing dt"""
    days_ahead = 5 - dt.weekday()  # 5 = Saturday
    if days_ahead < 0:  # Already past Saturday
        days_ahead += 7
    return dt + pd.Timedelta(days=days_ahead)

itunes_df['chart_week_saturday'] = itunes_df['collection_date'].apply(get_saturday)
billboard_df['chart_date'] = pd.to_datetime(billboard_df['chart_date'])

# Merge
training_data = itunes_df.merge(
    billboard_df,
    left_on=['song_name', 'artist_name', 'chart_week_saturday'],
    right_on=['song_name', 'artist_name', 'chart_date'],
    how='left'
)

# Fill missing values (songs not on Billboard = position 101+)
training_data['chart_position'] = training_data['chart_position'].fillna(101)
training_data['reached_number_1'] = training_data['reached_number_1'].fillna(0).astype(int)
```

### Train Model

```python
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

# Select features
features = [
    'digital_sales',
    'sales_7day_ma',
    'sales_14day_ma',
    'sales_delta_7d',
    'sales_growth_7d',
    'sales_momentum'
]

# Prepare data (drop rows with NaN from rolling calculations)
model_data = training_data.dropna(subset=features + ['reached_number_1'])

X = model_data[features]
y = model_data['reached_number_1']

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train
model = XGBClassifier(
    max_depth=5,
    n_estimators=100,
    learning_rate=0.1,
    scale_pos_weight=len(y_train[y_train==0]) / len(y_train[y_train==1])  # Handle imbalance
)

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba):.3f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Feature importance
importance_df = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(importance_df)
```

### Make Predictions

```python
# Get latest data for prediction
latest_date = itunes_df['collection_date'].max()
latest_data = itunes_df[itunes_df['collection_date'] == latest_date].copy()

# Calculate features
# ... (same as above)

# Predict
latest_data['prob_number_1'] = model.predict_proba(latest_data[features])[:, 1]

# Top predictions
top_predictions = (
    latest_data
    .nlargest(20, 'prob_number_1')
    [['song_name', 'artist_name', 'prob_number_1', 'digital_sales', 'sales_7day_ma']]
)

print("\nTop 20 Predictions for Next Week's #1:")
print(top_predictions)
```

### Compare to Kalshi

```python
# Your model's prediction
model_prob = 0.65  # 65% chance of reaching #1

# Kalshi market price
kalshi_price = 0.45  # $0.45 = 45% implied probability

# Calculate edge
edge = model_prob - kalshi_price  # 0.20 = 20% edge!

# Trading decision
if edge > 0.10:  # 10% minimum threshold
    print(f"✓ BUY YES contract!")
    print(f"   Model: {model_prob:.1%}")
    print(f"   Market: {kalshi_price:.1%}")
    print(f"   Edge: {edge:.1%}")
elif edge < -0.10:
    print(f"✓ BUY NO contract (or sell YES)")
else:
    print(f"✗ No trade - edge too small ({edge:.1%})")
```

## Automation

### Daily Collection (Cron)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 8 AM
0 8 * * * cd /Users/pradyumchitlu/kalshi\ project/Alt-Data-Kalshi-Project/Billboard/Data-Collection && /usr/bin/python3 run_collection.py >> logs/cron.log 2>&1
```

### Scheduler (Python)

```python
# scheduler_daily.py
import schedule
import time
from run_collection import collect_all_today

schedule.every().day.at("08:00").do(collect_all_today)

while True:
    schedule.run_pending()
    time.sleep(60)
```

Run it:
```bash
python3 scheduler_daily.py &
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | `pip3 install -r requirements.txt` |
| No historical data | Check date format: `YYYYMMDD` (e.g., `20241101`) |
| Empty dataframes | Verify files exist: `ls data/itunes/` |
| NaN in features | Use `dropna()` or `fillna()` after rolling calculations |
| Class imbalance | Use `scale_pos_weight` in XGBoost |

## Next Steps

1. ✅ **Collect historical data** ← Start here!
   ```bash
   python3 collect_historical.py
   ```

2. ✅ **Load and explore**
   ```python
   import pandas as pd
   from pathlib import Path
   
   itunes = pd.concat([pd.read_csv(f) for f in Path('data/itunes').glob('*.csv')])
   print(itunes.head())
   print(itunes.describe())
   ```

3. ✅ **Calculate features**
   - Moving averages (7, 14, 30 days)
   - Deltas (week-over-week changes)
   - Growth rates
   - Momentum

4. ✅ **Train model**
   - XGBoost or LightGBM
   - Target: `reached_number_1`
   - Evaluate with AUC-ROC

5. ✅ **Make predictions**
   - Predict next week's #1
   - Compare to Kalshi prices
   - Find edge and trade!

---

**Ready to build your Billboard predictor!** 🎵📈💰

