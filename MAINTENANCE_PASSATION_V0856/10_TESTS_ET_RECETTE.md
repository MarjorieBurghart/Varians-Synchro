# Procédures reproductibles de tests et de recette

## Niveau 1 — sans PySide6 / sans Internet

Depuis la racine décompressée :

```bash
python -m compileall -q varians_synchro tests
python -m pytest -q
python -m pytest -q tests/test_core.py tests/test_physical_alignment.py tests/test_source_integrity.py
python -m pytest -q tests/test_varians_export.py tests/test_varians_export_audit.py
python -m pytest -q tests/test_i18n_full_0855.py
python -m pytest -q tests/test_maintenance_0856.py
```

Le nombre de tests « ignorés » varie selon Qt et son installation. Un `skip` n'est pas une réussite du scénario graphique. Pour l'audit ponctuel de projets **copies** :

```bash
python audit_vsynch.py EXEMPLE.vsynch --base Mu --check-paths --output audit.json
python recette_v085.py EXEMPLE.vsynch --base Mu --strict --output recette.json
```

Un audit strict peut retourner 1 pour un **avertissement documentaire** nécessitant analyse humaine (source déplacée, absence de données pour un témoin secondaire), sans que l'application soit cassée. `recette_v085.py` garde un identifiant historique v0.8.5 dans son rapport : il ne certifie pas à lui seul toute version nouvelle. Ne pas modifier le projet source pendant l'audit.

## Niveau 2 — environnement Qt GUI

Installer PySide6, vérifier `python -c "import PySide6;print(PySide6.__version__)"`, puis exécuter `python -m pytest -q` et `python run.py`. L'usage de `QT_QPA_PLATFORM=offscreen` peut aider en CI pour certaines fenêtres, **pas** pour remplacer les tests d'interaction réelle et les chargements d'images du serveur.

**Intégration continue** : le workflow GitHub `.github/workflows/tests.yml` lance, à chaque envoi et pull request, la compilation, `tools/check_maintenance.py` et toute la suite (tests Qt compris, avec PySide6 et `QT_QPA_PLATFORM=offscreen`) sous Linux et Windows.

**Version prête à l'emploi** : le workflow `.github/workflows/binaries.yml` construit avec PyInstaller une archive pour Windows, macOS (Apple Silicon et Intel) et Linux, à chaque release publiée (archives jointes à la release) et à chaque modification de `packaging/`. Chaque exécutable construit est vérifié sur son système par `--self-test` (`varians_synchro/self_test.py` : traductions, aide, ressources, projet d'exemple, synchronisation et exports, fenêtre avec le module d'affichage du système) avant d'être zippé ; `tests/test_packaging.py` vérifie la recette sans construire. Voir [`packaging/LISEZMOI.md`](../packaging/LISEZMOI.md).

### Checklist de recette manuelle (Windows prioritaire)

- [ ] Démarrage normal depuis `python run.py`, et depuis Spyder en processus indépendant ; absence de double fenêtre intempestive.
- [ ] Création d'un projet avec **une image locale et aucun TEI** ; annulation de création/ouverture sans perdre l'état en cours.
- [ ] Ouverture du projet démo livré, sauvegarde dans une **copie**, réouverture : témoins, pivot, sources, affichages, ordre et liens identiques.
- [ ] Import ALTO puis PAGE sur des copies ; géométrie correcte, polygons visibles et coordonnées stables.
- [ ] Page sans XML OCR : aucune invention de lignes ; liaison automatique ambiguë laissée à valider.
- [ ] Ordre de pages / régions / lignes modifié : flux et validation de liaison TEI actualisés.
- [ ] Groupe 1↔2, groupes multiples, absence confirmée, ligne hors périmètre et restauration ; recalcul sans perte des validations.
- [ ] Changement de langue dans **les sept langues**, interface réaffichée, projet courant et modifications non sauvegardées préservés.
- [ ] Sélection clic/Ctrl/Maj, zoom/polygones, navigation par groupes et relecture rapide.
- [ ] Export JSON `validated` / `working` dans un dossier vide ; refus d'un dossier rempli ; compte des `base_keys` secondaires.
- [ ] Export projet complet depuis un pivot avec TEI ; import effectif dans la version visée de Varians ; géométrie et `base_keys` vérifiées sur Mu/F/L.
- [ ] IIIF : Manifest v2 et v3, images disponibles/indisponibles, copie HD complète/incomplète, annulation, enregistrement des SHA-256.
- [ ] Sauvegarde `.vsynch.bak` de l'état précédent après second enregistrement ; suppression de l'écriture finale simulée → original intact.

## Niveau 3 — tests de non-régression de données et publication

1. Faire une copie contrôlée d'un ancien `.vsynch` représentatif, relever le SHA-256 original.
2. Vérifier lecture sans mutation (`load_project`, audit), export vers un répertoire temporaire, ouverture/fermeture sans sauvegarde.
3. Comparer les identifiants UID des lignes, `pair_sessions`, états et dates de validations avant/après une sauvegarde **explicitement demandée**.
4. Vérifier les contrats JSON par `verify_export_payloads` (tous les témoins, pas juste un fichier secondaire isolé), polygones et Canvas.
5. Contrôler les sept catalogues avec `reload_catalogs`, et effectuer une validation native des formulations critiques.
6. Consigner pour chaque scénario : OS, Python/PySide6, commande exacte, entrée (copie de référence), SHA-256 avant/après, résultat, captures d'erreur et statut.

## Matrice tests ↔ domaines

| Domaine | Fichiers principaux |
|---|---|
| Persistance/projets/rétrocompatibilité | `test_core.py`, `test_project_open_creation_regression_0812.py`, `test_unsaved_changes.py` |
| Sessions/lectures/algorithmes | `test_physical_alignment.py`, `test_reading_stream.py`, `test_textual_progress.py`, `test_recalculation_existing_proposals.py` |
| Écarts et exceptions | `test_confirmed_exceptions.py`, `test_ignored_lines.py`, `test_residual_alignment.py` |
| TEI et images | `test_tei_binding_083.py`, `test_tei_visual_084.py`, `test_page_xml_support.py`, `test_alto_polygon_geometry.py` |
| IIIF et HD | `test_imaging.py`, `test_hd_completion_0852.py`, `test_hd_registry_0853.py` |
| Export et audit | `test_varians_export.py`, `test_varians_export_audit.py`, `test_source_integrity.py` |
| Qt/Spyder/localisation | `test_qt_lifecycle.py`, `test_spyder_launch.py`, `test_app_icon.py`, `test_app_icon_qt.py`, `test_i18n_xml_catalogs.py`, `test_i18n_full_0855.py` |
| Intégrité documentaire v0.8.5.6 | `test_maintenance_0856.py`, `tools/check_maintenance.py` |

**Résultats effectivement constatés** : pour la livraison v0.8.5.6, [`TESTS_V0856.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/TESTS_V0856.md) (historique Git) ; depuis, la CI GitHub (`.github/workflows/tests.yml`, Linux et Windows) rejoue la suite à chaque modification. Ne pas reporter les nombres d'une version comme s'ils validaient la suivante.
