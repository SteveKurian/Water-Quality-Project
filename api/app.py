from flask import Flask, request, jsonify
from datetime import datetime
import pandas as pd
from bson import ObjectId
from .db import get_collection
from dotenv import load_dotenv
load_dotenv()


def _iso_or_none(ts):
    return ts.isoformat() if ts is not None else None

def _compact(d: dict):
    out = {k: v for k, v in d.items() if v is not None}
    return {k: v for k, v in out.items() if not (isinstance(v, dict) and len(v) == 0)}

def _range_query(low, high):
    return _compact({"$gte": low, "$lte": high})

def _time_query(start_ts, end_ts):
    return _compact({"$gte": _iso_or_none(start_ts), "$lte": _iso_or_none(end_ts)})

app = Flask(__name__)

def _parse_float(name):
    v = request.args.get(name)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None

def _parse_int(name, default=None, cap=None):
    v = request.args.get(name)
    if v is None or v == "":
        return default
    try:
        iv = int(v)
        if cap is not None:
            iv = min(iv, cap)
        return iv
    except Exception:
        return default

def _parse_iso(name):
    v = request.args.get(name)
    if not v:
        return None
    try:
        return pd.to_datetime(v, utc=True)
    except Exception:
        return None

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/api/observations")
def observations():
    coll = get_collection()

    
    t_query = _time_query(_parse_iso("start"), _parse_iso("end"))
    query = {"timestamp": t_query} if t_query else {}

    
    range_specs = {
        "temperature": (_parse_float("min_temp"), _parse_float("max_temp")),
        "salinity":    (_parse_float("min_sal"),  _parse_float("max_sal")),
        "odo":         (_parse_float("min_odo"),  _parse_float("max_odo")),
    }
    numeric_filters = {
        field: _range_query(lo, hi)
        for field, (lo, hi) in range_specs.items()
    }
    query.update({k: v for k, v in numeric_filters.items() if v})

    limit = _parse_int("limit", default=100, cap=1000)
    skip = _parse_int("skip", default=0)

    cursor = coll.find(query, projection={"_id": False}).skip(skip).limit(limit)
    items = list(cursor)
    count = coll.count_documents(query)

    return jsonify({"count": count, "items": items})

@app.get("/api/stats")
def stats():
    coll = get_collection()
    
    docs = list(coll.find({}, projection={"_id": False, "temperature": 1, "salinity": 1, "odo": 1}))
    if not docs:
        return jsonify({"stats": {}})
    df = pd.DataFrame(docs)
    out = {}
    for col in ["temperature", "salinity", "odo"]:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if not series.empty:
                out[col] = {
                    "count": int(series.count()),
                    "mean": float(series.mean()),
                    "min": float(series.min()),
                    "p25": float(series.quantile(0.25)),
                    "p50": float(series.quantile(0.50)),
                    "p75": float(series.quantile(0.75)),
                    "max": float(series.max()),
                }
    return jsonify(out)

@app.get("/api/outliers")
def outliers():
    method = request.args.get("method", "iqr").lower()
    field = request.args.get("field", "temperature").lower()
    k = _parse_float("k") or 1.5
    limit = _parse_int("limit", default=200, cap=1000)

    coll = get_collection()
    docs = list(coll.find({}, projection={"_id": False, field: 1, "timestamp": 1}))
    if not docs:
        return jsonify({"items": []})

    df = pd.DataFrame(docs)
    s = pd.to_numeric(df.get(field), errors="coerce")

    if method == "z":
        z = (s - s.mean()) / s.std(ddof=0)
        mask = z.abs() > k 
    else:
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        mask = (s < lo) | (s > hi)

    flagged = df[mask].head(limit).fillna("").to_dict(orient="records")
    return jsonify({"method": method, "field": field, "k": k, "count": int(mask.sum()), "items": flagged})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

