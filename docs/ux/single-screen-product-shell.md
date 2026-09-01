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

- compact Boldüngo identity/header;
- house/workflow progress indicator;
- main content viewport;
- bottom navigation / stage controls;
- secondary drawer for details, expert and compatibility tools.

## Workflow states

### Photos

Primary content: the four orientation capture slots, compact capture status, known front width and the next safe action. Multiple photos per orientation remain supported. Notes remain available contextually rather than forcing permanent vertical height.

### Survey

Primary content: generation/import handoff and active Survey validation. A rejected import must not leave a stale Survey looking current.

### Scene

Primary content: validation/result state driven by the current Survey → Scene contract. Construction remains locked until existing validation passes.

### Maquette

Primary content: the existing construction action and model state. Viewer/share/export routes may remain secondary outputs.

## Panels, overlays and drawers

Detail photo groups, API controls, raw JSON, prompt links, reports, compatibility tools and future/experimental controls remain available in secondary panels. Moving a control is not authorization to delete its functionality.

## Scroll rules

- persistent header/progress and bottom navigation do not scroll away on phone;
- only the active workspace panel scrolls when necessary;
- the primary CTA remains outside the scrolling content;
- expert/raw content scrolls inside its drawer;
- the main path must not require traversing a document-length page.

## Touch and hierarchy

Primary touch targets should be comfortably thumb-sized. Each state has one dominant next action. Overlays and drawers have explicit close behavior and preserve entered state.

## Migration plan

### Phase 1 — shell foundation

Reorganize the existing working `photo.html` UI at runtime into a fixed viewport cockpit while retaining the existing DOM controls, IDs and listeners. The first implementation uses four persistent workflow states, compact 2×2 photo capture, a fixed primary CTA, bottom navigation and a secondary tools drawer.

### Phase 2 — state orchestration

Derive visible workflow state more deeply from validated Survey/Scene state without duplicating architectural truth.

### Phase 3 — absorb Maquette

Bring model/viewer/instruction status further into the same shell while preserving useful output URLs.

### Phase 4 — compatibility retirement

Remove obsolete page-era structures only after equivalent behavior is covered and CI remains green. Removal is deliberate and separate from additive shell work.

## Guardrails

Reject any shell change that:

- mechanically renames BrickHouse internals to Boldüngo;
- removes working functionality just to shorten the screen;
- weakens Survey/Scene validation;
- hardcodes benchmark-house facts into generic rules;
- mutates generated/imported JSON to make validation pass;
- introduces a second source of truth for active Survey/Scene identity;
- restores page-to-page navigation for the core workflow;
- copies proprietary visual identity from a reference product.

## First acceptance target

Capture the benchmark views, enter the known front width, generate the Survey PDF, import/validate Survey, produce/import/validate Scene and unlock construction while staying in one persistent Boldüngo cockpit.