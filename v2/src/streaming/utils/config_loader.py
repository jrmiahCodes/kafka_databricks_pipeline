from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StreamingJobConfig:
    environment: str
    kafka_bootstrap_servers: str
    kafka_raw_topic: str
    kafka_security_protocol: str
    kafka_sasl_mechanism: str
    api_key: str
    api_secret: str
    bronze_table: str
    silver_parsed_table: str
    silver_features_table: str
    dlq_table: str
    bronze_checkpoint: str
    silver_parse_checkpoint: str
    silver_features_checkpoint: str
    silver_dedupe_watermark: str
    enforce_fail_fast: bool

    def kafka_sasl_enabled(self) -> bool:
        return self.kafka_security_protocol.upper().startswith("SASL")

    def kafka_sasl_jaas_config(self) -> str:
        username = self.api_key.replace("\\", "\\\\").replace('"', '\\"')
        password = self.api_secret.replace("\\", "\\\\").replace('"', '\\"')
        return (
            "kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required "
            f'username="{username}" password="{password}";'
        )
    
    def kafka_read_options(self) -> dict[str, str]:
        options = {
            "kafka.bootstrap.servers": self.kafka_bootstrap_servers,
            "subscribe": self.kafka_raw_topic,
            "startingOffsets": "earliest",
        }
        if self.kafka_sasl_enabled():
            options.update(
                {
                    "kafka.security.protocol": self.kafka_security_protocol,
                    "kafka.sasl.mechanism": self.kafka_sasl_mechanism,
                    "kafka.sasl.jaas.config": self.kafka_sasl_jaas_config(),
                    "kafka.ssl.endpoint.identification.algorithm": "https",
                }
            )
        return options


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def load_streaming_config() -> StreamingJobConfig:
    
    kafka_security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL").strip()
    kafka_sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN").strip()
    api_key = ""
    api_secret = ""

    if kafka_security_protocol.upper().startswith("SASL"):
        api_key = _require_env("API_KEY")
        api_secret = _require_env("API_SECRET")

    return StreamingJobConfig(
        environment=os.getenv("APP_ENV", "dev"),
        kafka_bootstrap_servers=_require_env("KAFKA_BOOTSTRAP_SERVERS"),
        kafka_raw_topic=os.getenv("KAFKA_RAW_TOPIC", "twitch_chat_raw"),
        kafka_security_protocol=kafka_security_protocol,
        kafka_sasl_mechanism=kafka_sasl_mechanism,
        api_key=api_key,
        api_secret=api_secret,
        bronze_table=os.getenv("BRONZE_TABLE", "twitch_pipeline.bronze.bronze_chat_raw"),
        silver_parsed_table=os.getenv("SILVER_PARSED_TABLE", "twitch_pipeline.silver.silver_chat_parsed"),
        silver_features_table=os.getenv("SILVER_FEATURES_TABLE", "twitch_pipeline.silver.silver_chat_features"),
        dlq_table=os.getenv("DLQ_TABLE", "twitch_pipeline.silver.chat_dlq"),
        bronze_checkpoint=_require_env("BRONZE_CHECKPOINT"),
        silver_parse_checkpoint=_require_env("SILVER_PARSE_CHECKPOINT"),
        silver_features_checkpoint=_require_env("SILVER_FEATURES_CHECKPOINT"),
        silver_dedupe_watermark=os.getenv("SILVER_DEDUPE_WATERMARK", "2 hours"),
        enforce_fail_fast=_bool_env("ENFORCE_FAIL_FAST", True),
    )
