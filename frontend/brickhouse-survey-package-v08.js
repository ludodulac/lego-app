// v0.8 layers a final shape/identity closure on top of the proven v0.7
// coverage-aware handoff without changing historical prompts or audits.
import './brickhouse-survey-package-v07.js?v=pdf-handoff-0.7-coverage-audit';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const finalContractAuditUrl = new URL('./brickhouse-survey-final-contract-audit-v32.txt', import.meta.url).href;

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

globalThis.fetch = async function finalContractAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const auditResponse = await upstreamFetch(finalContractAuditUrl, { cache: 'no-store' });
  if (!auditResponse.ok) {
    throw new Error(`Final Survey contract addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithCoverageAudit, finalAudit] = await Promise.all([
    response.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithCoverageAudit}\n\n${finalAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
