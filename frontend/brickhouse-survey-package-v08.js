// v0.8 layers final reasoning and contract closure on top of the proven v0.7
// coverage-aware handoff without changing historical prompts or validators.
import './brickhouse-survey-package-v07.js?v=pdf-handoff-0.7-coverage-audit';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const reasoningAuditUrl = new URL('./brickhouse-survey-reasoning-audit-v34.txt', import.meta.url).href;
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

  const [reasoningResponse, auditResponse] = await Promise.all([
    upstreamFetch(reasoningAuditUrl, { cache: 'no-store' }),
    upstreamFetch(finalContractAuditUrl, { cache: 'no-store' }),
  ]);
  if (!reasoningResponse.ok) {
    throw new Error(`Survey reasoning addendum: HTTP ${reasoningResponse.status}`);
  }
  if (!auditResponse.ok) {
    throw new Error(`Final Survey contract addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithCoverageAudit, reasoningAudit, finalAudit] = await Promise.all([
    response.text(),
    reasoningResponse.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithCoverageAudit}\n\n${reasoningAudit}\n\n${finalAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
