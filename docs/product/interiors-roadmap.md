# BrickHouse interiors roadmap

Interiors are deliberately deferred from the current exterior-first milestone, but the product architecture must leave room for them.

## Future user inputs
- room-by-room photos captured indoors;
- optional floor-plan images;
- text descriptions such as "ground floor: kitchen left, living room right, WC at rear";
- explicit corrections from the user when inferred room layout is uncertain.

## Future model boundary
Introduce a separate `InteriorModel` rather than overloading `BuildingModel`.

Candidate concepts:
- floors / levels;
- rooms and room polygons;
- doors and internal circulation;
- stairs;
- fixed architectural elements;
- optional furniture / decoration layer;
- source + confidence for every inferred element.

`BuildingModel` should remain responsible for external massing, facade openings and roofs. `InteriorModel` can later reference the same volume/floor IDs and feed a separate deterministic interior-brick realization step.

## Product rule
Do not block exterior reconstruction on missing interior data. Exterior-only projects must remain first-class and fully buildable.
