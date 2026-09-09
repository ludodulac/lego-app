const buildButton = document.querySelector('#build-bricks');
const statusEl = document.querySelector('#status');
const studsInput = document.querySelector('#studs');
const apiInput = document.querySelector('#api-url');

function apiBase() {
  return apiInput?.value.trim().replace(/\/$/, '') ?? '';
}

function pendingSceneValidation() {
  try {
    const raw = sessionStorage.getItem('brickhouse.validatedScene');
    return raw ? JSON.parse(raw) : null;
  } catch {
    sessionStorage.removeItem('brickhouse.validatedScene');
    return null;
  }
}

window.addEventListener('brickhouse:scene-validated', (event) => {
  if (event.detail?.scene) sessionStorage.setItem('brickhouse.validatedScene', JSON.stringify(event.detail));
});

buildButton?.addEventListener('click', async (event) => {
  const validation = pendingSceneValidation();
  if (!validation?.scene) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  const base = apiBase();
  if (!base) {
    statusEl.textContent = 'URL API manquante.';
    return;
  }

  buildButton.disabled = true;
  statusEl.textContent = 'BrickHouse construit la Scene architecturale complète…';
  try {
    const response = await fetch(`${base}/api/v1/build-scene`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scene: validation.scene,
        front_width_studs: Number(studsInput?.value) || 48,
        allow_partial: true,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : `Erreur moteur HTTP ${response.status}`);
    localStorage.setItem('brickhouse.pendingArchitecturalScene', JSON.stringify(validation));
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(payload));
    sessionStorage.removeItem('brickhouse.validatedScene');
    window.location.href = './viewer.html';
  } catch (error) {
    statusEl.textContent = `Construction impossible : ${error.message}`;
    buildButton.disabled = false;
  }
}, true);
