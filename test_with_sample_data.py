#!/usr/bin/env python3
"""
Test script using sample data to verify HTI symbol detection.
"""

import pandas as pd
from datetime import datetime

def test_with_sample_data():
    """Test with sample data to check for HTI symbol."""
    print("🔍 Testing with sample data and checking for HTI symbol...")
    print("=" * 60)
    
    # Read the sample file
    filename = 'sample_settlement_data.dat'
    print(f"📖 Reading sample file: {filename}")
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
        print("✅ Sample file read successfully")
    except FileNotFoundError:
        print(f"❌ Sample file not found: {filename}")
        return False

    # Split into lines and find the header index
    lines = content.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('Series'):
            header_idx = i
            break
    
    if header_idx is None:
        print("❌ Could not find header line starting with 'Series'")
        print("🔍 First few lines of the file:")
        for i, line in enumerate(lines[:10]):
            print(f"   {i+1}: {line}")
        return False
    
    print(f"✅ Found header at line {header_idx + 1}")

    # Extract column names and data rows
    columns = lines[header_idx].split()
    data_rows = [ln.split() for ln in lines[header_idx+1:] if ln.strip()]
    
    print(f"📊 Found {len(data_rows)} data rows")
    print(f"📋 Columns: {columns}")

    # Build DataFrame
    try:
        df = pd.DataFrame(data_rows, columns=columns)
        print(f"✅ DataFrame created with shape: {df.shape}")
    except Exception as e:
        print(f"❌ Failed to create DataFrame: {e}")
        return False

    # Filter for HTI
    hti_df = df[df['Series'].str.startswith('HTI')]
    
    print(f"\n🔍 HTI Symbol Analysis:")
    print(f"   Total records: {len(df)}")
    print(f"   HTI records: {len(hti_df)}")
    
    if not hti_df.empty:
        print("\n✅ HTI series found!")
        print("\n📊 HTI Settlement Records:")
        print("-" * 80)
        print(f"{'Series':<15} {'Expiry':<12} {'Strike':<8} {'Call/Put':<8} {'Settlement':<12} {'Volume':<8} {'OI':<8}")
        print("-" * 80)
        
        for _, row in hti_df.iterrows():
            print(f"{row['Series']:<15} {row['Expiry']:<12} {row['Strike']:<8} "
                  f"{row['Call/Put']:<8} {row['Settlement']:<12} "
                  f"{row['Volume']:<8} {row['OpenInterest']:<8}")
        
        print("\n📈 Summary:")
        print(f"   - HTI Call options: {len(hti_df[hti_df['Call/Put'] == 'Call'])}")
        print(f"   - HTI Put options: {len(hti_df[hti_df['Call/Put'] == 'Put'])}")
        print(f"   - Total HTI volume: {hti_df['Volume'].astype(int).sum()}")
        print(f"   - Total HTI open interest: {hti_df['OpenInterest'].astype(int).sum()}")
        
        return True
    else:
        print("\n❌ No HTI series found in sample data")
        print("\n🔍 Available symbols:")
        available_symbols = df['Series'].unique()
        for symbol in available_symbols:
            print(f"   - {symbol}")
        
        return False

def main():
    """Main function."""
    print("🚀 HKEX Settlement Price Parser - Sample Data Test")
    print("=" * 60)
    print(f"⏰ Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_with_sample_data()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed successfully! HTI symbol found in sample data.")
    else:
        print("⚠️  Test completed with issues. HTI symbol not found.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
