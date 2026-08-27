const button=document.querySelector('#load-reference-house');
const message=document.querySelector('#message');

function validBundle(bundle){
  return bundle?.schema_version==='0.1'
    && Array.isArray(bundle?.brick_model?.parts)
    && bundle.brick_model.parts.length>0
    && Array.isArray(bundle?.bom?.lines)
    && bundle?.assembly_plan?.steps?.length>0;
}

async function loadReferenceHouse(){
  if(!button)return;
  button.disabled=true;
  if(message)message.textContent='Chargement de la maison de référence…';
  try{
    const response=await fetch('./brickhouse-partial-export.json',{cache:'no-store'});
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const bundle=await response.json();
    if(!validBundle(bundle))throw new Error('export de référence incomplet');
    // viewer.js already owns the canonical pending-export handoff. Reuse it so
    // the exact same bundle is rendered, persisted as currentExport, and then
    // consumed by the notice page without introducing a second rendering path.
    localStorage.setItem('brickhouse.pendingExport',JSON.stringify(bundle));
    window.location.reload();
  }catch(error){
    if(message)message.textContent=`Impossible de charger la maison de référence : ${error.message}`;
    button.disabled=false;
  }
}

button?.addEventListener('click',loadReferenceHouse);
