// v0.14 preserves evidence-backed multi-view identity on top of the active
// ownership-aware Survey prompt without changing historical prompt layers.
import './brickhouse-survey-package-v13.js?v=pdf-handoff-0.13-target-context-ownership';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const identityAuditUrl = new URL('./brickhouse-survey-multiview-identity-audit-v39.txt', import.meta.url).href;

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

globalThis.fetch = async function multiviewIdentityAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const auditResponse = await upstreamFetch(identityAuditUrl, { cache: 'no-store' });
  if (!auditResponse.ok) {
    throw new Error(`Survey multi-view identity addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithExistingAudits, identityAudit] = await Promise.all([
    response.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithExistingAudits}\n\n${identityAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
