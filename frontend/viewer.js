import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const PLATE_WORLD_HEIGHT = 1 / 2.5;
const canvas = document.querySelector('#viewer');
const messageEl = document.querySelector('#message');
const summaryEl = document.querySelector('#model-summary');
const fileInput = document.querySelector('#file-input');
const resetButton = document.querySelector('#reset-view');
const sampleButton = document.querySelector('#load-sample');
const downloadBomButton = document.querySelector('#download-bom');
const assemblyCard = document.querySelector('#assembly-card');
const assemblyTitle = document.querySelector('#assembly-title');
const assemblyProgress = document.querySelector('#assembly-progress');
const assemblyRange = document.querySelector('#assembly-range');
const assemblyPrev = document.querySelector('#assembly-prev');
const assemblyNext = document.querySelector('#assembly-next');
const assemblyFull = document.querySelector('#assembly-full');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0e1528);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x25324a, 2.2));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.8);
keyLight.position.set(10, 18, 12);
scene.add(keyLight);
const ground = new THREE.GridHelper(80, 80, 0x506080, 0x26324a);
ground.position.y = -0.01;
scene.add(ground);
const modelGroup = new THREE.Group();
scene.add(modelGroup);

const materials = {
  brick: new THREE.MeshStandardMaterial({ color: 0xd6c5a3, roughness: 0.78, metalness: 0.02 }),
  roof_tile: new THREE.MeshStandardMaterial({ color: 0xb25d52, roughness: 0.72, metalness: 0.02 }),
  ridge_tile: new THREE.MeshStandardMaterial({ color: 0xe8a76b, roughness: 0.68, metalness: 0.02 }),
};

let lastBundle = null;
let meshByPlacementId = new Map();
let currentAssemblyStep = null;

function setMessage(text = '') { messageEl.textContent = text; }
function parseCanonicalDimensions(part) {
  const match = part.part_id.match(/_(\d+)X(\d+)$/);
  if (!match) throw new Error(`Dimensions inconnues pour ${part.part_id}`);
  let width = Number(match[1]); let length = Number(match[2]);
  if (part.rotation_quarter_turns % 2 === 1) [width, length] = [length, width];
  return { width, length, heightPlates: part.category === 'brick' ? 3 : 1 };
}
function validateBundle(bundle) {
  if (!bundle || bundle.schema_version !== '0.1') throw new Error('Export BrickHouse schema_version 0.1 requis.');
  if (!bundle.brick_model || !Array.isArray(bundle.brick_model.parts)) throw new Error('brick_model.parts est manquant.');
  if (!bundle.bom || !Array.isArray(bundle.bom.lines)) throw new Error('bom.lines est manquant.');
  if (bundle.brick_model.building_id !== bundle.building_id || bundle.bom.building_id !== bundle.building_id) throw new Error('Les identifiants building_id sont incohérents.');
  if (bundle.bom.total_parts !== bundle.brick_model.parts.length) throw new Error('Le total de la BOM ne correspond pas au BrickModel.');
  if (bundle.assembly_plan) {
    const steps = bundle.assembly_plan.steps;
    if (!Array.isArray(steps) || steps.length !== bundle.assembly_plan.total_steps) throw new Error('AssemblyPlan invalide.');
    if (bundle.assembly_plan.total_parts !== bundle.brick_model.parts.length) throw new Error('AssemblyPlan incomplet.');
  }
}
function clearModel() { while (modelGroup.children.length) { const child = modelGroup.children.pop(); child.geometry?.dispose(); } meshByPlacementId = new Map(); }
function makePartMesh(part) {
  const { width, length, heightPlates } = parseCanonicalDimensions(part);
  const height = heightPlates * PLATE_WORLD_HEIGHT;
  const geometry = new THREE.BoxGeometry(width * 0.96, height * 0.92, length * 0.96);
  const mesh = new THREE.Mesh(geometry, materials[part.category] ?? materials.brick);
  mesh.position.set(part.x_studs + width / 2, part.z_plates * PLATE_WORLD_HEIGHT + height / 2, part.y_studs + length / 2);
  mesh.userData = part;
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({ color: 0x151922, transparent: true, opacity: 0.45 })));
  return mesh;
}
function updateSummary(bundle) {
  const model = bundle.brick_model;
  const values = [bundle.building_id, String(bundle.bom.total_parts), String(bundle.bom.unique_part_types), `${model.width_studs} × ${model.depth_studs} tenons`];
  [...summaryEl.querySelectorAll('dd')].forEach((node, index) => { node.textContent = values[index] ?? '—'; });
}
function frameModel() {
  const box = new THREE.Box3().setFromObject(modelGroup); if (box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3()); const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z, 1); const distance = maxDim / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) * 1.55;
  controls.target.copy(center); camera.position.set(center.x + distance * 0.9, center.y + distance * 0.65, center.z + distance * 1.05);
  camera.near = Math.max(distance / 100, 0.05); camera.far = distance * 20; camera.updateProjectionMatrix(); controls.update();
}
function configureAssembly(bundle) {
  const plan = bundle.assembly_plan;
  if (!plan || !plan.steps?.length) { assemblyCard.hidden = true; currentAssemblyStep = null; for (const mesh of meshByPlacementId.values()) mesh.visible = true; return; }
  assemblyCard.hidden = false; assemblyRange.min = '0'; assemblyRange.max = String(plan.steps.length - 1); showAssemblyStep(0);
}
function showAssemblyStep(index) {
  const plan = lastBundle?.assembly_plan; if (!plan?.steps?.length) return;
  const clamped = Math.max(0, Math.min(index, plan.steps.length - 1)); currentAssemblyStep = clamped; assemblyRange.value = String(clamped);
  const visibleIds = new Set(); let cumulative = 0;
  for (let i = 0; i <= clamped; i += 1) { for (const id of plan.steps[i].placement_ids) visibleIds.add(id); cumulative += plan.steps[i].placement_ids.length; }
  for (const [id, mesh] of meshByPlacementId) mesh.visible = visibleIds.has(id);
  const step = plan.steps[clamped]; assemblyTitle.textContent = step.title; assemblyProgress.textContent = `Étape ${step.sequence}/${plan.total_steps} · ${cumulative}/${plan.total_parts} pièces`;
  assemblyPrev.disabled = clamped === 0; assemblyNext.disabled = clamped === plan.steps.length - 1;
}
function showFullModel() {
  for (const mesh of meshByPlacementId.values()) mesh.visible = true; currentAssemblyStep = null;
  const plan = lastBundle?.assembly_plan; assemblyTitle.textContent = 'Modèle complet'; assemblyProgress.textContent = plan ? `${plan.total_parts} pièces` : '';
  assemblyPrev.disabled = false; assemblyNext.disabled = false;
}
function downloadBom(bundle) {
  const total = bundle.bom.lines.reduce((sum, line) => sum + line.quantity, 0);
  if (total !== bundle.bom.total_parts) throw new Error('BOM incohérente.');
  const text = ['part_id,category,quantity', ...bundle.bom.lines.map((line) => `${line.part_id},${line.category},${line.quantity}`)].join('\n') + '\n';
  const blob = new Blob([text], { type: 'text/csv;charset=utf-8' }); const url = URL.createObjectURL(blob); const link = document.createElement('a');
  link.href = url; link.download = `${bundle.building_id}-bom.csv`; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
}
function renderBundle(bundle) {
  validateBundle(bundle); clearModel();
  for (const part of bundle.brick_model.parts) { const mesh = makePartMesh(part); modelGroup.add(mesh); meshByPlacementId.set(part.placement_id, mesh); }
  lastBundle = bundle; updateSummary(bundle); configureAssembly(bundle); frameModel(); setMessage('');
}
async function loadSample() {
  setMessage('Chargement de l’exemple…');
  try { const response = await fetch('./sample-export.json', { cache: 'no-store' }); if (!response.ok) throw new Error(`HTTP ${response.status}`); renderBundle(await response.json()); }
  catch (error) { setMessage(`Impossible de charger l’exemple : ${error.message}`); }
}
fileInput.addEventListener('change', async () => { const file = fileInput.files?.[0]; if (!file) return; try { renderBundle(JSON.parse(await file.text())); } catch (error) { setMessage(`JSON invalide : ${error.message}`); } finally { fileInput.value = ''; } });
resetButton.addEventListener('click', () => { if (lastBundle) frameModel(); }); sampleButton.addEventListener('click', loadSample);
downloadBomButton.addEventListener('click', () => { try { if (lastBundle) downloadBom(lastBundle); } catch (error) { setMessage(error.message); } });
assemblyRange.addEventListener('input', () => showAssemblyStep(Number(assemblyRange.value))); assemblyPrev.addEventListener('click', () => showAssemblyStep((currentAssemblyStep ?? 0) - 1)); assemblyNext.addEventListener('click', () => showAssemblyStep((currentAssemblyStep ?? -1) + 1)); assemblyFull.addEventListener('click', showFullModel);
function resizeRenderer() { const width = canvas.clientWidth; const height = canvas.clientHeight; const needResize = canvas.width !== Math.floor(width * renderer.getPixelRatio()) || canvas.height !== Math.floor(height * renderer.getPixelRatio()); if (needResize) { renderer.setSize(width, height, false); camera.aspect = width / Math.max(height, 1); camera.updateProjectionMatrix(); } }
renderer.setAnimationLoop(() => { resizeRenderer(); controls.update(); renderer.render(scene, camera); });
loadSample();
