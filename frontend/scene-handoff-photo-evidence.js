const PHOTO_EVIDENCE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.5.pdf';
const SCENE_HANDOFF_FILENAME = 'BRICKHOUSE-SURVEY-TO-SCENE.txt';
const SCENE_HANDOFF_VERSION = 'scene-handoff-0.5-photo-evidence';

function alignPromptWithPhotoEvidenceContract(prompt) {
  const authority = `AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO\nLe JSON ArchitecturalSurvey v0.1 validé reste la source de vérité autoritative pour l’inventaire, les IDs, les certitudes, les attributs et les relations. Le PDF photo original ${PHOTO_EVIDENCE_FILENAME} est requis uniquement comme preuve visuelle complémentaire pour borner les métriques de Scene : profondeur, hauteur, positions, dimensions secondaires, pente et raccords physiques.\nNe recommence PAS le Survey et ne modifie jamais un fait Survey certain à partir du PDF. Les pixels servent seulement à métriser ou à laisser null/unresolved ce que le Survey a déjà identifié.\nSi le PDF n’est pas accessible dans la conversation, ne fabrique aucune métrique manquante : indique que l’entrée photo obligatoire manque. Ne retourne pas une Scene vide comme substitut à une reconstruction non exécutée.\nSi les deux fichiers sont présents, exploite obligatoirement le Survey ET les pages photo avant de conclure qu’une métrique est inconnue.`;
  const aligned = prompt
    .replace(/AUTORITÉ DE L’ENTRÉE — AUCUN FICHIER SUPPLÉMENTAIRE[\s\S]*?\n\nPORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE/, `${authority}\n\nPORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE`)
    .replace('- aucune dépendance à des photos/PDF/fichiers externes n’a été introduite ;', '- le PDF photo original a été utilisé uniquement comme preuve géométrique complémentaire ;');
  if (aligned.includes('AUTORITÉ DE L’ENTRÉE — AUCUN FICHIER SUPPLÉMENTAIRE') || aligned.includes('N’exige, ne réclame et ne suppose aucun PDF') || aligned.includes('Tu N’AS PAS accès aux photos originales')) throw new Error('contrat Survey → Scene contradictoire avec le handoff photo');
  return aligned;
}
function pendingValidatedSurvey() { try { const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null'); return payload?.valid_for_scene_fusion ? payload.survey : null; } catch { return null; } }
function downloadText(filename, content) { const blob = new Blob([content], { type: 'text/plain;charset=utf-8' }); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
function normalizeEvidenceList(items) { if (!Array.isArray(items)) return items; return items.flatMap(item => { if (item && typeof item === 'object' && Number.isInteger(item.photo_index) && item.photo_index > 0) return [item]; if (typeof item !== 'string') return []; const match = item.trim().match(/^photo:(\d+)$/i); if (!match) return []; const photoIndex = Number(match[1]); if (!Number.isInteger(photoIndex) || photoIndex < 1) return []; return [{ photo_index: photoIndex, observation: `Référence photo externe ${item.trim()}` }]; }); }
function normalizeExternalScene(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
  const normalized = { ...value };
  if (Array.isArray(normalized.volumes)) normalized.volumes = normalized.volumes.map(item => item && typeof item === 'object' ? { ...item, evidence: normalizeEvidenceList(item.evidence) } : item);
  for (const key of ['openings', 'chimneys', 'platforms', 'stairs', 'supports']) if (Array.isArray(normalized[key])) normalized[key] = normalized[key].map(item => item && typeof item === 'object' ? { ...item, evidence: normalizeEvidenceList(item.evidence) } : item);
  return normalized;
}
async function buildSceneHandoff() {
  const survey = pendingValidatedSurvey();
  if (!survey) throw new Error('Aucun ArchitecturalSurvey validé disponible. Importez d’abord le Survey retourné par l’IA.');
  const response = await fetch('./brickhouse-survey-to-scene-prompt.txt', { cache: 'no-store' });
  if (!response.ok) throw new Error(`prompt Survey → Scene indisponible: HTTP ${response.status}`);
  const prompt = alignPromptWithPhotoEvidenceContract(await response.text());
  return `BRICKHOUSE — HANDOFF SURVEY -> SCENE\nHANDOFF_VERSION=${SCENE_HANDOFF_VERSION}\n\nFICHIERS OBLIGATOIRES DANS LE MÊME CHAT\n1. Ce fichier ${SCENE_HANDOFF_FILENAME}\n2. Le PDF photo original ${PHOTO_EVIDENCE_FILENAME}\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé exactement brickhouse-scene-result.json contenant directement un ArchitecturalScene v0.2, sans wrapper.\n\n================ SURVEY VALIDÉ — AUTORITATIF ================\n${JSON.stringify(survey, null, 2)}\n\n================ CONTRAT SURVEY -> SCENE ================\n${prompt}\n`;
}
window.brickhouseScenePhotoEvidence = { PHOTO_EVIDENCE_FILENAME, SCENE_HANDOFF_FILENAME, SCENE_HANDOFF_VERSION, buildSceneHandoff, normalizeExternalScene, pendingValidatedSurvey, downloadText };
