const PHOTO_EVIDENCE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf';
const SCENE_HANDOFF_FILENAME = 'BRICKHOUSE-SURVEY-TO-SCENE.txt';
const SCENE_HANDOFF_VERSION = 'scene-handoff-0.4-photo-evidence';

function alignPromptWithPhotoEvidenceContract(prompt) {
  const authority = `AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO\nLe JSON ArchitecturalSurvey v0.1 validé reste la source de vérité autoritative pour l’inventaire, les IDs, les certitudes, les attributs et les relations. Le PDF photo original ${PHOTO_EVIDENCE_FILENAME} est requis uniquement comme preuve visuelle complémentaire pour borner les métriques de Scene : profondeur, hauteur, positions, dimensions secondaires, pente et raccords physiques.\nNe recommence PAS le Survey et ne modifie jamais un fait Survey certain à partir du PDF. Les pixels servent seulement à métriser ou à laisser null/unresolved ce que le Survey a déjà identifié.\nSi le PDF n’est pas accessible dans la conversation, ne fabrique aucune métrique manquante : indique que l’entrée photo obligatoire manque. Ne retourne pas une Scene vide comme substitut à une reconstruction non exécutée.\nSi les deux fichiers sont présents, exploite obligatoirement le Survey ET les pages photo avant de conclure qu’une métrique est inconnue.`;
  const aligned = prompt
    .replace(
      /AUTORITÉ DE L’ENTRÉE — AUCUN FICHIER SUPPLÉMENTAIRE[\s\S]*?\n\nPORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE/,
      `${authority}\n\nPORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE`,
    )
    .replace(
      '- aucune dépendance à des photos/PDF/fichiers externes n’a été introduite ;',
      '- le PDF photo original a été utilisé uniquement comme preuve géométrique complémentaire ;',
    );
  if (
    aligned.includes('AUTORITÉ DE L’ENTRÉE — AUCUN FICHIER SUPPLÉMENTAIRE')
    || aligned.includes('N’exige, ne réclame et ne suppose aucun PDF')
    || aligned.includes('Tu N’AS PAS accès aux photos originales')
  ) {
    throw new Error('contrat Survey → Scene contradictoire avec le handoff photo');
  }
  return aligned;
}

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

function normalizeEvidenceList(items) {
  if (!Array.isArray(items)) return items;
  return items.flatMap(item => {
    if (item && typeof item === 'object' && Number.isInteger(item.photo_index) && item.photo_index > 0) return [item];
    if (typeof item !== 'string') return [];
    const match = item.trim().match(/^photo:(\d+)$/i);
    if (!match) return [];
    const photoIndex = Number(match[1]);
    if (!Number.isInteger(photoIndex) || photoIndex < 1) return [];
    return [{ photo_index: photoIndex, observation: `Référence photo externe ${item.trim()}` }];
  });
}

function normalizeExternalScene(value) {
  if (!value || typeof value !== 'object' || value.schema_version !== '0.2') return value;
  const clone = JSON.parse(JSON.stringify(value));
  const visit = node => {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) {
      node.forEach(visit);
      return;
    }
    if (Array.isArray(node.evidence)) node.evidence = normalizeEvidenceList(node.evidence);
    Object.values(node).forEach(visit);
  };
  visit(clone);

  for (const volume of clone.volumes ?? []) {
    if (volume?.floors && typeof volume.floors === 'object') {
      const numeric = Number(volume.floors.value);
      if (Number.isInteger(numeric) && numeric >= 1 && numeric <= 10) volume.floors = numeric;
    }
  }
  for (const platform of clone.platforms ?? []) {
    if (platform?.thickness == null && Number(platform?.height) > 0) {
      platform.thickness = Number(platform.height);
      delete platform.height;
    }
  }
  if (!clone.appearance || typeof clone.appearance !== 'object' || Array.isArray(clone.appearance)) clone.appearance = {};
  return clone;
}

function normalizeSceneTextareaBeforeImport(event) {
  const button = event.target.closest?.('#import-analysis');
  if (!button) return;
  const textarea = document.querySelector('#external-analysis');
  if (!textarea?.value.trim()) return;
  try {
    const parsed = JSON.parse(textarea.value.trim());
    if (parsed?.schema_version !== '0.2') return;
    textarea.value = JSON.stringify(normalizeExternalScene(parsed), null, 2);
  } catch {
    // The normal import path owns JSON syntax errors and user-facing diagnostics.
  }
}

document.addEventListener('click', normalizeSceneTextareaBeforeImport, true);

function decorateSceneHandoffButton() {
  const button = document.querySelector('#download-scene-handoff');
  if (!button || button.dataset.photoEvidenceContract === '1') return;
  button.dataset.photoEvidenceContract = '1';
  button.textContent = 'Créer le fichier Survey → Scene (PDF photo requis)';
  const helper = document.createElement('p');
  helper.className = 'microcopy scene-photo-evidence-note';
  helper.innerHTML = `À l’étape suivante, envoyez à l’IA <strong>deux fichiers</strong> : ce handoff et le PDF photo original <strong>${PHOTO_EVIDENCE_FILENAME}</strong>. Le Survey reste autoritatif ; le PDF sert uniquement à reconstruire la géométrie.`;
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
    const prompt = alignPromptWithPhotoEvidenceContract(await response.text());
    const handoff = `BRICKHOUSE — HANDOFF SURVEY → SCENE AVEC PREUVES PHOTO\nHANDOFF_VERSION=${SCENE_HANDOFF_VERSION}\n\nENTRÉES OBLIGATOIRES — DEUX FICHIERS\n1. CE fichier ${SCENE_HANDOFF_FILENAME}.\n2. Le PDF photo original ${PHOTO_EVIDENCE_FILENAME} qui a servi à produire le Survey validé.\n\nRÈGLE DE PRIORITÉ\nLe présent handoff définit la tâche active Survey → Scene. Le PDF photo est fourni UNIQUEMENT comme source de preuves visuelles et métriques. Ignore dans ce PDF toute ancienne instruction demandant de produire un Survey : ne produis PAS de nouveau Survey et ne modifies PAS le Survey validé ci-dessous. Analyse seulement ses pages photo et leurs libellés/orientations comme preuves complémentaires.\n\nINTERDICTION DE PROJECTION SANS IMAGES\nNe tente pas de reconstruire la Scene depuis le Survey textuel seul. Pour toute profondeur, hauteur, volume secondaire, pente ou raccord physique, recoupe obligatoirement le Survey avec les pages photo du PDF. Si le PDF photo n’est pas réellement accessible dans cette conversation, ne fabrique aucune métrique : indique que l’entrée photo obligatoire manque au lieu de produire une Scene faussement complète.\n\nENTRÉE SÉMANTIQUE AUTORITATIVE\nLe JSON ArchitecturalSurvey v0.1 placé à la fin de ce fichier est déjà validé par BrickHouse. Il reste la source de vérité pour l’inventaire, les IDs, les certitudes et les relations. Les photos peuvent préciser la géométrie métrique mais ne peuvent pas supprimer ou renommer un fait Survey certain.\n\nCONTRAT DE SÉRIALISATION — OBLIGATOIRE\nChaque evidence Scene est un OBJET exactement de la forme { \"photo_index\": 1, \"observation\": \"preuve visible\" }. N’écris jamais une chaîne comme \"photo:1\", \"known_measurement:front_width\" ou un ID Survey dans un tableau evidence. Une PropertyValue user_provided peut avoir evidence:[] si sa provenance est déjà portée par source. SceneVolume.floors est un ENTIER, jamais un PropertyValue. Platform utilise thickness, jamais height. appearance est toujours présent ; si aucune couleur n’est défendable, utilise l’objet vide {}.\n\nOBJECTIF MÉTRIQUE\nUtilise la largeur utilisateur du Survey comme ancre d’échelle lorsqu’elle existe. À partir des vues originales, estime prudemment les rapports nécessaires à volume_main.depth, volume_main.height et aux dimensions des volumes secondaires multi-vues. Pour les relations certaines dont le contact est visible sur les photos, résous conjointement les positions/dimensions et encode geometry_status:\"resolved\" lorsque le contact est géométriquement défendable. Conserve null/unresolved seulement si les images ne permettent réellement pas de borner la métrique.\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé exactement brickhouse-scene-result.json. Son contenu doit être UNIQUEMENT un objet ArchitecturalScene v0.2 complet à la racine, avec schema_version \"0.2\". Ne renvoie ni le Survey ni une enveloppe external-bundle.\n\nLa réponse finale du chat doit seulement annoncer ou joindre brickhouse-scene-result.json.\n\n================ PROMPT SURVEY → SCENE ================\n${prompt}\n\n================ ARCHITECTURAL SURVEY VALIDÉ ================\n${JSON.stringify(survey, null, 2)}\n`;
    downloadText(SCENE_HANDOFF_FILENAME, handoff);
    if (status) status.textContent = `${SCENE_HANDOFF_FILENAME} prêt · ${SCENE_HANDOFF_VERSION}. Étape suivante : envoyez ce TXT ET ${PHOTO_EVIDENCE_FILENAME} dans la même conversation IA.`;
  } catch (error) {
    if (status) status.textContent = `Impossible de préparer le fichier Survey → Scene : ${error.message}`;
  } finally {
    button.disabled = false;
  }
}, true);
