// v0.6 layers the topology-completeness audit on top of the proven v0.5
// terrain-aware handoff without changing the historical PDF generator.
import './brickhouse-survey-package-v05.js?v=pdf-handoff-0.5-terrain-audit';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const topologyAuditUrl = new URL('./brickhouse-survey-topology-audit-v30.txt', import.meta.url).href;

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

globalThis.fetch = async function topologyAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const addendumResponse = await upstreamFetch(topologyAuditUrl, { cache: 'no-store' });
  if (!addendumResponse.ok) {
    throw new Error(`Topology Survey addendum: HTTP ${addendumResponse.status}`);
  }

  const [promptWithTerrainAudit, topologyAudit] = await Promise.all([
    response.text(),
    addendumResponse.text(),
  ]);

  return new Response(`${promptWithTerrainAudit}\n\n${topologyAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
