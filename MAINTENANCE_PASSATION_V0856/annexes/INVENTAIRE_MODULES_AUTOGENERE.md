# Inventaire technique généré automatiquement (code v0.8.5.6)

Génération reproductible : `python tools/generate_module_inventory.py` depuis la racine.
Inspection statique AST : **aucun module applicatif n’est importé ni exécuté**.
Les numéros de ligne sont ceux de **cette livraison uniquement**.

**52 fichiers Python** dans `varians_synchro/` (dont `__init__.py`).

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

## `varians_synchro/app_icon.py` (46 lignes)
**Objet (docstring source)** : Icône de l'application : le logo de Varians-Synchro. Les images de ``icons/`` (à côté de ``run.py``) sont produites à partir du logo (``logo/*.psd``) par ``tools/generate_icons.py``. Ce module ne charge PySide6 qu'à l'appel d'``application_icon`` : il s'importe sans Qt.
**Fonctions au premier niveau** : `icon_files` (l.17), `application_icon` (l.22), `use_own_taskbar_entry` (l.33)

## `varians_synchro/automatic.py` (171 lignes)
**Objet (docstring source)** : Conservative, offline, deterministic TEI/HTR line alignment proposals. No generative AI or source modification. Only unassigned intervals are eligible. The sequence matcher detects shared textual spans, projects matched character intervals to physical lines, and NEVER labels interpolation as verified.
**Dépendances internes observées** : `alignment`, `errors`
**Fonctions au premier niveau** : `normalize` (l.19), `_concatenate` (l.27), `_free_spans` (l.37), `propose_alignment` (l.45), `apply_proposals` (l.152)

## `varians_synchro/bulk_binding.py` (204 lignes)
**Objet (docstring source)** : Conservative batch page↔ALTO/PAGE proposals and atomic confirmation. Strong matches use explicit XML imageFilename / unique filename stems. The ordinal fallback is ALWAYS labeled as provisional and requires user approval. No matching operation modifies page order, line IDs or source data.
**Dépendances internes observées** : `errors`, `page_order`, `reading_stream`
**Fonctions au premier niveau** : `_stem` (l.18), `_strong` (l.22), `_page_candidates` (l.26), `_xml_candidates` (l.36), `binding_fingerprint` (l.43), `propose_bindings` (l.61), `binding_selection_conflicts` (l.137), `apply_binding_choices` (l.171)

## `varians_synchro/core.py` (327 lignes)
**Objet (docstring source)** : Varians-Synchro: persistent inventory of documentary resources. No TEI, ALTO or remote source is ever modified by the application. Version 0.1 deliberately does not assert that page/image matches are verified.
**Dépendances internes observées** : `alto_geometry`, `errors`, `imaging`, `page_xml`, `tei_binding`
**Fonctions au premier niveau** : `new_project` (l.26), `_staged_file` (l.32), `save_project` (l.55), `_is_relative_file_path` (l.97), `_resolve_relative_paths` (l.106), `load_project` (l.133), `validate_project` (l.148), `create_witness` (l.179), `add_image_source` (l.188), `add_alto_source` (l.196), `lname` (l.204), `inspect_line_source` (l.208), `add_line_source` (l.222), `inspect_alto` (l.227), `import_tei` (l.269), `inspect_manifest` (l.291), `diagnostic` (l.297), `check_alto_files` (l.306)

## `varians_synchro/correspondence_navigation.py` (62 lignes)
**Objet (docstring source)** : Read-only reciprocal navigation over a physical ALTO pair session. This module never changes line selection or alignment data. Links with confirmed absences have no target lines, and can be reported to the researcher without manufacturing a fictitious counterpart. Direct links only: no transitive inference and no assumption that HTR is reliable.
**Fonctions au premier niveau** : `build_pair_navigation_index` (l.11), `combined_counterparts` (l.38)

## `varians_synchro/error_report.py` (58 lignes)
**Objet (docstring source)** : Erreur imprévue dans une action de l'interface : un message à l'écran. Sans ce crochet, une exception levée dans un clic (slot Qt) n'allait qu'à la console ou au journal de démarrage : pour l'utilisateur, rien ne se passait. Le crochet garde ce comportement (le détail technique reste dans la console) et montre en plus un message, traduit quand le texte de l'erreur est connu des catalogues.
**Dépendances internes observées** : `i18n`
**Fonctions au premier niveau** : `describe` (l.18), `show` (l.25), `install` (l.46)

## `varians_synchro/errors.py` (53 lignes)
**Objet (docstring source)** : Messages des moteurs, traduisibles. Les moteurs (sans Qt) écrivent leurs erreurs et avertissements en français : c'est le texte des journaux, des tests et de ``str(exc)``. L'interface les montre dans sa langue : - un message fixe est la valeur française d'une clé du catalogue ; ``tr(texte)`` le traduit par l'alias français ; - un message avec des valeurs (un sigle, un fichier…) est un ``Localized`` : une chaîne française qui garde sa clé et ses valeurs, pour que ``localized_text`` le traduise avec les mêmes valeurs. ``localized(ValueError, 'clé', sigle=…)`` construit l'exception ; ``localized_text(exc_ou_texte)`` donne le texte à afficher.
**Dépendances internes observées** : `i18n`
**Classes déclarées au premier niveau** : `Localized` (l.21)
**Fonctions au premier niveau** : `_rebuild` (l.34), `localized` (l.38), `localized_text` (l.43)

## `varians_synchro/exceptions.py` (166 lignes)
**Objet (docstring source)** : V0.7.3: safe, explicit, pair-local confirmed textual absences. No inference of omission from geometry or HTR. A selected passage in ONE witness is asserted to lack a counterpart in the other witness of this pair. Existing *uncertain automatic* groups can be partially peeled away; manual or validated groups are never silently rewritten. Preview and commit are separate, checked, all-or-nothing operations.
**Dépendances internes observées** : `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `_digest` (l.20), `_selection` (l.25), `_runs` (l.47), `preview_confirmed_absence` (l.58), `confirm_absence` (l.94), `pair_exception_summary` (l.151)

## `varians_synchro/gui.py` (40 lignes)
**Objet (docstring source)** : Minimal PySide6 application shell for witness-centered Varians-Synchro. The historical V0.5 editor and its TXT interface were retired in V0.8.0. The legacy project *data* are still readable: no project migration discards older text resources or alignment sessions. The historical algorithm modules remain in the package for backwards-compatible project introspection.
**Dépendances internes observées** : `app_icon`, `error_report`, `guided_ui`, `i18n`, `qt_lifecycle`
**Fonctions au premier niveau** : `main` (l.18)

## `varians_synchro/guided_ui.py` (23 lignes)
**Objet (docstring source)** : Point d'entrée de l'interface de Varians-Synchro. Les fenêtres sont réparties dans les modules ``ui_*`` : - ``ui_main_window`` : fenêtre principale (``GuidedWindow``) ; - ``ui_pair`` : synchronisation visuelle d'une paire de témoins ; - ``ui_pages`` : images et associations ALTO/PAGE d'un témoin ; - ``ui_batch_binding`` : association automatique par lot ; - ``ui_resources`` : ajout et modification d'un témoin ; - ``ui_tei_binding`` : liaison TEI ↔ lignes physiques ; - ``ui_reading_order``, ``ui_scope`` : ordre de lecture, périmètre ; - ``ui_widgets`` : widgets Qt qui traduisent leurs textes, ``_run_modal``. Ce module ne charge PySide6 qu'à l'
**Dépendances internes observées** : `ui_main_window`
**Fonctions au premier niveau** : `make_guided_window` (l.20)

## `varians_synchro/hd_registry.py` (160 lignes)
**Objet (docstring source)** : Durable, source-bound IIIF HD downloads linked to manuscript Canvas IDs. No network requests. The registry stores where successful downloads live; it never turns an image into a new manuscript page or replaces an IIIF source. The original ``images.json`` remains the authoritative download receipt.
**Dépendances internes observées** : `errors`, `imaging`
**Fonctions au premier niveau** : `_sha256` (l.19), `inspect_hd_folder` (l.27), `register_hd_snapshot` (l.83), `register_hd_folder` (l.91), `local_copy_plan` (l.97), `varians_remote_key` (l.135), `varians_offline_index` (l.149)

## `varians_synchro/help_search.py` (121 lignes)
**Objet (docstring source)** : Recherche dans l'aide de Varians-Synchro, sans Qt (reprise de Varians). L'aide est une longue page découpée en sections (un titre et le texte qui le suit). La recherche ne tient compte ni des accents ni de la casse, ni des signes typographiques (« ’ » vaut « ' », « » » vaut « " », une espace insécable une espace). Plusieurs mots : les sections qui les contiennent tous, dans n'importe quel ordre ; entre guillemets, l'expression exacte. Les positions sont celles du texte de l'aide (une par caractère) ; la fenêtre d'aide les passe à Qt avec ``Utf16Positions``.
**Classes déclarées au premier niveau** : `Section` (l.25), `Hit` (l.34), `Utf16Positions` (l.106)
**Fonctions au premier niveau** : `fold` (l.43), `query_terms` (l.61), `search` (l.71), `_excerpt` (l.92)

## `varians_synchro/i18n.py` (115 lignes)
**Objet (docstring source)** : Varians-Synchro localization: XML catalogs, same schema as Varians. The files ``i18n/fr.xml`` and ``i18n/en.xml`` live beside ``run.py``. All UI message values (including the French defaults) come from these files. Application state, source texts, folio labels and manuscripts are NEVER translated.
**Fonctions au premier niveau** : `_load_one` (l.21), `_parameters` (l.39), `reload_catalogs` (l.43), `available_languages` (l.71), `language_labels` (l.75), `set_language` (l.80), `get_language` (l.87), `tr` (l.91), `french` (l.104), `translate_template` (l.111)

## `varians_synchro/imaging.py` (375 lignes)
**Objet (docstring source)** : IIIF/local page registry, ALTO-to-page mapping, export for external HTR. Images and ALTO are immutable external inputs. An export is a temporary working copy.
**Dépendances internes observées** : `core`, `errors`, `page_order`
**Fonctions au premier niveau** : `_http_bytes` (l.19), `_label` (l.29), `_first` (l.40), `parse_manifest` (l.46), `fetch_manifest` (l.85), `create_pages` (l.89), `bind_alto` (l.134), `mapped_alto_page` (l.142), `bind_line_source` (l.149), `mapped_line_page` (l.153), `suggest_alto_bindings` (l.157), `suggest_line_bindings` (l.176), `image_request_url` (l.180), `image_bytes` (l.189), `export_iiif_htr_zip` (l.199), `import_htr_results` (l.236), `iiif_hd_url` (l.274), `export_iiif_hd_images` (l.294)

## `varians_synchro/interpolation.py` (344 lignes)
**Objet (docstring source)** : Geometry-first manuscript column matching between confirmed 1:1 anchors. This module never assumes a transcription is correct. A physical ALTO column can be aligned between its first and last confirmed lines even when the ALTO reading-order list is interleaved with other columns, text lines are ragged, or OCR order contains small vertical inversions. The output is *suggestions*, not validated textual equivalence; no source or confirmed link is modified.
**Dépendances internes observées** : `automatic`, `i18n`, `physical_alignment`
**Fonctions au premier niveau** : `_bbox` (l.20), `_center_y` (l.32), `_overlap_ratio` (l.36), `_column_interval` (l.42), `_htr_similarity` (l.115), `_partition` (l.124), `_unlinked_segments` (l.172), `_anchor_row` (l.220), `suggest_between_anchors` (l.225)

## `varians_synchro/line_scope.py` (100 lignes)
**Objet (docstring source)** : Project-wide witness ALTO scope: lines excluded from the edited work. Ignored != unaligned != confirmed textual absence. Only project witness records contain ignored_line_ids; no ALTO file, source image or pair-level setting is altered. Existing projects need no migration.
**Dépendances internes observées** : `errors`, `physical_alignment`
**Fonctions au premier niveau** : `ignored_ids` (l.13), `linked_scope_conflicts` (l.17), `update_ignored_lines` (l.31)

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

## `varians_synchro/physical_alignment.py` (590 lignes)
**Objet (docstring source)** : Alignment between physical ALTO lines without TEI or TXT. These sessions have no editorial base: `reference_witness_id` is a reversible technical display/comparison choice, not an assertion about the edition. Original ALTO and images are never edited. Legacy TEI sessions remain separate.
**Dépendances internes observées** : `alignment`, `automatic`, `errors`, `imaging`, `page_order`
**Fonctions au premier niveau** : `_now` (l.22), `_hash` (l.26), `line_uid` (l.31), `physical_lines` (l.37), `_witness` (l.70), `create_pair_session` (l.74), `pair_indices` (l.97), `link_is_stale` (l.106), `stale_link_ids` (l.122), `_revalidation_check` (l.131), `revalidate_pair_links` (l.145), `revalidate_pair_link` (l.171), `page_links_impact` (l.177), `add_pair_link` (l.200), `extend_pair_link` (l.237), `detach_pair_lines` (l.311), `is_revisable_automatic` (l.371), `replace_revisable_pair_proposals` (l.383), `remove_pair_link` (l.448), `set_pair_link_states` (l.455), `pair_progress` (l.472), `verify_pair_sessions` (l.503), `suggest_htr_pair_alignment` (l.517), `apply_pair_proposals` (l.576)

## `varians_synchro/project_state.py` (35 lignes)
**Objet (docstring source)** : Reliable, UI-independent detection of project changes since the last save. The project is a JSON-serializable dictionary and nested editors mutate it in place. Comparing its persisted JSON representation catches every such mutation, without a fragile collection of per-button `dirty = True` assignments.
**Classes déclarées au premier niveau** : `ProjectChangeTracker` (l.19)
**Fonctions au premier niveau** : `project_fingerprint` (l.13)

## `varians_synchro/qt_lifecycle.py` (57 lignes)
**Objet (docstring source)** : One QApplication per process, with Spyder/IPython-friendly window lifetime. This module deliberately has no Qt dependency so lifecycle logic is unit-testable without a graphical display. `QApplication` and the main window are injected by `gui.main()` after importing PySide6.
**Fonctions au premier niveau** : `launch` (l.11)

## `varians_synchro/rapid_review.py` (112 lignes)
**Objet (docstring source)** : V0.7.2 — rapid, non-destructive human review of physical correspondences. This module never auto-validates machine suggestions. Display sorting and filtering have no effect on .vsynch storage order or Varians JSON export.
**Dépendances internes observées** : `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `ordered_links` (l.20), `review_counts` (l.53), `pending_ids` (l.60), `following_anchor_interval` (l.64), `verify_before_review` (l.80), `validate_checked` (l.102), `suggestions_for_interval` (l.108)

## `varians_synchro/reading_stream.py` (203 lignes)
**Objet (docstring source)** : V0.7: continuous documentary reading streams and human anchor intervals. This layer never infers textual equivalence. It only orders physical lines and extracts *every active line* strictly between user-confirmed homologous anchors. No ALTO/PAGE, saved line UID, fingerprint, or existing pair link is rewritten. Overrides are stored in the documentary witness's page dictionaries: ``reading_order`` (all pages), ``reading_region_order`` (region identifiers), ``reading_line_order`` (the line UIDs of one page). The last takes precedence.
**Dépendances internes observées** : `errors`, `imaging`, `page_order`, `physical_alignment`
**Classes déclarées au premier niveau** : `ReadingOrderError` (l.19)
**Fonctions au premier niveau** : `_unique_order` (l.23), `set_page_order` (l.28), `_region` (l.37), `set_region_order` (l.41), `set_line_order` (l.54), `reset_page_line_order` (l.64), `rebind_page` (l.71), `page_regions` (l.87), `reading_stream` (l.93), `anchor_intervals` (l.136)

## `varians_synchro/residual_alignment.py` (285 lignes)
**Objet (docstring source)** : Conservative second-pass suggestions for orphan physical manuscript lines. The *existing* partner link is expanded only after a separate preview/commit. This is not a transcription or a claim that texts match: a neighbouring line may carry an omission or addition. Never auto-extend a human/validated link. PAGE and ALTO share the physical_lines interface; neither source is modified.
**Dépendances internes observées** : `physical_alignment`
**Fonctions au premier niveau** : `_box` (l.17), `_cy` (l.28), `_overlap` (l.32), `_same_column` (l.37), `_local_pitch` (l.41), `_linked_info` (l.55), `_nearest_group` (l.78), `suggest_residual_extensions` (l.113), `apply_residual_extensions` (l.218)

## `varians_synchro/resource_workflow.py` (146 lignes)
**Objet (docstring source)** : Witness-centered project resources, with non-destructive staged import. The physical-line alignment model is deliberately not touched. Source files are only inspected, never rewritten. GUI dialogs collect selections first; ``apply_witness_draft`` commits them as one coherent project change.
**Dépendances internes observées** : `core`, `errors`, `imaging`, `page_order`, `tei_binding`
**Fonctions au premier niveau** : `_local_key` (l.22), `_manifest_key` (l.26), `_xml_kind` (l.31), `store_tei_reference` (l.38), `set_project_pivot` (l.63), `resource_summary` (l.69), `apply_witness_draft` (l.82)

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

## `varians_synchro/textual_progress.py` (338 lignes)
**Objet (docstring source)** : V0.7.1: linear, multi-folio text-quantity alignment between human anchors. The two streams are *declared homologous by the editor*: this module never tries to prove equivalence through geometry or OCR. Weight-based cuts are only *tentative* estimates of manuscript line segmentation. No source, existing link, line UID, or TEI is changed by previewing. Protected links (manual / validated / absence) form immutable obstacles. Automatic groups may be recalculated after explicit confirmation with the existing atomic writer.
**Dépendances internes observées** : `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `_chars` (l.23), `_length` (l.28), `_weights` (l.48), `_cumulative` (l.107), `_partition` (l.116), `_method` (l.164), `_segments` (l.172), `suggest_textual_progress` (l.266)

## `varians_synchro/ui_batch_binding.py` (209 lignes)
**Objet (docstring source)** : Fenêtre « Associer automatiquement les images et les ALTO/PAGE » : propositions par lot, que l’utilisateur peut modifier.
**Dépendances internes observées** : `bulk_binding`, `errors`, `i18n`, `ui_widgets`
**Classes déclarées au premier niveau** : `ProtectedBindingComboBox` (l.14), `BatchBindingDialog` (l.26)

## `varians_synchro/ui_help.py` (282 lignes)
**Objet (docstring source)** : Aide intégrée de Varians-Synchro : le guide ``help/<langue>.html`` affiché dans une fenêtre du logiciel (et non plus un fichier ouvert par une autre application). La fenêtre n'est pas modale : on lit l'aide en travaillant. ``open_help`` en garde une par fenêtre parente ; ouverte depuis la fenêtre de synchronisation (elle-même modale), elle en est l'enfant et reste donc utilisable. Recherche reprise de Varians (``help_search``) : un champ (Ctrl+F), la liste des sections qui contiennent tous les mots, avec un extrait, et les occurrences surlignées, parcourues par ◀ ▶ (F3, Maj+F3). Le sommaire, fait de liens, n'est pas une section.
**Dépendances internes observées** : `errors`, `help_search`, `i18n`, `ui_widgets`
**Classes déclarées au premier niveau** : `HelpDialog` (l.41)
**Fonctions au premier niveau** : `help_path` (l.31), `open_help` (l.264)

## `varians_synchro/ui_main_window.py` (672 lignes)
**Objet (docstring source)** : Fenêtre principale de Varians-Synchro : projet et témoins, pages, synchronisation, avancement et exports.
**Dépendances internes observées** : `core`, `errors`, `i18n`, `physical_alignment`, `project_state`, `resource_workflow`, `tei_binding`, `ui_batch_binding`, `ui_help`, `ui_pages`, `ui_pair`, `ui_resources`, `ui_scope`, `ui_tei_binding`, `ui_widgets`, `validation`, `varians_export`, `varians_project_export`
**Classes déclarées au premier niveau** : `_PairList` (l.27), `GuidedWindow` (l.44)

## `varians_synchro/ui_pages.py` (581 lignes)
**Objet (docstring source)** : Fenêtre « Images et associations ALTO/PAGE » d’un témoin : ordre des pages, association des XML, copies HD et export pour une HTR.
**Dépendances internes observées** : `errors`, `hd_registry`, `i18n`, `imaging`, `page_management`, `page_order`, `physical_alignment`, `reading_stream`, `ui_batch_binding`, `ui_widgets`, `viewer`
**Classes déclarées au premier niveau** : `DraggablePagesList` (l.22), `HDDownloadThread` (l.35), `HTRExportThread` (l.72), `PagesDialog` (l.97)

## `varians_synchro/ui_pair.py` (959 lignes)
**Objet (docstring source)** : Fenêtre « Synchronisation visuelle entre témoins » : groupes de lignes de deux témoins, propositions, révision rapide et revalidation.
**Dépendances internes observées** : `correspondence_navigation`, `errors`, `exceptions`, `i18n`, `interpolation`, `line_scope`, `overlay_filters`, `physical_alignment`, `rapid_review`, `reading_stream`, `residual_alignment`, `tei_binding`, `textual_progress`, `ui_help`, `ui_proposals`, `ui_reading_order`, `ui_widgets`, `viewer`
**Classes déclarées au premier niveau** : `PairDialog` (l.33)

## `varians_synchro/ui_proposals.py` (88 lignes)
**Objet (docstring source)** : Fenêtre où l'on choisit, parmi des propositions calculées, celles à enregistrer ; outils communs aux fenêtres de propositions de la synchronisation (HTR–HTR, progression textuelle, interpolation géométrique, lignes résiduelles). La fenêtre ne fait que montrer et sélectionner : chaque appelant garde ses vérifications, ses confirmations et son enregistrement (``add_buttons``).
**Dépendances internes observées** : `physical_alignment`, `ui_widgets`
**Classes déclarées au premier niveau** : `ProposalReviewDialog` (l.43)
**Fonctions au premier niveau** : `line_names` (l.16), `named` (l.21), `replaced_machine_groups` (l.26), `ask` (l.36)

## `varians_synchro/ui_reading_order.py` (185 lignes)
**Objet (docstring source)** : Fenêtre « Ordre de lecture » : pages, régions et lignes d’un témoin.
**Dépendances internes observées** : `errors`, `i18n`, `imaging`, `page_order`, `reading_stream`, `ui_widgets`
**Classes déclarées au premier niveau** : `ReadingOrderDialog` (l.15)

## `varians_synchro/ui_resources.py` (202 lignes)
**Objet (docstring source)** : Fenêtre « Ajouter un témoin… » / « Modifier le témoin et ses ressources » : sigle, images, XML, TEI et Manifests IIIF, appliqués d’un bloc.
**Dépendances internes observées** : `errors`, `i18n`, `resource_workflow`, `ui_batch_binding`, `ui_widgets`
**Classes déclarées au premier niveau** : `WitnessResourceDialog` (l.17)

## `varians_synchro/ui_scope.py` (85 lignes)
**Objet (docstring source)** : Fenêtre « Périmètre » : lignes d’un témoin exclues de l’étude.
**Dépendances internes observées** : `errors`, `i18n`, `line_scope`, `ui_widgets`, `viewer`
**Classes déclarées au premier niveau** : `SingleWitnessScopeDialog` (l.14)

## `varians_synchro/ui_tei_binding.py` (449 lignes)
**Objet (docstring source)** : Fenêtre « Liaison TEI ↔ lignes physiques » : contrôle visuel d’une ligne TEI sur l’image, sur un brouillon du projet.
**Dépendances internes observées** : `errors`, `i18n`, `tei_binding`, `tei_visual`, `ui_widgets`, `viewer`
**Classes déclarées au premier niveau** : `TEILineFetchThread` (l.23), `TEIReviewCard` (l.39), `TEIPhysicalBindingDialog` (l.164)

## `varians_synchro/ui_widgets.py` (132 lignes)
**Objet (docstring source)** : Widgets Qt qui traduisent leurs textes, ouverture modale d'une fenêtre et appels différés liés à une fenêtre. Les fenêtres de l'interface utilisent ces classes à la place de celles de PySide6 : un texte passé à ``QLabel``, ``setWindowTitle`` ou ``QMessageBox.warning`` est une clé de traduction (ou un texte français connu des catalogues) et s'affiche dans la langue choisie.
**Dépendances internes observées** : `i18n`
**Classes déclarées au premier niveau** : `QLabel` (l.49), `QPushButton` (l.58), `QListWidget` (l.67), `QComboBox` (l.72), `QTabWidget` (l.79), `QTreeWidget` (l.84), `QDialog` (l.89), `QMainWindow` (l.94), `QMessageBox` (l.99), `QInputDialog` (l.114), `QFileDialog` (l.123)
**Fonctions au premier niveau** : `_run_modal` (l.21), `call_soon` (l.33)

## `varians_synchro/validation.py` (163 lignes)
**Objet (docstring source)** : Read-only V0.7.4 preflight for documentary streams and physical pairs. The audit NEVER repairs historical links, guesses an omission, or modifies data. Warnings may reflect unavailable external resources on a different workstation. Hard errors mark contradictions that must not be silently treated as reliable.
**Dépendances internes observées** : `core`, `physical_alignment`, `reading_stream`, `tei_binding`, `varians_export`
**Fonctions au premier niveau** : `_item` (l.17), `audit_project` (l.26)

## `varians_synchro/varians_export.py` (423 lignes)
**Objet (docstring source)** : Export physical-line sessions to the Varians alignment JSON schema. Opening the exported project in Varians 0.9.4.0 is checked by tests/test_varians_094_compat.py (the real Varians code reads it). Lines are written in the witness's reading order (reading_stream). One explicit technical reference witness is used for these export files. This DOES NOT magically create an editorial TEI line mapping. The TEI XML <lb/> line IDs must still be reconciled with the physical reference's page::ordinal keys before manuscript-to-edition synchronization is guaranteed. No network, Qt, or local source-image files are required for the export.
**Dépendances internes observées** : `errors`, `imaging`, `page_order`, `physical_alignment`, `reading_stream`
**Fonctions au premier niveau** : `_get_witness` (l.33), `_image_block` (l.37), `_build_witness_cache` (l.54), `_line_fingerprint` (l.108), `_shared_pero_uuid` (l.115), `_safe_same_segmentation_after_format_change` (l.128), `_reference_health` (l.158), `_pair_for_base` (l.170), `make_varians_alignments` (l.178), `inspect_varians_export` (l.274), `verify_export_payloads` (l.321), `export_varians_alignments` (l.365)

## `varians_synchro/varians_project_export.py` (341 lignes)
**Objet (docstring source)** : Build a directly openable Varians project.xml bundle from Synchro resources. Target syntax: Varians's documented teiManuscriptProject format with one TEI edition. This is a physical mapping export; it does NOT assert that line links have been reconciled with TEI <lb/> unless the editor independently confirms it. The caller must run a final integration test against their installed Varians.
**Dépendances internes observées** : `core`, `errors`, `hd_registry`, `varians_export`
**Fonctions au premier niveau** : `_varians_safe_id` (l.24), `_source_path` (l.29), `_relative_or_absolute` (l.36), `_cache_varians_manifest` (l.42), `blank_tei_edition` (l.91), `export_varians_project` (l.122)

## `varians_synchro/viewer.py` (744 lignes)
**Objet (docstring source)** : Reusable manuscript page viewer with clickable ALTO overlay. Images can be IIIF or local. Full physical lines are the interaction unit; HTR is supplementary and never needed for visual selection. A 4200px-wide IIIF request provides useful magnification without downloading all canvases.
**Dépendances internes observées** : `alto_geometry`, `errors`, `i18n`, `imaging`, `overlay_filters`, `overlay_selection`, `page_order`, `physical_alignment`, `reading_stream`, `selection_policy`, `ui_widgets`
**Classes déclarées au premier niveau** : `FetchThread` (l.30), `ZoomableGraphicsView` (l.57), `ClickableLine` (l.78), `WitnessLineList` (l.147), `LineImagePanel` (l.169), `PageViewer` (l.727)

## Attention à la lecture

Les méthodes des classes (notamment celles des fenêtres `ui_*`), les fonctions de tests et les importations dynamiques ne sont pas détaillés ici. Cette liste est **un point d’entrée**, pas une analyse d’appels complète. Les dépendances proviennent d’une inspection syntaxique (AST) et peuvent inclure des chemins conditionnels. Pour les contrats, consulter les chapitres métiers du dossier.
