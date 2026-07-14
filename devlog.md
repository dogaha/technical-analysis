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
- Block the stuff
