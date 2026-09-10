// Final Scene handoff audit for the real user correction loop.
//
// This follows the existing append-only prompt-audit architecture. It never
// mutates the accepted Survey or a Scene. It only makes the native Scene
// connectivity contract explicit to the external reasoning pass and, after a
// rejected Scene import, carries that exact candidate + validator error into
// the next canonical Survey -> Scene PDF.
const originalFetchConnectivityAudit = globalThis.fetch.bind(globalThis);
const CONNECTIVITY_AUDIT_MARKER = 'BRICKHOUSE — SCENE CONNECTIVITY PREFLIGHT v4.9';
const REJECTED_SCENE_KEY = 'brickhouse.lastRejectedSceneCandidate';
const REJECTED_ERROR_KEY = 'brickhouse.lastSceneValidationError';

const CONNECTIVITY_AUDIT = `
${CONNECTIVITY_AUDIT_MARKER}

PRÉFLIGHT DE CONNECTIVITÉ — AVANT LE JSON FINAL
Le backend ArchitecturalScene v0.2 valide la géométrie numérique, pas seulement les phrases de relation. Avant de produire le fichier final :
- pour CHAQUE StairRun, teste numériquement ses deux extrémités \`start\` et \`end\` ;
- chacune doit réellement rejoindre, dans la tolérance Scene de 0,12 m, le sol/terrain, une Platform, un volume du bâtiment, ou l'extrémité d'un autre StairRun ;
- une relation \`connects_to\` écrite dans \`relations\` ne répare jamais un vide métrique ;
- pour un escalier à plusieurs volées, vérifie aussi la continuité endpoint-à-endpoint entre les volées et que les deux extrémités extérieures du système aboutissent à de vrais supports ;
- si le raccord est visible dans les preuves, résous conjointement uniquement les valeurs \`inferred\` nécessaires pour encoder ce contact ;
- si le raccord est réellement caché ou non bornable, ne fabrique pas un contact uniquement pour passer le validateur : conserve l'incertitude autorisée par le contrat et explique le blocker plutôt que de falsifier le Survey.

AUDIT FINAL OBLIGATOIRE
Pour chaque StairRun, écris mentalement : \`start -> [support réel]\` et \`end -> [support réel]\`, puis recalcule les coordonnées finales. Ne sérialise la Scene que si ce test est cohérent avec les photos et le Survey.
`;

function correctionContext() {
  let candidate = '';
  let error = '';
  try {
    candidate = localStorage.getItem(REJECTED_SCENE_KEY) || '';
    error = localStorage.getItem(REJECTED_ERROR_KEY) || '';
  } catch {
    return '';
  }
  if (!candidate || !error) return '';
  return `
BRICKHOUSE — CORRECTION ITÉRATIVE DE SCENE

Ceci n'est PAS une nouvelle reconstruction depuis zéro. Boldüngo a déjà reçu une ArchitecturalScene v0.2 et l'a refusée avec le diagnostic exact ci-dessous.

DIAGNOSTIC BOLDÜNGO — AUTORITATIF
${error}

SCENE REFUSÉE — POINT DE DÉPART À CORRIGER
${candidate}

RÈGLES DE CORRECTION
- le Survey validé inclus dans le PDF reste immuable et prioritaire ;
- conserve les IDs, objets, relations et géométries de la Scene refusée lorsqu'ils ne sont pas responsables du diagnostic ;
- remonte à la première incohérence métrique responsable du diagnostic et corrige seulement les valeurs \`inferred\` nécessaires, dans les limites des preuves photo ;
- ne change jamais une donnée Survey ou une mesure utilisateur pour compenser un défaut aval ;
- n'invente pas de raccord caché, de dimension ou d'objet ;
- réexécute tous les audits de ce prompt sur la Scene corrigée complète ;
- sortie : uniquement \`brickhouse-scene-result.json\`, ArchitecturalScene v0.2 à la racine.
`;
}

globalThis.fetch = async (...args) => {
  const response = await originalFetchConnectivityAudit(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;

  let text = await response.text();
  if (!text.includes(CONNECTIVITY_AUDIT_MARKER)) text = `${text}\n${CONNECTIVITY_AUDIT}\n`;
  const correction = correctionContext();
  if (correction) text = `${text}\n${correction}\n`;

  return new Response(text, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
