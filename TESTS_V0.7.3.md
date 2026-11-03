# Validation V0.7.3

- **204 tests réussis** et **7 tests Qt ignorés faute de PySide6** dans l’environnement de fabrication. Deux suites héritées de l’ancien moteur géométrique (`test_full_column_interpolation.py` et `test_recalculation_existing_proposals.py`) n’ont pas été exécutées lors de cette passe, à cause de leurs temps d’exécution problématiques déjà repérés en V0.7.2.
- **10 nouveaux tests dédiés aux exceptions** réussis.
- Comparaison sur le projet de référence `projetTest.vsynch`, avant toute nouvelle exception : les exports JSON `validated` et `working` pour Mu/F/A sont **identiques bit à bit en sérialisation canonique** entre V0.7.2.3 et V0.7.3.
- Aucun test graphique PySide6 sous Windows n’a pu être exécuté ici ; il faut vérifier la boîte de confirmation, le raccourci `Ctrl+Maj+A` et les opérations de retrait sur une installation PySide6.

Commande exécutée depuis le dossier source :

```bash
PYTHONPATH=. pytest -q --ignore=tests/test_full_column_interpolation.py --ignore=tests/test_recalculation_existing_proposals.py
```
