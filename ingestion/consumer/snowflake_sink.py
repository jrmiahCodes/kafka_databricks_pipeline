from kafka import KafkaConsumer
import json
import snowflake.connector
import os

# Connect to Snowflake
conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse="COMPUTE_WH",
    database="TWITCH_DB",
    schema="RAW"
)
cursor = conn.cursor()

consumer = KafkaConsumer(
    'twitch_chat_enriched',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for msg in consumer:
    data = msg.value
    cursor.execute("""
        INSERT INTO TWITCH_CHAT_RAW (USERNAME, MESSAGE, COMPOUND_SCORE, SENTIMENT_JSON)
        VALUES (%s, %s, %s, %s)
    """, (
        data['user'],
        data['message'],
        data['sentiment']['compound'],
        json.dumps(data['sentiment'])
    ))
    conn.commit()
