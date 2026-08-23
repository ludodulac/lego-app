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

function selectedSlotRecords() {
  return slots.map((slot, index) => {
    const input = slot.querySelector('.guided-photo-input');
    const note = slot.querySelector('.guided-photo-note');
    const file = input?.files?.[0] ?? null;
    return {
      slot: slot.dataset.slot,
      label: slot.dataset.label,
      index: index + 1,
      file,
      note: note?.value.trim() ?? '',
      role: 'guided_base',
    };
  }).filter(item => item.file);
}

function selectedExtraRecords() {
  return [...(extraPhotosInput?.files ?? [])].slice(0, MAX_EXTRA_PHOTOS).map((file, index) => ({
    slot: `extra_${index + 1}`,
    label: `Vue supplémentaire ${index + 1}`,
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
  const file = input?.files?.[0] ?? null;
  slot.classList.toggle('has-photo', Boolean(file));
  if (name) name.textContent = file ? file.name : 'Aucune photo';
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
  const input = slot.querySelector('.guided-photo-input');
  input?.addEventListener('change', () => {
    updateSlot(slot);
    syncTechnicalPhotoInput();
  });
}

extraPhotosInput?.addEventListener('change', () => {
  if ((extraPhotosInput.files?.length ?? 0) > MAX_EXTRA_PHOTOS) {
    packageStatus.textContent = `Gardez au maximum ${MAX_EXTRA_PHOTOS} vues supplémentaires ciblées.`;
  }
  updateExtraSummary();
  syncTechnicalPhotoInput();
});

// --- Minimal ZIP writer (stored/uncompressed files, UTF-8 names) ---
// This keeps the handoff self-contained without adding a runtime dependency.
const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(bytes) {
  let c = 0xffffffff;
  for (const byte of bytes) c = crcTable[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function u16(value) { return [value & 0xff, (value >>> 8) & 0xff]; }
function u32(value) { return [value & 0xff, (value >>> 8) & 0xff, (value >>> 16) & 0xff, (value >>> 24) & 0xff]; }
function concatArrays(chunks) {
  const total = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { out.set(chunk, offset); offset += chunk.length; }
  return out;
}

function dosDateTime(date = new Date()) {
  const year = Math.max(1980, date.getFullYear());
  const time = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
  const day = date.getDate();
  const month = date.getMonth() + 1;
  const dosDate = ((year - 1980) << 9) | (month << 5) | day;
  return { time, date: dosDate };
}

async function createZip(entries) {
  const encoder = new TextEncoder();
  const localChunks = [];
  const centralChunks = [];
  let offset = 0;
  const stamp = dosDateTime();

  for (const entry of entries) {
    const nameBytes = encoder.encode(entry.name);
    const data = entry.bytes instanceof Uint8Array ? entry.bytes : new Uint8Array(entry.bytes);
    const crc = crc32(data);
    const localHeader = new Uint8Array([
      ...u32(0x04034b50), ...u16(20), ...u16(0x0800), ...u16(0),
      ...u16(stamp.time), ...u16(stamp.date), ...u32(crc), ...u32(data.length), ...u32(data.length),
      ...u16(nameBytes.length), ...u16(0),
    ]);
    localChunks.push(localHeader, nameBytes, data);

    const centralHeader = new Uint8Array([
      ...u32(0x02014b50), ...u16(20), ...u16(20), ...u16(0x0800), ...u16(0),
      ...u16(stamp.time), ...u16(stamp.date), ...u32(crc), ...u32(data.length), ...u32(data.length),
      ...u16(nameBytes.length), ...u16(0), ...u16(0), ...u16(0), ...u16(0), ...u32(0), ...u32(offset),
    ]);
    centralChunks.push(centralHeader, nameBytes);
    offset += localHeader.length + nameBytes.length + data.length;
  }

  const central = concatArrays(centralChunks);
  const end = new Uint8Array([
    ...u32(0x06054b50), ...u16(0), ...u16(0), ...u16(entries.length), ...u16(entries.length),
    ...u32(central.length), ...u32(offset), ...u16(0),
  ]);
  return new Blob([...localChunks, central, end], { type: 'application/zip' });
}

async function fetchText(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path} : HTTP ${response.status}`);
  return response.text();
}

function requestText(records) {
  const width = Number(knownWidthInput?.value);
  const general = notesInput?.value.trim() || 'Aucune précision générale.';
  const photoLines = records.map((item, idx) => `${idx + 1}. ${item.label} (${item.role === 'targeted_extra' ? 'vue supplémentaire ciblée' : 'vue de base'}) — fichier ${item.file.name}${item.note ? ` — note utilisateur : ${item.note}` : ''}`).join('\n');
  return `BRICKHOUSE — DEMANDE D'ANALYSE EXTERNE\n\nVous recevez un paquet préparé par BrickHouse. Analysez les images comme un ensemble multi-vues d'un même bâtiment. Les libellés de vues donnés par l'utilisateur sont des repères forts, mais vérifiez leur cohérence par les objets répétés, angles, ouvertures, terrasse, escalier, toiture, terrain et bâtiments voisins.\n\nIMPORTANT :\n- ne jamais inventer une ouverture dans une zone cachée ;\n- verrouiller d'abord le nombre d'ouvertures par pan, puis leur identité, leur ordre, leur position, puis leurs dimensions ;\n- exploiter les vues supplémentaires pour lever des occultations ou vérifier la géométrie, pas pour multiplier artificiellement les objets ;\n- pour une terrasse, un escalier ou un palier, segmenter uniquement les primitives réellement soutenues par les photos : une zone cachée reste inconnue et ne doit pas être complétée pour fermer une chaîne de circulation ;\n- dans ArchitecturalScene, chaque Platform et StairRun représentant une observation active du Survey doit réutiliser exactement l'id stable de cette observation ; ne créer aucune primitive extérieure absente du Survey ;\n- une observation Survey plausible ne devient pas une géométrie métrique très confiante : conserver une confiance prudente jusqu'à preuve supplémentaire ;\n- ne jamais inverser gauche/droite ;\n- les éléments d'un bâtiment voisin ne doivent jamais être attribués à la maison cible ;\n- toute mesure utilisateur est prioritaire et doit garder source.kind=user_provided.\n\nPHOTOS FOURNIES :\n${photoLines}\n\nINFORMATIONS GENERALES :\n${general}\n\nLARGEUR AVANT CONNUE : ${Number.isFinite(width) && width > 0 ? `${width} m` : 'inconnue'}\nTAILLE CIBLE DE MAQUETTE : ${Number(studsInput?.value) || 48} tenons de façade\n\nLes fichiers de prompts BrickHouse sont inclus dans le paquet. Exécutez conceptuellement : topologie → ArchitecturalSurvey v0.1 → ArchitecturalScene v0.2.\n\nSORTIE ATTENDUE : créez un fichier téléchargeable nommé brickhouse-external-result.json ayant exactement cette enveloppe :\n{\n  "schema_version": "external-bundle-0.1",\n  "kind": "brickhouse_external_result",\n  "survey": { ... ArchitecturalSurvey v0.1 complet ... },\n  "scene": { ... ArchitecturalScene v0.2 complet reconstruit uniquement depuis ce Survey ... }\n}\n\nNe remplacez pas le fichier par une longue réponse dans le chat si votre interface permet de créer un fichier.\n`;
}

packageButton?.addEventListener('click', async () => {
  const records = selectedPhotoRecords();
  if (!records.length) {
    packageStatus.textContent = 'Ajoutez au moins une photo avant de préparer le paquet.';
    return;
  }
  if (records.length > MAX_TOTAL_PHOTOS) {
    packageStatus.textContent = `Gardez au maximum ${MAX_TOTAL_PHOTOS} photos.`;
    return;
  }
  packageButton.disabled = true;
  packageStatus.textContent = 'Préparation du paquet BrickHouse…';
  try {
    const [topologyPrompt, surveyPrompt, scenePrompt] = await Promise.all([
      fetchText('./brickhouse-topology-prompt.txt'),
      fetchText('./brickhouse-survey-prompt.txt'),
      fetchText('./brickhouse-survey-to-scene-prompt.txt'),
    ]);
    const encoder = new TextEncoder();
    const manifest = {
      schema_version: 'handoff-0.2',
      kind: 'brickhouse_external_ai_handoff',
      created_at: new Date().toISOString(),
      known_front_width_m: Number(knownWidthInput?.value) > 0 ? Number(knownWidthInput.value) : null,
      target_front_width_studs: Number(studsInput?.value) || 48,
      general_notes: notesInput?.value.trim() || '',
      capture_strategy: {
        guided_base_views: records.filter(item => item.role === 'guided_base').length,
        targeted_extra_views: records.filter(item => item.role === 'targeted_extra').length,
        principle: 'few_high_value_views_plus_targeted_extras',
      },
      photos: records.map((item, index) => ({
        photo_index: index + 1,
        slot: item.slot,
        label: item.label,
        capture_role: item.role,
        filename: `photos/${String(index + 1).padStart(2, '0')}-${item.file.name}`,
        media_type: item.file.type,
        user_note: item.note,
      })),
    };
    const entries = [
      { name: '00-LIRE-ET-ANALYSER.txt', bytes: encoder.encode(requestText(records)) },
      { name: 'manifest.json', bytes: encoder.encode(JSON.stringify(manifest, null, 2) + '\n') },
      { name: 'instructions/01-topologie.txt', bytes: encoder.encode(topologyPrompt) },
      { name: 'instructions/02-survey.txt', bytes: encoder.encode(surveyPrompt) },
      { name: 'instructions/03-survey-vers-scene.txt', bytes: encoder.encode(scenePrompt) },
    ];
    for (let index = 0; index < records.length; index += 1) {
      entries.push({
        name: manifest.photos[index].filename,
        bytes: new Uint8Array(await records[index].file.arrayBuffer()),
      });
    }
    const blob = await createZip(entries);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'brickhouse-photos-a-analyser.zip';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    packageStatus.textContent = `${records.length} photo(s) regroupée(s). Envoyez brickhouse-photos-a-analyser.zip à l’IA puis remettez ici son fichier brickhouse-external-result.json.`;
  } catch (error) {
    packageStatus.textContent = `Impossible de préparer le paquet : ${error.message}`;
  } finally {
    packageButton.disabled = false;
  }
});

// Keep the technical input synchronized if the old advanced field is edited directly.
technicalPhotos?.addEventListener('change', () => {
  if (technicalPhotos.files?.length && !selectedPhotoRecords().length) {
    packageStatus.textContent = 'Des photos ont été ajoutées via les options avancées. Pour le paquet IA guidé, placez-les plutôt dans les cases ou dans les vues supplémentaires ci-dessus.';
  }
});
