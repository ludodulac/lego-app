import './brickhouse-survey-package.js';
import './survey-neutral-normalize.js';

const button = document.querySelector('#import-analysis');
const input = document.querySelector('#external-analysis');
const apiInput = document.querySelector('#api-url');
const status = document.querySelector('#status');
const knownWidth = document.querySelector('#known-width');

let handingOffScene = false;

function apiBase() { return apiInput?.value.trim().replace(/\/$/, '') || ''; }
function extractJson(raw) {
  let value = String(raw || '').trim();
  if (value.startsWith('```')) {
    const lines = value.split(/\r?\n/);
    lines.shift();
    if (lines.at(-1)?.trim() === '```') lines.pop();
    value = lines.join('\n').trim();
  }
  const start = value.indexOf('{');
  const end = value.lastIndexOf('}');
  return start >= 0 && end > start ? value.slice(start, end + 1) : value;
}

function isBundleRoot(value) {
  return value?.schema_version === 'external-bundle-0.1'
    && value?.kind === 'brickhouse_external_result';
}

function looksLikeBundle(value) {
  return Boolean(value && typeof value === 'object' && (
    value.kind === 'brickhouse_external_result'
    || Object.prototype.hasOwnProperty.call(value, 'survey')
    || Object.prototype.hasOwnProperty.call(value, 'scene')
  ));
}

function isBundle(value) {
  return isBundleRoot(value)
    && value?.survey?.schema_version === '0.1'
    && value?.scene?.schema_version === '0.2';
}

function bundleContractIssue(value) {
  if (!looksLikeBundle(value)) return null;
  if (value?.schema_version !== 'external-bundle-0.1') {
    return `Version de l’enveloppe incompatible : attendu « external-bundle-0.1 », reçu « ${value?.schema_version ?? 'absent'} ».`;
  }
  if (value?.kind !== 'brickhouse_external_result') {
    return `Type d’enveloppe incompatible : attendu « brickhouse_external_result », reçu « ${value?.kind ?? 'absent'} ».`;
  }
  if (!value?.survey || !value?.scene) {
    return 'Le résultat BrickHouse doit contenir à la fois survey et scene.';
  }
  if (value.survey.schema_version !== '0.1') {
    return `Version Survey incompatible : attendu « 0.1 », reçu « ${value.survey.schema_version ?? 'absent'} ». Régénérez le résultat avec la commande BrickHouse la plus récente.`;
  }
  if (value.scene.schema_version !== '0.2') {
    return `Version Scene incompatible : attendu « 0.2 », reçu « ${value.scene.schema_version ?? 'absent'} ». Régénérez le résultat avec la commande BrickHouse la plus récente.`;
  }
  return null;
}

function formatDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return 'Le fichier résultat ne respecte pas le contrat BrickHouse.';
  return detail.slice(0, 12).map(item => {
    const path = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : 'champ';
    return `${path} : ${item.msg || item.type || 'valeur invalide'}`;
  }).join(' · ');
}

button?.addEventListener('click', async event => {
  if (handingOffScene) return;
  let parsed;
  try { parsed = JSON.parse(extractJson(input?.value)); } catch { return; }

  const contractIssue = bundleContractIssue(parsed);
  if (contractIssue) {
    event.preventDefault();
    event.stopImmediatePropagation();
    status.textContent = `Import du résultat IA impossible : ${contractIssue}`;
    return;
  }
  if (!isBundle(parsed)) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  const base = apiBase();
  if (!base) { status.textContent = 'URL API BrickHouse manquante.'; return; }
  button.disabled = true;
  status.textContent = 'BrickHouse vérifie d’abord le relevé contenu dans le fichier résultat…';

  try {
    const surveyResponse = await fetch(`${base}/api/v1/validate-survey`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.survey),
    });
    const surveyPayload = await surveyResponse.json();
    if (!surveyResponse.ok) throw new Error(`Survey invalide : ${formatDetail(surveyPayload.detail)}`);
    if (!surveyPayload.valid_for_scene_fusion) {
      const messages = (surveyPayload.issues ?? []).filter(item => item.severity === 'error').map(item => item.message);
      throw new Error(messages.join(' ') || 'Le relevé contenu dans le fichier résultat est refusé.');
    }

    localStorage.setItem('brickhouse.pendingArchitecturalSurvey', JSON.stringify(surveyPayload));
    const frontWidth = (surveyPayload.survey?.known_measurements ?? []).find(item => item.kind === 'front_width');
    if (frontWidth?.value && knownWidth) {
      knownWidth.value = String(frontWidth.value);
      localStorage.setItem('brickhouse.knownFrontWidthM', String(frontWidth.value));
    }

    input.value = JSON.stringify(parsed.scene, null, 2);
    status.textContent = 'Relevé valide. BrickHouse contrôle maintenant automatiquement la reconstruction 3D…';
    handingOffScene = true;
    button.disabled = false;
    setTimeout(() => {
      try { button.click(); }
      finally { handingOffScene = false; }
    }, 0);
  } catch (error) {
    button.disabled = false;
    status.textContent = `Import du résultat IA impossible : ${error.message}`;
  }
}, { capture: true });
