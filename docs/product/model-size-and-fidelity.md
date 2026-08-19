# BrickHouse model size and fidelity

BrickHouse separates three concepts:

1. **Real building dimensions** — stored in `BuildingModel` in metres.
2. **Physical brick-model format** — how much shelf/table space the customer wants to use.
3. **Fidelity level** — how aggressively architectural details may be simplified.

## Format profiles

- **Compact** — target front/max footprint around 32 studs. Souvenir/display model, lower part count, stronger simplification.
- **Standard** — around 48 studs. Default balance between recognisability, facade detail, part count and display space.
- **Grand** — around 64 studs. More room for windows, surrounds, roof articulation and other facade details.

The engine keeps the source proportions and snaps the model to the stud grid. It should report the approximate resulting scale and physical footprint rather than asking ordinary users to choose a 1:N scale.

## Fidelity profiles

- **Essential** — preserve silhouette, roof, openings and dominant facade rhythm; simplify minor decorative details.
- **Detailed** — preserve window families, sills/surrounds, stronger roof/facade articulation and other supported details when the selected format has enough grid resolution.

Format and fidelity are independent. A Compact + Detailed request may be impossible for a complex facade. In that case BrickHouse should recommend either a larger format or Essential fidelity instead of silently deleting details.

## Pricing direction

Future pricing can be driven by the generated result rather than by a fixed scale: part count, unique/special part families, format, fidelity, printed-manual/shipping options and optional interior package. The deterministic engine should expose estimates before checkout; pricing itself remains outside the reconstruction engine.
