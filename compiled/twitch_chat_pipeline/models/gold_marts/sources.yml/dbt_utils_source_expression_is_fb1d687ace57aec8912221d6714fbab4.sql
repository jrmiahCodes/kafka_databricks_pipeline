



select
    1
from "workspace"."twitch_pipeline_silver"."twitch_chat_parsed"

where not(sent_neg BETWEEN 0.0 AND 1.0)

