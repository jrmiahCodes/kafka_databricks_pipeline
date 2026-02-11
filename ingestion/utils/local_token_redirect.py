import http.server
import socketserver
import webbrowser
import urllib.parse
import os

PORT = 3000
CLIENT_ID = os.getenv("CLIENT_ID")  # Replace with your actual Client ID
REDIRECT_URI = f"http://localhost:{PORT}"
SCOPES = "chat:read+chat:edit"

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.fragment:  # The token is in the fragment (#)
            params = urllib.parse.parse_qs(parsed_url.fragment)
            token = params.get('access_token', [''])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2> Token captured! You can close this window.</h2>")
            print(f"\nYour Twitch OAuth Token:\n\noauth:{token}\n")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Waiting for Twitch redirect...</h2>")

def start_server():
    with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
        auth_url = (
            f"https://id.twitch.tv/oauth2/authorize"
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=token"
            f"&scope={SCOPES}"
        )
        print(f"Opening Twitch authorization page:\n{auth_url}\n")
        webbrowser.open(auth_url)
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
