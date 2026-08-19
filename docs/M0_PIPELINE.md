# M0 end-to-end pipeline

BH-016 connects the deterministic M0 engine into one command.

## Reference command

From the repository root after installing the project:

```bash
pip install -e ".[dev]"
brickhouse-m0 docs/examples/building-model-simple-house.json frontend/sample-export.json --front-width-studs 48
```

Equivalent module invocation:

```bash
python -m brickhouse.pipeline docs/examples/building-model-simple-house.json frontend/sample-export.json --front-width-studs 48
```

## Pipeline

`BuildingModel JSON -> BuildingModel -> BuildingGeometry -> BuildingBrickShell -> SpatialBrickShell + SpatialRoof -> BrickModel -> BOM -> BrickExportBundle JSON`

The input building remains metric until the shared-scale brick-shell stage. The target front width controls the M0 model scale; all other wall spans use that same scale.

## Current M0 constraints

- exactly one rectangular volume for brick-shell generation;
- gable roof required for the full reference pipeline;
- canonical supplier-independent parts;
- stepped abstract roof representation;
- no photo analysis yet.

The output bundle is the contract consumed by the static browser viewer in `frontend/`.
