





with validation_errors as (

    select
        topic, partition, offset
    from "workspace"."twitch_pipeline_silver"."twitch_chat_parsed"
    group by topic, partition, offset
    having count(*) > 1

)

select *
from validation_errors


