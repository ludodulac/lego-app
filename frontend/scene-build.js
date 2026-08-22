const buildButton = document.querySelector('#build-bricks');
const apiInput = document.querySelector('#api-url');
const studsInput = document.querySelector('#studs');
const jsonPreview = document.querySelector('#json-preview');
const statusEl = document.querySelector('#status');

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
  statusEl.textContent = 'BrickHouse construit la Scene complète, terrasse et escalier compris…';
  try {
    const response = await fetch(`${base}/api/v1/build-scene`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scene, front_width_studs: Number(studsInput.value) || 48 }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : `Erreur moteur HTTP ${response.status}`);
    localStorage.setItem('brickhouse.pendingArchitecturalScene', JSON.stringify({ scene }));
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(payload));
    window.location.href = './viewer.html';
  } catch (error) {
    statusEl.textContent = `Construction impossible : ${error.message}`;
    buildButton.disabled = false;
  }
}, true);
