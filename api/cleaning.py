import os
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
import json
from db import get_db_client

DATA_RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
DATA_CLEAN = Path(__file__).resolve().parents[1] / "data" / "cleaned"
DATA_CLEAN.mkdir(parents=True, exist_ok=True)

NUMERIC_FIELDS = ["temperature", "salinity", "odo"]  # adapt to your CSV column names

def load_csvs(raw_dir=DATA_RAW):
    files = sorted(raw_dir.glob("*.csv"))
    dfs = []
    for f in files:
        df = pd.read_csv(f, parse_dates=True, infer_datetime_format=True)
        # normalize timestamp column name if possible
        if "timestamp" not in df.columns:
            for candidate in ["Time", "Date", "Date Time", "date", "time", "Time hh:mm:ss"]:
                if candidate in df.columns:
                    df["timestamp"] = pd.to_datetime(df[candidate], errors="coerce")
                    break
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def clean_zscore(df, numeric_fields=NUMERIC_FIELDS, z_thresh=3.0):
    df2 = df.copy()
    # coerce numeric
    for col in numeric_fields:
        if col in df2.columns:
            df2[col] = pd.to_numeric(df2[col], errors="coerce")
    # compute z-scores column-wise ignoring NaNs
    z = np.abs(stats.zscore(df2[numeric_fields], nan_policy="omit", axis=0))
    # if a column was missing from df, stats.zscore will not have it; safe guard:
    # z is ndarray shaped (n_rows, n_numeric_present)
    # build boolean mask: keep rows where all present z <= threshold or nan
    # create mask per column
    mask = np.ones(len(df2), dtype=bool)
    numeric_present = [c for c in numeric_fields if c in df2.columns]
    if numeric_present:
        z_df = pd.DataFrame(z, columns=numeric_present, index=df2.index)
        # treat NaN z as False (do not mark as outlier)
        mask &= ~(z_df > z_thresh).any(axis=1).fillna(False).values
    removed = (~mask).sum()
    return df2[mask].reset_index(drop=True), int(removed), int(len(df2))

def insert_to_db(df, db_name="water_quality_data", coll_name="asv_1", index_field="timestamp"):
    client = get_db_client()
    db = client[db_name]
    coll = db[coll_name]
    # ensure timestamp saved as ISO string or datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    docs = df.to_dict(orient="records")
    if docs:
        coll.insert_many(docs)
    # optional: create index
    try:
        coll.create_index([(index_field, 1)])
    except Exception:
        pass
    return len(docs)

def main():
    df = load_csvs()
    if df.empty:
        print("No CSVs found in", DATA_RAW)
        return
    cleaned, removed, original = clean_zscore(df)
    print(f"Original rows: {original}")
    print(f"Removed (outliers): {removed}")
    print(f"Remaining: {len(cleaned)}")
    # write cleaned CSV
    out_path = DATA_CLEAN / f"cleaned_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    cleaned.to_csv(out_path, index=False)
    # insert into db
    inserted = insert_to_db(cleaned)
    print(f"Inserted {inserted} rows into DB")

if __name__ == "__main__":
    main()
