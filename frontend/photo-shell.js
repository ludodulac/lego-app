const stateOrder = ['photos', 'survey', 'scene', 'model'];

function shellReady() {
  return document.querySelector('.layout') && document.querySelector('.panel');
}

function button(label, state) {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = 'shell-nav-button';
  el.dataset.shellState = state;
  el.innerHTML = `<span class="shell-nav-dot" aria-hidden="true"></span><span>${label}</span>`;
  return el;
}

function makePanel(state, label) {
  const panel = document.createElement('section');
  panel.className = 'shell-state-panel';
  panel.dataset.shellPanel = state;
  panel.setAttribute('aria-label', label);
  return panel;
}

function move(node, target) {
  if (node) target.appendChild(node);
}

function initShell() {
  if (!shellReady() || document.body.classList.contains('boldungo-shell-enabled')) return;

  const layout = document.querySelector('.layout');
  const legacyPanel = document.querySelector('.panel');
  const resultPanel = document.querySelector('.result-panel');
  const cards = [...legacyPanel.querySelectorAll(':scope > .simple-card')];
  const [viewsCard, detailsCard, factsCard, handoffCard, futureCard] = cards;
  const advancedPanel = legacyPanel.querySelector(':scope > .advanced-panel');
  const status = legacyPanel.querySelector(':scope > #status');
  const buildButton = document.querySelector('#build-bricks');

  document.body.classList.add('boldungo-shell-enabled');

  const cockpit = document.createElement('div');
  cockpit.className = 'boldungo-cockpit';

  const shellHeader = document.createElement('section');
  shellHeader.className = 'shell-progress';
  shellHeader.innerHTML = `
    <div class="shell-progress-copy">
      <span class="shell-kicker">Ma maison</span>
      <strong id="shell-state-title">Photos</strong>
    </div>
    <div class="shell-progress-meter" aria-label="Progression du projet">
      <span class="shell-progress-fill" id="shell-progress-fill"></span>
    </div>
    <button type="button" class="shell-tools-button" id="shell-tools-button" aria-expanded="false" aria-controls="shell-tools-drawer">Outils</button>`;

  const workspace = document.createElement('div');
  workspace.className = 'shell-workspace';
  const photosPanel = makePanel('photos', 'Photos');
  const surveyPanel = makePanel('survey', 'Survey');
  const scenePanel = makePanel('scene', 'Scene');
  const modelPanel = makePanel('model', 'Maquette');

  move(viewsCard, photosPanel);
  move(factsCard, photosPanel);
  move(handoffCard, surveyPanel);
  move(resultPanel, scenePanel);

  const modelCard = document.createElement('section');
  modelCard.className = 'simple-card shell-model-card';
  modelCard.innerHTML = `
    <div class="simple-heading"><div><p class="eyebrow">Maquette</p><h2>Construire la maison</h2><p>La construction reste verrouillée tant que la Scene n'est pas validée par les contrats existants.</p></div></div>
    <div class="shell-build-home"></div>`;
  if (buildButton) modelCard.querySelector('.shell-build-home').appendChild(buildButton);
  modelPanel.appendChild(modelCard);

  workspace.append(photosPanel, surveyPanel, scenePanel, modelPanel);

  const actionBar = document.createElement('div');
  actionBar.className = 'shell-primary-action';
  actionBar.innerHTML = '<button type="button" id="shell-primary-button">Créer mon relevé</button>';

  const bottomNav = document.createElement('nav');
  bottomNav.className = 'shell-bottom-nav';
  bottomNav.setAttribute('aria-label', 'Parcours Boldüngo');
  bottomNav.append(
    button('Photos', 'photos'),
    button('Relevé', 'survey'),
    button('Maison', 'scene'),
    button('Maquette', 'model'),
  );

  const drawerBackdrop = document.createElement('div');
  drawerBackdrop.className = 'shell-drawer-backdrop';
  drawerBackdrop.hidden = true;

  const drawer = document.createElement('aside');
  drawer.className = 'shell-tools-drawer';
  drawer.id = 'shell-tools-drawer';
  drawer.setAttribute('aria-label', 'Détails et outils avancés');
  drawer.setAttribute('aria-hidden', 'true');
  drawer.innerHTML = `<div class="shell-drawer-head"><div><span class="shell-kicker">Secondaire</span><strong>Détails et outils</strong></div><button type="button" id="shell-tools-close">Fermer</button></div><div class="shell-drawer-scroll"></div>`;
  const drawerScroll = drawer.querySelector('.shell-drawer-scroll');
  move(detailsCard, drawerScroll);
  move(advancedPanel, drawerScroll);
  move(futureCard, drawerScroll);

  const legacyIntro = [...legacyPanel.children].filter(node => ['P', 'H1'].includes(node.tagName));
  legacyIntro.forEach(node => node.remove());
  if (status) cockpit.appendChild(status);

  cockpit.prepend(shellHeader, workspace);
  cockpit.append(actionBar, bottomNav);
  layout.replaceChildren(cockpit);
  document.body.append(drawerBackdrop, drawer);

  const titles = { photos: 'Photos', survey: 'Relevé', scene: 'Maison', model: 'Maquette' };
  const primaryLabels = { photos: 'Créer mon relevé', survey: 'Importer mon relevé', scene: 'Vérifier ma maison', model: 'Construire ma maquette' };
  let activeState = 'photos';

  function closeDrawer() {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    drawerBackdrop.hidden = true;
    shellHeader.querySelector('#shell-tools-button').setAttribute('aria-expanded', 'false');
  }

  function openDrawer() {
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    drawerBackdrop.hidden = false;
    shellHeader.querySelector('#shell-tools-button').setAttribute('aria-expanded', 'true');
  }

  function setState(state) {
    if (!stateOrder.includes(state)) return;
    activeState = state;
    cockpit.dataset.shellState = state;
    workspace.querySelectorAll('[data-shell-panel]').forEach(panel => {
      panel.hidden = panel.dataset.shellPanel !== state;
    });
    bottomNav.querySelectorAll('[data-shell-state]').forEach(navButton => {
      const selected = navButton.dataset.shellState === state;
      navButton.classList.toggle('active', selected);
      navButton.setAttribute('aria-current', selected ? 'page' : 'false');
    });
    document.querySelector('#shell-state-title').textContent = titles[state];
    document.querySelector('#shell-progress-fill').style.width = `${((stateOrder.indexOf(state) + 1) / stateOrder.length) * 100}%`;
    document.querySelector('#shell-primary-button').textContent = primaryLabels[state];
  }

  bottomNav.addEventListener('click', event => {
    const navButton = event.target.closest('[data-shell-state]');
    if (navButton) setState(navButton.dataset.shellState);
  });

  shellHeader.querySelector('#shell-tools-button').addEventListener('click', () => drawer.classList.contains('open') ? closeDrawer() : openDrawer());
  drawer.querySelector('#shell-tools-close').addEventListener('click', closeDrawer);
  drawerBackdrop.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeDrawer(); });

  document.querySelector('#shell-primary-button').addEventListener('click', () => {
    if (activeState === 'photos') {
      document.querySelector('#download-ai-package')?.click();
      return;
    }
    if (activeState === 'survey') {
      document.querySelector('#external-analysis-file')?.click();
      return;
    }
    if (activeState === 'scene') {
      const result = document.querySelector('#result');
      if (result && !result.hidden) result.scrollIntoView({ block: 'start', behavior: 'smooth' });
      else setState('survey');
      return;
    }
    document.querySelector('#build-bricks')?.click();
  });

  const resultObserver = new MutationObserver(() => {
    const result = document.querySelector('#result');
    if (result && !result.hidden && activeState === 'survey') setState('scene');
  });
  const result = document.querySelector('#result');
  if (result) resultObserver.observe(result, { attributes: true, attributeFilter: ['hidden'] });

  setState('photos');
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initShell, { once: true });
else initShell();
