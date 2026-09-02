import './benchmark-test.js';
import './scene-required-inputs.js';
import './partial-scene-build.js';

const buildButton = document.querySelector('#build-bricks');
const apiInput = document.querySelector('#api-url');
const studsInput = document.querySelector('#studs');
const jsonPreview = document.querySelector('#json-preview');
const statusEl = document.querySelector('#status');

// In the simplified photo workflow the existing build button is still the
// canonical control, but it must remain visible without opening technical tools.
if (buildButton) {
  const advanced = document.querySelector('.advanced-panel');
  if (advanced?.parentNode) {
    const card = document.createElement('section');
    card.className = 'simple-card build-ready-card';
    card.innerHTML = '<div class="simple-heading"><div><p class="eyebrow">Dernière étape</p><h2>Construire la maquette</h2><p>BrickHouse construit tout ce qui est suffisamment résolu et laisse les zones encore inconnues hors de la maquette plutôt que de les inventer.</p></div></div>';
    buildButton.textContent = 'Construire ma maquette';
    buildButton.classList.add('primary', 'big-action');
    card.appendChild(buildButton);
    advanced.parentNode.insertBefore(card, advanced);
  }
}

function currentScene() {
  const raw = jsonPreview?.textContent?.trim();
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed?.schema_version === '0.2' && Array.isArray(parsed?.volumes) ? parsed : null;
  } catch {
    return null;
  }
}

function lastSceneSurveyValidationAllowsPartial() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.lastSceneSurveyValidation') || 'null');
    if (!payload?.scene || payload.scene.schema_version !== '0.2') return false;
    return !(payload.issues ?? []).some(issue => issue.severity === 'error');
  } catch {
    return false;
  }
}

function exposePartialBuildWhenSafe() {
  if (!buildButton || !currentScene() || !lastSceneSurveyValidationAllowsPartial()) return;
  buildButton.disabled = false;
  buildButton.textContent = 'Construire les briques fiables';
}

// The strict Scene gate can legitimately report projection blockers for an
// unresolved roof or exterior junction while the backend partial pipeline is
// still able to build the trustworthy shell. Keep that path available only
// after Survey → Scene validation has succeeded without errors.
if (jsonPreview && buildButton) {
  new MutationObserver(() => queueMicrotask(exposePartialBuildWhenSafe))
    .observe(jsonPreview, { childList: true, characterData: true, subtree: true });
  new MutationObserver(() => {
    if (buildButton.disabled) queueMicrotask(exposePartialBuildWhenSafe);
  }).observe(buildButton, { attributes: true, attributeFilter: ['disabled'] });
}

async function requestSceneBuild(base, scene, frontWidthStuds, { allowPartial = false } = {}) {
  const response = await fetch(`${base}/api/v1/build-scene`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scene,
      front_width_studs: frontWidthStuds,
      allow_partial: allowPartial,
    }),
  });
  const payload = await response.json();
  return { response, payload };
}

// Capture the click before photo.js' legacy BuildingModel build handler. For a
// normal BuildingModel proposal we do nothing and the existing handler runs.
document.addEventListener('click', async event => {
  if (!buildButton || event.target !== buildButton) return;
  const scene = currentScene();
  if (!scene) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  const base = apiInput.value.trim().replace(/\/$/, '');
  if (!base) { statusEl.textContent = 'URL API manquante.'; return; }

  buildButton.disabled = true;
  const frontWidthStuds = Number(studsInput.value) || 48;
  statusEl.textContent = 'BrickHouse construit la Scene complète…';
  try {
    let { response, payload } = await requestSceneBuild(base, scene, frontWidthStuds);

    if (!response.ok && response.status === 422 && lastSceneSurveyValidationAllowsPartial()) {
      statusEl.textContent = 'Certaines zones restent inconnues : construction des briques déjà fiables sans inventer le reste…';
      ({ response, payload } = await requestSceneBuild(base, scene, frontWidthStuds, { allowPartial: true }));
    }

    if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : `Erreur moteur HTTP ${response.status}`);
    if (!Array.isArray(payload?.brick_model?.parts) || !payload.brick_model.parts.length) {
      throw new Error('Le moteur a renvoyé une maquette sans pièces.');
    }
    if (!payload?.assembly_plan?.steps?.length) {
      throw new Error('Le moteur a renvoyé une maquette sans étapes de montage.');
    }

    localStorage.setItem('brickhouse.pendingArchitecturalScene', JSON.stringify({ scene }));
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(payload));
    window.location.href = './viewer.html';
  } catch (error) {
    statusEl.textContent = `Construction impossible : ${error.message}`;
    buildButton.disabled = false;
  }
}, true);
