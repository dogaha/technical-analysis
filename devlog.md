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
- Cleaned target/ out of git tracking

### Decisions
- Fixed via pre_hook: SET timezone = 'UTC'; instead of profiles.yml
  (profiles.yml has no timezone/session_properties key for postgres adapter)