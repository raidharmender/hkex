#!/usr/bin/env python3
"""
Test script to verify the original code and check for HTI symbol in August 22, 2023 data.
"""

import requests
from io import StringIO
import pandas as pd
from datetime import datetime
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_original_code():
    """Test the original code and check for HTI symbol."""
    print("🔍 Testing original code and checking for HTI symbol...")
    print("=" * 60)
    
    # 1. Download the file
    url = 'https://hkex.com/hk/eng/stat/dmstat/datadownload/sp250822.dat'
    print(f"📥 Downloading from: {url}")
    
    try:
        # Try with SSL verification disabled
        resp = requests.get(url, verify=False, timeout=30)
        resp.raise_for_status()
        print("✅ File downloaded successfully")
    except requests.RequestException as e:
        print(f"❌ Failed to download file: {e}")
        print("🔄 Trying alternative approach...")
        
        # Try with different headers
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            resp = requests.get(url, verify=False, headers=headers, timeout=30)
            resp.raise_for_status()
            print("✅ File downloaded successfully with custom headers")
        except requests.RequestException as e2:
            print(f"❌ Still failed: {e2}")
            return False

    # 2. Split into lines and find the header index
    lines = resp.text.splitlines()
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

    # 3. Extract column names and data rows
    columns = lines[header_idx].split()
    data_rows = [ln.split() for ln in lines[header_idx+1:] if ln.strip()]
    
    print(f"📊 Found {len(data_rows)} data rows")
    print(f"📋 Columns: {columns}")

    # 4. Build DataFrame
    try:
        df = pd.DataFrame(data_rows, columns=columns)
        print(f"✅ DataFrame created with shape: {df.shape}")
    except Exception as e:
        print(f"❌ Failed to create DataFrame: {e}")
        return False

    # 5. Filter for HTI
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
                  f"{row['Volume']:<8} {row['Open Interest']:<8}")
        
        print("\n📈 Summary:")
        print(f"   - HTI Call options: {len(hti_df[hti_df['Call/Put'] == 'Call'])}")
        print(f"   - HTI Put options: {len(hti_df[hti_df['Call/Put'] == 'Put'])}")
        print(f"   - Total HTI volume: {hti_df['Volume'].astype(int).sum()}")
        print(f"   - Total HTI open interest: {hti_df['Open Interest'].astype(int).sum()}")
        
        return True
    else:
        print("\n❌ No HTI series found in sp250822.dat")
        print("\n🔍 Available symbols (first 10):")
        available_symbols = df['Series'].unique()[:10]
        for symbol in available_symbols:
            print(f"   - {symbol}")
        
        return False

def main():
    """Main function."""
    print("🚀 HKEX Settlement Price Parser - Original Code Test")
    print("=" * 60)
    print(f"⏰ Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_original_code()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed successfully! HTI symbol found.")
    else:
        print("⚠️  Test completed with issues. HTI symbol not found.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
