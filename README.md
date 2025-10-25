# Water Quality Data Service (CSV → Cleaning → DB → API → Client)

A small end‑to‑end pipeline built like a junior CS project:
CSV ➜ cleaning (z‑score) ➜ MongoDB/mongomock ➜ Flask REST API ➜ Streamlit client with Plotly charts.

## Quick Start

```bash
# 0) (Optional) create & activate a virtualenv for Python 3.10+
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# 1) Install deps
pip install -r requirements.txt

# 2) Put raw CSVs into data/raw/ 

# 3) Run cleaning + load into DB (Mongo if MONGO_URL is set, else in-memory mongomock)
python -m api.cleaning

# 4) Start the API
python -m api.app

# 5) In another terminal, start the Streamlit client
streamlit run client/app.py
```

### Switching between MongoDB and mongomock
- **MongoDB**: set `MONGO_URL` (e.g., `mongodb://localhost:27017`)
- **mongomock** (default): do nothing; the app will use an in-memory DB for quick dev.

## API (Flask)

- `GET /api/health` → `{ "status": "ok" }`
- `GET /api/observations` with optional query params:
  - `start`, `end`: ISO timestamps (e.g., `2021-10-21T13:45:00`)
  - `min_temp`, `max_temp`, `min_sal`, `max_sal`, `min_odo`, `max_odo`
  - `limit` (default 100, max 1000), `skip`
- `GET /api/stats` → summary stats for temperature, salinity, odo.
- `GET /api/outliers?field=temperature&method=iqr&k=1.5`

## Project Layout

```
water-quality-pipeline/
├─ data/
│  ├─ raw/        # put your CSVs here
│  └─ cleaned/    # cleaned CSVs are written here
├─ api/
│  ├─ app.py      # Flask REST API
│  ├─ cleaning.py # ETL: read CSVs, z-score clean, insert into DB
│  └─ db.py       # tiny DB helper (Mongo or mongomock)
└─ client/
   └─ app.py      # Streamlit UI
```

## Notes

- The cleaner auto-detects numeric columns and looks for timestamp columns.
- If your CSVs have separate `Date` and `Time` columns, the cleaner tries to combine them.
- Z‑score outlier rule: drop any row where **any numeric field** has |z| > 3.
