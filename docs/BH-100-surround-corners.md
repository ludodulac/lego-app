# BH-100 — Architectural surround corner coverage

Decorative opening surrounds are represented as an evidence-backed ring outside the glazing void. The source `BuildingModel`/`ArchitecturalScene` geometry remains authoritative; LEGO placements are representation only.

Invariants:

- the head and surround base include the two corner cells aligned with the jamb columns;
- vertical jambs stay in the currently approved upright brick technique;
- when an independently observed sill replaces the surround base, the sill keeps only its own opening-width cells and generic sill evidence;
- the two lower jamb corner cells remain surround-owned so material/color evidence is not silently transferred to the sill;
- no surround placement may enter the glazing void;
- facade orientation changes only world-grid anchoring, not the local architectural coverage.

This tranche deliberately uses only the existing placement-approved canonical `BRICK_1XN` family. It does not promote plates, tiles, brackets, SNOT, or sideways-building techniques.