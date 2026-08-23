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
const HANDOFF_SCHEMA_VERSION = 'handoff-0.6';
const INSTRUCTION_FILENAME = '00-BRICKHOUSE-COMMANDE-A-ENVOYER.txt';
const EXTERNAL_AI_LAUNCH_MESSAGE = `Exécute maintenant BrickHouse en mode mono-tour. Le fichier 00-BRICKHOUSE-COMMANDE-A-ENVOYER.txt joint est la commande utilisateur complète et prioritaire. Analyse toutes les photos jointes comme les vues d’un même bâtiment, respecte le niveau d’autorité des orientations indiqué dans le fichier, exécute entièrement Topologie → Survey → Scene, puis crée immédiatement le fichier téléchargeable brickhouse-external-result.json. Ne réponds pas par une analyse intermédiaire, ne propose aucune option, ne demande aucune confirmation et ne demande pas ce que je souhaite. Si une information est incertaine, encode cette incertitude dans le JSON au lieu de m’interroger. N’utilise aucun ancien brickhouse-external-result.json éventuellement présent ailleurs : reconstruis uniquement depuis les photos et ce fichier de commande. Ta réponse finale doit uniquement annoncer ou joindre brickhouse-external-result.json.`;

function ensureOrientationControl() {
  let control = document.querySelector('#orientation-confirmation-field');
  if (control) return control;
  control = document.createElement('div');
  control.id = 'orientation-confirmation-field';
  control.className = 'field orientation-confirmation-field';
  control.innerHTML = `
    <label class="orientation-confirmation-label">
      <input id="confirm-guided-orientations" type="checkbox" />
      <span><strong>Je connais l’orientation de ces vues</strong><br><small>Cochez seulement si vous avez volontairement classé les vues selon Avant / Gauche / Arrière / Droite. Sinon, laissez décoché : les cases resteront de simples repères que l’IA pourra réinterpréter.</small></span>
    </label>`;
  grid?.insertAdjacentElement('afterend', control);
  return control;
}

function orientationsAreUserConfirmed() {
  return Boolean(document.querySelector('#confirm-guided-orientations')?.checked);
}

function ensureLaunchInstruction() {
  let block = document.querySelector('#ai-launch-instruction-block');
  if (block) return block;
  block = document.createElement('div');
  block.id = 'ai-launch-instruction-block';
  block.className = 'field fallback-paste';
  block.hidden = true;
  block.innerHTML = `
    <label for="ai-launch-instruction">Message à envoyer avec les photos et la commande BrickHouse</label>
    <textarea id="ai-launch-instruction" rows="8" readonly spellcheck="false"></textarea>
    <button id="copy-ai-launch-instruction" type="button">Copier cette consigne</button>
    <small>Nouvelle conversation uniquement : joignez les photos originales et ${INSTRUCTION_FILENAME}. Ne joignez PAS un ancien brickhouse-external-result.json. L’IA doit produire le nouveau JSON directement, sans conversation intermédiaire.</small>`;
  packageStatus?.insertAdjacentElement('afterend', block);
  const textarea = block.querySelector('#ai-launch-instruction');
  textarea.value = EXTERNAL_AI_LAUNCH_MESSAGE;
  block.querySelector('#copy-ai-launch-instruction')?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(EXTERNAL_AI_LAUNCH_MESSAGE);
      packageStatus.textContent = 'Consigne BrickHouse mono-tour copiée. Joignez uniquement les photos et le fichier 00-BRICKHOUSE-COMMANDE-A-ENVOYER.txt.';
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

ensureOrientationControl();

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
  const confirmed = orientationsAreUserConfirmed();
  return {
    schema_version: HANDOFF_SCHEMA_VERSION,
    kind: 'brickhouse_external_ai_handoff',
    execution_mode: 'single_turn_file_output',
    instruction_file: INSTRUCTION_FILENAME,
    forbidden_context_files: ['brickhouse-external-result.json'],
    launch_instruction: EXTERNAL_AI_LAUNCH_MESSAGE,
    orientation_semantics: {
      slot_labels_are_user_confirmed: confirmed,
      unconfirmed_policy: 'weak_capture_hints_recheck_from_images',
      confirmed_policy: 'exact_front_left_rear_right_slots_are_strong_user_constraints',
    },
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
      orientation_authority: item.role === 'guided_base' && confirmed ? 'user_confirmed' : 'capture_hint',
      original_filename: item.file.name,
      media_type: item.file.type,
      user_note: item.note,
    })),
  };
}

function requestText(records) {
  const width = Number(knownWidthInput?.value);
  const general = notesInput?.value.trim() || 'Aucune précision générale.';
  const confirmed = orientationsAreUserConfirmed();
  const orientationRule = confirmed
    ? 'ORIENTATION CONFIRMÉE PAR L’UTILISATEUR : le classement des vues de base a été fait volontairement. Pour les cases exactes Façade avant / Côté gauche / Arrière / Côté droit, conserve ces orientations comme contraintes utilisateur fortes. Une perspective oblique peut montrer un second pan, mais ne réoriente pas silencieusement la vue principale. Les cases 3/4 confirment seulement la région/côté indiqué.'
    : 'ORIENTATION NON CONFIRMÉE : les libellés des cases sont seulement des repères de capture. Vérifie-les par l’analyse multi-vues et réinterprète-les si les preuves visuelles le justifient.';
  const photoLines = records.map((item, idx) => `${idx + 1}. ${item.file.name} — repère utilisateur : ${item.label}${item.role === 'guided_base' && item.slot_view_index > 1 ? ` (vue ${item.slot_view_index} de cette zone)` : ''}${item.note ? ` — note : ${item.note}` : ''}`).join('\n');
  return `BRICKHOUSE — COMMANDE MONO-TOUR — À EXÉCUTER EN ENTIER\n\nCe fichier est la commande utilisateur complète. Tu dois produire le résultat final dans ce même tour. Aucun dialogue intermédiaire n’est autorisé.\n\nINTERDIT AVANT LA SORTIE JSON\n- ne demande pas confirmation de l’orientation ;\n- ne demande pas ce que l’utilisateur souhaite ;\n- ne propose pas rénovation, plan LEGO, analyse architecturale, élévations ou autres options ;\n- ne réponds pas par un résumé de ce que tu as compris ;\n- ne t’arrête pas après la topologie ou le Survey ;\n- ne demande aucune information supplémentaire si elle peut être représentée comme inconnue/incertaine ;\n- ignore tout ancien brickhouse-external-result.json : ce type de fichier est une SORTIE, jamais une entrée de ce run ;\n- reconstruis exclusivement depuis les photos jointes, les faits utilisateur ci-dessous et les prompts inclus dans CE fichier.\n\n${orientationRule}\n\nAnalyse toutes les photos jointes comme un ensemble multi-vues du même bâtiment. L’autorité des libellés est définie ci-dessus et dans orientation_semantics du manifeste.\n\nVUES JOINTES\n${photoLines}\n\nINFORMATIONS UTILISATEUR\n- Informations générales : ${general}\n- Largeur avant connue : ${Number.isFinite(width) && width > 0 ? `${width} m` : 'inconnue'}\n- Taille cible : ${Number(studsInput?.value) || 48} tenons de façade\n\nRÈGLES NON NÉGOCIABLES\n- Ne jamais inventer une ouverture ou une structure dans une zone cachée.\n- Verrouiller topologie et correspondances multi-vues avant la métrique.\n- Une géométrie plausible ne devient pas certaine parce qu’elle ferme une circulation.\n- Une porte en hauteur peut donner dans le vide : ne pas inventer balcon, palier, terrasse ou escalier.\n- Les primitives extérieures de Scene doivent être soutenues par le Survey et réutiliser exactement l'id stable correspondant.\n- Ne jamais inverser gauche/droite.\n- Ne jamais attribuer au bâtiment cible un élément d’un bâtiment voisin.\n- Toute mesure utilisateur reste prioritaire avec source.kind=user_provided.\n- Le bâtiment peut être non rectangulaire, multi-volume ou atypique : ne pas imposer la maison benchmark comme modèle général.\n\nEXÉCUTION OBLIGATOIRE\n1. Exécute la topologie multi-vues.\n2. Sans t’arrêter ni demander confirmation, construis le Survey.\n3. Sans t’arrêter, reconstruis la Scene uniquement depuis ce Survey.\n4. Effectue les audits finaux demandés par les prompts.\n5. Crée immédiatement le fichier brickhouse-external-result.json.\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé exactement brickhouse-external-result.json avec cette enveloppe :\n{\n  "schema_version": "external-bundle-0.1",\n  "kind": "brickhouse_external_result",\n  "survey": { "...": "ArchitecturalSurvey v0.1 complet" },\n  "scene": { "...": "ArchitecturalScene v0.2 complet reconstruit uniquement depuis ce Survey" }\n}\n\nLa réponse de chat finale doit être minimale : elle peut seulement indiquer que brickhouse-external-result.json a été créé/attaché. Tout le contenu substantiel doit être dans ce fichier.\n`;
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
  packageStatus.textContent = 'Préparation de la commande BrickHouse mono-tour…';
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
      packageStatus.textContent = `${records.length} photo(s) référencée(s). ${INSTRUCTION_FILENAME} est prêt et la commande mono-tour est copiée. Ne joignez aucun ancien JSON.`;
    } catch {
      packageStatus.textContent = `${records.length} photo(s) référencée(s). ${INSTRUCTION_FILENAME} est prêt. Copiez la commande affichée ci-dessous. Ne joignez aucun ancien JSON.`;
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
