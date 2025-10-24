import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

API_BASE = st.secrets.get("api_base", "http://localhost:5000/api")

st.set_page_config(layout="wide", page_title="Water Quality Client")

st.sidebar.header("Filters")
start = st.sidebar.date_input("Start date", datetime.utcnow().date() - timedelta(days=7))
end = st.sidebar.date_input("End date", datetime.utcnow().date())
min_temp = st.sidebar.number_input("Min temp", value=float(-10.0))
max_temp = st.sidebar.number_input("Max temp", value=float(50.0))
min_sal = st.sidebar.number_input("Min salinity", value=float(0.0))
max_sal = st.sidebar.number_input("Max salinity", value=float(50.0))
limit = st.sidebar.slider("Limit", 10, 1000, 200)
skip = st.sidebar.number_input("Skip", 0)

if st.sidebar.button("Fetch"):
    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "min_temp": min_temp,
        "max_temp": max_temp,
        "min_sal": min_sal,
        "max_sal": max_sal,
        "limit": limit,
        "skip": skip
    }
    resp = requests.get(f"{API_BASE}/observations", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    if not items:
        st.warning("No observations returned")
    else:
        df = pd.DataFrame(items)
        st.subheader("Observations")
        st.dataframe(df)
        # ensure timestamp column
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.sort_values("timestamp")
        # Line chart temperature over time
        if "temperature" in df.columns:
            fig1 = px.line(df, x="timestamp", y="temperature", title="Temperature over time")
            st.plotly_chart(fig1, use_container_width=True)
        # Histogram salinity
        if "salinity" in df.columns:
            fig2 = px.histogram(df, x="salinity", nbins=40, title="Salinity distribution")
            st.plotly_chart(fig2, use_container_width=True)
        # Scatter temp vs salinity color by odo
        if {"temperature","salinity","odo"}.issubset(df.columns):
            fig3 = px.scatter(df, x="temperature", y="salinity", color="odo",
                              title="Temperature vs Salinity colored by ODO", hover_data=["timestamp"])
            st.plotly_chart(fig3, use_container_width=True)
        # Map if lat/lon present
        if {"latitude","longitude"}.issubset(df.columns):
            st.subheader("Map")
            st.map(df.rename(columns={"latitude":"lat","longitude":"lon"})[["lat","lon"]].dropna())
        # stats panel
        st.subheader("Stats")
        stats_resp = requests.get(f"{API_BASE}/stats", timeout=10).json()
        st.json(stats_resp)
        # outliers
        st.subheader("Outliers (temperature)")
        out_resp = requests.get(f"{API_BASE}/outliers", params={"field":"temperature","method":"zscore","k":3}, timeout=10).json()
        st.write(f"{out_resp.get('count',0)} flagged")
        st.dataframe(pd.DataFrame(out_resp.get("items", [])))
