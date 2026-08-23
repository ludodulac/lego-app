const grid = document.querySelector('#guided-photo-grid');
const packageButton = document.querySelector('#download-ai-package');
const packageStatus = document.querySelector('#ai-package-status');
const technicalPhotos = document.querySelector('#photos');
const extraPhotosInput = document.querySelector('#guided-extra-photos');
const extraSummary = document.querySelector('#guided-extra-summary');
const notesInput = document.querySelector('#notes');
const knownWidthInput = document.querySelector('#known-width');
const studsInput = document.querySelector('#studs');

const slots = [...document.querySelectorAll('.guided-photo-slot')];
const MAX_TOTAL_PHOTOS = 12;
const MAX_EXTRA_PHOTOS = 6;
const HANDOFF_SCHEMA_VERSION = 'handoff-0.4';
const INSTRUCTION_FILENAME = 'brickhouse-analyse-instructions.txt';
const EXTERNAL_AI_LAUNCH_MESSAGE = `Exécute immédiatement la tâche BrickHouse définie dans le fichier brickhouse-analyse-instructions.txt joint, en utilisant toutes les photos jointes comme vues du même bâtiment. Le fichier texte est l’instruction utilisateur principale, pas une documentation facultative. Ne me demande pas ce que je souhaite obtenir et ne propose pas d’autres analyses. Suis intégralement le protocole qu’il contient et crée à la fin le fichier téléchargeable brickhouse-external-result.json demandé.`;

function ensureLaunchInstruction() {
  let block = document.querySelector('#ai-launch-instruction-block');
  if (block) return block;
  block = document.createElement('div');
  block.id = 'ai-launch-instruction-block';
  block.className = 'field fallback-paste';
  block.hidden = true;
  block.innerHTML = `
    <label for="ai-launch-instruction">Message à envoyer avec les photos et le fichier d’instructions</label>
    <textarea id="ai-launch-instruction" rows="5" readonly spellcheck="false"></textarea>
    <button id="copy-ai-launch-instruction" type="button">Copier cette consigne</button>
    <small>Dans une nouvelle conversation IA, joignez les photos originales et ${INSTRUCTION_FILENAME}, puis envoyez exactement cette consigne. N’ajoutez aucune explication sur le bâtiment.</small>`;
  packageStatus?.insertAdjacentElement('afterend', block);
  const textarea = block.querySelector('#ai-launch-instruction');
  textarea.value = EXTERNAL_AI_LAUNCH_MESSAGE;
  block.querySelector('#copy-ai-launch-instruction')?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(EXTERNAL_AI_LAUNCH_MESSAGE);
      packageStatus.textContent = 'Consigne BrickHouse copiée. Collez-la dans le même message que les photos et le fichier d’instructions.';
    } catch {
      textarea.focus();
      textarea.select();
      packageStatus.textContent = 'Copie automatique indisponible : copiez la consigne affichée ci-dessous.';
    }
  });
  return block;
}

function selectedSlotRecords() {
  return slots.flatMap((slot) => {
    const input = slot.querySelector('.guided-photo-input');
    const note = slot.querySelector('.guided-photo-note');
    const files = [...(input?.files ?? [])];
    return files.map((file, fileIndex) => ({
      slot: slot.dataset.slot,
      label: slot.dataset.label,
      slot_view_index: fileIndex + 1,
      file,
      note: note?.value.trim() ?? '',
      role: 'guided_base',
    }));
  });
}

function selectedExtraRecords() {
  return [...(extraPhotosInput?.files ?? [])].slice(0, MAX_EXTRA_PHOTOS).map((file, index) => ({
    slot: `extra_${index + 1}`,
    label: `Vue supplémentaire ${index + 1}`,
    slot_view_index: 1,
    file,
    note: '',
    role: 'targeted_extra',
  }));
}

function selectedPhotoRecords() {
  return [...selectedSlotRecords(), ...selectedExtraRecords()].slice(0, MAX_TOTAL_PHOTOS);
}

function syncTechnicalPhotoInput() {
  if (!technicalPhotos || typeof DataTransfer === 'undefined') return;
  const transfer = new DataTransfer();
  for (const record of selectedPhotoRecords()) transfer.items.add(record.file);
  technicalPhotos.files = transfer.files;
  technicalPhotos.dispatchEvent(new Event('change', { bubbles: true }));
}

function updateSlot(slot) {
  const input = slot.querySelector('.guided-photo-input');
  const name = slot.querySelector('.guided-photo-name');
  const files = [...(input?.files ?? [])];
  slot.classList.toggle('has-photo', files.length > 0);
  if (!name) return;
  if (!files.length) name.textContent = 'Aucune photo';
  else if (files.length === 1) name.textContent = files[0].name;
  else name.textContent = `${files.length} photos sélectionnées`;
}

function updateExtraSummary() {
  if (!extraSummary) return;
  const count = selectedExtraRecords().length;
  if (!count) {
    extraSummary.textContent = 'Ajoutez-les surtout lorsqu’une zone complexe est mal visible : escalier tournant, dessous de terrasse, arrière masqué, jonction de volumes, toiture particulière… Jusqu’à 6 vues supplémentaires.';
    return;
  }
  extraSummary.textContent = `${count} vue(s) supplémentaire(s) sélectionnée(s). Elles seront analysées avec les vues de base, pas comme des bâtiments séparés.`;
}

for (const slot of slots) {
  slot.querySelector('.guided-photo-input')?.addEventListener('change', () => {
    updateSlot(slot);
    const total = selectedSlotRecords().length + selectedExtraRecords().length;
    if (total > MAX_TOTAL_PHOTOS) packageStatus.textContent = `BrickHouse utilise au maximum ${MAX_TOTAL_PHOTOS} photos au total. Retirez quelques vues redondantes.`;
    syncTechnicalPhotoInput();
  });
}

extraPhotosInput?.addEventListener('change', () => {
  if ((extraPhotosInput.files?.length ?? 0) > MAX_EXTRA_PHOTOS) packageStatus.textContent = `Gardez au maximum ${MAX_EXTRA_PHOTOS} vues supplémentaires ciblées.`;
  updateExtraSummary();
  syncTechnicalPhotoInput();
});

async function fetchText(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path} : HTTP ${response.status}`);
  return response.text();
}

function manifestFor(records) {
  return {
    schema_version: HANDOFF_SCHEMA_VERSION,
    kind: 'brickhouse_external_ai_handoff',
    instruction_file: INSTRUCTION_FILENAME,
    launch_instruction: EXTERNAL_AI_LAUNCH_MESSAGE,
    known_front_width_m: Number(knownWidthInput?.value) > 0 ? Number(knownWidthInput.value) : null,
    target_front_width_studs: Number(studsInput?.value) || 48,
    general_notes: notesInput?.value.trim() || '',
    capture_strategy: {
      guided_base_views: records.filter(item => item.role === 'guided_base').length,
      guided_base_zones: new Set(records.filter(item => item.role === 'guided_base').map(item => item.slot)).size,
      targeted_extra_views: records.filter(item => item.role === 'targeted_extra').length,
      principle: 'few_high_value_views_plus_targeted_extras',
    },
    photos: records.map((item, index) => ({
      photo_index: index + 1,
      slot: item.slot,
      label: item.label,
      slot_view_index: item.slot_view_index,
      capture_role: item.role,
      original_filename: item.file.name,
      media_type: item.file.type,
      user_note: item.note,
    })),
  };
}

function requestText(records) {
  const width = Number(knownWidthInput?.value);
  const general = notesInput?.value.trim() || 'Aucune précision générale.';
  const photoLines = records.map((item, idx) => `${idx + 1}. ${item.file.name} — repère utilisateur : ${item.label}${item.role === 'guided_base' && item.slot_view_index > 1 ? ` (vue ${item.slot_view_index} de cette zone)` : ''}${item.note ? ` — note : ${item.note}` : ''}`).join('\n');
  return `BRICKHOUSE — INSTRUCTION PRINCIPALE — À EXÉCUTER IMMÉDIATEMENT\n\nCe fichier définit la tâche demandée par l’utilisateur. Il ne s’agit pas d’une documentation facultative. Commence directement l’analyse sans demander ce que l’utilisateur souhaite obtenir et sans proposer de diagnostic alternatif.\n\nAnalyse toutes les photos jointes comme un ensemble multi-vues du même bâtiment. Les libellés ci-dessous sont seulement des repères de prise de vue : vérifie-les par le contenu réel des images et ne force jamais une photo à correspondre à son libellé. Plusieurs photos peuvent volontairement montrer le même côté ou le même angle depuis des positions différentes.\n\nVUES JOINTES\n${photoLines}\n\nINFORMATIONS UTILISATEUR\n- Informations générales : ${general}\n- Largeur avant connue : ${Number.isFinite(width) && width > 0 ? `${width} m` : 'inconnue'}\n- Taille cible : ${Number(studsInput?.value) || 48} tenons de façade\n\nRÈGLES NON NÉGOCIABLES\n- Ne jamais inventer une ouverture ou une structure dans une zone cachée.\n- Verrouiller d’abord topologie et correspondances multi-vues, puis nombre d’ouvertures par pan, identité, ordre, position et dimensions.\n- Une géométrie plausible ne devient pas certaine parce qu’elle ferme proprement une chaîne de circulation.\n- Une porte en hauteur peut donner dans le vide : ne pas inventer balcon, palier, terrasse ou escalier.\n- Les primitives extérieures de Scene doivent être soutenues par le Survey et réutiliser exactement l'id stable correspondant.\n- Ne jamais inverser gauche/droite.\n- Ne jamais attribuer au bâtiment cible un élément d’un bâtiment voisin.\n- Toute mesure utilisateur reste prioritaire avec source.kind=user_provided.\n- Le bâtiment peut être non rectangulaire, multi-volume ou atypique : ne pas imposer la maison benchmark comme modèle général.\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé brickhouse-external-result.json avec exactement cette enveloppe :\n{\n  "schema_version": "external-bundle-0.1",\n  "kind": "brickhouse_external_result",\n  "survey": { "...": "ArchitecturalSurvey v0.1 complet" },\n  "scene": { "...": "ArchitecturalScene v0.2 complet reconstruit uniquement depuis ce Survey" }\n}\n\nSi une ambiguïté réelle subsiste, conserve-la explicitement comme incertitude au lieu de demander à l’utilisateur de choisir une architecture plausible.\n`;
}

function combinedInstruction(records, topologyPrompt, surveyPrompt, scenePrompt) {
  const manifest = manifestFor(records);
  return `${requestText(records)}\n\n========================================\nMANIFESTE BRICKHOUSE\n========================================\n${JSON.stringify(manifest, null, 2)}\n\n========================================\nÉTAPE 1 — TOPOLOGIE MULTI-VUES\n========================================\n${topologyPrompt}\n\n========================================\nÉTAPE 2 — ARCHITECTURAL SURVEY\n========================================\n${surveyPrompt}\n\n========================================\nÉTAPE 3 — SURVEY → SCENE\n========================================\n${scenePrompt}\n`;
}

function downloadTextFile(filename, text, type = 'text/plain;charset=utf-8') {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

packageButton?.addEventListener('click', async () => {
  const records = [...selectedSlotRecords(), ...selectedExtraRecords()];
  if (!records.length) {
    packageStatus.textContent = 'Ajoutez au moins une photo avant de préparer les instructions.';
    return;
  }
  if (records.length > MAX_TOTAL_PHOTOS) {
    packageStatus.textContent = `BrickHouse accepte au maximum ${MAX_TOTAL_PHOTOS} photos au total. Vous en avez sélectionné ${records.length} : retirez quelques vues redondantes.`;
    return;
  }
  packageButton.disabled = true;
  packageStatus.textContent = 'Préparation des instructions BrickHouse…';
  try {
    const [topologyPrompt, surveyPrompt, scenePrompt] = await Promise.all([
      fetchText('./brickhouse-topology-prompt.txt'),
      fetchText('./brickhouse-survey-prompt.txt'),
      fetchText('./brickhouse-survey-to-scene-prompt.txt'),
    ]);
    downloadTextFile(INSTRUCTION_FILENAME, combinedInstruction(records, topologyPrompt, surveyPrompt, scenePrompt));
    const launchBlock = ensureLaunchInstruction();
    launchBlock.hidden = false;
    try {
      await navigator.clipboard.writeText(EXTERNAL_AI_LAUNCH_MESSAGE);
      packageStatus.textContent = `${records.length} photo(s) référencée(s). Le fichier ${INSTRUCTION_FILENAME} est téléchargé et la consigne de lancement est copiée. Dans une nouvelle conversation IA, joignez les mêmes photos + ce fichier, puis collez la consigne.`;
    } catch {
      packageStatus.textContent = `${records.length} photo(s) référencée(s). Le fichier ${INSTRUCTION_FILENAME} est téléchargé. Dans une nouvelle conversation IA, joignez les mêmes photos + ce fichier, puis copiez la consigne affichée ci-dessous.`;
    }
  } catch (error) {
    packageStatus.textContent = `Impossible de préparer les instructions : ${error.message}`;
  } finally {
    packageButton.disabled = false;
  }
});

technicalPhotos?.addEventListener('change', () => {
  if (technicalPhotos.files?.length && !selectedPhotoRecords().length) {
    packageStatus.textContent = 'Des photos ont été ajoutées via les options avancées. Pour le handoff IA guidé, placez-les plutôt dans les zones ci-dessus.';
  }
});
