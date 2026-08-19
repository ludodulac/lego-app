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
scene.background = new THREE.Color(0x101827);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;

scene.add(new THREE.HemisphereLight(0xdcecff, 0x20283a, 2.35));
const keyLight = new THREE.DirectionalLight(0xfff4df, 3.1);
keyLight.position.set(18, 28, 16);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.left = -55;
keyLight.shadow.camera.right = 55;
keyLight.shadow.camera.top = 55;
keyLight.shadow.camera.bottom = -55;
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0x9ec5ff, 0.75);
fillLight.position.set(-14, 10, -18);
scene.add(fillLight);
const ground = new THREE.GridHelper(80, 80, 0x53627c, 0x27344b);
ground.position.y = -0.01;
scene.add(ground);
const modelGroup = new THREE.Group();
scene.add(modelGroup);

const palette = { brick: 0xd8c7a4, roof_tile: 0xb9564b, ridge_tile: 0xe5a15f };
const materials = Object.fromEntries(Object.entries(palette).map(([key, color]) => [key, new THREE.MeshStandardMaterial({ color, roughness: 0.48, metalness: 0.01 })]));
const fadedMaterials = Object.fromEntries(Object.entries(palette).map(([key, color]) => [key, new THREE.MeshStandardMaterial({ color, roughness: 0.62, transparent: true, opacity: 0.32, depthWrite: false })]));
const highlightMaterials = Object.fromEntries(Object.entries(palette).map(([key, color]) => [key, new THREE.MeshStandardMaterial({ color, roughness: 0.34, emissive: color, emissiveIntensity: 0.18 })]));
const edgeMaterial = new THREE.LineBasicMaterial({ color: 0x171b24, transparent: true, opacity: 0.34 });
const studGeometry = new THREE.CylinderGeometry(0.30, 0.30, 0.15, 14);
const studDetailEnabled = !window.matchMedia('(max-width: 760px)').matches;

let lastBundle = null;
let meshByPlacementId = new Map();
let roofRiseByPlacementId = new Map();
let currentAssemblyStep = null;

function setMessage(text = '') { messageEl.textContent = text; }

function parseCanonicalDimensions(part) {
  const match = part.part_id.match(/_(\d+)X(\d+)$/);
  if (!match) throw new Error(`Dimensions inconnues pour ${part.part_id}`);
  let width = Number(match[1]);
  let length = Number(match[2]);
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

function buildRoofRiseMap(parts) {
  const result = new Map();
  const ridgeZ = Math.min(...parts.filter((part) => part.category === 'ridge_tile').map((part) => part.z_plates), Infinity);
  for (const side of ['negative', 'positive']) {
    const sideParts = parts.filter((part) => part.category === 'roof_tile' && part.roof_side === side);
    if (!sideParts.length) continue;
    const courseMap = new Map();
    for (const part of sideParts) {
      const axis = part.rotation_quarter_turns % 2 === 0 ? part.x_studs : part.y_studs;
      const course = courseMap.get(axis) ?? { axis, z: part.z_plates, parts: [] };
      course.z = Math.min(course.z, part.z_plates);
      course.parts.push(part);
      courseMap.set(axis, course);
    }
    const courses = [...courseMap.values()].sort((a, b) => side === 'negative' ? a.axis - b.axis : b.axis - a.axis);
    let previousRise = 1;
    for (let i = 0; i < courses.length; i += 1) {
      const current = courses[i];
      const inward = courses[i + 1];
      let rise = inward ? inward.z - current.z : (Number.isFinite(ridgeZ) ? ridgeZ - current.z : previousRise);
      if (rise <= 0) rise = previousRise;
      rise = Math.max(1, Math.min(rise, 6));
      previousRise = rise;
      for (const part of current.parts) result.set(part.placement_id, rise);
    }
  }
  return result;
}

function clearModel() {
  while (modelGroup.children.length) modelGroup.remove(modelGroup.children[0]);
  meshByPlacementId = new Map();
}

function materialFor(part, state = 'normal') {
  const key = palette[part.category] ? part.category : 'brick';
  return state === 'current' ? highlightMaterials[key] : state === 'previous' ? fadedMaterials[key] : materials[key];
}

function setPartState(group, state) {
  group.visible = state !== 'hidden';
  if (!group.visible) return;
  group.userData.state = state;
  const material = materialFor(group.userData.part, state);
  group.traverse((child) => { if (child.isMesh) child.material = material; });
}

function makeRoofMesh(part, width, length) {
  const risePlates = roofRiseByPlacementId.get(part.placement_id) ?? 1;
  const riseWorld = risePlates * PLATE_WORLD_HEIGHT;
  const thickness = 0.22;
  const slopeAlongX = part.rotation_quarter_turns % 2 === 0;
  const run = slopeAlongX ? width : length;
  const slopedRun = Math.sqrt(run * run + riseWorld * riseWorld);
  const geometry = slopeAlongX
    ? new THREE.BoxGeometry(slopedRun * 1.03, thickness, length * 0.97)
    : new THREE.BoxGeometry(width * 0.97, thickness, slopedRun * 1.03);
  const body = new THREE.Mesh(geometry, materialFor(part));
  body.castShadow = true;
  body.receiveShadow = true;
  body.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry), edgeMaterial));

  const direction = part.roof_side === 'positive' ? -1 : 1;
  const angle = Math.atan2(riseWorld, run) * direction;
  if (slopeAlongX) body.rotation.z = angle;
  else body.rotation.x = -angle;

  const group = new THREE.Group();
  group.userData = { part, state: 'normal' };
  group.add(body);
  group.position.set(
    part.x_studs + width / 2,
    part.z_plates * PLATE_WORLD_HEIGHT + riseWorld / 2 + thickness / 2,
    part.y_studs + length / 2,
  );
  return group;
}

function makePartMesh(part) {
  const { width, length, heightPlates } = parseCanonicalDimensions(part);
  if (part.category === 'roof_tile') return makeRoofMesh(part, width, length);

  const height = heightPlates * PLATE_WORLD_HEIGHT;
  const group = new THREE.Group();
  group.userData = { part, state: 'normal' };
  const geometry = new THREE.BoxGeometry(width * 0.96, height * 0.92, length * 0.96);
  const body = new THREE.Mesh(geometry, materialFor(part));
  body.castShadow = true;
  body.receiveShadow = true;
  body.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry), edgeMaterial));
  group.add(body);

  const addStuds = part.category === 'brick' && (studDetailEnabled || width * length <= 4);
  if (addStuds) {
    for (let x = 0; x < width; x += 1) for (let z = 0; z < length; z += 1) {
      const stud = new THREE.Mesh(studGeometry, materialFor(part));
      stud.position.set(x - (width - 1) / 2, height * 0.46 + 0.07, z - (length - 1) / 2);
      stud.castShadow = true;
      group.add(stud);
    }
  }
  group.position.set(part.x_studs + width / 2, part.z_plates * PLATE_WORLD_HEIGHT + height / 2, part.y_studs + length / 2);
  return group;
}

function updateSummary(bundle) {
  const model = bundle.brick_model;
  const values = [bundle.building_id, String(bundle.bom.total_parts), String(bundle.bom.unique_part_types), `${model.width_studs} × ${model.depth_studs} tenons`];
  [...summaryEl.querySelectorAll('dd')].forEach((node, index) => { node.textContent = values[index] ?? '—'; });
}

function frameModel() {
  const box = new THREE.Box3().setFromObject(modelGroup);
  if (box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z, 1);
  const distance = maxDim / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) * 1.55;
  controls.target.copy(center);
  camera.position.set(center.x + distance * 0.9, center.y + distance * 0.65, center.z + distance * 1.05);
  camera.near = Math.max(distance / 100, 0.05);
  camera.far = distance * 20;
  camera.updateProjectionMatrix();
  controls.update();
}

function configureAssembly(bundle) {
  const plan = bundle.assembly_plan;
  if (!plan || !plan.steps?.length) {
    assemblyCard.hidden = true;
    currentAssemblyStep = null;
    for (const mesh of meshByPlacementId.values()) setPartState(mesh, 'normal');
    return;
  }
  assemblyCard.hidden = false;
  assemblyRange.min = '0';
  assemblyRange.max = String(plan.steps.length - 1);
  showAssemblyStep(0);
}

function showAssemblyStep(index) {
  const plan = lastBundle?.assembly_plan;
  if (!plan?.steps?.length) return;
  const clamped = Math.max(0, Math.min(index, plan.steps.length - 1));
  currentAssemblyStep = clamped;
  assemblyRange.value = String(clamped);
  const previousIds = new Set();
  let cumulative = 0;
  for (let i = 0; i < clamped; i += 1) {
    for (const id of plan.steps[i].placement_ids) previousIds.add(id);
    cumulative += plan.steps[i].placement_ids.length;
  }
  const step = plan.steps[clamped];
  const currentIds = new Set(step.placement_ids);
  cumulative += currentIds.size;
  for (const [id, mesh] of meshByPlacementId) setPartState(mesh, currentIds.has(id) ? 'current' : previousIds.has(id) ? 'previous' : 'hidden');
  assemblyTitle.textContent = step.title;
  assemblyProgress.textContent = `Étape ${step.sequence}/${plan.total_steps} · +${step.placement_ids.length} · ${cumulative}/${plan.total_parts} pièces`;
  assemblyPrev.disabled = clamped === 0;
  assemblyNext.disabled = clamped === plan.steps.length - 1;
}

function showFullModel() {
  for (const mesh of meshByPlacementId.values()) setPartState(mesh, 'normal');
  currentAssemblyStep = null;
  const plan = lastBundle?.assembly_plan;
  assemblyTitle.textContent = 'Modèle complet';
  assemblyProgress.textContent = plan ? `${plan.total_parts} pièces` : '';
  assemblyPrev.disabled = false;
  assemblyNext.disabled = false;
}

function downloadBom(bundle) {
  const total = bundle.bom.lines.reduce((sum, line) => sum + line.quantity, 0);
  if (total !== bundle.bom.total_parts) throw new Error('BOM incohérente.');
  const text = ['part_id,category,quantity', ...bundle.bom.lines.map((line) => `${line.part_id},${line.category},${line.quantity}`)].join('\n') + '\n';
  const blob = new Blob([text], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${bundle.building_id}-bom.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function renderBundle(bundle) {
  validateBundle(bundle);
  clearModel();
  roofRiseByPlacementId = buildRoofRiseMap(bundle.brick_model.parts);
  for (const part of bundle.brick_model.parts) {
    const mesh = makePartMesh(part);
    modelGroup.add(mesh);
    meshByPlacementId.set(part.placement_id, mesh);
  }
  lastBundle = bundle;
  updateSummary(bundle);
  configureAssembly(bundle);
  frameModel();
  setMessage('');
}

async function loadSample() {
  setMessage('Chargement de l’exemple…');
  try {
    const response = await fetch('./sample-export.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderBundle(await response.json());
  } catch (error) {
    setMessage(`Impossible de charger l’exemple : ${error.message}`);
  }
}

fileInput.addEventListener('change', async () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  try { renderBundle(JSON.parse(await file.text())); }
  catch (error) { setMessage(`JSON invalide : ${error.message}`); }
  finally { fileInput.value = ''; }
});
resetButton.addEventListener('click', () => { if (lastBundle) frameModel(); });
sampleButton.addEventListener('click', loadSample);
downloadBomButton.addEventListener('click', () => { try { if (lastBundle) downloadBom(lastBundle); } catch (error) { setMessage(error.message); } });
assemblyRange.addEventListener('input', () => showAssemblyStep(Number(assemblyRange.value)));
assemblyPrev.addEventListener('click', () => showAssemblyStep((currentAssemblyStep ?? 0) - 1));
assemblyNext.addEventListener('click', () => showAssemblyStep((currentAssemblyStep ?? -1) + 1));
assemblyFull.addEventListener('click', showFullModel);

function resizeRenderer() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const needResize = canvas.width !== Math.floor(width * renderer.getPixelRatio()) || canvas.height !== Math.floor(height * renderer.getPixelRatio());
  if (needResize) {
    renderer.setSize(width, height, false);
    camera.aspect = width / Math.max(height, 1);
    camera.updateProjectionMatrix();
  }
}
renderer.setAnimationLoop(() => { resizeRenderer(); controls.update(); renderer.render(scene, camera); });
loadSample();
