import {formatCentimeters,precisionSummary} from './precision-summary.js';

const card=document.querySelector('#precision-card');
const summaryEl=document.querySelector('#precision-summary');
const guidanceEl=document.querySelector('#scale-guidance');
const modelSummary=document.querySelector('#model-summary');

function currentBundle(){
  try{return JSON.parse(localStorage.getItem('brickhouse.currentExport')||'null');}catch{return null;}
}

function renderPrecision(){
  if(!card||!summaryEl||!guidanceEl)return;
  const summary=precisionSummary(currentBundle());
  if(!summary){card.hidden=true;return;}
  card.hidden=false;
  summaryEl.textContent=`Arrondi de la grille LEGO : erreur moyenne ${formatCentimeters(summary.mean_error_m)}, pire écart ${formatCentimeters(summary.worst_error_m)}. Ces valeurs mesurent uniquement l'arrondi LEGO, pas l'incertitude des photos.`;

  const preferred=summary.preferred_front_width_studs;
  const recommended=summary.recommended_front_width_studs;
  const improvement=summary.improvement_fraction;
  if(preferred&&recommended&&improvement!==null&&recommended!==preferred&&improvement>=0.01){
    guidanceEl.textContent=`Échelle actuelle : ${preferred} tenons en façade. Une largeur de ${recommended} tenons réduirait le score d'erreur de grille d'environ ${(improvement*100).toFixed(0)} %.`;
  }else if(preferred&&recommended){
    guidanceEl.textContent=`L'échelle actuelle de ${preferred} tenons est déjà la meilleure dans la plage testée autour de cette taille.`;
  }else{
    guidanceEl.textContent='Aucune recommandation d’échelle n’est attachée à cet export.';
  }
}

const observer=modelSummary?new MutationObserver(()=>queueMicrotask(renderPrecision)):null;
observer?.observe(modelSummary,{childList:true,subtree:true,characterData:true});
window.addEventListener('DOMContentLoaded',()=>setTimeout(renderPrecision,0));
setTimeout(renderPrecision,0);

export {renderPrecision};
