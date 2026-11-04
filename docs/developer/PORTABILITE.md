# Portabilité de Varians-Synchro

Varians-Synchro est une application **Python 3 / PySide6 multiplateforme**.
La conception ne repose ni sur Windows ni sur Spyder : Windows, macOS et Linux
sont des environnements visés, sous réserve de la disponibilité de Python et
de PySide6 pour l'architecture et la version du système concernées.

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

Les tests sans interface Qt ont été exécutés dans un environnement Linux.
Le rendu et les interactions de fenêtre doivent encore être testés avec PySide6
sur Windows, macOS et Linux. Le logiciel n'est pas garanti sur **toutes** les
plateformes pouvant exécuter Python si PySide6 et ses bibliothèques Qt natives
ne sont pas disponibles.
