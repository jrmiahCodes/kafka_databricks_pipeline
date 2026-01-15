# 🎥 Twitch Chat Data Pipeline — Real-Time Analytics with Kafka & Snowflake

## 🧭 Overview
This project implements a **real-time data pipeline** that ingests Twitch chat messages, enriches them, and loads them into **Snowflake** for downstream analytics. The pipeline is built with a modular, cloud-ready architecture using **Python, Apache Kafka, and Snowflake’s Kafka Connector**.

It demonstrates modern **data engineering principles** including streaming ingestion, schema evolution, event-driven processing, and secure role-based access control — designed to showcase end-to-end technical competency for a **data engineering or analytics engineering portfolio**.

---

## 🌟 Project Goals

- Build a **real-time ingestion pipeline** from the Twitch API (chat messages, metadata, etc.).
- Use **Kafka** as the message broker to decouple ingestion, transformation, and storage layers.
- Implement **Snowflake Kafka Sink Connector** for continuous, fault-tolerant loading into Snowflake.
- Enrich messages with contextual data (timestamps, channel info, message metadata).
- Store raw and enriched data in **structured Snowflake tables** for analytical queries and dashboards.
- Employ **secure Snowflake role hierarchy** for service accounts and downstream transformations.
- Showcase **production-level observability, modular code structure, and CI-ready architecture**.

---

## 🛠️ Architecture Overview

### Data Flow Summary
- Twitch chat messages are captured using a Python-based producer.
- Raw messages are published to a Kafka topic (`twitch_chat_raw`).
- A Python consumer enriches messages with metadata and sentiment analysis before writing them to another topic (`twitch_chat_enriched`).
- Kafka Connect with the **Snowflake Sink Connector** streams enriched messages directly into Snowflake tables.
- Snowflake acts as the analytics layer, with data modeled into **RAW**, **STAGE**, and **ANALYTICS** schemas.

---

## 🥢 Components

### 1. **Python Ingestion Layer**
- Authenticates with Twitch OAuth.
- Listens to chat messages via IRC or EventSub API.
- Publishes messages to Kafka (`twitch_chat_raw`).

### 2. **Kafka Ecosystem**
- **Kafka Broker** manages message queues.
- **Kafka Connect Worker** handles sink connector plugins.
- **Snowflake Sink Connector** streams topic data directly into Snowflake.

### 3. **Snowflake Warehouse**
- Securely stores data with fine-grained role and schema control.
- Data modeled into:
  - `RAW.TWITCH_CHAT_RAW`
  - `STAGE.TWITCH_CHAT_ENRICHED`
  - `ANALYTICS.CHAT_FEATURES`

### 4. **Access & Security**
- Dedicated Snowflake roles:
  - `PIPELINE_ROLE`: Kafka → Snowflake ingestion
  - `DBT_ROLE`: downstream transformations
  - `ANALYST_ROLE`: read-only query access
- Supports **keypair authentication** for service accounts.

---

## 🧩 Observability & Validation

To monitor connector health:
```bash
curl http://localhost:8083/connectors
curl http://localhost:8083/connectors/snowflake-sink-twitch/status
```

To check data ingestion in Snowflake:
```sql
USE DATABASE TWITCH_DB;
USE SCHEMA RAW;
SELECT * FROM TWITCH_CHAT_RAW LIMIT 10;
```

---

## 🧪 Skills Demonstrated

| Category | Tools / Concepts |
|-----------|------------------|
| **Data Ingestion** | Twitch API, OAuth, Python |
| **Streaming** | Apache Kafka, Kafka Connect |
| **Data Warehousing** | Snowflake (Raw → Stage → Analytics layers) |
| **ETL/ELT** | Python producers, DBT-style modeling |
| **Security** | Role-based access, keypair auth |
| **Infrastructure** | Kafka setup, connector orchestration |
| **Monitoring** | REST API health checks, Connect logs |
| **Resume Focus** | End-to-end streaming pipeline in modern data stack |

---

## 📈 Future Enhancements
- Add **dbt transformations** to automate staging models.
- Build a **Streamlit dashboard** using Snowflake data.
- Deploy ingestion app on a **cloud VM or container**.
- Introduce **Kafka Streams or Flink** for real-time aggregations.

---

## 🗾 Summary
This project demonstrates the ability to:
- Build and orchestrate a **real-time, event-driven data pipeline**.
- Integrate Python, Kafka, and Snowflake in a **production-style workflow**.
- Manage authentication, roles, and schema design securely.
- Deliver measurable, portfolio-ready results suitable for a **data engineering or analytics engineering** role.

---

**Author:** Jeremiah Garcia  
**Purpose:** Professional portfolio project (Data Engineering / Analytics Engineering)

