"""
ingest.py — Load raw synthetic events into SQLite (data/events.db).

This is the "100,000+ events processed" claim made real: it reads the CSV
produced by data/generate_data.py, writes the `inference_events` table, adds
the cost constants as a small reference table, and creates indexes the model
queries rely on.

Run:
    python data/generate_data.py        # produces data/events.csv (if not present)
    python pipeline/ingest.py           # builds data/events.db
"""

from __future__ import annotations

import os
import sqlite3

import pandas as pd

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "events.csv")
DB_PATH = os.path.join(DATA_DIR, "events.db")

# ---------------------------------------------------------------------------
# Cost basis — the constants that turn gpu_seconds into cost and let every
# model compute margin. Illustrative values for a synthetic portfolio.
# ---------------------------------------------------------------------------
GPU_HOURLY_COST = {"H100": 2.90, "H200": 3.60, "B200": 5.20}   # $/GPU-hour (compute)
POWER_COST_PER_GPU_HOUR = 0.45                                  # $/GPU-hour (fixed / take-or-pay)
OVERHEAD_RATE = 0.18                                           # fraction added for networking/storage/etc.


def cost_constants_frame() -> pd.DataFrame:
    rows = []
    for gpu, hourly in GPU_HOURLY_COST.items():
        compute_per_sec = hourly / 3600.0
        power_per_sec = POWER_COST_PER_GPU_HOUR / 3600.0
        rows.append(
            {
                "gpu_type": gpu,
                "gpu_hourly_cost": hourly,
                "power_cost_per_gpu_hour": POWER_COST_PER_GPU_HOUR,
                "overhead_rate": OVERHEAD_RATE,
                "compute_cost_per_gpu_second": round(compute_per_sec, 8),
                "power_cost_per_gpu_second": round(power_per_sec, 8),
                "blended_cost_per_gpu_second": round(
                    (compute_per_sec + power_per_sec) * (1 + OVERHEAD_RATE), 8
                ),
            }
        )
    return pd.DataFrame(rows)


def ingest(csv_path: str = CSV_PATH, db_path: str = DB_PATH) -> None:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"{csv_path} not found. Run `python data/generate_data.py` first."
        )

    events = pd.read_csv(csv_path, parse_dates=["timestamp"])

    if os.path.exists(db_path):
        os.remove(db_path)

    with sqlite3.connect(db_path) as conn:
        events.to_sql("inference_events", conn, index=False)
        cost_constants_frame().to_sql("cost_constants", conn, index=False)

        cur = conn.cursor()
        cur.execute("CREATE INDEX idx_events_ts ON inference_events(timestamp)")
        cur.execute("CREATE INDEX idx_events_product ON inference_events(product)")
        cur.execute("CREATE INDEX idx_events_gpu ON inference_events(gpu_type)")
        cur.execute("CREATE INDEX idx_events_workload ON inference_events(workload_type)")
        conn.commit()

        n = cur.execute("SELECT COUNT(*) FROM inference_events").fetchone()[0]

    print(f"Loaded {n:,} events into {db_path}")
    print("  tables: inference_events, cost_constants")


if __name__ == "__main__":
    ingest()
