// Append-only Survey -> Scene relation-anchor contract.
// Keep producer output aligned with the existing ArchitecturalScene v0.2 validator.
const originalFetchRelationAnchor = globalThis.fetch.bind(globalThis);
const RELATION_ANCHOR_MARKER = 'BRICKHOUSE — SCENE RELATION ANCHOR CONTRACT v4.8';

const RELATION_ANCHOR_CONTRACT = `
${RELATION_ANCHOR_MARKER}

RELATION ENDPOINTS AND semantic_anchor_volume_id
Before emitting each Scene relation, classify subject_id and object_id against the Scene primitives actually present in this JSON: volumes, openings, roofs, chimneys, platforms, stairs and equipment.

For a relation with geometry_status:"resolved":
- if BOTH subject_id and object_id already identify concrete Scene primitives present in this JSON, OMIT semantic_anchor_volume_id;
- NEVER emit two resolved Scene endpoints plus semantic_anchor_volume_id, even when the anchor would repeat one of those endpoint volume ids;
- semantic_anchor_volume_id is reserved for the existing schema case where exactly one endpoint remains a semantic/non-materialized boundary or entity id, while the concrete Scene volume that metrically anchors that semantic endpoint is itself resolved and present;
- when semantic_anchor_volume_id is used, it MUST identify that existing concrete Scene volume and MUST NOT merely duplicate a subject_id or object_id that is already a concrete Scene primitive.

For a relation with geometry_status:"unresolved":
- OMIT semantic_anchor_volume_id; unresolved relation geometry is represented by geometry_status itself, not by a metric semantic anchor.

FINAL RELATION SELF-CHECK
Reject your own candidate before response if any relation has BOTH concrete Scene endpoints and semantic_anchor_volume_id.
Example forbidden shape: subject_id:"opening_A", object_id:"volume_B", both present as Scene primitives, plus semantic_anchor_volume_id:"volume_B".
Example allowed semantic-anchor shape: subject_id identifies a concrete Scene primitive, object_id identifies a semantic building boundary not materialized as a Scene primitive, geometry_status:"resolved", and semantic_anchor_volume_id identifies the concrete Scene volume that resolves that boundary metrically.
Do not change endpoint ids merely to avoid this rule. Do not invent geometry, ownership, facade or dimensions.
`;

globalThis.fetch = async (...args) => {
  const response = await originalFetchRelationAnchor(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;

  const text = await response.text();
  if (text.includes(RELATION_ANCHOR_MARKER)) {
    return new Response(text, { status: response.status, statusText: response.statusText, headers: response.headers });
  }
  return new Response(`${text}\n\n${RELATION_ANCHOR_CONTRACT}\n`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
