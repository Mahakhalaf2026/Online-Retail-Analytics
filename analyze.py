import pandas as pd
import numpy as np
import json

df = pd.read_pickle('clean_data.pkl')
cancelled = pd.read_pickle('cancelled_data.pkl')

results = {}

# ---- 1. Yearly Avg/Min/Max ----
yearly = df.groupby('Year')['Sales'].agg(['mean','min','max','sum','count']).reset_index()
yearly.columns = ['Year','AvgSale','MinSale','MaxSale','TotalRevenue','TransactionLines']
results['yearly_stats'] = yearly.round(2).to_dict('records')

# ---- 2. Top-selling customers (exclude GUEST) ----
cust = df[df['Customer ID']!='GUEST'].groupby('Customer ID').agg(
    TotalRevenue=('Sales','sum'), Orders=('Invoice','nunique'), Items=('Quantity','sum')
).reset_index()
top_customers = cust.sort_values('TotalRevenue', ascending=False).head(15)
results['top_customers'] = top_customers.round(2).to_dict('records')

# ---- 3. Best/Worst performing months (by YearMonth to be precise across years) ----
monthly = df.groupby('YearMonth')['Sales'].sum().reset_index().sort_values('YearMonth')
results['monthly_revenue'] = monthly.round(2).to_dict('records')
best_months = monthly.sort_values('Sales', ascending=False).head(5)
worst_months = monthly.sort_values('Sales', ascending=True).head(5)
results['best_months'] = best_months.round(2).to_dict('records')
results['worst_months'] = worst_months.round(2).to_dict('records')

# Also aggregate by calendar month name (seasonality, across years)
month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
seasonality = df.groupby('MonthName')['Sales'].sum().reindex(month_order).reset_index()
results['seasonality'] = seasonality.round(2).to_dict('records')

# ---- 4. Best/Worst selling regions (Country) ----
region = df.groupby('Country').agg(TotalRevenue=('Sales','sum'), Orders=('Invoice','nunique')).reset_index()
best_regions = region.sort_values('TotalRevenue', ascending=False).head(10)
worst_regions = region[region['TotalRevenue']>0].sort_values('TotalRevenue', ascending=True).head(10)
results['best_regions'] = best_regions.round(2).to_dict('records')
results['worst_regions'] = worst_regions.round(2).to_dict('records')
results['all_regions'] = region.sort_values('TotalRevenue',ascending=False).round(2).to_dict('records')

# ---- 5. Top products ----
products = df.groupby(['StockCode','Description']).agg(
    TotalRevenue=('Sales','sum'), QtySold=('Quantity','sum')
).reset_index().sort_values('TotalRevenue', ascending=False).head(10)
results['top_products'] = products.round(2).to_dict('records')

# ---- 6. Pareto Analysis (80/20 rule) on customers ----
cust_sorted = cust.sort_values('TotalRevenue', ascending=False).reset_index(drop=True)
cust_sorted['CumRevenue'] = cust_sorted['TotalRevenue'].cumsum()
cust_sorted['CumPct'] = cust_sorted['CumRevenue'] / cust_sorted['TotalRevenue'].sum() * 100
cust_sorted['CustPct'] = (cust_sorted.index+1) / len(cust_sorted) * 100
pct_customers_80 = (cust_sorted['CumPct'] <= 80).sum() / len(cust_sorted) * 100
results['pareto_customers_pct_for_80pct_revenue'] = round(pct_customers_80,1)

# ---- 7. RFM Analysis (Recency, Frequency, Monetary) ----
snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
rfm = df[df['Customer ID']!='GUEST'].groupby('Customer ID').agg(
    Recency=('InvoiceDate', lambda x: (snapshot_date - x.max()).days),
    Frequency=('Invoice','nunique'),
    Monetary=('Sales','sum')
).reset_index()

r_labels = [4,3,2,1]; f_labels=[1,2,3,4]; m_labels=[1,2,3,4]
rfm['R'] = pd.qcut(rfm['Recency'], 4, labels=r_labels).astype(int)
rfm['F'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=f_labels).astype(int)
rfm['M'] = pd.qcut(rfm['Monetary'], 4, labels=m_labels).astype(int)
rfm['RFM_Score'] = rfm['R'] + rfm['F'] + rfm['M']

def segment(row):
    if row['RFM_Score'] >= 10: return 'Champions'
    elif row['RFM_Score'] >= 8: return 'Loyal Customers'
    elif row['RFM_Score'] >= 6: return 'Potential Loyalists'
    elif row['RFM_Score'] >= 4: return 'At Risk'
    else: return 'Lost/Hibernating'

rfm['Segment'] = rfm.apply(segment, axis=1)
seg_summary = rfm.groupby('Segment').agg(Customers=('Customer ID','count'), AvgMonetary=('Monetary','mean')).reset_index()
results['rfm_segments'] = seg_summary.round(2).to_dict('records')
rfm.to_pickle('rfm.pkl')

# ---- 8. Cohort Retention Analysis ----
cust_orders = df[df['Customer ID']!='GUEST'][['Customer ID','InvoiceDate']].copy()
cust_orders['OrderMonth'] = cust_orders['InvoiceDate'].dt.to_period('M')
cust_orders['CohortMonth'] = cust_orders.groupby('Customer ID')['InvoiceDate'].transform('min').dt.to_period('M')
cust_orders['CohortIndex'] = (cust_orders['OrderMonth'] - cust_orders['CohortMonth']).apply(lambda x: x.n)
cohort_data = cust_orders.groupby(['CohortMonth','CohortIndex'])['Customer ID'].nunique().reset_index()
cohort_pivot = cohort_data.pivot(index='CohortMonth', columns='CohortIndex', values='Customer ID')
cohort_size = cohort_pivot.iloc[:,0]
retention = cohort_pivot.divide(cohort_size, axis=0).round(3)
retention.index = retention.index.astype(str)
results['cohort_retention'] = retention.reset_index().fillna(0).round(3).to_dict('records')

# ---- 9. Weekday & Hour patterns ----
weekday_sales = df.groupby('Weekday')['Sales'].sum().reindex(
    ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).reset_index()
results['weekday_sales'] = weekday_sales.round(2).to_dict('records')

hour_sales = df.groupby('Hour')['Sales'].sum().reset_index()
results['hour_sales'] = hour_sales.round(2).to_dict('records')

# ---- 10. YoY Growth ----
yoy = yearly[['Year','TotalRevenue']].copy()
yoy['YoY_Growth_%'] = yoy['TotalRevenue'].pct_change()*100
results['yoy_growth'] = yoy.round(2).to_dict('records')

# ---- 11. Return / Cancellation impact ----
results['cancellation_summary'] = {
    'cancelled_transaction_lines': len(cancelled),
    'cancelled_value_estimate': round(float((cancelled['Quantity']*cancelled['Price']).sum()),2),
}

# ---- 12. Overall KPIs ----
results['kpis'] = {
    'total_revenue': round(float(df['Sales'].sum()),2),
    'total_orders': int(df['Invoice'].nunique()),
    'total_customers': int(df[df['Customer ID']!='GUEST']['Customer ID'].nunique()),
    'total_countries': int(df['Country'].nunique()),
    'avg_order_value': round(float(df.groupby('Invoice')['Sales'].sum().mean()),2),
    'date_range': f"{df['InvoiceDate'].min().date()} to {df['InvoiceDate'].max().date()}",
    'total_products': int(df['StockCode'].nunique()),
}

with open('analysis_results.json','w') as f:
    json.dump(results, f, indent=2, default=str)

print("KPIs:", results['kpis'])
print("Yearly:", results['yearly_stats'])
print("Pareto:", results['pareto_customers_pct_for_80pct_revenue'], "% of customers = 80% revenue")
print("RFM segments:", results['rfm_segments'])
