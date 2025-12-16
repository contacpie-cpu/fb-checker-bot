from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

def keep_alive():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
