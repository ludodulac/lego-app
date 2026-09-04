const BENCHMARK_ID = 'real-house-5';
const MANIFEST_URL = `./benchmarks/${BENCHMARK_ID}/manifest.json`;
const SLOT_MAPPING = new Map([
  [1, { slot: 'front', detail: false }],
  [2, { slot: 'right', detail: false }],
  [3, { slot: 'left', detail: false }],
  [4, { slot: 'left', detail: false }],
  [5, { slot: 'rear', detail: false }],
]);

function requestedBenchmark() {
  return new URLSearchParams(globalThis.location?.search || '').get('benchmark');
}

function inputFor(slot, detail) {
  const className = detail ? 'detail-photo-slot' : 'guided-photo-slot';
  const inputClass = detail ? 'detail-photo-input' : 'guided-photo-input';
  return document.querySelector(`.${className}[data-slot="${slot}"] .${inputClass}`);
}

function setInputFiles(input, files) {
  const transfer = new DataTransfer();
  files.forEach(file => transfer.items.add(file));
  input.files = transfer.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

async function fetchAsFile(path) {
  const response = await fetch(`./benchmarks/${BENCHMARK_ID}/${path}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  const blob = await response.blob();
  return new File([blob], path, { type: blob.type || 'image/jpeg' });
}

async function preloadBenchmark() {
  if (requestedBenchmark() !== BENCHMARK_ID) return;

  const status = document.querySelector('#ai-package-status');
  document.body.dataset.benchmark = BENCHMARK_ID;
  if (status) status.textContent = `Chargement du benchmark ${BENCHMARK_ID}…`;

  try {
    const manifestResponse = await fetch(MANIFEST_URL, { cache: 'no-store' });
    if (!manifestResponse.ok) throw new Error(`manifest: HTTP ${manifestResponse.status}`);
    const manifest = await manifestResponse.json();
    if (manifest.id !== BENCHMARK_ID || manifest.orientation_authority !== 'capture_hint') {
      throw new Error('manifest benchmark incompatible');
    }

    const grouped = new Map();
    for (const photo of manifest.photos || []) {
      const mapping = SLOT_MAPPING.get(photo.photo_index);
      if (!mapping) continue;
      const key = `${mapping.detail ? 'detail' : 'guided'}:${mapping.slot}`;
      if (!grouped.has(key)) grouped.set(key, { ...mapping, files: [] });
      grouped.get(key).files.push(await fetchAsFile(photo.path));
    }

    if ([...grouped.values()].reduce((sum, group) => sum + group.files.length, 0) !== 5) {
      throw new Error('le benchmark doit contenir exactement 5 photos mappées');
    }

    for (const group of grouped.values()) {
      const input = inputFor(group.slot, group.detail);
      if (!input) throw new Error(`champ photo introuvable: ${group.slot}`);
      setInputFiles(input, group.files);
    }

    const orientationCheckbox = document.querySelector('#confirm-guided-orientations');
    if (orientationCheckbox) orientationCheckbox.checked = false;
    const knownWidth = document.querySelector('#known-width');
    if (knownWidth) knownWidth.value = '';
    const notes = document.querySelector('#notes');
    if (notes) notes.value = '';

    if (status) {
      status.textContent = `Benchmark ${BENCHMARK_ID} chargé · 5 photos originales · orientations = indices de capture · largeur inconnue · prêt à créer le PDF Survey.`;
    }
  } catch (error) {
    if (status) status.textContent = `Benchmark ${BENCHMARK_ID} NON chargé : ${error.message}`;
    console.error(error);
  }
}

// Run after the page's other module scripts have had a chance to attach their
// input change listeners. Normal photo.html visits are a strict no-op.
setTimeout(preloadBenchmark, 0);
