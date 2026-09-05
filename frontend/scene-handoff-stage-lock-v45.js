// Make the active Survey → Scene prompt output-exclusive. This layer is
// intentionally append-only so the accepted Survey and v4.3/v4.4 contracts
// remain unchanged.
const originalFetchStageLock = globalThis.fetch.bind(globalThis);
const STAGE_LOCK_MARKER = 'BRICKHOUSE — SURVEY → SCENE STAGE LOCK v4.5';

const STAGE_LOCK = `

${STAGE_LOCK_MARKER}
THIS IS NOT A PHOTOS → SURVEY TASK.
Photos → Survey is already complete. The ArchitecturalSurvey embedded in this handoff is VALIDATED, ACCEPTED and IMMUTABLE INPUT. Do not regenerate it, rewrite it, improve it, summarize it as the output, or return brickhouse-survey-result.json.

YOUR ONLY TASK
Fuse that accepted Survey with the photo evidence into ArchitecturalScene v0.2 under the v4.3 + v4.4 rules above.

ONLY PERMITTED OUTPUT
- exactly one artifact named brickhouse-scene-result.json;
- direct ArchitecturalScene v0.2 root with schema_version="0.2";
- never an ArchitecturalSurvey root and never a wrapper around the Scene.

FINAL STAGE PREFLIGHT — BEFORE RESPONDING
1. If the candidate root contains Survey-stage collections such as "photos", "observations" or "known_measurements", STOP: that is the wrong stage and must not be returned.
2. Confirm schema_version is exactly "0.2" and the root is Scene-shaped according to the ArchitecturalScene contract.
3. Confirm the accepted Survey itself has not been edited or regenerated.
4. Confirm the only attached/announced result is brickhouse-scene-result.json.

The photo pages at the end are metric/fusion evidence for Scene only. Their presence never authorizes a new Survey.
`;

globalThis.fetch = async (...args) => {
  const response = await originalFetchStageLock(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;
  const text = await response.text();
  if (text.includes(STAGE_LOCK_MARKER)) return new Response(text, { status: response.status, statusText: response.statusText, headers: response.headers });
  return new Response(`${text}${STAGE_LOCK}`, { status: response.status, statusText: response.statusText, headers: response.headers });
};
