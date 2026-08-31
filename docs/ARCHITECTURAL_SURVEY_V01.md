# ArchitecturalSurvey v0.1

Boldüngo / BrickHouse sépare **ce que les photos montrent**, **ce que le bâtiment est géométriquement** et **comment LEGO peut le représenter**.

## Pipeline

1. Photos + faits utilisateur
2. `ArchitecturalSurvey v0.1` — évidence et observations sémantiques
3. Fusion / raisonnement architectural
4. `ArchitecturalScene v0.2` — géométrie cohérente du bâtiment et du site
5. Politique d’approximation LEGO
6. `BrickModel` / plans / export

Invariant : une simplification ultérieure ne réécrit jamais la compréhension antérieure.

## Autorité du Survey

Le Survey est l’autorité pour :
- inventaire des objets observés ;
- IDs stables ;
- façade/côté lorsque prouvé ;
- certitude d’existence ;
- attributs sémantiques et leur certitude ;
- relations topologiques observées ;
- provenance/evidence.

Il n’est pas l’autorité métrique finale. Une existence `certain` n’autorise pas l’invention de dimensions ou coordonnées certaines.

## Repère canonique

La façade avant canonique fixe le repère :
- `x` : gauche → droite lorsqu’on regarde la façade avant depuis l’extérieur ;
- `y` : avant → arrière ;
- `z` : bas → haut.

Le mapping gauche/droite d’une image est une donnée d’évidence qui doit survivre aux transformations. Le renderer ou la Scene ne doit jamais l’inverser silencieusement.

## Observation vs interprétation vs représentation

Une observation peut mentionner salissure, humidité ou vieillissement pour aider à comprendre terrain, exposition ou continuité de matière. Cela ne signifie pas que le modèle LEGO doit reproduire ces traces.

Les couches de surface séparent donc matériau/couleur nominale, finition et weathering observé. La politique par défaut conserve l’architecture nominale et n’imite pas les salissures temporaires.

## Ouvertures

Les ouvertures sont des composants architecturaux, pas de simples trous. Le Survey peut conserver notamment :
- type d’ouverture ;
- cadre/matériau/couleur ;
- nombre de vantaux/meneaux ;
- vitrage ;
- appui ;
- encadrement décoratif ;
- ordre/rang qualitatif ;
- preuve multi-vues.

Les comptes et identités priment sur une métrique approximative. Une grande ouverture simple ne doit pas devenir plusieurs ouvertures uniquement pour faciliter la construction LEGO.

## Certitude

Chaque observation utilise :
- `certain` — directement visible ou explicitement confirmé ;
- `plausible` — soutenu mais non unique ;
- `unproven` — hypothèse à ne pas promouvoir sans nouvelle preuve.

La certitude de l’objet et la certitude de ses attributs doivent rester séparées.

## Terrain qualitatif

Le terrain est une observation architecturale/site à part entière. Une pente clairement visible doit survivre au Survey même si son amplitude numérique est inconnue.

Règles :
- auditer chaque façade pertinente ;
- conserver une pente visible avec une observation `kind:"terrain"` ;
- conserver la direction qualitative si elle est prouvée ;
- ne jamais inventer angle, pourcentage ou différence d’altitude ;
- l’absence de métrique n’autorise pas à effacer une pente certaine ;
- les zones occultées restent explicitement inconnues plutôt que complétées.

L’audit actuellement injecté au handoff est `frontend/brickhouse-survey-terrain-audit-v29.txt`.

## Enveloppe et topologie

Si le bâtiment cible est certainement visible, le Survey doit posséder une ancre sémantique stable `kind:"building_boundary"`. Cette observation est non métrique : elle identifie l’enveloppe, elle n’invente ni profondeur ni hauteur.

Pour une `platform` ou un `stair` certain :
- si le raccord à l’enveloppe est visiblement certain, conserver une relation `connects_to` vers le `building_boundary` ;
- si le raccord à une autre primitive est certain, conserver la relation correspondante ;
- une relation `supports` ne remplace pas `connects_to` lorsqu’elles décrivent deux faits physiques différents ;
- ne jamais créer une relation certaine pour fermer une zone cachée.

L’audit actuellement injecté au handoff est `frontend/brickhouse-survey-topology-audit-v30.txt`.

## Discipline de génération Photos → Survey

Le prompt historique `frontend/brickhouse-survey-prompt.txt` reste volontairement conservé. Les garde-fous récents sont superposés de façon additive via les wrappers versionnés du frontend.

Ce choix est architectural : une tentative de condenser le prompt historique lors de l’ajout du terrain avait supprimé des protections existantes et fait échouer les régressions. Les évolutions futures doivent donc préserver les règles déjà prouvées et ajouter des audits génériques ciblés.

## Benchmark réel

Le benchmark principal conserve les 5 photos originales de la maison test. Il sert à découvrir des défauts génériques du contrat, jamais à encoder des valeurs propres à cette maison comme défauts globaux.

Le dernier run neutre avant l’audit topologique a démontré que le terrain droit pouvait être conservé qualitativement sans amplitude inventée, puis a révélé l’absence de `building_boundary` et de relations `connects_to`. Ces défauts ont motivé les audits v2.9/v3.0 et leurs tests.

Pour l’état opérationnel exact et les prochains contrôles, voir `docs/CURRENT_PROJECT_STATE.md`.
