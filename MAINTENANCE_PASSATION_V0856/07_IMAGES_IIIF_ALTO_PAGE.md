# Acquisition documentaire, images et géométrie

## Ingestion et liaison

- Images locales / IIIF : `core.add_image_source` stocke la référence ; `imaging.parse_manifest`, `fetch_manifest` et `create_pages` établissent les pages documentaires et leurs métadonnées. IIIF Presentation v2/v3 est géré ; les miniatures/rendus HD font appel au serveur distant et peuvent être indisponibles. La présence d'un Canvas dans le Manifest ne signifie pas qu'il possède un XML OCR, ni qu'il a été sélectionné.
- XML : `core.inspect_line_source` distingue ALTO (`alto`) et PAGE (`PcGts`) par **élément racine XML**, indépendamment de l'extension du fichier. `core.inspect_alto` et `page_xml.inspect_page_xml` conservent rectangles, textes et, le cas échéant, polygones et informations d'ordre.
- Liaison : `bulk_binding.propose_bindings` examine notamment les ressemblances de noms ; `imaging.bind_line_source` / `bind_alto` lient un **index de page XML** à une page documentaire avec une référence explicite. Prévoir toujours une vérification humaine avant une affectation équivoque.
- Géométrie : `alto_geometry.py` extrait les polygones ALTO s'ils existent ; PAGE fournit polygones de points. Le rectangle `bbox` est conservé pour les algorithmes et le contour natif est préféré pour certains surlignages (`viewer.py`, `overlay_selection.py`). Ne pas remplacer un polygone par sa boîte englobante dans les rendus.

## Images IIIF téléchargées en haute résolution

`imaging.export_iiif_hd_images` fournit les copies, avec reçu `images.json` ; `hd_registry.inspect_hd_folder` valide le reçu, l'identité de chaque Canvas, l'URL d'image IIIF, le nom local sûr, la signature JPEG, la taille et l'empreinte. Le registre `witnesses[].hd_downloads[]` conserve des lots de copies **liés au témoin**, sans injecter les images comme pages scientifiques nouvelles.

`hd_registry.local_copy_plan` fixe la règle conservatrice : pour exporter les copies en tant que ressources locales dans Varians, il faut **toutes les pages IIIF de ce témoin dont `alto_binding` est renseigné**, avec une copie actuelle et conforme. Une copie manquante ou altérée désactive l'option **pour le témoin concerné**, pas pour les autres. L'original du Manifest et les URL IIIF sont conservés et restent utilisables.

`varians_project_export` recopie les fichiers éligibles après vérification d'empreinte juste avant la publication ; il construit `iiif/local/<sigle_sûr>/index.json` et, si disponibles, des caches de Manifest. Le cache recréé est un **sous-ensemble sûr des champs connus**, pas une copie canonique de tous les métadonnées du Manifest original.

## Autres ressources HTR

`imaging.export_iiif_htr_zip` fournit des ressources pour HTR, `imaging.import_htr_results` rattache des XML de résultats à l'inventaire. Préserver la distinction entre acquisition de données HTR et enregistrement de copies HD : les deux fonctions ne garantissent pas l'identité des produits ni des droits de réutilisation sur les images.

## Portabilité, réseau et sécurité

- Les chemins de sources dans le `.vsynch` peuvent être **absolus** et devenir invalides après transfert ; ne pas les corriger automatiquement en substituant des fichiers de même nom.
- Les sources HTTP/IIIF peuvent rediriger, demander des authentifications ou échouer temporairement. Tester en conditions réelles, consigner code HTTP, service IIIF et Canvas. Ne jamais interpréter un 429/timeout comme une preuve d'absence de page.
- Conserver les limites de taille et les délais réseau existants (`imaging._http_bytes`). Ne pas faire dépendre l'audit de l'accès réseau.
- Tester séparément ALTO rectangles, ALTO polygones, PAGE polygones, double page, scans non-OCR, source manquante ou transformée.

**Tests clés** : `tests/test_imaging.py`, `test_page_xml_support.py`, `test_alto_polygon_geometry.py`, `test_alto_polygon_qt.py`, `test_hd_registry_0853.py`, `test_hd_completion_0852.py`, `test_resources_081.py`, `test_page_order.py`.
