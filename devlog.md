# Dev Journal

## Pre-Log

### Tech Stack
- DBT
- AIRFLOW
- PYTHON
- JUPYTER NOTEBOOKS
- POSTGRES
- DOCKER

### What Has Been Done
- Pipeline for manual bulk ingestion of NinjaTrader Historical Data
- Analysis of Cleaned Data

---

## 2025-07-13

### What I worked on
- Started devlog
- Fixed timezone bug in silver layer bar_time conversion
  - Fixed via pre_hook: SET timezone = 'UTC'; instead of profiles.yml
  (profiles.yml has no timezone/session_properties key for postgres adapter)
- Cleaned target/ out of git tracking

---

## 2025-07-14

### What I worked on
- Implemented NYSE OPEN Market Days Filter
  - pandas_market_dates => CSV
  - Seed CSV
  - stage cme_data
  - use inner join to filter out the dates not present
- Updated Analysis ot work with Filter

### TO-DO
- Decide a daily time range to trade
- Analyze said time range

---

## 2025-07-15

### What I worked on
- Made Notebooks cleaner, added and implemented functions to and from utils
onto the notebooks
- Decided on 8:30 and 9:30 Time Frame
- Began analysis on Time Range

### TO-DO
- Implement ATR into the swing detector
- Finish Analysis on Time range
  - profits to target
  - stop loss
  - volumes to trade
