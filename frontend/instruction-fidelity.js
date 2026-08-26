function instructionFidelitySummary(bundle) {
  const issues = Array.isArray(bundle?.fidelity_issues) ? bundle.fidelity_issues : [];
  const omitted = issues.filter(issue => issue?.code === 'partial_scene_object_omitted');
  if (!omitted.length) return null;

  return {
    partial: true,
    title: 'Notice provisoire — géométrie connue uniquement',
    message: 'Cette notice monte uniquement les briques que BrickHouse peut placer sans inventer les zones encore incertaines.',
    omitted: omitted.map(issue => ({
      object_id: issue.object_id ?? 'objet inconnu',
      message: issue.message ?? 'Géométrie encore non résolue.',
    })),
  };
}

export { instructionFidelitySummary };
