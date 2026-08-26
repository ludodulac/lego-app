# BH-078 — notice step semantics

`AssemblyPlan` is the construction contract used by both the interactive viewer and printable notice.

For notice-quality output, a step must describe one local construction action:

- wall courses are split by facade before they are split into short chunks;
- placements inside a facade step follow their physical position along that facade;
- every step carries a deterministic `view` hint (`front`, `rear`, `left`, `right`, or `perspective`);
- `view` is derived from the actual placements and is therefore stable across viewer and notice renderers;
- the existing invariants remain: terrain/site first, structure bottom-up, exterior structures after the shell, window mini-assemblies, facade details, roof last, and every placement exactly once.

The renderer may still crop or zoom around the current placements, but it should not independently reinterpret which side of the model is being built when a `view` hint is present.
