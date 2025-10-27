import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
load_dotenv()


st.set_page_config(page_title="Water Quality Client", layout="wide")

API_BASE = os.environ.get("API_BASE", "http://localhost:5000")

st.title("Water Quality")

with st.sidebar:
    st.header("Filters")
    start = st.text_input("Start (ISO)", value="")
    end = st.text_input("End (ISO)", value="")
    min_temp = st.number_input("Min temperature", value=float("nan"))
    max_temp = st.number_input("Max temperature", value=float("nan"))
    min_sal = st.number_input("Min salinity", value=float("nan"))
    max_sal = st.number_input("Max salinity", value=float("nan"))
    min_odo = st.number_input("Min ODO", value=float("nan"))
    max_odo = st.number_input("Max ODO", value=float("nan"))
    limit = st.slider("Limit", 10, 1000, 200, 10)
    skip = st.number_input("Skip (pagination)", min_value=0, value=0, step=50)

    def _param(v):
        return None if (isinstance(v, float) and pd.isna(v)) or v == "" else v

    params = {
        "start": _param(start),
        "end": _param(end),
        "min_temp": _param(min_temp),
        "max_temp": _param(max_temp),
        "min_sal": _param(min_sal),
        "max_sal": _param(max_sal),
        "min_odo": _param(min_odo),
        "max_odo": _param(max_odo),
        "limit": limit,
        "skip": skip,
    }
    st.caption("Leave fields blank for no filter.")

tabs = st.tabs(["Data", "Visualizations", "Statistics", "Outliers"])

with tabs[0]:
    st.subheader("Observations")
    try:
        resp = requests.get(f"{API_BASE}/api/observations", params={k:v for k,v in params.items() if v is not None}, timeout=20)
        data = resp.json()
        st.write(f"Count: **{data.get('count', 0)}**")
        items = data.get("items", [])
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data returned for the selected filters.")
    except Exception as e:
        st.error(f"Failed to load observations: {e}")

with tabs[1]:
    st.subheader("Charts")
    if 'df' in locals() and not df.empty:
        if "timestamp" in df.columns:
            df["_ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
        else:
            df["_ts"] = pd.NaT

        cols = df.columns

        if "temperature" in cols and "_ts" in cols:
            line_fig = px.line(df.sort_values("_ts"), x="_ts", y="temperature", title="Temperature over time")
            st.plotly_chart(line_fig, use_container_width=True)

        if "salinity" in cols:
            hist_fig = px.histogram(df, x="salinity", nbins=50, title="Salinity distribution")
            st.plotly_chart(hist_fig, use_container_width=True)

        if "temperature" in cols and "salinity" in cols:
            color_col = "odo" if "odo" in cols else None
            scat_fig = px.scatter(df, x="temperature", y="salinity", color=color_col, title="Temperature vs Salinity (color=ODO)")
            st.plotly_chart(scat_fig, use_container_width=True)

        lat_candidates = [c for c in cols if "lat" in c.lower()]
        lon_candidates = [c for c in cols if "lon" in c.lower() or "long" in c.lower()]
        if lat_candidates and lon_candidates:
            lat_c = lat_candidates[0]
            lon_c = lon_candidates[0]
            map_df = df[[lat_c, lon_c]].dropna()
            if not map_df.empty:
                st.map(map_df.rename(columns={lat_c:"latitude", lon_c:"longitude"}))
    else:
        st.info("Load data in the Data tab to unlock charts.")

with tabs[2]:
    st.subheader("Summary Statistics")
    try:
        s = requests.get(f"{API_BASE}/api/stats", timeout=20).json()
        if s:
            st.json(s)
        else:
            st.info("No stats available yet.")
    except Exception as e:
        st.error(f"Failed to load stats: {e}")

with tabs[3]:
    st.subheader("Outliers")
    field = st.selectbox("Field", ["temperature", "salinity", "odo"], index=0)
    method = st.selectbox("Method", ["iqr", "z"], index=0)
    k = st.number_input("k (IQR multiplier or z-threshold)", value=1.5)
    try:
        out = requests.get(f"{API_BASE}/api/outliers", params={"field": field, "method": method, "k": k}, timeout=20).json()
        st.write(f"Flagged count: **{out.get('count', 0)}**")
        items = out.get("items", [])
        if items:
            st.dataframe(pd.DataFrame(items), use_container_width=True)
        else:
            st.info("No outliers found with the current settings.")
    except Exception as e:
        st.error(f"Failed to load outliers: {e}")
