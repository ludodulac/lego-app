# Boldüngo / BrickHouse

> **Boldüngo** est le nom produit visible. Le dépôt `lego-app` et plusieurs packages/identifiants internes conservent volontairement le nom historique **BrickHouse**. Ne pas lancer de renommage mécanique.

Boldüngo transforme des photos réelles d’un bâtiment en une représentation architecturale structurée, puis en une approximation LEGO déterministe, vérifiable et exportable.

Pour toute reprise par une IA, commencer par **`AI_START_HERE.md`** puis consulter **`PROGRESSION.md`** pour l’état opérationnel et les prochaines briques.

## Pipeline actuel

Le pipeline de référence est :

`photos multi-vues → ArchitecturalSurvey v0.1 → ArchitecturalScene v0.2 → adaptation aux capacités LEGO → BrickModel → validation géométrique/assemblage → BOM / AssemblyPlan / InstructionPlan / BagPlan → viewer`

Principes invariants :
- le Survey conserve la vérité observée/sémantique et l’incertitude ;
- la Scene porte la vérité métrique/géométrique ;
- les contraintes LEGO ne doivent jamais modifier silencieusement la vérité architecturale ;
- une approximation ou une primitive non supportée doit être signalée comme perte de fidélité plutôt que transformée en faux fait architectural.

Voir `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md` et `docs/DECISIONS.md`.

## Workflow photo principal

Le workflow manuel actuellement validé avant dépendance à une API IA est en deux étapes :

1. **Photos → Survey** : Boldüngo génère un PDF contenant les instructions et les photos. Une conversation IA neutre doit retourner un `ArchitecturalSurvey v0.1` complet, importé sans correction manuelle.
2. **Survey → Scene** : le Survey validé et le PDF photo original sont fournis ensemble. Le Survey reste autoritatif pour inventaire/IDs/certitudes ; les photos servent à borner la géométrie. La sortie est un `ArchitecturalScene v0.2` complet.

Le flux historique one-shot `external-bundle-0.1` reste une compatibilité d’import, pas le workflow principal. Le jalon de validation bout-en-bout est suivi dans l’issue #274 / BH-090.

## Moteurs déterministes

Le dépôt contient notamment :
- `backend/brickhouse/building/` — contrats historiques BuildingModel ;
- `backend/brickhouse/scene/` — contrats ArchitecturalScene et primitives métriques ;
- `backend/brickhouse/geometry/` — géométrie architecturale ;
- `backend/brickhouse/bricks/` — adaptation LEGO, placement, toiture, détails Scene-aware, export et validation ;
- `lego_geometry_engine/` — géométrie physique LDraw, collisions/contacts/connecteurs/supports ;
- `frontend/` — parcours photo, handoffs IA, viewer ;
- `tests/` — régressions unitaires et bout-en-bout ;
- `docs/` — architecture, contrats, décisions et continuité.

Le moteur de construction doit rester autant que possible déterministe, testable et indépendant du fournisseur.

## État des capacités importantes

Le projet sait notamment :
- valider Survey et Scene ;
- conserver provenance, confiance et inconnues ;
- préserver plusieurs volumes, ouvertures, plateformes, escaliers, terrain et cheminées ;
- projeter une Scene vers une coque LEGO sans réécrire la Scene ;
- gérer plusieurs familles de pente de toiture, dont une famille 18° utilisée par une régression maison réelle ;
- ouvrir physiquement la toiture autour d’une cheminée métrique ;
- valider une partie de la géométrie LDraw : collision/contact, containment, support et connecteurs exacts ;
- produire BOM, AssemblyPlan, InstructionPlan et BagPlan comme contrats séparés ;
- exposer les limitations finales via `fidelity_issues`.

Le moteur géométrique n’est pas encore un solveur mécanique général : Technic, clips, charnières, SNOT, contraintes, stress et stabilité globale restent partiels ou hors périmètre actuel.

## Benchmark principal

Le benchmark réel principal reste une maison photographiée sous 5 vues originales. Une largeur réelle de façade avant de 10 m sert d’ancre d’échelle lors du test humain courant. Les photos supplémentaires historiques peuvent servir de vérité de contrôle, mais ne doivent pas être utilisées pour rendre artificiellement parfait le benchmark 5 vues.

Les règles apprises de ce benchmark doivent toujours être génériques ; aucune dimension, typologie ou topologie propre à cette maison ne doit être codée comme défaut global.

## Lancer les tests

Python 3.12+ est requis.

```bash
python -m pip install -e ".[dev]"
pytest -q
```

Le workflow `.github/workflows/ci.yml` exécute la suite de tests et plusieurs smoke tests. `.github/workflows/pages.yml` reconstruit et publie le frontend sur GitHub Pages. Lorsqu’une fonctionnalité dépend du chemin Pages, une CI verte seule ne suffit pas : vérifier aussi le déploiement.

## Pipeline M0 historique

Le CLI historique M0 reste disponible pour les bâtiments synthétiques et les régressions :

```bash
brickhouse-m0 docs/examples/building-model-simple-house.json frontend/sample-export.json --front-width-studs 48
```

Il constitue une brique du système actuel, pas la description complète du produit.

## Règles de développement

1. Préserver l’existant ; ajouter/étendre avant de supprimer.
2. Séparer compréhension architecturale, géométrie métrique, adaptation LEGO, construction, notice, sacs et approvisionnement.
3. Ne jamais inventer une géométrie, une mesure, une relation ou une certitude pour faire passer le pipeline.
4. Corriger la cause générique et ajouter une régression reproductible.
5. Une couche basse ne modifie pas un fait certain d’une couche haute pour faciliter la construction.
6. Le catalogue et les IDs internes restent indépendants des fournisseurs.
7. Toute décision architecturale structurante doit être indexée dans `docs/DECISIONS.md`.
8. Toute passation substantielle doit suivre `AI_START_HERE.md` et mettre à jour `PROGRESSION.md` ; les chronologies détaillées peuvent rester dans `docs/CURRENT_PROJECT_STATE.md` ou des documents spécialisés.

## Reprise du projet

La source de reprise courte est :

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main`, puis lis `PROGRESSION.md` et reprends la première brique non résolue.
