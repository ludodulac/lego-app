// Keep rejected ArchitecturalScene candidates inside the normal user checkpoint
// loop instead of sending the user back to Photos/Survey or requiring hand edits.
const REJECTED_SCENE_KEY = 'brickhouse.lastRejectedSceneCandidate';
const REJECTED_ERROR_KEY = 'brickhouse.lastSceneValidationError';
let lastSceneCandidate = '';

function parseScene(raw) {
  try {
    const value = JSON.parse(String(raw || '').trim());
    return value?.schema_version === '0.2' && Array.isArray(value?.volumes) ? value : null;
  } catch {
    return null;
  }
}

function activeSceneState() {
  return document.querySelector('.boldungo-cockpit')?.dataset.shellState === 'scene';
}

function rejectedState() {
  try {
    const candidate = localStorage.getItem(REJECTED_SCENE_KEY) || '';
    const error = localStorage.getItem(REJECTED_ERROR_KEY) || '';
    return candidate && error ? { candidate, error } : null;
  } catch {
    return null;
  }
}

function clearRejectedState() {
  try {
    localStorage.removeItem(REJECTED_SCENE_KEY);
    localStorage.removeItem(REJECTED_ERROR_KEY);
  } catch { /* localStorage unavailable: UI can still continue */ }
  document.querySelector('#shell-scene-correction')?.remove();
}

function canonicalSceneHandoffButton() {
  return document.querySelector('#download-scene-handoff');
}

function createCorrectionPdf() {
  const canonical = canonicalSceneHandoffButton();
  const feedback = document.querySelector('#shell-feedback');
  if (!canonical) {
    if (feedback) {
      feedback.hidden = false;
      feedback.dataset.kind = 'error';
      feedback.textContent = 'Le Survey validé n’est plus disponible. Réimportez uniquement votre JSON Relevé validé, sans refaire les photos.';
    }
    return;
  }
  canonical.click();
  const sceneStatus = document.querySelector('#shell-scene-status');
  if (sceneStatus) sceneStatus.textContent = 'PDF de correction créé · donnez-le à l’IA puis réimportez le JSON Maison';
}

function ensureCorrectionUi() {
  const state = rejectedState();
  if (!state) return;
  const card = document.querySelector('.shell-scene-card');
  if (!card) return;
  const sceneStatus = card.querySelector('#shell-scene-status');
  if (sceneStatus) sceneStatus.textContent = 'Maison à corriger';
  let button = card.querySelector('#shell-scene-correction');
  if (!button) {
    button = document.createElement('button');
    button.type = 'button';
    button.id = 'shell-scene-correction';
    button.className = 'primary big-action';
    button.textContent = 'Créer le PDF de correction Maison';
    button.addEventListener('click', createCorrectionPdf);
    card.appendChild(button);
  }
  document.querySelector('[data-shell-state="scene"]')?.click();
}

function rememberFailure(message) {
  const candidate = parseScene(lastSceneCandidate || document.querySelector('#external-analysis')?.value);
  if (!candidate) return;
  try {
    localStorage.setItem(REJECTED_SCENE_KEY, JSON.stringify(candidate, null, 2));
    localStorage.setItem(REJECTED_ERROR_KEY, message);
  } catch { /* keep visible error even without persistence */ }
  ensureCorrectionUi();
}

function onStatusChange() {
  const status = document.querySelector('#status')?.textContent?.trim() || '';
  const lower = status.toLowerCase();
  if (lower.includes('architecturalscene valide')) {
    clearRejectedState();
    return;
  }
  const failed = lower.includes('validation impossible')
    || lower.includes('scène refusée')
    || lower.includes('scene refusée')
    || lower.includes('import de la scène impossible')
    || lower.includes('import de la scene impossible');
  if (failed) rememberFailure(status);
}

function init() {
  const importButton = document.querySelector('#import-analysis');
  const external = document.querySelector('#external-analysis');
  const status = document.querySelector('#status');
  const primary = document.querySelector('#shell-primary-button');
  if (!importButton || !external || !status || !primary) {
    setTimeout(init, 50);
    return;
  }

  importButton.addEventListener('click', () => {
    const scene = parseScene(external.value);
    if (scene) lastSceneCandidate = JSON.stringify(scene, null, 2);
  }, { capture: true });

  primary.addEventListener('click', event => {
    if (!activeSceneState() || !rejectedState()) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    createCorrectionPdf();
  }, { capture: true });

  new MutationObserver(onStatusChange).observe(status, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  ensureCorrectionUi();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
  init();
}
