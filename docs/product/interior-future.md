# Future interior reconstruction

BrickHouse exterior reconstruction remains the current product focus. Interior reconstruction is a later optional layer and must not block exterior-only projects.

Possible future inputs:
- room-by-room photos captured inside the property;
- floor-plan images when available;
- floor-by-floor text descriptions;
- explicit user corrections for uncertain room adjacency or furniture.

The future architecture should use a separate InteriorModel referencing BuildingModel volumes/floors. It can describe rooms, internal doors, stairs, fixed fixtures and an optional furniture/decor layer, each with source/confidence metadata.

The deterministic brick engine can later translate InteriorModel independently and combine it with the exterior shell when the selected model format and fidelity have enough resolution.
