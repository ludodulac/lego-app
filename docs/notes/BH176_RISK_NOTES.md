# BH-176 risk note

The historical Scene glass-block renderer still uses BRICK_1X1 cells as a temporary material proxy. BH-176 intentionally limits that legacy path to structured glass-block evidence only; it is no longer allowed to represent glazed doors or semantically unresolved clear-glazed openings.

A future LEGORepresentationPlan slice should give glass-block masonry its own curated, physically validated motif vocabulary. Until then it remains explicitly separate from framed window/door motifs so the engine does not invent joinery.
