// Boldüngo phone-first shell v0.3. One viewport, one primary task, details on demand.
const stateOrder = ['photos', 'survey', 'scene', 'model'];

function shellReady() { return document.querySelector('.layout') && document.querySelector('.panel'); }
function navButton(label, state) { const el=document.createElement('button'); el.type='button'; el.className='shell-nav-button'; el.dataset.shellState=state; el.innerHTML=`<span class="shell-nav-dot" aria-hidden="true"></span><span>${label}</span>`; return el; }
function panel(state,label){const el=document.createElement('section');el.className='shell-state-panel';el.dataset.shellPanel=state;el.setAttribute('aria-label',label);return el;}
function move(node,target){if(node)target.appendChild(node);}
function shortCopy(root){
  const views=root.querySelector('#guided-photo-grid')?.closest('.simple-card');
  if(views){const h=views.querySelector('h2');if(h)h.textContent='Ajoutez vos photos';const badge=views.querySelector('.step-badge');if(badge)badge.textContent='4 côtés';}
  const names={front:'Avant',right:'Droite',left:'Gauche',rear:'Arrière'};
  root.querySelectorAll('#guided-photo-grid .guided-photo-slot').forEach(slot=>{const strong=slot.querySelector('strong');if(strong)strong.textContent=names[slot.dataset.slot]||strong.textContent;const hint=slot.querySelector(':scope > span');if(hint)hint.remove();});
  const handoff=root.querySelector('.ai-handoff-card');
  if(handoff){const h=handoff.querySelector('h2');if(h)h.textContent='Analyse ChatGPT';const p=handoff.querySelector('.simple-heading p:not(.eyebrow)');if(p)p.textContent='Envoyez le relevé à ChatGPT, puis importez le résultat.';const download=handoff.querySelector('#download-ai-package');if(download)download.textContent='Exporter pour ChatGPT';const fileLabel=handoff.querySelector('label[for="external-analysis-file"]');if(fileLabel)fileLabel.textContent='Résultat ChatGPT';const importer=handoff.querySelector('#import-analysis');if(importer)importer.textContent='Importer';}
}

function initShell(){
  if(!shellReady()||document.body.classList.contains('boldungo-shell-enabled'))return;
  const layout=document.querySelector('.layout'); const legacy=document.querySelector('.panel'); const resultPanel=document.querySelector('.result-panel');
  shortCopy(legacy);
  const cards=[...legacy.querySelectorAll(':scope > .simple-card')]; const [viewsCard,detailsCard,factsCard,handoffCard,futureCard]=cards;
  const advanced=legacy.querySelector(':scope > .advanced-panel'); const status=legacy.querySelector(':scope > #status'); const build=document.querySelector('#build-bricks');
  document.body.classList.add('boldungo-shell-enabled');
  const cockpit=document.createElement('div');cockpit.className='boldungo-cockpit';
  const header=document.createElement('header');header.className='shell-progress';header.innerHTML=`<div class="shell-progress-copy"><strong id="shell-state-title">Photos</strong></div><div class="shell-progress-meter" aria-label="Progression"><span class="shell-progress-fill" id="shell-progress-fill"></span></div><button type="button" class="shell-tools-button" id="shell-tools-button" aria-expanded="false">•••</button>`;
  const workspace=document.createElement('div');workspace.className='shell-workspace';
  const photos=panel('photos','Photos'),survey=panel('survey','Relevé'),scene=panel('scene','Maison'),model=panel('model','Maquette');
  move(viewsCard,photos); move(handoffCard,survey); move(resultPanel,scene);
  const modelCard=document.createElement('section');modelCard.className='simple-card shell-model-card';modelCard.innerHTML='<div class="shell-model-icon" aria-hidden="true">▦</div><h2>Maquette</h2><p>Prête après validation de la maison.</p><div class="shell-build-home"></div>';if(build)modelCard.querySelector('.shell-build-home').appendChild(build);model.appendChild(modelCard);
  workspace.append(photos,survey,scene,model);
  const action=document.createElement('div');action.className='shell-primary-action';action.innerHTML='<button type="button" id="shell-primary-button">Créer le relevé</button>';
  const bottom=document.createElement('nav');bottom.className='shell-bottom-nav';bottom.setAttribute('aria-label','Parcours');bottom.append(navButton('Photos','photos'),navButton('Relevé','survey'),navButton('Maison','scene'),navButton('Maquette','model'));
  const backdrop=document.createElement('div');backdrop.className='shell-drawer-backdrop';backdrop.hidden=true;
  const drawer=document.createElement('aside');drawer.className='shell-tools-drawer';drawer.id='shell-tools-drawer';drawer.setAttribute('aria-hidden','true');drawer.innerHTML='<div class="shell-drawer-head"><strong>Détails</strong><button type="button" id="shell-tools-close">Fermer</button></div><div class="shell-drawer-scroll"></div>';
  const drawerScroll=drawer.querySelector('.shell-drawer-scroll');move(factsCard,drawerScroll);move(detailsCard,drawerScroll);move(advanced,drawerScroll);move(futureCard,drawerScroll);
  [...legacy.children].filter(n=>['P','H1'].includes(n.tagName)).forEach(n=>n.remove());if(status)drawerScroll.prepend(status);
  cockpit.append(header,workspace,action,bottom);layout.replaceChildren(cockpit);document.body.append(backdrop,drawer);
  const titles={photos:'Photos',survey:'Relevé',scene:'Maison',model:'Maquette'};const labels={photos:'Créer le relevé',survey:'Importer le résultat',scene:'Continuer',model:'Construire'};let active='photos';
  function close(){drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true');backdrop.hidden=true;header.querySelector('#shell-tools-button').setAttribute('aria-expanded','false');}
  function open(){drawer.classList.add('open');drawer.setAttribute('aria-hidden','false');backdrop.hidden=false;header.querySelector('#shell-tools-button').setAttribute('aria-expanded','true');}
  function setState(state){if(!stateOrder.includes(state))return;active=state;cockpit.dataset.shellState=state;workspace.querySelectorAll('[data-shell-panel]').forEach(p=>p.hidden=p.dataset.shellPanel!==state);bottom.querySelectorAll('[data-shell-state]').forEach(b=>{const on=b.dataset.shellState===state;b.classList.toggle('active',on);b.setAttribute('aria-current',on?'page':'false');});document.querySelector('#shell-state-title').textContent=titles[state];document.querySelector('#shell-progress-fill').style.width=`${((stateOrder.indexOf(state)+1)/4)*100}%`;document.querySelector('#shell-primary-button').textContent=labels[state];}
  bottom.addEventListener('click',e=>{const b=e.target.closest('[data-shell-state]');if(b)setState(b.dataset.shellState);});header.querySelector('#shell-tools-button').addEventListener('click',()=>drawer.classList.contains('open')?close():open());drawer.querySelector('#shell-tools-close').addEventListener('click',close);backdrop.addEventListener('click',close);document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
  document.querySelector('#shell-primary-button').addEventListener('click',()=>{if(active==='photos'){document.querySelector('#download-ai-package')?.click();setState('survey');return;}if(active==='survey'){document.querySelector('#external-analysis-file')?.click();return;}if(active==='scene'){setState('model');return;}document.querySelector('#build-bricks')?.click();});
  document.querySelector('#external-analysis-file')?.addEventListener('change',()=>{if(document.querySelector('#external-analysis-file')?.files?.length)document.querySelector('#import-analysis')?.click();});
  const result=document.querySelector('#result');if(result)new MutationObserver(()=>{if(!result.hidden)setState('scene');}).observe(result,{attributes:true,attributeFilter:['hidden']});setState('photos');
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initShell,{once:true});else initShell();