const message = document.querySelector('#message');

async function loadReference() {
  try {
    const response = await fetch('./brickhouse-scene-current.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const scene = await response.json();
    if (scene?.schema_version !== '0.2' || !Array.isArray(scene?.volumes)) {
      throw new Error('référence ArchitecturalScene invalide');
    }
    localStorage.setItem('brickhouse.previewArchitecturalScene', JSON.stringify(scene));
    message.textContent = 'Référence BrickHouse chargée. Ouverture de la reconstruction 3D…';
    window.location.replace('./scene-viewer.html');
  } catch (error) {
    message.textContent = `Impossible de charger la référence BrickHouse : ${error.message}`;
  }
}

loadReference();
