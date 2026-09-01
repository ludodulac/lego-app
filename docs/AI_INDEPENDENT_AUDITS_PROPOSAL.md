# BrickHouse / Boldüngo — proposition d’audits IA indépendants

Date d’analyse : 2026-09-01
État de `main` examiné avant cette documentation : `ea6afbc6ea8690c69683ab0924b5bd6cc7dd3b96`.

Ce document est une **étude architecturale et une passation**, pas une implémentation fonctionnelle. Aucun contrat Survey/Scene existant n’est remplacé ici. L’objectif est d’évaluer une extension additive du pipeline avec deux rôles IA de contrôle indépendants.

## Résumé de décision

La proposition est pertinente, à une condition importante : les nouveaux audits ne doivent pas remplacer les validateurs déterministes déjà présents. Ils doivent couvrir ce que ces validateurs ne peuvent pas vérifier seuls, principalement la fidélité **aux pixels / photos sources** et les erreurs d’association multi-vues.

Architecture minimale recommandée :

`Photos → Survey → SurveyAudit → Survey validé → Scene → SceneAudit → Scene validée → adaptation LEGO → BrickModel`

Les audits produisent des contrats structurés distincts et **ne modifient jamais silencieusement** le Survey ou la Scene. Les boucles de correction ne sont déclenchées que lorsqu’un audit produit un problème actionnable.

## 1. Ce qui existe déjà

### 1.1 Séparation Survey / Scene / LEGO déjà forte

La séparation proposée est déjà le principe central du dépôt :

- `ArchitecturalSurvey v0.1` = autorité sémantique / observée ;
- `ArchitecturalScene v0.2` = autorité métrique / géométrique ;
- BuildingModel / projection M0 = sous-ensemble constructible ;
- adaptation LEGO = couche inférieure qui ne doit pas réécrire la vérité architecturale.

Sources canoniques :
- `docs/ARCHITECTURAL_SURVEY_V01.md`
- `docs/ARCHITECTURAL_SCENE_V02.md`
- `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`
- `docs/DECISIONS.md` ADR-009, ADR-010, ADR-011, ADR-012.

### 1.2 Photos → Survey contient déjà plusieurs audits *dans la même passe IA*

Le handoff Photos → Survey n’est plus un prompt unique naïf. Il superpose des garde-fous additifs : terrain, topologie, couverture/final-contract, raisonnement multi-vues, sérialisation stricte. Ces passes cherchent déjà notamment :

- omissions de toiture / cheminée / enveloppe ;
- connexions `connects_to` ;
- identité physique des ouvertures ;
- double comptage multi-vues ;
- hypothèses concurrentes ;
- contradiction entre vues ;
- prudence des certitudes ;
- conformité finale du JSON.

Mais ces audits sont exécutés par **la même conversation / le même modèle qui produit le Survey**. Ils améliorent l’auto-contrôle, sans fournir une vraie indépendance de lecture.

### 1.3 Validation déterministe du Survey

`backend/brickhouse/survey/models.py` impose déjà :

- schéma racine `ArchitecturalSurvey v0.1` ;
- IDs uniques ;
- références d’evidence vers des photos connues ;
- références de relations vers des observations existantes ;
- séparation objet / certitude d’attribut ;
- rôles photo cohérents ;
- capture de régions d’image facultatives.

`backend/brickhouse/survey/validation.py` ajoute des règles sémantiques, par exemple :

- une observation `opening` = exactement un objet physique ;
- cohérence de certains types architecturaux ;
- validité des rangs qualitatifs ;
- raffinement append-only avec nouvelle preuve ;
- protection des observations certaines / user-confirmed contre une réécriture silencieuse pendant une extension.

L’API expose déjà :

- `POST /api/v1/validate-survey`
- `POST /api/v1/validate-survey-extension`.

### 1.4 Validation Survey → Scene déjà très développée

`backend/brickhouse/scene/survey_validation.py`, `survey_structure_guard.py`, `fidelity_validation.py`, `topology_fidelity.py`, `opening_visual_fidelity.py`, `roof_fidelity.py` et les validations du modèle Scene couvrent déjà une grande partie des dérives **structurelles entre Survey et Scene** :

- largeur utilisateur conservée et provenance `user_provided` ;
- ouverture absente du Survey interdite ;
- ouverture `unproven` non promue ;
- façade d’ouverture conservée ;
- type sémantique conservé quand il est prouvé ;
- rang horizontal / vertical conservé ;
- toiture certaine non supprimée ;
- terrain qualitatif / métrique contrôlé ;
- certaines connexions plateforme/escalier vérifiées géométriquement ;
- omissions de géométrie certaine seulement acceptées si explicitement documentées ;
- attributs seulement plausibles non transformés en contraintes certaines.

L’API expose :

- `POST /api/v1/validate-scene`
- `POST /api/v1/validate-scene-against-survey`.

### 1.5 Préflight de construction LEGO déjà séparé

Avant construction, la projection et la compatibilité M0 produisent des blockers / warnings. `build-scene` ne doit pas transformer la Scene pour passer artificiellement. Le moteur LEGO possède aussi ses propres validations physiques.

### 1.6 Tests existants

Le dépôt possède déjà une couverture importante sous :

- `tests/survey/`
- `tests/scene/`
- `tests/pipeline/`
- `tests/bricks/`
- `lego_geometry_engine/tests/`.

Les tests Survey verrouillent notamment le contrat de capture, les rangs d’ouverture, les audits de couverture/final-contract, le raisonnement, la validation sémantique et les extensions. Les tests Scene verrouillent notamment la fidélité d’attribut, les comptes d’ouvertures, la topologie multi-vues, les valeurs métriques nullable, l’ordre des ouvertures, les toitures, la structure visible et la fidélité Survey → Scene.

## 2. Ce qui manque réellement

### 2.1 Il n’existe pas de contrôleur IA indépendant Photos + Survey

Les validateurs Survey actuels peuvent vérifier que `evidence.photo_index` existe, mais pas que le texte de l’evidence correspond réellement aux pixels.

Ils ne peuvent pas, sans vision :

- constater qu’une fenêtre mentionnée n’est en réalité pas visible ;
- découvrir une cheminée oubliée dans une photo ;
- voir que deux IDs sont en fait le même objet physique observé depuis deux angles ;
- détecter une mauvaise association gauche/droite résultant d’une perspective difficile ;
- juger qu’une certitude `certain` est visuellement trop forte ;
- découvrir une contradiction entre deux photos qui n’est pas explicitement encodée dans le Survey.

C’est le principal espace de valeur d’un `SurveyAudit` indépendant.

### 2.2 Il n’existe pas de contrôleur IA indépendant Photos + Survey + Scene

La validation Survey → Scene compare deux contrats structurés. Elle est forte pour les invariants explicites, mais elle ne re-regarde pas réellement la façade dans les photos pour déterminer si :

- une profondeur estimée est visuellement crédible ;
- un niveau de terrasse est compatible avec plusieurs angles ;
- une toiture métrique correspond à la silhouette photographique ;
- une position relative est décalée alors que le Survey ne portait qu’un ordre qualitatif ;
- un volume secondaire a une géométrie incompatible avec une vue arrière oblique ;
- une métrique est mathématiquement valide mais visuellement indéfendable.

C’est l’espace de valeur d’un `SceneAudit` indépendant.

### 2.3 Le workflow de correction explicite n’est pas encore matérialisé comme contrat dédié

`survey/validation.py` mentionne qu’une observation certaine erronée doit passer par un « workflow de correction explicite », tandis que `/validate-survey-extension` interdit précisément de réécrire des faits validés. Dans l’API inspectée, il n’existe pas encore de contrat/endpoint spécifique de correction Survey pilotée par un audit.

Une extension d’audit devra donc définir comment passer d’un diagnostic à un candidat corrigé sans mutation silencieuse.

### 2.4 La taxonomie de provenance n’est pas complètement alignée avec le vocabulaire souhaité

`SourceKind` actuel contient :

- `observed`
- `user_provided`
- `inferred`
- `generated_default`

`ArchitecturalScene` encode l’inconnu principalement par `null` et parfois par des enums `unknown`. La documentation parle aussi d’`estimated`, mais `SourceKind` n’a pas actuellement une valeur `estimated` dédiée.

Avant d’ajouter un audit, il faut **préserver le contrat actuel**. Une éventuelle évolution `estimated` doit être une décision séparée et versionnée ; elle n’est pas nécessaire pour introduire les audits.

## 3. Est-ce que les audits apportent une amélioration réelle ?

### SurveyAudit : oui, valeur potentiellement élevée

Il ne fait pas doublon avec `/validate-survey` parce que son autorité supplémentaire est le **contenu visuel**. Il peut attraper une classe d’erreurs que les validateurs déterministes ne peuvent pas voir.

Il est particulièrement pertinent pour :

- identité multi-vues ;
- omissions ;
- faux positifs visuels ;
- orientations ;
- relations physiques réellement visibles ;
- niveau de certitude par rapport aux pixels.

### SceneAudit : oui, mais avec périmètre plus ciblé

Une partie importante de ses responsabilités est déjà couverte par `validate-scene-against-survey`. Il serait donc inutile de lui demander de revérifier des invariants parfaitement déterministes comme :

- IDs ;
- façade déclarée ;
- largeur utilisateur exacte ;
- ordre qualitatif déjà encodé ;
- présence d’une primitive certaine ;
- connectivité métrique calculable.

Sa valeur doit être concentrée sur les questions **photo-géométrie** non déterministes : perspective, proportions, profondeur, hauteur relative, silhouette de toiture, emplacement de structures complexes, compatibilité visuelle des estimations.

Conclusion : `SurveyAudit` est probablement le gain le plus direct. `SceneAudit` est utile si son prompt est explicitement limité aux anomalies que les validateurs déterministes ne savent pas décider.

## 4. Architecture minimale additive recommandée

### 4.1 Ne modifier aucun contrat existant au départ

Conserver intégralement :

- `ArchitecturalSurvey v0.1`
- `ArchitecturalScene v0.2`
- API de validation existante
- projection M0
- BrickModel / validations LEGO.

Ajouter seulement deux nouveaux résultats d’audit.

### 4.2 Nouveau contrat `SurveyAudit v0.1`

Proposition minimale :

```json
{
  "schema_version": "0.1",
  "kind": "survey_audit",
  "survey_id": "...",
  "summary": {
    "status": "pass|needs_correction",
    "issue_count": 0
  },
  "findings": [
    {
      "id": "audit-...",
      "status": "confirmed|disputed|missing|duplicate|insufficient_evidence|contradiction",
      "target_type": "observation|relation|photo|survey",
      "target_id": "opening-...",
      "severity": "info|warning|error",
      "photo_evidence": [
        {"photo_index": 3, "observation": "..."}
      ],
      "message": "...",
      "suggested_action": "keep|lower_certainty|merge|add|remove|reorient|review"
    }
  ]
}
```

Règles :

- le contrôleur reçoit le PDF original + le Survey ;
- il n’a pas accès au raisonnement conversationnel du producteur ;
- il ne renvoie jamais un Survey complet corrigé en premier résultat ;
- chaque critique doit citer une preuve photo ou être `insufficient_evidence` ;
- aucune absence de preuve ne devient automatiquement preuve d’absence ;
- un finding ne change rien tant qu’une correction séparée n’a pas été générée et validée.

### 4.3 Étape de correction Survey séparée

Seulement si `SurveyAudit.summary.status == needs_correction` :

1. produire un **Survey candidat corrigé** à partir de `Survey original + SurveyAudit + PDF` ;
2. conserver un journal explicite de modifications ;
3. exécuter le modèle Pydantic et `validate_survey_semantics` ;
4. ajouter un futur validateur de correction qui vérifie que chaque modification est reliée à un finding d’audit ;
5. la sortie devient le « Survey validé » utilisé par Survey → Scene.

Aucune correction automatique ne doit être appliquée par simple patch aveugle du contrôleur.

### 4.4 Nouveau contrat `SceneAudit v0.1`

Proposition minimale :

```json
{
  "schema_version": "0.1",
  "kind": "scene_audit",
  "survey_id": "...",
  "scene_id": "...",
  "summary": {
    "status": "pass|needs_correction",
    "issue_count": 0
  },
  "findings": [
    {
      "id": "scene-audit-...",
      "status": "confirmed|disputed|insufficient_evidence|contradiction",
      "target_type": "volume|opening|roof|terrain|platform|stair|chimney|scene",
      "target_id": "...",
      "severity": "info|warning|error",
      "photo_evidence": [
        {"photo_index": 5, "observation": "..."}
      ],
      "scene_claim": "...",
      "message": "...",
      "suggested_action": "keep|reestimate|set_unknown|review"
    }
  ]
}
```

Le prompt du SceneAudit doit d’abord recevoir le résultat de `validate-scene-against-survey`. Il ne doit pas gaspiller un appel IA à redécouvrir les erreurs que le backend sait déjà calculer.

### 4.5 Gating minimal

Pipeline recommandé :

1. IA observation → Survey
2. backend `validate-survey`
3. si backend invalide : corriger le contrat sans lancer d’audit visuel coûteux
4. si backend valide : IA indépendante → SurveyAudit
5. si audit pass : Survey validé
6. si audit problème : une seule boucle correction → validation → audit ciblé
7. IA géométrique → Scene
8. backend `validate-scene-against-survey` puis `validate-scene`
9. si backend invalide : corriger sans lancer d’audit visuel complet
10. si backend valide : IA indépendante → SceneAudit
11. si audit pass : Scene validée
12. si audit problème : correction Scene ciblée → validations déterministes → re-audit ciblé
13. adaptation LEGO / BrickModel.

Cette stratégie évite de multiplier arbitrairement les appels : les contrôleurs IA interviennent seulement sur des candidats déjà structurellement valides.

## 5. Indépendance des contrôleurs

Pour réduire la corrélation d’erreur :

- nouvelle conversation / nouveau contexte pour chaque audit ;
- fournir les sources et le résultat structuré, pas le chain-of-thought du producteur ;
- utiliser un prompt d’auditeur différent d’un prompt de génération ;
- ordre des tâches différent : commencer par chercher les contradictions / omissions avant de lire les conclusions du résultat ;
- demander des findings falsifiables avec photo_index ;
- ne jamais demander « améliore ce Survey » ou « reconstruis une meilleure Scene » dans la passe d’audit ;
- si possible, varier fournisseur/modèle plus tard, mais ne pas rendre l’architecture dépendante de cela.

## 6. Mesurer l’efficacité sur le benchmark réel 5 photos

Le benchmark ne doit pas mesurer « est-ce que l’IA donne une jolie maison ». Il doit mesurer les erreurs détectables et la dérive entre couches.

### 6.1 Gold set humain minimal

Créer une fiche de vérité benchmark versionnée dans le dépôt, sans inclure les photos privées elles-mêmes si elles ne doivent pas être publiques. La fiche doit seulement énumérer les assertions humaines de référence nécessaires au scoring, par exemple :

- 5 vues appartiennent au même bâtiment ;
- façade avant largeur utilisateur = 10 m ;
- côté gauche observé dans deux vues ;
- arrière partiel / occulté ;
- pente du terrain côté droit monte avant → arrière ;
- terrasse/deck visible sous plusieurs angles ;
- escalier extérieur visible sous plusieurs angles ;
- cheminée visible si l’appartenance au bâtiment est certaine ;
- comptes d’ouvertures par façade pour les objets réellement distinguables ;
- relations physiquement prouvées ;
- zones explicitement inconnues.

Cette fiche doit rester indépendante de la sortie d’un modèle particulier.

### 6.2 Métriques Survey

Comparer `Survey initial` vs `Survey validé après audit` contre le gold set :

- **precision observations** : observations soutenues / observations produites ;
- **recall observations** : observations de référence retrouvées / observations de référence ;
- **duplicate rate** : objets physiques comptés plusieurs fois ;
- **multi-view identity error rate** ;
- **facade/orientation error rate** ;
- **relation precision/recall** ;
- **certainty calibration** : taux de claims `certain` réellement soutenus ;
- **unknown preservation** : zones non prouvées qui restent inconnues ;
- nombre d’erreurs backend avant/après audit.

Mesure de valeur du contrôleur :

`net audit gain = erreurs vraies corrigées - nouvelles erreurs introduites par la correction`.

Un audit qui signale beaucoup de choses mais dégrade la précision n’est pas utile.

### 6.3 Métriques Scene

Évaluer :

- conservation de tous les objets Survey certains ;
- taux de promotion illégitime de claims plausibles/unproven ;
- erreurs de façade ;
- ordre horizontal/vertical ;
- cohérence des connexions terrasse/escalier ;
- direction terrain ;
- compatibilité toiture / silhouette ;
- métriques utilisateur exactement conservées ;
- part de dimensions `null` lorsque non défendables ;
- nombre de blockers deterministic Survey→Scene ;
- nombre d’anomalies photo-géométrie trouvées uniquement par SceneAudit.

### 6.4 Test A/B obligatoire avant généralisation

Sur plusieurs runs du même benchmark :

A = pipeline courant

B = pipeline courant + SurveyAudit

C = pipeline courant + SurveyAudit + SceneAudit

Comparer :

- taux de pipeline arrivant à une Scene valide sans correction humaine ;
- nombre de défauts architecturaux confirmés avant LEGO ;
- coût / nombre d’appels IA ;
- nombre de boucles de correction ;
- stabilité entre runs ;
- erreurs finales visibles dans BrickModel/viewer attribuables à une mauvaise interprétation photo.

Ne généraliser SceneAudit que s’il attrape régulièrement des erreurs que les validateurs déterministes + SurveyAudit ne détectent pas.

## 7. Ordre d’implémentation recommandé

Phase 0 — documentation seulement (ce document) : FAIT.

Phase 1 — `SurveyAudit v0.1` uniquement :
- modèles Pydantic dédiés ;
- JSON schema / prompt audit ;
- import/validation ;
- aucune correction automatique ;
- tests synthétiques ;
- benchmark 5 photos en lecture indépendante.

Phase 2 — correction Survey explicite :
- contrat de changement / provenance ;
- validation que les corrections sont justifiées par findings ;
- une boucle maximum par défaut.

Phase 3 — `SceneAudit v0.1` :
- seulement après avoir mesuré le gain de SurveyAudit ;
- alimenté par PDF + Survey validé + Scene + rapport du validateur déterministe ;
- ciblé sur photo-géométrie, pas sur les invariants déjà calculables.

Phase 4 — intégration produit / automatisation :
- seulement lorsque les métriques démontrent le bénéfice ;
- préserver le round-trip manuel tant qu’il sert de banc d’essai.

## 8. Risques à éviter

- transformer l’audit en deuxième génération libre ;
- laisser le contrôleur réécrire directement la source qu’il audite ;
- faire voter deux IA semblables et appeler cela une vérité ;
- promouvoir une majorité de modèles en preuve photographique ;
- répéter dans les prompts d’audit toutes les validations déterministes ;
- déclencher une boucle infinie génération ↔ audit ;
- hardcoder la maison benchmark ;
- accepter une « correction » qui affaiblit un invariant backend ;
- publier les photos privées du benchmark dans le dépôt sans décision explicite.

## 9. Décision proposée

**GO expérimental pour SurveyAudit, architecture additive.**

**GO conditionnel pour SceneAudit** : concevoir le contrat maintenant, mais ne l’activer qu’après mesure du SurveyAudit et après avoir défini précisément les anomalies photo-géométrie non couvertes par `validate-scene-against-survey`.

Aucune étape existante ne doit être supprimée ou remplacée.

## 10. Instruction de reprise pour la prochaine conversation

Lire dans cet ordre :

1. `AI_START_HERE.md`
2. vérifier l’état réel de `main`
3. `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md`
4. `backend/brickhouse/survey/models.py`
5. `backend/brickhouse/survey/validation.py`
6. `backend/brickhouse/scene/models.py`
7. `backend/brickhouse/scene/fidelity_validation.py`
8. `backend/brickhouse/scene/survey_validation.py`
9. `backend/brickhouse/api.py`
10. tests `tests/survey/` et `tests/scene/` concernés.

Instruction courte suffisante :

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main`, puis lis `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` et reprends l’étude/implémentation additive des audits IA indépendants sans remplacer le pipeline existant.
