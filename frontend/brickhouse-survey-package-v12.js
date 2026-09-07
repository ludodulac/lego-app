// v0.12 preserves non-metric multi-run stair topology on top of the existing
// audited Survey prompt without changing the historical prompt layers.
import './brickhouse-survey-package-v11.js?v=pdf-handoff-0.11-orientation-provenance';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const stairTopologyAuditUrl = new URL('./brickhouse-survey-stair-topology-audit-v37.txt', import.meta.url).href;

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

globalThis.fetch = async function stairTopologyAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const auditResponse = await upstreamFetch(stairTopologyAuditUrl, { cache: 'no-store' });
  if (!auditResponse.ok) {
    throw new Error(`Survey stair topology addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithExistingAudits, stairTopologyAudit] = await Promise.all([
    response.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithExistingAudits}\n\n${stairTopologyAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
