



select
    1
from "workspace"."twitch_pipeline_silver"."twitch_chat_parsed"

where not(sent_compound BETWEEN -1.0 AND 1.0)

