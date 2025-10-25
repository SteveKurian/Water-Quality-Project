import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats  
from .db import get_collection

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEAN = ROOT / "data" / "cleaned"

NUMERIC_HINTS = {
    "temperature": ["temperature", "temp c", "temp", "temperature (c)", "temperature c"],
    "salinity": ["salinity", "sal", "salinity (ppt)","salinity (ppt) "],
    "odo": ["odo", "odo mg/l", "odo mg/l ", "odo mg/l%", "odo mg/l% ", "odo mg/l (%)"]
}

def _find_timestamp(df: pd.DataFrame) -> pd.Series:
    for col in df.columns:
        lc = str(col).strip().lower()
        if lc in {"timestamp", "time_utc", "datetime", "date_time"}:
            return pd.to_datetime(df[col], errors="coerce", utc=True)
    
    date_cols = [c for c in df.columns if "date" in str(c).lower()]
    time_cols = [c for c in df.columns if "time" in str(c).lower()]

    if date_cols and time_cols:
        date_col = date_cols[0]
        time_col = time_cols[0]
        combo = df[date_col].astype(str).str.strip() + " " + df[time_col].astype(str).str.strip()
        return pd.to_datetime(combo, errors="coerce", utc=True, infer_datetime_format=True)
    
    for c in df.columns:
        if "time" in str(c).lower():
            return pd.to_datetime(df[c], errors="coerce", utc=True, infer_datetime_format=True)
    
    return pd.to_datetime(pd.Series(range(len(df))), unit="s", utc=True)

def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    
    df = df.rename(columns=lambda c: str(c).strip().lower())

    
    df["timestamp"] = _find_timestamp(df)

    def first_present(candidates: list[str]) -> str | None:
        for name in candidates:
            if name in df.columns:
                return name
        return None

    src_for = {
        "temperature": first_present(NUMERIC_HINTS["temperature"]),
        "salinity":    first_present(NUMERIC_HINTS["salinity"]),
        "odo":         first_present(NUMERIC_HINTS["odo"]),
    }

    for canonical, source in src_for.items():
        if source and canonical not in df.columns:
            df[canonical] = pd.to_numeric(df[source], errors="coerce")

    obj_cols = [c for c in df.select_dtypes(include=["object"]).columns if c != "timestamp"]
    if obj_cols:
        df[obj_cols] = df[obj_cols].apply(lambda s: pd.to_numeric(s, errors="ignore"))

    return df

def _zscore_clean(df: pd.DataFrame, numeric_cols: list[str], z_thresh: float = 3.0) -> pd.DataFrame:
    
    z = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std(ddof=0)
    mask = (z.abs() <= z_thresh) | z.isna()  
    keep = mask.all(axis=1)
    return df[keep].copy()

def load_and_clean():
    DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    all_paths = sorted(DATA_RAW.glob("*.csv"))
    if not all_paths:
        print(f"No CSVs found in {DATA_RAW}")
        return

    raw_count = 0
    removed = 0
    kept = 0

    cleaned_frames = []

    for path in all_paths:
        df = pd.read_csv(path, low_memory=False)
        df = _standardize_columns(df)

    
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        core_cols = [c for c in ["temperature", "salinity", "odo"] if c in df.columns]
        numeric_cols = list(sorted(set(numeric_cols + core_cols)))
        before = len(df)
        raw_count += before

        df = df[df["timestamp"].notna()]

        if numeric_cols:
            df_clean = _zscore_clean(df, numeric_cols, z_thresh=3.0)
        else:
            df_clean = df.copy()

        after = len(df_clean)
        removed += (before - after)
        kept += after

        out_path = DATA_CLEAN / f"cleaned_{path.name}"
        df_clean.to_csv(out_path, index=False)
        cleaned_frames.append(df_clean)

    if cleaned_frames:
        all_clean = pd.concat(cleaned_frames, ignore_index=True)
        all_clean.to_csv(DATA_CLEAN / "cleaned_all.csv", index=False)

        coll = get_collection()
        coll.drop()
        
        coll.create_index("timestamp")

        records = all_clean.to_dict(orient="records")
        for r in records:
            if isinstance(r.get("timestamp"), pd.Timestamp):
                r["timestamp"] = r["timestamp"].isoformat()

        if records:
            coll.insert_many(records)

    print("=== Cleaning Report ===")
    print(f"Total rows originally: {raw_count}")
    print(f"Rows removed as outliers: {removed}")
    print(f"Rows remaining after cleaning: {kept}")

if __name__ == "__main__":
    load_and_clean()
