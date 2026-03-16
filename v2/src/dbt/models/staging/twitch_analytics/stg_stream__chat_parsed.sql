

event_id
source_topic
source_partition
source_offset
event_ts
bronze_ingestion_ts
silver_processed_ts
channel
chatter_id
message_text
message_text_normalized
message_length
source_platform

source {{ ref('silver_chat_parsed') }}
