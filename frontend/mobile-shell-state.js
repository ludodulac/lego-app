const shell = document.querySelector('[data-boldungo-shell="single-screen"]');
const progressSteps = [...document.querySelectorAll('.shell-progress-step')];
const mobileLinks = [...document.querySelectorAll('.mobile-shell-nav a')];
const guidedInputs = [...document.querySelectorAll('.guided-photo-input,.detail-photo-input')];
const scenePreview = document.querySelector('#json-preview');
const result = document.querySelector('#result');
const sceneHandoffHome = document.querySelector('#scene-handoff-home');
const buildButton = document.querySelector('#build-bricks');

function readStoredSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return Boolean(payload?.valid_for_scene_fusion && payload?.survey?.schema_version === '0.1');
  } catch {
    return false;
  }
}

function currentScene() {
  const raw = scenePreview?.textContent?.trim();
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed?.schema_version === '0.2' && Array.isArray(parsed?.volumes) ? parsed : null;
  } catch {
    return null;
  }
}

function hasCapturedEvidence() {
  if (guidedInputs.some(input => (input.files?.length ?? 0) > 0)) return true;
  return Boolean(document.querySelector('.guided-photo-slot.has-photo,.detail-photo-slot.has-photo'));
}

function computeStage() {
  const surveyReady = readStoredSurvey() || Boolean(sceneHandoffHome?.querySelector('#download-scene-handoff'));
  const sceneReady = Boolean(currentScene());
  const buildReady = sceneReady && Boolean(buildButton && !buildButton.disabled);
  if (buildReady || sceneReady) return 3;
  if (surveyReady) return 2;
  if (hasCapturedEvidence() || (result && !result.hidden)) return 1;
  return 0;
}

function syncShellState() {
  const active = computeStage();
  if (shell) shell.dataset.shellStage = String(active + 1);

  progressSteps.forEach((step, index) => {
    step.classList.toggle('is-active', index === active);
    step.classList.toggle('is-complete', index < active);
    if (index === active) step.setAttribute('aria-current', 'step');
    else step.removeAttribute('aria-current');
  });

  mobileLinks.forEach((link, index) => {
    const targetStage = index === 0 ? 0 : index === 1 ? 0 : index === 2 ? Math.min(active, 2) : active;
    link.classList.toggle('is-active', index === 0 ? active === 0 : index === 2 ? active === 1 || active === 2 : index === 3 ? active >= 2 : false);
    if (targetStage === active) link.setAttribute('data-shell-current', 'true');
    else link.removeAttribute('data-shell-current');
  });
}

const observer = new MutationObserver(syncShellState);
for (const target of [result, scenePreview, sceneHandoffHome, buildButton]) {
  if (target) observer.observe(target, { subtree: true, childList: true, characterData: true, attributes: true });
}

document.addEventListener('change', syncShellState, true);
document.addEventListener('input', syncShellState, true);
window.addEventListener('storage', syncShellState);
window.addEventListener('pageshow', syncShellState);

syncShellState();
