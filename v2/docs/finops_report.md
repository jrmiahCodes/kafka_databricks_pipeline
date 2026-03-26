# FinOps Report: v2 Kafka + Databricks Streaming Pipeline

## Purpose

This report documents cost-aware design choices and the measured baseline benchmark used to compare v1 and v2. The goal is not just theoretical pricing awareness. The goal is to connect pipeline design choices to observed batch behavior, attributable job-compute usage, and the tradeoff between operational clarity and spend.

## 1) Measured Inputs for Cost Analysis

This repository captures benchmark-oriented micro-batch metrics that can be used as direct inputs to cost analysis.

Operational benchmark inputs:

- `run_id`
- `job_name`
- `batch_id`
- `batch_processed_ts`
- `row_count`
- `target_table`

These rows are written to `OPS_METRICS_TABLE` and make it possible to compare baseline, replay, malformed-input, and stress-test runs using measured job behavior rather than architecture claims alone.

Serving-layer runtime baseline:

- Full `dbt build` against target `dev` completed in `26.9s`
- Processed `13 models` and `25 tests`
- Result summary: `38 total`, `33 success`, `5 no-op`

This is tracked as lightweight end-to-end operational awareness rather than a stakeholder KPI. It is useful because Gold-layer cost is not only about model SQL complexity. Warehouse sizing, repeated exploratory queries, and dashboard usage also affect serving-layer spend.

## 2) Why Job Compute Over Interactive Clusters for Repeatable ETL

For scheduled ingestion and transformation, Databricks job compute is preferred because it is easier to bound and attribute:

- Jobs start for a workload and terminate after completion, reducing idle runtime.
- Compute policy can enforce instance families, autoscaling bounds, and runtime limits.
- Cost attribution is cleaner by job and run than shared interactive clusters.
- Operational behavior is more reproducible across benchmark scenarios.

Interactive or serverless notebooks remain useful for exploration, setup, and incident debugging, but they are not the primary execution surface for repeatable ETL because benchmark-session overhead can blur true pipeline runtime cost.

## 3) Checkpoint and Storage Tradeoffs

Streaming checkpoints are non-optional for fault tolerance and progress tracking, but they introduce persistent storage cost.

Tradeoffs:

- More granular micro-batches can improve latency but can increase checkpoint churn.
- Long-lived state and frequent metadata writes can grow storage over time.
- Deleting checkpoints too aggressively can break recovery semantics.

Practical approach:

- Use dedicated checkpoint paths per job and environment.
- Monitor checkpoint growth trend, not just absolute size.
- Pair checkpoint retention strategy with replay and runbook expectations.

## 4) Delta Retention and Cost Considerations

Delta cost posture should align to layer purpose:

- Bronze keeps replayable raw history long enough for backfill and audit needs.
- Silver retains enough history for contract debugging and feature reprocessing.
- Serving tables optimize for downstream access patterns rather than raw recovery.

Cost and risk notes:

- Overly long retention inflates storage and metadata scan overhead.
- Overly short retention can break incident recovery and historical reprocessing.
- VACUUM and OPTIMIZE cadence should be explicit and environment-specific.

## 5) Expected Compute Hotspots in This Pipeline

Likely hotspots include:

- regex-heavy feature extraction in `silver_features`
- high-volume string normalization in `silver_parse`
- minute-level operational and engagement rollups downstream in dbt
- replay windows or bursty workloads that compress more work into fewer batches
- SQL warehouse time consumed by dbt builds, exploratory verification queries, and dashboard reads

Mitigation strategy:

- keep Bronze minimal
- stage canonical parsing before downstream heuristics
- reuse intermediate expressions where possible
- measure batch shape changes before and after feature additions

## 6) Cost-Aware Dev Exploration and Serving-Layer SQL

This project surfaced an important practical lesson: exploratory querying in a Databricks trial or paid workspace is still billable compute. That includes:

- dbt serving-layer builds
- Gold-table validation queries
- row reconciliation queries
- billing-system inspection queries
- dashboard queries and refreshes

For this reason, serving-layer cost should be treated as a real part of end-to-end pipeline cost rather than assumed negligible.

Practical development guidance:

- Use the smallest practical SQL warehouse for dev exploration.
- Set aggressive auto-stop for dev warehouses.
- Batch investigation into one focused session instead of repeatedly waking the warehouse for many short checks.
- Prefer bounded filters, narrow projections, and aggregate-first checks before event-level joins.
- Save or export small result sets when repeated inspection is needed instead of rerunning the same query pattern.
- Keep ad hoc exploration logically separate from scheduled serving-model builds when evaluating pipeline runtime cost.

Environment note:

- A Databricks Free Edition workspace can be useful for lightweight SQL iteration and dashboard prototyping because it is quota-limited rather than trial-credit based.
- A Databricks free trial or paid workspace consumes billable usage units for serverless jobs and SQL warehouse activity.
- Free Edition is still a separate environment, so it is useful for dev iteration but not a direct substitute for final paid-workspace validation.

## 7) Cost per Million Messages Processed

A practical portfolio KPI is unit economics at message scale.

Baseline formula:

`cost_per_million_messages_usd = (total_pipeline_cost_usd / total_messages_processed) * 1000000`

Where `total_pipeline_cost_usd` should include:

- streaming job compute
- scheduled dbt or serving-model compute
- storage for Delta and checkpoints, allocated proportionally
- relevant Kafka and cloud costs included in the comparison scope

Interpretation guidance:

- compare by `run_id`
- compare baseline versus stress-test scenarios
- pair cost with DLQ rate, freshness, and throughput so cost reductions do not hide quality regressions

## 8) Native Spark Expressions vs Python UDF Cost Impact

Native Spark expressions are preferred in this pipeline for cost and performance reasons:

- Catalyst optimization is available for native expressions.
- Python serialization overhead is reduced.
- Execution plans remain easier to inspect.
- Batch comparisons stay easier to attribute when logic remains within Spark's native engine.

Python UDFs are reserved for cases without practical native equivalents. If introduced, they should be measured with before-and-after cost and latency comparisons.

## 9) Practical Cost-Control Recommendations

1. Enforce cluster policies for all scheduled jobs.
2. Use environment-specific schedules; avoid production cadence in dev.
3. Set explicit retention policies for Bronze, Silver, and checkpoint locations.
4. Review feature logic for regex or shuffle-heavy regressions.
5. Prefer incremental dbt materializations where semantics allow.
6. Tag runs consistently by pipeline, environment, owner, and benchmark scenario.
7. Track cost and reliability together using unit economics plus freshness and DLQ indicators.
8. Right-size SQL warehouses and set aggressive auto-stop in trial/demo environments.
9. Treat exploratory SQL and dashboard activity as measurable engineering cost, not free ambient work.

## 10) Baseline Benchmark Findings (`RUN_ID = v2_baseline_backlog_2026_03_16`)

### Benchmark environment

All three jobs ran on the same job-cluster shape:

- Databricks Runtime `15.4 LTS`
- Spark `3.5.0`
- Photon enabled
- node type `m5d.large`
- single-node job cluster
- estimated DBU rate shown in the job UI: `0.986 DBU/hour`
- Unity Catalog access mode: dedicated / single user
- `spark.sql.shuffle.partitions = 8`
- dedicated checkpoint paths per stage under Unity Catalog volumes

### Measured output reconciliation

The baseline replay processed a small backlog and reconciled cleanly across all streaming stages:

- Bronze: `7006` rows
- Silver parsed: `7005` rows
- Silver features: `7005` rows
- DLQ: `1` row (`CONTRACT_ERROR / CONTRACT_REQUIRED_FIELDS_MISSING`)

Reconciliation outcome:

- `7006 Bronze = 7005 valid + 1 DLQ`
- `silver_features` matched the valid parsed set exactly

### Batch shape

Each stage processed one productive micro-batch in this baseline replay:

- `bronze_ingest`: batch `0` = `7006`
- `silver_parse`: batch `0` = `7005`
- `silver_features`: batch `0` = `7005`

Observed operational note:

- `silver_parse` emitted an additional zero-row batch (`batch_id = 1`) under `availableNow`; this was treated as expected termination noise rather than a correctness issue.

### Job runtime behavior

Databricks job-level timing showed that cluster startup and scheduling overhead dominated elapsed time at this load:

- `bronze_ingest_job`: total `10m 1s`, waiting `7m 25s`, library install `20s`, running `2m 16s`
- `silver_parse_job`: total `10m 33s`, waiting `7m 22s`, library install `20s`, running `2m 52s`
- `Silver_features_job`: total `9m 24s`, waiting `6m 52s`, library install `20s`, running `2m 12s`

Available Spark UI observations reinforced the same conclusion:

- Bronze streaming work completed in about `67s`
- Silver Parse productive streaming work completed in about `1m 22s`, followed by a short no-op query of `928 ms`
- Silver Features stage/task work also completed quickly relative to total elapsed job time, but the detailed Spark UI view was not retained for the final benchmark record

Serving-layer build note:

- A subsequent full `dbt build` against target `dev` completed in `26.9s`
- Build scope: `13 models`, `25 tests`
- Result summary: `38 total`, `33 success`, `5 no-op`

This does not imply that Gold is expensive by default. It does show that serving-layer runtime should be tracked separately from streaming job runtime, and that warehouse choice plus exploratory query behavior can matter more than model count alone.

### Attributable job-compute usage

`system.billing.usage` produced clean job-attributed rows for the three benchmark jobs:

- `bronze_ingest_job`: `0.1132448389 DBU`
- `silver_parse_job`: `0.1228156122 DBU`
- `Silver_features_job`: `0.1104432294 DBU`

Total attributable benchmark job compute:

- `0.3465036805 DBU`

### Interactive benchmark-session overhead

The same billing window also contained `INTERACTIVE` serverless notebook usage tied to:

- notebook path: `/Users/jeremiahpg@gmail.com/pipeline_query_tests`
- notebook id: `2816283970830393`
- `is_serverless = true`
- `is_photon = true`

This interactive usage was not attributed to the three dedicated job clusters and was treated separately as benchmark-session overhead related to reset, prep, verification, metric inspection, and exploratory queries.

### Practical interpretation

This baseline benchmark established six concrete findings:

1. The v2 refactor behaved correctly end to end under controlled backlog replay.
2. Micro-batch observability is now in place across Bronze, Parse, Features, DLQ, and the compact ops metrics table.
3. At this workload, each stage processed essentially one productive batch, so the benchmark reflects a low-volume replay rather than a throughput stress case.
4. Cluster acquisition, job scheduling, and library install overhead dominated elapsed runtime more than Spark transformation work.
5. The split v2 architecture improved clarity, observability, and failure isolation, but was economically over-separated for a backlog this small when executed as three independent job-cluster runs.
6. Serving-layer validation is operationally lightweight at this scale, but warehouse-backed exploration still needs cost discipline in trial or paid environments.

## 11) What This Means for Future Cost Testing

This report is now grounded in one measured baseline run rather than only a theoretical framework.

The next cost questions are intentionally narrower:

- At what replay volume do three isolated jobs become operationally worthwhile?
- How much does shared-cluster or multi-task orchestration reduce startup overhead?
- How do malformed-input rates and bursty workloads change unit economics?
- How much serving-layer cost is introduced once Gold is scheduled, queried repeatedly, or attached to dashboards in a paid workspace?
- Which dev workflows belong in a lower-cost or quota-limited environment versus the paid validation environment?

Until those larger-scale scenarios are measured, the main defensible claim is:

> v2 is operationally clearer and more reliable than v1, but on very small replay volumes the main cost driver is orchestration overhead rather than streaming transformation complexity.
