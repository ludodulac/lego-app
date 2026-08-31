import './scene-survey-gate.js';

const surveyImportButton = document.querySelector('#import-analysis');
const surveyExternalInput = document.querySelector('#external-analysis');
const surveyExternalFile = document.querySelector('#external-analysis-file');
const surveyApiInput = document.querySelector('#api-url');
const surveyKnownWidthInput = document.querySelector('#known-width');
const surveyStatus = document.querySelector('#status');
const surveyEmpty = document.querySelector('#empty-state');
const surveyResult = document.querySelector('#result');
const surveyResultName = document.querySelector('#result-name');
const surveyConfidence = document.querySelector('#confidence');
const surveyConfirmation = document.querySelector('#confirmation-card');
const surveyQuestions = document.querySelector('#questions');
const surveyAssumptions = document.querySelector('#assumptions');
const surveyProportions = document.querySelector('#proportions-card');
const surveyScaleBasis = document.querySelector('#scale-basis');
const surveyEvidence = document.querySelector('#proportion-evidence');
const surveyPreview = document.querySelector('#json-preview');
const surveyRefine = document.querySelector('#refine');
const surveyDownload = document.querySelector('#download-model');
const surveyDownloadValidated = document.querySelector('#download-survey');
const surveyReplace = document.querySelector('#replace-survey');
const surveyReport = document.querySelector('#download-report');
const surveyBuild = document.querySelector('#build-bricks');
const surveySceneHandoffHome = document.querySelector('#scene-handoff-home');
const SCENE_HANDOFF_VERSION = 'scene-handoff-0.1';
const SCENE_HANDOFF_FILENAME = 'BRICKHOUSE-SURVEY-TO-SCENE.txt';
let currentValidatedSurvey = null;
let replaceMode = false;

function surveyApiBase() { return surveyApiInput.value.trim().replace(/\/$/, ''); }
function surveyEscape(value) { return String(value).replace(/[&<>\"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;' }[char])); }
function safeFilename(value) { return String(value || 'brickhouse-survey').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase() || 'brickhouse-survey'; }
function downloadBlob(filename, content, type) { const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url); }
function downloadJson(filename, value) { downloadBlob(filename, JSON.stringify(value, null, 2) + '\n', 'application/json;charset=utf-8'); }

function extractJsonObject(raw) {
  let value = raw.trim();
  if (value.startsWith('```')) {
    const lines = value.split(/\r?\n/);
    if (lines[0].trim().toLowerCase() === '```json' || lines[0].trim() === '```') lines.shift();
    value = lines.join('\n').trim();
  }
  const start = value.indexOf('{');
  if (start < 0) return value;
  let depth = 0, inString = false, escaped = false;
  for (let index = start; index < value.length; index += 1) {
    const char = value[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') { inString = true; continue; }
    if (char === '{') depth += 1;
    else if (char === '}' && --depth === 0) return value.slice(start, index + 1);
  }
  return value.slice(start);
}

function isArchitecturalSurvey(value) {
  return value?.schema_version === '0.1'
    && value?.canonical_frame?.front_facade === 'front'
    && Array.isArray(value?.photos)
    && Array.isArray(value?.observations)
    && !value?.building;
}

function frontWidthMeasurement(survey) {
  return (survey?.known_measurements ?? []).find(item => item.kind === 'front_width') ?? null;
}

function withKnownWidth(survey) {
  const clone = JSON.parse(JSON.stringify(survey));
  const typed = Number(surveyKnownWidthInput?.value);
  if (!Number.isFinite(typed) || typed <= 0) return clone;
  clone.known_measurements = (clone.known_measurements ?? []).filter(item => item.kind !== 'front_width');
  clone.known_measurements.push({ kind: 'front_width', value: typed, units: 'm', source: { kind: 'user_provided', confidence: 0.99 } });
  localStorage.setItem('brickhouse.knownFrontWidthM', String(typed));
  return clone;
}

function pendingValidatedSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return payload?.valid_for_scene_fusion ? payload.survey : null;
  } catch { return null; }
}

function persistEnrichedSurvey(survey) {
  currentValidatedSurvey = survey;
  try {
    const pending = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    if (pending) {
      pending.survey = survey;
      localStorage.setItem('brickhouse.pendingArchitecturalSurvey', JSON.stringify(pending));
    }
  } catch { /* no-op: the downloadable handoff still contains the enriched Survey */ }
  surveyPreview.textContent = JSON.stringify(survey, null, 2);
}

async function createSceneHandoff() {
  if (!currentValidatedSurvey) {
    surveyStatus.textContent = 'Aucun ArchitecturalSurvey validé disponible pour préparer la Scene.';
    return;
  }
  const enriched = withKnownWidth(currentValidatedSurvey);
  persistEnrichedSurvey(enriched);
  surveyStatus.textContent = 'Préparation du fichier unique Survey → Scene…';
  try {
    const response = await fetch('./brickhouse-survey-to-scene-prompt.txt', { cache: 'no-store' });
    if (!response.ok) throw new Error(`prompt Survey → Scene : HTTP ${response.status}`);
    const prompt = await response.text();
    const handoff = `BRICKHOUSE — HANDOFF SURVEY → SCENE\nHANDOFF_VERSION=${SCENE_HANDOFF_VERSION}\n\nCe fichier est l'unique entrée de cette étape. Exécute immédiatement la reconstruction Survey → Scene sans demander de confirmation et sans demander d'autre fichier.\n\nENTRÉE AUTORITATIVE\nLe JSON ArchitecturalSurvey v0.1 placé à la fin de ce fichier est déjà validé par BrickHouse. Il est la source de vérité. Ne change ni son inventaire, ni ses IDs, ni ses relations certaines.\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé exactement brickhouse-scene-result.json. Son contenu doit être UNIQUEMENT un objet ArchitecturalScene v0.2 complet à la racine, avec schema_version \"0.2\". Ne produis pas d'enveloppe external-bundle, ne renvoie pas le Survey, ne renvoie pas la topologie et ne mets pas la Scene dans une clé \"scene\".\n\nRÈGLES D'EXÉCUTION\n- applique intégralement le prompt Survey → Scene inclus ci-dessous ;\n- préserve les IDs Survey des openings/platforms/stairs ;\n- préserve les relations certaines ;\n- si une relation physique est comprise mais son raccord métrique est caché, utilise geometry_status:\"unresolved\" ;\n- n'invente aucune géométrie cachée pour rendre la construction possible ;\n- si une métrique n'est pas suffisamment contrainte, respecte les null/unknown autorisés par le contrat ;\n- effectue l'audit final du prompt avant de créer le fichier.\n\nLa réponse finale du chat doit seulement annoncer ou joindre brickhouse-scene-result.json.\n\n================ PROMPT SURVEY → SCENE ================\n${prompt}\n\n================ ARCHITECTURAL SURVEY VALIDÉ ================\n${JSON.stringify(enriched, null, 2)}\n`;
    downloadBlob(SCENE_HANDOFF_FILENAME, handoff, 'text/plain;charset=utf-8');
    const width = frontWidthMeasurement(enriched);
    surveyStatus.textContent = `${SCENE_HANDOFF_FILENAME} prêt · ${SCENE_HANDOFF_VERSION}${width ? ` · largeur avant ${width.value} m incluse` : ''}. Envoyez uniquement ce fichier à l'IA.`;
  } catch (error) {
    surveyStatus.textContent = `Impossible de préparer le fichier Survey → Scene : ${error.message}`;
  }
}

function isSurveyExtension(base, candidate) {
  if (!base || !candidate || base.id !== candidate.id) return false;
  const baseIndexes = new Set((base.photos ?? []).map(photo => photo.photo_index));
  return (candidate.photos ?? []).some(photo => !baseIndexes.has(photo.photo_index));
}

function renderSurveyValidation(payload, { extended = false, replaced = false } = {}) {
  const survey = payload.survey;
  const issues = payload.issues ?? [];
  const errors = issues.filter(issue => issue.severity === 'error');
  const warnings = issues.filter(issue => issue.severity !== 'error');
  const openingCount = survey.observations.filter(item => item.kind === 'opening').length;
  const certainCount = survey.observations.filter(item => item.certainty === 'certain').length;
  const knownWidth = frontWidthMeasurement(survey);
  currentValidatedSurvey = payload.valid_for_scene_fusion ? survey : null;
  if (knownWidth && surveyKnownWidthInput) surveyKnownWidthInput.value = String(knownWidth.value);
  surveyEmpty.hidden = true; surveyResult.hidden = false; surveyResultName.textContent = survey.name;
  surveyConfidence.textContent = payload.valid_for_scene_fusion ? (replaced ? 'Relevé corrigé validé' : extended ? 'Relevé étendu validé' : 'Relevé validé') : 'À corriger';
  surveyConfirmation.hidden = false;
  surveyConfirmation.innerHTML = errors.length
    ? `<h3>${extended ? 'Extension refusée' : 'Relevé refusé avant reconstruction'}</h3><p>${errors.map(issue => surveyEscape(issue.message)).join(' ')}</p>`
    : warnings.length
      ? `<h3>Relevé validé avec réserves</h3><p>${warnings.map(issue => surveyEscape(issue.message)).join(' ')}</p>`
      : replaced
        ? '<h3>Relevé corrigé validé</h3><p>Cette révision remplace maintenant le relevé précédent comme source de vérité pour la prochaine Scene.</p>'
        : extended
          ? '<h3>Extension du relevé validée</h3><p>Les nouvelles vues ont été ajoutées sans modifier les faits déjà validés.</p>'
          : '<h3>Relevé architectural validé</h3><p>Les observations peuvent maintenant servir à la reconstruction de scène. Rien n’est encore construit en LEGO.</p>';
  const handoffMarkup = payload.valid_for_scene_fusion
    ? `<p><strong>Étape suivante :</strong> créez le fichier Survey → Scene puis envoyez-le avec le PDF photo original dans la même conversation IA. Sur téléphone, vous n’avez rien à copier.</p><p><button id="download-scene-handoff" class="primary big-action" type="button">Créer le fichier Survey → Scene à envoyer à l’IA</button></p><p><small>${SCENE_HANDOFF_FILENAME} · prompt v4.3 · ${SCENE_HANDOFF_VERSION}</small></p>`
    : '';
  if (surveySceneHandoffHome) {
    surveySceneHandoffHome.innerHTML = handoffMarkup;
    surveySceneHandoffHome.querySelector('#download-scene-handoff')?.addEventListener('click', createSceneHandoff);
  }
  surveyQuestions.innerHTML = payload.valid_for_scene_fusion
    ? '<p>Le Survey est validé. Le bouton Survey → Scene est disponible directement sous l’import.</p><p><a class="prompt-link" href="./brickhouse-survey-extension-prompt.txt" target="_blank" rel="noopener">Ajouter de nouvelles photos au Survey ↗</a></p>'
    : '<p>Corrigez d’abord les erreurs du relevé. La reconstruction de scène reste désactivée.</p>';
  surveyRefine.disabled = true;
  surveyAssumptions.innerHTML = [`${survey.photos.length} photo(s) documentée(s).`, `${survey.observations.length} observation(s), dont ${certainCount} certaine(s).`, `${openingCount} ouverture(s) observée(s).`, knownWidth ? `Largeur avant connue : ${knownWidth.value} m · mesure utilisateur transportée dans le fichier Survey.` : 'Aucune largeur avant mesurée n’est encore transportée dans ce Survey.', 'Une révision explicitement demandée remplace le Survey précédent seulement après validation complète.', 'Les matériaux nominaux et les détails d’ouverture sont conservés séparément des imperfections.', 'Le relevé ne choisit pas encore la profondeur ni la hauteur globale du bâtiment.', 'Le fichier Survey validé est la source de vérité sémantique et métrique connue pour la reconstruction suivante.'].map(item => `<li>${surveyEscape(item)}</li>`).join('');
  surveyProportions.hidden = false;
  surveyScaleBasis.textContent = knownWidth ? `Repère canonique : x = gauche→droite, y = avant→arrière, z = bas→haut. Largeur avant utilisateur : ${knownWidth.value} m.` : 'Repère canonique : x = gauche→droite en regardant la façade avant, y = avant→arrière, z = bas→haut.';
  surveyEvidence.innerHTML = survey.photos.map(photo => `<li>Photo ${photo.photo_index} · façade ${surveyEscape(photo.facade)} · image gauche → offset ${surveyEscape(photo.image_left_maps_to_facade_offset)}</li>`).join('');
  surveyPreview.textContent = JSON.stringify(survey, null, 2); surveyDownloadValidated.hidden = !payload.valid_for_scene_fusion; surveyDownload.disabled = true; surveyReport.disabled = true; surveyBuild.disabled = true;
  surveyStatus.textContent = payload.valid_for_scene_fusion ? (replaced ? 'ArchitecturalSurvey corrigé valide et actif. Le handoff Survey → Scene est disponible sous l’import.' : extended ? 'Extension ArchitecturalSurvey valide. Le handoff Survey → Scene est disponible sous l’import.' : 'ArchitecturalSurvey valide. Le handoff Survey → Scene est disponible directement sous l’import.') : 'ArchitecturalSurvey compris mais refusé. Corrigez les erreurs sémantiques affichées.';
}

function restoreValidatedSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    const storedWidth = Number(localStorage.getItem('brickhouse.knownFrontWidthM'));
    if (surveyKnownWidthInput && Number.isFinite(storedWidth) && storedWidth > 0 && !surveyKnownWidthInput.value) surveyKnownWidthInput.value = String(storedWidth);
    if (payload?.survey && typeof payload.valid_for_scene_fusion === 'boolean') renderSurveyValidation(payload);
  } catch { localStorage.removeItem('brickhouse.pendingArchitecturalSurvey'); }
}

surveyKnownWidthInput?.addEventListener('change', () => { const value = Number(surveyKnownWidthInput.value); if (Number.isFinite(value) && value > 0) localStorage.setItem('brickhouse.knownFrontWidthM', String(value)); });
surveyExternalFile?.addEventListener('change', async () => { const file = surveyExternalFile.files?.[0]; if (!file) return; try { surveyExternalInput.value = await file.text(); surveyStatus.textContent = `Fichier chargé : ${file.name}. Cliquez sur « Importer le résultat dans Boldungo ».`; } catch (error) { surveyStatus.textContent = `Impossible de lire le fichier JSON : ${error.message}`; } });
surveyReplace?.addEventListener('click', () => { replaceMode = true; surveyExternalInput.value = ''; if (surveyExternalFile) surveyExternalFile.value = ''; surveyStatus.textContent = 'Mode correction du relevé activé : choisissez le JSON Survey corrigé ci-dessus, puis cliquez sur « Importer le résultat dans Boldungo ». Le relevé actuel ne sera remplacé que si le nouveau est valide.'; surveyExternalFile?.focus(); });
surveyDownloadValidated?.addEventListener('click', () => { if (!currentValidatedSurvey) return; const enriched = withKnownWidth(currentValidatedSurvey); persistEnrichedSurvey(enriched); downloadJson(`${safeFilename(enriched.name)}-architectural-survey-v0.1.json`, enriched); surveyStatus.textContent = frontWidthMeasurement(enriched) ? `Relevé téléchargé avec largeur avant ${frontWidthMeasurement(enriched).value} m incluse dans le fichier.` : 'Relevé téléchargé sans mesure de largeur avant.'; });

surveyImportButton.addEventListener('click', async event => {
  const raw = extractJsonObject(surveyExternalInput.value); if (!raw) return;
  let parsed; try { parsed = JSON.parse(raw); } catch { return; } if (!isArchitecturalSurvey(parsed)) return;
  event.preventDefault(); event.stopImmediatePropagation(); const baseUrl = surveyApiBase(); if (!baseUrl) { surveyStatus.textContent = 'URL API manquante.'; return; }
  parsed = withKnownWidth(parsed); const baseSurvey = pendingValidatedSurvey(); const replacing = replaceMode && Boolean(baseSurvey); const extension = !replacing && isSurveyExtension(baseSurvey, parsed);
  surveyImportButton.disabled = true; surveyStatus.textContent = replacing ? 'Validation de la correction avant remplacement du relevé actuel…' : extension ? 'Contrôle de l’extension : vérification qu’aucun fait validé n’a été modifié…' : 'Validation du relevé architectural par BrickHouse…';
  try {
    const endpoint = extension ? '/api/v1/validate-survey-extension' : '/api/v1/validate-survey'; const body = extension ? { base: baseSurvey, candidate: parsed } : parsed;
    const response = await fetch(`${baseUrl}${endpoint}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); const payload = await response.json();
    if (!response.ok) { const detail = typeof payload.detail === 'string' ? payload.detail : 'Le relevé ne respecte pas ArchitecturalSurvey v0.1.'; throw new Error(detail); }
    renderSurveyValidation(payload, { extended: extension, replaced: replacing });
    if (payload.valid_for_scene_fusion) { localStorage.setItem('brickhouse.pendingArchitecturalSurvey', JSON.stringify(payload)); if (replacing) { localStorage.removeItem('brickhouse.pendingArchitecturalScene'); localStorage.removeItem('brickhouse.pendingExport'); replaceMode = false; } }
  } catch (error) { surveyStatus.textContent = `Import du relevé impossible : ${error.message}`; } finally { surveyImportButton.disabled = false; }
}, { capture: true });

restoreValidatedSurvey();