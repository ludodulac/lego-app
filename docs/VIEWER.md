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

BrickHouse canonical coordinates remain authoritative in exports and BOM data: model X runs left→right when looking at the front facade, model Y runs front→rear, and model Z runs bottom→top. The viewer performs a display-only right-handed Three.js mapping:

- engine X maps to Three.js X;
- engine Y maps to **negative** Three.js Z;
- engine Z (plates) maps to Three.js Y;
- the canonical front camera stands on positive Three.js Z, so increasing model X remains screen-left→screen-right;
- this handedness transform is presentation-only and must never rewrite BrickModel placements, BOM coordinates or architectural measurements;
- 1 stud = 1 viewer world unit;
- 1 plate = 0.4 viewer world unit;
- canonical dimensions are parsed from M0 ids such as `BRICK_1X6` and rotated using `rotation_quarter_turns`.

Standard brick-like parts receive cylindrical top studs in the display layer. To keep mobile rendering bounded, large stud fields are suppressed on narrow screens while small parts keep their studs. Sloped roof parts expose their visible top stud row separately. These details never alter BrickModel geometry, BOM quantities or placement coordinates.

Materials use category-specific `MeshStandardMaterial` properties: glazing is transparent with low roughness, timber is rougher, metal carries explicit metalness, and semantic colors clone the same material behavior rather than flattening every category to one generic surface. Assembly highlighting derives faded/current variants from those same category materials.

The viewer frames the rendered meshes themselves rather than treating architectural `width_studs` / `depth_studs` as the complete display canvas. This keeps camera framing compatible with roof overhang and other LEGO representation extents while leaving architectural dimensions semantically unchanged.

## Current limitations

This remains a geometry/debug viewer rather than the final product UI. Bodies are simplified procedural solids rather than exact supplier meshes; underside tubes and internal LEGO geometry are not modeled. Click selection, editing, animation and human-optimized instruction steps are not implemented yet.
