# BH-176 — production opening representation boundary

The production M0 path now treats architectural opening truth and LEGO representation as separate stages.

1. BuildingModel/ArchitecturalScene opening semantics remain unchanged.
2. `LEGORepresentationPlan` selects only curated, placement-approved framed-glazing motifs.
3. Reserved motif footprints are applied to the derived wall grid before spatial wall infill.
4. Planned frame/pane parts are emitted from that same plan and keep `opening_id` provenance into BrickModel.
5. Unsupported required openings stay as architectural voids and produce fidelity diagnostics instead of invented joinery.
6. Post-projection Scene enrichment no longer fabricates glazed doors or semantically unresolved glazed openings from `BRICK_1X1` cells. The historical cell path remains temporarily limited to structured glass-block material, which is deliberately not treated as a framed window motif.

This slice does not regenerate the private real-house benchmark. Visual validation remains downstream of spatial truth, representation planning, and physical support checks.
