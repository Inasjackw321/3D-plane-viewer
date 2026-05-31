#!/usr/bin/env python3
"""
Live 3D Flight Tracker
Proxies adsb.fi (free, no auth) to avoid browser CORS restrictions.
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

ADSB_FI = "https://api.adsb.fi/v1"

# Center + radius (nautical miles) per region
REGIONS = {
    "middle_east":   (27,  45,  1500),
    "europe":        (51,  13,  1800),
    "north_america": (38, -95,  2200),
    "asia":          (30, 110,  2200),
    "global":        None,
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/flights"):
            self._proxy()
        else:
            super().do_GET()

    def _proxy(self):
        qs     = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        region = qs.get("region", ["global"])[0]
        rp     = REGIONS.get(region)

        if rp:
            lat, lng, radius = rp
            url = f"{ADSB_FI}/aircraft?lat={lat}&lng={lng}&radius={radius}"
        else:
            url = f"{ADSB_FI}/flights"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "FlightTracker/1.0",
                         "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            code = 200
        except Exception as e:
            data = json.dumps({"error": str(e), "aircraft": []}).encode()
            code = 200

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads      = True
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
