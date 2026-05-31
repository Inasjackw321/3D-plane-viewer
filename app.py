#!/usr/bin/env python3
"""
Live 3D Flight Tracker
Serves the app and proxies OpenSky API calls server-side (avoids browser CORS).
"""
import http.server
import socketserver
import threading
import webbrowser
import urllib.request
import urllib.parse
import json
import os

PORT = 3000
HOST = "localhost"

# Bounding boxes: (lamin, lomin, lamax, lomax)
REGIONS = {
    "middle_east":   (12,  32,  42,  63),
    "europe":        (35, -12,  72,  45),
    "north_america": (24, -125, 50, -66),
    "asia":          (-10, 60,  55, 150),
    "global":        None,
}

OPENSKY = "https://opensky-network.org/api/states/all"


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/flights"):
            self._proxy()
        else:
            super().do_GET()

    def _proxy(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        region = params.get("region", ["global"])[0]
        bbox   = REGIONS.get(region)

        url = OPENSKY
        if bbox:
            url += f"?lamin={bbox[0]}&lomin={bbox[1]}&lamax={bbox[2]}&lomax={bbox[3]}"

        try:
            req  = urllib.request.Request(url, headers={"User-Agent": "FlightTracker/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            code = 200
        except Exception as e:
            data = json.dumps({"error": str(e), "states": []}).encode()
            code = 200  # let JS handle the empty states gracefully

        self.send_response(code)
        self.send_header("Content-Type",  "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass  # silence per-request logs


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded so the proxy fetch doesn't block static-file serving."""
    daemon_threads     = True
    allow_reuse_address = True


os.chdir(os.path.dirname(os.path.abspath(__file__)))

with ThreadedServer((HOST, PORT), Handler) as httpd:
    url = f"http://{HOST}:{PORT}"
    print(f"\n  ✈  Live 3D Flight Tracker")
    print(f"  →  {url}")
    print(f"  Ctrl+C to stop\n")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
