const messageEl = document.querySelector('#message');

function loadScene() {
  const keys = ['brickhouse.previewArchitecturalScene', 'brickhouse.pendingSceneValidation', 'brickhouse.lastSceneSurveyValidation'];
  for (const key of keys) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      const value = JSON.parse(raw);
      const candidate = value?.scene ?? value;
      if (candidate?.schema_version === '0.2' && Array.isArray(candidate.volumes)) return candidate;
    } catch { /* try next source */ }
  }
  return null;
}

function platformStructureNotes(scene) {
  const notes = [];
  for (const observation of scene?.platform_structure_observations ?? []) {
    const labels = [];
    if (observation.vertical_posts === 'observed') labels.push('poteaux verticaux visibles');
    if (observation.diagonal_bracing === 'observed') labels.push('contreventements diagonaux visibles');
    if (!labels.length) continue;
    const unresolved = [];
    if (observation.exact_count_known === false) unresolved.push('nombre exact inconnu');
    if (observation.exact_coordinates_known === false) unresolved.push('positions exactes inconnues');
    const suffix = unresolved.length ? ` (${unresolved.join(', ')})` : '';
    notes.push(`Terrasse ${observation.platform_id} : ${labels.join(' et ')}${suffix}. Aucun support 3D arbitraire n’est ajouté.`);
  }
  for (const platform of scene?.platforms ?? []) {
    if (platform.edge_treatment === 'open_railing' && !platform.edges) {
      notes.push(`Terrasse ${platform.id} : garde-corps ouvert observé, mais les côtés et interruptions exacts ne sont pas résolus. Aucun garde-corps 3D arbitraire n’est ajouté.`);
    }
  }
  return notes;
}

const scene = loadScene();
const notes = platformStructureNotes(scene);
if (messageEl && notes.length) {
  messageEl.textContent = [messageEl.textContent.trim(), ...notes].filter(Boolean).join(' ');
}

export { platformStructureNotes };
