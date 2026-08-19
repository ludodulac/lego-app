# Joint bonding v0.1

BH-006 adds the first structural rule to wall brick placement: adjacent courses should avoid aligning vertical joints whenever an exact alternative layout exists.

## Scope

The wall remains:

- rectangular;
- one stud thick;
- without openings;
- built only from canonical `1xN` bricks in the M0 catalog.

No corner bonding, loads, windows, doors, colors, metric conversion, or supplier constraints are handled yet.

## Strategy

For each course, the engine enumerates exact compositions of the wall width using spans:

`8, 6, 4, 3, 2, 1`

The first course prefers the composition with the fewest bricks, with larger pieces as the deterministic tie-breaker.

Each following course is selected using this priority:

1. minimize the number of vertical joint positions shared with the previous course;
2. minimize the number of bricks;
3. prefer larger spans from left to right as deterministic tie-breaker.

Touching the wall boundary is not a joint. Only internal boundaries between adjacent bricks count.

## Example

For a 16-stud wall:

- course A: `8 + 8` -> joint at `8`;
- course B: `6 + 8 + 2` -> joints at `6` and `14`;
- course C repeats course A;
- course D repeats course B.

This removes aligned joints between neighboring courses while keeping exact coverage.

## Limitation

This is a local bonding heuristic, not a structural solver. It only compares each course with the immediately preceding course. A later optimizer may consider multi-course bond quality, corners, openings, reinforcement, part availability and cost.
