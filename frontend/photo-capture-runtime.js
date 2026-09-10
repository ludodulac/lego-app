// Lightweight capture-only runtime for the normal photo cockpit.
// Historical one-turn prompt generation remains in photo-simple.js, but is no
// longer loaded by photo.html. This module owns only file selection metadata.

const packageStatus = document.querySelector('#ai-package-status');
const technicalPhotos = document.querySelector('#photos');
const baseSlots = [...document.querySelectorAll('.guided-photo-slot')];
const detailSlots = [...document.querySelectorAll('.detail-photo-slot')];
const MAX_PHOTOS_PER_GROUP = 4;

function ensureOrientationControl() {
  let control = document.querySelector('#orientation-confirmation-field');
  if (control) return control;
  const grid = document.querySelector('#guided-photo-grid');
  if (!grid) return null;
  control = document.createElement('div');
  control.id = 'orientation-confirmation-field';
  control.className = 'field orientation-confirmation-field';
  control.innerHTML = `
    <label class="orientation-confirmation-label">
      <input id="confirm-guided-orientations" type="checkbox" />
      <span><strong>Je confirme les quatre orientations principales</strong><br><small>Cochez seulement si Avant / Droite / Gauche / Arrière ont été classés volontairement. Les groupes de détails n’acquièrent jamais d’orientation implicite.</small></span>
    </label>`;
  grid.insertAdjacentElement('afterend', control);
  return control;
}

function filesForSlot(slot, inputSelector) {
  return [...(slot.querySelector(inputSelector)?.files ?? [])].slice(0, MAX_PHOTOS_PER_GROUP);
}

function selectedFiles() {
  return [
    ...baseSlots.flatMap(slot => filesForSlot(slot, '.guided-photo-input')),
    ...detailSlots.flatMap(slot => filesForSlot(slot, '.detail-photo-input')),
  ];
}

function syncTechnicalPhotoInput() {
  if (!technicalPhotos || typeof DataTransfer === 'undefined') return;
  const transfer = new DataTransfer();
  for (const file of selectedFiles()) transfer.items.add(file);
  technicalPhotos.files = transfer.files;
  technicalPhotos.dispatchEvent(new Event('change', { bubbles: true }));
}

function updateSlot(slot, inputSelector, nameSelector) {
  const input = slot.querySelector(inputSelector);
  const name = slot.querySelector(nameSelector);
  const count = input?.files?.length ?? 0;
  const used = Math.min(count, MAX_PHOTOS_PER_GROUP);
  slot.classList.toggle('has-photo', used > 0);
  if (count > MAX_PHOTOS_PER_GROUP && packageStatus) {
    packageStatus.textContent = `Maximum ${MAX_PHOTOS_PER_GROUP} photos par groupe. Les suivantes ne seront pas incluses.`;
  }
  if (!name) return;
  if (!used) name.textContent = 'Aucune photo';
  else if (used === 1) name.textContent = input.files[0].name;
  else name.textContent = `${used} photos sélectionnées`;
}

function bindSlot(slot, inputSelector, nameSelector) {
  const input = slot.querySelector(inputSelector);
  input?.addEventListener('change', () => {
    updateSlot(slot, inputSelector, nameSelector);
    syncTechnicalPhotoInput();
  });
  updateSlot(slot, inputSelector, nameSelector);
}

ensureOrientationControl();
baseSlots.forEach(slot => bindSlot(slot, '.guided-photo-input', '.guided-photo-name'));
detailSlots.forEach(slot => bindSlot(slot, '.detail-photo-input', '.detail-photo-name'));
syncTechnicalPhotoInput();
