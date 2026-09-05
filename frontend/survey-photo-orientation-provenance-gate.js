// Reject Survey photo identities that silently diverge from the current capture
// inputs. Capture hints are provenance metadata: they may be questioned in notes,
// but the returned photos[] identity must preserve the handoff slot mapping.
const importButton = document.querySelector('#import-analysis');
const externalAnalysis = document.querySelector('#external-analysis');
const status = document.querySelector('#status');

const SLOT_ORDER = ['front', 'right', 'left', 'rear'];
const DETAIL_ORDER = ['detail_1', 'detail_2', 'detail_3', 'detail_4', 'detail_5', 'detail_6'];
const MAX_PHOTOS_PER_GROUP = 4;

function extractJsonObject(raw) {
  let value = String(raw || '').trim();
  if (value.startsWith('```')) {
    const lines = value.split(/\r?\n/);
    if (lines[0].trim().toLowerCase() === '```json' || lines[0].trim() === '```') lines.shift();
    if (lines.at(-1)?.trim() === '```') lines.pop();
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

function surveysInPayload(payload) {
  const surveys = [];
  if (payload?.schema_version === '0.1' && Array.isArray(payload?.photos)) surveys.push(payload);
  if (payload?.survey?.schema_version === '0.1' && Array.isArray(payload.survey?.photos)) surveys.push(payload.survey);
  return surveys;
}

function currentCapturePhotoContract() {
  const expected = [];
  for (const slotName of SLOT_ORDER) {
    const slot = document.querySelector(`.guided-photo-slot[data-slot="${slotName}"]`);
    const input = slot?.querySelector('.guided-photo-input');
    [...(input?.files || [])].slice(0, MAX_PHOTOS_PER_GROUP).forEach(() => expected.push({
      capture_role: 'facade_view',
      facade: slotName,
    }));
  }
  for (const slotName of DETAIL_ORDER) {
    const slot = document.querySelector(`.detail-photo-slot[data-slot="${slotName}"]`);
    const input = slot?.querySelector('.detail-photo-input');
    [...(input?.files || [])].slice(0, MAX_PHOTOS_PER_GROUP).forEach(() => expected.push({
      capture_role: 'targeted_detail',
      facade: null,
    }));
  }
  return expected;
}

function orientationProvenanceError(survey) {
  const expected = currentCapturePhotoContract();
  const actual = Array.isArray(survey?.photos) ? survey.photos : [];
  if (!expected.length) return null;
  if (actual.length !== expected.length) {
    return `Photos refusées : le Survey contient ${actual.length} photo(s), mais le handoff courant en contient ${expected.length}.`;
  }

  for (let index = 0; index < expected.length; index += 1) {
    const expectedPhoto = expected[index];
    const actualPhoto = actual[index];
    const expectedIndex = index + 1;
    if (Number(actualPhoto?.photo_index) !== expectedIndex) {
      return `Photos refusées : photo_index ${actualPhoto?.photo_index ?? 'absent'} ne correspond pas à la position ${expectedIndex} du handoff courant.`;
    }
    if (actualPhoto?.capture_role !== expectedPhoto.capture_role) {
      return `Photos refusées : la photo ${expectedIndex} a capture_role=${actualPhoto?.capture_role ?? 'absent'} au lieu de ${expectedPhoto.capture_role}.`;
    }
    if ((actualPhoto?.facade ?? null) !== expectedPhoto.facade) {
      const expectedFacade = expectedPhoto.facade ?? 'null';
      const actualFacade = actualPhoto?.facade ?? 'null';
      return `Orientation refusée : la photo ${expectedIndex} a été réassignée à ${actualFacade}, alors que le handoff courant la fournit comme ${expectedFacade}. Une contradiction visuelle doit être conservée en note, pas remplacer l’identité de capture.`;
    }
  }
  return null;
}

importButton?.addEventListener('click', event => {
  const raw = extractJsonObject(externalAnalysis?.value);
  if (!raw) return;

  let payload;
  try { payload = JSON.parse(raw); } catch { return; }
  for (const survey of surveysInPayload(payload)) {
    const error = orientationProvenanceError(survey);
    if (!error) continue;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (status) status.textContent = `${error} Recréez le Survey depuis le handoff courant ; aucune Scene ne sera préparée avec cette permutation.`;
    return;
  }
}, { capture: true });
