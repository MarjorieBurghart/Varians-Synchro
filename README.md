# Varians-Synchro

Varians-Synchro relie, ligne à ligne, les manuscrits d'une édition critique, pour [Varians](https://github.com/MarjorieBurghart/Varians). Il montre deux témoins côte à côte, avec le contour de chaque ligne ; vous placez quelques repères, il propose les correspondances intermédiaires d'après la quantité de texte, vous les vérifiez sur les images et les validez. Chaque témoin est aligné sur un témoin pivot. Le résultat s'exporte vers Varians : un fichier de synchronisation par témoin, ou un projet Varians complet, prêt à ouvrir.

Les lignes viennent d'un logiciel de reconnaissance (eScriptorium, Transkribus, Kraken, PERO OCR…), en ALTO ou PAGE XML ; les images sont des fichiers locaux ou un Manifest IIIF. Varians-Synchro ne modifie jamais ces fichiers : tout son travail est dans le fichier de projet `.vsynch`.

*English: Varians-Synchro aligns the lines of manuscript witnesses for the Varians editor. The user guide exists in seven languages ([English](help/en.html)), as does the [developer guide](docs/developer/en.md).*

## Installer et lancer

**Version prête à l'emploi**, sans Python à installer : sur la [page des versions](https://github.com/MarjorieBurghart/Varians-Synchro/releases), une archive pour Windows, macOS (Apple Silicon ou Intel) ou Linux. Décompressez-la et lancez Varians-Synchro ; son `LISEZMOI.txt` (sept langues) explique le premier lancement d'un logiciel non signé. `Varians-Synchro --self-test rapport.json` vérifie l'installation. Construction : [`packaging/LISEZMOI.md`](packaging/LISEZMOI.md).

**Avec Python** : Python 3.10 ou plus récent, et PySide6 (`requirements.txt`). Windows, macOS et Linux.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt     # Windows : .venv\Scripts\python.exe
.venv/bin/python run.py
```

`start_windows.bat` et `start_unix.sh` lancent `run.py`. Sous Spyder, `run.py` démarre l'application dans un processus séparé. Détails : [`docs/developer/PORTABILITE.md`](docs/developer/PORTABILITE.md).

## Aide

Le guide utilisateur s'ouvre dans le logiciel par **Ouvrir le guide utilisateur** ou **F1**, dans la langue de l'interface : présentation, premier essai, création d'un projet Varians, ajout d'un témoin à un projet existant, chaque étape et le format des fichiers de synchronisation. Ses fichiers sont dans `help/` ([français](help/fr.html), [English](help/en.html), [Deutsch](help/de.html), [čeština](help/cs.html), [italiano](help/it.html), [русский](help/ru.html), [日本語](help/ja.html)).

Pour un premier essai, le dossier `demo_local_ALTO/` contient un petit projet d'exemple (`exemple.vsynch`, deux témoins d'une page) : copiez-le ailleurs et suivez la section « Premier essai » du guide.

## Pour reprendre le code

- [`DOCS_INDEX.md`](DOCS_INDEX.md) : la liste des documents.
- [Dossier de maintenance et de passation](MAINTENANCE_PASSATION_V0856/00_LIRE_EN_PREMIER.md) : contrats des données, architecture, carte du code, tests, décisions.
- [`docs/developer/`](docs/developer/fr.md) : guide du développeur (sept langues) et références techniques (architecture, format `.vsynch`, export vers Varians, internationalisation, portabilité).
- [`CHANGELOG.md`](CHANGELOG.md) : les changements de chaque version ; les anciennes notes de livraison sont dans l'historique Git ([`docs/HISTORIQUE.md`](docs/HISTORIQUE.md)).

## Tests

```sh
python -m pip install -r requirements-dev.txt -c constraints.txt
python -m pytest -q
python tools/check_maintenance.py
python -m ruff check .
```

`python -m ruff check .` vérifie le code avec des règles minimales, qui ne visent que de vrais défauts (`ruff.toml`) : import ou variable inutilisés, nom non défini, erreur de syntaxe, argument par défaut modifiable, fonction créée dans une boucle qui voit la variable de la dernière itération. Le style n'est pas vérifié. La CI le lance avant les tests.

`constraints.txt` fixe les versions testées des dépendances (PySide6, pytest ; lxml et Saxon pour les tests de compatibilité avec Varians ; outils de construction des archives). La CI et la construction des archives l'emploient : une nouvelle version de PySide6 ne change pas une release sans qu'on l'ait voulu. Sans `-c constraints.txt`, pip prend les dernières versions permises. Pour monter une version : l'installer, lancer toute la suite des tests et la vérification d'une installation construite (`packaging/build.py`), puis changer `constraints.txt` dans un commit à part.

Les tests de l'interface pilotent les fenêtres Qt (sans écran : `QT_QPA_PLATFORM=offscreen`). Les tests de compatibilité ouvrent les projets exportés avec le vrai code de Varians : placer son code source à côté (`../Varians`) ou indiquer son dossier dans `VARIANS_SOURCE`. La CI GitHub rejoue l'ensemble sous Linux, Windows et macOS, avec Varians 0.9.4.6 ; le projet exporté y est aussi ouvert dans la vraie fenêtre de Varians.
