# PROJECT PRINCIPLES — Boldüngo / BrickHouse

Ce document est la constitution courte et stable du projet. Il contient des invariants durables, pas l'état technique du jour. Les faits changeants (HEAD, PR, CI, endpoints présents, tests, chantier actif) doivent être vérifiés dans le dépôt réel.

## Mission

Transformer des preuves architecturales, notamment des photos, en une représentation structurée et traçable permettant de produire une maquette LEGO fidèle et des instructions de construction, sans inventer ce que les preuves ne permettent pas d'établir.

## Principes non négociables

1. **Préserver la vérité architecturale.** Ne jamais modifier une observation, une mesure ou une certitude pour satisfaire plus facilement une contrainte LEGO, géométrique ou logicielle.
2. **Séparer les représentations.** Le pipeline moderne conserve des frontières explicites : preuves/photos → `ArchitecturalSurvey` → `ArchitecturalScene` → représentations LEGO → instructions.
3. **Survey = autorité sémantique ; Scene = autorité métrique.** Le Survey porte inventaire, identité, certitudes et relations ; la Scene reconstruit leur géométrie cohérente.
4. **Les vérités utilisateur sont protégées.** Une donnée `user_provided` ne doit jamais être remplacée silencieusement par une inférence ou une correction automatique.
5. **L'inconnu reste inconnu.** Ne pas remplir une lacune par plausibilité. Distinguer observation, hypothèse, estimation et absence de preuve.
6. **Les mutations sont explicites et traçables.** Un audit diagnostique ; il ne réécrit pas silencieusement son entrée. Une correction est un artefact séparé, journalisé et revalidé.
7. **Le déterministe reste obligatoire.** Une passe IA ne remplace jamais les validateurs, contrats, tests ou garde-fous déterministes existants.
8. **Les boucles IA sont bornées.** Un ré-audit après correction est ciblé sur le voisinage déterministe de la correction ; pas de boucle ouverte correction → audit → correction sans borne explicite.
9. **Les prompts évoluent par couches additives.** Préserver les garde-fous existants et ajouter des régressions avant de condenser ou remplacer un prompt historique.
10. **Préserver l'existant.** Le dépôt est un logiciel vivant : ajouter/étendre avant de supprimer ou réécrire, sauf justification explicite.
11. **Les données privées restent privées.** Ne pas publier dans le dépôt des photos, PDF, Survey ou autres assets privés fournis pour un benchmark ou un cas réel sans autorisation explicite.
12. **Une expérimentation ne devient pas doctrine sans mesure.** Les audits ou nouvelles passes IA doivent démontrer un gain non redondant avant généralisation. `SceneAudit` reste conditionnel à cette preuve.

## Hiérarchie de vérité

- Ces principes et les ADR définissent les règles durables.
- Les contrats et tests exécutables définissent le comportement garanti.
- `main`, les PR/issues et la CI définissent l'état technique courant.
- Les documents de passation indiquent où reprendre mais peuvent vieillir ; ils ne doivent jamais l'emporter sur l'état réel du dépôt.

Pour comprendre pourquoi une règle existe, consulter `docs/DECISIONS.md`. Pour reprendre le travail, commencer par `AI_START_HERE.md`.
