// v0.9 adds an explicit provenance lock for user-provided measurements.
// It layers on top of v0.8 without changing the established PDF generator.
import './brickhouse-survey-package-v08.js?v=pdf-handoff-0.8-final-contract-audit';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const measurementAuditUrl = new URL('./brickhouse-survey-measurement-provenance-audit-v35.txt', import.meta.url).href;

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

globalThis.fetch = async function measurementProvenanceAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const auditResponse = await upstreamFetch(measurementAuditUrl, { cache: 'no-store' });
  if (!auditResponse.ok) {
    throw new Error(`Survey measurement provenance addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithExistingAudits, measurementAudit] = await Promise.all([
    response.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithExistingAudits}\n\n${measurementAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
