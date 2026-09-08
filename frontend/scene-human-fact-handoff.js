export const HUMAN_FACT_SCENE_HANDOFF_KEY = 'brickhouse.pendingHumanFactSceneHandoff';
export const HUMAN_FACT_SCENE_HANDOFF_ENDPOINT = '/api/v1/prepare-human-fact-scene-handoff';

function apiUrl(base, path) {
  const normalized = String(base || '').trim().replace(/\/$/, '');
  return `${normalized}${path}`;
}

export async function prepareHumanFactSceneHandoff({ apiBase, survey, humanFacts, fetchImpl = fetch }) {
  if (!survey || survey.schema_version !== '0.1') throw new Error('ArchitecturalSurvey v0.1 requis');
  if (!Array.isArray(humanFacts) || humanFacts.length === 0) throw new Error('Au moins un fait utilisateur est requis');

  const response = await fetchImpl(apiUrl(apiBase, HUMAN_FACT_SCENE_HANDOFF_ENDPOINT), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ survey, human_facts: humanFacts }),
  });
  if (!response.ok) throw new Error(`handoff faits utilisateur : HTTP ${response.status}`);

  const payload = await response.json();
  if (payload?.source_survey_id !== survey.id || payload?.scene_input_survey?.schema_version !== '0.1') {
    throw new Error('handoff faits utilisateur invalide');
  }
  return payload;
}

export function persistHumanFactSceneHandoff(payload, storage = localStorage) {
  if (!payload?.source_survey_id || !payload?.scene_input_survey || !Array.isArray(payload?.human_facts)) {
    throw new Error('handoff faits utilisateur incomplet');
  }
  storage.setItem(HUMAN_FACT_SCENE_HANDOFF_KEY, JSON.stringify(payload));
  return payload;
}

export function readHumanFactSceneHandoff(storage = localStorage) {
  try {
    return JSON.parse(storage.getItem(HUMAN_FACT_SCENE_HANDOFF_KEY) || 'null');
  } catch {
    return null;
  }
}
