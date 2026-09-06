const BENCHMARK_ID = 'real-house-5';
const VALIDATED_CANDIDATE_SHA = '5cf374b0c8a70bb9823c2e69a1367461d75508f9';
const CANDIDATE_URL = `https://raw.githubusercontent.com/ludodulac/lego-app/${VALIDATED_CANDIDATE_SHA}/tests/fixtures/real_house_5_scene_candidate.json`;

const jsonInput = document.querySelector('#scene-result-json');
const fileInput = document.querySelector('#scene-result-file');
const status = document.querySelector('#scene-result-status');

function shouldPreloadCandidate() {
  const params = new URLSearchParams(globalThis.location.search);
  return params.get('benchmark') === BENCHMARK_ID && params.get('stage') === 'scene';
}

async function preloadValidatedCandidate() {
  if (!shouldPreloadCandidate() || !jsonInput) return;
  if (jsonInput.value.trim() || fileInput?.files?.length) return;

  status.textContent = 'Chargement du candidat Scene validé BH-151…';
  try {
    const response = await fetch(CANDIDATE_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const scene = await response.json();
    if (scene?.schema_version !== '0.2' || scene?.id !== 'brickhouse-scene-real-house-5-candidate') {
      throw new Error('checkpoint Scene inattendu');
    }

    jsonInput.value = JSON.stringify(scene, null, 2);
    jsonInput.dataset.preloadedCandidate = 'bh-151';
    jsonInput.dataset.preloadedCandidateSha = VALIDATED_CANDIDATE_SHA;
    jsonInput.closest('details')?.setAttribute('open', '');
    jsonInput.dispatchEvent(new Event('input', { bubbles: true }));
    status.textContent = 'Candidat Scene BH-151 préchargé. Cliquez sur « Importer et vérifier la Scene » pour exécuter les contrôles Survey → Scene.';
  } catch (error) {
    status.textContent = `Candidat Scene validé indisponible : ${error.message}. Vous pouvez toujours importer brickhouse-scene-result.json manuellement.`;
  }
}

preloadValidatedCandidate();
