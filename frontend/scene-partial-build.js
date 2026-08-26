const buildButton = document.querySelector('#build-partial-lego');
const messageEl = document.querySelector('#message');
const DEFAULT_API_URL = 'https://brickhouse-api.onrender.com';

function loadScene() {
  const keys = [
    'brickhouse.previewArchitecturalScene',
    'brickhouse.pendingSceneValidation',
    'brickhouse.lastSceneSurveyValidation',
  ];
  for (const key of keys) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      const value = JSON.parse(raw);
      const candidate = value?.scene ?? value;
      if (candidate?.schema_version === '0.2' && Array.isArray(candidate.volumes)) {
        return candidate;
      }
    } catch {
      // Try the next stored scene source.
    }
  }
  return null;
}

function engineApiUrl() {
  return (localStorage.getItem('brickhouse.engineApiUrl') ?? DEFAULT_API_URL)
    .trim()
    .replace(/\/$/, '');
}

async function buildTrustworthySubset() {
  const scene = loadScene();
  if (!scene) {
    messageEl.textContent = 'Aucune reconstruction architecturale disponible pour lancer la maquette LEGO.';
    return;
  }
  const base = engineApiUrl();
  if (!base) {
    messageEl.textContent = 'L’API moteur BrickHouse n’est pas configurée.';
    return;
  }

  buildButton.disabled = true;
  messageEl.textContent = 'BrickHouse prépare les premières briques fiables sans compléter les zones encore inconnues…';
  try {
    localStorage.setItem('brickhouse.engineApiUrl', base);
    const response = await fetch(`${base}/api/v1/build-scene`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scene,
        front_width_studs: 48,
        allow_partial: true,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(
        typeof payload.detail === 'string'
          ? payload.detail
          : `Erreur moteur HTTP ${response.status}`,
      );
    }
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(payload));
    window.location.href = './viewer.html';
  } catch (error) {
    messageEl.textContent = `Impossible de préparer les premières briques : ${error.message}`;
    buildButton.disabled = false;
  }
}

if (buildButton) {
  buildButton.addEventListener('click', buildTrustworthySubset);
}

export { buildTrustworthySubset, loadScene };
