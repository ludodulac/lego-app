// Reject AI-claimed user measurements that were not explicitly supplied in the
// current capture UI. This is a client-side provenance guard before any Survey
// validator or Survey -> Scene handoff can accept the value.
const importButton = document.querySelector('#import-analysis');
const externalAnalysis = document.querySelector('#external-analysis');
const knownWidthInput = document.querySelector('#known-width');
const status = document.querySelector('#status');

function extractJsonObject(raw) {
  let value = String(raw || '').trim();
  if (value.startsWith('```')) {
    const lines = value.split(/\r?\n/);
    if (lines[0].trim().toLowerCase() === '```json' || lines[0].trim() === '```') lines.shift();
    if (lines.at(-1)?.trim() === '```') lines.pop();
    value = lines.join('\n').trim();
  }
  const start = value.indexOf('{');
  if (start < 0) return value;
  let depth = 0, inString = false, escaped = false;
  for (let index = start; index < value.length; index += 1) {
    const char = value[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') { inString = true; continue; }
    if (char === '{') depth += 1;
    else if (char === '}' && --depth === 0) return value.slice(start, index + 1);
  }
  return value.slice(start);
}

function surveysInPayload(payload) {
  const surveys = [];
  if (payload?.schema_version === '0.1' && Array.isArray(payload?.known_measurements)) surveys.push(payload);
  if (payload?.survey?.schema_version === '0.1' && Array.isArray(payload.survey?.known_measurements)) surveys.push(payload.survey);
  return surveys;
}

function explicitFrontWidth() {
  const value = Number(knownWidthInput?.value);
  return Number.isFinite(value) && value > 0 ? value : null;
}

function provenanceError(survey) {
  const claimed = (survey?.known_measurements ?? []).filter(item => item?.source?.kind === 'user_provided');
  if (!claimed.length) return null;

  const authorizedFrontWidth = explicitFrontWidth();
  for (const measurement of claimed) {
    if (measurement.kind !== 'front_width') {
      return `Mesure refusée : « ${measurement.kind || 'inconnue'} » est marquée user_provided mais aucun champ de capture actuel ne peut l'autoriser.`;
    }
    if (authorizedFrontWidth === null) {
      return 'Mesure refusée : le Survey affirme une largeur avant fournie par l’utilisateur, mais aucune largeur n’a été saisie dans Boldungo.';
    }
    const value = Number(measurement.value);
    if (measurement.units !== 'm' || !Number.isFinite(value) || Math.abs(value - authorizedFrontWidth) > 1e-9) {
      return `Mesure refusée : la largeur avant user_provided du Survey ne correspond pas exactement à la largeur saisie (${authorizedFrontWidth} m).`;
    }
  }
  return null;
}

importButton?.addEventListener('click', event => {
  const raw = extractJsonObject(externalAnalysis?.value);
  if (!raw) return;

  let payload;
  try { payload = JSON.parse(raw); } catch { return; }
  for (const survey of surveysInPayload(payload)) {
    const error = provenanceError(survey);
    if (!error) continue;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (status) status.textContent = `${error} Recréez le Survey depuis le handoff courant ; aucune Scene ne sera préparée avec cette mesure.`;
    return;
  }
}, { capture: true });
