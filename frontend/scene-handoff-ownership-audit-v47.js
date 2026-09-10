// Keep target-vs-context ownership explicit during Survey -> Scene. This layer
// is append-only and runs after the v4.6 output frame, so it cannot change stage
// identity or the accepted Survey source.
const originalFetchOwnershipAudit = globalThis.fetch.bind(globalThis);
const OWNERSHIP_MARKER = 'BRICKHOUSE — SURVEY → SCENE OWNERSHIP AUDIT v4.7';

const OWNERSHIP_AUDIT = `

${OWNERSHIP_MARKER}
This addendum is mandatory and does not replace any earlier Survey → Scene rule.

TARGET SCENE ONLY
ArchitecturalScene represents the building being reconstructed, not every architectural object visible in the photos. Read Survey observations' attributes.subject_ownership and attribute_certainty.subject_ownership before creating any metric primitive.

- subject_ownership="target_building" with certainty="certain": the observation may be reconstructed if its own metric geometry is sufficiently supported.
- subject_ownership="external_context" with certainty="certain": NEVER create a target Scene primitive with that observation ID. Preserve it only as Survey/context evidence; do not absorb it into target volumes, roofs, chimneys, openings, equipment, stairs or platforms.
- subject_ownership whose value or certainty is unresolved/plausible/unproven remains uncertain. NEVER promote it to target_building merely to complete the Scene, but do not let that uncertain attribute erase an observation whose object existence is certain and whose certain Survey relations physically connect it to the target building or to a certain relation chain anchored to the target building.

PRESERVE EXISTENCE BEFORE OWNERSHIP RESOLUTION
When an observation has certainty="certain" and at least one certain connects_to/supports/part_of relation places it in an exterior assembly that is itself certainly connected to a target building_boundary, preserve the observable primitive when the Scene schema can encode its visible geometry. This rule does not assert target ownership: keep the ownership uncertainty explicit in notes/provenance and keep any hidden or numerically unproved contact unresolved. A certain relation chain is evidence that the object participates in the reconstructed architectural assembly; it is not permission to invent dimensions, hidden junctions, or ownership.

If the visible metric geometry is not sufficiently bounded for the primitive's required Scene fields, state that metric limitation explicitly instead of deleting the object for ownership reasons or fabricating coordinates. Never use this rule for an observation whose ownership is certainly external_context.

IDENTITY / MULTI-VIEW
Do not merge two visible objects merely because they have similar shape, material, color, facade position or apparent 2D overlap. A same_physical_object / part_of identity must remain consistent with certain ownership. A certain target-owned observation and a certain external-context observation cannot describe the same target primitive.

NEIGHBOR OBJECT PRE-FLIGHT
Before final output, audit every emitted volume, roof, chimney, opening, equipment item, stair and platform against the accepted Survey ID and its ownership. Remove a target Scene primitive when the matching Survey observation is certainly external_context. For unresolved/uncertain ownership, preserve object certainty and certain target-linked relation chains without promoting ownership; omit geometry only when the required metric fields themselves are genuinely unbounded, and name that limitation explicitly.
`;

globalThis.fetch = async (...args) => {
  const response = await originalFetchOwnershipAudit(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;

  const text = await response.text();
  if (text.includes(OWNERSHIP_MARKER)) {
    return new Response(text, { status: response.status, statusText: response.statusText, headers: response.headers });
  }
  return new Response(`${text}${OWNERSHIP_AUDIT}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
