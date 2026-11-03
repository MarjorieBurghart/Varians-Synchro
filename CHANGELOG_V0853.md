# Varians-Synchro V0.8.5.3 — Registre des images IIIF HD

Base : V0.8.5.2. Moteur d'alignement V0.7.4, schéma JSON des synchronisations Varians et algorithme de lecture TEI conservés.

## Nouveautés

- Conservation par témoin dans `.vsynch` des lots HD téléchargés : emplacement du dossier, nom des JPEG, identifiant Canvas, URL IIIF, taille et SHA-256.
- Rattachement manuel des téléchargements V0.8.5.1/V0.8.5.2 déjà présents, via `images.json` ; sans téléchargement réseau.
- Exports Varians incluant les **copies de travail IIIF locales uniquement lorsque tous les Canvas associés à une segmentation ALTO/PAGE sont couverts pour ce témoin**.
- Copie sous `iiif/local/<sigle>/` et index conforme au lecteur local Varians 0.8.x ; cache de Manifest reconstitué à partir du catalogue de Canvas déjà importé.
- Échec de couverture : export IIIF classique (sans `localCopy`), avec indication des Canvas manquants dans le rapport ; autres témoins non affectés.
- Interface de gestion des pages : groupes distincts « Copies HD IIIF » et « Traitement HTR externe » ; aide et infobulles FR/EN.
- Fin de téléchargement : ne confond pas un lot publié avec une erreur de rattachement au projet ; propose alors l'import manuel du `images.json`.

## Compatibilité / limites

- `hd_downloads` est une propriété **facultative** du témoin ; les `.vsynch` anciens s'ouvrent sans conversion.
- Les JPEG restent dans leur dossier d'origine jusqu'à l'export Varians ; enregistrer le `.vsynch` après rattachement.
- L'export de projet Varians a été contrôlé contre le lecteur IIIF local de **Varians V0.8.5.6**. La version actuelle de Varians doit être testée sous Windows.
- Les tests graphiques Qt ne peuvent pas être exécutés dans le présent environnement ; voir `TESTS_V0853.md`.
