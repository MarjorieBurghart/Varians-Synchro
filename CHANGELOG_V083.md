# Varians-Synchro V0.8.2 + V0.8.3

## V0.8.2 — Analyse TEI par témoin
- Extraction stricte des `<lb edRef="#SIGLE"/>` en ordre documentaire.
- Gestion prudente des `<app>/<lem>/<rdg>` et `<choice>` ; les ambiguïtés bloquent la liaison plutôt que de combiner les lectures.
- Les TEI sont inspectées à l'import et conservées sans changement.

## V0.8.3 — Liaison TEI ↔ lignes physiques
- Liaison après exclusion explicite des lignes hors périmètre et vérification d'effectifs égaux.
- Nouvelle fenêtre « Lier la TEI aux lignes ALTO/PAGE… » accessible à la deuxième étape.
- Aperçu des liens, vérification d'empreintes, validation explicite, persistance `.vsynch`.
- Statut « à revérifier » si le fichier TEI, la segmentation, les exclusions ou l'ordre des lignes ont changé.
- Audit global des liaisons TEI, sans altération des associations Mu–F–A ni de l'export JSON pour Varians.
- Catalogues de traduction français et anglais actualisés.

## Restant en V0.8.4
- Afficher les lignes éditées TEI dans les deux vues à la place de la HTR.
- Rechercher dans le texte TEI et naviguer depuis le résultat vers la ligne physique et son correspondant dans l'autre témoin.

Le moteur de progression textuelle V0.7.4, les images locales/IIIF, les polygones ALTO/PAGE et les exports JSON ont été préservés.
