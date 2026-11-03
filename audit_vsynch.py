#!/usr/bin/env python3
"""Read-only project audit. No Qt dependency, network or project modification."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from varians_synchro.core import load_project
from varians_synchro.validation import audit_project


def main(argv=None):
    ap = argparse.ArgumentParser(description='Vérification de cohérence Varians-Synchro V0.7.4')
    ap.add_argument('project', type=Path, help='Fichier .vsynch à analyser, sans modification')
    ap.add_argument('--base', help='Sigle pivot pour auditer les base_keys de Varians')
    ap.add_argument('--output', type=Path, help='Rapport JSON à écrire dans un fichier distinct')
    ap.add_argument('--check-paths', action='store_true', help='Signaler les fichiers sources locaux absents')
    ap.add_argument('--strict', action='store_true', help='Code de sortie 1 aussi pour les avertissements')
    args = ap.parse_args(argv)
    result = audit_project(load_project(args.project), args.base, check_paths=args.check_paths)
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        if args.output.resolve() == args.project.resolve():
            ap.error('Le rapport ne doit pas remplacer le projet .vsynch')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + '\n', encoding='utf-8')
    print(serialized)
    return 1 if result['errors'] or (args.strict and result['warnings']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
