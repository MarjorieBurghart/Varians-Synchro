# Inventaire technique généré automatiquement (code v0.8.5.6)

Génération reproductible : `python tools/generate_module_inventory.py` depuis la racine.
Inspection statique AST : **aucun module applicatif n’est importé ni exécuté**.
Les numéros de ligne sont ceux de **cette livraison uniquement**.

**37 fichiers Python** dans `varians_synchro/` (dont `__init__.py`).

## `varians_synchro/__init__.py` (1 lignes)
**Dépendances internes observées** : `core`
Pas de fonction ou classe déclarée au premier niveau.

## `varians_synchro/alignment.py` (164 lignes)
**Objet (docstring source)** : Manual physical-line alignments, independent of editorial XML (v0.3). Sessions store rich links; the legacy Varians JSON is an export projection. The application NEVER edits source TEI/ALTO files.
**Dépendances internes observées** : `imaging`, `physical_alignment`
**Fonctions au premier niveau** : `base_key` (l.16), `get_base_lines` (l.21), `target_lines` (l.32), `create_session` (l.51), `_indices` (l.69), `add_link` (l.76), `remove_link` (l.102), `export_varians` (l.108)

## `varians_synchro/alto_geometry.py` (164 lignes)
**Objet (docstring source)** : ALTO physical-line polygon geometry (pure Python, no Qt dependency). PERO and other HTR engines may describe a sloping text line using <TextLine><Shape><Polygon POINTS="x,y ..."/></Shape></TextLine>. The TextLine HPOS/VPOS/WIDTH/HEIGHT attributes are only an axis-aligned *envelope*, which can overlap neighbouring lines even when the polygons don't. This module never changes the source file or the persistent line identifiers. For projects imported before polygons were stored, original ALTO files are consulted on demand and cached; if missing, original bounding boxes remain.
**Dépendances internes observées** : `imaging`, `page_xml`
**Fonctions au premier niveau** : `parse_alto_points` (l.22), `_local_name` (l.49), `textline_polygon` (l.53), `_source_geometry` (l.66), `_cached_source_geometry` (l.83), `page_line_polygons` (l.87), `polygon_contains` (l.145)

## `varians_synchro/automatic.py` (170 lignes)
**Objet (docstring source)** : Conservative, offline, deterministic TEI/HTR line alignment proposals. No generative AI or source modification. Only unassigned intervals are eligible. The sequence matcher detects shared textual spans, projects matched character intervals to physical lines, and NEVER labels interpolation as verified.
**Dépendances internes observées** : `alignment`
**Fonctions au premier niveau** : `normalize` (l.18), `_concatenate` (l.26), `_free_spans` (l.36), `propose_alignment` (l.44), `apply_proposals` (l.151)

## `varians_synchro/bulk_binding.py` (203 lignes)
**Objet (docstring source)** : Conservative batch page↔ALTO/PAGE proposals and atomic confirmation. Strong matches use explicit XML imageFilename / unique filename stems. The ordinal fallback is ALWAYS labeled as provisional and requires user approval. No matching operation modifies page order, line IDs or source data.
**Dépendances internes observées** : `imaging`, `page_order`
**Fonctions au premier niveau** : `_stem` (l.18), `_strong` (l.22), `_page_candidates` (l.26), `_xml_candidates` (l.36), `binding_fingerprint` (l.43), `propose_bindings` (l.61), `binding_selection_conflicts` (l.137), `apply_binding_choices` (l.171)

## `varians_synchro/core.py` (290 lignes)
**Objet (docstring source)** : Varians-Synchro: persistent inventory of documentary resources. No TEI, ALTO or remote source is ever modified by the application. Version 0.1 deliberately does not assert that page/image matches are verified.
**Dépendances internes observées** : `alto_geometry`, `imaging`, `page_xml`, `tei_binding`
**Fonctions au premier niveau** : `new_project` (l.25), `_staged_file` (l.31), `save_project` (l.54), `load_project` (l.96), `validate_project` (l.110), `create_witness` (l.141), `add_image_source` (l.150), `add_alto_source` (l.158), `lname` (l.166), `inspect_line_source` (l.170), `add_line_source` (l.184), `inspect_alto` (l.189), `import_tei` (l.231), `inspect_manifest` (l.253), `diagnostic` (l.259), `check_alto_files` (l.268)

## `varians_synchro/correspondence_navigation.py` (62 lignes)
**Objet (docstring source)** : Read-only reciprocal navigation over a physical ALTO pair session. This module never changes line selection or alignment data. Links with confirmed absences have no target lines, and can be reported to the researcher without manufacturing a fictitious counterpart. Direct links only: no transitive inference and no assumption that HTR is reliable.
**Fonctions au premier niveau** : `build_pair_navigation_index` (l.11), `combined_counterparts` (l.38)

## `varians_synchro/exceptions.py` (166 lignes)
**Objet (docstring source)** : V0.7.3: safe, explicit, pair-local confirmed textual absences. No inference of omission from geometry or HTR. A selected passage in ONE witness is asserted to lack a counterpart in the other witness of this pair. Existing *uncertain automatic* groups can be partially peeled away; manual or validated groups are never silently rewritten. Preview and commit are separate, checked, all-or-nothing operations.
**Dépendances internes observées** : `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `_digest` (l.20), `_selection` (l.25), `_runs` (l.47), `preview_confirmed_absence` (l.58), `confirm_absence` (l.94), `pair_exception_summary` (l.151)

## `varians_synchro/gui.py` (32 lignes)
**Objet (docstring source)** : Minimal PySide6 application shell for witness-centered Varians-Synchro. The historical V0.5 editor and its TXT interface were retired in V0.8.0. The legacy project *data* are still readable: no project migration discards older text resources or alignment sessions. The historical algorithm modules remain in the package for backwards-compatible project introspection.
**Dépendances internes observées** : `guided_ui`, `i18n`, `qt_lifecycle`
**Fonctions au premier niveau** : `main` (l.17)

## `varians_synchro/guided_ui.py` (3187 lignes)
**Objet (docstring source)** : Witness-centered PySide6 GUI; the V0.7 physical alignment engine is preserved.
**Dépendances internes observées** : `bulk_binding`, `core`, `correspondence_navigation`, `exceptions`, `hd_registry`, `i18n`, `imaging`, `interpolation`, `line_scope`, `overlay_filters`, `page_management`, `page_order`, `physical_alignment`, `project_state`, `rapid_review`, `reading_stream`, `residual_alignment`, `resource_workflow`, `tei_binding`, `tei_visual`, `textual_progress`, `validation`, `varians_export`, `varians_project_export`, `viewer`
**Fonctions au premier niveau** : `make_guided_window` (l.29)

## `varians_synchro/hd_registry.py` (159 lignes)
**Objet (docstring source)** : Durable, source-bound IIIF HD downloads linked to manuscript Canvas IDs. No network requests. The registry stores where successful downloads live; it never turns an image into a new manuscript page or replaces an IIIF source. The original ``images.json`` remains the authoritative download receipt.
**Dépendances internes observées** : `imaging`
**Fonctions au premier niveau** : `_sha256` (l.18), `inspect_hd_folder` (l.26), `register_hd_snapshot` (l.82), `register_hd_folder` (l.90), `local_copy_plan` (l.96), `varians_remote_key` (l.134), `varians_offline_index` (l.148)

## `varians_synchro/i18n.py` (108 lignes)
**Objet (docstring source)** : Varians-Synchro localization: XML catalogs, same schema as Varians. The files ``i18n/fr.xml`` and ``i18n/en.xml`` live beside ``run.py``. All UI message values (including the French defaults) come from these files. Application state, source texts, folio labels and manuscripts are NEVER translated.
**Fonctions au premier niveau** : `_load_one` (l.21), `_parameters` (l.39), `reload_catalogs` (l.43), `available_languages` (l.71), `language_labels` (l.75), `set_language` (l.80), `get_language` (l.87), `tr` (l.91), `translate_template` (l.104)

## `varians_synchro/imaging.py` (367 lignes)
**Objet (docstring source)** : IIIF/local page registry, ALTO-to-page mapping, export for external HTR. Images and ALTO are immutable external inputs. An export is a temporary working copy.
**Dépendances internes observées** : `core`, `page_order`
**Fonctions au premier niveau** : `_http_bytes` (l.18), `_label` (l.28), `_first` (l.39), `parse_manifest` (l.45), `fetch_manifest` (l.84), `create_pages` (l.88), `bind_alto` (l.133), `mapped_alto_page` (l.141), `bind_line_source` (l.148), `mapped_line_page` (l.152), `suggest_alto_bindings` (l.156), `suggest_line_bindings` (l.175), `image_request_url` (l.179), `image_bytes` (l.188), `export_iiif_htr_zip` (l.198), `import_htr_results` (l.226), `iiif_hd_url` (l.264), `export_iiif_hd_images` (l.285)

## `varians_synchro/interpolation.py` (342 lignes)
**Objet (docstring source)** : Geometry-first manuscript column matching between confirmed 1:1 anchors. This module never assumes a transcription is correct. A physical ALTO column can be aligned between its first and last confirmed lines even when the ALTO reading-order list is interleaved with other columns, text lines are ragged, or OCR order contains small vertical inversions. The output is *suggestions*, not validated textual equivalence; no source or confirmed link is modified.
**Dépendances internes observées** : `automatic`, `i18n`, `physical_alignment`
**Fonctions au premier niveau** : `_bbox` (l.20), `_center_y` (l.32), `_overlap_ratio` (l.36), `_column_interval` (l.42), `_htr_similarity` (l.115), `_partition` (l.124), `_unlinked_segments` (l.172), `_anchor_row` (l.220), `suggest_between_anchors` (l.225)

## `varians_synchro/line_scope.py` (99 lignes)
**Objet (docstring source)** : Project-wide witness ALTO scope: lines excluded from the edited work. Ignored != unaligned != confirmed textual absence. Only project witness records contain ignored_line_ids; no ALTO file, source image or pair-level setting is altered. Existing projects need no migration.
**Dépendances internes observées** : `physical_alignment`
**Fonctions au premier niveau** : `ignored_ids` (l.12), `linked_scope_conflicts` (l.16), `update_ignored_lines` (l.30)

## `varians_synchro/overlay_filters.py` (57 lignes)
**Objet (docstring source)** : Pure, UI-independent semantics for ALTO line-overlay filtering. The source of truth is always the physical-pair alignment session. Filtering changes visibility of image frames only; it never mutates links or selected IDs. In particular, interpolated geometric links are AUTOMATIC proposals, despite not having an origin string beginning with ``automatic``.
**Fonctions au premier niveau** : `style_for_link` (l.21), `overlay_visible` (l.40)

## `varians_synchro/overlay_selection.py` (63 lignes)
**Objet (docstring source)** : Unambiguous picking of visual ALTO lines when their bounding boxes overlap. Pure geometry: no Qt dependency; remains usable in tests and on every Python platform. The imported ALTO rectangles are never changed. At a click point inside several boxes, prefer the nearest vertical centreline (and then the closest horizontal centre), rather than the arbitrary graphics-item z-order.
**Dépendances internes observées** : `alto_geometry`
**Fonctions au premier niveau** : `choose_line_at` (l.13), `choose_line_geometry` (l.42)

## `varians_synchro/page_management.py` (37 lignes)
**Objet (docstring source)** : Human page ordering; never change page identity or ALTO/PAGE associations. Only ``reading_order`` is written. The image and its XML binding stay together, including when a page is moved across a folio or an image-source boundary.
**Dépendances internes observées** : `page_order`, `reading_stream`
**Fonctions au premier niveau** : `page_ids_in_reading_order` (l.12), `commit_page_order` (l.16), `invert_page_order` (l.23), `move_page_by_id` (l.27)

## `varians_synchro/page_order.py` (65 lignes)
**Objet (docstring source)** : Documentary reading order for pages, independent of dialog import order. IIIF Canvas order is authoritative. For local images, common folio labels (e.g. f014v, 1r, 1v, 2r) or natural filename numbers are used. Mixed-source witnesses retain their source-group order; a future page-order editor may allow manual cross-group reordering. This module never renumbers page IDs.
**Fonctions au premier niveau** : `_natural` (l.16), `folio_key` (l.21), `_local_key` (l.34), `ordered_pages` (l.43)

## `varians_synchro/page_xml.py` (153 lignes)
**Objet (docstring source)** : PAGE-XML (PRImA / PAGE) parser for Varians-Synchro. Produces the same physical-line inventory as ALTO, with true PAGE TextLine Coords polygons and line-level TextEquiv/Unicode. No image/HTR processing or transformation of the source file is performed. Namespace versions are accepted by local element name, after checking the PAGE document structure.
**Dépendances internes observées** : `alto_geometry`
**Fonctions au premier niveau** : `_name` (l.18), `_direct` (l.22), `_line_text` (l.26), `_region_order` (l.44), `_baseline_points` (l.59), `_line_info` (l.78), `inspect_page_xml` (l.102)

## `varians_synchro/physical_alignment.py` (492 lignes)
**Objet (docstring source)** : Alignment between physical ALTO lines without TEI or TXT. These sessions have no editorial base: `reference_witness_id` is a reversible technical display/comparison choice, not an assertion about the edition. Original ALTO and images are never edited. Legacy TEI sessions remain separate.
**Dépendances internes observées** : `alignment`, `automatic`, `imaging`, `page_order`
**Fonctions au premier niveau** : `_now` (l.21), `_hash` (l.25), `line_uid` (l.30), `physical_lines` (l.36), `_witness` (l.69), `create_pair_session` (l.73), `pair_indices` (l.96), `add_pair_link` (l.105), `extend_pair_link` (l.142), `detach_pair_lines` (l.212), `is_revisable_automatic` (l.272), `replace_revisable_pair_proposals` (l.284), `remove_pair_link` (l.349), `set_pair_link_states` (l.356), `pair_progress` (l.373), `verify_pair_sessions` (l.404), `suggest_htr_pair_alignment` (l.418), `apply_pair_proposals` (l.478)

## `varians_synchro/project_state.py` (35 lignes)
**Objet (docstring source)** : Reliable, UI-independent detection of project changes since the last save. The project is a JSON-serializable dictionary and nested editors mutate it in place. Comparing its persisted JSON representation catches every such mutation, without a fragile collection of per-button `dirty = True` assignments.
**Classes déclarées au premier niveau** : `ProjectChangeTracker` (l.19)
**Fonctions au premier niveau** : `project_fingerprint` (l.13)

## `varians_synchro/qt_lifecycle.py` (47 lignes)
**Objet (docstring source)** : One QApplication per process, with Spyder/IPython-friendly window lifetime. This module deliberately has no Qt dependency so lifecycle logic is unit-testable without a graphical display. `QApplication` and the main window are injected by `gui.main()` after importing PySide6.
**Fonctions au premier niveau** : `launch` (l.11)

## `varians_synchro/rapid_review.py` (107 lignes)
**Objet (docstring source)** : V0.7.2 — rapid, non-destructive human review of physical correspondences. This module never auto-validates machine suggestions. Display sorting and filtering have no effect on .vsynch storage order or Varians JSON export.
**Dépendances internes observées** : `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `ordered_links` (l.18), `review_counts` (l.48), `pending_ids` (l.55), `following_anchor_interval` (l.59), `verify_before_review` (l.75), `validate_checked` (l.97), `suggestions_for_interval` (l.103)

## `varians_synchro/reading_stream.py` (180 lignes)
**Objet (docstring source)** : V0.7: continuous documentary reading streams and human anchor intervals. This layer never infers textual equivalence. It only orders physical lines and extracts *every active line* strictly between user-confirmed homologous anchors. No ALTO/PAGE, saved line UID, fingerprint, or existing pair link is rewritten. Overrides are stored in the documentary witness's page dictionaries: ``reading_order`` (all pages), ``reading_region_order`` (region identifiers), ``reading_line_order`` (the line UIDs of one page). The last takes precedence.
**Dépendances internes observées** : `page_order`, `physical_alignment`
**Classes déclarées au premier niveau** : `ReadingOrderError` (l.17)
**Fonctions au premier niveau** : `_unique_order` (l.21), `set_page_order` (l.26), `_region` (l.35), `set_region_order` (l.39), `set_line_order` (l.52), `reset_page_line_order` (l.62), `page_regions` (l.69), `reading_stream` (l.75), `anchor_intervals` (l.118)

## `varians_synchro/residual_alignment.py` (285 lignes)
**Objet (docstring source)** : Conservative second-pass suggestions for orphan physical manuscript lines. The *existing* partner link is expanded only after a separate preview/commit. This is not a transcription or a claim that texts match: a neighbouring line may carry an omission or addition. Never auto-extend a human/validated link. PAGE and ALTO share the physical_lines interface; neither source is modified.
**Dépendances internes observées** : `physical_alignment`
**Fonctions au premier niveau** : `_box` (l.17), `_cy` (l.28), `_overlap` (l.32), `_same_column` (l.37), `_local_pitch` (l.41), `_linked_info` (l.55), `_nearest_group` (l.78), `suggest_residual_extensions` (l.113), `apply_residual_extensions` (l.218)

## `varians_synchro/resource_workflow.py` (145 lignes)
**Objet (docstring source)** : Witness-centered project resources, with non-destructive staged import. The physical-line alignment model is deliberately not touched. Source files are only inspected, never rewritten. GUI dialogs collect selections first; ``apply_witness_draft`` commits them as one coherent project change.
**Dépendances internes observées** : `core`, `imaging`, `page_order`, `tei_binding`
**Fonctions au premier niveau** : `_local_key` (l.21), `_manifest_key` (l.25), `_xml_kind` (l.30), `store_tei_reference` (l.37), `set_project_pivot` (l.62), `resource_summary` (l.68), `apply_witness_draft` (l.81)

## `varians_synchro/review.py` (96 lignes)
**Objet (docstring source)** : Review policy and batch operations for line alignment sessions (v0.5). Confidence is a heuristic matching score, NEVER a scholarly verification. All operations preserve immutable link identity and never modify source files.
**Dépendances internes observées** : `alignment`
**Fonctions au premier niveau** : `configure_session` (l.13), `prepare_proposals` (l.22), `bulk_set_state` (l.44), `session_progress` (l.65), `project_progress` (l.93)

## `varians_synchro/selection_policy.py` (40 lignes)
**Objet (docstring source)** : Pure cross-folio line selection rules shared by manuscript and text clicks. Selection is transient visual UI state, never written to .vsynch or used by the matching algorithm itself. All UIDs belong to one witness; the caller supplies the already validated documentary reading order, including ignored lines.
**Fonctions au premier niveau** : `update_line_selection` (l.10)

## `varians_synchro/spyder_launch.py` (82 lignes)
**Objet (docstring source)** : Safe Spyder entrypoint: start the Qt GUI in a separate Python process. No Qt imports are permitted here. A single Spyder kernel may load a different Qt binding or platform plugin; creating Qt widgets in that same native process can terminate the kernel without raising a Python exception.
**Fonctions au premier niveau** : `in_spyder_kernel` (l.20), `isolated_environment` (l.42), `log_directory` (l.53), `launch_isolated` (l.63)

## `varians_synchro/tei_binding.py` (273 lignes)
**Objet (docstring source)** : Safe, witness-specific TEI extraction and explicit TEI↔physical line bindings. TEI is read only. Bindings are *not* witness-to-witness correspondence links. No '<lb/>' without the exact target @edRef is silently assigned. Unresolved apparatus readings block bulk linking, never fabricate witness text.
**Dépendances internes observées** : `reading_stream`
**Fonctions au premier niveau** : `_local` (l.23), `_refs` (l.27), `_digest` (l.31), `_stamp` (l.35), `extract_witness_tei` (l.40), `_resource` (l.148), `preview_tei_binding` (l.158), `apply_tei_binding` (l.198), `refresh_tei_source` (l.218), `tei_binding_status` (l.239), `linked_tei_texts` (l.255)

## `varians_synchro/tei_visual.py` (159 lignes)
**Objet (docstring source)** : Read-only visual review model for TEI↔physical-line proposals. This module deliberately has no PySide6 dependency. It never changes project sources, correspondence groups, TEI bindings, or the TEI XML. All coordinates are expressed in the XML page coordinate system, then projected to the actual image/IIIF Canvas dimensions for fetching and rendering.
**Dépendances internes observées** : `alto_geometry`, `imaging`, `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `_positive` (l.17), `review_pairs` (l.27), `line_preview_descriptor` (l.35), `fetch_preview_bytes` (l.126), `render_transform` (l.133)

## `varians_synchro/textual_progress.py` (336 lignes)
**Objet (docstring source)** : V0.7.1: linear, multi-folio text-quantity alignment between human anchors. The two streams are *declared homologous by the editor*: this module never tries to prove equivalence through geometry or OCR. Weight-based cuts are only *tentative* estimates of manuscript line segmentation. No source, existing link, line UID, or TEI is changed by previewing. Protected links (manual / validated / absence) form immutable obstacles. Automatic groups may be recalculated after explicit confirmation with the existing atomic writer.
**Dépendances internes observées** : `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `_chars` (l.23), `_length` (l.28), `_weights` (l.48), `_cumulative` (l.107), `_partition` (l.116), `_method` (l.164), `_segments` (l.172), `suggest_textual_progress` (l.264)

## `varians_synchro/validation.py` (163 lignes)
**Objet (docstring source)** : Read-only V0.7.4 preflight for documentary streams and physical pairs. The audit NEVER repairs historical links, guesses an omission, or modifies data. Warnings may reflect unavailable external resources on a different workstation. Hard errors mark contradictions that must not be silently treated as reliable.
**Dépendances internes observées** : `core`, `physical_alignment`, `reading_stream`, `tei_binding`, `varians_export`
**Fonctions au premier niveau** : `_item` (l.17), `audit_project` (l.26)

## `varians_synchro/varians_export.py` (421 lignes)
**Objet (docstring source)** : Export physical-line sessions to the Varians alignment JSON schema. Opening the exported project in Varians 0.9.4.0 is checked by tests/test_varians_094_compat.py (the real Varians code reads it). Lines are written in the witness's reading order (reading_stream). One explicit technical reference witness is used for these export files. This DOES NOT magically create an editorial TEI line mapping. The TEI XML <lb/> line IDs must still be reconciled with the physical reference's page::ordinal keys before manuscript-to-edition synchronization is guaranteed. No network, Qt, or local source-image files are required for the export.
**Dépendances internes observées** : `imaging`, `page_order`, `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `_get_witness` (l.32), `_image_block` (l.36), `_build_witness_cache` (l.53), `_line_fingerprint` (l.107), `_shared_pero_uuid` (l.114), `_safe_same_segmentation_after_format_change` (l.127), `_reference_health` (l.157), `_pair_for_base` (l.169), `make_varians_alignments` (l.177), `inspect_varians_export` (l.272), `verify_export_payloads` (l.319), `export_varians_alignments` (l.363)

## `varians_synchro/varians_project_export.py` (289 lignes)
**Objet (docstring source)** : Build a directly openable Varians project.xml bundle from Synchro resources. Target syntax: Varians's documented teiManuscriptProject format with one TEI edition. This is a physical mapping export; it does NOT assert that line links have been reconciled with TEI <lb/> unless the editor independently confirms it. The caller must run a final integration test against their installed Varians.
**Dépendances internes observées** : `core`, `hd_registry`, `varians_export`
**Fonctions au premier niveau** : `_varians_safe_id` (l.23), `_source_path` (l.28), `_relative_or_absolute` (l.35), `_cache_varians_manifest` (l.41), `export_varians_project` (l.85)

## `varians_synchro/viewer.py` (736 lignes)
**Objet (docstring source)** : Reusable manuscript page viewer with clickable ALTO overlay. Images can be IIIF or local. Full physical lines are the interaction unit; HTR is supplementary and never needed for visual selection. A 4200px-wide IIIF request provides useful magnification without downloading all canvases.
**Dépendances internes observées** : `alto_geometry`, `i18n`, `imaging`, `overlay_filters`, `overlay_selection`, `page_order`, `physical_alignment`, `reading_stream`, `selection_policy`
**Classes déclarées au premier niveau** : `FetchThread` (l.27), `ZoomableGraphicsView` (l.54), `ClickableLine` (l.75), `WitnessLineList` (l.144), `LineImagePanel` (l.166), `PageViewer` (l.719)

## Attention à la lecture

Les fonctions et classes **internes à** `guided_ui.make_guided_window`, les méthodes des classes, les fonctions de tests et les importations dynamiques ne sont pas détaillés ici. Cette liste est **un point d’entrée**, pas une analyse d’appels complète. Les dépendances proviennent d’une inspection syntaxique (AST) et peuvent inclure des chemins conditionnels. Pour les contrats, consulter les chapitres métiers du dossier.
