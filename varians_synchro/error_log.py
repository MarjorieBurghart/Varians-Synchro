"""Journal des erreurs de Varians-Synchro, sans Qt (comme celui de Varians).

Quand quelque chose échoue chez un utilisateur, il en reste une trace, qu'il
peut envoyer : le fichier ``varians-synchro.log``, dans le dossier de
``log_dir`` (bouton « Journal des erreurs » de la fenêtre d'aide, ou de la
boîte « Action impossible »). Il garde au plus ``MAX_BYTES`` octets, plus
``BACKUPS`` fichiers plus anciens (``varians-synchro.log.1``, ``.2``).

``install`` (appelé au démarrage de l'interface, voir ``error_log_ui``)
ouvre le journal, y écrit une ligne d'en-tête (versions de Varians-Synchro,
de Python, de Qt et du système) et y note les exceptions non rattrapées, du
fil principal (``sys.excepthook``, que PySide6 appelle aussi pour une erreur
dans un clic) comme des autres fils (``threading.excepthook``) ; le crochet
précédent est toujours appelé ensuite, si bien que rien d'autre ne change.
Les modules y écrivent par ``logger(nom)`` : erreurs montrées à
l'utilisateur (``errors.localized_text``), Manifest IIIF qui n'a pas
répondu…

Le journal ne gêne jamais le logiciel : si son dossier ne peut pas être créé
ou son fichier ouvert, ``install`` rend None et rien ne change ; une écriture
qui échoue ensuite est ignorée (``logging``).

Il contient des noms de fichiers, des adresses et des messages d'erreur,
jamais le texte des transcriptions.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import platform as _platform
import sys
import threading
from pathlib import Path

ENVIRONMENT = 'VARIANS_SYNCHRO_LOG_DIR'
FILE_NAME = 'varians-synchro.log'
MAX_BYTES = 1_000_000
BACKUPS = 2
LOGGER = 'varians_synchro'
_FORMAT = '%(asctime)s %(levelname)s [%(process)d %(threadName)s] %(name)s : %(message)s'

# Sans journal, rien n'est écrit sur la sortie d'erreur par ce logger.
logging.getLogger(LOGGER).addHandler(logging.NullHandler())

_state = {'handler': None, 'path': None, 'excepthook': None, 'thread_hook': None}


def log_dir(platform=None, environ=None, home=None) -> Path:
    """Dossier du journal : ``VARIANS_SYNCHRO_LOG_DIR`` s'il est donné, sinon
    ``%LOCALAPPDATA%\\Varians-Synchro\\logs`` sous Windows,
    ``~/Library/Logs/Varians-Synchro`` sous macOS et ``$XDG_STATE_HOME`` (ou
    ``~/.local/state``) ``/varians-synchro/logs`` ailleurs."""
    platform = sys.platform if platform is None else platform
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else Path(home)
    override = (environ.get(ENVIRONMENT) or '').strip()
    if override:
        return Path(os.path.abspath(os.path.expanduser(override)))
    if platform == 'win32' and environ.get('LOCALAPPDATA'):
        return Path(environ['LOCALAPPDATA']) / 'Varians-Synchro' / 'logs'
    if platform == 'darwin':
        return home / 'Library' / 'Logs' / 'Varians-Synchro'
    state = (environ.get('XDG_STATE_HOME') or '').strip()
    root = Path(state) if state and os.path.isabs(state) else home / '.local' / 'state'
    return root / 'varians-synchro' / 'logs'


def logger(name) -> logging.Logger:
    """Logger d'une partie du logiciel (``varians_synchro.<name>``), qui écrit
    dans le journal une fois celui-ci ouvert."""
    return logging.getLogger(f'{LOGGER}.{name}')


def installed() -> bool:
    """Vrai si le journal est ouvert."""
    return _state['handler'] is not None


def journal_path() -> Path | None:
    """Fichier du journal ouvert, ou None."""
    return _state['path']


def install(header, directory=None) -> Path | None:
    """Ouvre le journal (une seule fois) dans ``directory`` (``log_dir()``
    par défaut), y écrit ``header`` avec les versions de Python et du
    système, et y note désormais les exceptions non rattrapées. Rend le
    chemin du fichier, ou None s'il ne peut pas être écrit."""
    if installed():
        return _state['path']
    folder = Path(directory) if directory is not None else log_dir()
    path = folder / FILE_NAME
    try:
        folder.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding='utf-8')
    except (OSError, ValueError):
        return None
    handler.setFormatter(logging.Formatter(_FORMAT))
    root = logging.getLogger(LOGGER)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    _state.update(handler=handler, path=path, excepthook=sys.excepthook, thread_hook=threading.excepthook)
    sys.excepthook = _excepthook
    threading.excepthook = _thread_excepthook
    root.info('%s ; Python %s ; %s', header, sys.version.split()[0], _platform.platform())
    return path


def uninstall() -> None:
    """Ferme le journal et rend les crochets d'exceptions d'avant (tests)."""
    handler = _state['handler']
    if handler is None:
        return
    if sys.excepthook is _excepthook:
        sys.excepthook = _state['excepthook']
    if threading.excepthook is _thread_excepthook:
        threading.excepthook = _state['thread_hook']
    logging.getLogger(LOGGER).removeHandler(handler)
    handler.close()
    _state.update(handler=None, path=None, excepthook=None, thread_hook=None)


def _excepthook(kind, value, traceback):
    previous = _state['excepthook'] or sys.__excepthook__
    if not issubclass(kind, KeyboardInterrupt):
        logging.getLogger(LOGGER).error('Exception non rattrapée', exc_info=(kind, value, traceback))
    previous(kind, value, traceback)


def _thread_excepthook(args):
    if not issubclass(args.exc_type, SystemExit):
        name = args.thread.name if args.thread is not None else '?'
        logging.getLogger(LOGGER).error('Exception non rattrapée dans le fil %s', name,
                                        exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    (_state['thread_hook'] or threading.__excepthook__)(args)
