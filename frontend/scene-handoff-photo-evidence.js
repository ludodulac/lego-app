const PHOTO_EVIDENCE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf';
const SCENE_HANDOFF_FILENAME = 'BRICKHOUSE-SURVEY-TO-SCENE.txt';
const SCENE_HANDOFF_VERSION = 'scene-handoff-0.2-photo-evidence';

function pendingValidatedSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return payload?.valid_for_scene_fusion ? payload.survey : null;
  } catch {
    return null;
  }
}

function downloadText(filename, content) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function decorateSceneHandoffButton() {
  const button = document.querySelector('#download-scene-handoff');
  if (!button || button.dataset.photoEvidenceContract === '1') return;
  button.dataset.photoEvidenceContract = '1';
  button.textContent = 'Créer le fichier Survey → Scene (photos requises)';
  const helper = document.createElement('p');
  helper.className = 'microcopy scene-photo-evidence-note';
  helper.innerHTML = `Cette étape doit être envoyée à l’IA avec le PDF photo original <strong>${PHOTO_EVIDENCE_FILENAME}</strong>. Aucune nouvelle photo n’est nécessaire.`;
  button.closest('p')?.insertAdjacentElement('afterend', helper);
}

const observer = new MutationObserver(decorateSceneHandoffButton);
observer.observe(document.documentElement, { childList: true, subtree: true });
decorateSceneHandoffButton();

document.addEventListener('click', async event => {
  const button = event.target.closest?.('#download-scene-handoff');
  if (!button) return;

  event.preventDefault();
  event.stopImmediatePropagation();

  const status = document.querySelector('#status');
  const survey = pendingValidatedSurvey();
  if (!survey) {
    if (status) status.textContent = 'Aucun ArchitecturalSurvey validé disponible pour préparer la Scene.';
    return;
  }

  button.disabled = true;
  if (status) status.textContent = 'Préparation du handoff Survey → Scene avec contrat de preuve photo…';
  try {
    const response = await fetch('./brickhouse-survey-to-scene-prompt.txt', { cache: 'no-store' });
    if (!response.ok) throw new Error(`prompt Survey → Scene : HTTP ${response.status}`);
    const prompt = await response.text();
    const handoff = `BRICKHOUSE — HANDOFF SURVEY → SCENE AVEC PREUVES PHOTO\nHANDOFF_VERSION=${SCENE_HANDOFF_VERSION}\n\nENTRÉES OBLIGATOIRES — DEUX FICHIERS\n1. CE fichier ${SCENE_HANDOFF_FILENAME}.\n2. Le PDF photo original ${PHOTO_EVIDENCE_FILENAME} qui a servi à produire le Survey validé.\n\nRÈGLE DE PRIORITÉ\nLe présent handoff définit la tâche active Survey → Scene. Le PDF photo est fourni UNIQUEMENT comme source de preuves visuelles et métriques. Ignore dans ce PDF toute ancienne instruction demandant de produire un Survey : ne produis PAS de nouveau Survey et ne modifies PAS le Survey validé ci-dessous. Analyse seulement ses pages photo et leurs libellés/orientations comme preuves complémentaires.\n\nINTERDICTION DE PROJECTION SANS IMAGES\nNe tente pas de reconstruire la Scene depuis le Survey textuel seul. Pour toute profondeur, hauteur, volume secondaire, pente ou raccord physique, recoupe obligatoirement le Survey avec les pages photo du PDF. Si le PDF photo n’est pas réellement accessible dans cette conversation, ne fabrique aucune métrique : indique que l’entrée photo obligatoire manque au lieu de produire une Scene faussement complète.\n\nENTRÉE SÉMANTIQUE AUTORITATIVE\nLe JSON ArchitecturalSurvey v0.1 placé à la fin de ce fichier est déjà validé par BrickHouse. Il reste la source de vérité pour l’inventaire, les IDs, les certitudes et les relations. Les photos peuvent préciser la géométrie métrique mais ne peuvent pas supprimer ou renommer un fait Survey certain.\n\nOBJECTIF MÉTRIQUE\nUtilise la largeur utilisateur du Survey comme ancre d’échelle lorsqu’elle existe. À partir des vues originales, estime prudemment les rapports nécessaires à volume_main.depth, volume_main.height et aux dimensions des volumes secondaires multi-vues. Pour les relations certaines dont le contact est visible sur les photos, résous conjointement les positions/dimensions et encode geometry_status:\"resolved\" lorsque le contact est géométriquement défendable. Conserve null/unresolved seulement si les images ne permettent réellement pas de borner la métrique.\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé exactement brickhouse-scene-result.json. Son contenu doit être UNIQUEMENT un objet ArchitecturalScene v0.2 complet à la racine, avec schema_version \"0.2\". Ne renvoie ni le Survey ni une enveloppe external-bundle.\n\nLa réponse finale du chat doit seulement annoncer ou joindre brickhouse-scene-result.json.\n\n================ PROMPT SURVEY → SCENE ================\n${prompt}\n\n================ ARCHITECTURAL SURVEY VALIDÉ ================\n${JSON.stringify(survey, null, 2)}\n`;
    downloadText(SCENE_HANDOFF_FILENAME, handoff);
    if (status) status.textContent = `${SCENE_HANDOFF_FILENAME} prêt · ${SCENE_HANDOFF_VERSION}. Envoyez-le à l’IA AVEC ${PHOTO_EVIDENCE_FILENAME}. Ne reprenez aucune photo.`;
  } catch (error) {
    if (status) status.textContent = `Impossible de préparer le fichier Survey → Scene : ${error.message}`;
  } finally {
    button.disabled = false;
  }
}, true);
