# 3D BrickModel viewer

The viewer is a static browser client under `frontend/`. It consumes the BrickHouse export bundle and does not reconstruct architectural geometry.

## Files

- `frontend/index.html` — viewer UI and Three.js import map.
- `frontend/styles.css` — responsive desktop/mobile layout.
- `frontend/viewer.js` — validation, BrickModel rendering, OrbitControls, camera framing and assembly playback.
- `frontend/sample-export.json` — sample bundle; the Pages workflow regenerates it from the reference BuildingModel before deployment.

## Run locally

The viewer uses ES modules and `fetch()`, so serve the folder over HTTP rather than opening `index.html` directly from the filesystem.

```bash
python -m http.server 8000 --directory frontend
```

Then open `http://localhost:8000`.

## Controls

- left/touch drag: orbit;
- wheel/pinch: zoom;
- right drag: pan;
- **Recentrer la vue**: auto-frame the current model;
- **Ouvrir un JSON**: load a local export bundle;
- **Recharger l’exemple**: reload `sample-export.json`.

When an `assembly_plan` is present, an additional mounting card appears with a slider, previous/next controls and a full-model button. At a selected step, all parts referenced by that step and every previous step are visible; later parts are hidden. Older bundles without `assembly_plan` remain compatible and simply show the complete model.

## Rendering conventions

- engine X maps to Three.js X;
- engine Y maps to Three.js Z;
- engine Z (plates) maps to Three.js Y;
- 1 stud = 1 viewer world unit;
- 1 plate = 0.4 viewer world unit;
- canonical dimensions are parsed from M0 ids such as `BRICK_1X6` and rotated using `rotation_quarter_turns`.

## Current limitations

This remains a geometry/debug viewer rather than the final product UI. Parts are boxes rather than exact supplier meshes. Studs/tubes, realistic roof slopes, click selection, editing, animation and human-optimized instruction steps are not implemented yet.
