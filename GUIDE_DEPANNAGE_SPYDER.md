# Démarrage de Varians-Synchro sous Spyder

## 1. Identifier la cause exacte

Ouvrez `diagnostic_spyder.py` dans Spyder et exécutez-le (F5). Il affiche l'exécutable Python du **noyau Spyder** et le message d'erreur exact de PySide6. Le script n'installe rien et ne crée pas de fenêtre Qt.

Dans la console IPython de Spyder, vous pouvez également essayer :

```python
import sys
print(sys.executable)
import PySide6
print(PySide6.__version__)
from PySide6.QtWidgets import QApplication
```

## 2. Si `No module named PySide6`

Installez PySide6 **dans l'environnement Python du noyau Spyder**, pas dans un autre Python :

```python
%pip install "PySide6>=6.6,<7"
```

Si `%pip` n'est pas disponible, ouvrez un terminal et employez exactement le chemin donné par `print(sys.executable)` :

```powershell
"C:\CHEMIN\VERS\python.exe" -m pip install "PySide6>=6.6,<7"
```

Dans **PowerShell**, utilisez `& "C:\CHEMIN\VERS\python.exe" -m pip install ...`.
Redémarrez le noyau de Spyder après l'installation.

## 3. Si PySide6 existe mais ne s'importe pas

La trace complète indiquera la dépendance, la bibliothèque native ou le symbole manquant. Ne réinstallez pas aveuglément des paquets Qt : certains environnements utilisent PyQt et PySide en parallèle, ce qui peut entraîner des conflits. Conservez la sortie de `diagnostic_spyder.py` pour identifier le correctif adapté.

## 4. Alternative : exécuter le logiciel hors Spyder

Depuis le dossier du logiciel :

```powershell
py -3 -m pip install -r requirements.txt
py -3 run.py
```

Cette méthode utilise le Python sélectionné par `py -3`, qui **peut être différent** du Python de Spyder. Pour retrouver votre environnement précis, utilisez `sys.executable`.

## 5. Cycle de vie Qt

Varians-Synchro V0.5.2 conserve le correctif de la V0.5.1 : si un QApplication PySide6 existe, il le réutilise et ne lance pas une deuxième boucle Qt. Il n'exécute pas `app.exec()` une seconde fois dans Spyder.
