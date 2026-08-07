# Flight Tracker 3D

A real-time 3D flight tracker. A small Python server proxies live ADS-B data
from [airplanes.live](https://airplanes.live) and serves a WebGL globe
(MapLibre GL + Three.js) that renders every military aircraft as an animated
low-poly 3D model at its true altitude.

## Run

No dependencies — pure Python standard library.

```bash
python3 app.py
```

Then open <http://localhost:3000> (it opens automatically).

Options:

```bash
python3 app.py --port 8080      # listen on a different port
python3 app.py --host 0.0.0.0   # expose on your LAN
python3 app.py --no-browser     # don't auto-open the browser
```

## Features

- **Animated 3D models** — spinning helicopter/tandem/prop rotors, glowing
  engine exhausts, dark glass canopies, and blinking navigation + strobe lights.
  Metallic PBR materials with image-based reflections.
- **True altitude** — aircraft sit at their real height above the map with a
  vertical altitude line to the ground; climb/descend as the data updates.
- **Bank into turns** — fixed-wing aircraft roll into their turns based on
  heading change.
- **Type classification** — fighters, tankers, AWACS/ISR, cargo/airlift, and
  attack/transport helicopters, each colour-coded and filterable.
- **Heading prediction** — dashed forward-projection of where each aircraft
  will be in ~4 minutes.
- **Search** — find any aircraft by callsign, type, registration or hex.
- **Aircraft list** — live sortable panel of everything airborne; click to fly to.
- **Follow mode** — lock the camera onto one aircraft.
- **Time-of-day** — a sun slider relights the whole scene from dawn to dusk.
- **Night mode** — swap satellite imagery for a dark basemap.
- **Regions** — Middle East, Europe, N. America, Asia-Pacific, Global.

### Keyboard shortcuts

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `L` | Labels | `A` | Rotor animation |
| `T` | Trails | `G` | Navigation lights |
| `S` | Altitude lines | `F` | Aircraft list |
| `P` | Prediction lines | `N` | Night mode |
| `D` | Tag detail | `/` | Focus search |
| `+ / -` | Zoom | `Esc` | Close panels / unfollow |

## How it works

- `app.py` — threaded HTTP server. Serves the static page and proxies
  `/api/flights?region=…`, fanning out to several airplanes.live sampling
  points plus the `/mil` feed, de-duplicating by ICAO hex. Requests are
  **rate-limited to ~1/second** (airplanes.live's limit) and results are
  **cached** for a few seconds; the last good result is served if the upstream
  briefly fails.
- `index.html` — the entire client: MapLibre satellite globe with a custom
  Three.js layer that draws each aircraft as a fixed-pixel 3D icon (so models
  never balloon when zooming), procedural airframes plus optional real glTF
  models in `assets/`.

## Data

Live data © [airplanes.live](https://airplanes.live). Be considerate of their
free API — the built-in rate limiting keeps you within their ~1 request/second
policy so your IP doesn't get blocked.
