const API_URL='https://brickhouse-api.onrender.com';
const engine=document.querySelector('#engine-status');
const api=document.querySelector('#api-status');
const vision=document.querySelector('#vision-status');
async function refreshStatus(){
  api.textContent='Réveil / vérification…';
  try{
    const response=await fetch(`${API_URL}/health`,{cache:'no-store'});
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const health=await response.json();
    api.textContent='En ligne sur Render Free';api.className='ok';
    engine.textContent=health.status==='ok'?'Opérationnel':'À vérifier';engine.className=health.status==='ok'?'ok':'wait';
    vision.textContent=health.vision_enabled?'Analyse intégrée activée':'Handoff externe disponible';vision.className=health.vision_enabled?'ok':'wait';
  }catch{
    api.textContent='Serveur gratuit en veille ou indisponible';api.className='wait';
    engine.textContent='État inconnu';engine.className='wait';
    vision.textContent='Handoff externe disponible';vision.className='wait';
  }
}
refreshStatus();
