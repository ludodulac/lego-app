const gateImportButton = document.querySelector('#import-analysis');
const gateExternalInput = document.querySelector('#external-analysis');
const gateApiInput = document.querySelector('#api-url');
const gateStatus = document.querySelector('#status');
let bypassSceneSurveyGateOnce = false;
let sceneProgressTimer = null;
let sceneProgressTimeout = null;
let sceneStatusWatchdog = null;
let protectSceneStatus = false;
let lastSceneStatus = '';
const IDLE_STATUS_PREFIX = 'Ajoutez vos photos puis lancez l’analyse';

function gateApiBase() { return gateApiInput.value.trim().replace(/\/$/, ''); }
function gateExtractJson(raw) {
  const value = raw.trim();
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
function pendingSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return payload?.valid_for_scene_fusion ? payload.survey : null;
  } catch { return null; }
}
function formatValidationDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return 'La scène ne respecte pas le contrat ArchitecturalScene v0.2.';
  return detail.slice(0, 8).map(item => {
    const path = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : 'champ inconnu';
    return `${path || 'racine'} : ${item.msg || item.type || 'valeur invalide'}`;
  }).join(' · ');
}
function isIdleStatus(text) { return String(text || '').trim().startsWith(IDLE_STATUS_PREFIX); }
function rememberSceneStatus(text) {
  const value = String(text || '').trim();
  if (!value || isIdleStatus(value) || value.startsWith('Vérification du moteur BrickHouse')) return;
  lastSceneStatus = value;
}
function restoreSceneStatusIfNeeded() {
  if (!protectSceneStatus || !lastSceneStatus) return;
  if (isIdleStatus(gateStatus.textContent)) gateStatus.textContent = lastSceneStatus;
}
function startSceneStatusProtection() {
  protectSceneStatus = true;
  if (sceneStatusWatchdog) clearInterval(sceneStatusWatchdog);
  sceneStatusWatchdog = setInterval(restoreSceneStatusIfNeeded, 250);
}
function stopSceneStatusProtection() {
  protectSceneStatus = false;
  lastSceneStatus = '';
  if (sceneStatusWatchdog) clearInterval(sceneStatusWatchdog);
  sceneStatusWatchdog = null;
}

const statusObserver = new MutationObserver(() => {
  if (!protectSceneStatus) return;
  const text = gateStatus.textContent || '';
  if (isIdleStatus(text)) {
    queueMicrotask(restoreSceneStatusIfNeeded);
    return;
  }
  rememberSceneStatus(text);
});
statusObserver.observe(gateStatus, { childList: true, characterData: true, subtree: true });

gateExternalInput?.addEventListener('input', () => {
  if (!gateExternalInput.value.trim()) stopSceneStatusProtection();
});

function stopSceneProgress() {
  if (sceneProgressTimer) clearInterval(sceneProgressTimer);
  if (sceneProgressTimeout) clearTimeout(sceneProgressTimeout);
  sceneProgressTimer = null;
  sceneProgressTimeout = null;
}

function startSceneProgress() {
  stopSceneProgress();
  const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  let index = 0;
  const update = () => {
    const text = gateStatus.textContent || '';
    const inGate = text.includes('Contrôle de cohérence entre le Survey validé et la scène reconstruite')
      || text.includes('Contrôle Survey → Scene');
    const inFinal = text.includes('Cohérence Survey → Scene validée. Validation géométrique finale')
      || text.includes('Validation de la scène architecturale par BrickHouse')
      || text.includes('Validation géométrique finale');
    if (!inGate && !inFinal) { stopSceneProgress(); return; }
    const label = inFinal ? 'Validation géométrique finale' : 'Contrôle Survey → Scene';
    gateStatus.textContent = `${frames[index % frames.length]} ${label} en cours…`;
    rememberSceneStatus(gateStatus.textContent);
    index += 1;
  };
  update();
  sceneProgressTimer = setInterval(update, 180);
  sceneProgressTimeout = setTimeout(() => {
    const text = gateStatus.textContent || '';
    if (text.includes('en cours')) {
      stopSceneProgress();
      gateStatus.textContent = 'La validation prend anormalement longtemps (>45 s). Le serveur est peut-être en réveil ou la requête est bloquée. Vous pouvez réessayer sans construire.';
      rememberSceneStatus(gateStatus.textContent);
      gateImportButton.disabled = false;
    }
  }, 45000);
}

gateImportButton.addEventListener('click', async event => {
  if (bypassSceneSurveyGateOnce) { bypassSceneSurveyGateOnce = false; return; }
  let parsed;
  try { parsed = JSON.parse(gateExtractJson(gateExternalInput.value)); } catch { return; }
  const isScene = parsed?.schema_version === '0.2' && Array.isArray(parsed?.volumes) && !parsed?.building;
  const survey = pendingSurvey();
  if (!isScene || !survey) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  const base = gateApiBase();
  if (!base) { gateStatus.textContent = 'URL API manquante.'; return; }
  startSceneStatusProtection();
  gateImportButton.disabled = true;
  gateStatus.textContent = 'Contrôle de cohérence entre le Survey validé et la scène reconstruite…';
  rememberSceneStatus(gateStatus.textContent);
  startSceneProgress();
  try {
    const response = await fetch(`${base}/api/v1/validate-scene-against-survey`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ survey, scene: parsed }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(formatValidationDetail(payload.detail));
    if (!payload.valid_for_projection) {
      stopSceneProgress();
      const errors = (payload.issues ?? []).filter(item => item.severity === 'error').map(item => item.message);
      gateStatus.textContent = `Scène refusée par le Survey : ${errors.join(' ') || 'dérive sémantique détectée.'}`;
      rememberSceneStatus(gateStatus.textContent);
      return;
    }
    localStorage.setItem('brickhouse.lastSceneSurveyValidation', JSON.stringify(payload));
    gateStatus.textContent = 'Cohérence Survey → Scene validée. Validation géométrique finale…';
    rememberSceneStatus(gateStatus.textContent);
    bypassSceneSurveyGateOnce = true;
    gateImportButton.disabled = false;
    gateImportButton.click();
  } catch (error) {
    stopSceneProgress();
    gateStatus.textContent = `Validation Survey → Scene impossible : ${error.message}`;
    rememberSceneStatus(gateStatus.textContent);
  } finally {
    gateImportButton.disabled = false;
  }
}, { capture: true });
