# Twitch Chat Streaming Analytics Pipeline

## Overview
This project implements an end-to-end **real-time data pipeline** for ingesting, processing, and analyzing Twitch chat messages using a modern lakehouse architecture.

The pipeline demonstrates:
- Kafka-based streaming ingestion
- Spark Structured Streaming with `foreachBatch`
- Bronze / Silver data contracts
- dbt-based testing and Gold modeling
- Databricks-native orchestration and dashboards

The primary goal of this project is to showcase **streaming ingestion correctness, data contracts, goverance and analytical modeling**, rather than purely batch ETL.
I've showcased SQL and data modeling in other projects, the Databricks dashboard and dbt models were less important than streaming ingestion and configuring kafka in general.

---

## Architecture
Kafka → Spark Structured Streaming → Delta Lake (Bronze/Silver)
→ dbt (Gold models + tests)
→ Databricks Dashboards

### Key Technologies
- **Kafka** – real-time message ingestion
- **Spark Structured Streaming** – micro-batch processing
- **Delta Lake** – transactional storage
- **Databricks** – execution, orchestration, visualization
- **dbt** – testing, transformations, lineage

---

## Data Layers

### Bronze: Raw Ingestion
- One row per Kafka message
- Append-only Delta table
- Stores raw JSON payload
- Tracks:
  - topic
  - partition
  - offset
  - ingest timestamp
  - parse_status (`OK` / `PARSE_ERROR`)
  - parse_error message

Bronze guarantees **lossless ingestion** and **replayability**.

Bronze stores the raw, immutable Kafka event log.
Each Kafka message is represented once, identified by (topic, partition, offset).

Data is ingested in an append-first manner, with idempotent MERGE semantics used to:

  - Prevent duplicate inserts during streaming retries

  - Annotate records with operational metadata (parse_status, parse_error)

The raw payload itself is never modified after ingestion.
---

### Silver: Parsed & Enriched
- Only successfully parsed messages
- JSON fields extracted into columns
- Enriched with:
  - sentiment scores
  - message length
  - entropy
  - emote metrics
  - engagement flag

The Silver schema represents a **locked data contract**:
- `topic + partition + offset` uniquely identify a message
- All downstream consumers rely on this contract

---

### Gold: Analytics Models (dbt)
Gold models are built using dbt and materialized as fact and dimension tables.

Examples:
- Sentiment distribution over time
- Message volume by minute
- Engagement vs non-engagement messages
- Emote-only message analysis

Gold models are optimized for **dashboarding and BI consumption**.

---

## Data Quality & Contracts

Data quality is enforced at multiple layers:

### Ingestion-time
- Schema enforcement via `from_json`
- Explicit `parse_status` handling
- Idempotent MERGE logic for updates

### dbt Tests
- Not-null constraints
- Range checks for sentiment scores
- Uniqueness across `(topic, partition, offset)`
- Semantic expectations on Silver tables

---

## Orchestration

- Streaming ingestion runs continuously via Spark Structured Streaming
- dbt models are executed as a **Databricks Job**
- dbt project is stored in a **Git-backed Databricks Repo**
- dbt commands:
  dbt run
  dbt test

## Documentation & Lineage

- dbt provides logical lineage and documentation
- Unity Catalog tracks physical lineage and table usage
- A Github Actions workflow was setup to deploy the dbt docs as a gh-page and merge to main branch on every commit.
  - This allows you to view always updated dbt docs and saves time in the long run by automating this process.
 
## Key Learnings

- Streaming pipelines require explicit idempotency handling
  - A key moment was figuring out that Structured Streaming guarantees at-least once execution:
    That led to 2 key discoveries; the use of .cache() or .persist() so that in the event of a Spark retry, it re-reads the data it
    already has cached without having to impact performance. The 2nd discovery is that if there are intensive actions during the
    foreachBatch like I created with Spark silver enrichment, Spark is prone to replay all the actions and that led to data duplication
    when using .append. To combat this, we use MERGE semantics to guarantee an exactly-one effect. 

- dbt integrates cleanly with Databricks for testing and modeling

- Running Kafka locally was a huge pain fraught with a ton of debugging. At first this project was using Snowflake and I configured a Snowflake sink.
  Then when I switch over to databricks, it turns out you cannot actually use your local machine as the point of ingestion. Which eludicated me to
  the necessity of Confluent Cloud or other managed systems for Kafka. The workaround for this was using a public DNS as a Kafka advertised listener,
  pointing Databricks to that, forwarding my ports to let Databricks connect and doing a historical one time dump before closing everything back up.
  A security risk and not ideal for streaming setups.

## Future Improvements

**Quite a few future improvements and ideas having worked through this project:**
  - Using a python consumer isn't the best for throughput, 


## Author

Built by Jeremiah Garcia as a portfolio project focused on real-time data engineering, Kafka with Spark streaming ingestion and lakehouse architecture.
