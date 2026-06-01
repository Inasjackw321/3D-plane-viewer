# Aircraft 3D models

Drop downloaded **glTF Binary (`.glb`)** files here using these exact names.
The app loads them at runtime and falls back to the built-in procedural
shapes for any file that is missing or fails to load — so it always works.

| File name        | Aircraft                  | Used for kind |
|------------------|---------------------------|---------------|
| `c17.glb`        | C-17 Globemaster III      | `cargo`       |
| `kc46.glb`       | KC-46A Pegasus            | `tanker`      |
| `e3.glb`         | E-3 Sentry AWACS          | `awacs`       |

## How to get the files from Sketchfab

1. Open the model page (e.g. the C-17 Globemaster III).
2. Click **Download 3D Model** (only available if the author enabled it and
   you are signed in — downloads are subject to each model's license).
3. Choose the **glTF (.glb)** / **Autoconverted format: GLB** option.
4. Rename the downloaded file to the name in the table above and place it in
   this `models/` folder.
5. Reload the page (Ctrl+Shift+R). The downloaded model replaces the
   placeholder shape for that aircraft type.

## Notes

- The loader auto-centers each model, scales it to a consistent size, and
  rotates the longest axis to point "forward". If a model ends up facing the
  wrong way, tweak its `rotDeg: [x, y, z]` entry in `MODEL_FILES` inside
  `index.html` (values in degrees).
- To add more types, add a `models/<name>.glb` file and a matching entry in
  `MODEL_FILES` (keys: `fighter`, `tanker`, `awacs`, `cargo`, `attack_heli`,
  `transport_heli`).
- Large `.glb` files (tens of MB) will slow first load; prefer models under
  ~5 MB where possible.
