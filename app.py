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
import time

PORT = 3000
HOST = "localhost"

API_BASE = "https://api.airplanes.live/v2"
RADIUS   = 250  # nautical miles (API maximum)
# airplanes.live enforces ~1 request/second per IP. Bursting past it gets the
# IP temporarily blocked (HTTP 403), so we serialise upstream calls and keep at
# least this gap between request starts.
RATE_LIMIT_S = 1.05
_rate_lock = threading.Lock()
_last_req  = [0.0]


def _throttle():
    """Block until at least RATE_LIMIT_S has passed since the last request."""
    with _rate_lock:
        wait = RATE_LIMIT_S - (time.monotonic() - _last_req[0])
        if wait > 0:
            time.sleep(wait)
        _last_req[0] = time.monotonic()

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
    _throttle()
    url = f"{API_BASE}/point/{lat}/{lon}/{RADIUS}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlightTracker/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    return data.get("ac") or data.get("aircraft") or []


def fetch_mil():
    _throttle()
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
    # Serve locally-stored 3D model files with correct MIME types.
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".glb":  "model/gltf-binary",
        ".gltf": "model/gltf+json",
    }

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
            n_ok, n_fail, last_err = 0, 0, None

            # Fetch sequentially. fetch_point / fetch_mil each call _throttle(),
            # so requests are paced to airplanes.live's ~1 req/sec limit and the
            # IP is never blocked for bursting.
            jobs = [(False, lambda la=la, lo=lo: fetch_point(la, lo)) for la, lo in points]
            jobs.append((True, fetch_mil))

            for is_mil, fn in jobs:
                try:
                    result = fn()
                    n_ok += 1
                except Exception as fe:
                    n_fail += 1
                    last_err = fe
                    continue
                for a in result:
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
                    # Military version always wins: an aircraft seen on the civil
                    # endpoint first (without mil=True) must not block the mil
                    # endpoint from tagging it later.
                    if key not in seen or (is_mil and not seen[key].get("mil")):
                        seen[key] = a

            payload = {"aircraft": list(seen.values()), "sources_ok": n_ok, "sources_failed": n_fail}
            # If every upstream fetch failed, the data source is unreachable —
            # surface that instead of silently returning an empty list.
            if n_ok == 0 and n_fail > 0:
                code = getattr(last_err, "code", None)
                detail = f"HTTP {code}" if code else type(last_err).__name__
                payload["error"] = f"Flight data source unreachable ({detail})"
            out = json.dumps(payload).encode()
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
