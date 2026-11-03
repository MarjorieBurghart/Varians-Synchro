# Recette V0.8.2 + V0.8.3

- Suite non graphique (lancer depuis la racine) : `python -m pytest -q`.
- Extraction TEI d'un seul témoin par `@edRef`, y compris `<hi>`, `<choice>`, `<app>`, `<lem wit>`, `<rdg wit>`, sans mélange de lectures.
- Contrôle TEI ↔ lignes physiques actives, exclusion des lignes hors périmètre, liaison sur plusieurs folios, prévisualisation avant confirmation.
- Refus de liaison si effectifs différents ou apparat ambigu ; vérification de l'état périmé après modification du fichier, de l'ordre ou des exclusions.
- Réanalyse explicite de la source et archivage de l'ancienne liaison ; sauvegarde/réouverture du `.vsynch`.
- Non-régression du moteur V0.7.4, de l'association des images PAGE/ALTO et des exports JSON vers Varians.
- Les tests PySide6 sont facultatifs et ignorés lorsqu'aucun Qt n'est installé. Vérifier **sur Windows/Spyder** les deux nouvelles fenêtres, la sélection multifolio et l'annulation d'un périmètre provisoire.

Les tests unitaires n'établissent pas l'exactitude philologique de toutes les variantes d'une édition TEI réelle. Vérifier sur les éditions critiques qui seront importées et adapter le traitement des cas éditoriaux non prévus plutôt que de leur attribuer une lecture arbitraire.
