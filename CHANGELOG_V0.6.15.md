# Varians-Synchro V0.6.15

- **Export direct JSON au format `tei-manuscript-alignment` (Varians 0.8.5.2)**, un fichier par témoin, avec `base_keys` et polygones PAGE si disponibles.
- Deux ensembles séparés : **validés** et **de travail (validés + propositions)**.
- Nouveau bouton « Exporter JSON pour Varians… » dans « 3 · Synchronisation », traduit en français/anglais dans les catalogues XML.
- Commande autonome `exporter_json_varians.py` pour Python Windows, macOS et Linux, sans PySide6.
- Détection des références périmées, protection des lignes ignorées et interdiction des remplacements silencieux.
- Récupération prouvée des anciennes associations PERO ALTO↔PAGE grâce à la concordance UUID + empreinte historique + texte + géométrie.
- Aucun transfert arbitraire vers une TEI encore absente : le témoin de base est **physique et provisoire**.
- 151 tests réussis, six tests d'interface Qt sautés faute de PySide6.
