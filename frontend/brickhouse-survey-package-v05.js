// v0.5 keeps the complete v0.4 handoff generator intact and augments only the
// Survey prompt payload that it fetches when the user creates the PDF.
import './brickhouse-survey-package-v04.js?v=pdf-handoff-0.4';

const nativeFetch = globalThis.fetch.bind(globalThis);
const terrainAuditUrl = new URL('./brickhouse-survey-terrain-audit-v29.txt', import.meta.url).href;

function absoluteUrl(input) {
  if (typeof input === 'string') return new URL(input, globalThis.location?.href || import.meta.url).href;
  if (input && typeof input.url === 'string') return input.url;
  return String(input);
}

globalThis.fetch = async function terrainAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await nativeFetch(input, init);
  if (!url.endsWith('/brickhouse-survey-prompt.txt')) return response;

  const addendumResponse = await nativeFetch(terrainAuditUrl, { cache: 'no-store' });
  if (!addendumResponse.ok) {
    throw new Error(`Terrain Survey addendum: HTTP ${addendumResponse.status}`);
  }

  const [basePrompt, terrainAudit] = await Promise.all([
    response.text(),
    addendumResponse.text(),
  ]);

  return new Response(`${basePrompt}\n\n${terrainAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
