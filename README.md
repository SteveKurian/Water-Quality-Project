# Water Quality Data Service

Water Quality Data Service (CSV → Cleaning → DB → API → Client)

The Water Quality Data Project is a full data pipeline that processes and visualizes water quality observations. It starts by loading raw CSV files, cleaning the data to eliminate outliers, and storing the cleaned dataset in a NoSQL database (MongoDB or mongomock). A Flask REST API is built to provide access to the data through endpoints that support filtering, statistics, and outlier detection. The project also includes a Streamlit client that communicates with the API to display tables, summary statistics, and interactive Plotly visualizations.

---

## Features
- Loads and cleans raw environmental water quality data
- Detects and removes outliers to improve data quality
- Stores cleaned data in MongoDB or an in-memory mock database
- REST API provides filtered access to dataset
- Interactive Streamlit dashboard for visualization and analysis
- Summary statistics, tables, and Plotly-based graphs for insights

---

## Tech Stack:
Python • Flask • Pandas • MongoDB • Matplotlib • HTML/CSS • JavaScript

---

### Quick Start

```bash
# 0) (Optional) create & activate a virtualenv for Python 3.10+
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# 1) Install dependencies
pip install -r requirements.txt

# 2) Put raw CSVs into data/raw/ 

# 3) Run cleaning + load into DB (Mongo if MONGO_URL is set, else in-memory mongomock)
python -m api.cleaning

# 4) Start the API
python -m api.app

# 5) In another terminal, start the Streamlit client
streamlit run client/app.py
```

## Switching between MongoDB and mongomock
- **MongoDB**: set `MONGO_URL` (e.g., `mongodb://localhost:27017`)
- **mongomock** (default): do nothing; the app will use an in-memory DB for quick dev.

## API (Flask)

- `GET /api/health` → `{ "status": "ok" }`

## Project Layout

```
water-quality-pipeline/
├─ data/
│  ├─ raw/        
│  └─ cleaned/    
├─ api/
│  ├─ app.py      
│  ├─ cleaning.py
│  └─ db.py       
└─ client/
   └─ app.py      
```

---

## Demo Video
Here is a quick demo showing how our Water Quality Analysis Dashboard works:

[Demo Video](https://drive.google.com/file/d/1dARl9_XCVIQNGW3l2x_Y2Iqq0aU6EU0U/view?usp=sharing)

---

## Future Enhancements
- Integrate live data streaming from real-time water sensors
- Add machine learning to predict contamination risk
- Deploy API and dashboard online using Docker + Render/Heroku

---

## Use Case
This project can be used by environmental researchers, public health officials, and city planners to:
- Monitor water quality across regions
- Detect unusual contamination patterns
- Support clean water policy decisions

---

## Contributors

This project was made in collaboration with the following for the class CIS3590 - Internship Ready Software Development:
- Shatoya Gardner  
- Shirina Shaji Daniel
- Steve Kurian

---
