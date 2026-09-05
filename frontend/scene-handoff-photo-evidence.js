const LEGACY_PHOTO_EVIDENCE_FILENAME = 'BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf';
const LEGACY_SCENE_HANDOFF_FILENAME = 'BRICKHOUSE-SURVEY-TO-SCENE.txt';
const SINGLE_SCENE_HANDOFF_FILENAME = 'BRICKHOUSE-SURVEY-TO-SCENE-pdf-handoff-0.2.pdf';
const SCENE_HANDOFF_VERSION = 'scene-handoff-0.5-single-hybrid-pdf';
const PROMPT_VERSION = '4.3';

const SLOT_ORDER = ['front', 'right', 'left', 'rear'];
const SLOT_LABELS = {
  front: 'Façade avant',
  right: 'Côté droit',
  left: 'Côté gauche',
  rear: 'Arrière',
};
const DETAIL_ORDER = ['detail_1', 'detail_2', 'detail_3', 'detail_4', 'detail_5', 'detail_6'];
const MAX_PHOTOS_PER_GROUP = 4;
const MAX_PHOTOS = 40;
const PAGE_W = 960;
const PAGE_H = 1358;
const MARGIN = 64;
const TEXT_SIZE = 19;
const TEXT_LINE_HEIGHT = 27;

function pendingValidatedSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return payload?.valid_for_scene_fusion ? payload.survey : null;
  } catch {
    return null;
  }
}

function orientationConfirmed() {
  return Boolean(document.querySelector('#confirm-guided-orientations')?.checked);
}

function photoRecords() {
  const records = [];
  for (const slotName of SLOT_ORDER) {
    const slot = document.querySelector(`.guided-photo-slot[data-slot="${slotName}"]`);
    const input = slot?.querySelector('.guided-photo-input');
    const note = slot?.querySelector('.guided-photo-note')?.value.trim() || '';
    [...(input?.files || [])].slice(0, MAX_PHOTOS_PER_GROUP).forEach((file, index) => records.push({
      file,
      slot: slotName,
      label: SLOT_LABELS[slotName] || slotName,
      note,
      slotViewIndex: index + 1,
      captureRole: 'facade_view',
      orientationAuthority: orientationConfirmed() ? 'user_confirmed' : 'capture_hint',
    }));
  }
  for (const slotName of DETAIL_ORDER) {
    const slot = document.querySelector(`.detail-photo-slot[data-slot="${slotName}"]`);
    const input = slot?.querySelector('.detail-photo-input');
    const note = slot?.querySelector('.detail-photo-note')?.value.trim() || '';
    [...(input?.files || [])].slice(0, MAX_PHOTOS_PER_GROUP).forEach((file, index) => records.push({
      file,
      slot: slotName,
      label: slot?.dataset.label || slotName,
      note,
      slotViewIndex: index + 1,
      captureRole: 'targeted_detail',
      orientationAuthority: 'none',
    }));
  }
  if (records.length > MAX_PHOTOS) throw new Error(`Maximum ${MAX_PHOTOS} photos pour ce handoff.`);
  return records;
}

function alignPromptWithSinglePdfContract(prompt) {
  const authority = `AUTORITÉ DES ENTRÉES — SURVEY + PREUVES PHOTO\nCette étape reçoit de préférence UN SEUL PDF hybride : ${SINGLE_SCENE_HANDOFF_FILENAME}. Ses premières pages contiennent les instructions et le JSON ArchitecturalSurvey v0.1 validé en texte PDF extractible ; ses dernières pages contiennent les photos originales comme preuves visuelles. Le Survey reste autoritatif pour l’inventaire, les IDs, les certitudes, les attributs et les relations. Les pages photo servent uniquement à borner la géométrie métrique de Scene : profondeur, hauteur, positions, dimensions secondaires, pente et raccords physiques.\nNe recommence PAS le Survey et ne modifie jamais un fait Survey certain à partir des pixels. Si les pages photo de ce même PDF ne sont pas réellement accessibles, ne fabrique aucune métrique manquante : indique que la preuve photo obligatoire manque.\nLe chemin historique à deux fichiers (${LEGACY_SCENE_HANDOFF_FILENAME} + ${LEGACY_PHOTO_EVIDENCE_FILENAME}) reste compatible, mais lorsqu’un PDF hybride unique est fourni, il satisfait à lui seul les deux rôles d’entrée.`;
  const aligned = prompt.replace(
    /AUTORITÉ DES ENTRÉES — SURVEY \+ PREUVES PHOTO[\s\S]*?\n\nPORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE/,
    `${authority}\n\nPORTÉE GÉNÉRIQUE — RÈGLE ABSOLUE`,
  );
  if (!aligned.includes(SINGLE_SCENE_HANDOFF_FILENAME)) {
    throw new Error('contrat Survey → Scene non aligné avec le PDF hybride unique');
  }
  return aligned;
}

function sceneHandoffText(survey, prompt, records) {
  const photoLines = records.map((record, index) =>
    `${index + 1}. ${record.file.name} — ${record.label}` +
    `${record.slotViewIndex > 1 ? ` (vue ${record.slotViewIndex})` : ''}` +
    `${record.note ? ` — note utilisateur: ${record.note}` : ''}` +
    ` — capture_role=${record.captureRole} — orientation_authority=${record.orientationAuthority}`
  ).join('\n');
  return `BRICKHOUSE — HANDOFF SURVEY → SCENE — PDF HYBRIDE UNIQUE\nHANDOFF_VERSION=${SCENE_HANDOFF_VERSION}\nPROMPT_VERSION=${PROMPT_VERSION}\n\nENTRÉE UNIQUE\nCe PDF est l’unique fichier requis pour cette étape. Lis d’abord toutes les pages de texte. Les pages photo sont volontairement placées À LA FIN du document : elles servent uniquement comme preuves visuelles complémentaires pour la métrique de Scene. Ne demande aucun autre fichier si ces pages sont accessibles.\n\nRÈGLE DE PRIORITÉ\nLe JSON ArchitecturalSurvey v0.1 inclus ci-dessous est déjà validé par BrickHouse. Il est la source de vérité pour l’inventaire, les IDs, les certitudes, les attributs et les relations. Les photos ne peuvent ni refaire le Survey, ni renommer, déplacer ou supprimer un fait Survey certain. Elles servent seulement à borner profondeur, hauteur, positions, dimensions secondaires, pente, terrain et raccords physiques.\n\nINTERDICTION DE PROJECTION SANS IMAGES\nNe tente pas de reconstruire la Scene depuis le Survey textuel seul. Pour toute métrique non user_provided, recoupe le Survey avec les pages photo placées à la fin de CE PDF. Si ces pages ne sont pas réellement accessibles, indique que la preuve photo requise manque au lieu d’inventer une Scene faussement complète.\n\nPHOTOS À LA FIN DU PDF — ORDRE DE PREUVE\n${photoLines || 'Aucune photo intégrée : utiliser le fallback historique à deux fichiers.'}\n\nCONTRAT DE SÉRIALISATION — OBLIGATOIRE\n- sortie : un fichier nommé exactement brickhouse-scene-result.json ;\n- racine : ArchitecturalScene v0.2, schema_version=\"0.2\", sans wrapper ;\n- préserve exactement les IDs Survey des openings/platforms/stairs/volumes rendus ;\n- préserve les relations certaines ;\n- n’invente aucune géométrie cachée ;\n- geometry_status=\"resolved\" uniquement si le contact numérique final respecte la tolérance backend ;\n- conserve null/unresolved lorsque les images ne permettent réellement pas de borner une métrique ;\n- effectue l’audit final du prompt avant de créer le fichier.\n\nLa réponse finale du chat doit seulement annoncer ou joindre brickhouse-scene-result.json.\n\n================ PROMPT SURVEY → SCENE ================\n${prompt}\n\n================ ARCHITECTURAL SURVEY VALIDÉ ================\n${JSON.stringify(survey, null, 2)}\n\n================ FIN DU TEXTE — LES PAGES SUIVANTES SONT LES PHOTOS ================\n`;
}

function ascii(text) {
  return String(text).normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[–—→]/g, '-')
    .replace(/[^\x09\x0A\x0D\x20-\x7E]/g, '?');
}

function wrapText(ctx, text, maxWidth) {
  const out = [];
  for (const rawLine of ascii(text).split(/\r?\n/)) {
    if (!rawLine) {
      out.push('');
      continue;
    }
    const words = rawLine.split(/\s+/);
    let line = '';
    for (const word of words) {
      const candidate = line ? `${line} ${word}` : word;
      if (ctx.measureText(candidate).width <= maxWidth) {
        line = candidate;
      } else {
        if (line) out.push(line);
        line = word;
      }
    }
    out.push(line);
  }
  return out;
}

function makeTextPages(text) {
  const probe = document.createElement('canvas').getContext('2d');
  if (!probe) throw new Error('Canvas de mesure indisponible.');
  probe.font = `${TEXT_SIZE}px sans-serif`;
  const lines = wrapText(probe, text, PAGE_W - MARGIN * 2);
  const perPage = Math.floor((PAGE_H - MARGIN * 2) / TEXT_LINE_HEIGHT);
  const pages = [];
  let pageNumber = 1;
  for (let offset = 0; offset < lines.length; offset += perPage) {
    pages.push({ kind: 'text', lines: lines.slice(offset, offset + perPage), label: `page texte ${pageNumber}` });
    pageNumber += 1;
  }
  return pages;
}

function newPageCanvas() {
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W;
  canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d', { alpha: false });
  if (!ctx) throw new Error('Canvas 2D indisponible sur cet appareil.');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, PAGE_W, PAGE_H);
  return { canvas, ctx };
}

function assertCanvasHealthy(canvas, label) {
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error(`${label}: canvas inaccessible.`);
  const points = [[4, 4], [PAGE_W - 5, 4], [4, PAGE_H - 5], [PAGE_W - 5, PAGE_H - 5]];
  for (const [x, y] of points) {
    const pixel = ctx.getImageData(x, y, 1, 1).data;
    if (pixel[3] < 240 || pixel[0] < 220 || pixel[1] < 220 || pixel[2] < 220) {
      throw new Error(`${label}: page graphique invalide détectée avant export.`);
    }
  }
}

function canvasJpegBytes(canvas, label, quality = 0.9) {
  assertCanvasHealthy(canvas, label);
  const dataUrl = canvas.toDataURL('image/jpeg', quality);
  if (!dataUrl.startsWith('data:image/jpeg;base64,') || dataUrl.length < 2000) throw new Error(`${label}: encodage JPEG invalide.`);
  const binary = atob(dataUrl.split(',')[1]);
  if (binary.length < 1000) throw new Error(`${label}: page JPEG anormalement vide.`);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function releaseCanvas(canvas) {
  canvas.width = 1;
  canvas.height = 1;
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
  if (!image.naturalWidth || !image.naturalHeight) throw new Error(`Photo ${index + 1}: dimensions invalides.`);
  const { canvas, ctx } = newPageCanvas();
  try {
    ctx.fillStyle = '#111';
    ctx.font = 'bold 23px sans-serif';
    ctx.fillText(`PHOTO ${index + 1} — ${ascii(record.label)}`, MARGIN, 42);
    ctx.font = '16px sans-serif';
    ctx.fillText(ascii(record.file.name), MARGIN, 76);
    ctx.fillText(`capture_role=${record.captureRole} · orientation_authority=${record.orientationAuthority}`, MARGIN, 102);
    if (record.note) ctx.fillText(`note: ${ascii(record.note).slice(0, 100)}`, MARGIN, 128);
    const top = 164;
    const maxW = PAGE_W - MARGIN * 2;
    const maxH = PAGE_H - top - MARGIN;
    const scale = Math.min(maxW / image.naturalWidth, maxH / image.naturalHeight);
    const w = Math.max(1, image.naturalWidth * scale);
    const h = Math.max(1, image.naturalHeight * scale);
    ctx.drawImage(image, (PAGE_W - w) / 2, top + (maxH - h) / 2, w, h);
    const bytes = canvasJpegBytes(canvas, `photo ${index + 1}`);
    return { kind: 'image', bytes, width: PAGE_W, height: PAGE_H, label: `photo ${index + 1}` };
  } finally {
    image.src = '';
    releaseCanvas(canvas);
  }
}

function concat(parts) {
  const total = parts.reduce((sum, part) => sum + part.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const part of parts) { out.set(part, offset); offset += part.length; }
  return out;
}

function latinBytes(value) {
  const bytes = new Uint8Array(value.length);
  for (let i = 0; i < value.length; i += 1) bytes[i] = value.charCodeAt(i) & 0xff;
  return bytes;
}

function pdfString(value) {
  return ascii(value).replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

function textContent(lines) {
  const startY = PAGE_H - MARGIN - TEXT_SIZE;
  const body = lines.map((line, index) => `${index === 0 ? '' : `0 -${TEXT_LINE_HEIGHT} Td\n`}(${pdfString(line)}) Tj\n`).join('');
  return `BT\n/F1 ${TEXT_SIZE} Tf\n${MARGIN} ${startY} Td\n${body}ET\n`;
}

function pdfFromPages(pages) {
  if (!pages.length) throw new Error('Aucune page à exporter.');
  const objects = [];
  const addObject = parts => { objects.push(parts); return objects.length; };
  const catalogId = addObject([]);
  const pagesId = addObject([]);
  const fontId = addObject([latinBytes('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')]);
  const pageIds = [];

  for (const page of pages) {
    if (page.kind === 'text') {
      const content = textContent(page.lines || []);
      const contentId = addObject([latinBytes(`<< /Length ${content.length} >>\nstream\n${content}endstream`)]);
      pageIds.push(addObject([latinBytes(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${PAGE_W} ${PAGE_H}] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`)]));
      continue;
    }
    if (!(page.bytes instanceof Uint8Array) || page.bytes.length < 1000) throw new Error(`${page.label || 'page'}: données JPEG absentes.`);
    const imageId = addObject([
      latinBytes(`<< /Type /XObject /Subtype /Image /Width ${page.width} /Height ${page.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${page.bytes.length} >>\nstream\n`),
      page.bytes,
      latinBytes('\nendstream'),
    ]);
    const content = `q\n${PAGE_W} 0 0 ${PAGE_H} 0 0 cm\n/Im0 Do\nQ\n`;
    const contentId = addObject([latinBytes(`<< /Length ${content.length} >>\nstream\n${content}endstream`)]);
    pageIds.push(addObject([latinBytes(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${PAGE_W} ${PAGE_H}] /Resources << /XObject << /Im0 ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>`)]));
  }

  objects[catalogId - 1] = [latinBytes(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`)];
  objects[pagesId - 1] = [latinBytes(`<< /Type /Pages /Count ${pageIds.length} /Kids [${pageIds.map(id => `${id} 0 R`).join(' ')}] >>`)];
  const chunks = [latinBytes('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n')];
  const offsets = [0];
  let length = chunks[0].length;
  objects.forEach((parts, index) => {
    offsets.push(length);
    const head = latinBytes(`${index + 1} 0 obj\n`);
    const tail = latinBytes('\nendobj\n');
    chunks.push(head, ...parts, tail);
    length += head.length + parts.reduce((sum, part) => sum + part.length, 0) + tail.length;
  });
  const xrefOffset = length;
  let xref = `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let i = 1; i <= objects.length; i += 1) xref += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`;
  xref += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  chunks.push(latinBytes(xref));
  return new Blob([concat(chunks)], { type: 'application/pdf' });
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

function downloadText(filename, content) {
  downloadBlob(new Blob([content], { type: 'text/plain;charset=utf-8' }), filename);
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

function unwrapPositiveScalarPropertyValue(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
  if (!Object.prototype.hasOwnProperty.call(value, 'value')) return value;
  const numeric = Number(value.value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : value;
}

function normalizeExternalScene(value) {
  if (!value || typeof value !== 'object' || value.schema_version !== '0.2') return value;
  const clone = JSON.parse(JSON.stringify(value));
  const visit = node => {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) { node.forEach(visit); return; }
    if (Array.isArray(node.evidence)) node.evidence = normalizeEvidenceList(node.evidence);
    Object.values(node).forEach(visit);
  };
  visit(clone);
  if (typeof clone.id !== 'string' || !clone.id.trim()) clone.id = 'brickhouse-scene';
  if (typeof clone.name !== 'string' || !clone.name.trim()) clone.name = 'BrickHouse architectural scene';
  for (const volume of clone.volumes ?? []) {
    if (volume?.floors && typeof volume.floors === 'object') {
      const numeric = Number(volume.floors.value);
      if (Number.isInteger(numeric) && numeric >= 1 && numeric <= 10) volume.floors = numeric;
    }
  }
  for (const platform of clone.platforms ?? []) {
    platform.width = unwrapPositiveScalarPropertyValue(platform.width);
    platform.depth = unwrapPositiveScalarPropertyValue(platform.depth);
    platform.thickness = unwrapPositiveScalarPropertyValue(platform.thickness);
    if (platform?.thickness == null && Number(platform?.height) > 0) {
      platform.thickness = Number(platform.height);
      delete platform.height;
    }
  }
  for (const stair of clone.stairs ?? []) stair.width = unwrapPositiveScalarPropertyValue(stair.width);
  if (clone.terrain && !Array.isArray(clone.terrain.profiles) && Array.isArray(clone.terrain.facade_grade_profiles)) {
    clone.terrain.profiles = clone.terrain.facade_grade_profiles;
    delete clone.terrain.facade_grade_profiles;
    delete clone.terrain.appearance;
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
  if (!button || button.dataset.singleHybridSceneHandoff === '1') return;
  button.dataset.singleHybridSceneHandoff = '1';
  button.textContent = 'Créer le PDF unique Survey → Scene';
  const existing = document.querySelector('.scene-photo-evidence-note');
  if (existing) existing.remove();
  const helper = document.createElement('p');
  helper.className = 'microcopy scene-photo-evidence-note';
  helper.innerHTML = `Un seul fichier sera généré : <strong>${SINGLE_SCENE_HANDOFF_FILENAME}</strong>. Les instructions et le Survey sont en texte extractible au début ; les photos sont placées à la fin.`;
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
  try {
    const records = photoRecords();
    if (status) status.textContent = records.length
      ? `Préparation du PDF Survey → Scene unique avec ${records.length} photo(s)…`
      : 'Photos non disponibles dans cette session : préparation du fallback historique Survey → Scene…';

    const response = await fetch('./brickhouse-survey-to-scene-prompt.txt', { cache: 'no-store' });
    if (!response.ok) throw new Error(`prompt Survey → Scene : HTTP ${response.status}`);
    const rawPrompt = await response.text();
    if (!rawPrompt.startsWith(`BRICKHOUSE — PROMPT DE RECONSTRUCTION SURVEY → SCENE v${PROMPT_VERSION}`)) {
      throw new Error(`le prompt Survey → Scene actif n’est pas la version v${PROMPT_VERSION} attendue`);
    }
    const prompt = alignPromptWithSinglePdfContract(rawPrompt);
    const handoff = sceneHandoffText(survey, prompt, records);

    if (!records.length) {
      downloadText(LEGACY_SCENE_HANDOFF_FILENAME, handoff);
      if (status) status.textContent = `${LEGACY_SCENE_HANDOFF_FILENAME} prêt en fallback. Les photos n’étaient plus chargées : envoyez aussi ${LEGACY_PHOTO_EVIDENCE_FILENAME}.`;
      return;
    }

    const pages = makeTextPages(handoff);
    const textPageCount = pages.length;
    for (let index = 0; index < records.length; index += 1) {
      if (status) status.textContent = `PDF Survey → Scene · encodage photo ${index + 1}/${records.length}…`;
      pages.push(await makePhotoPage(records[index], index));
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    const pdf = pdfFromPages(pages);
    if (pdf.size < 5000) throw new Error('PDF final anormalement petit.');
    downloadBlob(pdf, SINGLE_SCENE_HANDOFF_FILENAME);
    if (status) status.textContent = `${SINGLE_SCENE_HANDOFF_FILENAME} prêt · ${textPageCount} page(s) de texte extractible puis ${records.length} photo(s). Envoyez uniquement ce PDF à l’IA.`;
  } catch (error) {
    if (status) status.textContent = `Impossible de préparer le fichier Survey → Scene : ${error.message}`;
  } finally {
    button.disabled = false;
  }
}, true);
