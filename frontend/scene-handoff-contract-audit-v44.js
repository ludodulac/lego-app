// Layer a strict serialization/contact audit onto the active Survey → Scene
// prompt without duplicating or weakening the authoritative v4.3 reasoning
// contract. Loaded before scene-handoff-photo-evidence.js, so its fetch of the
// prompt receives this append-only addendum.
const originalFetch = globalThis.fetch.bind(globalThis);
const AUDIT_MARKER = 'BRICKHOUSE — SURVEY → SCENE STRICT OUTPUT AUDIT v4.4';

const AUDIT = `

${AUDIT_MARKER}
This addendum is mandatory and does not replace any v4.3 rule above.

ROOT METADATA — REQUIRED
- the ArchitecturalScene v0.2 root contains non-empty "id" and "name" fields;
- use "brickhouse-scene" / "BrickHouse architectural scene" only when the model has no more specific non-empty values; never overwrite a non-empty model value.

EVIDENCE SERIALIZATION — REQUIRED
- every Scene evidence item is an OBJECT with photo_index and observation; never serialize a bare string such as "photo:1";
- SceneVolume.floors is an integer, never a PropertyValue object;
- Platform.width, Platform.depth, Platform.thickness and StairRun.width are strictly positive JSON numbers, never PropertyValue objects;
- Platform uses thickness, never height;
- Terrain uses the canonical terrain.profiles field; do not emit terrain.facade_grade_profiles.

QUALITATIVE TERRAIN
If the Survey contains a certain/plausible terrain direction but the metric amplitude cannot be bounded, preserve the qualitative direction in terrain.profiles using the nullable elevations allowed by the Scene contract. Do not invent an amplitude merely to make the terrain look complete.

CERTAIN CHIMNEYS
ArchitecturalScene v0.2 supports chimneys. A certain Survey chimney must not be silently dropped merely because it is secondary. When the visible photos bound its placement and dimensions sufficiently for the strict SceneChimney schema, emit a chimney primitive supported by those photos. If the schema cannot represent the remaining metric uncertainty without fabrication, keep that limitation explicit in notes rather than inventing a dimension.

FINAL RESOLVED-CONTACT AUDIT
For every relation emitted with geometry_status="resolved", recompute the final numeric geometry. The backend contact tolerance is 0.12 m. A StairRun endpoint contact is determined by the start/end centerline point itself; stair width never counts as contact. A relation to building_boundary keeps that Survey endpoint and uses semantic_anchor_volume_id only for the unambiguous metrically touched Scene volume. Never mark a relation resolved solely because its Survey statement says the relation is certain.
`;

globalThis.fetch = async (...args) => {
  const response = await originalFetch(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;
  const text = await response.text();
  if (text.includes(AUDIT_MARKER)) return new Response(text, { status: response.status, statusText: response.statusText, headers: response.headers });
  return new Response(`${text}${AUDIT}`, { status: response.status, statusText: response.statusText, headers: response.headers });
};
