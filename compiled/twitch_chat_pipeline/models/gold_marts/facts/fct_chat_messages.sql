

select
    md5(cast(coalesce(cast(topic as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(partition as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(offset as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as message_id,

    topic,
    partition,
    offset,

    user,
    message,

    sent_neg,
    sent_neu,
    sent_pos,
    sent_compound,

    message_length,
    entropy,
    is_emote_only,
    emote_count,
    repeat_char_ratio,
    alpha_ratio,
    engagement_flag,

    case
    when is_emote_only then 'EMOTE_ONLY'
    when message_length < 3 or entropy < 0.8 then 'LOW_EFFORT'
    when repeat_char_ratio >= 0.7 then 'REPETITIVE_SPAM'
    when engagement_flag then 'ENGAGED_CHAT'
    else 'OTHER'
    end as message_type,

    kafka_timestamp,
    ingest_ts

from "workspace"."twitch_pipeline_silver"."twitch_chat_parsed"