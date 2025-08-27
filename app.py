import requests
from io import StringIO
import pandas as pd

# 1. Download the file
url = 'https://hkex.com/hk/eng/stat/dmstat/datadownload/sp250822.dat'
resp = requests.get(url)
resp.raise_for_status()

# 2. Split into lines and find the header index
lines = resp.text.splitlines()
header_idx = next(
    i for i, line in enumerate(lines) if line.strip().startswith('Series')
)

# 3. Extract column names and data rows
columns = lines[header_idx].split()
data_rows = [ln.split() for ln in lines[header_idx+1:] if ln.strip()]

# 4. Build DataFrame
df = pd.DataFrame(data_rows, columns=columns)

# 5. Filter for HTI
hti_df = df[df['Series'].str.startswith('HTI')]

# 6. Output result
if not hti_df.empty:
    print("HTI series found:")
    print(hti_df.to_string(index=False))
else:
    print("No HTI series in sp250822.dat.")
