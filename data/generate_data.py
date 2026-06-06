"""
generate_data.py — Seeded synthetic generator for the `inference_events` table.

Produces ~120,000 GPU inference events over a ~12-month window. The distributions
are deliberately engineered (not random noise) so the five models surface real,
defensible effects:

  - demand trend ........ upward growth + weekly seasonality in `timestamp`
  - cost-per-token ...... output-token intensity varies by product
  - batch tradeoff ...... higher batch_size -> better throughput, worse latency
  - cache effect ........ ~20-40% blended hit rate, higher for repeat-heavy products
  - utilization band .... 65-85% so absorption / margin effects are visible

Run:
    python data/generate_data.py            # writes data/events.csv
    python data/generate_data.py --rows 200000 --seed 7

Output: a CSV consumed by pipeline/ingest.py to build data/events.db.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42
N_ROWS = 120_000
WINDOW_DAYS = 365
START = datetime(2025, 1, 1)

# ---- categorical universes -------------------------------------------------
PRODUCTS = ["ProductA", "ProductB", "ProductC", "ProductD", "ProductE"]
GPU_TYPES = ["H100", "H200", "B200"]
WORKLOADS = ["interactive", "batch"]

# Per-product output-token intensity multiplier. ProductC is output-heavy.
PRODUCT_OUTPUT_INTENSITY = {
    "ProductA": 0.85,
    "ProductB": 1.00,
    "ProductC": 1.55,   # generates more output tokens per call
    "ProductD": 1.10,
    "ProductE": 0.75,
}

# Per-product decode efficiency. Output-heavy products are decode-bound and
# parallelize worse, so each output token costs more compute. This is what
# makes ProductC read as "above blended cost-per-token" in Model 1 — the
# effect comes from genuinely costlier output tokens, not from arithmetic.
PRODUCT_DECODE_EFFICIENCY = {
    "ProductA": 1.05,
    "ProductB": 1.00,
    "ProductC": 0.70,   # decode-bound -> high cost-per-output-token
    "ProductD": 0.95,
    "ProductE": 1.10,
}

# Per-product cache friendliness (repeat-prompt heavy products cache better).
PRODUCT_CACHE_BASE = {
    "ProductA": 0.42,
    "ProductB": 0.30,
    "ProductC": 0.18,
    "ProductD": 0.35,
    "ProductE": 0.25,
}

# GPU throughput (tokens/GPU-second) and relative cost profile.
GPU_THROUGHPUT = {"H100": 2400.0, "H200": 3200.0, "B200": 4600.0}


def generate(n_rows: int = N_ROWS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # --- timestamp: upward demand trend + weekly seasonality ----------------
    # Sample a day with probability rising over the year, then weight weekdays
    # higher than weekends to create weekly seasonality.
    day_idx = np.arange(WINDOW_DAYS)
    trend = 1.0 + 1.4 * (day_idx / WINDOW_DAYS)          # ~2.4x more volume by year-end
    weekday = (START + pd.to_timedelta(day_idx, unit="D")).weekday
    weekly = np.where(weekday < 5, 1.0, 0.55)            # weekends quieter
    day_weights = trend * weekly
    day_weights /= day_weights.sum()
    days = rng.choice(day_idx, size=n_rows, p=day_weights)
    seconds = rng.integers(0, 86_400, size=n_rows)
    timestamps = [START + timedelta(days=int(d), seconds=int(s)) for d, s in zip(days, seconds)]

    # --- categoricals -------------------------------------------------------
    product = rng.choice(PRODUCTS, size=n_rows, p=[0.28, 0.22, 0.18, 0.17, 0.15])
    workload_type = rng.choice(WORKLOADS, size=n_rows, p=[0.65, 0.35])
    gpu_type = rng.choice(GPU_TYPES, size=n_rows, p=[0.5, 0.3, 0.2])

    # --- tokens -------------------------------------------------------------
    tokens_input = rng.lognormal(mean=6.0, sigma=0.6, size=n_rows).astype(int) + 8
    intensity = np.array([PRODUCT_OUTPUT_INTENSITY[p] for p in product])
    base_output = rng.lognormal(mean=5.4, sigma=0.7, size=n_rows)
    tokens_output = (base_output * intensity).astype(int) + 4

    # --- batch_size: batch workloads run much larger batches ----------------
    batch_size = np.where(
        workload_type == "batch",
        rng.integers(16, 129, size=n_rows),     # 16..128
        rng.integers(1, 17, size=n_rows),        # 1..16
    )

    # --- latency: inverse-ish with batch, interactive tighter ---------------
    # Larger batch -> higher per-request latency; interactive has tighter spread.
    base_latency = 40 + 6.5 * batch_size
    noise_scale = np.where(workload_type == "interactive", 0.10, 0.30)
    latency_ms = base_latency * rng.normal(1.0, noise_scale, size=n_rows)
    latency_ms = np.clip(latency_ms, 15, None).round(1)

    # --- gpu_seconds: split into fast parallel prefill + slow sequential decode
    # Prefill (input) is highly parallel and cheap per token; decode (output) is
    # sequential and dominates cost. Output-heavy products decode less
    # efficiently, so their output tokens are genuinely more expensive.
    throughput = np.array([GPU_THROUGHPUT[g] for g in gpu_type])
    decode_eff = np.array([PRODUCT_DECODE_EFFICIENCY[p] for p in product])
    batch_efficiency = 1.0 + 0.45 * np.log2(batch_size)   # bigger batch amortizes
    prefill_seconds = tokens_input / (throughput * 6.0 * batch_efficiency)
    decode_seconds = tokens_output / (throughput * batch_efficiency * decode_eff)
    gpu_seconds = prefill_seconds + decode_seconds
    gpu_seconds *= rng.normal(1.0, 0.08, size=n_rows)
    gpu_seconds = np.clip(gpu_seconds, 1e-4, None).round(5)

    # --- cache_hit: per-product base, repeat prompts cache better -----------
    cache_p = np.array([PRODUCT_CACHE_BASE[p] for p in product])
    cache_p = np.where(workload_type == "batch", cache_p + 0.06, cache_p)
    cache_hit = rng.random(n_rows) < cache_p

    # --- utilization_pct: engineered 65-85% band ----------------------------
    utilization_pct = rng.normal(75, 5, size=n_rows)
    # higher batch nudges utilization up
    utilization_pct += (batch_size / 128.0) * 6
    utilization_pct = np.clip(utilization_pct, 60, 92).round(2)

    df = pd.DataFrame(
        {
            "event_id": np.arange(1, n_rows + 1),
            "timestamp": timestamps,
            "product": product,
            "workload_type": workload_type,
            "gpu_type": gpu_type,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "latency_ms": latency_ms,
            "batch_size": batch_size,
            "cache_hit": cache_hit.astype(int),
            "gpu_seconds": gpu_seconds,
            "utilization_pct": utilization_pct,
        }
    )
    return df.sort_values("timestamp").reset_index(drop=True).assign(
        event_id=lambda d: np.arange(1, len(d) + 1)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic inference_events.")
    parser.add_argument("--rows", type=int, default=N_ROWS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(__file__), "events.csv"),
    )
    args = parser.parse_args()

    df = generate(args.rows, args.seed)
    df.to_csv(args.out, index=False)
    print(f"Generated {len(df):,} events -> {args.out}")
    print(f"  date range : {df.timestamp.min()} .. {df.timestamp.max()}")
    print(f"  cache-hit  : {df.cache_hit.mean():.1%}")
    print(f"  utilization: {df.utilization_pct.mean():.1f}% (band {df.utilization_pct.min()}-{df.utilization_pct.max()})")


if __name__ == "__main__":
    main()
