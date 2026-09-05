const SURVEY_BUTTON_ID = 'download-ai-package';
const SCENE_BUTTON_ID = 'download-scene-handoff';

function enterSceneOnlyMode() {
  document.body.dataset.stage = 'scene';

  const surveyButton = document.getElementById(SURVEY_BUTTON_ID);
  if (surveyButton) {
    surveyButton.hidden = true;
    surveyButton.disabled = true;
    surveyButton.setAttribute('aria-hidden', 'true');
  }

  const surveyStatus = document.getElementById('ai-package-status');
  if (surveyStatus) surveyStatus.hidden = true;

  const card = document.querySelector('.ai-handoff-card');
  if (card) {
    const heading = card.querySelector('.simple-heading');
    if (heading) {
      heading.innerHTML = `
        <div>
          <p class="eyebrow">Étape Survey → Scene</p>
          <h2>Créer la Scene à partir du Survey accepté</h2>
          <p>Le Survey est déjà validé. Ne recréez pas de PDF Survey. Attendez le bouton <strong>Créer le PDF unique Survey → Scene</strong> ci-dessous.</p>
        </div>`;
    }
  }

  const ensureSceneButtonVisible = () => {
    const sceneButton = document.getElementById(SCENE_BUTTON_ID);
    if (!sceneButton) return;
    sceneButton.hidden = false;
    sceneButton.scrollIntoView?.({ block: 'nearest' });
  };

  ensureSceneButtonVisible();
  new MutationObserver(ensureSceneButtonVisible).observe(document.documentElement, { childList: true, subtree: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', enterSceneOnlyMode, { once: true });
} else {
  enterSceneOnlyMode();
}
