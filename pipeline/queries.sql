-- queries.sql
-- Named, documented aggregations feeding each model. Each query joins
-- inference_events to cost_constants so gpu_seconds becomes cost.
--
-- Convention: cost($) = gpu_seconds * blended_cost_per_gpu_second
-- Run any block against data/events.db (sqlite3 data/events.db < pipeline/queries.sql).

-- =====================================================================
-- Q1  cost_per_token_by_product   -> Model 1 (Token Economics)
-- Cost per 1K output tokens by product and gpu_type, decomposed into
-- compute / power / overhead.
-- =====================================================================
SELECT
    e.product,
    e.gpu_type,
    SUM(e.tokens_output)                                              AS output_tokens,
    SUM(e.gpu_seconds)                                               AS gpu_seconds,
    SUM(e.gpu_seconds * c.compute_cost_per_gpu_second)               AS compute_cost,
    SUM(e.gpu_seconds * c.power_cost_per_gpu_second)                 AS power_cost,
    SUM(e.gpu_seconds * (c.compute_cost_per_gpu_second
                       + c.power_cost_per_gpu_second) * c.overhead_rate) AS overhead_cost,
    1000.0 * SUM(e.gpu_seconds * c.blended_cost_per_gpu_second)
           / SUM(e.tokens_output)                                    AS cost_per_1k_output_tokens
FROM inference_events e
JOIN cost_constants c USING (gpu_type)
GROUP BY e.product, e.gpu_type
ORDER BY cost_per_1k_output_tokens DESC;

-- =====================================================================
-- Q2  cost_per_inference_by_workload_batch  -> Model 2 (Inference Economics)
-- Cost per inference and mean latency across batch-size buckets, split by
-- workload_type — the latency/throughput/cost tradeoff.
-- =====================================================================
SELECT
    e.workload_type,
    CASE
        WHEN e.batch_size <= 8   THEN '01-08'
        WHEN e.batch_size <= 16  THEN '09-16'
        WHEN e.batch_size <= 32  THEN '17-32'
        WHEN e.batch_size <= 64  THEN '33-64'
        ELSE '65-128'
    END                                                              AS batch_bucket,
    COUNT(*)                                                         AS n_inferences,
    AVG(e.batch_size)                                                AS avg_batch_size,
    AVG(e.latency_ms)                                                AS avg_latency_ms,
    AVG(e.gpu_seconds * c.blended_cost_per_gpu_second)               AS cost_per_inference
FROM inference_events e
JOIN cost_constants c USING (gpu_type)
GROUP BY e.workload_type, batch_bucket
ORDER BY e.workload_type, avg_batch_size;

-- =====================================================================
-- Q3  cache_hit_cost_delta   -> Model 3 (Cache Modeling)
-- Cost per inference for cache hits vs misses, by workload. The delta is
-- the per-request saving each cache hit captures.
-- =====================================================================
SELECT
    e.workload_type,
    e.cache_hit,
    COUNT(*)                                                         AS n_inferences,
    AVG(e.gpu_seconds)                                               AS avg_gpu_seconds,
    AVG(e.gpu_seconds * c.blended_cost_per_gpu_second)               AS cost_per_inference
FROM inference_events e
JOIN cost_constants c USING (gpu_type)
GROUP BY e.workload_type, e.cache_hit
ORDER BY e.workload_type, e.cache_hit;

-- =====================================================================
-- Q4  demand_time_series   -> Model 4 (Demand Forecasting)
-- Daily GPU-seconds and inference volume — the historical usage trend that
-- gets projected forward into fleet requirements.
-- =====================================================================
SELECT
    DATE(e.timestamp)                                                AS day,
    COUNT(*)                                                         AS n_inferences,
    SUM(e.gpu_seconds)                                               AS gpu_seconds,
    SUM(e.gpu_seconds * c.blended_cost_per_gpu_second)               AS cost
FROM inference_events e
JOIN cost_constants c USING (gpu_type)
GROUP BY day
ORDER BY day;

-- =====================================================================
-- Q5  utilization_vs_margin   -> Model 5 (Capacity Allocation)
-- Per product x workload: volume, utilization, and cost — the inputs to the
-- utilization-vs-margin frontier and reallocation analysis.
-- =====================================================================
SELECT
    e.product,
    e.workload_type,
    COUNT(*)                                                         AS n_inferences,
    AVG(e.utilization_pct)                                           AS avg_utilization_pct,
    SUM(e.gpu_seconds)                                               AS gpu_seconds,
    SUM(e.tokens_output)                                             AS output_tokens,
    SUM(e.gpu_seconds * c.blended_cost_per_gpu_second)               AS cost,
    1000.0 * SUM(e.gpu_seconds * c.blended_cost_per_gpu_second)
           / SUM(e.tokens_output)                                    AS cost_per_1k_output_tokens
FROM inference_events e
JOIN cost_constants c USING (gpu_type)
GROUP BY e.product, e.workload_type
ORDER BY e.product, e.workload_type;
