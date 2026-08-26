const messageEl = document.querySelector('#message');

async function loadFirstBricks() {
  try {
    const response = await fetch('./brickhouse-partial-export.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const bundle = await response.json();
    if (!Array.isArray(bundle?.brick_model?.parts) || !bundle.brick_model.parts.length) {
      throw new Error('export BrickHouse vide');
    }
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(bundle));
    window.location.href = './viewer.html';
  } catch (error) {
    messageEl.textContent = `Impossible de charger les premières briques : ${error.message}`;
  }
}

loadFirstBricks();

export { loadFirstBricks };
