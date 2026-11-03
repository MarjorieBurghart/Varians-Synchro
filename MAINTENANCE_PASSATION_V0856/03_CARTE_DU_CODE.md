# Cartographie mainteneur : responsabilités, composants et points d'entrée

**Inventaire exact des symboles :** `annexes/INVENTAIRE_MODULES_AUTOGENERE.md` (généré par analyse statique du code et reproductible). Dans cette livraison : **37 fichiers Python dans `varians_synchro`**, dont `__init__.py` ; **54 fichiers `tests/test_*.py`**.

## Vue des modules fonctionnels

| Groupe | Modules | Fonctions et décisions clés |
|---|---|---|
| Application | `gui`, `guided_ui`, `viewer`, `qt_lifecycle`, `spyder_launch` | Shell PySide6, états des fenêtres, sélection, images, processus Spyder |
| Projet, ressources | `core`, `project_state`, `resource_workflow`, `bulk_binding` | Format `.vsynch`, sauvegarde/backup, témoins, ressources, liaisons page↔XML |
| Pages et géométries | `imaging`, `page_xml`, `alto_geometry`, `hd_registry`, `page_order`, `page_management` | IIIF, ALTO/PAGE, polygones, copies HD, folios |
| Lignes et correspondances | `physical_alignment`, `reading_stream`, `line_scope`, `correspondence_navigation`, `selection_policy`, `overlay_selection`, `overlay_filters` | UID, flux physique, groupes, exclusion, navigation et surlignages |
| Algorithmes | `automatic`, `textual_progress`, `interpolation`, `residual_alignment`, `rapid_review`, `review`, `exceptions` | Propositions HTR, progression, corrections, validation, absences |
| Édition TEI | `tei_binding`, `tei_visual`, `alignment` | Extraction et rattachement TEI, preview, alignement historique |
| Export et vérification | `varians_export`, `varians_project_export`, `validation` | Deux niveaux de JSON, projet Varians, audit |
| Traduction | `i18n` | Chargement de sept catalogues XML, placeholders, changement de langue |

## Points d'entrée depuis la racine

| Script | Exécution attendue | Effets |
|---|---|---|
| `run.py` | GUI normale ou lancement isolé Spyder | Lance l'application ; Qt requis |
| `start_windows.bat`, `start_unix.sh` | Raccourcis locaux | Sélection de l'interpréteur, lancement `run.py` |
| `start_isolated.py` | Démarrage isolé pour dépannage | Lance une instance de l'application dans autre processus |
| `audit_vsynch.py` | `python audit_vsynch.py projet.vsynch [--base Mu]` | Audit sans écrire le projet |
| `recette_v085.py` | `python recette_v085.py projet.vsynch [--base Mu]` | Contrôles complets sans écrire le projet ; rapport éventuel |
| `exporter_json_varians.py` | `python exporter_json_varians.py projet.vsynch --base Mu --output DOSSIER` | Publie JSON et rapport dans dossier vide |
| `verifier_base_keys_json.py` | `python verifier_base_keys_json.py fichier.json` | Examen local d'un export JSON |
| `creer_demo.py` | Voir `--help` / lecture du script | Données de démonstration ; peut écrire des fichiers |
| `diagnostic_spyder.py`, `diagnostic_flux_lecture.py` | Diagnostic ponctuel | Contrôles d'environnement / lecture ; étudier options avant usage |
| `tools/generate_module_inventory.py` | `python tools/generate_module_inventory.py` | Régénère l'inventaire AST du présent dossier |
| `tools/check_maintenance.py` | `python tools/check_maintenance.py` | Vérifie dossier, liens internes, catalogues et empreintes |

## Points d'attention pour une refactorisation

`guided_ui.make_guided_window()` est une **factory** qui définit des composants Qt localement et relie de nombreuses fonctions métier. Ne pas déduire de l'absence de classes « top-level » que ce module n'a pas de classes. Le module `viewer.py` définit plusieurs classes Qt. `alignment.py` est une couche historique TEI conservée ; ne pas la supprimer tant que des projets antérieurs la nécessitent. L'exportateur `varians_project_export.py` n'est **pas** un simple wrapper de `varians_export.py` : il prépare également XML projet, TEI copiée, cache IIIF et ressources sous contraintes propres.

**Pour un changement donné**, identifier (1) contrat persistant, (2) branche métier, (3) appel GUI, (4) validations, (5) exports dépendants, (6) tests ; ne pas modifier un seul module en supposant que le flux s'y termine.
