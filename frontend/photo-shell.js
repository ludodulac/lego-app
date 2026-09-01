// Boldüngo phone-first shell v0.6. HUD first; immediate import feedback.
const stateOrder = ['photos', 'survey', 'scene', 'model'];

function shellReady() { return document.querySelector('.layout') && document.querySelector('.panel'); }
function move(node, target) { if (node) target.appendChild(node); }
function panel(state, label) {
  const el = document.createElement('section');
  el.className = 'shell-state-panel';
  el.dataset.shellPanel = state;
  el.setAttribute('aria-label', label);
  return el;
}
function navButton(label, state) {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = 'shell-nav-button';
  el.dataset.shellState = state;
  el.innerHTML = `<span class="shell-nav-dot" aria-hidden="true"></span><span>${label}</span>`;
  return el;
}

function simplifyPhotoSlots(grid) {
  const names = { front: 'Avant', right: 'Droite', left: 'Gauche', rear: 'Arrière' };
  grid?.querySelectorAll('.guided-photo-slot').forEach(slot => {
    const strong = slot.querySelector('strong');
    if (strong) strong.textContent = names[slot.dataset.slot] || strong.textContent;
    slot.querySelector(':scope > span')?.remove();
    const name = slot.querySelector('.guided-photo-name');
    if (name && /aucune photo/i.test(name.textContent || '')) name.textContent = 'Ajouter';
  });
}

function initShell() {
  if (!shellReady() || document.body.classList.contains('boldungo-shell-enabled')) return;

  const layout = document.querySelector('.layout');
  const legacy = document.querySelector('.panel');
  const resultPanel = document.querySelector('.result-panel');
  const cards = [...legacy.querySelectorAll(':scope > .simple-card')];
  const [viewsCard, detailsCard, factsCard, handoffCard, futureCard] = cards;
  const advanced = legacy.querySelector(':scope > .advanced-panel');
  const status = legacy.querySelector(':scope > #status');
  const build = document.querySelector('#build-bricks');
  const guidedGrid = document.querySelector('#guided-photo-grid');
  const download = document.querySelector('#download-ai-package');
  const resultFile = document.querySelector('#external-analysis-file');
  const resultText = document.querySelector('#external-analysis');
  const importButton = document.querySelector('#import-analysis');

  simplifyPhotoSlots(guidedGrid);
  document.body.classList.add('boldungo-shell-enabled');

  const cockpit = document.createElement('div');
  cockpit.className = 'boldungo-cockpit';

  const header = document.createElement('header');
  header.className = 'shell-progress';
  header.innerHTML = `
    <strong id="shell-state-title">Photos</strong>
    <div class="shell-progress-meter" aria-label="Progression"><span class="shell-progress-fill" id="shell-progress-fill"></span></div>
    <button type="button" class="shell-help-button" id="shell-help-button" aria-expanded="false" aria-controls="shell-tools-drawer" aria-label="Aide">?</button>`;

  const workspace = document.createElement('div');
  workspace.className = 'shell-workspace';
  const photos = panel('photos', 'Photos');
  const survey = panel('survey', 'Relevé');
  const scene = panel('scene', 'Maison');
  const model = panel('model', 'Maquette');

  const photoCard = document.createElement('section');
  photoCard.className = 'shell-main-card shell-photo-card';
  photoCard.innerHTML = '<div class="shell-card-title"><h2>4 vues</h2><span>Maison</span></div>';
  move(guidedGrid, photoCard);
  photos.appendChild(photoCard);

  const surveyCard = document.createElement('section');
  surveyCard.className = 'shell-main-card shell-survey-card';
  surveyCard.innerHTML = '<div class="shell-state-icon" aria-hidden="true">⌁</div><h2>Relevé</h2><strong id="shell-survey-status">Photos prêtes</strong><div class="shell-export-home"></div>';
  if (download) {
    download.textContent = 'Exporter';
    surveyCard.querySelector('.shell-export-home').appendChild(download);
  }
  survey.appendChild(surveyCard);

  const sceneCard = document.createElement('section');
  sceneCard.className = 'shell-main-card shell-scene-card';
  sceneCard.innerHTML = '<div class="shell-state-icon" aria-hidden="true">⌂</div><h2 id="shell-scene-name">Maison</h2><strong id="shell-scene-status">En attente</strong><button type="button" id="shell-scene-details">Détails</button>';
  scene.appendChild(sceneCard);

  const modelCard = document.createElement('section');
  modelCard.className = 'shell-main-card shell-model-card';
  modelCard.innerHTML = '<div class="shell-state-icon" aria-hidden="true">▦</div><h2>Maquette</h2><strong>Après validation</strong><div class="shell-build-home"></div>';
  if (build) modelCard.querySelector('.shell-build-home').appendChild(build);
  model.appendChild(modelCard);

  workspace.append(photos, survey, scene, model);

  const action = document.createElement('div');
  action.className = 'shell-primary-action';
  action.innerHTML = '<button type="button" id="shell-primary-button">Créer le relevé</button>';

  const feedback = document.createElement('div');
  feedback.className = 'shell-feedback';
  feedback.id = 'shell-feedback';
  feedback.setAttribute('role', 'status');
  feedback.setAttribute('aria-live', 'polite');
  feedback.hidden = true;

  const bottom = document.createElement('nav');
  bottom.className = 'shell-bottom-nav';
  bottom.setAttribute('aria-label', 'Parcours');
  bottom.append(
    navButton('Photos', 'photos'),
    navButton('Relevé', 'survey'),
    navButton('Maison', 'scene'),
    navButton('Maquette', 'model'),
  );

  const backdrop = document.createElement('div');
  backdrop.className = 'shell-drawer-backdrop';
  backdrop.hidden = true;

  const drawer = document.createElement('aside');
  drawer.className = 'shell-tools-drawer';
  drawer.id = 'shell-tools-drawer';
  drawer.setAttribute('aria-hidden', 'true');
  drawer.innerHTML = '<div class="shell-drawer-head"><strong id="shell-drawer-title">Aide</strong><button type="button" id="shell-tools-close" aria-label="Fermer">×</button></div><div class="shell-drawer-scroll"></div>';
  const drawerScroll = drawer.querySelector('.shell-drawer-scroll');

  move(viewsCard, drawerScroll);
  move(resultPanel, drawerScroll);
  move(handoffCard, drawerScroll);
  move(factsCard, drawerScroll);
  move(detailsCard, drawerScroll);
  move(advanced, drawerScroll);
  move(futureCard, drawerScroll);
  if (status) drawerScroll.prepend(status);

  [...legacy.children].filter(node => ['P', 'H1'].includes(node.tagName)).forEach(node => node.remove());
  cockpit.append(header, workspace, action, bottom, feedback);
  layout.replaceChildren(cockpit);
  document.body.append(backdrop, drawer);

  const titles = { photos: 'Photos', survey: 'Relevé', scene: 'Maison', model: 'Maquette' };
  const actions = { photos: 'Créer le relevé', survey: 'Importer', scene: 'Continuer', model: 'Construire' };
  let active = 'photos';
  let feedbackTimer = 0;

  function showFeedback(message, kind = 'info', persist = false) {
    const text = String(message || '').trim();
    if (!text) return;
    window.clearTimeout(feedbackTimer);
    feedback.textContent = text;
    feedback.dataset.kind = kind;
    feedback.hidden = false;
    if (!persist) feedbackTimer = window.setTimeout(() => { feedback.hidden = true; }, 3200);
  }
  function closeDrawer() {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    backdrop.hidden = true;
    header.querySelector('#shell-help-button').setAttribute('aria-expanded', 'false');
  }
  function openDrawer() {
    drawer.querySelector('#shell-drawer-title').textContent = `Aide · ${titles[active]}`;
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    backdrop.hidden = false;
    header.querySelector('#shell-help-button').setAttribute('aria-expanded', 'true');
  }
  function setState(state) {
    if (!stateOrder.includes(state)) return;
    active = state;
    cockpit.dataset.shellState = state;
    workspace.querySelectorAll('[data-shell-panel]').forEach(p => { p.hidden = p.dataset.shellPanel !== state; });
    bottom.querySelectorAll('[data-shell-state]').forEach(button => {
      const on = button.dataset.shellState === state;
      button.classList.toggle('active', on);
      button.setAttribute('aria-current', on ? 'page' : 'false');
    });
    document.querySelector('#shell-state-title').textContent = titles[state];
    document.querySelector('#shell-progress-fill').style.width = `${((stateOrder.indexOf(state) + 1) / 4) * 100}%`;
    document.querySelector('#shell-primary-button').textContent = actions[state];
    closeDrawer();
  }
  function syncSceneSummary() {
    const result = document.querySelector('#result');
    const name = document.querySelector('#result-name')?.textContent?.trim();
    const confidence = document.querySelector('#confidence')?.textContent?.trim();
    document.querySelector('#shell-scene-name').textContent = name && name !== '—' ? name : 'Maison';
    document.querySelector('#shell-scene-status').textContent = result && !result.hidden ? (confidence && confidence !== '—' ? confidence : 'Prête') : 'En attente';
  }
  function mirrorStatus() {
    const message = status?.textContent?.trim() || '';
    if (!message) return;
    const lower = message.toLowerCase();
    if (lower.includes('impossible') || lower.includes('refus') || lower.includes('invalide') || lower.includes('manquante')) {
      surveyCard.querySelector('#shell-survey-status').textContent = 'À corriger';
      showFeedback(message, 'error', true);
    } else if (lower.includes('valide')) {
      surveyCard.querySelector('#shell-survey-status').textContent = 'Relevé importé';
      showFeedback('Relevé importé ✓', 'success');
    } else if (lower.includes('vérif') || lower.includes('charg') || lower.includes('contrôle')) {
      surveyCard.querySelector('#shell-survey-status').textContent = 'Vérification…';
      showFeedback('Vérification du relevé…', 'info', true);
    }
  }

  bottom.addEventListener('click', event => {
    const button = event.target.closest('[data-shell-state]');
    if (button) setState(button.dataset.shellState);
  });
  header.querySelector('#shell-help-button').addEventListener('click', () => drawer.classList.contains('open') ? closeDrawer() : openDrawer());
  drawer.querySelector('#shell-tools-close').addEventListener('click', closeDrawer);
  backdrop.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeDrawer(); });
  sceneCard.querySelector('#shell-scene-details').addEventListener('click', openDrawer);

  document.querySelector('#shell-primary-button').addEventListener('click', () => {
    if (active === 'photos') {
      download?.click();
      setState('survey');
      return;
    }
    if (active === 'survey') {
      showFeedback('Choisissez le relevé', 'info');
      resultFile?.click();
      return;
    }
    if (active === 'scene') {
      setState('model');
      return;
    }
    build?.click();
  });

  resultFile?.addEventListener('change', async () => {
    const file = resultFile.files?.[0];
    if (!file) return;
    surveyCard.querySelector('#shell-survey-status').textContent = 'Lecture…';
    showFeedback('Lecture du relevé…', 'info', true);
    try {
      const text = await file.text();
      if (resultText) resultText.value = text;
      surveyCard.querySelector('#shell-survey-status').textContent = 'Vérification…';
      showFeedback('Vérification du relevé…', 'info', true);
      importButton?.click();
    } catch (error) {
      surveyCard.querySelector('#shell-survey-status').textContent = 'Erreur de lecture';
      showFeedback(`Impossible de lire le relevé : ${error.message}`, 'error', true);
    }
  });

  if (status) new MutationObserver(mirrorStatus).observe(status, { childList: true, subtree: true, characterData: true });

  const result = document.querySelector('#result');
  if (result) {
    new MutationObserver(() => {
      syncSceneSummary();
      if (!result.hidden) {
        surveyCard.querySelector('#shell-survey-status').textContent = 'Relevé importé';
        showFeedback('Relevé importé ✓', 'success');
        setState('scene');
      }
    }).observe(result, { attributes: true, subtree: true, childList: true, characterData: true });
  }

  syncSceneSummary();
  setState('photos');
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initShell, { once: true });
else initShell();
