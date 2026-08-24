import { loadBundledBenchmark } from './benchmark-fixtures.js';

const SLOT_BY_PHOTO_INDEX = new Map([
  [1, 'front'],
  [2, 'right'],
  [3, 'left'],
  [4, 'left'],
  [5, 'rear'],
]);

function makeCaptureGuidance() {
  const firstCard = document.querySelector('.simple-card');
  if (!firstCard || document.querySelector('#capture-overlap-guidance')) return;

  const guidance = document.createElement('div');
  guidance.id = 'capture-overlap-guidance';
  guidance.className = 'field';
  guidance.innerHTML = `
    <label>Conseil essentiel pour relier les vues</label>
    <small><strong>Gardez toujours un élément reconnaissable d’une photo à la suivante.</strong> Par exemple : un angle de mur, une fenêtre, une terrasse, un garde-corps, une cheminée ou un morceau de toiture. Boldungo utilise ces éléments communs comme ancres pour comprendre que deux images montrent bien le même bâtiment et pour savoir si la caméra est restée sur le même côté ou a franchi un angle. Une vue partielle est utile si elle conserve une jonction claire avec une autre vue.</small>
  `;
  firstCard.querySelector('.simple-heading')?.insertAdjacentElement('afterend', guidance);
}

function makeButton() {
  const firstCard = document.querySelector('.simple-card');
  if (!firstCard || document.querySelector('#load-real-house-benchmark')) return;

  const box = document.createElement('div');
  box.className = 'field';
  box.innerHTML = `
    <label>Test rapide du logiciel</label>
    <button id="load-real-house-benchmark" class="primary" type="button">Charger la maison test — 5 photos</button>
    <small id="benchmark-load-status">Recharge les cinq photos de référence directement dans les zones ci-dessous. Ordre du benchmark : 1 façade, 2 côté droit, 3 côté gauche, 4 seconde vue du côté gauche, 5 vue arrière / 3/4 arrière partielle. Les orientations restent de simples indices de capture, pas des vérités imposées à l’IA.</small>
  `;
  const guidance = document.querySelector('#capture-overlap-guidance');
  (guidance ?? firstCard.querySelector('.simple-heading'))?.insertAdjacentElement('afterend', box);
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

    status.textContent = `${manifest.title} chargée : 5 photos. Les vues se recouvrent par des éléments communs ; Boldungo doit utiliser ces ancres pour reconstruire la continuité sans inventer les zones cachées.`;
  } catch (error) {
    status.textContent = `Impossible de charger la maison test : ${error.message}. Le benchmark doit contenir les cinq JPEG originaux dans frontend/benchmarks/real-house-5/.`;
  } finally {
    button.disabled = false;
  }
}

makeCaptureGuidance();
makeButton();
