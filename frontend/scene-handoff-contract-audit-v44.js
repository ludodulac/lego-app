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

PLATFORM / TERRACE STRUCTURE — PRESERVE EXISTENCE BEFORE METRIC DETAIL
ArchitecturalScene v0.2 supports root-level "platform_structure_observations" for visible terrace/deck structure whose existence is evidence-backed but whose exact count or coordinates are not metrically resolved. Do not choose between inventing SupportPost coordinates and losing visible structure.
- Allowed kinds are "vertical_post", "diagonal_brace", and "guardrail".
- Each observation is an object: { "id":"...", "platform_id":"...", "kind":"vertical_post|diagonal_brace|guardrail", "statement":"...", "count":integer|null, "source":{...}, "evidence":[...] }.
- Use Platform.supports only for SupportPost geometry whose position, width, depth and height are actually constrained by the evidence.
- If posts or diagonal braces are visibly present but their exact count/coordinates are not defensible, preserve each observed structural kind in platform_structure_observations instead of fabricating metric supports.
- If a guardrail is visibly established but its exact sides, interruptions or metric profile are unresolved, preserve a guardrail observation rather than inventing Platform.edges. Use edge_treatment/edges only when their geometric meaning is supported.
- A platform_structure_observation never manufactures a metric contact and never upgrades an unresolved relation to resolved.
- Preserve the Survey platform ID exactly in platform_id. Evidence and source confidence must reflect only what the photos/Survey support.

SPATIAL / STRUCTURAL REASONING — REQUIRED BEFORE LEGO READINESS
Treat every exterior assembly as occupied 3D space connected to the rest of one architectural scene, not as an isolated primitive. Before final output, reason jointly about the platform footprint and elevation, stair start/end and direction of ascent, massive landing/secondary volume footprint, building boundary, support structure, roof, chimney and openings.
For every pair whose relationship is evidenced, check the applicable facts: contact versus gap, above/below, overlap in plan, protrusion/overhang, adjacency, containment/embedding, and which object physically bears or receives the other. Do not infer a relationship merely because it would make construction convenient.
A certain physical relationship whose metric location is not yet defensible remains explicitly unresolved; it must not be converted into arbitrary coordinates merely to make the Scene buildable. Conversely, a relationship declared resolved must be numerically true in the serialized geometry.
The Scene is not LEGO-ready merely because it validates syntactically. Critical architectural occupancy and physical relationships must be coherent first; LEGO component choice and wall infill happen downstream and must not rewrite this architectural truth.

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
