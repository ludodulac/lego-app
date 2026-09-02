const fileInput = document.querySelector('#scene-file');
const apiInput = document.querySelector('#api-url');
const studsInput = document.querySelector('#front-width-studs');
const allowPartialInput = document.querySelector('#allow-partial');
const buildButton = document.querySelector('#build-scene');
const messageEl = document.querySelector('#message');
const detailsEl = document.querySelector('#details');

const DEFAULT_API_URL = 'https://brickhouse-api.onrender.com';
let currentScene = null;

function setMessage(text, details = null) {
  messageEl.textContent = text;
  if (details == null || details === '') {
    detailsEl.hidden = true;
    detailsEl.textContent = '';
    return;
  }
  detailsEl.hidden = false;
  detailsEl.textContent = typeof details === 'string' ? details : JSON.stringify(details, null, 2);
}

function apiBase() {
  return apiInput.value.trim().replace(/\/$/, '');
}

function errorDetail(payload, status) {
  if (typeof payload?.detail === 'string') return payload.detail;
  if (Array.isArray(payload?.detail)) return payload.detail.map(item => item.msg ?? JSON.stringify(item)).join(' · ');
  return `Erreur moteur HTTP ${status}`;
}

async function postJson(path, body) {
  const base = apiBase();
  if (!base) throw new Error('L’API moteur n’est pas configurée.');
  const response = await fetch(`${base}${path}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(errorDetail(payload, response.status));
  return payload;
}

function validateLocalScene(scene) {
  if (!scene || typeof scene !== 'object') throw new Error('Le fichier JSON ne contient pas un objet.');
  if (scene.schema_version !== '0.2') throw new Error('Cette page attend une ArchitecturalScene schema_version 0.2.');
  if (!Array.isArray(scene.volumes) || scene.volumes.length === 0) throw new Error('La scène ne contient aucun volume.');
  if (!Array.isArray(scene.openings)) throw new Error('La scène ne contient pas de tableau openings.');
}

fileInput.addEventListener('change', async () => {
  const file = fileInput.files?.[0];
  currentScene = null;
  buildButton.disabled = true;
  if (!file) {
    setMessage('Choisissez une ArchitecturalScene JSON pour commencer.');
    return;
  }
  try {
    const scene = JSON.parse(await file.text());
    validateLocalScene(scene);
    currentScene = scene;
    buildButton.disabled = false;
    setMessage(`Scène chargée : ${scene.name ?? scene.id ?? file.name}. Elle n’est pas enregistrée dans le dépôt.`);
  } catch (error) {
    setMessage(`Impossible de charger la scène : ${error.message}`);
  }
});

apiInput.value = localStorage.getItem('brickhouse.engineApiUrl') ?? DEFAULT_API_URL;
apiInput.addEventListener('change', () => {
  const value = apiBase();
  if (value) localStorage.setItem('brickhouse.engineApiUrl', value);
  else localStorage.removeItem('brickhouse.engineApiUrl');
});

buildButton.addEventListener('click', async () => {
  if (!currentScene) return;
  const frontWidthStuds = Number(studsInput.value);
  if (!Number.isInteger(frontWidthStuds) || frontWidthStuds <= 0 || frontWidthStuds > 256) {
    setMessage('La largeur LEGO doit être un nombre entier entre 1 et 256 tenons.');
    return;
  }

  buildButton.disabled = true;
  try {
    localStorage.setItem('brickhouse.engineApiUrl', apiBase());
    setMessage('Validation déterministe de l’ArchitecturalScene…');
    const validation = await postJson('/api/v1/validate-scene', currentScene);
    const blockers = (validation.projection?.issues ?? []).filter(issue => issue.severity === 'blocker');
    if (blockers.length && !allowPartialInput.checked) {
      setMessage('La scène stricte contient encore des points bloquants.', blockers);
      return;
    }

    setMessage('Génération du vrai modèle LEGO, de la nomenclature et des étapes de montage…');
    const bundle = await postJson('/api/v1/build-scene', {
      scene: currentScene,
      front_width_studs: frontWidthStuds,
      allow_partial: allowPartialInput.checked,
    });

    if (!Array.isArray(bundle?.brick_model?.parts) || bundle.brick_model.parts.length === 0) {
      throw new Error('Le moteur a renvoyé un export sans pièces LEGO.');
    }
    if (!bundle?.assembly_plan?.steps?.length) {
      throw new Error('Le moteur a renvoyé un export sans étapes de montage.');
    }

    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(bundle));
    window.location.href = './viewer.html';
  } catch (error) {
    setMessage(`Impossible de construire : ${error.message}`);
  } finally {
    buildButton.disabled = currentScene == null;
  }
});

export { postJson, validateLocalScene };
