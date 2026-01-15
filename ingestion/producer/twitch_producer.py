from dotenv import load_dotenv
import sys
import os
import socket
import json
from kafka import KafkaProducer

load_dotenv()
# Twitch IRC connection setup
server = 'irc.chat.twitch.tv'
port = 6667
nickname = os.getenv("TWITCH_NICK")
token = os.getenv("TWITCH_TOKEN")  # oauth:...
channel = '#k3soju'

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

sock = socket.socket()
sock.connect((server, port))
sock.send(f"PASS {token}\n".encode('utf-8'))
sock.send(f"NICK {nickname}\n".encode('utf-8'))
sock.send(f"JOIN {channel}\n".encode('utf-8'))

# DEBUG: Check the initial response from Twitch
initial_resp = sock.recv(2048).decode('utf-8')
print(f"Twitch Response: {initial_resp}") 

if "Login authentication failed" in initial_resp:
    print("CRITICAL: Your Twitch OAuth token is expired or invalid.")
    sock.close()
    sys.exit(1)
print("Successfully connected to Twitch IRC.")

while True:
    resp = sock.recv(2048).decode('utf-8')
    if resp.startswith('PING'):
        sock.send("PONG\n".encode('utf-8'))
    elif len(resp) > 0:
        if "PRIVMSG" in resp:
            username = resp.split('!', 1)[0][1:]
            message = resp.split('PRIVMSG', 1)[1].split(':', 1)[1]
            data = {'user': username, 'message': message.strip()}
            producer.send('twitch_chat', value=data)
            print(f"Sent: {data}")
