# Compute Economics Portfolio

A synthetic, end-to-end model of GPU inference economics — from raw events to a
Board-ready brief. It takes ~120,000 generated inference events, loads them into
SQLite, and runs five models that each answer a specific question about how
token usage, batching, caching, demand, and capacity allocation drive compute
margin.

> **Focus:** AI compute & infrastructure demand economics — unit cost, demand forecasting, capacity allocation, and margin.
> **Data:** 100% synthetic and seeded. Zero confidentiality exposure.

---

## Headline insights

_One line per model — the figures below are produced by the executed notebooks (synthetic, seeded data). These are the lines spoken to in an interview._

| # | Model | Headline insight |
|---|-------|------------------|
| 1 | **Token Economics** | **ProductC runs ~17% above** blended cost per 1K output tokens — it is *decode-bound*, not just high-volume; cost is ~75% compute / 15% overhead / 10% power. |
| 2 | **Inference Economics** | Raising interactive batch **3 → 14 cuts cost/inference ~39%** but adds **~72 ms** latency; the margin-optimal batch under a **150 ms SLO is 16**. |
| 3 | **Cache Modeling** | Each **+10 points of cache-hit rate cuts effective cost/inference ~11.8%** — **≈ $2.3M/yr** at a representative 1B inferences/day. |
| 4 | **Demand Forecasting** | Demand compounds **~2.4×/yr**; fleet scales **~1,260 → ~1,985 GPUs** by Q4 (base) ≈ **$22M** capex; band ~1,770–2,200 (down/up). |
| 5 | **Capacity Allocation** | Interactive earns **~47% more margin per GPU-second**; mix is already ~77% interactive, so further shift adds only **+1.0 margin pt** — the binding lever is **utilization toward ~85%**. |

**Capstone:** the five numbers woven into one narrative — cost → cache → demand → allocation → margin.

📄 **One-page executive brief:** [`portfolio/executive_brief.pdf`](portfolio/executive_brief.pdf) (editable source: [`portfolio/executive_brief.docx`](portfolio/executive_brief.docx)) — the board-level artifact, no code, the five insights + integrated story + recommended decisions.

> Dollar and fleet figures use one clearly-labeled scaling assumption (sample → 1B inferences/day); all **percentage** results are scale-free. Assumptions are stated at the top of each notebook.

---

## How to run

```bash
# 1. install deps
pip install -r requirements.txt

# 2. generate the synthetic event table (seeded, reproducible)
python data/generate_data.py            # -> data/events.csv

# 3. load events into SQLite
python pipeline/ingest.py               # -> data/events.db (inference_events + cost_constants)

# 4. open the models in dependency order
jupyter lab models/                     # 01 → 05, then portfolio/capstone_summary.ipynb
```

The SQL each model consumes lives in [`pipeline/queries.sql`](pipeline/queries.sql) (one named, documented query per model).

**No Jupyter?** Pre-rendered, self-contained versions of every notebook (charts embedded) are in [`exports/`](exports) as both `.html` and `.pdf` — start with [`exports/capstone_summary.pdf`](exports/capstone_summary.pdf).

---

## Repository structure

```
compute-economics-portfolio/
  README.md                  ← front door: what this is, how to run, headline insights
  requirements.txt
  data/
    generate_data.py         ← synthetic event generator (seeded, reproducible)
    events.csv               ← generated event table (gitignored)
    events.db                ← SQLite database (generated, gitignored)
  pipeline/
    ingest.py                ← load raw events → SQLite + cost constants
    queries.sql              ← named aggregations feeding each model
  models/
    01_token_economics.ipynb
    02_inference_economics.ipynb
    03_cache_modeling.ipynb
    04_demand_forecasting.ipynb
    05_capacity_allocation.ipynb
  portfolio/
    capstone_summary.ipynb   ← integrates one headline result from each model
    executive_brief.pdf      ← one-page board-level brief (rendered)
    executive_brief.docx     ← editable source of the brief
  exports/                   ← pre-rendered .html + .pdf of every notebook (charts embedded)
```

Each model notebook contains three things: **(1) inputs & assumptions, (2) working code with visible output, (3) a written insight** stating what the model reveals.

---

## The data: `inference_events`

~120,000 GPU inference events over a ~12-month window. Distributions are
engineered (not random noise) so the models surface real effects — an upward
demand trend with weekly seasonality, a ~20–40% cache-hit band, and a 65–85%
utilization band.

| Column | Description |
|--------|-------------|
| `event_id` | Unique sequential integer |
| `timestamp` | Event time; engineered upward demand trend + weekly seasonality |
| `product` | ProductA–E — enables per-product margin |
| `workload_type` | `interactive` (latency-sensitive) vs `batch` (throughput-tolerant) |
| `gpu_type` | H100 / H200 / B200 — different cost & throughput profiles |
| `tokens_input` | Prompt tokens |
| `tokens_output` | Completion tokens (the expensive ones) |
| `latency_ms` | Inversely related to batch size; interactive tighter |
| `batch_size` | Higher batch = better throughput, worse latency (core tradeoff) |
| `cache_hit` | Boolean; ~20–40% hit rate, higher for repeat-heavy products |
| `gpu_seconds` | Compute consumed — the basis for cost |
| `utilization_pct` | GPU utilization at event time (65–85% band) |

**Cost basis** (in `cost_constants`, set in [`pipeline/ingest.py`](pipeline/ingest.py)):
GPU hourly cost by `gpu_type`, fixed power cost per GPU-hour (take-or-pay), and a
blendable $/GPU-second. These turn `gpu_seconds` into cost and let every model
compute margin.

---

## Models → Questions Answered

| Model | Question it answers |
|-------|---------------------|
| 1 Token Economics | How throughput and token mix drive cost per token and margin |
| 2 Inference Economics | The latency–throughput–cost tradeoff and where margin optimizes |
| 3 Cache Modeling | The ROI of cache optimization on effective cost per inference |
| 4 Demand Forecasting | How usage growth translates into compute and capital requirements |
| 5 Capacity Allocation | How to optimize utilization against margin across workloads |
| Capstone | How the five models integrate into an executive decision view |
