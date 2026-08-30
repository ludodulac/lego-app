const doc = typeof document === 'undefined' ? null : document;
const importButton = doc?.querySelector('#import-analysis');
const externalInput = doc?.querySelector('#external-analysis');
const status = doc?.querySelector('#status');

function slug(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function sameJsonValue(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

export function normalizeNeutralSurvey(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return { value, changed: false, issue: null };
  }
  if (value.schema_version !== '0.1' || !Array.isArray(value.photos) || !Array.isArray(value.observations)) {
    return { value, changed: false, issue: null };
  }

  const normalized = JSON.parse(JSON.stringify(value));
  let changed = false;

  if (typeof normalized.id !== 'string' || !normalized.id.trim()) {
    const nameSlug = slug(normalized.name);
    if (!nameSlug) {
      return { value, changed: false, issue: 'Le Survey v0.1 n’a ni id utilisable ni name permettant de créer un identifiant technique stable.' };
    }
    normalized.id = `survey-${nameSlug}-v01`;
    changed = true;
  }

  const frame = normalized.canonical_frame;
  if (!frame || typeof frame !== 'object' || Array.isArray(frame)) {
    return { value, changed: false, issue: 'canonical_frame est absent ou n’est pas un objet.' };
  }

  if (!Object.prototype.hasOwnProperty.call(frame, 'front_facade')) {
    if (frame.front === 'front') {
      frame.front_facade = 'front';
      delete frame.front;
      changed = true;
    } else {
      return { value, changed: false, issue: 'canonical_frame.front_facade manque et aucun alias exact front="front" ne permet une normalisation sans supposition.' };
    }
  } else if (Object.prototype.hasOwnProperty.call(frame, 'front') && frame.front !== frame.front_facade) {
    return { value, changed: false, issue: 'canonical_frame contient des valeurs contradictoires entre front_facade et front.' };
  } else if (Object.prototype.hasOwnProperty.call(frame, 'front')) {
    delete frame.front;
    changed = true;
  }

  if (!Object.prototype.hasOwnProperty.call(frame, 'x_direction')) {
    if (frame.view === 'front_view_left_to_right') {
      frame.x_direction = 'front_view_left_to_right';
      delete frame.view;
      changed = true;
    } else {
      return { value, changed: false, issue: 'canonical_frame.x_direction manque et aucun alias exact view="front_view_left_to_right" ne permet une normalisation sans supposition.' };
    }
  } else if (Object.prototype.hasOwnProperty.call(frame, 'view') && frame.view !== frame.x_direction) {
    return { value, changed: false, issue: 'canonical_frame contient des valeurs contradictoires entre x_direction et view.' };
  } else if (Object.prototype.hasOwnProperty.call(frame, 'view')) {
    delete frame.view;
    changed = true;
  }

  for (const observation of normalized.observations) {
    if (!observation || typeof observation !== 'object' || Array.isArray(observation)) continue;
    const attributes = observation.attributes;
    if (!attributes || typeof attributes !== 'object' || Array.isArray(attributes)) continue;

    const nestedCertainty = attributes.attribute_certainty;
    if (nestedCertainty !== undefined) {
      if (!nestedCertainty || typeof nestedCertainty !== 'object' || Array.isArray(nestedCertainty)) {
        return { value, changed: false, issue: `L’observation ${observation.id || '(sans id)'} contient attributes.attribute_certainty sous une forme non normalisable.` };
      }
      if (observation.attribute_certainty === undefined) {
        observation.attribute_certainty = nestedCertainty;
      } else if (!sameJsonValue(observation.attribute_certainty, nestedCertainty)) {
        return { value, changed: false, issue: `L’observation ${observation.id || '(sans id)'} contient deux cartes attribute_certainty contradictoires.` };
      }
      delete attributes.attribute_certainty;
      changed = true;
    }

    if (observation.kind === 'opening' && attributes.semantic_type === 'opening') {
      delete attributes.semantic_type;
      if (observation.attribute_certainty && typeof observation.attribute_certainty === 'object') {
        delete observation.attribute_certainty.semantic_type;
      }
      changed = true;
    }
  }

  return { value: normalized, changed, issue: null };
}

function extractJsonObject(raw) {
  let text = String(raw || '').trim();
  if (text.startsWith('```')) {
    const lines = text.split(/\r?\n/);
    lines.shift();
    if (lines.at(-1)?.trim() === '```') lines.pop();
    text = lines.join('\n').trim();
  }
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  return start >= 0 && end > start ? text.slice(start, end + 1) : text;
}

importButton?.addEventListener('click', event => {
  let parsed;
  try {
    parsed = JSON.parse(extractJsonObject(externalInput?.value));
  } catch {
    return;
  }

  const result = normalizeNeutralSurvey(parsed);
  if (result.issue) {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (status) status.textContent = `Import impossible : ${result.issue}`;
    return;
  }
  if (!result.changed) return;

  if (externalInput) externalInput.value = JSON.stringify(result.value, null, 2);
  if (status) status.textContent = 'Le JSON IA contenait uniquement des écarts de forme non sémantiques ; Boldungo les a normalisés avant validation stricte.';
}, { capture: true });
