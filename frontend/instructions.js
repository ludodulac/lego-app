const fileInput = document.querySelector('#instruction-file');
const loadSampleButton = document.querySelector('#load-instruction-sample');
const printButton = document.querySelector('#print-instructions');
const downloadBomButton = document.querySelector('#download-bom');
const subtitle = document.querySelector('#instruction-subtitle');
const summary = document.querySelector('#instruction-summary');
const stepsEl = document.querySelector('#steps');
const message = document.querySelector('#instruction-message');

let currentBundle = null;

function validateBundle(bundle) {
  if (!bundle?.brick_model?.parts || !bundle?.bom?.lines) throw new Error('Export BrickHouse invalide.');
  if (!bundle.assembly_plan?.steps?.length) throw new Error('Cet export ne contient pas encore d’AssemblyPlan.');
  if (bundle.assembly_plan.total_parts !== bundle.brick_model.parts.length) throw new Error('AssemblyPlan incomplet.');
}

function partMap(bundle) {
  return new Map(bundle.brick_model.parts.map((part) => [part.placement_id, part]));
}

function aggregateStepParts(step, byPlacement) {
  const counts = new Map();
  for (const id of step.placement_ids) {
    const part = byPlacement.get(id);
    if (!part) throw new Error(`Placement inconnu dans la notice : ${id}`);
    counts.set(part.part_id, (counts.get(part.part_id) ?? 0) + 1);
  }
  return [...counts.entries()].sort(([a], [b]) => a.localeCompare(b));
}

function renderSummary(bundle) {
  const model = bundle.brick_model;
  subtitle.textContent = `Bâtiment ${bundle.building_id}`;
  const items = [
    ['Pièces', bundle.bom.total_parts],
    ['Types', bundle.bom.unique_part_types],
    ['Étapes', bundle.assembly_plan.total_steps],
    ['Taille', `${model.width_studs} × ${model.depth_studs} tenons`],
  ];
  summary.innerHTML = items.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join('');
}

function renderSteps(bundle) {
  const byPlacement = partMap(bundle);
  let cumulative = 0;
  stepsEl.innerHTML = '';
  for (const step of bundle.assembly_plan.steps) {
    cumulative += step.placement_ids.length;
    const rows = aggregateStepParts(step, byPlacement)
      .map(([partId, quantity]) => `<div class="part-row"><span class="part-id">${partId}</span><span class="quantity">× ${quantity}</span></div>`)
      .join('');
    const card = document.createElement('article');
    card.className = 'step-card';
    card.innerHTML = `<div class="step-heading"><h2>Étape ${step.sequence}</h2><span>${step.title}</span></div><div class="part-list">${rows}</div><p class="cumulative">${step.placement_ids.length} pièce(s) ajoutée(s) · ${cumulative}/${bundle.assembly_plan.total_parts} au total</p>`;
    stepsEl.appendChild(card);
  }
}

function renderBundle(bundle) {
  validateBundle(bundle);
  currentBundle = bundle;
  renderSummary(bundle);
  renderSteps(bundle);
  message.textContent = '';
}

function csvText(bundle) {
  const total = bundle.bom.lines.reduce((sum, line) => sum + line.quantity, 0);
  if (total !== bundle.bom.total_parts) throw new Error('BOM incohérente.');
  const rows = ['part_id,category,quantity', ...bundle.bom.lines.map((line) => `${line.part_id},${line.category},${line.quantity}`)];
  return `${rows.join('\n')}\n`;
}

function downloadBom(bundle) {
  const blob = new Blob([csvText(bundle)], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${bundle.building_id}-bom.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function loadSample() {
  message.textContent = 'Chargement…';
  try {
    const response = await fetch('./sample-export.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderBundle(await response.json());
  } catch (error) { message.textContent = error.message; }
}

fileInput.addEventListener('change', async () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  try { renderBundle(JSON.parse(await file.text())); }
  catch (error) { message.textContent = error.message; }
  finally { fileInput.value = ''; }
});
loadSampleButton.addEventListener('click', loadSample);
printButton.addEventListener('click', () => window.print());
downloadBomButton.addEventListener('click', () => { if (currentBundle) downloadBom(currentBundle); });
loadSample();
