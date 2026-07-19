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

## 2025-07-17

### Decisions Made
- Inefficient to limit the ML model, let it do it's thing
- No longer use ATR for swing detector


### What I worked on
- Reworked the get swing function in utils
  - added following price vs fighting price movememnt column. 
  lets me see ho much it moves with/against the trend
  - Redid format of code to follow three cases:  Open, Continuation, Reversal
  - Fixed bugs with pivots
- Made utils functions even more general
  - renamed some functions
  - added optional parameters to some functions
- Made all Notebooks Compatible with functions
- Dropped IQR for winsorized for outlier handling

### TO-DO
- Study up on ML
- Prepare for what is next
- write down conclusions drawn from notebooks

---

## 2025-07-18

### Decisons
- Add Swings to gold layer
- Study up on ML Concepts
  - Supervised Learning
  - Train / Test Splits
  - Random Forest / Logistical Regression
  - Evaluation Metrics
  - Overfitting
  - Feature Scaling
- Extend Chart Usage To observe (8:00 - 8:30) and trade [8:30 - 9:30]
  - Look into other time frames later
- Gather all the necessary swing data so that the model can base decisions on
  - Volume
  - Time of Day
  - ATR
  - swing_efficiency
  - previous_swing(s)
  - VWAP
  - Session Data
    - High
    - Low
    - Open

### What I worked on
- Nothing






