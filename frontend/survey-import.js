const surveyImportButton = document.querySelector('#import-analysis');
const surveyExternalInput = document.querySelector('#external-analysis');
const surveyApiInput = document.querySelector('#api-url');
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
const surveyReport = document.querySelector('#download-report');
const surveyBuild = document.querySelector('#build-bricks');

function surveyApiBase() { return surveyApiInput.value.trim().replace(/\/$/, ''); }
function surveyEscape(value) { return String(value).replace(/[&<>\"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;' }[char])); }

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

function renderSurveyValidation(payload) {
  const survey = payload.survey;
  const issues = payload.issues ?? [];
  const errors = issues.filter(issue => issue.severity === 'error');
  const warnings = issues.filter(issue => issue.severity !== 'error');
  const openingCount = survey.observations.filter(item => item.kind === 'opening').length;
  const certainCount = survey.observations.filter(item => item.certainty === 'certain').length;

  surveyEmpty.hidden = true;
  surveyResult.hidden = false;
  surveyResultName.textContent = survey.name;
  surveyConfidence.textContent = payload.valid_for_scene_fusion ? 'Relevé validé' : 'À corriger';
  surveyConfirmation.hidden = false;
  surveyConfirmation.innerHTML = errors.length
    ? `<h3>Relevé refusé avant reconstruction</h3><p>${errors.map(issue => surveyEscape(issue.message)).join(' ')}</p>`
    : warnings.length
      ? `<h3>Relevé validé avec réserves</h3><p>${warnings.map(issue => surveyEscape(issue.message)).join(' ')}</p>`
      : '<h3>Relevé architectural validé</h3><p>Les observations peuvent maintenant servir à la reconstruction de scène. Rien n’est encore construit en LEGO.</p>';

  surveyQuestions.innerHTML = '<p>Étape suivante : fusionner ce relevé validé vers ArchitecturalScene. La construction reste volontairement désactivée à ce stade.</p>';
  surveyRefine.disabled = true;
  surveyAssumptions.innerHTML = [
    `${survey.photos.length} photo(s) documentée(s).`,
    `${survey.observations.length} observation(s), dont ${certainCount} certaine(s).`,
    `${openingCount} ouverture(s) observée(s).`,
    'Les matériaux nominaux et les détails d’ouverture sont conservés séparément des imperfections.',
    'Le relevé ne choisit pas encore la profondeur ni la hauteur globale du bâtiment.'
  ].map(item => `<li>${surveyEscape(item)}</li>`).join('');

  surveyProportions.hidden = false;
  surveyScaleBasis.textContent = 'Repère canonique : x = gauche→droite en regardant la façade avant, y = avant→arrière, z = bas→haut.';
  surveyEvidence.innerHTML = survey.photos.map(photo => `<li>Photo ${photo.photo_index} · façade ${surveyEscape(photo.facade)} · image gauche → offset ${surveyEscape(photo.image_left_maps_to_facade_offset)}</li>`).join('');
  surveyPreview.textContent = JSON.stringify(survey, null, 2);
  surveyDownload.disabled = true;
  surveyReport.disabled = true;
  surveyBuild.disabled = true;
  surveyStatus.textContent = payload.valid_for_scene_fusion
    ? 'ArchitecturalSurvey valide. Étape suivante : reconstruction de scène — ne construisez pas encore.'
    : 'ArchitecturalSurvey compris mais refusé pour la reconstruction. Corrigez les erreurs sémantiques affichées.';
}

surveyImportButton.addEventListener('click', async event => {
  const raw = extractJsonObject(surveyExternalInput.value);
  if (!raw) return;
  let parsed;
  try { parsed = JSON.parse(raw); } catch { return; }
  if (!isArchitecturalSurvey(parsed)) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  const base = surveyApiBase();
  if (!base) { surveyStatus.textContent = 'URL API manquante.'; return; }
  surveyImportButton.disabled = true;
  surveyStatus.textContent = 'Validation du relevé architectural par BrickHouse…';
  try {
    const response = await fetch(`${base}/api/v1/validate-survey`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(parsed),
    });
    const payload = await response.json();
    if (!response.ok) {
      const detail = typeof payload.detail === 'string' ? payload.detail : 'Le relevé ne respecte pas ArchitecturalSurvey v0.1.';
      throw new Error(detail);
    }
    renderSurveyValidation(payload);
    localStorage.setItem('brickhouse.pendingArchitecturalSurvey', JSON.stringify(payload));
  } catch (error) {
    surveyStatus.textContent = `Import du relevé impossible : ${error.message}`;
  } finally {
    surveyImportButton.disabled = false;
  }
}, { capture: true });
