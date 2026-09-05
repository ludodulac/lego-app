const SURVEY_BUTTON_ID = 'download-ai-package';
const SCENE_BUTTON_ID = 'download-scene-handoff';
const BENCHMARK_ID = 'real-house-5';
const ACCEPTED_SURVEY_URL = `./benchmarks/${BENCHMARK_ID}/accepted-survey-v0.1.json`;

function sceneBenchmarkRequested() {
  const params = new URLSearchParams(globalThis.location?.search || '');
  return params.get('benchmark') === BENCHMARK_ID && params.get('stage') === 'scene';
}

function ensureSceneButton() {
  const existing = document.getElementById(SCENE_BUTTON_ID);
  if (existing) {
    existing.hidden = false;
    existing.disabled = false;
    return existing;
  }
  const home = document.getElementById('scene-handoff-home');
  if (!home) return null;
  home.innerHTML = `<p><button id="${SCENE_BUTTON_ID}" class="primary big-action" type="button">Créer le PDF unique Survey → Scene</button></p><p><small>Le Survey accepté est déjà chargé. Ce bouton crée uniquement le handoff ArchitecturalScene.</small></p>`;
  return document.getElementById(SCENE_BUTTON_ID);
}

async function seedAcceptedBenchmarkSurvey() {
  if (!sceneBenchmarkRequested()) return;
  const response = await fetch(ACCEPTED_SURVEY_URL, { cache: 'no-store' });
  if (!response.ok) throw new Error(`accepted Survey: HTTP ${response.status}`);
  const survey = await response.json();
  if (survey?.schema_version !== '0.1' || !Array.isArray(survey?.observations)) {
    throw new Error('accepted Survey checkpoint invalide');
  }
  localStorage.setItem('brickhouse.pendingArchitecturalSurvey', JSON.stringify({
    survey,
    valid_for_scene_fusion: true,
    issues: [],
    source: 'accepted_repo_checkpoint',
  }));
  ensureSceneButton();
}

async function enterSceneOnlyMode() {
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
          <p>Le Survey est déjà validé. Sur cette page, aucun PDF Photos → Survey ne doit être généré.</p>
        </div>`;
    }
  }

  try {
    await seedAcceptedBenchmarkSurvey();
  } catch (error) {
    const status = document.getElementById('status');
    if (status) status.textContent = `Impossible de charger le Survey accepté : ${error.message}`;
  }

  const ensureVisible = () => {
    const sceneButton = document.getElementById(SCENE_BUTTON_ID);
    if (sceneButton) {
      sceneButton.hidden = false;
      sceneButton.disabled = false;
    } else if (sceneBenchmarkRequested()) {
      ensureSceneButton();
    }
  };

  ensureVisible();
  new MutationObserver(ensureVisible).observe(document.documentElement, { childList: true, subtree: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', enterSceneOnlyMode, { once: true });
} else {
  enterSceneOnlyMode();
}
