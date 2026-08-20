const photosInput = document.querySelector('#photos');
const photoList = document.querySelector('#photo-list');
const notesInput = document.querySelector('#notes');
const knownWidthInput = document.querySelector('#known-width');
const studsInput = document.querySelector('#studs');
const apiInput = document.querySelector('#api-url');
const analyzeButton = document.querySelector('#analyze');
const refineButton = document.querySelector('#refine');
const downloadButton = document.querySelector('#download-model');
const reportButton = document.querySelector('#download-report');
const buildButton = document.querySelector('#build-bricks');
const statusEl = document.querySelector('#status');
const visionState = document.querySelector('#vision-state');
const photoLimits = document.querySelector('#photo-limits');
const emptyState = document.querySelector('#empty-state');
const resultEl = document.querySelector('#result');
const resultName = document.querySelector('#result-name');
const confidenceEl = document.querySelector('#confidence');
const confirmationCard = document.querySelector('#confirmation-card');
const questionsEl = document.querySelector('#questions');
const assumptionsEl = document.querySelector('#assumptions');
const proportionsCard = document.querySelector('#proportions-card');
const scaleBasisEl = document.querySelector('#scale-basis');
const proportionEvidenceEl = document.querySelector('#proportion-evidence');
const jsonPreview = document.querySelector('#json-preview');

let analysis = null;
let capabilities = null;
const DEFAULT_API_URL = 'https://brickhouse-api.onrender.com';
const FALLBACK_MAX_PHOTOS = 6;
const FALLBACK_MAX_BYTES = 12 * 1024 * 1024;
const FALLBACK_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

apiInput.value = localStorage.getItem('brickhouse.engineApiUrl') ?? DEFAULT_API_URL;

function apiBase() { return apiInput.value.trim().replace(/\/$/, ''); }
function limits() {
  return {
    maxPhotos: capabilities?.max_photos ?? FALLBACK_MAX_PHOTOS,
    maxBytes: capabilities?.max_photo_bytes ?? FALLBACK_MAX_BYTES,
    types: capabilities?.supported_photo_types ?? FALLBACK_TYPES,
  };
}
function selectedPhotos() { return [...(photosInput.files ?? [])]; }
function formatMb(bytes) { return `${Math.round(bytes / 1024 / 1024)} Mo`; }
function setVisionCard(ready, message) {
  visionState.classList.toggle('warning', !ready);
  visionState.innerHTML = `<strong>${ready ? 'Analyse photo prête' : 'Analyse photo indisponible'}</strong><p>${message}</p>`;
}

async function checkCapabilities() {
  const base = apiBase();
  capabilities = null;
  analyzeButton.disabled = true;
  if (!base) {
    setVisionCard(false, 'Aucune API BrickHouse configurée.');
    statusEl.textContent = 'Configurez l’API BrickHouse.';
    return;
  }
  statusEl.textContent = 'Vérification du moteur BrickHouse…';
  try {
    const response = await fetch(`${base}/api/v1/capabilities`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    capabilities = await response.json();
    const l = limits();
    photoLimits.textContent = `JPEG, PNG ou WebP · ${l.maxPhotos} photos maximum · ${formatMb(l.maxBytes)} maximum par photo`;
    if (capabilities.photo_analysis_ready) {
      const model = capabilities.photo_model ? ` · modèle ${capabilities.photo_model}` : '';
      setVisionCard(true, `Le moteur photo est prêt${model}. Version moteur ${capabilities.engine_revision.slice(0, 8)}.`);
      statusEl.textContent = 'Ajoutez vos photos puis lancez l’analyse.';
      analyzeButton.disabled = false;
    } else {
      const reason = capabilities.photo_analysis_reason === 'missing_server_api_key'
        ? 'La clé du fournisseur de vision n’est pas configurée sur le serveur.'
        : 'Le fournisseur de vision n’est pas prêt.';
      setVisionCard(false, `${reason} Les photos ne seront pas envoyées tant que cette fonction reste désactivée.`);
      statusEl.textContent = 'Analyse photo en attente d’activation du fournisseur de vision.';
    }
  } catch (error) {
    setVisionCard(false, `Impossible de vérifier le serveur : ${error.message}`);
    statusEl.textContent = 'Le serveur BrickHouse est indisponible ou en cours de réveil.';
  }
}

apiInput.addEventListener('change', () => {
  const base = apiBase();
  if (base) localStorage.setItem('brickhouse.engineApiUrl', base);
  else localStorage.removeItem('brickhouse.engineApiUrl');
  checkCapabilities();
});

function photoProblem(files) {
  const l = limits();
  if (!files.length) return 'Ajoutez au moins une photo.';
  if (files.length > l.maxPhotos) return `Maximum ${l.maxPhotos} photos.`;
  const badType = files.find(file => !l.types.includes(file.type));
  if (badType) return `Format non pris en charge : ${badType.name}.`;
  const tooLarge = files.find(file => file.size > l.maxBytes);
  if (tooLarge) return `${tooLarge.name} dépasse ${formatMb(l.maxBytes)}.`;
  return '';
}

function renderPhotoList() {
  const files = selectedPhotos();
  photoList.innerHTML = files.map((file, index) => `<div class="photo-chip" title="${file.name}">${index + 1}. ${file.name}</div>`).join('');
  const problem = photoProblem(files);
  if (problem && files.length) statusEl.textContent = problem;
  else if (files.length) statusEl.textContent = `${files.length} photo(s) prête(s). ${knownWidthInput.value ? 'La largeur connue fixera l’échelle après correction de perspective.' : 'Une largeur réelle connue améliorerait fortement l’échelle.'}`;
  analyzeButton.disabled = !capabilities?.photo_analysis_ready || Boolean(problem);
}

photosInput.addEventListener('change', renderPhotoList);
knownWidthInput.addEventListener('input', renderPhotoList);

function downloadJson(data, name) {
  const blob = new Blob([JSON.stringify(data, null, 2) + '\n'], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[char]));
}

function trialReport() {
  if (!analysis) return null;
  return {
    schema_version: '0.1',
    kind: 'brickhouse_photo_trial_report',
    created_at: new Date().toISOString(),
    server: {
      api_url: apiBase(),
      engine_revision: capabilities?.engine_revision ?? null,
      photo_provider: capabilities?.photo_provider ?? null,
      photo_model: capabilities?.photo_model ?? null,
    },
    input: {
      photos: selectedPhotos().map((file, index) => ({
        index: index + 1,
        name: file.name,
        media_type: file.type,
        bytes: file.size,
      })),
      known_front_width_m: knownWidthInput.value ? Number(knownWidthInput.value) : null,
      user_notes: notesInput.value.trim(),
      target_front_width_studs: Number(studsInput.value) || 48,
    },
    analysis,
  };
}

function renderAnalysis(value) {
  analysis = value;
  emptyState.hidden = true;
  resultEl.hidden = false;
  resultName.textContent = value.building.name;
  confidenceEl.textContent = `${Math.round(value.confidence * 100)} %`;
  const compatibility = value.m0_compatibility ?? { buildable: true, blockers: [], warnings: [] };
  const blockers = compatibility.blockers ?? [];
  const warnings = compatibility.warnings ?? [];
  confirmationCard.hidden = !value.needs_confirmation && !blockers.length && !warnings.length;
  confirmationCard.innerHTML = blockers.length
    ? `<h3>Architecture pas encore constructible par le moteur M0</h3><p>${blockers.map(escapeHtml).join(' ')}</p>`
    : warnings.length
      ? `<h3>À vérifier avant construction</h3><p>${warnings.map(escapeHtml).join(' ')}</p>`
      : '<h3>À confirmer</h3><p>Répondez aux points que vous connaissez. Vous pouvez aussi conserver les estimations actuelles.</p>';

  const evidence = value.proportion_evidence ?? [];
  proportionsCard.hidden = !value.scale_basis && !evidence.length;
  scaleBasisEl.textContent = value.scale_basis ? `Échelle : ${value.scale_basis}` : 'Échelle : provisoire, aucune base explicite fournie.';
  proportionEvidenceEl.innerHTML = evidence.length
    ? evidence.map(item => `<li><strong>${escapeHtml(item.facade)}</strong> — ${escapeHtml(item.observation)} <small>(${escapeHtml(item.method)}, ${Math.round((item.confidence ?? 0) * 100)} %)</small></li>`).join('')
    : '<li>Aucune justification géométrique explicite fournie.</li>';

  questionsEl.innerHTML = value.questions.length
    ? value.questions.map((q, index) => `<div class="question ${q.importance}" data-question-id="${escapeHtml(q.id)}"><strong>${escapeHtml(q.question)}</strong><small>${escapeHtml(q.reason)}</small><label for="answer-${index}">Votre réponse</label><textarea id="answer-${index}" class="answer" rows="2" placeholder="Écrivez ce que vous savez…"></textarea></div>`).join('')
    : '<p>Aucune question importante pour cette proposition.</p>';
  refineButton.disabled = !value.questions.length;
  const assumptionRows = [...(value.assumptions ?? []), ...warnings.map(w => `Limite moteur : ${w}`)];
  assumptionsEl.innerHTML = assumptionRows.length ? assumptionRows.map(item => `<li>${escapeHtml(item)}</li>`).join('') : '<li>Aucune hypothèse explicitée.</li>';
  jsonPreview.textContent = JSON.stringify(value.building, null, 2);
  downloadButton.disabled = false;
  reportButton.disabled = false;
  buildButton.disabled = !compatibility.buildable;
  if (!compatibility.buildable) statusEl.textContent = 'La maison a bien été comprise, mais cette architecture dépasse encore le moteur M0.';
}

function clarificationContext() {
  if (!analysis) return '';
  const answers = [...questionsEl.querySelectorAll('.question')].map((node, index) => {
    const answer = node.querySelector('.answer')?.value.trim() ?? '';
    if (!answer) return null;
    const q = analysis.questions[index];
    return `Q: ${q.question}\nR: ${answer}`;
  }).filter(Boolean);
  if (!answers.length) return '';
  return `\n\nREFINEMENT REQUEST. Here is the previous BrickHouse proposal:\n${JSON.stringify(analysis.building)}\n\nPrevious scale basis: ${analysis.scale_basis ?? 'unknown'}\nPrevious proportion evidence: ${JSON.stringify(analysis.proportion_evidence ?? [])}\n\nUser answers to BrickHouse clarification questions:\n${answers.join('\n\n')}\nUpdate the proposal to honor these answers. Facts explicitly supplied in these answers are user_provided. Re-evaluate assumptions, confidence, scale_basis, proportion_evidence, needs_confirmation and remaining questions.`;
}

async function runAnalysis(extraContext = '') {
  const files = selectedPhotos();
  const base = apiBase();
  const problem = photoProblem(files);
  if (problem) { statusEl.textContent = problem; return; }
  if (!capabilities?.photo_analysis_ready) { statusEl.textContent = 'L’analyse photo n’est pas activée sur ce serveur.'; return; }
  const form = new FormData();
  for (const file of files) form.append('photos', file, file.name);
  const notes = [notesInput.value.trim(), extraContext].filter(Boolean).join('\n');
  if (notes) form.append('user_notes', notes);
  if (knownWidthInput.value) form.append('known_front_width_m', knownWidthInput.value);
  analyzeButton.disabled = true;
  refineButton.disabled = true;
  downloadButton.disabled = true;
  reportButton.disabled = true;
  buildButton.disabled = true;
  statusEl.textContent = extraContext ? 'Mise à jour de la reconstruction avec vos réponses…' : 'Correction de perspective, comparaison des vues et reconstruction de la maison…';
  try {
    localStorage.setItem('brickhouse.engineApiUrl', base);
    const response = await fetch(`${base}/api/v1/analyze-photos`, { method: 'POST', body: form });
    const payload = await response.json();
    if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : `Erreur HTTP ${response.status}`);
    renderAnalysis(payload);
    if (payload.m0_compatibility?.buildable) statusEl.textContent = payload.needs_confirmation ? 'Proposition créée. Vérifiez les proportions, questions et hypothèses avant de construire.' : 'Proposition suffisamment fiable pour lancer la construction.';
  } catch (error) {
    statusEl.textContent = `Analyse impossible : ${error.message}`;
    if (analysis) {
      downloadButton.disabled = false;
      reportButton.disabled = false;
      buildButton.disabled = analysis.m0_compatibility?.buildable === false;
      refineButton.disabled = !analysis.questions.length;
    }
  } finally {
    renderPhotoList();
  }
}

analyzeButton.addEventListener('click', () => runAnalysis());
refineButton.addEventListener('click', () => {
  const context = clarificationContext();
  if (!context) { statusEl.textContent = 'Répondez à au moins une question avant de relancer l’analyse.'; return; }
  runAnalysis(context);
});
downloadButton.addEventListener('click', () => {
  if (analysis) downloadJson(analysis.building, `${analysis.building.id}.json`);
});
reportButton.addEventListener('click', () => {
  const report = trialReport();
  if (report) downloadJson(report, `${analysis.building.id}-photo-trial.json`);
});
buildButton.addEventListener('click', async () => {
  if (!analysis) return;
  if (analysis.m0_compatibility?.buildable === false) { statusEl.textContent = 'Cette proposition n’est pas encore compatible avec le moteur M0.'; return; }
  const base = apiBase();
  if (!base) { statusEl.textContent = 'URL API manquante.'; return; }
  buildButton.disabled = true;
  statusEl.textContent = 'BrickHouse transforme la proposition en maquette constructible…';
  try {
    const response = await fetch(`${base}/api/v1/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ building: analysis.building, front_width_studs: Number(studsInput.value) || 48 }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : `Erreur moteur HTTP ${response.status}`);
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(payload));
    window.location.href = './viewer.html';
  } catch (error) {
    statusEl.textContent = `Construction impossible : ${error.message}`;
    buildButton.disabled = false;
  }
});

checkCapabilities();
