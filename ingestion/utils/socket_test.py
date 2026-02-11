import socket
from dotenv import load_dotenv
import os 

load_dotenv()
# Twitch IRC connection setup
server = 'irc.chat.twitch.tv'
port = 6667
nickname = os.getenv("TWITCH_NICK")
token = os.getenv("TWITCH_TOKEN")  # oauth:...
channel = '#jasontheween'


sock = socket.socket()
sock.connect((server, port))
sock.send(f"PASS {token}\n".encode('utf-8'))
sock.send(f"NICK {nickname}\n".encode('utf-8'))
sock.send(f"JOIN {channel}\n".encode('utf-8'))

while True:
    resp = sock.recv(2048).decode('utf-8')
    if resp.startswith('PING'):
        sock.send("PONG\n".encode('utf-8'))
    elif len(resp) > 0:
        print(resp)