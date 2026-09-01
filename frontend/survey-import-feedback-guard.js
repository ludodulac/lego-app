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

function surveyProblems(parsed) {
  const problems = [];
  if (parsed?.schema_version !== '0.1') problems.push('schema_version doit valoir « 0.1 »');
  if (!parsed?.id) problems.push('champ racine « id » manquant');
  if (parsed?.canonical_frame?.front_facade !== 'front') {
    if (parsed?.canonical_frame?.front === 'front') problems.push('ancien champ « canonical_frame.front » : utilisez « front_facade »');
    else problems.push('canonical_frame.front_facade doit valoir « front »');
  }
  if (parsed?.canonical_frame?.x_direction !== 'front_view_left_to_right') problems.push('canonical_frame.x_direction non conforme');
  if (!Array.isArray(parsed?.photos)) problems.push('liste « photos » manquante');
  if (!Array.isArray(parsed?.observations)) problems.push('liste « observations » manquante');
  if (parsed?.building) problems.push('ancien champ racine « building » non accepté');
  return problems;
}

importButton?.addEventListener('click', event => {
  const raw = extractJsonObject(input?.value);
  if (!raw) {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (status) status.textContent = 'Import du relevé impossible : le fichier est vide ou n’a pas été lu.';
    return;
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (status) status.textContent = `Import du relevé impossible : JSON illisible (${error.message}).`;
    return;
  }
  const problems = surveyProblems(parsed);
  if (problems.length) {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (status) status.textContent = `Import du relevé impossible : ${problems.join(' · ')}.`;
  }
}, { capture: true });
