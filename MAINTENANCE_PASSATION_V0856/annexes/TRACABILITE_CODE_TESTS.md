# Traçabilité fonctions / tests / anciennes notes

| Risque ou exigence | Code à étudier | Tests existants | Source historique |
|---|---|---|---|
| Sauvegarde, backup, compatibilité | `core.py`, `project_state.py` | `test_core.py`, `test_unsaved_changes.py` | `FORMAT_PROJET.md`, `CORRECTIF_SAUVEGARDE_V0.7.2.1.md` |
| Création/ouverture transactionnelles | `ui_main_window.py` | `test_project_open_creation_regression_0812.py` | `CORRECTIF_OUVERTURE_PROJET_V0812.md` |
| Association pages-images-XML | `imaging.py`, `bulk_binding.py` | `test_resources_081.py`, `test_page_management.py` | `GUIDE_RESSOURCES_V081.md` |
| PAGE et polygones ALTO | `page_xml.py`, `alto_geometry.py`, `viewer.py` | `test_page_xml_support.py`, `test_alto_polygon_geometry.py` | `GUIDE_PAGE_XML.md` |
| Ordres et flux de lecture | `page_order.py`, `reading_stream.py` | `test_reading_stream.py`, `test_page_order.py` | `GUIDE_ORDRE_VISUEL_PAGES.md` |
| Groupe n↔m, liens protégés | `physical_alignment.py` | `test_physical_alignment.py`, `test_manual_group_editing.py` | `GUIDE_CORRECTIONS_MANUELLES.md` |
| Interpolation et poids de progression | `textual_progress.py`, `interpolation.py`, `residual_alignment.py` | `test_textual_progress.py`, `test_full_column_interpolation.py`, `test_residual_alignment.py` | `GUIDE_PROGRESSION_TEXTUELLE.md` |
| Absence confirmée et périmètre | `exceptions.py`, `line_scope.py` | `test_confirmed_exceptions.py`, `test_ignored_lines.py` | `GUIDE_EXCEPTIONS_EDITORIALES.md`, `GUIDE_PERIMETRE.md` |
| Liaison TEI | `tei_binding.py`, `tei_visual.py` | `test_tei_binding_083.py`, `test_tei_visual_084.py` | `GUIDE_LIAISON_TEI_V083.md`, `GUIDE_CONTROLE_VISUEL_TEI_V084.md` |
| Exports, base_keys et audit | `varians_export.py`, `varians_project_export.py`, `validation.py` | `test_varians_export.py`, `test_varians_export_audit.py` | `EXPORT_VARIANS.md`, `DIAGNOSTIC_BASE_KEYS.md` |
| Copies HD, Canvas, SHA-256 | `imaging.py`, `hd_registry.py` | `test_hd_registry_0853.py`, `test_hd_completion_0852.py` | `GUIDE_COPIES_HD_V0853.md` |
| I18n, langue Qt et runtime Spyder | `i18n.py`, `gui.py`, `spyder_launch.py` | `test_i18n_full_0855.py`, `test_spyder_launch.py` | `INTERNATIONALISATION.md`, `TESTS_V0855.md` |
| Icône de l'application, barre des tâches Windows | `app_icon.py`, `qt_lifecycle.py`, `gui.py`, `tools/generate_icons.py` | `test_app_icon.py`, `test_app_icon_qt.py`, `test_qt_lifecycle.py` | `MAINTENANCE_PASSATION_V0856/09_INTERFACE_ET_I18N.md` |
| Dossier lui-même | `tools/check_maintenance.py` | `test_maintenance_0856.py` | `CHANGELOG_V0856.md` |

Les noms de tests indiquent une **couverture à examiner**, et non la preuve que toutes les branches sont testées. Un changement critique demande en plus des tests ciblés sur les nouveaux cas.
