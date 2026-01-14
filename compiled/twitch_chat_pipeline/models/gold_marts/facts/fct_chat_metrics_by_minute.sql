

select
    date_trunc('minute', kafka_timestamp) as minute,

    -- volume
    count(*) as message_count,

    -- sentiment
    avg(sent_compound) as avg_sentiment,
    sum(case when sent_compound >  0.05 then 1 else 0 end) as positive_messages,
    sum(case when sent_compound < -0.05 then 1 else 0 end) as negative_messages,
    sum(case when sent_compound between -0.05 and 0.05 then 1 else 0 end) as neutral_messages,

    -- engagement
    sum(case when engagement_flag then 1 else 0 end) as engaged_messages,
    avg(cast(engagement_flag as int)) as engagement_rate,

    -- behavior
    sum(case when is_emote_only then 1 else 0 end) as emote_only_messages,
    avg(message_length) as avg_message_length

from "workspace"."twitch_pipeline_silver"."twitch_chat_parsed"
group by 1