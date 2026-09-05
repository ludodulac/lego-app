// v0.11 adds a capture-orientation provenance lock on top of the existing
// audited Survey prompt without changing the hybrid PDF generator itself.
import './brickhouse-survey-package-v09.js?v=pdf-handoff-0.9-measurement-provenance';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const orientationAuditUrl = new URL('./brickhouse-survey-orientation-provenance-audit-v36.txt', import.meta.url).href;

function absoluteUrl(input) {
  if (typeof input === 'string') return new URL(input, globalThis.location?.href || import.meta.url).href;
  if (input && typeof input.url === 'string') return input.url;
  return String(input);
}

function isSurveyPromptUrl(url) {
  try {
    return new URL(url, globalThis.location?.href || import.meta.url).pathname.endsWith('/brickhouse-survey-prompt.txt');
  } catch {
    return false;
  }
}

globalThis.fetch = async function orientationProvenanceAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const auditResponse = await upstreamFetch(orientationAuditUrl, { cache: 'no-store' });
  if (!auditResponse.ok) {
    throw new Error(`Survey orientation provenance addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithExistingAudits, orientationAudit] = await Promise.all([
    response.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithExistingAudits}\n\n${orientationAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
