#!/usr/bin/env python3
"""
Live 3D Flight Tracker
Fetches all aircraft from adsb.fi and filters by bounding box server-side.
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

ADSB_FI = "https://api.adsb.fi/v1/flights"

# (lat-min, lon-min, lat-max, lon-max)
BBOXES = {
    "middle_east":   (12,  32,  42,  63),
    "europe":        (35, -12,  72,  45),
    "north_america": (24, -125, 50, -66),
    "asia":          (-10, 60,  55, 150),
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
        bbox   = BBOXES.get(region)

        try:
            req = urllib.request.Request(
                ADSB_FI,
                headers={"User-Agent": "FlightTracker/1.0",
                         "Accept":     "application/json"},
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = json.loads(resp.read())

            # adsb.fi returns { "aircraft": [...] } or { "ac": [...] }
            aircraft = raw.get("aircraft") or raw.get("ac") or []

            if bbox:
                lamin, lomin, lamax, lomax = bbox
                aircraft = [
                    a for a in aircraft
                    if isinstance(a.get("lat"), (int, float))
                    and isinstance(a.get("lon"), (int, float))
                    and lamin <= a["lat"] <= lamax
                    and lomin <= a["lon"] <= lomax
                ]

            out = json.dumps({"aircraft": aircraft}).encode()
            code = 200
        except Exception as e:
            out  = json.dumps({"error": str(e), "aircraft": []}).encode()
            code = 200

        self.send_response(code)
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
