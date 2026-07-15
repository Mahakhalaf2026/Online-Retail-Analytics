# Online Retail II — Sales Performance & Customer Analytics

End-to-end data analyst project: cleaning, exploratory analysis, customer segmentation, and an interactive dashboard, built on the [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) dataset (1,067,371 raw transaction lines, a UK-based online retailer, Dec 2009–Dec 2011).

**[View the live dashboard](./index.html)** · **[Download the Excel workbook](./Online_Retail_Analysis.xlsx)**

## What this project demonstrates

- Data cleaning at scale (1M+ rows) with a documented, reproducible methodology
- KPI reporting (yearly avg/min/max, revenue, AOV)
- Customer segmentation with **RFM analysis** (Recency, Frequency, Monetary)
- **Pareto (80/20) analysis** of revenue concentration
- **Cohort retention analysis** — how long customers keep buying after their first order
- Seasonality and time-of-day/day-of-week behavior analysis
- A dark-themed, recruiter-ready interactive dashboard (HTML + Chart.js, no build step, deployable straight to GitHub Pages)

## Repo structure

```
├── index.html                  # Interactive dashboard (open directly, or deploy via GitHub Pages)
├── Online_Retail_Analysis.xlsx # Excel workbook: KPIs, yearly stats, charts, all built with live formulas
├── scripts/
│   ├── clean_data.py           # Cleaning pipeline (pandas)
│   └── analyze.py              # All analysis: RFM, cohorts, Pareto, seasonality, etc.
└── data/
    ├── cleaning_report.json         # Row-level audit trail of every cleaning step
    ├── analysis_results.json        # All computed analysis outputs (feeds the dashboard)
    └── online_retail_cleaned_sample.csv  # 20k-row sample of the cleaned dataset
```

> **Note on the full cleaned dataset:** the full cleaned file is ~1M rows (~136MB), over GitHub's comfortable file-size limit, so only a 20k-row sample is committed here. Get the full raw dataset from the [UCI repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii) and run `scripts/clean_data.py` to reproduce the complete cleaned file locally, or use [Git LFS](https://git-lfs.com/) if you want the full file in the repo.

## Data cleaning methodology

| Step | Rows affected |
|---|---|
| Raw rows loaded | 1,067,371 |
| Exact duplicate rows removed | 34,335 |
| Cancelled/returned transactions separated out (kept, not deleted) | 19,494 |
| Non-positive quantity or price removed (data entry errors) | 6,019 |
| Test/adjustment stock codes removed (postage, bank charges, etc.) | 4,183 |
| Missing Customer IDs labeled `GUEST` (kept for revenue, excluded from customer analysis) | 226,868 |
| Extreme outliers flagged (>3× IQR, kept but flagged for review, not removed) | 52,247 |
| **Final analysis-ready rows** | **1,003,730** |

Cancellations were separated rather than discarded so they remain available for a dedicated returns-analysis extension. Outliers were flagged, not deleted, since large wholesale orders are legitimate in this dataset — deleting them would understate true revenue.

## Key findings

- **Revenue concentration**: only ~23% of customers generate 80% of total revenue (Pareto analysis)
- **Seasonality**: revenue climbs sharply from September into a November peak, consistent with holiday demand
- **Geography**: the UK dominates by a wide margin; a small set of European markets form a meaningful long tail
- **Shopping behavior**: purchases concentrate on weekdays, late morning to early afternoon — consistent with B2B-influenced buying
- **Retention**: cohort analysis shows meaningful drop-off after month 1, with a "warm" segment of repeat buyers stabilizing around 15–25% of each cohort in later months

## Ideas for extending this project further

If you want to push this even further for your portfolio:

1. **Market basket analysis** (association rules / Apriori) — "customers who bought X also bought Y," useful for cross-sell recommendations
2. **Customer lifetime value (CLV) modeling** — predictive, not just historical, using a BG/NBD or Gamma-Gamma model
3. **Time series forecasting** — Prophet or ARIMA on monthly revenue to forecast the next 3–6 months
4. **Anomaly detection** — flag unusual spikes/drops in daily revenue automatically (e.g., Isolation Forest)
5. **A geographic choropleth map** instead of a bar chart for the regional breakdown
6. **Returns analysis** — the cancelled-transactions data is preserved separately; a follow-up notebook could quantify return rate by product/customer
7. **Deploy the dashboard properly** — push this repo to GitHub, enable GitHub Pages (Settings → Pages → deploy from `main` branch), and link the live URL from your CV instead of the raw file

## Tech stack

Python (pandas, openpyxl) · Chart.js · HTML/CSS/JS (no framework, no build step — works as a static GitHub Pages site)

## Source

Chen, D. (2019). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D
