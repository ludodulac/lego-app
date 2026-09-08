import './scene-handoff-contract-audit-v44.js';
import './scene-handoff-stage-lock-v45.js';
import './scene-handoff-output-frame-v46.js';
import './scene-handoff-ownership-audit-v47.js';
import './scene-handoff-scale-audit-v48.js';
import {
  HUMAN_FACT_SCENE_HANDOFF_KEY,
  readHumanFactSceneHandoff,
} from './scene-human-fact-handoff.js';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const PENDING_SURVEY_KEY = 'brickhouse.pendingArchitecturalSurvey';

function pendingValidatedSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem(PENDING_SURVEY_KEY) || 'null');
    return payload?.valid_for_scene_fusion ? payload.survey : null;
  } catch {
    return null;
  }
}

function observationIds(survey) {
  return (survey?.observations ?? []).map(item => item.id).sort();
}

function sameJson(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

export function effectiveSceneInput(acceptedSurvey, storage = localStorage) {
  if (!acceptedSurvey) return { survey: null, humanFacts: [] };
  const handoff = readHumanFactSceneHandoff(storage);
  const derivedSurvey = handoff?.scene_input_survey;
  const validDerived = handoff?.source_survey_id === acceptedSurvey.id
    && derivedSurvey?.id === acceptedSurvey.id
    && derivedSurvey?.schema_version === '0.1'
    && sameJson(observationIds(derivedSurvey), observationIds(acceptedSurvey))
    && sameJson(derivedSurvey?.known_measurements ?? [], acceptedSurvey?.known_measurements ?? [])
    && Array.isArray(handoff?.human_facts)
    && handoff.human_facts.length > 0;
  if (validDerived) {
    return { survey: derivedSurvey, humanFacts: handoff.human_facts };
  }
  return { survey: acceptedSurvey, humanFacts: [] };
}

function absoluteUrl(input) {
  if (typeof input === 'string') return new URL(input, globalThis.location?.href || import.meta.url).href;
  if (input && typeof input.url === 'string') return input.url;
  return String(input);
}

function isScenePromptUrl(url) {
  try {
    return new URL(url, globalThis.location?.href || import.meta.url).pathname.endsWith('/brickhouse-survey-to-scene-prompt.txt');
  } catch {
    return false;
  }
}

function compactObservation(item) {
  const attributes = item?.attributes ?? {};
  const attributeCertainty = item?.attribute_certainty ?? attributes.attribute_certainty ?? null;
  const result = {
    id: item?.id ?? null,
    kind: item?.kind ?? null,
    facade: item?.facade ?? null,
    certainty: item?.certainty ?? null,
  };
  for (const key of ['physical_object_count', 'semantic_type', 'slope_direction', 'roof_type', 'facade_is_gable', 'facade_roof_relationship', 'roof_edge_type', 'stair_topology']) {
    if (Object.prototype.hasOwnProperty.call(attributes, key)) result[key] = attributes[key];
  }
  if (attributeCertainty != null) result.attribute_certainty = attributeCertainty;
  return result;
}

export function buildSceneSourceLock(survey, humanFacts = []) {
  if (!survey || survey.schema_version !== '0.1') return '';

  const observations = (survey.observations ?? []).map(compactObservation);
  const boundaryIds = observations.filter(item => item.kind === 'building_boundary').map(item => item.id);
  const terrain = observations.filter(item => item.kind === 'terrain' && ['certain', 'plausible'].includes(item.certainty));
  const roofs = observations.filter(item => item.kind === 'roof' && ['certain', 'plausible'].includes(item.certainty));
  const relations = (survey.relations ?? []).map(item => ({
    id: item.id,
    kind: item.kind,
    subject_id: item.subject_id,
    object_id: item.object_id,
    certainty: item.certainty,
  }));
  const manifest = {
    survey_id: survey.id,
    known_measurements: survey.known_measurements ?? [],
    observations,
    building_boundary_ids: boundaryIds,
    active_terrain: terrain,
    active_roofs: roofs,
    relations,
    human_facts: humanFacts,
  };

  return `VERROU SOURCE SURVEY → SCENE — GÉNÉRÉ AUTOMATIQUEMENT PAR BOLDUNGO\nCe manifeste est dérivé du Survey validé actuellement actif dans Boldungo et, lorsqu'elles existent, de corrections sémantiques utilisateur validées séparément par le backend. Le Survey accepté reste inchangé. Le manifeste décrit l'entrée dérivée effectivement autorisée pour la reconstruction Scene ; pour les attributs explicitement listés dans human_facts, cette valeur user_provided enrichit le Survey accepté sans le réécrire. Toute autre information continue de venir du Survey accepté et des preuves photo.\n\nRÈGLES DE FERMETURE OBLIGATOIRES\n- N'invente aucun ID d'opening, platform, stair, volume secondaire ou chimney absent des observations Survey correspondantes. volume_main reste l'ancre métrique Scene autorisée pour l'enveloppe principale.\n- Les éléments de human_facts sont des faits sémantiques user_provided validés et traçables ; ils peuvent enrichir les attributs d'observation mais ne deviennent jamais des known_measurements.\n- Pour chaque observation terrain certaine/plausible listée dans active_terrain, terrain.profiles contient un profil de la même façade. Une amplitude inconnue reste null ; elle ne justifie jamais la suppression du profil.\n- Pour chaque observation roof certaine/plausible, conserve les hypothèses qualitatives soutenues et leur niveau de certitude. facade_is_gable:true certain/plausible ne doit pas devenir type:\"other\" par simple prudence ; les métriques non contraintes restent null.\n- Chaque relation certaine conserve son id et son identité d'endpoints. Si un endpoint Survey appartient à building_boundary_ids, la Scene utilise l'alias sémantique littéral building_boundary avec semantic_anchor_volume_id:\"volume_main\" lorsque le contact métrique est résolu ; n'invente jamais obs-building-envelope, obs-building-boundary-new ou un autre alias.\n- Avant sortie, compare le JSON Scene final à ce manifeste. S'il manque un terrain actif, une hypothèse roof soutenue ou si un ID/endpoint a dérivé, corrige la Scene avant de créer brickhouse-scene-result.json.\n\nMANIFESTE SOURCE EXACT\n${JSON.stringify(manifest, null, 2)}\n`;
}

globalThis.fetch = async function sourceLockedScenePromptFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isScenePromptUrl(url)) return response;

  const acceptedSurvey = pendingValidatedSurvey();
  const { survey, humanFacts } = effectiveSceneInput(acceptedSurvey);
  if (!survey) return response;
  const prompt = await response.text();
  const sourceLock = buildSceneSourceLock(survey, humanFacts);
  return new Response(`${prompt}\n\n${sourceLock}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};

function extractCandidateSurvey(raw) {
  const text = String(raw || '').trim();
  if (!text) return null;
  try {
    const parsed = JSON.parse(text);
    return parsed?.schema_version === '0.1' ? parsed : null;
  } catch {
    return null;
  }
}

function clearStaleSurveyHandoff() {
  localStorage.removeItem(PENDING_SURVEY_KEY);
  localStorage.removeItem(HUMAN_FACT_SCENE_HANDOFF_KEY);
  localStorage.removeItem('brickhouse.pendingSceneValidation');
  localStorage.removeItem('brickhouse.lastSceneSurveyValidation');
  const home = document.querySelector('#scene-handoff-home');
  if (home) home.innerHTML = '';
}

document.addEventListener('click', event => {
  const button = event.target.closest?.('#import-analysis');
  if (!button) return;
  const textarea = document.querySelector('#external-analysis');
  if (extractCandidateSurvey(textarea?.value)) clearStaleSurveyHandoff();
}, true);
