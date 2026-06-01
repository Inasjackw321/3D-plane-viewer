# Aircraft 3D models

**You don't need to download or store anything here.** Real aircraft models
now load automatically at runtime from the open-source
[Flightradar24 3D model set](https://github.com/Flightradar24/fr24-3d-models)
(GPL-2), matched to each aircraft's real ICAO type code.

How it works (see `MODEL_FILES`/`modelForType` in `index.html`):

- Each aircraft's type code is mapped to the closest airframe in the FR24 set
  — e.g. **KC-46 → Boeing 767**, **A330 MRTT → A330**, **E-7/P-8 → 737**,
  **KC-135 → narrowbody jet**.
- Fighters, helicopters, and distinctive transports (C-17, C-130, A400M) keep
  their purpose-built procedural shapes, since no airliner model looks right.
- Models are fetched by the browser (CORS-enabled), normalised (centred,
  scaled, nose forward), and cached. Anything without a match falls back to a
  procedural shape, so the app always renders.

To add or change a mapping, edit `MIL_TYPE_MODEL` / `FR24_HAVE` in
`index.html`. The folder is kept only so this note travels with the repo.
