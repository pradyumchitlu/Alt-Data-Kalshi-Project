#!/usr/bin/env python3
"""
Load Billboard Hot 100 historical data from Historical-100.csv
This is the ground truth for training your model
"""
import pandas as pd
import logging
from pathlib import Path
from file_storage import FileStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_billboard_historical(csv_path='Historical-100.csv'):
    """
    Load Billboard Hot 100 historical data from CSV
    
    Expected CSV format should include:
    - chart_date: Date of the chart
    - song_name: Name of the song
    - artist_name: Artist name
    - chart_position: Position on Hot 100 (1-100)
    - weeks_on_chart: Weeks the song has been on chart (optional)
    
    Args:
        csv_path: Path to Historical-100.csv
    
    Returns:
        DataFrame with Billboard Hot 100 historical data
    """
    logger.info("=" * 80)
    logger.info("LOADING BILLBOARD HOT 100 HISTORICAL DATA")
    logger.info("=" * 80)
    
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        logger.error(f"ERROR: {csv_path} not found!")
        logger.info(f"Please place Historical-100.csv in: {Path.cwd()}")
        return None
    
    logger.info(f"\nLoading from: {csv_file}")
    
    try:
        # Load CSV
        df = pd.read_csv(csv_file)
        
        logger.info(f"✓ Loaded {len(df)} records")
        logger.info(f"\nColumns: {list(df.columns)}")
        
        # Check for required columns
        required_cols = ['song_name', 'artist_name', 'chart_position']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            logger.warning(f"\nWARNING: Missing columns: {missing}")
            logger.info("Attempting to map columns automatically...")
            
            # Common column name variations
            col_mapping = {
                'song': 'song_name',
                'title': 'song_name',
                'track': 'song_name',
                'artist': 'artist_name',
                'performer': 'artist_name',
                'position': 'chart_position',
                'rank': 'chart_position',
                'chart_position': 'chart_position',
                'date': 'chart_date',
                'week': 'chart_date',
                'weeks': 'weeks_on_chart'
            }
            
            # Try to map columns
            for col in df.columns:
                col_lower = col.lower().replace(' ', '_')
                if col_lower in col_mapping and col_mapping[col_lower] in missing:
                    df = df.rename(columns={col: col_mapping[col_lower]})
                    logger.info(f"  Mapped '{col}' → '{col_mapping[col_lower]}'")
        
        # Parse date if present
        if 'chart_date' in df.columns:
            df['chart_date'] = pd.to_datetime(df['chart_date'])
            date_range = f"{df['chart_date'].min()} to {df['chart_date'].max()}"
            logger.info(f"\nDate range: {date_range}")
        
        # Show summary
        logger.info(f"\nData summary:")
        logger.info(f"  Total records: {len(df):,}")
        logger.info(f"  Unique songs: {df['song_name'].nunique():,}")
        logger.info(f"  Unique artists: {df['artist_name'].nunique():,}")
        
        if 'chart_date' in df.columns:
            logger.info(f"  Date span: {(df['chart_date'].max() - df['chart_date'].min()).days} days")
            logger.info(f"  Weeks: {df['chart_date'].nunique():,}")
        
        # Show #1 songs
        if 'chart_position' in df.columns:
            number_ones = df[df['chart_position'] == 1]
            logger.info(f"\n  Songs that reached #1: {len(number_ones):,}")
            
            logger.info(f"\n  Sample #1 songs:")
            sample = number_ones.head(5)
            for idx, row in sample.iterrows():
                date_str = row.get('chart_date', 'Unknown date')
                logger.info(f"    • {row['song_name']} - {row['artist_name']} ({date_str})")
        
        logger.info("\n" + "=" * 80)
        logger.info("SUCCESS - Billboard data loaded")
        logger.info("=" * 80)
        
        return df
        
    except Exception as e:
        logger.error(f"ERROR loading CSV: {e}")
        return None


def save_to_individual_files(df):
    """
    Save Billboard data to individual CSV files by date
    (matches format of other collectors)
    """
    if df is None or 'chart_date' not in df.columns:
        logger.error("Cannot save: DataFrame is None or missing chart_date")
        return False
    
    logger.info("\nSaving to individual date files...")
    
    storage = FileStorage()
    dates = df['chart_date'].unique()
    
    for date_val in sorted(dates):
        date_data = df[df['chart_date'] == date_val]
        
        # Convert to list of tuples for file_storage
        data_to_save = []
        for _, row in date_data.iterrows():
            data_to_save.append((
                row['song_name'],
                row['artist_name'],
                int(row['chart_position']),
                int(row.get('weeks_on_chart', 1)),
                pd.to_datetime(date_val).date()
            ))
        
        storage.save_billboard_data(data_to_save, pd.to_datetime(date_val).date())
    
    logger.info(f"✓ Saved {len(dates)} date files to data/billboard/")
    return True


def create_target_variables(df):
    """
    Create useful target variables for modeling
    """
    if df is None:
        return None
    
    logger.info("\nCreating target variables...")
    
    # Binary: reached #1
    df['reached_number_1'] = (df['chart_position'] == 1).astype(int)
    
    # Binary: reached top 10
    df['reached_top10'] = (df['chart_position'] <= 10).astype(int)
    
    # Binary: reached top 40
    df['reached_top40'] = (df['chart_position'] <= 40).astype(int)
    
    logger.info(f"  • reached_number_1: {df['reached_number_1'].sum():,} songs")
    logger.info(f"  • reached_top10: {df['reached_top10'].sum():,} songs")
    logger.info(f"  • reached_top40: {df['reached_top40'].sum():,} songs")
    
    return df


def main():
    """Main execution"""
    # Load Billboard data
    df = load_billboard_historical('Historical-100.csv')
    
    if df is not None:
        # Create target variables
        df = create_target_variables(df)
        
        # Save to individual files (optional - matches other collectors)
        # Uncomment if you want individual date files
        # save_to_individual_files(df)
        
        # Save processed version
        output_file = 'data/billboard_historical_processed.csv'
        df.to_csv(output_file, index=False)
        logger.info(f"\n✓ Saved processed data to: {output_file}")
        
        logger.info("\n" + "=" * 80)
        logger.info("USAGE IN YOUR MODEL")
        logger.info("=" * 80)
        logger.info("\nimport pandas as pd")
        logger.info("")
        logger.info("# Load Billboard historical data")
        logger.info("billboard = pd.read_csv('data/billboard_historical_processed.csv')")
        logger.info("")
        logger.info("# This gives you ground truth labels:")
        logger.info("#   - reached_number_1: 1 if song hit #1, else 0")
        logger.info("#   - reached_top10: 1 if song hit top 10, else 0")
        logger.info("#   - chart_position: actual position (1-100)")
        logger.info("")
        logger.info("# Merge with your feature data:")
        logger.info("training_data = itunes_df.merge(")
        logger.info("    billboard,")
        logger.info("    on=['song_name', 'artist_name', 'chart_date'],")
        logger.info("    how='left'")
        logger.info(")")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()

