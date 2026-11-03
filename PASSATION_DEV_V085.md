# Note de passation technique — Varians-Synchro V0.8.5

## Objet et invariants

Outil autonome Python/PySide6 d'alignement **physique** de témoins à partir d'images locales/IIIF et de segmentation ALTO/PAGE. Il ne modifie pas les sources TEI/ALTO/PAGE. Il exporte deux jeux d'alignements (`validated`/`working`) au format `tei-manuscript-alignment`, avec `base_keys` vers le témoin pivot technique.

Le moteur validé de V0.7.4 estime la progression des textes dans des **suites continues de lignes** entre repères homologues. Ne pas remplacer par des heuristiques fondées sur la géométrie d'une page isolée. Les correspondances peuvent traverser plusieurs folios ; ne jamais détruire des groupes manuels/validés lors d'un recalcul automatique.

## Structure

- `core.py` : inventaire, import ALTO/PAGE, gestion des témoins, lecture/sauvegarde `.vsynch` (version de projet sur disque = 1, version du logiciel = 0.8.5).
- `resource_workflow.py`, `bulk_binding.py`, `page_management.py`, `page_order.py` : import et associations image/segmentation, gestion de l'ordre physique.
- `reading_stream.py`, `textual_progress.py`, `physical_alignment.py`, `selection_policy.py`, `overlay_selection.py` : moteur de progression et décisions éditoriales, sélections.
- `tei_binding.py`, `tei_visual.py` : extraction TEI filtrée par `@edRef` et `@wit`, liaison aux lignes physiques, recadrage et affichage.
- `viewer.py`, `guided_ui.py`, `gui.py` : interface PySide6 ; `run.py`, `spyder_launch.py`, `start_isolated.py` : lancement isolé.
- `varians_export.py` : sérialisation vers Varians, intégrité des `base_keys`, écriture groupée et atomique des exports.
- `validation.py`, `audit_vsynch.py`, `recette_v085.py` : contrôles lecture seule sans Qt.
- `i18n/fr.xml`, `i18n/en.xml` : traductions XML externes, placeholder sets vérifiés à l'import.

## État persistant

- `witnesses[]` contiennent pages, sources d'images/segmentations, lignes ignorées.
- `pair_sessions[]` contient les liens physiques explicites : états validés/incertains, groupes correspondance et absence. Aucun lien transitif F↔A n'est inventé via Mu.
- `text_resources[]` inclut les TEI et liaisons TEI↔physique, distinctes des groupes entre témoins. Les anciennes ressources TXT/PIVOT sont encore conservées dans les projets historiques, mais aucun nouvel import TXT n'est offert.
- `pivot_witness_id` est le témoin de référence pour `base_keys`. Ne pas l'assimiler nécessairement à la TEI.
- `save_project` écrit `.vsynch` atomiquement et conserve la version précédente en `.vsynch.bak` ; `load_project` migre des valeurs anciennes **en mémoire seulement**.

## Pièges connus

- IIIF : de grands Manifests peuvent contenir 469 Canvas avec seulement cinq XML de segmentation ; ne jamais dupliquer silencieusement les associations ou exiger des XML pour tous les Canvas.
- Les folios et identifiants de pages doivent rester stables lors d'un réordonnancement.
- Les `<lb>` TEI doivent être explicitement attribués au bon `@edRef`; en présence d'un apparat `<app>` on ne concatène pas les lectures non attribuées au témoin.
- Après changement de TEI, des lignes physiques, ou du périmètre, la liaison doit passer en état « à revérifier », pas être reconstruite silencieusement.
- Une sélection simple remplace la sélection du témoin **sur tous les folios** ; Ctrl ajoute/retire, Maj étend une plage ; les correspondances dans l'autre témoin sont un surlignage non sélectionné.
- `gui.py` est le lanceur PySide6 utilisé ; les anciens modules géométriques gardent des parcours accessibles, donc ne pas les éliminer sans audit d'appels.

## Recette et travaux encore nécessaires

Voir `RAPPORT_RECETTE_V085.md`. Au terme de ce lot : 294 tests automatisés réussis, 11 tests Qt ignorés. Les fichiers `test081.vsynch` et `projetTest.vsynch` ont été audités sans modification. Il faut encore lancer le programme sur Windows avec PySide6 et réaliser un import JSON dans la version la plus récente de Varians. Les avertissements de repères dans `projetTest` demandent une décision éditoriale humaine.
