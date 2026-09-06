const BENCHMARK_ID = 'real-house-5';
const ACCEPTED_SURVEY_URL = `./benchmarks/${BENCHMARK_ID}/accepted-survey-v0.1.json`;
const DEFAULT_API_URL = 'https://brickhouse-api.onrender.com';
const VALIDATION_TIMEOUT_MS = 45000;

const fileInput = document.querySelector('#scene-result-file');
const jsonInput = document.querySelector('#scene-result-json');
const importButton = document.querySelector('#scene-import-result');
const buildButton = document.querySelector('#scene-build-bricks');
const buildSize = document.querySelector('#scene-build-size');
const status = document.querySelector('#scene-result-status');
const summary = document.querySelector('#scene-result-summary');

let acceptedScene = null;
let surveyValidation = null;
let architecturalReady = false;

function apiBase() {
  return (localStorage.getItem('brickhouse.engineApiUrl') || DEFAULT_API_URL).replace(/\/$/, '');
}

function extractJson(raw) {
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

function formatDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return 'La Scene ne respecte pas le contrat BrickHouse.';
  return detail.slice(0, 8).map(item => {
    const path = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : 'champ inconnu';
    return `${path || 'racine'} : ${item.msg || item.type || 'valeur invalide'}`;
  }).join('\n');
}

function sceneShapeError(scene) {
  if (!scene || typeof scene !== 'object' || Array.isArray(scene)) return 'Le fichier doit contenir un objet JSON.';
  if (scene.schema_version !== '0.2') return 'schema_version doit valoir exactement "0.2".';
  if (!Array.isArray(scene.volumes) || !scene.volumes.length) return 'ArchitecturalScene doit contenir au moins un volume.';
  if ('photos' in scene || 'observations' in scene || 'known_measurements' in scene) {
    return 'Ce fichier ressemble encore à un Survey. Il faut importer brickhouse-scene-result.json.';
  }
  return '';
}

async function acceptedSurvey() {
  try {
    const stored = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    if (stored?.valid_for_scene_fusion && stored?.survey?.schema_version === '0.1') return stored.survey;
  } catch {
    // Fall through to the immutable repository checkpoint.
  }
  const response = await fetch(ACCEPTED_SURVEY_URL, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Survey accepté indisponible (HTTP ${response.status}).`);
  const survey = await response.json();
  if (survey?.schema_version !== '0.1' || !Array.isArray(survey?.observations)) {
    throw new Error('Le checkpoint Survey accepté est invalide.');
  }
  localStorage.setItem('brickhouse.pendingArchitecturalSurvey', JSON.stringify({
    survey,
    valid_for_scene_fusion: true,
    issues: [],
    source: 'accepted_repo_checkpoint',
  }));
  return survey;
}

async function postJson(path, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), VALIDATION_TIMEOUT_MS);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    let payload = null;
    try { payload = await response.json(); }
    catch { payload = {}; }
    return { response, payload };
  } finally {
    clearTimeout(timeout);
  }
}

function setSummary(lines) {
  const values = lines.filter(Boolean);
  summary.textContent = values.join('\n');
  summary.hidden = !values.length;
}

function resetAcceptedScene() {
  acceptedScene = null;
  surveyValidation = null;
  architecturalReady = false;
  buildButton.disabled = true;
  setSummary([]);
}

function architecturalReadiness(validation, sceneValidation) {
  const surveyErrors = (validation?.issues || []).filter(issue => issue.severity === 'error');
  const projectionIssues = sceneValidation?.projection?.issues || [];
  const projectionBlockers = projectionIssues.filter(issue => issue.severity === 'blocker');
  const requiredInputs = sceneValidation?.required_inputs || [];
  const compatibilityBlockers = sceneValidation?.m0_compatibility?.blockers || [];
  const reasons = [
    ...surveyErrors.map(issue => `${issue.code || 'survey_scene'}${issue.object_id ? ` [${issue.object_id}]` : ''} : ${issue.message}`),
    ...projectionBlockers.map(issue => issue.message || issue.code).filter(Boolean),
    ...requiredInputs.map(item => item.label || item.message || item.code).filter(Boolean),
    ...compatibilityBlockers.filter(Boolean),
  ];
  return { ready: reasons.length === 0, reasons };
}

async function readCandidateText() {
  const file = fileInput?.files?.[0];
  if (file) return file.text();
  return jsonInput?.value || '';
}

async function importScene() {
  resetAcceptedScene();
  importButton.disabled = true;
  status.textContent = 'Lecture et validation de la Scene…';
  try {
    const raw = extractJson(await readCandidateText());
    if (!raw) throw new Error('Choisissez brickhouse-scene-result.json ou collez son contenu JSON.');
    let scene;
    try { scene = JSON.parse(raw); }
    catch (error) { throw new Error(`JSON illisible : ${error.message}`); }

    const shapeError = sceneShapeError(scene);
    if (shapeError) throw new Error(shapeError);

    const survey = await acceptedSurvey();
    status.textContent = 'Contrôle du contrat et de la fidélité Survey → Scene…';
    const first = await postJson('/api/v1/validate-scene-against-survey', { survey, scene });
    if (!first.response.ok) throw new Error(formatDetail(first.payload?.detail));

    surveyValidation = first.payload;
    localStorage.setItem('brickhouse.lastSceneSurveyValidation', JSON.stringify(surveyValidation));
    const surveyErrors = (surveyValidation?.issues || []).filter(issue => issue.severity === 'error');
    if (surveyErrors.length) {
      const details = surveyErrors.slice(0, 8).map(issue => `${issue.code || 'erreur'}${issue.object_id ? ` [${issue.object_id}]` : ''} : ${issue.message}`);
      setSummary(details);
      throw new Error('La Scene contredit le Survey accepté.');
    }

    status.textContent = 'Validation géométrique finale par le moteur BrickHouse…';
    const second = await postJson('/api/v1/validate-scene', scene);
    if (!second.response.ok) throw new Error(formatDetail(second.payload?.detail));

    acceptedScene = second.payload?.scene || scene;
    const readiness = architecturalReadiness(surveyValidation, second.payload);
    architecturalReady = readiness.ready;
    localStorage.setItem('brickhouse.pendingArchitecturalScene', JSON.stringify({
      scene: acceptedScene,
      survey_validation: surveyValidation,
      scene_validation: second.payload,
      architectural_readiness: readiness,
      source: 'scene_result_import',
    }));

    const projectionIssues = second.payload?.projection?.issues || [];
    const warnings = projectionIssues.filter(issue => issue.severity === 'warning').map(issue => issue.message);
    const compatibilityWarnings = second.payload?.m0_compatibility?.warnings || [];
    const allWarnings = [...compatibilityWarnings, ...warnings];

    setSummary([
      `Scene contrôlée : ${acceptedScene.name || acceptedScene.id || 'ArchitecturalScene v0.2'}`,
      architecturalReady
        ? 'Maturité architecturale : prête pour adaptation LEGO.'
        : `Maturité architecturale insuffisante — LEGO bloqué : ${readiness.reasons.join(' ')}`,
      allWarnings.length ? `Avertissements : ${allWarnings.join(' ')}` : '',
    ]);

    buildButton.disabled = !architecturalReady;
    buildButton.textContent = architecturalReady ? 'Construire la maquette LEGO' : 'LEGO bloqué — Scene à résoudre';
    status.textContent = architecturalReady
      ? 'Scene validée et architecturalement prête. Vous pouvez lancer l’adaptation LEGO.'
      : 'Scene valide syntaxiquement, mais pas assez résolue architecturalement. Corrigez la Scene avant toute adaptation LEGO.';
  } catch (error) {
    const timeout = error?.name === 'AbortError';
    status.textContent = timeout
      ? 'Validation interrompue après 45 s : le moteur BrickHouse n’a pas répondu.'
      : `Import impossible : ${error.message}`;
  } finally {
    importButton.disabled = false;
  }
}

async function buildScene() {
  if (!acceptedScene || !surveyValidation || !architecturalReady) return;
  buildButton.disabled = true;
  status.textContent = 'Adaptation LEGO de la Scene en cours…';
  const baseRequest = {
    scene: acceptedScene,
    front_width_studs: Number(buildSize?.value) || 48,
    allow_partial: false,
  };
  try {
    const result = await postJson('/api/v1/build-scene', baseRequest);
    if (!result.response.ok) throw new Error(formatDetail(result.payload?.detail));
    if (!Array.isArray(result.payload?.brick_model?.parts) || !result.payload.brick_model.parts.length) {
      throw new Error('Le moteur a renvoyé une maquette sans pièces.');
    }
    if (!result.payload?.assembly_plan?.steps?.length) {
      throw new Error('Le moteur a renvoyé une maquette sans étapes de montage.');
    }
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(result.payload));
    localStorage.setItem('brickhouse.pendingArchitecturalScene', JSON.stringify({
      scene: acceptedScene,
      survey_validation: surveyValidation,
      architectural_readiness: { ready: true, reasons: [] },
      source: 'scene_result_import',
    }));
    globalThis.location.href = './viewer.html';
  } catch (error) {
    const timeout = error?.name === 'AbortError';
    status.textContent = timeout
      ? 'Construction interrompue après 45 s : le moteur BrickHouse n’a pas répondu.'
      : `Construction impossible : ${error.message}`;
    buildButton.disabled = false;
  }
}

fileInput?.addEventListener('change', async () => {
  resetAcceptedScene();
  if (!fileInput.files?.[0]) {
    status.textContent = 'En attente de brickhouse-scene-result.json.';
    return;
  }
  status.textContent = `${fileInput.files[0].name} prêt à être vérifié.`;
});
jsonInput?.addEventListener('input', resetAcceptedScene);
importButton?.addEventListener('click', importScene);
buildButton?.addEventListener('click', buildScene);

export { architecturalReadiness };
