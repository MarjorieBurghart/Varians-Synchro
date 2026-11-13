# Première reprise : protocole de démarrage sécurisé

## 1. Conserver le point de départ

- Décompresser **dans un dossier de travail neuf** ; conserver intacte l'archive officielle et son empreinte SHA-256.
- Le code est désormais suivi dans le dépôt Git `MarjorieBurghart/Varians-Synchro` : l'historique Git remplace les anciennes listes d'empreintes SHA-256 (`SHA256SUMS.txt`, `MANIFEST_SHA256.json`), retirées. La livraison v0.8.5.6 d'origine est la release `v0.8.5.6`.
- Constituer un dépôt Git si nécessaire : importer une première révision de la livraison, puis développer sur une branche ; ne pas afficher de fausses informations de commit ou de licence.
- Ne **jamais** exécuter un test d'écriture sur un projet scientifique original. Travailler sur une copie de `.vsynch` et de ses ressources.

## 2. Environnement

Python 3.10+ (annotations `|`, `Path.is_relative_to`, etc.) ; recommandé un environnement isolé cohérent Python/PySide6. Dépendance déclarée : `PySide6>=6.6,<7` dans `requirements.txt`. Le noyau des outils en ligne de commande et de nombreux tests ne dépend pas de Qt. Pour les tests : `requirements-dev.txt` (application et `pytest`). Versions testées : `constraints.txt` (`-c constraints.txt`), qu'emploient la CI et la construction des archives. Sur Windows/Spyder, utiliser l'interpréteur actif **du même environnement**, pas un Python supposé global.

```bash
python -m venv .venv
# Activer .venv avec la commande propre au système
python -m pip install -r requirements-dev.txt -c constraints.txt
python -m compileall -q varians_synchro tests
python -m pytest -q
python run.py
```

Sous Windows, `start_windows.bat` lance `py -3 run.py` : il peut donc sélectionner un autre Python que celui du venv si celui-ci n'est pas activé. Pour les diagnostics Spyder : `python diagnostic_spyder.py`, `python diagnostic_flux_lecture.py`, `python start_isolated.py` selon le besoin ; consulter aussi [`GUIDE_DEPANNAGE_SPYDER.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_DEPANNAGE_SPYDER.md) et [`GUIDE_STABILITE_SPYDER.md`](https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/GUIDE_STABILITE_SPYDER.md).

## 3. Premiers fichiers à ouvrir

`run.py` → `varians_synchro/gui.py` → `varians_synchro/guided_ui.py` (point d'entrée) → `varians_synchro/ui_main_window.py` (fenêtre principale). Côté données : `core.py` et `resource_workflow.py`; appariement : `physical_alignment.py`, `reading_stream.py`, `textual_progress.py`; TEI : `tei_binding.py`; export : `varians_export.py`, `varians_project_export.py`.

L'interface est répartie en modules `ui_*` : une fenêtre par module (liste dans `03_CARTE_DU_CODE.md`). Lire d'abord leurs appels à la logique métier et les opérations d'ouverture/sauvegarde de `ui_main_window.py` ; ne pas commencer par une refonte cosmétique qui changerait l'ordre des mutations.

## 4. Opérations sans risque sur une copie

```bash
python creer_demo.py --help
python audit_vsynch.py CHEMIN_COPIE.vsynch --base Mu
python recette_v085.py CHEMIN_COPIE.vsynch --base Mu --check-paths --output rapport_recette.json
python verifier_base_keys_json.py CHEMIN_EXPORT/validated/F.json
```

`creer_demo.py` : recrée la démonstration livrée dans `demo_local_ALTO/` (deux témoins A et B, ALTO et images synthétiques), avec des chemins relatifs ; elle s'ouvre telle quelle, sans relancer ce script. L'exemple de `Mu` est illustratif : utiliser le véritable sigle présent dans le projet audité. `--check-paths` signale des dépendances externes absentes, ce qui peut être normal après déplacement d'un projet.

## 5. Configuration documentaire minimale

Un utilisateur novice doit toujours pouvoir commencer avec un témoin, une image locale et aucun TEI ni IIIF ni synchronisation. Le projet sait évoluer vers plusieurs témoins, ressources ALTO/PAGE et liaisons TEI. **Ne pas faire des couches avancées une condition d'ouverture ou de création.**

## 6. Fin de première journée (critère)

Être capable d'expliquer où sont : a) les lignes ALTO/PAGE et leurs UID, b) les groupes par paire, c) le choix du pivot, d) les liaisons TEI facultatives, e) les deux exportateurs et leur niveau de preuve ; fournir un résultat de tests daté et une liste de scénarios GUI à refaire.
