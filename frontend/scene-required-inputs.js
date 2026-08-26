const confirmationCard = document.querySelector('#confirmation-card');
const statusEl = document.querySelector('#status');

function escapeHtml(value) {
  return String(value).replace(/[&<>\"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;',
  }[char]));
}

export function describeRequiredInput(item) {
  if (item?.reason === 'shed_construction_requires_exact_pitch' && item.field === 'pitch_degrees') {
    const range = item.known_range_degrees;
    const context = range
      ? ` Les photos permettent seulement de situer cette pente entre ${range.min}° et ${range.max}°.`
      : '';
    return `Il manque la pente exacte du toit « ${item.object_id} » pour construire la maquette.${context} Boldungo ne choisira pas un angle à votre place.`;
  }
  if (item?.reason === 'gable_construction_requires_exact_pitch' && item.field === 'pitch_degrees') {
    const range = item.known_range_degrees;
    const context = range
      ? ` La pente est actuellement bornée entre ${range.min}° et ${range.max}°.`
      : '';
    return `Il manque la pente exacte du toit « ${item.object_id} ».${context}`;
  }
  if (item?.field === 'down_slope_direction') {
    return `Il manque le sens de descente du toit « ${item.object_id} ».`;
  }
  if (item?.field === 'ridge_direction') {
    return `Il manque l’orientation du faîtage du toit « ${item.object_id} ».`;
  }
  if (['width', 'depth', 'height'].includes(item?.field)) {
    const labels = { width: 'largeur', depth: 'profondeur', height: 'hauteur' };
    return `Il manque la ${labels[item.field]} exacte du volume « ${item.object_id} ».`;
  }
  return `Une information supplémentaire est nécessaire pour « ${item?.object_id ?? 'la scène'} » (${item?.field ?? 'champ inconnu'}).`;
}

function latestValidationPayload() {
  for (const key of ['brickhouse.lastSceneSurveyValidation', 'brickhouse.pendingSceneValidation']) {
    try {
      const payload = JSON.parse(localStorage.getItem(key) || 'null');
      if (Array.isArray(payload?.required_inputs) && payload.required_inputs.length) return payload;
    } catch { /* ignore malformed stale storage */ }
  }
  return null;
}

function renderRequiredInputs() {
  const payload = latestValidationPayload();
  const items = payload?.required_inputs ?? [];
  if (!confirmationCard || !items.length) return;

  let panel = document.querySelector('#required-inputs-panel');
  if (!panel) {
    panel = document.createElement('div');
    panel.id = 'required-inputs-panel';
    panel.className = 'required-inputs-panel';
    confirmationCard.appendChild(panel);
  }
  if (payload.scene?.schema_version === '0.2') {
    localStorage.setItem('brickhouse.previewArchitecturalScene', JSON.stringify(payload.scene));
  }
  panel.innerHTML = `<h4>Ce qu’il manque pour continuer</h4><ul>${items.map(item => `<li>${escapeHtml(describeRequiredInput(item))}</li>`).join('')}</ul><p><a class="file-button" href="./scene-viewer.html">Voir la reconstruction 3D actuelle →</a></p>`;

  if (items.length === 1 && items[0]?.reason === 'shed_construction_requires_exact_pitch') {
    statusEl.textContent = 'La reconstruction est comprise. Il manque seulement la pente exacte du toit pour générer la maquette. Vous pouvez déjà ouvrir l’aperçu 3D architectural.';
  }
}

const observer = new MutationObserver(() => queueMicrotask(renderRequiredInputs));
if (confirmationCard) observer.observe(confirmationCard, { childList: true, subtree: true });
renderRequiredInputs();
