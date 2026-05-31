#!/usr/bin/env python3
"""Live 3D Flight Tracker — proxies airplanes.live to avoid browser CORS."""
import http.server
import socketserver
import threading
import webbrowser
import urllib.request
import urllib.parse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

PORT = 3000
HOST = "localhost"

API_BASE = "https://api.airplanes.live/v2"
RADIUS   = 250  # nautical miles (API maximum)

# Multiple sampling points per region so 250 nm circles give good coverage
REGION_POINTS = {
    "middle_east":   [(27, 45), (24, 55), (33, 44), (35, 51), (30, 31)],
    "europe":        [(51,  0), (50,  8), (49,  2), (40, -4), (41, 12), (52, 21)],
    "north_america": [(41, -74), (42, -88), (33, -97), (34, -118), (33, -84)],
    "asia":          [(40, 116), (35, 139), ( 1, 103), (19,  73), (14, 101)],
    "global":        [(27, 45), (51, 0), (41, -74), (40, 116), (35, 139),
                      (-34, 151), (1, 103), (-23, -46), (60, 30), (-26, 28)],
}


def fetch_point(lat, lon):
    url = f"{API_BASE}/point/{lat}/{lon}/{RADIUS}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FlightTracker/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    return data.get("ac") or data.get("aircraft") or []


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/flights"):
            self._proxy()
        else:
            super().do_GET()

    def _proxy(self):
        qs     = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        region = qs.get("region", ["global"])[0]
        points = REGION_POINTS.get(region, REGION_POINTS["global"])

        try:
            seen = {}
            with ThreadPoolExecutor(max_workers=10) as ex:
                futures = {ex.submit(fetch_point, lat, lon): (lat, lon)
                           for lat, lon in points}
                for fut in as_completed(futures):
                    try:
                        for a in fut.result():
                            key = a.get("hex") or a.get("icao24")
                            if key and key not in seen:
                                seen[key] = a
                    except Exception:
                        pass
            out = json.dumps({"aircraft": list(seen.values())}).encode()
        except Exception as e:
            out = json.dumps({"error": str(e), "aircraft": []}).encode()

        self.send_response(200)
        self.send_header("Content-Type",  "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(out)

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
