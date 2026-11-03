# Recette V0.8.0–V0.8.1

## Vérifications automatiques

- Reprise et conservation de la suite de V0.7.4 (alignement, PAGE/ALTO, ordre des pages, absence confirmée, projet JSON, export Varians).
- Création minimale et sauvegarde de projet avec pivot, changement de pivot sans modifier les sessions.
- Import d'images triées naturellement ; réimport identique sans doubles sources, identifiants stables.
- Import de PAGE-XML valide, refus global en cas de XML non pris en charge ; import TEI par référence sans alignement fictif.
- Manifest IIIF indisponible : URL conservée pour consultation ultérieure.
- Associations par nom / référence de PAGE, par rang naturel sous conditions, sans hypothèse ordinale sur sous-ensemble IIIF.
- Refus non destructif en cas de pages de nombres différents, source XML déjà associée, double affectation ou prévisualisation périmée.
- Association image/XML et ordre manuel inchangés après modification du témoin et réouverture du projet.
- Catalogues FR/EN : mêmes clés et paramètres.
- Régression sur le projet documentaire Mu–F–A fourni pendant le développement : modification du seul libellé du témoin Mu, sessions physiques inchangées et JSON des alignements identiques avant/après.

**249 tests réussis ; 8 modules/tests Qt ignorés en absence de PySide6 dans cet environnement.**

**Tests de performance exploratoires (hors interface)** : 100 images locales et 100 PAGE-XML synthétiques, import + proposition + application d'associations en environ 0,25 s dans cet environnement. C'est une mesure ponctuelle et non une promesse pour de gros XML ou des téléchargements IIIF.

## Essais graphiques encore nécessaires

1. Démarrer depuis Spyder ; vérifier le lancement isolé et l'absence de crash sur plusieurs ouvertures.
2. Créer un projet neuf, choisir son fichier `.vsynch` et annuler les dialogues pour vérifier l'absence de remplacement du projet actuel.
3. Ajouter un témoin minimal, puis cliquer sur une ligne de l'inventaire pour ouvrir sa fiche.
4. Importer 4 images et 4 PAGE avec noms homologues, visualiser les propositions, corriger une paire et appliquer.
5. Importer une série aux **noms différents mais rangs correspondants**, vérifier les miniatures et la confirmation supplémentaire pour l'ordre naturel.
6. Importer 4 images et 3 XML et vérifier l'absence de couplage ordinal aveugle.
7. Charger un Manifest IIIF de centaines de Canvas : aucun index global n'est supposé, et les références précédemment associées restent correctes.
8. Vérifier les boutons et messages FR et EN, la possibilité de défiler dans la fiche de témoin sur écran de faible hauteur.
9. Ouvrir un projet de travail déjà synchronisé ; comparer la navigation et l'export `validated/` / `working/` avant/après ajout d'une ressource.

Le bilan final des essais Windows/PySide6 ne peut être affirmé sans exécution sur la machine de test de l'utilisateur.
