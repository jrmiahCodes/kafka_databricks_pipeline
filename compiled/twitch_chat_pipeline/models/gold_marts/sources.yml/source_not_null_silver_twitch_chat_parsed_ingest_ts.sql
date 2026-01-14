
    
    



select ingest_ts
from "workspace"."twitch_pipeline_silver"."twitch_chat_parsed"
where ingest_ts is null


