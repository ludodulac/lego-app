// Route ArchitecturalScene imports before the Survey importer can misclassify them.
// A Scene is meaningful only against the validated Survey that produced its handoff.
const importButton = document.querySelector('#import-analysis');
const externalInput = document.querySelector('#external-analysis');
const status = document.querySelector('#status');

function extractJsonObject(raw) {
  const value = String(raw || '').trim();
  const start = value.indexOf('{');
  if (start < 0) return value;
  let depth = 0;
  let inString = false;
  let escaped = false;
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

function activeSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return payload?.valid_for_scene_fusion && payload?.survey?.schema_version === '0.1'
      ? payload.survey
      : null;
  } catch {
    return null;
  }
}

function isArchitecturalScene(value) {
  return value?.schema_version === '0.2'
    && Array.isArray(value?.volumes)
    && !value?.building;
}

importButton?.addEventListener('click', event => {
  let parsed;
  try {
    parsed = JSON.parse(extractJsonObject(externalInput?.value));
  } catch {
    return;
  }
  if (!isArchitecturalScene(parsed) || activeSurvey()) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  if (status) {
    status.textContent = 'ArchitecturalScene v0.2 reconnue, mais aucun ArchitecturalSurvey v0.1 validé n’est actif. Réactivez ou importez d’abord le Survey qui a produit ce handoff ; la Scene n’a pas été interprétée comme un relevé.';
  }
}, true);
