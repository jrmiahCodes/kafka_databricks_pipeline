# FinOps Report: v2 Kafka + Databricks Streaming Pipeline

## Purpose

This report documents cost-aware design choices and the measurement framework used to compare v1 and v2. The goal is not just theoretical pricing awareness. The goal is to connect pipeline design choices to measured batch behavior, expected cost drivers, and tradeoffs between reliability and spend.

## 1) Measured Inputs for Cost Analysis

This repository now captures benchmark-oriented micro-batch metrics that can be used as direct inputs to cost analysis.

Operational benchmark inputs:

- `run_id`
- `job_name`
- `batch_id`
- `batch_processed_ts`
- `row_count`
- `target_table`

These rows are written to `OPS_METRICS_TABLE` and make it possible to compare baseline, replay, malformed-input, and stress-test runs using measured job behavior rather than architecture claims alone.

Serving-layer baseline:

- Full `dbt build` against target `dev` completed in `26.9s`
- Processed `13 models` and `25 tests`
- Result summary: `38 total`, `33 success`, `5 no-op`

This is not treated as a stakeholder KPI. It is a lightweight engineering signal for end-to-end runtime awareness and helps frame serving-layer cost and freshness tradeoffs alongside the streaming job metrics.

## 2) Why Job Compute Over Interactive Clusters for Repeatable ETL

For scheduled ingestion and transformation, Databricks job compute is preferred because it is easier to bound and attribute:

- Jobs start for a workload and terminate after completion, reducing idle runtime.
- Compute policy can enforce instance families, autoscaling bounds, and runtime limits.
- Cost attribution is cleaner by job and run than shared interactive clusters.
- Operational behavior is more reproducible across benchmark scenarios.

Interactive clusters remain useful for exploration and incident debugging, but they are not the primary execution surface for repeatable ETL due to idle cost and governance drift.

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
- SQL warehouse time consumed by dbt serving-layer builds, ad hoc exploration, and dashboard queries

Mitigation strategy:

- keep Bronze minimal
- stage canonical parsing before downstream heuristics
- reuse intermediate expressions where possible
- measure batch shape changes before and after feature additions

## 6) Serving-Layer SQL Warehouse Cost Awareness

The Gold and serving-layer dbt models are lightweight in code volume, but they can still consume noticeable cost when run on a SQL warehouse.

Practical points:

- `dbt build` runtime is not the only cost driver; warehouse startup time, auto-resume behavior, and repeated exploratory queries can materially add to usage.
- SQL warehouses can start automatically when a query runs, a scheduled job executes, or a dashboard opens.
- A small serving-layer model set is still billed on the warehouse SKU in use, so warehouse size and auto-stop settings matter.
- For this reason, serving-layer cost should be reviewed alongside streaming job cost rather than assumed to be negligible.

Repository guidance:

- Track dbt build wall-clock time as an engineering signal.
- Review SQL warehouse billable usage with `system.billing.usage` and `system.billing.list_prices`.
- Prefer right-sized warehouses and aggressive auto-stop for portfolio/demo environments.
- Avoid conflating stakeholder-facing Gold models with always-on BI serving requirements when evaluating cost.

## 7) Cost-Aware Table Exploration in Dev

Exploratory querying in a Databricks trial or paid workspace is not free just because it is ad hoc. Queries against Gold tables, Silver tables, and billing system tables still run on billable compute.

Practical dev-mode guidance:

- Use the smallest practical SQL warehouse for exploratory work.
- Configure aggressive auto-stop for dev warehouses.
- Separate exploratory querying from scheduled serving-model builds so ad hoc analysis does not blur with pipeline runtime.
- Batch investigative questions into one focused session instead of repeatedly waking the warehouse for many short checks.
- Prefer narrow projections, explicit filters, and bounded time windows over `select *` scans.
- Start with sampled rows, metadata checks, and limited aggregates before escalating to wide reconciliations.
- Reuse query history and query profile to inspect expensive queries before rerunning modified versions.
- Use account budgets and serverless budget policies so dev exploration can be attributed and reviewed separately from scheduled workloads.

Examples of cheaper-first habits:

- filter by `run_id`, date range, or partition window before reconciling row counts
- inspect only required columns for reconciliation
- compare minute/day aggregates before doing event-level joins
- export or save a small result set for repeated inspection instead of re-running the same warehouse query many times

This repository treats exploratory querying as a legitimate part of engineering work, but one that should be intentionally bounded in dev environments.

## 8) Cost per Million Messages Processed

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

## 9) Free Edition vs Free Trial Cost Caveat

It is important to distinguish two Databricks entry paths:

- Free Edition: no-cost, quota-limited, serverless-only environment intended for learning and experimentation
- Free trial: full-platform evaluation account with time-boxed usage credits

In Free Edition, serverless usage is constrained by platform quotas rather than billed against trial credits. In a free trial or paid account, serverless jobs and SQL warehouses consume billable usage units that draw down credits or incur cost.

This matters for portfolio benchmarking because exploratory SQL, dashboard refreshes, and serving-layer `dbt build` activity may consume trial credits even when the streaming jobs themselves appear modest.

## 10) Native Spark Expressions vs Python UDF Cost Impact

Native Spark expressions are preferred in this pipeline for cost and performance reasons:

- Catalyst optimization is available for native expressions.
- Python serialization overhead is reduced.
- Execution plans remain easier to inspect.
- Batch comparisons stay easier to attribute when logic remains within Spark's native engine.

Python UDFs are reserved for cases without practical native equivalents. If introduced, they should be measured with before-and-after cost and latency comparisons.

## 11) Practical Cost-Control Recommendations

1. Enforce cluster policies for all scheduled jobs.
2. Use environment-specific schedules; avoid production cadence in dev.
3. Set explicit retention policies for Bronze, Silver, and checkpoint locations.
4. Review feature logic for regex or shuffle-heavy regressions.
5. Prefer incremental dbt materializations where semantics allow.
6. Tag runs consistently by pipeline, environment, owner, and benchmark scenario.
7. Track cost and reliability together using unit economics plus freshness and DLQ indicators.
8. Set SQL warehouse auto-stop aggressively in trial/demo environments and avoid leaving exploratory warehouses running.
9. Keep a dedicated dev exploration warehouse so ad hoc SQL can be measured separately from scheduled jobs and dbt builds.

## 12) What to Add Once Benchmark Numbers Are Finalized

When measured numbers are ready, expand this report with:

- runtime summary by `run_id`
- total rows processed by job
- mean and percentile batch sizes by job
- DLQ rate by scenario
- estimated cost per million messages by scenario
- v1 versus v2 comparison notes tied to specific design changes

That final section is where the report moves from cost-aware framework to measured cost comparison.
