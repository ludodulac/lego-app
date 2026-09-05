// Front-load the Survey → Scene output contract while preserving the v4.3
// first-line version marker required by the existing handoff generator.
//
// This layer runs after v4.5. It does not weaken or replace any prior audit;
// it only moves the stage/output identity close to the top of the fetched prompt
// so a neutral model sees ArchitecturalScene as the task before the immutable
// ArchitecturalSurvey input appears later in the PDF.
const originalFetchOutputFrame = globalThis.fetch.bind(globalThis);
const OUTPUT_FRAME_MARKER = 'BRICKHOUSE — SCENE OUTPUT FRAME v4.6';

const OUTPUT_FRAME = `
${OUTPUT_FRAME_MARKER}
THIS TASK BEGINS AFTER PHOTOS → SURVEY. THAT STAGE IS COMPLETE.

OUTPUT_TARGET=ArchitecturalScene v0.2
OUTPUT_FILE=brickhouse-scene-result.json
OUTPUT_SCHEMA_VERSION=0.2

WRONG_STAGE_OUTPUT — NEVER RETURN
- ArchitecturalSurvey v0.1;
- brickhouse-survey-result.json;
- any root with schema_version="0.1";
- any root containing Survey-stage collections such as "photos", "observations" or "known_measurements".

The accepted ArchitecturalSurvey included later in the handoff is IMMUTABLE INPUT DATA ONLY. Do not regenerate it, rewrite it, improve it, or use it as the response shape. Fuse it with the photo evidence into one ArchitecturalScene v0.2 and return only brickhouse-scene-result.json.

FINAL RESPONSE GATE
Before responding, inspect the root you are about to emit. If it is Survey-shaped, discard it and produce the Scene instead. The only permitted root has schema_version="0.2" and follows the ArchitecturalScene contract below.
`;

globalThis.fetch = async (...args) => {
  const response = await originalFetchOutputFrame(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;

  const text = await response.text();
  if (text.includes(OUTPUT_FRAME_MARKER)) {
    return new Response(text, { status: response.status, statusText: response.statusText, headers: response.headers });
  }

  const firstBreak = text.indexOf('\n');
  if (firstBreak < 0) {
    return new Response(`${text}\n${OUTPUT_FRAME}`, { status: response.status, statusText: response.statusText, headers: response.headers });
  }

  // Keep the authoritative v4.3 header as the literal first line because the
  // existing generator validates rawPrompt.startsWith(...v4.3) before use.
  const framed = `${text.slice(0, firstBreak + 1)}${OUTPUT_FRAME}\n${text.slice(firstBreak + 1)}`;
  return new Response(framed, { status: response.status, statusText: response.statusText, headers: response.headers });
};
