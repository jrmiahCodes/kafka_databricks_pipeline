from kafka import KafkaConsumer, KafkaProducer
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

consumer = KafkaConsumer(
    'twitch_chat',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

analyzer = SentimentIntensityAnalyzer()

for msg in consumer:
    data = msg.value
    sentiment = analyzer.polarity_scores(data['message'])
    enriched = {
        'user': data['user'],
        'message': data['message'],
        'sentiment': sentiment,
    }
    producer.send('twitch_chat_enriched', value=enriched)
    print(f"Processed: {enriched}")
