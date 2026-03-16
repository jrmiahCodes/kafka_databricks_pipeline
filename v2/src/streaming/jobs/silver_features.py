from __future__ import annotations

from typing import Any

from streaming.utils.config_loader import StreamingJobConfig, load_streaming_config
from streaming.utils.logging import get_logger

LOGGER = get_logger("streaming.silver_features")


def build_feature_dataframe(spark: Any, cfg: StreamingJobConfig) -> Any:
    """Build lightweight real-time features from canonical parsed Silver events.

    Notes:
    - This job assumes `silver_parsed_table` is already contract-valid and deduplicated on `event_id`.
    - No dedupe/merge logic is implemented here by design (handled upstream in `silver_parse`).
    - Output is intentionally narrow: `event_id` + derived feature columns only.
    - Features are cheap heuristics for moderation support, engagement summaries, and downstream Gold metrics.
    - Heavier ML/LLM scoring (including true emote semantics) is intentionally deferred.
    """

    from pyspark.sql import functions as F

    silver = spark.readStream.table(cfg.silver_parsed_table)

    # `message_length` is the canonical parsed-contract field from upstream Silver parse.
    # `message_len` is a local trimmed length used for feature math in this job.
    message_clean = F.trim(F.col("message_text"))
    message_lower = F.lower(message_clean)
    message_len = F.length(message_clean)
    alpha_char_count = F.length(F.regexp_replace(message_clean, r"[^A-Za-z]", ""))
    numeric_char_count = F.length(F.regexp_replace(message_clean, r"[^0-9]", ""))
    token_count = F.when(message_len > 0, F.size(F.split(message_clean, r"\s+"))).otherwise(F.lit(0))

    link_count = F.greatest(F.size(F.split(message_lower, "http")) - F.lit(1), F.lit(0))

    # Token-shape heuristic only; this is not true Twitch emote dictionary/model resolution.
    candidate_tokens_clean = F.trim(F.regexp_replace(message_clean, r"[^A-Za-z0-9_]+", " "))
    candidate_emote_token_count = F.when(
        F.length(candidate_tokens_clean) > 0,
        F.size(F.split(candidate_tokens_clean, r"\s+")),
    ).otherwise(F.lit(0))

    collapsed_repeats = F.regexp_replace(message_clean, r"(.)\\1+", r"$1")
    repeated_extra_chars = message_len - F.length(collapsed_repeats)
    repeat_char_ratio = F.when(message_len > 0, repeated_extra_chars / message_len).otherwise(F.lit(0.0))
    text_complexity_proxy = F.when(message_len > 0, alpha_char_count / message_len).otherwise(F.lit(0.0))

    return silver.select(
        "event_id",
        token_count.alias("token_count"),
        alpha_char_count.alias("alpha_char_count"),
        numeric_char_count.alias("numeric_char_count"),
        link_count.alias("link_count"),
        candidate_emote_token_count.alias("candidate_emote_token_count"),
        repeat_char_ratio.alias("repeat_char_ratio"),
        text_complexity_proxy.alias("text_complexity_proxy"),
        F.when(F.col("event_ts").isNotNull(), (F.current_timestamp().cast("long") - F.col("event_ts").cast("long")).cast("int"))
        .otherwise(F.lit(None).cast("int"))
        .alias("event_to_feature_latency_seconds"),
        # Heuristic spam signal; explicit thresholding for operational readability.
        F.when((repeat_char_ratio >= F.lit(0.7)) | message_lower.rlike(r"(.)\\1{4,}"), F.lit(True))
        .otherwise(F.lit(False))
        .alias("has_repeat_spam_pattern"),
        F.when(
            (F.col("message_length") >= F.lit(2))
            & (text_complexity_proxy >= F.lit(0.3))
            & (repeat_char_ratio < F.lit(0.7)),
            F.lit(True),
        )
        .otherwise(F.lit(False))
        .alias("engagement_signal"),
        F.current_timestamp().alias("feature_processed_ts"),
    )


def run(spark: Any | None = None) -> Any:
    cfg = load_streaming_config()

    if spark is None:
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.appName("v2_silver_features").getOrCreate()

    feature_df = build_feature_dataframe(spark, cfg)

    LOGGER.info(
        "silver_features_start",
        extra={"context": {"table": cfg.silver_features_table, "expects_canonical_silver": True}},
    )

    return (
        feature_df.writeStream.format("delta")
        .trigger(availableNow=True)
        .outputMode("append")
        .option("checkpointLocation", cfg.silver_features_checkpoint)
        .toTable(cfg.silver_features_table)
    )
