// User-checkpoint bridge for the phone-first shell.
// Keeps the canonical Survey/Scene generators untouched and only exposes the
// already-existing next action at the point where the user expects it.

function ready() {
  return document.body.classList.contains('boldungo-shell-enabled')
    && document.querySelector('.shell-survey-card');
}

function currentSchema() {
  const raw = document.querySelector('#json-preview')?.textContent?.trim();
  if (!raw) return null;
  try { return JSON.parse(raw)?.schema_version ?? null; } catch { return null; }
}

function ensureSurveyNextAction() {
  if (!ready()) return;
  const card = document.querySelector('.shell-survey-card');
  const validated = currentSchema() === '0.1'
    && !document.querySelector('#result')?.hidden
    && Boolean(document.querySelector('#download-scene-handoff'));
  let button = document.querySelector('#shell-survey-next');

  if (!validated) {
    button?.remove();
    return;
  }

  if (!button) {
    button = document.createElement('button');
    button.type = 'button';
    button.id = 'shell-survey-next';
    button.className = 'primary big-action';
    button.textContent = 'Créer le PDF Maison';
    button.addEventListener('click', () => {
      const canonical = document.querySelector('#download-scene-handoff');
      if (!canonical) return;
      canonical.click();
      document.querySelector('[data-shell-state="scene"]')?.click();
    });
    card.appendChild(button);
  }
}

function syncSceneImportLabel() {
  if (!ready()) return;
  const cockpit = document.querySelector('.boldungo-cockpit');
  const primary = document.querySelector('#shell-primary-button');
  if (!cockpit || !primary) return;
  if (cockpit.dataset.shellState === 'scene' && currentSchema() !== '0.2') {
    primary.textContent = 'Importer le JSON Maison';
  }
}

function sync() {
  ensureSurveyNextAction();
  syncSceneImportLabel();
}

function init() {
  if (!ready()) {
    setTimeout(init, 50);
    return;
  }
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
