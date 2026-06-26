"""
Splits all_states_combined.csv into small, per-state CSV files so the
website never has to load the full 96MB / 294-column file into memory.

Run once: python preprocess.py
Output:   data/by_state/<state_key>.csv  (one per state, ~9-10k rows x 8 cols)
          data/states_meta.json          (list of available states + capital/lat/lon)
"""
import pandas as pd
import json
import os
import re

SRC = "/mnt/user-data/uploads/all_states_combined.csv"
OUT_DIR = "/home/claude/weather_site/data/by_state"
META_OUT = "/home/claude/weather_site/data/states_meta.json"

METRICS = [
    "temp_mean", "temp_min", "temp_max", "humidity", "precipitation",
    "wind_speed", "wind_gust", "cloud_cover", "pressure",
    "global_radiation", "sunshine",
]

print("Reading combined CSV (this is the only time we touch the big file)...")
df = pd.read_csv(SRC, parse_dates=["DATE"])
print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

states = sorted(df["STATE"].unique())
print(f"Found {len(states)} states with data: {states}")

meta = []
for state in states:
    sub = df[df["STATE"] == state].copy()
    prefix = re.sub(r"[^A-Z0-9]+", "_", state.upper()).strip("_")
    cols = {f"{prefix}_{m}": m for m in METRICS}
    missing = [c for c in cols if c not in sub.columns]
    if missing:
        print(f"  [WARN] {state}: missing columns {missing}, skipping")
        continue

    out = sub[["DATE", "YEAR", "MONTH", "DAY"] + list(cols.keys())].rename(columns=cols)
    out = out.sort_values("DATE")
    state_key = state.lower().replace(" ", "_")
    out.to_csv(os.path.join(OUT_DIR, f"{state_key}.csv"), index=False)

    capital = sub["CAPITAL"].iloc[0]
    lat = float(sub["LAT"].iloc[0])
    lon = float(sub["LON"].iloc[0])
    meta.append({
        "state_key": state_key,
        "state": state,
        "capital": capital,
        "lat": lat,
        "lon": lon,
        "rows": len(out),
        "date_min": str(out["DATE"].min().date()),
        "date_max": str(out["DATE"].max().date()),
    })
    print(f"  [OK] {state}: {len(out)} rows -> {state_key}.csv")

with open(META_OUT, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\nDone. {len(meta)} per-state files written to {OUT_DIR}")
print(f"Metadata written to {META_OUT}")
