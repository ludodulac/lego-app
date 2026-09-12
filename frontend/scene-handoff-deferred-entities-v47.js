// Append-only Survey -> Scene completeness contract.
// Certain Survey entities must not disappear merely because Scene geometry is unresolved.
const originalFetchDeferredEntities = globalThis.fetch.bind(globalThis);
const DEFERRED_ENTITIES_MARKER = 'BRICKHOUSE — DEFERRED CERTAIN ENTITIES v4.7';

const DEFERRED_ENTITIES_CONTRACT = `
${DEFERRED_ENTITIES_MARKER}

CERTAIN EXISTENCE WITHOUT RESOLVED SCENE GEOMETRY
ArchitecturalScene v0.2 also permits this root collection:
"deferred_entities": [
  {
    "survey_id": "<exact Survey observation id>",
    "kind": "opening|chimney",
    "geometry_status": "unresolved",
    "reason": "<optional concise explanation>"
  }
]

This collection is an existence/identity bridge only. It is NOT a nullable Scene primitive.
For each accepted Survey observation whose object certainty is "certain":
- promote it to the normal metric Scene primitive only when the required Scene geometry is actually supported by the evidence;
- otherwise preserve it exactly once in deferred_entities using its exact Survey id and kind;
- NEVER duplicate semantic_type, facade, ownership, coordinates, dimensions, orientation or other Survey payload into a deferred entity;
- NEVER invent missing geometry merely to avoid deferral;
- a Survey id MUST NOT be both a normal Scene primitive and a deferred entity.

OPENING TYPE CERTAINTY
Object certainty and attribute certainty are independent.
If an opening exists certainly but attributes.semantic_type is only plausible or unproven, a promoted SceneOpening MUST use type:"unknown" rather than strengthening window/door/glazed-door plausibility into fact.
Only attribute_certainty.semantic_type="certain" authorizes a non-unknown SceneOpening type derived from that Survey semantic_type.

COMPLETENESS GATE BEFORE RESPONSE
- every certain Survey opening is either a normal SceneOpening with evidence-backed geometry OR one deferred_entities reference of kind "opening";
- every certain Survey chimney is either a normal Chimney with evidence-backed target geometry OR one deferred_entities reference of kind "chimney";
- unresolved facade, ownership, host face or metric geometry is a reason to defer, never a reason to delete and never a license to guess;
- deferred_entities preserve Survey semantic existence only; BuildingModel/LEGO projection remains intentionally blocked until they are geometrically promoted.
`;

globalThis.fetch = async (...args) => {
  const response = await originalFetchDeferredEntities(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;

  const text = await response.text();
  if (text.includes(DEFERRED_ENTITIES_MARKER)) {
    return new Response(text, { status: response.status, statusText: response.statusText, headers: response.headers });
  }
  return new Response(`${text}\n\n${DEFERRED_ENTITIES_CONTRACT}\n`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
