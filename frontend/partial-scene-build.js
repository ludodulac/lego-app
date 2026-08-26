function prepareConservativePartialScene(scene) {
  const copy = structuredClone(scene);
  const omitted = new Map();

  copy.roofs = (copy.roofs ?? []).filter(roof => {
    const incompleteGable = roof.type === 'gable' && (!roof.ridge_direction || roof.pitch_degrees == null);
    const incompleteShed = roof.type === 'shed' && (!roof.down_slope_direction || roof.pitch_degrees == null);
    if (incompleteGable || incompleteShed) {
      omitted.set(roof.id, 'toiture non résolue');
      return false;
    }
    return true;
  });

  const unresolvedJunctionObjects = new Set();
  for (const relation of copy.relations ?? []) {
    if (relation.geometry_status === 'unresolved') {
      unresolvedJunctionObjects.add(relation.subject_id);
      unresolvedJunctionObjects.add(relation.object_id);
    }
  }

  copy.platforms = (copy.platforms ?? []).filter(platform => {
    if (!unresolvedJunctionObjects.has(platform.id)) return true;
    omitted.set(platform.id, 'raccord métrique non résolu');
    return false;
  });
  copy.stairs = (copy.stairs ?? []).filter(stair => {
    if (!unresolvedJunctionObjects.has(stair.id)) return true;
    omitted.set(stair.id, 'raccord métrique non résolu');
    return false;
  });

  copy.relations = (copy.relations ?? []).filter(
    relation => !omitted.has(relation.subject_id) && !omitted.has(relation.object_id),
  );
  copy.notes = [
    copy.notes,
    omitted.size
      ? `Partial LEGO build: omitted unresolved objects ${[...omitted.keys()].join(', ')}. Original Scene remains authoritative.`
      : null,
  ].filter(Boolean).join(' ');

  return {
    scene: copy,
    omitted: [...omitted.entries()].map(([object_id, reason]) => ({ object_id, reason })),
  };
}

export { prepareConservativePartialScene };
