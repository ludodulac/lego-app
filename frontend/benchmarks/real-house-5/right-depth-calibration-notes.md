# real-house-5 right-side depth calibration notes

Benchmark-only working note for the next Scene calibration pass.

The right capture (photo 2) is strongly oblique, so raw image-width ratios must not vote on building depth. Use the BH-198 planar rectification layer first. The visible utility pole is an occluder/boundary and must not be used as a building edge or scale object.

Candidate independent cue families visible on the same wall plane:

- the high right-side window (`right-opening-1`), with a conservative French residential window prior selected only after visual configuration is bounded;
- the lower translucent/glass-block opening (`right-opening-3`), using the versioned modular glass-block prior only if the visible module grid can be counted with sufficient confidence;
- facade/opening rhythm and cross-view consistency as secondary geometric checks, not additional pseudo-independent measurements.

Do not use the small lower service opening (`right-opening-2`) as a strong absolute-scale cue unless its architectural type becomes clear. Preserve `known_measurements=[]`. The goal is an inferred depth interval with provenance, not an exact measurement.
