// Add a measurement-free scale-inference audit to the active Survey → Scene prompt.
//
// The accepted Survey remains immutable. This layer never creates a measurement or
// metric value itself; it only requires the downstream architectural reasoning pass
// to exhaust several independent photo-backed scale cues before asking a user to
// measure the building or returning an unnecessarily empty metric envelope.
const originalFetchScaleAudit = globalThis.fetch.bind(globalThis);
const SCALE_AUDIT_MARKER = 'BRICKHOUSE — MEASUREMENT-FREE SCALE AUDIT v4.8';

const SCALE_AUDIT = `
${SCALE_AUDIT_MARKER}

MESURE UTILISATEUR NON OBLIGATOIRE
Une ArchitecturalScene utile doit pouvoir être estimée sans demander par défaut à l’utilisateur de mesurer sa maison. Si le Survey contient \`known_measurements:[]\`, effectue une calibration architecturale multi-indices AVANT de conclure que l’enveloppe principale doit rester métriquement vide.

CALIBRATION MULTI-INDICES — PAS DE DIMENSION STANDARD UNIQUE
- Utilise d’abord les rapports propres aux photos : répétitions, alignements, largeur/hauteur des ouvertures, rythmes d’étages, perspective recoupée entre façades, escalier, garde-corps, terrasse et autres éléments architecturaux identifiés par le Survey.
- Des dimensions architecturales usuelles peuvent seulement définir des PLAGES DE PRIOR plausibles. Elles ne sont ni des mesures, ni des constantes universelles, ni des vérités sur le bâtiment observé.
- Une seule fenêtre, une seule porte ou un seul objet de taille supposée ne suffit JAMAIS à établir l’échelle absolue. Exige plusieurs indices indépendants et cherche leur zone de consensus.
- Si plusieurs familles d’indices convergent vers un intervalle d’échelle raisonnable, choisis une estimation prudente dans cet intervalle et marque toutes les dimensions absolues concernées \`source.kind="inferred"\` avec confiance faible/modérée et evidence photo explicite.
- Si les indices sont contradictoires, atypiques ou trop faibles pour borner honnêtement un intervalle, conserve \`value:null\`. Ne force jamais un consensus pour satisfaire M0 ou le viewer.

PROVENANCE — FRONTIÈRE ABSOLUE
- Une calibration sans mesure utilisateur ne crée JAMAIS de \`known_measurements\` et ne rend JAMAIS une dimension \`user_provided\`.
- Ne transforme jamais un prior statistique externe en evidence observée du bâtiment.
- Une vraie mesure utilisateur, lorsqu’elle existe, reste plus forte que cette calibration et peut remplacer l’incertitude d’échelle sans changer les autres faits Survey.
- Les proportions relatives multi-vues peuvent avoir une confiance supérieure à l’échelle absolue ; conserve cette différence dans les sources/confiances au lieu de propager une fausse précision uniforme.

PRÉFLIGHT ENVELOPPE SANS ANCRE HUMAINE
Quand \`known_measurements\` est vide, audite explicitement si au moins deux familles d’indices indépendantes permettent de borner l’échelle. Si oui, tente une enveloppe principale \`width/depth/height\` cohérente et entièrement \`inferred\`, puis vérifie les ouvertures et objets connectés contre cette même échelle commune. Si non, garde les dimensions réellement non contraintes à \`null\` et explique quels indices se contredisent ou manquent.

RÈGLE PRODUIT
Ne demande une mesure humaine que lorsqu’un vrai blocker aval exige encore une métrique qu’aucun ensemble d’indices photo/architecturaux ne permet de borner honnêtement. L’absence de mesure utilisateur n’est pas, à elle seule, un blocker.
`;

globalThis.fetch = async (...args) => {
  const response = await originalFetchScaleAudit(...args);
  const request = args[0];
  const url = typeof request === 'string' ? request : request?.url || '';
  if (!url.includes('brickhouse-survey-to-scene-prompt.txt')) return response;

  const text = await response.text();
  if (text.includes(SCALE_AUDIT_MARKER)) {
    return new Response(text, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  }

  return new Response(`${text}\n${SCALE_AUDIT}\n`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};
