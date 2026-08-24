import { loadBundledBenchmark } from './benchmark-fixtures.js';

const SLOT_BY_PHOTO_INDEX = new Map([
  [1, 'front'],
  [2, 'right'],
  [3, 'left'],
  [4, 'left'],
  [5, 'rear'],
]);

function makeButton() {
  const firstCard = document.querySelector('.simple-card');
  if (!firstCard || document.querySelector('#load-real-house-benchmark')) return;

  const box = document.createElement('div');
  box.className = 'field';
  box.innerHTML = `
    <label>Test rapide du logiciel</label>
    <button id="load-real-house-benchmark" class="primary" type="button">Charger la maison test — 5 photos</button>
    <small id="benchmark-load-status">Recharge les cinq photos de référence directement dans les zones ci-dessous. Les orientations restent de simples indices de capture, pas des vérités imposées à l’IA.</small>
  `;
  firstCard.querySelector('.simple-heading')?.insertAdjacentElement('afterend', box);
  box.querySelector('#load-real-house-benchmark')?.addEventListener('click', loadBenchmark);
}

function filesForSlot(photos, slotName) {
  return photos.filter((photo) => SLOT_BY_PHOTO_INDEX.get(photo.photo_index) === slotName);
}

function setSlotFiles(slotName, records) {
  const slot = document.querySelector(`.guided-photo-slot[data-slot="${slotName}"]`);
  const input = slot?.querySelector('.guided-photo-input');
  if (!input || typeof DataTransfer === 'undefined') return;

  const transfer = new DataTransfer();
  for (const record of records) transfer.items.add(record.file);
  input.files = transfer.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

async function loadBenchmark() {
  const button = document.querySelector('#load-real-house-benchmark');
  const status = document.querySelector('#benchmark-load-status');
  if (!button || !status) return;

  button.disabled = true;
  status.textContent = 'Chargement des cinq photos originales…';

  try {
    const { manifest, photos } = await loadBundledBenchmark('real-house-5');
    if (photos.length !== 5) throw new Error(`benchmark incomplet : ${photos.length}/5 photos`);

    for (const slotName of ['front', 'front_left', 'left', 'rear', 'right', 'front_right']) {
      setSlotFiles(slotName, filesForSlot(photos, slotName));
    }

    const orientation = document.querySelector('#confirm-guided-orientations');
    if (orientation) orientation.checked = false;

    status.textContent = `${manifest.title} chargée : 5 photos. Vous pouvez maintenant créer le PDF d’analyse ou lancer les outils avancés exactement comme avec des photos utilisateur.`;
  } catch (error) {
    status.textContent = `Impossible de charger la maison test : ${error.message}. Le benchmark doit contenir les cinq JPEG originaux dans frontend/benchmarks/real-house-5/.`;
  } finally {
    button.disabled = false;
  }
}

makeButton();
