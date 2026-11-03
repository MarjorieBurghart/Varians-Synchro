# Recette de Varians-Synchro V0.8.5.5

Testé le 18 octobre 2026 à partir de l'archive v0.8.5.4 transmise.

## Résultats

- `PYTHONPATH=. QT_QPA_PLATFORM=offscreen python -m pytest -q` : **319 tests réussis, 13 ignorés** (tests Qt non exécutés : PySide6 absent de l'environnement).
- `PYTHONPATH=. python -m compileall -q varians_synchro tests` : réussi ; compilation syntaxique de tous les modules et tests.
- Sept catalogues XML : **653 clés identiques** chacun, textes non vides, paramètres `{...}` conservés et remplacement par des valeurs fictives réussi.
- Cinq catalogues complétés : **244 clés par langue** issues des listes de replis de v0.8.5.4, soit **1 220 traductions** ajoutées.
- Les balises `<h3>`, `<lb/>` et les marqueurs `base_keys` sont conservés dans les chaînes concernées ; les paramètres de substitution testés sur les sept langues.
- Les catalogues non modifiés de français et d'anglais conservent leur contenu.
- Code Python de l'application : **seul `varians_synchro/core.py` change** par rapport à v0.8.5.4 (constante de version). Le fichier `tests/test_i18n_full_0855.py` est nouveau.
- Sommes SHA-256 recalculées dans `MANIFEST_SHA256.json` et `SHA256SUMS.txt` ; contrôle de l'archive après construction.

## Vérifications restantes

- Test visuel de toutes les fenêtres avec PySide6 sur Windows et dans les environnements macOS/Linux (aucune vérification GUI native dans cette session).
- Révision linguistique et scientifique des traductions par locuteurs natifs. Privilégier les confirmations d'absence, validations et exports ; voir `docs/I18N_NATIVE_REVIEW_V0855.md`.
- Test d'import de JSON dans la version de Varians utilisée localement ; les fonctionnalités d'export n'ont pas été modifiées.

**Ne pas assimiler la présence des 653 entrées à une traduction validée par des locuteurs natifs.**
