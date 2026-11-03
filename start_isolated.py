"""Explicit alternative: launch Varians-Synchro outside Spyder's Qt process."""
from varians_synchro.spyder_launch import launch_isolated

if __name__ == '__main__':
    try:
        path, pid = launch_isolated()
        print(f'Fenêtre indépendante lancée (PID {pid}); journal : {path}')
    except Exception as exc:
        print(f'Lancement impossible : {exc}')
        raise
