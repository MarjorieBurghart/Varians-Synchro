#!/usr/bin/env python3
"""Lecture seule : projet, TEI, lignes physiques et JSON Varians.

Usage: python recette_v085.py projet.vsynch --base Mu [--output rapport.json]
No PySide6 or network. No source document, image or .vsynch is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from varians_synchro.core import load_project
from varians_synchro.validation import audit_project
from varians_synchro.varians_export import make_varians_alignments, verify_export_payloads


def release_report(path: Path, base: str | None = None, *, check_paths: bool = False) -> dict:
    """Create a machine-readable report without changing the source file."""
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    project = load_project(path)
    # Preserve the original when legacy defaults are filled in memory.
    audit = audit_project(project, base, check_paths=check_paths)
    result = {
        'tool': 'varians-synchro-release-audit', 'version': '0.8.5',
        'source_file': str(path), 'source_sha256_before': before,
        'project_name': project.get('name'),
        'witnesses': [w['id'] for w in project.get('witnesses', [])],
        'pivot_witness_id': project.get('pivot_witness_id'),
        'physical_pair_sessions': len(project.get('pair_sessions', [])),
        'tei_resources': sum(r.get('kind') == 'tei' for r in project.get('text_resources', [])),
        'audit': audit,
    }
    if base and audit.get('ok'):
        summaries = {}
        for mode in ('validated', 'working'):
            payload, diagnostics = make_varians_alignments(
                project, base, include_uncertain=(mode == 'working'))
            verify_export_payloads(payload, base)
            summaries[mode] = {
                wid: {
                    'pages': len(doc.get('pages', [])),
                    'lines': sum(len(page.get('lines', [])) for page in doc.get('pages', [])),
                    'mapped_secondary_lines': sum(
                        bool(line.get('base_keys')) for page in doc.get('pages', [])
                        for line in page.get('lines', [])) if wid != base else 0,
                    'payload_sha256': hashlib.sha256(json.dumps(doc, sort_keys=True,
                        ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest(),
                } for wid, doc in payload.items()
            }
        result['varians_export'] = summaries
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    result['source_sha256_after'] = after
    if before != after:
        raise RuntimeError('Le document source a changé pendant la recette : vérifier une écriture concurrente.')
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--base', help='Témoin de référence pour vérifier les JSON Varians')
    parser.add_argument('--output', type=Path, help='Rapport JSON (jamais dans le fichier source)')
    parser.add_argument('--check-paths', action='store_true', help='Vérifier les sources locales')
    parser.add_argument('--strict', action='store_true', help='Traiter les avertissements comme un échec')
    args = parser.parse_args(argv)
    source = args.project.resolve()
    if args.output:
        output = args.output.resolve()
        if output == source or output == source.with_name(source.name + '.bak') or output.suffix.lower() == '.vsynch':
            parser.error('Le rapport ne peut pas écraser un .vsynch ou sa copie .bak.')
    try:
        result = release_report(args.project, args.base, check_paths=args.check_paths)
    except Exception as exc:
        print(f'Recette impossible : {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding='utf-8')
    print(serialized)
    audit = result['audit']
    return 1 if (audit['errors'] or (args.strict and audit['warnings'])) else 0


if __name__ == '__main__':
    raise SystemExit(main())
