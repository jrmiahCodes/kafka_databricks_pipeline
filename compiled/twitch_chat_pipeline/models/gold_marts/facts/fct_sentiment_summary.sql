

with base as (
    select
        topic,
        date(kafka_timestamp) as message_date,
        sent_compound
    from "memory"."main"."fct_chat_messages"
)

select
    topic,
    message_date,

    count(*) as total_messages,

    sum(case when sent_compound >  0.05 then 1 else 0 end) as positive_messages,
    sum(case when sent_compound < -0.05 then 1 else 0 end) as negative_messages,
    sum(case when sent_compound between -0.05 and 0.05 then 1 else 0 end) as neutral_messages,

    round(
        sum(case when sent_compound > 0.05 then 1 else 0 end) * 1.0 / count(*),
        4
    ) as pct_positive,

    round(
        sum(case when sent_compound < -0.05 then 1 else 0 end) * 1.0 / count(*),
        4
    ) as pct_negative

from base
group by topic, message_date