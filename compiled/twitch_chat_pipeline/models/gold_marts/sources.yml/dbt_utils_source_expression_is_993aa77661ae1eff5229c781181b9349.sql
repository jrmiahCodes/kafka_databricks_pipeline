



select
    1
from "workspace"."twitch_pipeline_silver"."twitch_chat_parsed"

where not(message_length > 0)

