// v0.7 layers a final coverage-closure audit on top of the proven v0.6
// topology-aware handoff without changing any historical generator or audit.
import './brickhouse-survey-package-v06.js?v=pdf-handoff-0.6-topology-audit';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const coverageAuditUrl = new URL('./brickhouse-survey-coverage-audit-v31.txt', import.meta.url).href;

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

globalThis.fetch = async function coverageAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const addendumResponse = await upstreamFetch(coverageAuditUrl, { cache: 'no-store' });
  if (!addendumResponse.ok) {
    throw new Error(`Coverage Survey addendum: HTTP ${addendumResponse.status}`);
  }

  const [promptWithTopologyAudit, coverageAudit] = await Promise.all([
    response.text(),
    addendumResponse.text(),
  ]);

  return new Response(`${promptWithTopologyAudit}\n\n${coverageAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};