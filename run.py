"""Cross-platform GUI entrypoint, safe to execute from Spyder or a terminal.

Spyder uses its own native Qt runtime. To avoid mixing plugin paths or Qt
bindings inside Spyder's kernel, launch the GUI in a separate Python process
with the SAME interpreter. Direct terminal use remains unchanged.
"""
import faulthandler
import sys

from varians_synchro.spyder_launch import in_spyder_kernel, launch_isolated


def main():
    if in_spyder_kernel():
        try:
            logfile, pid = launch_isolated(__file__)
        except Exception as exc:
            print(f'Varians-Synchro : lancement isolé impossible : {exc}', file=sys.stderr)
            return 2
        print(f'Varians-Synchro lancé hors du noyau Spyder (PID {pid}).')
        print(f'Journal de démarrage : {logfile}')
        print('La fenêtre est indépendante : fermer Spyder ne fermera pas le projet.')
        return 0
    # In case of a fatal native Qt crash, record as much as Python can provide.
    faulthandler.enable()
    from varians_synchro.gui import main as qt_main
    return qt_main()


if __name__ == '__main__':
    # No SystemExit: keep Spyder interactive kernel unaffected.
    main()
