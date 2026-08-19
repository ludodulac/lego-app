# 3D BrickModel viewer (BH-015)

The first viewer is a static browser client under `frontend/`. It consumes the BH-014 export bundle and does not reconstruct architectural geometry.

## Files

- `frontend/index.html` — viewer UI and Three.js import map.
- `frontend/styles.css` — responsive desktop/mobile layout.
- `frontend/viewer.js` — validation, BrickModel rendering, OrbitControls and camera framing.
- `frontend/sample-export.json` — small schema-compatible demo model.

## Run locally

The viewer uses ES modules and `fetch()`, so serve the folder over HTTP rather than opening `index.html` directly from the filesystem.

From the repository root:

```bash
python -m http.server 8000 --directory frontend
```

Then open `http://localhost:8000` in a browser.

## Controls

- left drag / touch drag: orbit;
- wheel / pinch: zoom;
- right drag: pan;
- **Recentrer la vue**: auto-frame the current model;
- **Ouvrir un JSON**: load a local BH-014 export bundle;
- **Recharger l’exemple**: reload `sample-export.json`.

## Rendering conventions

- engine X maps to Three.js X;
- engine Y maps to Three.js Z;
- engine Z (plates) maps to Three.js Y;
- 1 stud = 1 viewer world unit;
- 1 plate = 0.4 viewer world unit;
- canonical dimensions are parsed from M0 ids such as `BRICK_1X6` and rotated using `rotation_quarter_turns`.

## Current limitations

This is a geometry/debug viewer, not the final product UI. Parts are rendered as simple boxes rather than exact supplier meshes. Studs/tubes, realistic roof slopes, colors from the BuildingModel, selection, editing, construction steps and photo workflow are not implemented yet.

The current Three.js dependency is pinned in the import map so the prototype remains reproducible. A later application milestone can move the viewer into the full bundled frontend stack.
