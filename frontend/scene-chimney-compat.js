// Keep the architectural compatibility hook intact and load the additive
// one-screen presentation layer beside it. The shell only moves existing DOM
// controls; it does not rewrite Survey/Scene truth or replace validators.
import './photo-shell.js?v=single-screen-shell-0.2';

if (!document.querySelector('link[data-boldungo-shell-style]')) {
  const shellStyle = document.createElement('link');
  shellStyle.rel = 'stylesheet';
  shellStyle.href = './photo-shell.css?v=single-screen-shell-0.2';
  shellStyle.dataset.boldungoShellStyle = 'true';
  document.head.appendChild(shellStyle);
}

function pendingValidatedSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return payload?.valid_for_scene_fusion ? payload.survey : null;
  } catch {
    return null;
  }
}

function positivePropertyValueNumber(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const numeric = Number(value.value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
}

function recoverCertainChimneys(scene, survey) {
  if (!scene || typeof scene !== 'object' || scene.schema_version !== '0.2') return scene;
  if (!survey || !Array.isArray(survey.observations)) return scene;

  const certainChimneyIds = new Set(
    survey.observations
      .filter(item => item?.kind === 'chimney' && item?.certainty === 'certain' && typeof item?.id === 'string')
      .map(item => item.id),
  );
  if (!certainChimneyIds.size || !Array.isArray(scene.volumes)) return scene;

  const clone = JSON.parse(JSON.stringify(scene));
  clone.chimneys = Array.isArray(clone.chimneys) ? clone.chimneys : [];
  const existingChimneyIds = new Set(clone.chimneys.map(item => item?.id).filter(Boolean));
  const retainedVolumes = [];

  for (const volume of clone.volumes) {
    if (!certainChimneyIds.has(volume?.id) || existingChimneyIds.has(volume?.id)) {
      retainedVolumes.push(volume);
      continue;
    }

    const width = positivePropertyValueNumber(volume.width);
    const depth = positivePropertyValueNumber(volume.depth);
    const height = positivePropertyValueNumber(volume.height);
    const position = volume.position;
    const positionIsComplete = position && [position.x, position.y, position.z].every(Number.isFinite);
    if (width == null || depth == null || height == null || !positionIsComplete || !volume.source) {
      retainedVolumes.push(volume);
      continue;
    }

    clone.chimneys.push({
      id: volume.id,
      position,
      width,
      depth,
      height,
      source: volume.source,
      evidence: Array.isArray(volume.evidence) ? volume.evidence : [],
    });
    existingChimneyIds.add(volume.id);
  }

  clone.volumes = retainedVolumes;
  return clone;
}

function normalizeCertainChimneyBeforeImport(event) {
  const button = event.target.closest?.('#import-analysis');
  if (!button) return;
  const textarea = document.querySelector('#external-analysis');
  if (!textarea?.value.trim()) return;
  try {
    const parsed = JSON.parse(textarea.value.trim());
    if (parsed?.schema_version !== '0.2') return;
    textarea.value = JSON.stringify(recoverCertainChimneys(parsed, pendingValidatedSurvey()), null, 2);
  } catch {
    // Keep syntax and schema errors owned by the normal import path.
  }
}

document.addEventListener('click', normalizeCertainChimneyBeforeImport, true);
