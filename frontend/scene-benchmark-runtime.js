import './scene-handoff-source-lock.js?v=scene-runtime-bh147';
import './scene-handoff-contract-audit-v44.js?v=scene-runtime-bh147';
import './scene-handoff-stage-lock-v45.js?v=scene-runtime-bh147';
import './scene-handoff-output-frame-v46.js?v=scene-runtime-bh147';
import './photo-slot-previews.js?v=scene-runtime-bh147';
import './scene-handoff-photo-evidence.js?v=scene-runtime-bh147';

const BENCHMARK_ID = 'real-house-5';
const ACCEPTED_SURVEY_PARTS = [1, 2, 3, 4, 5].map(index =>
  `./benchmarks/${BENCHMARK_ID}/accepted-survey-real-v0.1.part${index}`
);
const MANIFEST_URL = `./benchmarks/${BENCHMARK_ID}/manifest.json`;
const SLOT_MAPPING = new Map([
  [1, 'front'],
  [2, 'right'],
  [3, 'left'],
  [4, 'left'],
  [5, 'rear'],
]);

function requestedSceneBenchmark() {
  const params = new URLSearchParams(globalThis.location?.search || '');
  return params.get('benchmark') === BENCHMARK_ID && params.get('stage') === 'scene';
}

async function fetchAsFile(path) {
  const response = await fetch(`./benchmarks/${BENCHMARK_ID}/${path}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  const blob = await response.blob();
  return new File([blob], path, { type: blob.type || 'image/jpeg' });
}

async function fetchAcceptedSurvey() {
  const responses = await Promise.all(ACCEPTED_SURVEY_PARTS.map(url => fetch(url, { cache: 'no-store' })));
  responses.forEach((response, index) => {
    if (!response.ok) throw new Error(`accepted Survey part ${index + 1}: HTTP ${response.status}`);
  });
  const raw = (await Promise.all(responses.map(response => response.text()))).join('');
  return JSON.parse(raw);
}

function setInputFiles(input, files) {
  const transfer = new DataTransfer();
  files.forEach(file => transfer.items.add(file));
  input.files = transfer.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

async function seedSceneBenchmark() {
  const status = document.querySelector('#status');
  const packageStatus = document.querySelector('#ai-package-status');
  const button = document.querySelector('#download-scene-handoff');
  if (!requestedSceneBenchmark()) {
    if (status) status.textContent = 'Ouvrez cette page depuis le benchmark Scene.';
    if (button) button.disabled = true;
    return;
  }

  try {
    if (button) button.disabled = true;
    if (packageStatus) packageStatus.textContent = 'Chargement du Survey réel accepté et des cinq photos…';

    const [survey, manifestResponse] = await Promise.all([
      fetchAcceptedSurvey(),
      fetch(MANIFEST_URL, { cache: 'no-store' }),
    ]);
    if (!manifestResponse.ok) throw new Error(`manifest: HTTP ${manifestResponse.status}`);

    const manifest = await manifestResponse.json();
    if (survey?.schema_version !== '0.1' || !Array.isArray(survey?.observations)) {
      throw new Error('checkpoint Survey invalide');
    }
    if (manifest?.id !== BENCHMARK_ID) throw new Error('manifest benchmark invalide');

    const grouped = new Map();
    for (const photo of manifest.photos || []) {
      const slot = SLOT_MAPPING.get(photo.photo_index);
      if (!slot) continue;
      if (!grouped.has(slot)) grouped.set(slot, []);
      grouped.get(slot).push(await fetchAsFile(photo.path));
    }
    const count = [...grouped.values()].reduce((sum, files) => sum + files.length, 0);
    if (count !== 5) throw new Error(`5 photos attendues, ${count} chargée(s)`);

    for (const [slot, files] of grouped) {
      const input = document.querySelector(`.guided-photo-slot[data-slot="${slot}"] .guided-photo-input`);
      if (!input) throw new Error(`champ photo manquant: ${slot}`);
      setInputFiles(input, files);
    }

    localStorage.setItem('brickhouse.pendingArchitecturalSurvey', JSON.stringify({
      survey,
      valid_for_scene_fusion: true,
      issues: [],
      source: 'accepted_real_survey_checkpoint_stage2',
    }));

    if (packageStatus) packageStatus.textContent = 'Survey réel accepté chargé · 5 photos prêtes.';
    if (status) status.textContent = 'Prêt : créez le PDF Relevé → Scene 3D.';
    if (button) button.disabled = false;
  } catch (error) {
    if (status) status.textContent = `Préparation Scene impossible : ${error.message}`;
    if (packageStatus) packageStatus.textContent = 'Le benchmark Scene n’a pas pu être préparé.';
    if (button) button.disabled = true;
    console.error(error);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', seedSceneBenchmark, { once: true });
} else {
  seedSceneBenchmark();
}
