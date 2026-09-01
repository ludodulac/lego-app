# Boldungo mobile single-screen shell

This document records the migration contract for issue #312. It describes the shell behavior without changing the semantic contracts of Survey, Scene, validation, or build.

## Product invariant

The normal portrait-mobile journey stays in one Boldungo shell. Photos, measurement, Survey, Scene, and build are panels/states of that shell rather than a chain of replacement pages.

The shell must keep these properties:

- global progress remains visible;
- primary navigation remains reachable at the bottom of the viewport;
- only the relevant workflow panel needs to occupy the normal mobile viewport at a given moment;
- switching panels is presentation state only and must not become a second source of workflow truth;
- Survey remains the semantic authority and Scene remains the metric authority;
- existing IDs, validators, localStorage contracts, imports, handoffs, and build behavior remain reusable while the shell is introduced;
- technical and compatibility routes remain available until their functions are safely absorbed.

## Current migration

The first incremental implementation lives in `photo.html` and keeps all existing workflow hooks in place.

`mobile-shell-state.js` derives workflow progress from the existing photo, Survey, Scene, and build signals. It also maintains a separate, ephemeral mobile focus view whose only job is deciding which existing panel is visible. The focus view never validates data, mutates Survey/Scene, or authorizes construction.

The mobile panels are currently:

- Photos: guided capture plus optional detail capture;
- Mesure: known facade width and model size inputs;
- Survey: PDF handoff, import, and validated Survey handoff;
- Scene: validation result and technical Scene preview already produced by the existing modules;
- Maquette: the existing build button surfaced in a visible build card.

Desktop behavior remains additive and compatible: the shell-specific hiding rules apply only below the mobile breakpoint.

## Route compatibility

`viewer.html` remains a secondary output route because the Three.js viewer is a distinct shareable/export-style surface. Existing index and compatibility routes are not removed during this migration.

The intended direction is to absorb normal user actions into the shell first, then remove or redirect legacy navigation only after equivalent behavior is covered by regression tests.

## UX rule for future changes

When adding a new normal-user feature, prefer a panel, card, drawer, or overlay inside the shell over a new page. New authoritative workflow state must not be introduced merely to drive navigation; presentation should continue to derive from the existing domain state whenever possible.
