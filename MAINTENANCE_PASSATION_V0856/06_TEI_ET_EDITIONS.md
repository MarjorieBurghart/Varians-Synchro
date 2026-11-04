# Ressources TEI : liaison explicite, non création automatique

## Sources et propriété

Varians-Synchro **référence une TEI préexistante**, ne la transforme pas en édition « reconstruite » à partir du HTR et ne modifie pas le fichier original. `core.import_tei` appelle `tei_binding.extract_witness_tei` pour extraire les lignes attribuées à **un témoin donné**. Le champ `text_resources[]` garde chemin, hash SHA-256, sigle, diagnostics et statut. Une même opération ne doit pas fusionner les lectures de différents témoins.

## Traitement XML

`tei_binding.py` sélectionne le texte à partir de la structure TEI, traite `<pb>` et `<lb>` avec `@edRef`, identifie les lectures `<rdg>`/`<lem>` par `@wit`, prend en charge `<choice>` via une préférence explicite (`reg`, `corr`, `expan`, `orig`, `sic`, `abbr`) et émet des diagnostics quand un `<app>` n'offre pas une seule lecture exploitable. Les `<lb/>` sans `@edRef` sont signalés et exclus pour ce témoin. L'extraction porte sur une attribution de témoin ; ce n'est pas un parseur universel de toutes les variantes TEI possibles.

Exemple de principe (pas une édition complète) :

```xml
<pb n="4r" edRef="#Mu" facs="#canvas_4r"/>
<lb edRef="#Mu" xml:id="lb_Mu_4r_1"/>
<app><lem wit="#Mu">forme A</lem><rdg wit="#F">forme B</rdg></app>
```

Conserver espaces de noms et attributs d'identifiants. Une ambiguïté de choix de lecture est une **erreur de liaison**, pas un motif de sélectionner arbitrairement la première branche.

## Liaison TEI ↔ ligne physique

1. `preview_tei_binding(project, wid, rid)` ré-extrait **la source sur disque**, construit le flux des lignes physiques **actives**, et vérifie le nombre de `<lb/>` et de lignes, les diagnostics et le SHA-256 au moment de l'import.
2. La proposition actuelle apparie **par position** après cadrage explicite ; elle ne prouve pas que les textes sont équivalents. Une égalité de cardinalités est nécessaire mais **pas suffisante** pour une validation scientifique.
3. `apply_tei_binding` recalcule la prévisualisation et compare sa `signature` ; une signature périmée est refusée ; une liaison déjà existante requiert `replace=True` explicite.
4. `refresh_tei_source` conserve l'ancienne liaison dans `tei_binding_history` si l'utilisateur consent à son invalidation.
5. `tei_binding_status` vérifie la fraicheur de la TEI, de la segmentation, de l'ordre et du périmètre ; `linked_tei_texts` renvoie du texte **seulement** quand une unique TEI liée est actuellement valide pour ce témoin.

`tei_visual.py` produit des descripteurs de recadrage et des transformations d'images pour permettre une vérification visuelle début/fin et intermédiaire. Ces aperçus ne transforment pas une liaison en attestation automatique.

## Cas à ne pas automatiser

- Édition sans `<lb/>` attribués à un témoin, variantes sans lecture unique, identifiants de `<lb/>` dupliqués, changement de TEI après import.
- Ligne physique nouvellement exclue ou réordonnée : réexiger une prévisualisation.
- Plusieurs ressources TEI concurrentes : `linked_tei_texts` ne les fusionne pas ; décider explicitement de l'édition de référence.
- Pivot sans TEI : **permet** un export de correspondances physiques vers des JSON et un projet Varians complet via `varians_project_export`, avec la TEI vide de Varians ; les `<pb/>` et `<lb/>` du pivot y sont préparés par Varians (« Paramètres du projet »). Plusieurs TEI pour le pivot : export refusé, il faut en choisir une.

## Pour l'héritage et la refonte future

Les sessions historiques dans `alignment_sessions` sont conservées sans les convertir automatiquement en `pair_sessions`. Le support d'un ensemble multi-fichiers TEI ou de plusieurs éditions autonomes relève d'une **évolution future de l'écosystème Varians** : ne pas affirmer qu'un tel format est actuellement géré par l'exporteur de Synchro. Toute évolution doit préserver le parcours simple à un fichier et une image.

**Tests clés** : `tests/test_tei_binding_083.py`, `test_tei_visual_084.py`, `test_tei_visual_gui_qt_084.py`, `test_varians_export.py`, `test_varians_export_audit.py`.
