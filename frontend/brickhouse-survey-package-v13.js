// v0.13 preserves target-vs-context ownership on top of the existing audited
// Survey prompt without changing historical prompt layers or capture semantics.
import './brickhouse-survey-package-v12.js?v=pdf-handoff-0.12-stair-topology';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const ownershipAuditUrl = new URL('./brickhouse-survey-ownership-audit-v38.txt', import.meta.url).href;

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

globalThis.fetch = async function targetContextAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const auditResponse = await upstreamFetch(ownershipAuditUrl, { cache: 'no-store' });
  if (!auditResponse.ok) {
    throw new Error(`Survey ownership addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithExistingAudits, ownershipAudit] = await Promise.all([
    response.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithExistingAudits}\n\n${ownershipAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
