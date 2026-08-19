const fileInput = document.querySelector('#instruction-file');
const loadSampleButton = document.querySelector('#load-instruction-sample');
const printButton = document.querySelector('#print-instructions');
const downloadBomButton = document.querySelector('#download-bom');
const subtitle = document.querySelector('#instruction-subtitle');
const summary = document.querySelector('#instruction-summary');
const stepsEl = document.querySelector('#steps');
const message = document.querySelector('#instruction-message');

const PLATE_WORLD_HEIGHT = 0.4;
const CATEGORY_COLORS = { brick: '#d8c7a4', roof_tile: '#b9564b', ridge_tile: '#e5a15f' };
const PREVIOUS_TOP = '#d7dce4';
const PREVIOUS_SIDE_A = '#bcc4d0';
const PREVIOUS_SIDE_B = '#aeb8c6';
let currentBundle = null;

function validateBundle(bundle) {
  if (!bundle?.brick_model?.parts || !bundle?.bom?.lines) throw new Error('Export BrickHouse invalide.');
  if (!bundle.assembly_plan?.steps?.length) throw new Error('Cet export ne contient pas encore d’AssemblyPlan.');
  if (bundle.assembly_plan.total_parts !== bundle.brick_model.parts.length) throw new Error('AssemblyPlan incomplet.');
}

function partMap(bundle) { return new Map(bundle.brick_model.parts.map((part) => [part.placement_id, part])); }

function rawDimensions(part) {
  const match = part.part_id.match(/_(\d+)X(\d+)$/);
  if (!match) return { a: 1, b: 1 };
  return { a: Number(match[1]), b: Number(match[2]) };
}

function parseDimensions(part) {
  const { a, b } = rawDimensions(part);
  let width = a;
  let length = b;
  if (part.rotation_quarter_turns % 2 === 1) [width, length] = [length, width];
  const height = part.category === 'brick' ? 1.2 : part.category === 'roof_tile' ? 1.2 : 0.4;
  return { width, length, height };
}

function aggregateStepParts(step, byPlacement) {
  const counts = new Map();
  for (const id of step.placement_ids) {
    const part = byPlacement.get(id);
    if (!part) throw new Error(`Placement inconnu dans la notice : ${id}`);
    const key = `${part.category}|${part.part_id}`;
    const row = counts.get(key) ?? { partId: part.part_id, category: part.category, quantity: 0 };
    row.quantity += 1;
    counts.set(key, row);
  }
  return [...counts.values()].sort((a, b) => a.partId.localeCompare(b.partId));
}

function renderSummary(bundle) {
  const model = bundle.brick_model;
  subtitle.textContent = `Bâtiment ${bundle.building_id}`;
  const items = [['Pièces', bundle.bom.total_parts], ['Types', bundle.bom.unique_part_types], ['Étapes', bundle.assembly_plan.total_steps], ['Taille', `${model.width_studs} × ${model.depth_studs} tenons`]];
  summary.innerHTML = items.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join('');
}

function projectPoint(x, y, z) {
  return { x: (x - y) * 0.88, y: (x + y) * 0.44 - z * 1.12 };
}

function shade(hex, factor) {
  const value = Number.parseInt(hex.slice(1), 16);
  const r = Math.max(0, Math.min(255, Math.round(((value >> 16) & 255) * factor)));
  const g = Math.max(0, Math.min(255, Math.round(((value >> 8) & 255) * factor)));
  const b = Math.max(0, Math.min(255, Math.round((value & 255) * factor)));
  return `rgb(${r}, ${g}, ${b})`;
}

function polygon(ctx, points, fill, stroke = 'rgba(31,41,55,.26)') {
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i += 1) ctx.lineTo(points[i].x, points[i].y);
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 0.7;
  ctx.stroke();
}

function cuboidPolygons(part) {
  const { width, length, height } = parseDimensions(part);
  const x0 = part.x_studs, x1 = x0 + width;
  const y0 = part.y_studs, y1 = y0 + length;
  const z0 = part.z_plates * PLATE_WORLD_HEIGHT, z1 = z0 + height;
  const p = (x, y, z) => projectPoint(x, y, z);
  return {
    top: [p(x0,y0,z1),p(x1,y0,z1),p(x1,y1,z1),p(x0,y1,z1)],
    right: [p(x1,y0,z0),p(x1,y1,z0),p(x1,y1,z1),p(x1,y0,z1)],
    left: [p(x0,y1,z0),p(x1,y1,z0),p(x1,y1,z1),p(x0,y1,z1)],
  };
}

function slopePolygons(part) {
  const { width, length } = parseDimensions(part);
  const z0 = part.z_plates * PLATE_WORLD_HEIGHT;
  const high = z0 + 3 * PLATE_WORLD_HEIGHT;
  const low = z0 + 0.06;
  const x0 = part.x_studs, x1 = x0 + width;
  const y0 = part.y_studs, y1 = y0 + length;
  const p = (x, y, z) => projectPoint(x, y, z);
  const alongX = part.rotation_quarter_turns % 2 === 0;
  const negative = part.roof_side === 'negative';
  let a0, a1, b0, b1;
  if (alongX) {
    const leftZ = negative ? low : high;
    const rightZ = negative ? high : low;
    a0 = {x:x0,y:y0,z:leftZ}; a1 = {x:x0,y:y1,z:leftZ};
    b0 = {x:x1,y:y0,z:rightZ}; b1 = {x:x1,y:y1,z:rightZ};
  } else {
    const frontZ = negative ? low : high;
    const backZ = negative ? high : low;
    a0 = {x:x0,y:y0,z:frontZ}; a1 = {x:x1,y:y0,z:frontZ};
    b0 = {x:x0,y:y1,z:backZ}; b1 = {x:x1,y:y1,z:backZ};
  }
  const base = [p(x0,y0,z0),p(x1,y0,z0),p(x1,y1,z0),p(x0,y1,z0)];
  const top = [p(a0.x,a0.y,a0.z),p(b0.x,b0.y,b0.z),p(b1.x,b1.y,b1.z),p(a1.x,a1.y,a1.z)];
  const sideA = [base[0],base[1],top[1],top[0]];
  const sideB = [base[1],base[2],top[2],top[1]];
  const sideC = [base[2],base[3],top[3],top[2]];
  const sideD = [base[3],base[0],top[0],top[3]];
  return { top, right: sideB, left: sideC, extra: [sideA, sideD] };
}

function partProjectedPolygons(part) {
  if (part.category === 'roof_tile' && part.part_id.startsWith('BRICK_SLOPED_')) return slopePolygons(part);
  return cuboidPolygons(part);
}

function buildStepPreview(bundle, visibleIds, currentIds) {
  const canvas = document.createElement('canvas');
  canvas.className = 'step-preview';
  canvas.width = 960; canvas.height = 560;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#f7f9fc'; ctx.fillRect(0,0,canvas.width,canvas.height);
  const visibleParts = bundle.brick_model.parts.filter((part) => visibleIds.has(part.placement_id));
  if (!visibleParts.length) return canvas;
  const drawings = visibleParts.map((part) => ({ part, polygons: partProjectedPolygons(part), depth: part.x_studs + part.y_studs + part.z_plates * 0.08 })).sort((a,b) => a.depth-b.depth);
  const allPoints = drawings.flatMap((entry) => [...entry.polygons.top,...entry.polygons.right,...entry.polygons.left,...(entry.polygons.extra ?? []).flat()]);
  const minX=Math.min(...allPoints.map(p=>p.x)),maxX=Math.max(...allPoints.map(p=>p.x)),minY=Math.min(...allPoints.map(p=>p.y)),maxY=Math.max(...allPoints.map(p=>p.y));
  const pad=42,scale=Math.min((canvas.width-pad*2)/Math.max(maxX-minX,1),(canvas.height-pad*2)/Math.max(maxY-minY,1));
  const offsetX=(canvas.width-(maxX-minX)*scale)/2-minX*scale,offsetY=(canvas.height-(maxY-minY)*scale)/2-minY*scale;
  ctx.save();ctx.translate(offsetX,offsetY);ctx.scale(scale,scale);
  for (const {part,polygons} of drawings) {
    const current=currentIds.has(part.placement_id),base=current?(CATEGORY_COLORS[part.category]??'#e5a15f'):PREVIOUS_TOP,sideA=current?shade(base,.83):PREVIOUS_SIDE_A,sideB=current?shade(base,.72):PREVIOUS_SIDE_B;
    for (const extra of polygons.extra ?? []) polygon(ctx,extra,sideB);
    polygon(ctx,polygons.left,sideB);polygon(ctx,polygons.right,sideA);polygon(ctx,polygons.top,base);
  }
  ctx.restore();
  ctx.fillStyle='#344054';ctx.font='600 20px system-ui, sans-serif';ctx.fillText('Pièces déjà posées',28,34);ctx.fillStyle=PREVIOUS_TOP;ctx.fillRect(222,19,22,18);ctx.strokeStyle='#98a2b3';ctx.strokeRect(222,19,22,18);ctx.fillStyle='#344054';ctx.fillText('Nouvelles pièces',278,34);ctx.fillStyle='#e5a15f';ctx.fillRect(455,19,22,18);
  return canvas;
}

function renderSteps(bundle) {
  const byPlacement=partMap(bundle);let cumulative=0;const visibleIds=new Set();stepsEl.innerHTML='';
  for (const step of bundle.assembly_plan.steps) {
    const currentIds=new Set(step.placement_ids);for(const id of currentIds)visibleIds.add(id);cumulative+=currentIds.size;
    const rows=aggregateStepParts(step,byPlacement).map(({partId,category,quantity})=>`<div class="part-row"><span class="part-swatch ${category}"></span><span class="part-id">${partId}</span><span class="quantity">× ${quantity}</span></div>`).join('');
    const card=document.createElement('article');card.className='step-card';card.innerHTML=`<div class="step-heading"><div><p class="step-kicker">Ajouter ${step.placement_ids.length} pièce(s)</p><h2>Étape ${step.sequence}</h2></div><span>${step.title}</span></div><div class="visual-slot"></div><div class="step-layout"><div><h3>Pièces à ajouter</h3><div class="part-list">${rows}</div></div><div class="step-note"><strong>${cumulative}</strong><span>/ ${bundle.assembly_plan.total_parts}</span><small>pièces montées</small></div></div>`;
    card.querySelector('.visual-slot').appendChild(buildStepPreview(bundle,new Set(visibleIds),currentIds));stepsEl.appendChild(card);
  }
}

function renderBundle(bundle){validateBundle(bundle);currentBundle=bundle;renderSummary(bundle);renderSteps(bundle);message.textContent='';}
function csvText(bundle){const total=bundle.bom.lines.reduce((sum,line)=>sum+line.quantity,0);if(total!==bundle.bom.total_parts)throw new Error('BOM incohérente.');return `${['part_id,category,quantity',...bundle.bom.lines.map(line=>`${line.part_id},${line.category},${line.quantity}`)].join('\n')}\n`;}
function downloadBom(bundle){const blob=new Blob([csvText(bundle)],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`${bundle.building_id}-bom.csv`;document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);}
async function loadSample(){message.textContent='Chargement…';try{const response=await fetch('./sample-export.json',{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);renderBundle(await response.json());}catch(error){message.textContent=error.message;}}
fileInput.addEventListener('change',async()=>{const file=fileInput.files?.[0];if(!file)return;try{renderBundle(JSON.parse(await file.text()));}catch(error){message.textContent=error.message;}finally{fileInput.value='';}});loadSampleButton.addEventListener('click',loadSample);printButton.addEventListener('click',()=>window.print());downloadBomButton.addEventListener('click',()=>{if(currentBundle)downloadBom(currentBundle);});loadSample();
