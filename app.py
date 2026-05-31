#!/usr/bin/env python3
import http.server
import socketserver
import threading
import webbrowser
import time
import os

PORT = 3000
HOST = "localhost"

os.chdir(os.path.dirname(os.path.abspath(__file__)))

handler = http.server.SimpleHTTPRequestHandler
handler.log_message = lambda *_: None  # silence request logs

with socketserver.TCPServer((HOST, PORT), handler) as httpd:
    url = f"http://{HOST}:{PORT}"
    print(f"  🌍  Live 3D Flight Tracker")
    print(f"  →   {url}")
    print(f"  Ctrl+C to stop\n")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
