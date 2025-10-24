from flask import Flask, request, jsonify
from db import get_db_client
import os
import pandas as pd
import numpy as np
from scipy import stats

app = Flask(__name__)

CLIENT = get_db_client()
DB = CLIENT["water_quality_data"]
COL = DB["asv_1"]

def parse_int(name, default=None, minv=None, maxv=None):
    val = request.args.get(name)
    if val is None:
        return default
    try:
        i = int(val)
    except ValueError:
        return default
    if minv is not None and i < minv:
        return minv
    if maxv is not None and i > maxv:
        return maxv
    return i

@app.route("/api/health")
def health():
    return jsonify({"status":"ok"})

def doc_to_primitives(d):
    # convert ObjectId and datetimes to str
    out = {}
    for k,v in d.items():
        if k == "_id":
            continue
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            try:
                float(v)
                out[k] = v
            except Exception:
                out[k] = v
    return out

@app.route("/api/observations")
def observations():
    q = {}
    # time range filter
    start = request.args.get("start")
    end = request.args.get("end")
    if start or end:
        q["timestamp"] = {}
        if start:
            q["timestamp"]["$gte"] = pd.to_datetime(start)
        if end:
            q["timestamp"]["$lte"] = pd.to_datetime(end)
    # numeric filters
    def add_range(field, minp, maxp):
        if minp is None and maxp is None:
            return
        if field not in q:
            q[field] = {}
        if minp is not None:
            q[field]["$gte"] = float(minp)
        if maxp is not None:
            q[field]["$lte"] = float(maxp)

    add_range("temperature", request.args.get("min_temp"), request.args.get("max_temp"))
    add_range("salinity", request.args.get("min_sal"), request.args.get("max_sal"))
    add_range("odo", request.args.get("min_odo"), request.args.get("max_odo"))

    limit = parse_int("limit", 100, minv=1, maxv=1000)
    skip = parse_int("skip", 0, minv=0)
    cursor = COL.find(q).skip(skip).limit(limit)
    items = [doc_to_primitives(d) for d in cursor]
    total = COL.count_documents(q)
    return jsonify({"count": total, "items": items})

@app.route("/api/stats")
def stats():
    pipeline = [{"$project": {"temperature": 1, "salinity": 1, "odo": 1}},
                {"$match": {}}]
    docs = list(COL.find({}, {"_id":0, "temperature":1, "salinity":1, "odo":1}))
    if not docs:
        return jsonify({"count":0, "stats":{}})
    df = pd.DataFrame(docs)
    stats_out = {}
    numeric = [c for c in ["temperature","salinity","odo"] if c in df.columns]
    for c in numeric:
        col = pd.to_numeric(df[c], errors="coerce").dropna()
        stats_out[c] = {
            "count": int(col.count()),
            "mean": float(col.mean()) if not col.empty else None,
            "min": float(col.min()) if not col.empty else None,
            "max": float(col.max()) if not col.empty else None,
            "25%": float(col.quantile(0.25)) if not col.empty else None,
            "50%": float(col.quantile(0.50)) if not col.empty else None,
            "75%": float(col.quantile(0.75)) if not col.empty else None,
        }
    return jsonify({"count": len(df), "stats": stats_out})

@app.route("/api/outliers")
def outliers():
    field = request.args.get("field")
    method = request.args.get("method", "zscore")
    k = float(request.args.get("k", 3.0))
    if not field:
        return jsonify({"error":"missing field parameter"}), 400
    docs = list(COL.find({},{field:1, "timestamp":1, "latitude":1, "longitude":1}))
    df = pd.DataFrame(docs)
    if df.empty or field not in df.columns:
        return jsonify({"count":0, "items":[]})
    series = pd.to_numeric(df[field], errors="coerce").dropna()
    if method == "iqr":
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        low = q1 - k * iqr
        high = q3 + k * iqr
        mask = (df[field] < low) | (df[field] > high)
    else:  # zscore
        z = np.abs(stats.zscore(pd.to_numeric(df[field], errors="coerce"), nan_policy="omit"))
        mask = z > k
    flagged = df[mask]
    items = []
    for _, row in flagged.iterrows():
        items.append({
            "timestamp": row.get("timestamp").isoformat() if hasattr(row.get("timestamp"), "isoformat") else str(row.get("timestamp")),
            field: float(row[field]) if pd.notnull(row[field]) else None,
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
        })
    return jsonify({"count": len(items), "items": items})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
