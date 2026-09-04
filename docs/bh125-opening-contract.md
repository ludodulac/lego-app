# BH-125 — architectural opening representation contract

A known architectural window is an architectural anchor before it is a LEGO detail.

The derived wall raster must preserve its void before wall fill. The LEGO representation then has three explicit outcomes:

1. a validated frame/pane assembly represents the opening;
2. joinery-free glazing represents a simple opening without inventing subdivisions;
3. the opening remains an explicit void and the export receives a `lego_architectural_window_unrepresented` blocker when known composition cannot be represented by the validated vocabulary.

The third outcome is intentionally not converted into a blind wall and does not invent mullions, transoms, panes, or dimensions. Source BuildingModel/ArchitecturalScene geometry remains immutable.

Window parts carry `opening_id` provenance into BrickModel so downstream fidelity checks and the viewer can trace the representation back to the architectural opening.
