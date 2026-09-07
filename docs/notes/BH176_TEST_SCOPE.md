# BH-176 automated test scope

The added tests cover the production boundary rather than source-string wiring:

- semantic preservation for WINDOW / DOOR / UNKNOWN;
- validated frame/pane part IDs only for planned framed glazing;
- `opening_id` provenance in BrickModel;
- explicit blocker for a known unsupported window composition;
- plan footprint applied before spatial wall infill;
- Scene pipeline does not replace a planned glazed UNKNOWN opening with legacy BRICK_1X1 cells;
- structured glass blocks stay outside framed motifs and keep their dedicated material path;
- source BuildingModel / ArchitecturalScene objects remain unchanged.
