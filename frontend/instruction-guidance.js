const stepsRoot=document.querySelector('#steps');
let applying=false;

function currentBundle(){
  try{return JSON.parse(localStorage.getItem('brickhouse.currentExport')||'null');}catch{return null;}
}

function phaseRanges(plan){
  const ranges=new Map();
  for(const step of plan.steps){
    const key=`${step.bag}|${step.phase}`;
    const row=ranges.get(key)??{first:step.sequence,last:step.sequence,bag:step.bag,phase:step.phase};
    row.last=step.sequence;ranges.set(key,row);
  }
  return ranges;
}

function rotationLabel(part){
  const q=((part.rotation_quarter_turns??0)%4+4)%4;
  if(q===0)return null;
  return q===1?'Tourner de 90°':q===2?'Tourner de 180°':'Tourner de 270°';
}

function enhance(){
  if(applying)return;
  const bundle=currentBundle();
  if(!bundle?.assembly_plan?.steps?.length||!bundle?.brick_model?.parts?.length)return;
  const cards=[...stepsRoot.querySelectorAll('.step-card')];
  if(cards.length!==bundle.assembly_plan.steps.length)return;
  applying=true;
  try{
    stepsRoot.querySelectorAll('.phase-banner').forEach(el=>el.remove());
    const parts=new Map(bundle.brick_model.parts.map(p=>[p.placement_id,p]));
    const ranges=phaseRanges(bundle.assembly_plan);
    let previousKey=null;
    cards.forEach((card,index)=>{
      const step=bundle.assembly_plan.steps[index],key=`${step.bag}|${step.phase}`;
      card.dataset.phase=step.phase;card.dataset.bag=String(step.bag);
      if(key!==previousKey){
        const r=ranges.get(key),banner=document.createElement('section');
        banner.className='phase-banner';
        banner.innerHTML=`<div class="bag-number">${step.bag}</div><div><p>Sachet ${step.bag} / ${bundle.assembly_plan.total_bags}</p><h2>${step.phase}</h2><span>Préparez les pièces des étapes ${r.first} à ${r.last}.</span></div>`;
        card.before(banner);previousKey=key;
      }
      card.querySelectorAll('.instruction-kind-cue,.closeup-cue').forEach(el=>el.remove());
      if(step.instruction_kind==='subassembly'){
        const cue=document.createElement('div');cue.className='instruction-kind-cue';
        cue.innerHTML='<strong>Mini-construction</strong><span>Assemblez ces pièces ensemble avant d’insérer l’ensemble dans la maison.</span>';
        card.querySelector('.parts-tray')?.before(cue);
      }
      if(step.focus==='closeup'){
        const cue=document.createElement('div');cue.className='closeup-cue';cue.textContent='⌕ Vue rapprochée — vérifiez précisément le point de fixation';
        card.querySelector('.visual-slot')?.before(cue);card.classList.add('needs-closeup');
      }else card.classList.remove('needs-closeup');
      const rows=[...card.querySelectorAll('.visual-part-row')];
      const aggregated=[];
      for(const pid of step.placement_ids){const p=parts.get(pid);if(p&&!aggregated.some(x=>x.part_id===p.part_id&&x.category===p.category))aggregated.push(p);}
      rows.forEach((row,i)=>{
        row.querySelector('.rotation-part-cue')?.remove();
        const label=rotationLabel(aggregated[i]);
        if(label){const badge=document.createElement('span');badge.className='rotation-part-cue';badge.textContent=`↻ ${label}`;row.appendChild(badge);}
      });
    });
  }finally{applying=false;}
}

const observer=new MutationObserver(()=>queueMicrotask(enhance));
observer.observe(stepsRoot,{childList:true,subtree:true});
window.addEventListener('DOMContentLoaded',()=>setTimeout(enhance,0));
