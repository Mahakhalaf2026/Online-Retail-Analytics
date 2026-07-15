import pandas as pd
import numpy as np

print("Loading data...")
df = pd.read_csv('/mnt/user-data/uploads/online_retail_II.csv', dtype={'Customer ID': 'str'})
print("Raw shape:", df.shape)

report = {}
report['raw_rows'] = len(df)

# 1. Strip whitespace from text columns
for col in ['Description', 'Country', 'StockCode', 'Invoice']:
    df[col] = df[col].astype(str).str.strip()

# 2. Parse date
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

# 3. Flag cancellations (Invoice starting with 'C')
df['IsCancelled'] = df['Invoice'].str.startswith('C')
report['cancelled_rows'] = int(df['IsCancelled'].sum())

# 4. Remove exact duplicate rows
before = len(df)
df = df.drop_duplicates()
report['exact_duplicates_removed'] = before - len(df)

# 5. Remove cancelled transactions (returns) - keep separately for return analysis
cancelled_df = df[df['IsCancelled']].copy()
df_clean = df[~df['IsCancelled']].copy()

# 6. Remove non-positive quantity or price (bad/test data) in the clean set
before = len(df_clean)
df_clean = df_clean[(df_clean['Quantity'] > 0) & (df_clean['Price'] > 0)]
report['non_positive_removed'] = before - len(df_clean)

# 7. Remove known test/adjustment stock codes
test_codes = ['TEST001','TEST002','POST','D','M','BANK CHARGES','PADS','DOT','CRUK']
before = len(df_clean)
df_clean = df_clean[~df_clean['StockCode'].str.upper().isin(test_codes)]
report['test_codes_removed'] = before - len(df_clean)

# 8. Handle missing Customer ID -> keep but flag as 'Guest' for revenue analysis, exclude from customer-level analysis
report['missing_customer_id'] = int(df_clean['Customer ID'].isna().sum())
df_clean['Customer ID'] = df_clean['Customer ID'].fillna('GUEST')

# 9. Handle missing Description
report['missing_description'] = int(df_clean['Description'].isna().sum())
df_clean['Description'] = df_clean['Description'].replace('nan', np.nan)
df_clean['Description'] = df_clean['Description'].fillna('UNKNOWN ITEM')

# 10. Add derived columns
df_clean['Sales'] = df_clean['Quantity'] * df_clean['Price']
df_clean['Year'] = df_clean['InvoiceDate'].dt.year
df_clean['Month'] = df_clean['InvoiceDate'].dt.month
df_clean['MonthName'] = df_clean['InvoiceDate'].dt.strftime('%b')
df_clean['YearMonth'] = df_clean['InvoiceDate'].dt.to_period('M').astype(str)
df_clean['Weekday'] = df_clean['InvoiceDate'].dt.day_name()
df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour
df_clean['Quarter'] = df_clean['InvoiceDate'].dt.quarter

# 11. Outlier detection on Sales (IQR method) - flag, don't necessarily remove
Q1 = df_clean['Sales'].quantile(0.25)
Q3 = df_clean['Sales'].quantile(0.75)
IQR = Q3 - Q1
upper = Q3 + 3*IQR  # use 3x for extreme outliers only
df_clean['IsOutlier'] = df_clean['Sales'] > upper
report['extreme_outliers_flagged'] = int(df_clean['IsOutlier'].sum())

report['final_clean_rows'] = len(df_clean)
report['final_columns'] = list(df_clean.columns)

print(report)
df_clean.to_pickle('/home/claude/work/clean_data.pkl')
cancelled_df.to_pickle('/home/claude/work/cancelled_data.pkl')

import json
with open('/home/claude/work/cleaning_report.json','w') as f:
    json.dump(report, f, indent=2, default=str)
