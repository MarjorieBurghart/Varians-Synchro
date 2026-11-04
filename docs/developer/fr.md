> **Passation complète (v0.8.5.6)** : voir le [dossier autonome de maintenance](../../MAINTENANCE_PASSATION_V0856/00_LIRE_EN_PREMIER.md), qui contient les décisions ADR, contrats des données, cartographie AST et procédures de recette. Ce guide de v0.8.5.5 est conservé comme référence historique complémentaire.

# Documentation développeur — Varians-Synchro V0.8.5.5

## 1. Périmètre de reprise

Application autonome PySide6 d’alignement **physique** de témoins. L’édition TEI est une ressource facultative liée aux lignes ALTO/PAGE ; le programme ne produit ni ne modifie une édition critique TEI. Les formats métier enregistrés ne contiennent jamais de texte traduit par l’interface.

## 2. Points d’entrée et environnement

- `run.py` : point d’entrée interactif ; `start_windows.bat` / `start_unix.sh` : scripts d’exécution.
- `start_isolated.py`, `varians_synchro/spyder_launch.py` : lancement en sous-processus lorsque Spyder charge Qt dans son propre noyau.
- `recette_v085.py` et `audit_vsynch.py` : audits hors interface, en lecture seule.
- PySide6 nécessaire à l’interface. Une partie des tests s’exécute sans Qt ; ne pas considérer les `skip` comme des validations GUI.

## 3. Contrats et invariants

1. **Projet `.vsynch`** : JSON versionné par `core.py`. Identifiants de témoins, pages, lignes et Canvas stables. Sauvegarde atomique et `.vsynch.bak`. Une ouverture ne doit jamais écraser le projet avant affectation effective à la fenêtre.
2. **Lignes physiques** : ALTO rectangles, PAGE polygones. Flux de lecture ordonné à travers colonnes et folios ; respecter le réordonnancement humain. Les lignes hors périmètre sont ignorées et non supprimées.
3. **Couples de témoins** : groupes de correspondances n↔m, états validé/incertain et absences explicites propres à la paire. Les correspondances F↔A ne sont pas inférées automatiquement via le pivot Mu.
4. **Moteur V0.7.4** : `reading_stream.py` + `textual_progress.py` ; progression textuelle cumulée entre repères homologues, HTR puis géométrie puis uniforme. Préserver les ancres et groupes manuels/validés lors des recalculs.
5. **TEI** : `<lb edRef="#Mu"/>` et lectures d’apparat résolues par `@wit` ; toute ambiguïté bloquante doit être signalée, jamais fusionnée. Empreintes sur TEI, sources et périmètre ; liaison périmée non réutilisable sans révision.
6. **Export** : `varians_export.py` produit `validated/` et `working/` avec `base_keys` vers le pivot. `varians_project_export.py` prépare un projet Varians ; tester sa compatibilité avec la version actuelle de l’éditeur, au-delà d’une validation XML.
7. **IIIF HD** : `hd_registry.py` maintient `images.json`, Canvas, fichiers, SHA-256. Ne copier les HD locales dans Varians pour un témoin que si tous les Canvas requis avec ALTO/PAGE sont couverts et intègres. Préserver les URL IIIF originales.

## 4. Internationalisation

`i18n.py` charge les catalogues XML `i18n/<lang>.xml` et valide les ensembles de clés et les paramètres de formatage. `tr('clé')` gère l’interface et les messages ; `language_labels()` alimente le sélecteur. L’interface est reconstruite au changement de langue, mais le projet actif ne doit pas être remplacé. Les données éditoriales, identifiants et chemins ne doivent jamais être traduits. En V0.8.5.5, les 244 anciens replis anglais de chacune des langues de/cs/it/ru/ja ont reçu une traduction. Voir `docs/i18n_coverage.json` et `docs/I18N_NATIVE_REVIEW_V0855.md` : la couverture de toutes les clés ne vaut pas validation linguistique native.

## 5. Guide de tests et mises à jour

```bash
python -m compileall -q varians_synchro
PYTHONPATH=. pytest -q
python recette_v085.py projet.vsynch --base Mu --output audit.json
```

Tester impérativement les cas Qt sur Windows avec PySide6 : création/ouverture, sauvegarde, changement de langue, Manifest IIIF de 469 Canvas avec cinq ALTO, annulation des imports, téléchargement à 100 %, nouveau clic simple sur un autre folio, TEI liée puis modifiée, export Varians avec copies HD complètes et incomplètes. Dans les tests de non-régression, comparer les JSON canoniques `validated` et `working` sur `projetTest.vsynch` et `test081.vsynch` avec la version précédente. Ne pas écrire ces originaux.

## 6. Cartographie des modules (extraite du code)

### `__init__.py`

Classes: —. Top-level functions: —.

### `alignment.py`

Classes: —. Top-level functions: base_key, get_base_lines, target_lines, create_session, _indices, add_link, remove_link, export_varians.

### `alto_geometry.py`

Classes: —. Top-level functions: parse_alto_points, _local_name, textline_polygon, _source_geometry, _cached_source_geometry, page_line_polygons, polygon_contains.

### `automatic.py`

Classes: —. Top-level functions: normalize, _concatenate, _free_spans, propose_alignment, apply_proposals.

### `bulk_binding.py`

Classes: —. Top-level functions: _stem, _strong, _page_candidates, _xml_candidates, binding_fingerprint, propose_bindings, binding_selection_conflicts, apply_binding_choices.

### `core.py`

Classes: —. Top-level functions: new_project, _staged_file, save_project, load_project, validate_project, create_witness, add_image_source, add_alto_source, lname, inspect_line_source, add_line_source, inspect_alto, import_tei, inspect_manifest, diagnostic, check_alto_files.

### `correspondence_navigation.py`

Classes: —. Top-level functions: build_pair_navigation_index, combined_counterparts.

### `exceptions.py`

Classes: —. Top-level functions: _digest, _selection, _runs, preview_confirmed_absence, confirm_absence, pair_exception_summary.

### `gui.py`

Classes: —. Top-level functions: main.

### `guided_ui.py`

Classes: —. Top-level functions: make_guided_window.

### `hd_registry.py`

Classes: —. Top-level functions: _sha256, inspect_hd_folder, register_hd_snapshot, register_hd_folder, local_copy_plan, varians_remote_key, varians_offline_index.

### `i18n.py`

Classes: —. Top-level functions: _load_one, _parameters, reload_catalogs, available_languages, language_labels, set_language, get_language, tr, translate_template.

### `imaging.py`

Classes: —. Top-level functions: _http_bytes, _label, _first, parse_manifest, fetch_manifest, create_pages, bind_alto, mapped_alto_page, bind_line_source, mapped_line_page, suggest_alto_bindings, suggest_line_bindings, image_request_url, image_bytes, export_iiif_htr_zip, import_htr_results, iiif_hd_url, export_iiif_hd_images.

### `interpolation.py`

Classes: —. Top-level functions: _bbox, _center_y, _overlap_ratio, _column_interval, _htr_similarity, _partition, _unlinked_segments, _anchor_row, suggest_between_anchors.

### `line_scope.py`

Classes: —. Top-level functions: ignored_ids, linked_scope_conflicts, update_ignored_lines.

### `overlay_filters.py`

Classes: —. Top-level functions: style_for_link, overlay_visible.

### `overlay_selection.py`

Classes: —. Top-level functions: choose_line_at, choose_line_geometry.

### `page_management.py`

Classes: —. Top-level functions: page_ids_in_reading_order, commit_page_order, invert_page_order, move_page_by_id.

### `page_order.py`

Classes: —. Top-level functions: _natural, folio_key, _local_key, ordered_pages.

### `page_xml.py`

Classes: —. Top-level functions: _name, _direct, _line_text, _region_order, _baseline_points, _line_info, inspect_page_xml.

### `physical_alignment.py`

Classes: —. Top-level functions: _now, _hash, line_uid, physical_lines, _witness, create_pair_session, pair_indices, add_pair_link, extend_pair_link, detach_pair_lines, is_revisable_automatic, replace_revisable_pair_proposals, remove_pair_link, set_pair_link_states, pair_progress, verify_pair_sessions, suggest_htr_pair_alignment, apply_pair_proposals.

### `project_state.py`

Classes: ProjectChangeTracker. Top-level functions: project_fingerprint.

### `qt_lifecycle.py`

Classes: —. Top-level functions: launch.

### `rapid_review.py`

Classes: —. Top-level functions: ordered_links, review_counts, pending_ids, following_anchor_interval, verify_before_review, validate_checked, suggestions_for_interval.

### `reading_stream.py`

Classes: ReadingOrderError. Top-level functions: _unique_order, set_page_order, _region, set_region_order, set_line_order, reset_page_line_order, page_regions, reading_stream, anchor_intervals.

### `residual_alignment.py`

Classes: —. Top-level functions: _box, _cy, _overlap, _same_column, _local_pitch, _linked_info, _nearest_group, suggest_residual_extensions, apply_residual_extensions.

### `resource_workflow.py`

Classes: —. Top-level functions: _local_key, _manifest_key, _xml_kind, store_tei_reference, set_project_pivot, resource_summary, apply_witness_draft.

### `review.py`

Classes: —. Top-level functions: configure_session, prepare_proposals, bulk_set_state, session_progress, project_progress.

### `selection_policy.py`

Classes: —. Top-level functions: update_line_selection.

### `spyder_launch.py`

Classes: —. Top-level functions: in_spyder_kernel, isolated_environment, log_directory, launch_isolated.

### `tei_binding.py`

Classes: —. Top-level functions: _local, _refs, _digest, _stamp, extract_witness_tei, _resource, preview_tei_binding, apply_tei_binding, refresh_tei_source, tei_binding_status, linked_tei_texts.

### `tei_visual.py`

Classes: —. Top-level functions: _positive, review_pairs, line_preview_descriptor, fetch_preview_bytes, render_transform.

### `textual_progress.py`

Classes: —. Top-level functions: _chars, _length, _weights, _cumulative, _partition, _method, _segments, suggest_textual_progress.

### `validation.py`

Classes: —. Top-level functions: _item, audit_project.

### `varians_export.py`

Classes: —. Top-level functions: _get_witness, _image_block, _build_witness_cache, _line_fingerprint, _shared_pero_uuid, _safe_same_segmentation_after_format_change, _reference_health, _pair_for_base, make_varians_alignments, inspect_varians_export, verify_export_payloads, export_varians_alignments.

### `varians_project_export.py`

Classes: —. Top-level functions: _varians_safe_id, _source_path, _relative_or_absolute, _cache_varians_manifest, export_varians_project.

### `viewer.py`

Classes: FetchThread, ZoomableGraphicsView, ClickableLine, WitnessLineList, LineImagePanel, PageViewer. Top-level functions: —.

## 7. Points de vigilance pour la maintenance

- Ne pas confondre la sélection d’une ligne d’un témoin avec le surlignage de sa correspondance dans l’autre témoin.
- Ne pas convertir un échec de réseau IIIF en absence définitive de page.
- Toute nouvelle action Qt doit distinguer succès, annulation et échec **à partir du résultat métier** et non de la fermeture d’un dialogue.
- Les téléchargements et les exports de plusieurs fichiers doivent préparer leur résultat en dossier temporaire, puis publier ensemble.
- Les fonctionnalités historiques ne sont retirées qu’après analyse des appels et migration sûre des données anciennes.
- Préserver la terminologie éditoriale dans les traductions ; faire relire les catalogues par des spécialistes des langues et de la critique textuelle.

## 8. Passation recommandée

Lire successivement le [dossier de passation](../../MAINTENANCE_PASSATION_V0856/00_LIRE_EN_PREMIER.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`FORMAT_PROJET.md`](FORMAT_PROJET.md), [`EXPORT_VARIANS.md`](EXPORT_VARIANS.md), le guide utilisateur (`help/fr.html`, F1 dans le logiciel), puis cette cartographie. Rejouer la suite Python et ensuite la recette Qt sur Windows. Garder une copie de la V0.8.5.3 comme référence pour les régressions d’alignement.
