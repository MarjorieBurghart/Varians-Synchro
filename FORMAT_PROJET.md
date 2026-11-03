## Addendum V0.8.1 — pivot et TEI en attente

`pivot_witness_id`: champ optionnel à la racine, contenant l'ID stable d'un témoin existant ou `null` (les projets antérieurs sont chargés sans le réécrire immédiatement). Le premier témoin ajouté via la nouvelle fiche devient pivot par défaut. Un changement de pivot ne modifie pas les associations physiques déjà enregistrées.

Une TEI nouvellement importée en V0.8.1 est une entrée de `text_resources`, de type `tei`, avec `witness_id`, `status: tei_unaligned`, `source_sha256` et `lines: []`. Ce `lines: []` ne signifie pas qu'il n'y a aucun `<lb/>` dans le fichier ; la résolution est différée à la phase V0.8.2–V0.8.3.

---

# Format des projets `.vsynch` en V0.6.0

Le fichier est un JSON UTF-8 de `format: "varians-synchro-project"`, `version: 1` (inchangé depuis V0.5.x).

Les champs principaux : `name`, `created`, `witnesses`, `text_resources`, `alignment_sessions`, `pair_sessions`, `workflow_preference`.

- `workflow_preference` : `alto_only`, `pivot` ou `tei` ; c'est une préférence d'interface et non une limitation imposée au projet.
- `witnesses[]` : identité, sources images (`iiif`/`local`), ALTO et pages. La géométrie est sauvegardée dans les ALTO importés. Les pages associées retiennent les Canvas IIIF ou chemins locaux.
- `text_resources[]` : zéro ou plusieurs TEI et TXT/MD facultatifs.
- `alignment_sessions[]` : sessions historiques TEI–ALTO conservées telles quelles.
- `pair_sessions[]` : nouvelles sessions physiques non éditoriales.

Exemple simplifié (identifiants illustratifs) :

```json
{
  "pair_sessions": [{
    "id": "uuid-de-session",
    "kind": "physical-pair",
    "reference_witness_id": "A",
    "target_witness_id": "B",
    "links": [{
      "id": "uuid-du-lien",
      "reference_ids": ["urn:vsynch:line:uuid-A-1"],
      "target_ids": ["urn:vsynch:line:uuid-B-1", "urn:vsynch:line:uuid-B-2"],
      "fingerprints": {"urn:vsynch:line:uuid-A-1": "sha256", "urn:vsynch:line:uuid-B-1": "sha256"},
      "kind": "correspondence",
      "state": "validated",
      "origin": "manual"
    }]
  }]
}
```

Pour une absence confirmée, `kind = "absence"` et **exactement l'un** de `reference_ids[]` ou `target_ids[]` est vide. L'absence ne doit pas être confondue avec une ligne non résolue.

Les nouvelles sessions ne sont PAS des JSON `tei-manuscript-alignment` consommables directement par Varians. Le transfert sera assuré après rattachement à une TEI réelle ; aucun export trompeur ne doit être produit.


## Extension V0.6.11 — périmètre du témoin

Le nœud `witnesses[]` admet une propriété facultative :

```json
{
  "id": "A",
  "ignored_line_ids": ["urn:vsynch:line:identifiant-stable"]
}
```

L'absence de cette propriété équivaut à une liste vide. Ces identifiants sont issus de `physical_alignment.line_uid(witness_id, page_id, ordinal)` ; le stockage ne dépend ni du témoin actuellement affiché en face, ni de la session de comparaison. Il ne signifie pas une omission ou une absence attestée.

Une ligne marquée ignorée ne peut entrer dans une association ALTO–ALTO nouvelle avant réintégration. Les lignes déjà liées sont dissociées (avec confirmation préalable, dans toutes les paires concernées) avant que le marquage soit enregistré. Les liens et données sources historiques ne sont pas édités silencieusement.


## Champ facultatif V0.6.12

Une `TextLine` importée peut contenir `"polygon": [[x1, y1], [x2, y2], ...]` issu de `Shape/Polygon/POINTS`. Ces valeurs sont les coordonnées ALTO d'origine et **ne remplacent pas** la `bbox`. L'absence de `polygon` dans un projet plus ancien est normale : la géométrie peut être récupérée à la volée dans le fichier source pour l'affichage, sans enregistrer de migration implicite. Les identifiants physiques et leurs empreintes sont inchangés.

## Ajout V0.6.13 : PAGE-XML

Une entrée historique `witness.alto_sources[]` peut maintenant inclure `kind: "page"`, son chemin, empreinte SHA-256 et la collection `pages[]`. Dans `pages[].lines[]`, les objets `bbox` existent toujours pour les algorithmes, et `polygon` contient les véritables points de contour PAGE `[[x,y], ...]`. Une entrée ALTO existante sans champ `kind` est assimilée à `alto`.

Les entrées `witness.pages[].alto_binding` continuent à référencer `source_id` et `page_index`, que la source liée soit ALTO ou PAGE ; ces noms historiques ne doivent PAS être supprimés pendant une migration. Les correspondances de lignes `pair_sessions` sont inchangées.


### Complément géométrique des lignes résiduelles (V0.6.14)

Les groupes étendus conservent leur identifiant, leur état `uncertain` et une origine `interpolated-residual`. L'objet `evidence` peut comporter une liste `residual_extensions` qui conserve la date, les identifiants ajoutés et l'origine précédente. Aucune nouvelle rubrique obligatoire n'est ajoutée au format `.vsynch` ; les versions précédentes demeurent lisibles.


## V0.8.5.3 — Lots IIIF HD liés au témoin (facultatif)

Une entrée `witnesses[]` peut contenir `hd_downloads: [{directory, pages:[{canvas_id,file,iiif_image_url,size_bytes,sha256}]}]`. `directory` est le chemin absolu du dossier où `images.json` et les JPEG ont été publiés. Plusieurs lots peuvent coexister ; il n'y a ni image ni association ALTO/PAGE ajoutée au registre des pages. Un projet antérieur, sans `hd_downloads`, est équivalent à un témoin sans copie de travail référencée.

L'export vers Varians n'insère des copies locales que pour un témoin dont **toutes** les pages `image_kind=iiif` portant un `alto_binding` valide dans le modèle disposent de copies HD actuelles, identifiées par leur Canvas et leur URL et vérifiées par SHA-256. Les images externes manquantes ou altérées interdisent les copies locales pour **ce témoin uniquement** ; les autres témoins et les JSON de synchronisation sont conservés.
