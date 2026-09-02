const shell = document.querySelector('[data-boldungo-shell="single-screen"]');
const progressSteps = [...document.querySelectorAll('.shell-progress-step')];
const mobileLinks = [...document.querySelectorAll('.mobile-shell-nav a')];
const guidedInputs = [...document.querySelectorAll('.guided-photo-input,.detail-photo-input')];
const scenePreview = document.querySelector('#json-preview');
const result = document.querySelector('#result');
const sceneHandoffHome = document.querySelector('#scene-handoff-home');
const buildButton = document.querySelector('#build-bricks');
const progress = document.querySelector('.shell-progress');
const workflowPanel = document.querySelector('.panel');
const mobileViewport = window.matchMedia('(max-width: 620px)');
let requestedView = null;
let detailCaptureOpen = false;

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

function defaultView() {
  const surveyReady = readStoredSurvey() || Boolean(sceneHandoffHome?.querySelector('#download-scene-handoff'));
  const sceneReady = Boolean(currentScene());
  const buildReady = sceneReady && Boolean(buildButton && !buildButton.disabled);
  if (buildReady) return 'build';
  if (sceneReady) return 'scene';
  if (surveyReady) return 'survey';
  return 'photos';
}

function ensureStateCard() {
  let card = document.querySelector('#shell-state-card');
  if (card || !progress?.parentNode) return card;
  card = document.createElement('aside');
  card.id = 'shell-state-card';
  card.className = 'shell-state-card';
  card.setAttribute('aria-live', 'polite');
  progress.insertAdjacentElement('afterend', card);
  return card;
}

function stateCopy(active) {
  const hasEvidence = hasCapturedEvidence();
  const surveyReady = readStoredSurvey() || Boolean(sceneHandoffHome?.querySelector('#download-scene-handoff'));
  const sceneReady = Boolean(currentScene());
  const buildReady = sceneReady && Boolean(buildButton && !buildButton.disabled);

  if (buildReady) return { label: 'Maquette prête à construire', detail: 'La Scene est validée. Vous pouvez lancer la construction sans quitter ce parcours.', href: '#build-ready-card', action: 'Construire' };
  if (sceneReady) return { label: 'Scene reçue', detail: 'La reconstruction 3D est présente. Vérifiez les contrôles affichés avant la construction.', href: '#analysis-panel', action: 'Vérifier la Scene' };
  if (surveyReady) return { label: 'Survey validé', detail: 'Le relevé architectural est prêt. La prochaine étape est la reconstruction Survey → Scene.', href: '#survey-handoff-card', action: 'Préparer la Scene' };
  if (hasEvidence || active === 1) return { label: 'Photos en préparation', detail: 'Vos preuves sont en cours de collecte. Complétez les vues utiles puis générez le Survey.', href: '#survey-handoff-card', action: 'Continuer vers le Survey' };
  return { label: 'Commencer par les photos', detail: 'Ajoutez les vues disponibles. Une orientation manquante peut rester inconnue.', href: '#capture-card', action: 'Ajouter des photos' };
}

function renderStateCard(active) {
  const card = ensureStateCard();
  if (!card) return;
  const copy = stateCopy(active);
  card.innerHTML = `<div><small>État de votre maison</small><strong>${copy.label}</strong><span>${copy.detail}</span></div><a href="${copy.href}">${copy.action} →</a>`;
}

function decorateFocusPanels() {
  const captureCard = document.querySelector('#capture-card');
  const detailCard = document.querySelector('#detail-photo-grid')?.closest('.simple-card');
  if (detailCard) {
    detailCard.id ||= 'detail-capture-card';
    detailCard.classList.add('shell-detail-card');
  }
  if (captureCard && detailCard && !document.querySelector('#shell-detail-toggle')) {
    const toggle = document.createElement('button');
    toggle.id = 'shell-detail-toggle';
    toggle.className = 'shell-detail-toggle';
    toggle.type = 'button';
    toggle.setAttribute('aria-controls', detailCard.id);
    captureCard.appendChild(toggle);
  }
  const panels = [
    [captureCard, 'photos'],
    [detailCard, 'photos'],
    [document.querySelector('#measure-card'), 'measure'],
    [document.querySelector('#survey-handoff-card'), 'survey'],
    [document.querySelector('#analysis-panel'), 'scene'],
    [document.querySelector('#build-ready-card'), 'build'],
  ];
  for (const [panel, view] of panels) if (panel) panel.dataset.shellPanel = view;
}

function syncDetailCapture() {
  const detailCard = document.querySelector('#detail-capture-card');
  const toggle = document.querySelector('#shell-detail-toggle');
  detailCard?.classList.toggle('is-shell-detail-open', detailCaptureOpen);
  if (toggle) {
    toggle.setAttribute('aria-expanded', detailCaptureOpen ? 'true' : 'false');
    toggle.textContent = detailCaptureOpen ? 'Masquer les détails facultatifs' : 'Ajouter des détails facultatifs';
  }
}

function activeFocusView() {
  return requestedView || defaultView();
}

function renderFocusView() {
  decorateFocusPanels();
  syncDetailCapture();
  const activeView = activeFocusView();
  if (shell) shell.dataset.shellView = activeView;
  for (const panel of document.querySelectorAll('[data-shell-panel]')) {
    const visible = !mobileViewport.matches || panel.dataset.shellPanel === activeView;
    panel.classList.toggle('is-shell-view', visible);
  }
}

function viewForTarget(target) {
  if (target === '#capture-card') return 'photos';
  if (target === '#measure-card') return 'measure';
  if (target === '#survey-handoff-card') return 'survey';
  if (target === '#analysis-panel') return 'scene';
  if (target === '#build-ready-card' || target === '#build-actions') return 'build';
  return null;
}

function syncShellState() {
  const active = computeStage();
  if (shell) shell.dataset.shellStage = String(active + 1);

  progressSteps.forEach((step, index) => {
    step.classList.toggle('is-active', index === active);
    step.classList.toggle('is-complete', index < active);
    if (index === 3 && document.querySelector('#build-ready-card')) step.setAttribute('href', '#build-ready-card');
    if (index === active) step.setAttribute('aria-current', 'step');
    else step.removeAttribute('aria-current');
  });

  const buildReady = Boolean(currentScene() && buildButton && !buildButton.disabled);
  const visibleView = activeFocusView();
  mobileLinks.forEach((link, index) => {
    const label = link.querySelector('strong');
    if (index === 2 && label) label.textContent = 'Survey';
    if (index === 3) {
      link.setAttribute('href', buildReady ? '#build-ready-card' : '#analysis-panel');
      if (label) label.textContent = buildReady ? 'Maquette' : 'Scene';
    }
    const linkView = viewForTarget(link.getAttribute('href'));
    const isActive = linkView === visibleView;
    link.classList.toggle('is-active', isActive);
    if (isActive) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });

  renderStateCard(active);
  renderFocusView();
}

function activateTarget(event) {
  if (!mobileViewport.matches) return;
  const detailToggle = event.target.closest('#shell-detail-toggle');
  if (detailToggle) {
    detailCaptureOpen = !detailCaptureOpen;
    renderFocusView();
    if (detailCaptureOpen) requestAnimationFrame(() => document.querySelector('#detail-capture-card')?.scrollIntoView({ block: 'start', behavior: 'smooth' }));
    return;
  }
  const link = event.target.closest('a[href^="#"]');
  if (!link) return;
  const target = link.getAttribute('href');
  const view = viewForTarget(target);
  if (!view) return;
  requestedView = view;
  syncShellState();
  const destination = document.querySelector(target);
  if (!destination) return;
  event.preventDefault();
  requestAnimationFrame(() => destination.scrollIntoView({ block: 'start', behavior: 'smooth' }));
}

const observer = new MutationObserver(syncShellState);
for (const target of [result, scenePreview, sceneHandoffHome, buildButton]) {
  if (target) observer.observe(target, { subtree: true, childList: true, characterData: true, attributes: true });
}
if (workflowPanel) observer.observe(workflowPanel, { childList: true, subtree: true });

document.addEventListener('click', activateTarget, true);
document.addEventListener('change', syncShellState, true);
document.addEventListener('input', syncShellState, true);
window.addEventListener('storage', syncShellState);
window.addEventListener('pageshow', syncShellState);
mobileViewport.addEventListener?.('change', () => { requestedView = null; detailCaptureOpen = false; syncShellState(); });

syncShellState();
