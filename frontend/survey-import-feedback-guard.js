const importButton = document.querySelector('#import-analysis');
const input = document.querySelector('#external-analysis');
const status = document.querySelector('#status');

function extractJsonObject(raw) {
  let value = String(raw || '').trim();
  if (value.startsWith('```')) {
    const lines = value.split(/\r?\n/);
    if (lines[0].trim().toLowerCase() === '```json' || lines[0].trim() === '```') lines.shift();
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

function explainSurveyProblem(parsed) {
  if (parsed?.schema_version !== '0.1') return 'Ce fichier n’est pas un relevé ArchitecturalSurvey v0.1.';
  if (!parsed?.id) return 'Le relevé est incomplet : identifiant racine « id » manquant.';
  if (parsed?.canonical_frame?.front_facade !== 'front') return 'Le relevé utilise un ancien repère. Le champ canonical_frame.front_facade doit valoir « front ».';
  if (parsed?.canonical_frame?.x_direction !== 'front_view_left_to_right') return 'Le repère horizontal du relevé n’est pas conforme au contrat actuel.';
  if (!Array.isArray(parsed?.photos)) return 'Le relevé est incomplet : liste « photos » manquante.';
  if (!Array.isArray(parsed?.observations)) return 'Le relevé est incomplet : liste « observations » manquante.';
  if (parsed?.building) return 'Ce fichier utilise un ancien format de relevé non accepté.';
  return 'Le fichier ne correspond pas au contrat ArchitecturalSurvey actuel.';
}

importButton?.addEventListener('click', () => {
  const raw = extractJsonObject(input?.value);
  if (!raw) {
    if (status) status.textContent = 'Import du relevé impossible : le fichier est vide ou n’a pas été lu.';
    return;
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    if (status) status.textContent = `Import du relevé impossible : JSON illisible (${error.message}).`;
    return;
  }
  const looksCurrent = parsed?.schema_version === '0.1'
    && parsed?.id
    && parsed?.canonical_frame?.front_facade === 'front'
    && parsed?.canonical_frame?.x_direction === 'front_view_left_to_right'
    && Array.isArray(parsed?.photos)
    && Array.isArray(parsed?.observations)
    && !parsed?.building;
  if (!looksCurrent && status) status.textContent = `Import du relevé impossible : ${explainSurveyProblem(parsed)}`;
});
