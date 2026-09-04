const INPUT_SELECTOR = '.guided-photo-input, .detail-photo-input';
const MAX_VISIBLE_PREVIEWS = 4;

function slotFor(input) {
  return input.closest('.guided-photo-slot, .detail-photo-slot');
}

function ensurePreviewContainer(slot, input) {
  let container = slot.querySelector(':scope > .selected-photo-previews');
  if (container) return container;
  container = document.createElement('div');
  container.className = 'selected-photo-previews';
  container.setAttribute('aria-live', 'polite');
  const name = slot.querySelector(input.matches('.guided-photo-input') ? '.guided-photo-name' : '.detail-photo-name');
  if (name) name.before(container);
  else input.after(container);
  return container;
}

function installStyles() {
  if (document.querySelector('#selected-photo-preview-styles')) return;
  const style = document.createElement('style');
  style.id = 'selected-photo-preview-styles';
  style.textContent = `
    .selected-photo-previews{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;min-height:0}
    .selected-photo-previews:empty{display:none}
    .selected-photo-preview{display:block;width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:8px;border:1px solid #d0d5dd;background:#fff}
    .selected-photo-previews[data-count="1"]{grid-template-columns:1fr}
    .selected-photo-previews[data-count="1"] .selected-photo-preview{aspect-ratio:16/10}
  `;
  document.head.appendChild(style);
}

function renderPreviews(input) {
  const slot = slotFor(input);
  if (!slot) return;
  const container = ensurePreviewContainer(slot, input);
  container.replaceChildren();
  const files = [...(input.files || [])].slice(0, MAX_VISIBLE_PREVIEWS);
  container.dataset.count = String(files.length);
  const label = slot.dataset.label || slot.dataset.slot || 'Photo';

  files.forEach((file, index) => {
    const image = document.createElement('img');
    image.className = 'selected-photo-preview';
    image.alt = `${label} — photo ${index + 1} sur ${files.length}`;
    const url = URL.createObjectURL(file);
    image.src = url;
    image.addEventListener('load', () => URL.revokeObjectURL(url), { once: true });
    image.addEventListener('error', () => URL.revokeObjectURL(url), { once: true });
    container.appendChild(image);
  });
}

function renderAll() {
  document.querySelectorAll(INPUT_SELECTOR).forEach(renderPreviews);
}

installStyles();
document.addEventListener('change', event => {
  const input = event.target?.closest?.(INPUT_SELECTOR);
  if (input) renderPreviews(input);
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', renderAll, { once: true });
} else {
  renderAll();
}
