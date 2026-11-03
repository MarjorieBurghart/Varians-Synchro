# Correctif V0.6.16 : export vers Varians pour TEI à périmètre partiel

## Problème diagnostiqué dans projetTest.vsynch

Dans V0.6.15, l'export incluait les lignes `ignored_line_ids` dans Mu.json, ajoutant `vsynch_ignored=true`. Varians V0.8.5.2 ne traite pas cet indicateur : toutes les lignes de la base sont comptées comme des `<lb/>` obligatoires.

Dans ce projet, Mu possède 332 lignes physiques dont 121 ignorées, donc 211 lignes pertinentes. F possède 282 lignes, dont 41 ignorées, donc 241 lignes pertinentes.

## Correction

- Les lignes ignorées sont **exclues** des tableaux `pages[].lines` à l'export (pour tous les témoins) ; elles restent intactes dans le `.vsynch` original.
- Les numéros physiques `line` restent **inchangés** : sur le folio 2v de Mu, le premier numéro exporté est **41** (et non 1).
- Les `base_keys` de F pointent toujours vers ces numéros physiques inchangés.
- La source des images IIIF exportées contient explicitement l'identifiant de Canvas `image.canvas`, en plus de l'URL d'image et du service IIIF. Les 5 pages utiles ne sont pas remplacées par les centaines de pages hors corpus.
- `validated/` et `working/` restent des ensembles distincts ; le second peut contenir des erreurs d'alignement puisqu'il comprend les propositions non encore validées.

## Limite distincte : TEI partiellement transcrite

Le logiciel Varians V0.8.5.2 vérifie toujours que le nombre de `<lb/>` de sa TEI est égal au nombre de lignes physiques de son JSON de référence. Ce correctif ramène ce nombre de 332 à 211 **pour ce projet**, mais ne résout pas à lui seul la correspondance d'une transcription **incomplète** où l'on ne souhaite pas encore insérer toutes les limites des lignes à venir. Un vrai mécanisme de rattachement explicite des `<lb/>` aux lignes physiques reste nécessaire pour ce mode de travail.

## Utilisation

1. **Sauvegarder** le projet `.vsynch` et la TEI éditée par Varians.
2. Importer le nouvel export `Mu.json` et `F.json` depuis un même ensemble (`validated/` ou `working/`, jamais un mélange).
3. Dans Varians, vérifier que Mu est la base, et que F utilise bien la source d'images IIIF ou le mode **Automatique / à partir des données de synchronisation**.
4. Si le travail IIIF local a été activé, utiliser le correctif Varians séparé dans cette livraison, qui effectue l'association par identifiant de Canvas/service IIIF plutôt que par position dans la liste du Manifest.
5. Ne **pas** supprimer aveuglément 121 balises de la TEI existante : si du texte a déjà été saisi, effectuer une sauvegarde puis conserver les balises associées au texte pertinent ; supprimer uniquement les balises techniques vides et hors périmètre après contrôle.

Le statut `editorial_tei_alignment=NOT_ESTABLISHED` reste présent : une vraie correspondance des `<lb/>` éditoriaux avec les lignes physiques de Mu reste à vérifier.
