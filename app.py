#!/usr/bin/env python3
"""Live 3D Flight Tracker — proxies airplanes.live (civil + military)."""
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

# Bounding boxes for filtering global /mil results by region
REGION_BBOX = {
    "middle_east":   (12,  32,  42,  63),
    "europe":        (35, -12,  72,  45),
    "north_america": (24, -125, 50, -66),
    "asia":          (-10, 60,  55, 150),
    "global":        None,
}


def fetch_point(lat, lon):
    url = f"{API_BASE}/point/{lat}/{lon}/{RADIUS}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlightTracker/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    return data.get("ac") or data.get("aircraft") or []


def fetch_mil():
    url = f"{API_BASE}/mil"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlightTracker/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    aircraft = data.get("ac") or data.get("aircraft") or []
    for a in aircraft:
        a["mil"] = True
    return aircraft


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
        bbox   = REGION_BBOX.get(region)

        try:
            seen = {}
            tasks = [("civil", lat, lon) for lat, lon in points]

            with ThreadPoolExecutor(max_workers=12) as ex:
                civil_futs = {ex.submit(fetch_point, lat, lon): None for lat, lon in points}
                mil_fut    = ex.submit(fetch_mil)

                for fut in as_completed(list(civil_futs) + [mil_fut]):
                    is_mil = (fut is mil_fut)
                    try:
                        for a in fut.result():
                            key = a.get("hex") or a.get("icao24")
                            if not key:
                                continue
                            # filter military aircraft by region bbox
                            if is_mil and bbox:
                                lat_a = a.get("lat")
                                lon_a = a.get("lon")
                                if lat_a is None or lon_a is None:
                                    continue
                                lamin, lomin, lamax, lomax = bbox
                                if not (lamin <= lat_a <= lamax and lomin <= lon_a <= lomax):
                                    continue
                            if key not in seen:
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
