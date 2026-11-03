# Developer maintenance handbook — Varians-Synchro V0.8.5.5

## Mission and architectural boundaries

Python/PySide6 application for physical-line alignment across manuscript witnesses. It imports local/IIIF images, ALTO/PAGE segmentation and optional TEI; it does **not** edit TEI, ALTO or PAGE sources. Preserve the V0.7.4 text-progress matching engine and never silently overwrite validated/manual correspondence groups.

## Entry points and environment

`run.py` starts the GUI. `start_windows.bat` and `start_unix.sh` provide launchers; `start_isolated.py` and `spyder_launch.py` isolate Qt from Spyder. `recette_v085.py` and `audit_vsynch.py` are read-only, headless audits. Install PySide6 for actual GUI testing. Skipped Qt tests do not prove GUI correctness.

## Data contracts and invariants

- `.vsynch`: versioned JSON, stable witness/page/line/Canvas identities, atomic saving, previous revision `.vsynch.bak`; no mutation on load. Project and GUI state must only switch together after success.
- Physical stream: ALTO bounding boxes and PAGE polygons, reading order spanning columns/folios, manual rearrangement retained, ignored lines excluded but not deleted.
- Pair alignments: validated/uncertain n↔m groups and pair-local explicitly confirmed absences. Never infer F↔A correspondence transitively via Mu.
- V0.7.4 progression: anchors define corresponding text intervals, cumulative text size estimated from usable HTR, geometry or uniform fallback. Keep human-approved anchors and groups immutable during automatic updates.
- TEI: witness-specific `<lb edRef="#ID"/>`; apparatus `<app>/<lem>/<rdg>` requires determinable `@wit` readings. Track source and scope fingerprints; do not silently reuse stale links.
- Varians export: `validated/` and `working/` JSON, `base_keys` referencing physical base lines, transactional publishing; `varians_project_export.py` prepares `project.xml` and optional local HD cache. Parser compatibility is not full GUI integration certification.
- IIIF HD: Canvas identifiers, image source, file path and SHA-256 in `images.json`; only use local copies for a witness when **all required segmented Canvas** have verified copies, allowing several download batches.

## Localization and end-user documentation

External XML catalogs in `i18n/`, loaded by `varians_synchro/i18n.py`; key and format-placeholder equality is mandatory. Data identifiers, manuscript transcriptions, filenames and URLs must never be translated. V0.8.5.5 replaces all 244 identified English fallbacks in each of de/cs/it/ru/ja. See `docs/i18n_coverage.json` and `docs/I18N_NATIVE_REVIEW_V0855.md`. Native-speaker and discipline-specific linguistic review remains outstanding. User guides are supplied in `docs/user/<lang>.md`; the main window opens the currently selected language.

## Test recipe

```bash
python -m compileall -q varians_synchro
PYTHONPATH=. pytest -q
python recette_v085.py projet.vsynch --base Mu --output audit.json
```

For Windows Qt acceptance, exercise create/open/save, language switching, a 469-Canvas Manifest with only five ALTO/PAGE, manual selection across folios, TEI revisions, cancelled and completed HD downloads, local-copy export coverage, and launching from Spyder. Compare canonical `validated` and `working` exports on `projetTest.vsynch` and `test081.vsynch` with the previous release, without modifying the fixtures.

## Module inventory (AST-derived from the source)

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

## Risks and change policy

- Keep the counterpart highlight distinct from user selection; a simple click replaces the whole witness selection.
- Never interpret unreachable IIIF as missing editorial evidence.
- Progress-dialog closure must not be interpreted as business-operation cancellation.
- Generate multi-file exports into staging folders and publish only complete validated results.
- Audit call sites before removing historical modules or migrating old project fields.
- Ask domain experts to proofread terminology, especially for medieval textual scholarship.

## Human handover sequence

Read `ARCHITECTURE.md`, `FORMAT_PROJET.md`, `PASSATION_DEV_V085.md`, `EXPORT_VARIANS.md` and TEI/HD guides; run headless Python tests; then perform Windows/PySide6 tests and open the exported project in the latest Varians editor.
