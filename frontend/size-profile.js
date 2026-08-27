const studsSelect=document.querySelector('#studs');
const widthInput=document.querySelector('#width');
const depthInput=document.querySelector('#depth');

const PROFILE_LABELS={
  32:'Compact',
  48:'Standard',
  64:'Grand',
};

function positiveNumber(input){
  const value=Number(input?.value);
  return Number.isFinite(value)&&value>0?value:null;
}

function estimateProfile(){
  const frontStuds=positiveNumber(studsSelect);
  const realWidthM=positiveNumber(widthInput);
  const realDepthM=positiveNumber(depthInput);
  if(!frontStuds||!realWidthM||!realDepthM)return null;

  const depthStuds=Math.max(1,Math.round(frontStuds*realDepthM/realWidthM));
  const physicalWidthCm=frontStuds*.8;
  const physicalDepthCm=depthStuds*.8;
  const scaleDenominator=realWidthM/(frontStuds*.008);
  return {
    profile:PROFILE_LABELS[frontStuds]??`${frontStuds} tenons`,
    frontStuds,
    depthStuds,
    physicalWidthCm,
    physicalDepthCm,
    scaleDenominator,
  };
}

function ensureSummary(){
  let summary=document.querySelector('#size-profile-summary');
  if(summary)return summary;
  summary=document.createElement('div');
  summary.id='size-profile-summary';
  summary.className='field wide';
  studsSelect?.closest('.field')?.after(summary);
  return summary;
}

function render(){
  const summary=ensureSummary();
  const estimate=estimateProfile();
  if(!summary||!estimate)return;
  summary.innerHTML=`<label>Encombrement estimé · ${estimate.profile}</label><p class="intro"><strong>${estimate.frontStuds} × ${estimate.depthStuds} tenons</strong> · environ <strong>${estimate.physicalWidthCm.toFixed(1)} × ${estimate.physicalDepthCm.toFixed(1)} cm</strong> · échelle approximative <strong>1:${Math.round(estimate.scaleDenominator)}</strong>.</p><p class="intro">La grille finale peut varier légèrement pour préserver les ouvertures et les assemblages LEGO validés. Le nombre de pièces est calculé par le moteur après discrétisation, pas estimé arbitrairement ici.</p>`;
}

for(const input of [studsSelect,widthInput,depthInput])input?.addEventListener('input',render);
render();
