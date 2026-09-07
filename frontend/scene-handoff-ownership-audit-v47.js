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
- subject_ownership="unresolved", or any ownership whose certainty is plausible/unproven: do not metrify it as target geometry. Ownership must be resolved first; do not choose target_building merely because a primitive would make the Scene more complete.

IDENTITY / MULTI-VIEW
Do not merge two visible objects merely because they have similar shape, material, color, facade position or apparent 2D overlap. A same_physical_object / part_of identity must remain consistent with certain ownership. A certain target-owned observation and a certain external-context observation cannot describe the same target primitive.

NEIGHBOR OBJECT PRE-FLIGHT
Before final output, audit every emitted volume, roof, chimney, opening, equipment item, stair and platform against the accepted Survey ID and its ownership. If the matching Survey observation is certain external context or has unresolved/uncertain ownership, remove the target Scene primitive rather than inventing ownership.
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
