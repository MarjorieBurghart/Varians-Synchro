# Portabilité de Varians-Synchro

Varians-Synchro est une application **Python 3 / PySide6 multiplateforme**.
La conception ne repose ni sur Windows ni sur Spyder : Windows, macOS et Linux
sont des environnements visés, sous réserve de la disponibilité de Python et
de PySide6 pour l'architecture et la version du système concernées.

## Version prête à l'emploi

Une archive par système (Windows x64, macOS Apple Silicon et Intel, Linux
x64), sans Python à installer, est jointe à chaque release publiée par le
workflow « Binaries » (`.github/workflows/binaries.yml`). Elle est construite
par PyInstaller et vérifiée sur chacun de ces systèmes, fenêtre comprise, par
`Varians-Synchro --self-test` avant d'être publiée : voir
[`packaging/LISEZMOI.md`](../../packaging/LISEZMOI.md). Sous Linux, elle
demande glibc 2.35 ou plus récent (Ubuntu 22.04, Debian 12, Fedora 36…).

Les installations ci-dessous, avec Python, restent celles du développement. Elles prennent les dernières versions permises par `requirements.txt` ; pour les versions testées (celles de la CI et des archives), ajouter `-c constraints.txt` à la commande `pip install`.

## Installation sur Windows

Dans un terminal ouvert à la racine du dossier distribué :

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py
```

Le fichier `start_windows.bat` reste une commodité pour les postes où le
lanceur `py -3` dispose de PySide6. L'utilisation depuis Spyder est facultative.

## Installation sur Linux / macOS

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

Le script facultatif `start_unix.sh` lance `python3 run.py` (ou l'interpréteur
indiqué par `PYTHON`) depuis le dossier de l'application ; sous macOS/Linux
`./start_unix.sh` est utilisable si les droits d'exécution sont préservés.

## Principes techniques

- Les chemins de données sont construits avec `pathlib.Path`, sans concaténation
  de séparateurs propres à Windows.
- Le dossier `i18n/` est résolu relativement à l'emplacement réel du module,
  sans dépendre du répertoire courant ni de Spyder.
- Les données et images IIIF utilisent des API Python standard et des URL ;
  les images locales passent par le chargement Qt.
- La configuration de langue emploie `QSettings`, multiplateforme.
- Le cycle de vie Qt fonctionne dans un processus ayant déjà une
  `QApplication` (Spyder/Jupyter) ou dans un nouveau processus.
- La synchronisation physique ALTO–ALTO, l'interpolation géométrique et les
  fichiers `.vsynch` sont indépendants de la plateforme.

### Limites de validation

La suite de tests, interface Qt comprise (en mode `offscreen`), est rejouée par la CI GitHub sous Linux et sous Windows à chaque modification (`.github/workflows/tests.yml`). macOS n'y est pas ; il est vérifié par la construction de la version prête à l'emploi (`--self-test` sur macOS Apple Silicon et Intel, à chaque release et à chaque modification de `packaging/`). Il ne fonctionne pas sur une plateforme où PySide6 et ses bibliothèques Qt natives ne sont pas disponibles.
