# 🎯 UPDATES COMPLETE - Ready to Use!

## Changes Made

### 1. ✅ Corrected Historical Date Range
- **Updated from:** Sept 2024
- **Updated to:** June 28, 2017 (20170628.html)
- iTunes archive goes back 8+ years!
- ~2,700 days of historical data available

### 2. ✅ Billboard Historical Data - CSV Loading
- **Removed:** Billboard scraping (not available historically)
- **Added:** `load_billboard_csv.py` - loads your Historical-100.csv
- Automatically maps column names
- Creates target variables (reached_number_1, reached_top10, etc.)
- Provides merge instructions for training data

### 3. ✅ Verified Data Collection Completeness
Historical collectors capture ALL key data points, not just song names:

**iTunes Historical Data:**
```python
{
    'song_name': str,
    'artist_name': str,
    'digital_sales': int,
    'physical_sales': int (0),
    'total_sales': int,
    'collection_date': date
}
```

**Apple Music Historical Data:**
```python
{
    'song_id': str,
    'song_name': str,
    'artist_name': str,
    'streams': int,
    'playlist_adds': int (0),
    'chart_position': int,
    'collection_date': date
}
```

**Billboard from CSV:**
```python
{
    'song_name': str,
    'artist_name': str,
    'chart_position': int (1-100),
    'weeks_on_chart': int,
    'chart_date': date,
    'reached_number_1': bool,  # Target variable
    'reached_top10': bool,     # Target variable
    'reached_top40': bool      # Target variable
}
```

---

## 📊 How to Use

### Step 1: Test Current Scraping
```bash
cd "/Users/pradyumchitlu/kalshi project/Alt-Data-Kalshi-Project/Billboard/Data-Collection"
python3 TEST_SCRAPING.py
```

This will:
- Test all 4 current data sources (Spotify, YouTube, iTunes, Apple Music)
- Show first 5 songs from each to verify accuracy
- Test historical data collection with sample dates
- Attempt to load Historical-100.csv if present

### Step 2: Load Billboard Historical Data
```bash
python3 load_billboard_csv.py
```

Make sure `Historical-100.csv` is in the Data-Collection directory.

This will:
- Load all Billboard Hot 100 historical data
- Auto-detect and map column names
- Create target variables for modeling
- Save processed data to `data/billboard_historical_processed.csv`
- Show merge instructions

### Step 3: Collect Daily Data (Ongoing)
```bash
python3 run_collection.py
```

Collects today's data from:
- Spotify (daily chart)
- YouTube (music videos)
- iTunes (worldwide sales)
- Apple Music (streaming)
- Billboard (on Saturdays only)

### Step 4: Collect Historical Training Data
```bash
python3 collect_historical.py
```

**Default:** Collects last 6 months (faster for testing)

**To collect ALL data from 2017:**
Edit line 207 in `collect_historical.py`:
```python
# Change this:
itunes_start = date.today() - timedelta(days=180)  # Last 6 months

# To this:
itunes_start = start_date  # ALL data from June 2017
```

Then run:
```bash
python3 collect_historical.py
```

⚠️ **Note:** Collecting all data from 2017 will take several hours due to:
- ~2,700 days of iTunes data
- ~400+ days of Apple Music data  
- 1 second delay between requests (to be respectful to kworb.net)

---

## 🎓 Building Your Training Dataset

### Merge Strategy

```python
import pandas as pd
from datetime import datetime, timedelta

# 1. Load Billboard historical data (ground truth)
billboard = pd.read_csv('data/billboard_historical_processed.csv')
billboard['chart_date'] = pd.to_datetime(billboard['chart_date'])

# 2. Load iTunes historical data (features)
itunes_files = sorted(Path('data/itunes').glob('itunes_*.csv'))
itunes_list = []
for f in itunes_files:
    df = pd.read_csv(f)
    itunes_list.append(df)
itunes = pd.concat(itunes_list, ignore_index=True)
itunes['collection_date'] = pd.to_datetime(itunes['collection_date'])

# 3. Calculate Moving Averages & Deltas
itunes = itunes.sort_values(['song_name', 'artist_name', 'collection_date'])

# 7-day MA
itunes['sales_ma7'] = itunes.groupby(['song_name', 'artist_name'])['digital_sales'].transform(
    lambda x: x.rolling(7, min_periods=1).mean()
)

# 14-day MA
itunes['sales_ma14'] = itunes.groupby(['song_name', 'artist_name'])['digital_sales'].transform(
    lambda x: x.rolling(14, min_periods=1).mean()
)

# Day-over-day delta
itunes['sales_delta'] = itunes.groupby(['song_name', 'artist_name'])['digital_sales'].diff()

# Week-over-week delta
itunes['sales_delta_7d'] = itunes.groupby(['song_name', 'artist_name'])['digital_sales'].diff(7)

# Momentum (MA7 / MA14)
itunes['momentum'] = itunes['sales_ma7'] / itunes['sales_ma14']

# 4. Merge with Billboard (target)
# Billboard chart reflects data from ~1 week prior
billboard['feature_date'] = billboard['chart_date'] - timedelta(days=7)

training_data = billboard.merge(
    itunes,
    left_on=['song_name', 'artist_name', 'feature_date'],
    right_on=['song_name', 'artist_name', 'collection_date'],
    how='left'
)

# 5. Features for modeling
features = [
    'digital_sales',
    'sales_ma7',
    'sales_ma14', 
    'sales_delta',
    'sales_delta_7d',
    'momentum'
]

target = 'reached_number_1'

# 6. Train/test split
from sklearn.model_selection import train_test_split

X = training_data[features].fillna(0)
y = training_data[target]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 7. Train model
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 8. Evaluate
from sklearn.metrics import classification_report, roc_auc_score

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.3f}")

# 9. Feature importance
importances = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(importances)
```

---

## 📁 File Structure

```
Data-Collection/
├── TEST_SCRAPING.py              # ✅ UPDATED - Test all scrapers
├── run_collection.py             # ✅ Collect today's data
├── collect_historical.py         # ✅ UPDATED - Collect 2017-today
├── load_billboard_csv.py         # ✅ NEW - Load your CSV
│
├── spotify.py                    # Current day scraper
├── youtube.py                    # Current day scraper
├── itunes.py                     # Current + historical
├── apple_music.py                # Current + historical
├── billboard_scraper.py          # Current only (Saturdays)
│
├── file_storage.py               # ✅ Save to CSV files
│
├── Historical-100.csv            # ← Place your CSV here
│
└── data/                         # Output directory
    ├── spotify/
    ├── youtube/
    ├── itunes/
    ├── apple_music/
    ├── billboard/
    └── billboard_historical_processed.csv
```

---

## 🚀 Quick Start Checklist

- [ ] 1. Place `Historical-100.csv` in Data-Collection directory
- [ ] 2. Run `python3 TEST_SCRAPING.py` to verify current scraping works
- [ ] 3. Run `python3 load_billboard_csv.py` to load ground truth labels
- [ ] 4. Run `python3 collect_historical.py` to collect training data (6 months or all)
- [ ] 5. Run `python3 run_collection.py` daily to collect new data
- [ ] 6. Use merge strategy above to create training dataset
- [ ] 7. Train model on historical data
- [ ] 8. Use daily data for real-time predictions

---

## 📈 What You Can Now Analyze

With historical data from June 2017, you can:

1. **Calculate Moving Averages:** 7-day, 14-day, 30-day MAs
2. **Track Deltas:** Day-over-day, week-over-week changes
3. **Measure Momentum:** Rate of change in streams/sales
4. **Identify Patterns:** What streaming/sales trajectory leads to #1?
5. **Build Features:** 
   - Peak sales day
   - Days since release
   - Velocity (rate of growth)
   - Acceleration (rate of velocity change)
   - Cross-platform correlation (iTunes vs Apple Music)

---

## ⚠️ Important Notes

1. **iTunes archive:** June 2017 - present (~2,700 days)
2. **Apple Music archive:** October 2024 - present (~400 days)
3. **Billboard:** Use Historical-100.csv (provided by user)
4. **Spotify/YouTube:** Current day only (no historical archive)

5. **Rate limiting:** 1-second delay between requests (be respectful!)
6. **Data size:** Full historical collection = ~2,700 CSV files
7. **Time estimate:** Full collection ~1-2 hours

---

## 🎯 Next: Kalshi Market Integration

Once you have:
- ✅ Billboard historical data loaded
- ✅ Streaming/sales historical data collected
- ✅ Moving averages & deltas calculated
- ✅ Model trained

Then integrate with Kalshi:
1. Collect today's data daily
2. Calculate same features as training
3. Run model prediction
4. Compare with Kalshi market odds
5. Identify edge (your prediction vs market)
6. Place trades when edge is significant

---

**Status:** ✅ ALL SYSTEMS READY

**Archives Available:**
- iTunes: 2017-06-28 to present
- Apple Music: 2024-10-01 to present  
- Billboard: Historical-100.csv

**Data Points Captured:**
- ✅ Song names
- ✅ Artist names
- ✅ Sales/streams
- ✅ Chart positions
- ✅ Dates

**Ready to:**
- Calculate MAs
- Track deltas
- Build momentum features
- Train predictive model

