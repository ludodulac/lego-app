// User-checkpoint bridge for the phone-first shell.
// A validated Survey is a completed step: move the user to Maison and expose
// exactly one next action while delegating PDF generation to the canonical
// Survey → Scene handoff button maintained by survey-import.js.

let autoAdvancedSurveyId = null;

function ready() {
  return document.body.classList.contains('boldungo-shell-enabled')
    && document.querySelector('.boldungo-cockpit')
    && document.querySelector('#shell-primary-button');
}

function currentPayload() {
  const raw = document.querySelector('#json-preview')?.textContent?.trim();
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function currentSchema() {
  return currentPayload()?.schema_version ?? null;
}

function currentSurveyId() {
  const payload = currentPayload();
  return payload?.schema_version === '0.1' ? (payload.id || payload.name || 'validated-survey') : null;
}

function cockpit() {
  return document.querySelector('.boldungo-cockpit');
}

function primary() {
  return document.querySelector('#shell-primary-button');
}

function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}

function goToScene() {
  document.querySelector('[data-shell-state="scene"]')?.click();
}

function surveyIsValidated() {
  return currentSchema() === '0.1'
    && !document.querySelector('#result')?.hidden
    && Boolean(document.querySelector('#download-scene-handoff'));
}

function sceneIsValidated() {
  return currentSchema() === '0.2' && !document.querySelector('#result')?.hidden;
}

function setSceneStatus(message) {
  setText(document.querySelector('#shell-scene-status'), message);
}

function setPrimaryLabel(message) {
  setText(primary(), message);
}

function syncValidatedSurvey() {
  if (!surveyIsValidated()) return;
  const id = currentSurveyId();
  const shell = cockpit();
  if (!shell || !id) return;

  // BH-225 used a second button on the Relevé card. It made the next action
  // visible but left two competing CTAs. The shell primary action now owns it.
  document.querySelector('#shell-survey-next')?.remove();

  if (autoAdvancedSurveyId !== id) {
    autoAdvancedSurveyId = id;
    if (shell.dataset.sceneHandoffCreated !== 'false') {
      shell.dataset.sceneHandoffCreated = 'false';
    }
    goToScene();
  }

  if (shell.dataset.shellState === 'scene' && shell.dataset.sceneHandoffCreated !== 'true') {
    setPrimaryLabel('Créer le PDF Maison');
    setSceneStatus('Relevé validé ✓ · créez maintenant le PDF Maison');
  }
}

function syncSceneState() {
  const shell = cockpit();
  const button = primary();
  if (!shell || !button || shell.dataset.shellState !== 'scene') return;

  if (sceneIsValidated()) {
    if ('sceneHandoffCreated' in shell.dataset) delete shell.dataset.sceneHandoffCreated;
    return;
  }

  if (surveyIsValidated()) {
    if (shell.dataset.sceneHandoffCreated === 'true') {
      setPrimaryLabel('Importer le JSON Maison');
      setSceneStatus('PDF Maison créé ✓ · donnez-le à l’IA puis importez son JSON');
    } else {
      setPrimaryLabel('Créer le PDF Maison');
      setSceneStatus('Relevé validé ✓ · créez maintenant le PDF Maison');
    }
  }
}

function sync() {
  if (!ready()) return;
  if (currentSchema() !== '0.1') autoAdvancedSurveyId = null;
  syncValidatedSurvey();
  syncSceneState();
}

function handlePrimary(event) {
  const shell = cockpit();
  if (!shell || shell.dataset.shellState !== 'scene' || !surveyIsValidated()) return;

  event.preventDefault();
  event.stopImmediatePropagation();

  if (shell.dataset.sceneHandoffCreated === 'true') {
    document.querySelector('#external-analysis-file')?.click();
    return;
  }

  const canonical = document.querySelector('#download-scene-handoff');
  if (!canonical) return;
  canonical.click();
  shell.dataset.sceneHandoffCreated = 'true';
  setPrimaryLabel('Importer le JSON Maison');
  setSceneStatus('PDF Maison créé ✓ · donnez-le à l’IA puis importez son JSON');
}

function init() {
  if (!ready()) {
    setTimeout(init, 50);
    return;
  }
  primary().addEventListener('click', handlePrimary, { capture: true });
  sync();
  new MutationObserver(sync).observe(document.body, {
    subtree: true,
    childList: true,
    attributes: true,
    characterData: true,
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
  init();
}
