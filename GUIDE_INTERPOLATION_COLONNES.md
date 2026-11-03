# Synchroniser les colonnes avec deux ancrages — V0.6.7

## Usage

1. Dans **3 · Synchronisation**, ouvrir l'alignement visuel des lignes ALTO des deux manuscrits.
2. Dans chacun des deux manuscrits, choisir le même passage / la même colonne.
3. Associer manuellement la **première ligne** de chaque colonne, puis la **dernière ligne** correspondante (elles sont enregistrées comme validées).
4. Cliquer sur **Compléter entre ancrages (géométrie)**. Le moteur explore l'espace compris entre ces lignes et propose des groupes monotones d'éléments ALTO.
5. Lire l'indication du **nombre de lignes proposées par témoin** dans la prévisualisation. Cocher/décocher les propositions et enregistrer les choix.
6. Choisir le filtre **Synchronisations automatiques à vérifier**, puis cliquer sur les lignes pour contrôler visuellement leurs correspondantes (repérage rose dans le second manuscrit).
7. Valider les groupes corrects et sauvegarder le fichier `.vsynch`.

## Ce que fait le calcul

- Utilise la position des rectangles des lignes sur l'image ; il n'a pas besoin de HTR.
- Cherche des lignes dans la **même colonne** géométrique que les deux ancrages, même si le document ALTO a mélangé les colonnes ou légèrement inversé certaines lignes.
- Classe les lignes selon leurs centres verticaux, sans changer leur ordre ou leurs identifiants dans le document source.
- Propose des regroupements 1↔1, 1↔n, n↔1, parfois n↔m lorsque les manuscrits présentent des coupures de lignes différentes.
- Utilise une HTR de bonne ressemblance comme indice très secondaire, jamais comme preuve suffisante.
- Protège toujours les relations **manuelles et validées**. Depuis V0.6.9, les **propositions automatiques incertaines** ne sont plus considérées comme des ancrages définitifs : elles peuvent être recalculées après prévisualisation et confirmation explicite. Une ancienne proposition n’est remplacée que si toutes ses lignes, sur les deux témoins, figurent dans les nouvelles propositions sélectionnées.

## Limites et précautions scientifiques

Une proximité verticale entre deux manuscrits ne garantit jamais l'identité de leur contenu. Si le texte présente des omissions, ajouts, rubriques, gloses, changements de disposition ou transpositions, les propositions peuvent être inexactes. Toutes les interpolations sont enregistrées avec `origin=interpolated-geometry` et `state=uncertain`.

Le moteur s'arrête devant des limites de pages, des colonnes non identifiables, des liens existants contradictoires ou des groupes de taille très déséquilibrée. Aucun saut textuel n'est automatiquement interprété comme une absence. Les zones encore non associées restent visibles grâce au filtre « Lignes non synchronisées ».

## Conservation des données

La V0.6.7 ne modifie ni les fichiers ALTO, ni les images locales, ni les Manifests IIIF, ni les liens validés. Les sessions V0.6.6 restent lisibles dans le même format `.vsynch`.

## Tests

`PYTHONPATH=. python -m pytest -q` à la racine des sources (sur Windows, `python -m pytest -q` convient habituellement).

Les tests de logique fonctionnent sans PySide6. Les tests d'interface Qt, ignorés dans l'environnement de construction, doivent être validés sur le poste Windows/Spyder.


## Correctif V0.6.9 — « Aucune correspondance supplémentaire proposée »

Sur V0.6.7, après un premier essai « Compléter entre ancrages », les suggestions enregistrées restaient **incertaines**. Au second essai, le moteur les traitait néanmoins comme des barrières : il reconnaissait les colonnes, mais les petits intervalles libres ne lui laissaient plus rien à proposer.

V0.6.9 sépare maintenant **ancrages réellement protégés** (humains/validés) et **suggestions automatiques révisables**. Le recalcul peut traverser ces dernières, reconstruire une proposition d’alignement pour la colonne entière, puis laisser le chercheur décider des remplacements.

**Précaution :** sauvegarder le projet original avant l’essai. La prévisualisation ne modifie pas les liens. Après confirmation, seules les propositions automatiques incertaines dont toutes les lignes sont couvertes par la nouvelle sélection peuvent être remplacées. Une sélection incomplète peut donc aboutir à des groupes ignorés plutôt qu’à une suppression dangereuse. Les liens manuels et validés sont strictement conservés.
