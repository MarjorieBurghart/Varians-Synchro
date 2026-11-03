# Varians-Synchro v0.8.5.6 — dossier complet de maintenance et passation

**Date** : 19 octobre 2026. **Nature de version** : documentaire et outillage d'audit, **sans changement fonctionnel du moteur**.

## Changements

- `MAINTENANCE_PASSATION_V0856/` : dossier indépendant des guides utilisateur ; 15 chapitres et 2 annexes, architecture/flux, cartographie code, contrats `.vsynch`, algorithmes et invariants, TEI, IIIF/ALTO/PAGE, exports Varians, GUI/i18n, tests et recette, conventions, risques, 15 ADR et checklist de reprise.
- `tools/generate_module_inventory.py` : inventaire des 37 fichiers Python du package par analyse AST, sans import Qt ni effets de bord ; résultat dans `annexes/INVENTAIRE_MODULES_AUTOGENERE.md`.
- `tools/check_maintenance.py` : contrôle des chapitres, références Markdown, clé de version, 7 × 653 traductions, fraîcheur de l'inventaire AST et deux listes SHA-256 de livraison ; lecture seule.
- `tests/test_maintenance_0856.py` : nouveaux contrôles documentaires automatisés.
- Liens de reprise ajoutés dans `README.md`, `DOCS_INDEX.md`, `docs/developer/fr.md`.
- Constante `varians_synchro/core.py : VERSION = '0.8.5.6'`. Le `format` et `version` des projets `.vsynch` ne changent pas.

## Exclusions volontaires

- Aucune modification de la logique d'appariement, des exports, du format `.vsynch`, des 653 clés des sept catalogues, ou du rendu Qt.
- Aucun test d'import réel dans un build courant de Varians, aucune recette PySide6 native Windows et aucune certification par traducteur natif ne peuvent être déduits de la présence de la documentation.

**Résultats des tests de cette archive** : voir `TESTS_V0856.md`.
