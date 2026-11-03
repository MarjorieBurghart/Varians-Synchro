# Addendum V0.8.4.1 — Aperçu unique

- À l'ouverture, une seule carte doit exister et présenter la ligne TEI 1.
- Sélectionner une ligne TEI dans la liste doit remplacer l'image courante (et non ajouter un troisième panneau).
- « Début » et « Fin » doivent changer la sélection et l'aperçu.
- Filtrer le texte ne doit pas provoquer de multiples requêtes IIIF ; cliquer sur un résultat met à jour l'image.
- Aucun aperçu de la fin n'est téléchargé à l'ouverture ; vérifier que la validation alerte si les deux extrémités n'ont pas été chargées pour vérification.
- Vérifier les états « chargement », « indisponible », les recadrages polygonaux et la navigation dans le visualiseur.

**Statut :** la recette graphique PySide6 requiert un essai sur Windows ; les tests de non-régression sans Qt ont été exécutés dans l'environnement de construction.

---

# Recette V0.8.4 — Contrôle visuel et recherche TEI

## Commande

Depuis le dossier extrait :

```bash
python -m pytest -q
```

## Tests automatisés

- Conservation et récupération des premières et dernières lignes TEI, même sur plusieurs folios.
- Recadrage de ligne ALTO/PAGE en conservant le polygone source ; marges et limites de page.
- Projection entre la résolution d'un Canvas IIIF et les dimensions du fichier XML.
- Syntaxe de requête régionale pour IIIF v2 et IIIF v3 ; chemin de repli sans service IIIF.
- Vérification de l'empreinte d'une ligne physique avant sa prévisualisation.
- Texte TEI exposé uniquement à partir d'une liaison courante et validée ; refus si la TEI a changé.
- Sauvegarde et réouverture d'un `.vsynch` avec liaison TEI, puis consultation inchangée.
- Tests de non-régression : moteurs physique/textuel, projet, imports, rapprochement, export.

## Essais graphiques à réaliser sur Windows/Spyder

1. Vérifier l'affichage d'un **seul** aperçu à la fois, d'abord la première ligne puis la dernière après clic sur « Fin ».
2. Rechercher une expression dans la liste des lignes TEI ; sélectionner un résultat intermédiaire et vérifier la bonne image.
3. Cliquer sur « Voir dans le visualiseur… » pour chaque extrémité ; le zoom doit porter sur la ligne correcte.
4. Sur un fichier PAGE à polygone incliné, vérifier que l'outline suit réellement le contour.
5. Pour un Manifest IIIF v2/v3, vérifier qu'une région est demandée uniquement pour la ligne sélectionnée (et non toutes les extrémités ni tout le Manifest).
6. Désactiver le réseau, ouvrir le dialogue et vérifier les erreurs non bloquantes d'aperçu + confirmation supplémentaire.
7. Dans la synchronisation Mu–F, ouvrir « Texte TEI » sur Mu, chercher une chaîne TEI et contrôler le folio/la ligne sur l'image.
8. Modifier la TEI source après liaison et rouvrir le dialogue : la liaison doit être signalée comme périmée et aucune ancienne ligne TEI ne doit apparaître comme courante dans le visualiseur de paires.
9. Enregistrer et rouvrir un projet existant contenant des liaisons intertémoins validées ; les alignements ne doivent pas changer.

**La concordance exacte des extrémités reste une décision humaine.** Une égalité de nombres de lignes et un contour correct ne certifient pas chaque correspondance intermédiaire.
