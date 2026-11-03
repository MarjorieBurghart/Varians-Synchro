"""Diagnostic non destructif de l'environnement Qt actif.

Depuis Spyder : ouvrir ce fichier et le lancer avec F5 / %runfile.
Le script ne crée aucune QApplication : il ne perturbe pas l'interface déjà ouverte.
"""
import importlib
import importlib.util
import os
import platform
import sys
import traceback
from pathlib import Path


def check():
    print('=== DIAGNOSTIC VARIANS-SYNCHRO / SPYDER ===')
    print('Python :', sys.executable)
    print('Version :', platform.python_version())
    print('Prefix :', sys.prefix)
    print('QT_API :', os.environ.get('QT_API', '(non défini)'))
    for name in ('PySide6', 'PyQt6', 'PyQt5'):
        try:
            spec = importlib.util.find_spec(name)
            print(name, ':', spec.origin if spec is not None else 'NON TROUVÉ')
        except (ImportError, ValueError) as exc:
            print(name, ': recherche impossible :', repr(exc))
    print('Bindings Qt déjà chargés :', ', '.join(
        name for name in ('PySide6', 'PyQt6', 'PyQt5') if name in sys.modules) or 'aucun')
    try:
        side = importlib.import_module('PySide6')
        print('Version PySide6 :', getattr(side, '__version__', 'inconnue'))
        qtcore = importlib.import_module('PySide6.QtCore')
        qtwidgets = importlib.import_module('PySide6.QtWidgets')
        print('Qt :', qtcore.qVersion())
        for name in ('QApplication', 'QMainWindow', 'QDoubleSpinBox', 'QFileDialog'):
            getattr(qtwidgets, name)
            print(name + ' : OK')
        app = qtwidgets.QApplication.instance()
        print('QApplication existante :', 'oui' if app is not None else 'non')
        print('RESULTAT : PySide6 importable dans cet environnement.')
    except Exception:
        print('RESULTAT : erreur exacte de chargement :')
        traceback.print_exc()
        print('PySide6 introuvable ou non fonctionnel dans :', sys.executable)
    print('=== FIN DU DIAGNOSTIC ===')


if __name__ == '__main__':
    check()
