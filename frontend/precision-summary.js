function finiteNumber(value){return typeof value==='number'&&Number.isFinite(value)?value:null;}

function allGridErrors(bundle){
  const reports=bundle?.metadata?.discretization_quality;
  if(!Array.isArray(reports))return[];
  return reports.flatMap(report=>(report?.walls??[]).flatMap(wall=>wall?.errors??[]));
}

function precisionSummary(bundle){
  const errors=allGridErrors(bundle).map(error=>finiteNumber(error?.absolute_error_m)).filter(value=>value!==null);
  if(!errors.length)return null;
  const mean=errors.reduce((sum,value)=>sum+value,0)/errors.length;
  const worst=Math.max(...errors);
  const recommendation=bundle?.metadata?.scale_recommendation??null;
  return{
    mean_error_m:mean,
    worst_error_m:worst,
    applied_front_width_studs:finiteNumber(bundle?.brick_model?.width_studs),
    preferred_front_width_studs:finiteNumber(recommendation?.preferred_front_width_studs),
    recommended_front_width_studs:finiteNumber(recommendation?.recommended_front_width_studs),
    improvement_fraction:finiteNumber(recommendation?.improvement_fraction),
  };
}

function formatCentimeters(meters){return`${(meters*100).toFixed(1).replace('.',',')} cm`;}

export {allGridErrors,precisionSummary,formatCentimeters};
