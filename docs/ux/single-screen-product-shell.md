# Boldüngo single-screen product shell

Status: product invariant
Related issue: #312

## Decision

Boldüngo's normal user journey lives inside one persistent application shell. Photos, Survey, Scene and Maquette are workflow states of that shell, not a chain of destination pages.

This is an interaction architecture decision, not a visual imitation of any reference application. External references such as Clash Royale may be studied for mobile interaction principles only. Boldüngo must not copy proprietary assets, characters, icons, exact compositions or trade dress.

## Invariants

1. **One normal shell.** Opening Boldüngo opens the working cockpit. The normal workflow does not require returning to a marketing/home page between stages.
2. **Portrait-first viewport.** The primary composition is designed for a phone held in portrait orientation and should fit its essential context and primary action in the viewport.
3. **Persistent progress.** The user can always tell where the house is in the Photos → Survey → Scene → Maquette pipeline.
4. **Persistent bottom navigation.** Primary destinations/actions are reachable in the thumb zone. Switching them changes the active panel/state without discarding the house context.
5. **Low navigation depth.** Prefer contextual panels, sheets, drawers and overlays over nested page chains.
6. **One dominant CTA per state.** The next safe workflow action is visually dominant. Secondary actions are subordinate; destructive or expert actions are never visually confused with the primary action.
7. **No long-scroll dependency for the main path.** A state may contain internally scrollable content, but advancing the core workflow must not require traversing one long document page.
8. **Immediate feedback.** Capture, import, validation and construction actions expose their state immediately and keep errors next to the action/context that produced them.
9. **Advanced tools stay available.** Debug, raw JSON, prompt links, compatibility controls and other expert functions move into secondary drawers/panels rather than being removed.
10. **Responsive means the same shell.** Tablet and desktop may widen, split or dock panels, but they preserve the same workflow model and state. Desktop is not a separate navigation philosophy.
11. **Additive migration.** Existing working DOM IDs, listeners, imports, validators and handoffs remain intact until the shell has demonstrably absorbed their behavior. Compatibility pages may remain temporarily.
12. **Architecture truth is untouched by UX.** Shell state must not rewrite Survey/Scene data to make a workflow appear complete. Validation gates remain authoritative.

## Shell anatomy

### Persistent chrome

- compact Boldüngo identity/header;
- house/workflow progress indicator;
- main content viewport;
- bottom navigation / stage controls;
- optional secondary drawer trigger for expert/settings tools.

### Workflow states

#### Photos

Primary content: the four orientation capture slots, compact capture status, known front width and the next safe action.

The benchmark's multiple photos for one orientation remain supported. Detail groups and notes remain available through contextual expansion rather than disappearing.

Primary CTA when inputs are ready: create the autonomous Survey PDF.

#### Survey

Primary content: import result, validation status, uncertainties/questions and source identity. A rejected import must visibly invalidate the previous active Survey rather than leaving stale state looking current.

Primary CTA exists only when the Survey is valid for Scene fusion.

#### Scene

Primary content: active Survey source identity, Scene handoff/import, fidelity validation and unresolved geometry.

Construction is unavailable until the Scene passes the existing validation contract.

#### Maquette

Primary content: build status and model summary, then access to viewer/instructions/BOM-related outputs as they become available.

Viewer/share/export URLs may remain secondary routes because they are outputs, not the normal workflow shell.

## Panels, overlays and drawers

Use a panel/sheet when the user needs temporary focus while retaining the house context behind it. Examples: add photos to one orientation, edit a note, inspect a validation problem, import a JSON result.

Use the expert drawer for API URL, legacy technical photo input, raw JSON, prompt links, test/report downloads and compatibility controls. Moving a control to this drawer does not authorize deleting its functionality.

A modal is reserved for short blocking decisions or confirmations. Do not turn every workflow state into a modal stack.

## Scroll rules

- persistent header/progress and bottom navigation do not scroll away on phone;
- the active panel may scroll within the remaining viewport;
- primary CTA should remain reachable without requiring a full-page scroll, preferably through a sticky action zone when appropriate;
- large technical/raw data areas scroll internally;
- desktop may show a docked validation/result panel alongside the active workflow panel.

## Touch and hierarchy

- primary interactive targets should be comfortably thumb-sized (target approximately 44 CSS px minimum where practical);
- avoid placing the only primary action at the extreme top of a tall panel;
- use state, label and text in addition to color for completion/errors;
- preserve keyboard focus order and visible focus states;
- overlays/sheets must have an explicit close/back action and must not destroy entered state when dismissed.

## Migration plan

### Phase 1 — shell foundation

Introduce shell semantics and CSS around the existing Photos → Survey → Scene workflow while preserving current functional IDs and script imports. Convert mobile layout from a document-like column into an app viewport with persistent progress/bottom controls. Keep expert tools accessible.

### Phase 2 — state orchestration

Derive visible workflow state from the existing validated application state. Switch active panels without duplicating Survey/Scene truth in a second incompatible store. Add focused sheets for capture/import/validation where useful.

### Phase 3 — absorb Maquette

Bring build/model state into the same shell. Keep viewer, exports, debug and compatibility routes as secondary destinations where they remain useful.

### Phase 4 — compatibility retirement

Only after equivalent behavior is covered by CI/browser checks may obsolete navigation/pages be removed. Removal is a separate deliberate change, never an incidental part of adding the shell.

## Guardrails for implementation and review

A shell PR must be rejected if it:

- renames BrickHouse internals mechanically to Boldüngo;
- removes a working control merely to simplify the screen;
- weakens Survey/Scene validation;
- hardcodes benchmark-house facts into generic UI or workflow logic;
- mutates imported/generated JSON to make validation pass;
- introduces a second source of truth for active Survey/Scene identity;
- requires page-to-page navigation for the core Photos → Survey → Scene → Maquette journey;
- copies proprietary visual identity from a reference product.

## First acceptance target

The first complete shell milestone is the existing benchmark workflow: capture the five benchmark photos across the four orientation slots, enter the known front width, generate the Survey PDF, import and validate Survey, produce/import and validate Scene, then unlock construction — while remaining in one persistent Boldüngo shell and without changing the architectural contracts.