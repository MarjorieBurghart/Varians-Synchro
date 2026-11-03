# Procès-verbal de vérifications — Varians-Synchro v0.8.5.6

**Date :** 19 octobre 2026. **Base source :** archive v0.8.5.5 remise par l'utilisateur. **Objet :** refonte documentaire uniquement.

## Exécution locale de contrôle

| Contrôle | Résultat constaté |
|---|---|
| `python -m compileall -q varians_synchro tests tools` | OK |
| `python -m pytest -q` | **325 tests réussis, 13 ignorés**, aucun échec |
| `python tools/check_maintenance.py` | OK : sommaire, liens, 7 × 653 clés, inventaire AST, manifestes et versions |
| `python tools/generate_module_inventory.py` puis contrôle sans modification | Inventaire régénérable identique |
| Vérification ZIP `ZipFile.testzip()` | OK |
| Comparaison avec v0.8.5.5 | Tous les modules de `varians_synchro/` inchangés sauf la valeur de `VERSION` dans `core.py` ; sept catalogues et anciens tests inchangés |
| SHA-256 | Regénérés après création et vérifiés sur les fichiers effectivement empaquetés |

Les 13 tests ignorés concernent le contexte Qt/PySide6 **indisponible dans cet environnement** : ils ne doivent pas être présentés comme exécutés ni comme une vérification d'interface sous Windows.

## Périmètre non testé ici

- Exécution de `run.py` et inspection visuelle de toutes les fenêtres dans les sept langues, sur Windows, macOS et Linux avec PySide6.
- Contact réseau avec des serveurs IIIF réels, débit/annulation/erreurs HTTP.
- Import de `project.xml` et des JSON dans la **version actuelle de Varians** (contrat historique visé : Varians 0.8.x, JSON vérifié avec 0.8.5.2).
- Relecture native des catalogues allemand, tchèque, italien, russe et japonais.
- Tout projet scientifique original de l'utilisateur : aucun fichier de données réel non inclus dans l'archive n'a été ouvert ou modifié.

**Interprétation** : les tests démontrent une absence de régression détectée par la suite locale et l'intégrité de la documentation ; ils ne démontrent pas la réussite des scénarios GUI ou de la recette d'import externe.
