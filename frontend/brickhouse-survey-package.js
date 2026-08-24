const button = document.querySelector('#download-ai-package');
const status = document.querySelector('#ai-package-status');
const knownWidth = document.querySelector('#known-width');
const studs = document.querySelector('#studs');
const notes = document.querySelector('#notes');
const extraPhotos = document.querySelector('#guided-extra-photos');

const SLOT_ORDER = ['front', 'right', 'left', 'rear', 'front_left', 'front_right'];
const SLOT_LABELS = {
  front: 'Façade avant', right: 'Côté droit', left: 'Côté gauche', rear: 'Arrière',
  front_left: '3/4 avant gauche', front_right: '3/4 avant droit',
};
const PACKAGE_FILENAME = 'BRICKHOUSE-ANALYSE-COMPLETE.pdf';
const PDF_HANDOFF_VERSION = 'pdf-handoff-0.3';
const MAX_PHOTOS = 12;
const PAGE_W = 1240;
const PAGE_H = 1754;
const MARGIN = 86;

if (status) status.textContent = `Handoff ${PDF_HANDOFF_VERSION} prêt · ${PACKAGE_FILENAME} · sortie Survey uniquement`;

function orientationConfirmed() {
  return Boolean(document.querySelector('#confirm-guided-orientations')?.checked);
}

function photoRecords() {
  const records = [];
  for (const slotName of SLOT_ORDER) {
    const slot = document.querySelector(`.guided-photo-slot[data-slot="${slotName}"]`);
    const input = slot?.querySelector('.guided-photo-input');
    const note = slot?.querySelector('.guided-photo-note')?.value.trim() || '';
    [...(input?.files || [])].forEach((file, index) => records.push({
      file, slot: slotName, label: SLOT_LABELS[slotName] || slotName, note,
      slotViewIndex: index + 1,
      orientationAuthority: orientationConfirmed() ? 'user_confirmed' : 'capture_hint',
    }));
  }
  [...(extraPhotos?.files || [])].forEach((file, index) => records.push({
    file, slot: `extra_${index + 1}`, label: `Vue supplémentaire ${index + 1}`, note: '',
    slotViewIndex: 1, orientationAuthority: 'capture_hint',
  }));
  return records.slice(0, MAX_PHOTOS);
}

async function fetchText(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.text();
}

function commandText(records, topology, survey) {
  const width = Number(knownWidth?.value);
  const targetStuds = Number(studs?.value) || 48;
  const confirmed = orientationConfirmed();
  const photoLines = records.map((record, index) =>
    `${index + 1}. ${record.file.name} — ${record.label}` +
    `${record.slotViewIndex > 1 ? ` (vue ${record.slotViewIndex})` : ''}` +
    `${record.note ? ` — note utilisateur: ${record.note}` : ''}` +
    ` — orientation_authority=${record.orientationAuthority}`
  ).join('\n');
  const orientationRule = confirmed
    ? 'Les orientations Avant / Droite / Gauche / Arrière ont été confirmées par l’utilisateur et sont des contraintes fortes.'
    : 'Les libellés des cases sont des indices de capture seulement. Vérifie-les par recoupement multi-vues.';

  return `BRICKHOUSE — HANDOFF PHOTOS -> SURVEY\nHANDOFF_VERSION=${PDF_HANDOFF_VERSION}\n\nOBJECTIF UNIQUE\nAnalyse les pages photo de CE PDF, exécute la topologie comme raisonnement intermédiaire, puis produis UNIQUEMENT un ArchitecturalSurvey v0.1 complet. NE CONSTRUIS PAS DE SCENE dans ce tour. La Scene sera reconstruite seulement après validation du Survey par Boldungo.\n\nINTERDIT\n- ne demande aucune confirmation ni information supplémentaire ;\n- ne produis ni Scene, ni BuildingModel, ni LEGO ;\n- ne réponds pas par une synthèse ;\n- ne complète jamais une zone cachée par plausibilité ;\n- ne remplace jamais une inconnue par null dans un champ dont le contrat exige une valeur ;\n- ne transforme jamais la maison benchmark en règle générale.\n\n${orientationRule}\n\nPHOTOS, DANS L’ORDRE DU PDF\n${photoLines}\n\nFAITS UTILISATEUR\n- largeur réelle de façade avant: ${Number.isFinite(width) && width > 0 ? `${width} m` : 'inconnue'}\n- largeur cible future de maquette: ${targetStuds} tenons (information de contexte seulement, sans effet sur le Survey)\n- notes: ${notes?.value.trim() || 'aucune'}\n\nSORTIE OBLIGATOIRE\nCrée un fichier téléchargeable nommé exactement brickhouse-survey-result.json. Le fichier doit contenir UNIQUEMENT l’objet ArchitecturalSurvey v0.1 à la racine. Aucun wrapper, aucune clé survey, aucune Scene.\n\nAUDIT DE CONTRAT OBLIGATOIRE AVANT SORTIE\n- schema_version vaut exactement \"0.1\" ;\n- id et name sont présents et non vides ;\n- canonical_frame est présent ;\n- photos est non vide ; chaque photo possède photo_index, facade, description, source et image_left_maps_to_facade_offset ;\n- image_left_maps_to_facade_offset vaut exactement \"low\" ou \"high\", jamais null ;\n- observations et relations sont des tableaux ;\n- toute observation opening représente un seul objet physique et possède attributes.physical_object_count=1 ;\n- attributes.semantic_type, s’il est présent, vaut uniquement window, door, door_or_glazed_door, glazed_door_or_large_glazed_opening ou garage_door ; sinon OMETS semantic_type ; n’écris jamais semantic_type:\"opening\" ;\n- chaque relation contient id, kind, subject_id, object_id, certainty, statement et evidence ;\n- chaque relation référence deux IDs d’observations existantes ;\n- known_measurements transporte la largeur utilisateur seulement au format du contrat ;\n- JSON valide, sans commentaire ni texte avant/après.\n\nLa réponse finale du chat doit seulement annoncer ou joindre brickhouse-survey-result.json.\n\n================ TOPOLOGIE — RAISONNEMENT INTERMÉDIAIRE ================\n${topology}\n\n================ ARCHITECTURAL SURVEY — CONTRAT AUTORITATIF ================\n${survey}\n`;
}

function ascii(text) {
  return text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"').replace(/[–—→]/g, '-').replace(/[^\x09\x0A\x0D\x20-\x7E]/g, '?');
}

function wrapText(ctx, text, maxWidth) {
  const out = [];
  for (const rawLine of ascii(text).split(/\r?\n/)) {
    if (!rawLine) { out.push(''); continue; }
    const words = rawLine.split(/\s+/);
    let line = '';
    for (const word of words) {
      const candidate = line ? `${line} ${word}` : word;
      if (ctx.measureText(candidate).width <= maxWidth) line = candidate;
      else { if (line) out.push(line); line = word; }
    }
    out.push(line);
  }
  return out;
}

function makeTextPages(text) {
  const probe = document.createElement('canvas').getContext('2d');
  probe.font = '24px sans-serif';
  const lines = wrapText(probe, text, PAGE_W - MARGIN * 2);
  const perPage = Math.floor((PAGE_H - MARGIN * 2) / 34);
  const pages = [];
  for (let offset = 0; offset < lines.length; offset += perPage) {
    const canvas = document.createElement('canvas');
    canvas.width = PAGE_W; canvas.height = PAGE_H;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, PAGE_W, PAGE_H);
    ctx.fillStyle = '#111'; ctx.font = '24px sans-serif'; ctx.textBaseline = 'top';
    lines.slice(offset, offset + perPage).forEach((line, index) => ctx.fillText(line, MARGIN, MARGIN + index * 34));
    pages.push(canvas);
  }
  return pages;
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => { URL.revokeObjectURL(url); resolve(image); };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error(`Image illisible: ${file.name}`)); };
    image.src = url;
  });
}

async function makePhotoPage(record, index) {
  const image = await loadImage(record.file);
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W; canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, PAGE_W, PAGE_H);
  ctx.fillStyle = '#111'; ctx.font = 'bold 30px sans-serif';
  ctx.fillText(`PHOTO ${index + 1} — ${ascii(record.label)}`, MARGIN, 54);
  ctx.font = '20px sans-serif';
  ctx.fillText(ascii(record.file.name), MARGIN, 98);
  ctx.fillText(`orientation_authority=${record.orientationAuthority}`, MARGIN, 128);
  if (record.note) ctx.fillText(`note: ${ascii(record.note).slice(0, 100)}`, MARGIN, 158);
  const top = 205, maxW = PAGE_W - MARGIN * 2, maxH = PAGE_H - top - MARGIN;
  const scale = Math.min(maxW / image.naturalWidth, maxH / image.naturalHeight);
  const w = image.naturalWidth * scale, h = image.naturalHeight * scale;
  ctx.drawImage(image, (PAGE_W - w) / 2, top + (maxH - h) / 2, w, h);
  return canvas;
}

function canvasJpegBytes(canvas, quality = 0.9) {
  const binary = atob(canvas.toDataURL('image/jpeg', quality).split(',')[1]);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}
function concat(parts) {
  const total = parts.reduce((sum, part) => sum + part.length, 0), out = new Uint8Array(total);
  let offset = 0; for (const part of parts) { out.set(part, offset); offset += part.length; } return out;
}
function latinBytes(value) {
  const bytes = new Uint8Array(value.length); for (let i = 0; i < value.length; i++) bytes[i] = value.charCodeAt(i) & 0xff; return bytes;
}
function pdfFromCanvases(canvases) {
  const images = canvases.map(canvas => ({ bytes: canvasJpegBytes(canvas), width: canvas.width, height: canvas.height }));
  const objects = []; const addObject = parts => { objects.push(parts); return objects.length; };
  const catalogId = addObject([]), pagesId = addObject([]), pageIds = [];
  for (const image of images) {
    const imageId = addObject([latinBytes(`<< /Type /XObject /Subtype /Image /Width ${image.width} /Height ${image.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${image.bytes.length} >>\nstream\n`), image.bytes, latinBytes('\nendstream')]);
    const content = `q\n${PAGE_W} 0 0 ${PAGE_H} 0 0 cm\n/Im0 Do\nQ\n`;
    const contentId = addObject([latinBytes(`<< /Length ${content.length} >>\nstream\n${content}endstream`)]);
    pageIds.push(addObject([latinBytes(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${PAGE_W} ${PAGE_H}] /Resources << /XObject << /Im0 ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>`)]));
  }
  objects[catalogId - 1] = [latinBytes(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`)];
  objects[pagesId - 1] = [latinBytes(`<< /Type /Pages /Count ${pageIds.length} /Kids [${pageIds.map(id => `${id} 0 R`).join(' ')}] >>`)];
  const chunks = [latinBytes('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n')], offsets = [0]; let length = chunks[0].length;
  objects.forEach((parts, index) => { offsets.push(length); const head = latinBytes(`${index + 1} 0 obj\n`), tail = latinBytes('\nendobj\n'); chunks.push(head, ...parts, tail); length += head.length + parts.reduce((sum, p) => sum + p.length, 0) + tail.length; });
  const xrefOffset = length; let xref = `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let i = 1; i <= objects.length; i++) xref += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`;
  xref += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  chunks.push(latinBytes(xref)); return new Blob([concat(chunks)], { type: 'application/pdf' });
}
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = filename;
  document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

button?.addEventListener('click', async event => {
  event.preventDefault(); event.stopImmediatePropagation();
  const records = photoRecords();
  if (!records.length) { status.textContent = `Handoff ${PDF_HANDOFF_VERSION} · Ajoutez au moins une photo.`; return; }
  button.disabled = true; status.textContent = `Handoff ${PDF_HANDOFF_VERSION} · Création du PDF Survey avec ${records.length} photo(s)…`;
  try {
    const [topology, survey] = await Promise.all([fetchText('./brickhouse-topology-prompt.txt'), fetchText('./brickhouse-survey-prompt.txt')]);
    const pages = makeTextPages(commandText(records, topology, survey));
    for (let index = 0; index < records.length; index++) pages.push(await makePhotoPage(records[index], index));
    downloadBlob(pdfFromCanvases(pages), PACKAGE_FILENAME);
    status.textContent = `Handoff ${PDF_HANDOFF_VERSION} · ${PACKAGE_FILENAME} prêt · l’IA doit rendre brickhouse-survey-result.json.`;
  } catch (error) {
    status.textContent = `Impossible de créer le PDF Survey : ${error.message}`;
  } finally { button.disabled = false; }
}, { capture: true });
