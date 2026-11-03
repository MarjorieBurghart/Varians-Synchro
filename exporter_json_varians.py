"""Standalone Varians JSON exporter: Python 3.10+, no PySide6 required.

Usage:
    python exporter_json_varians.py myproject.vsynch --base Mu --output export_empty_folder
"""
import argparse
from varians_synchro.core import load_project
from varians_synchro.varians_export import export_varians_alignments


def main():
    parser = argparse.ArgumentParser(description='Export physical-line alignments as Varians-compatible JSON')
    parser.add_argument('project', help='Varians-Synchro .vsynch project')
    parser.add_argument('--base', required=True, help='Technical reference witness siglum')
    parser.add_argument('--output', required=True, help='New or empty output directory')
    args = parser.parse_args()
    reports = export_varians_alignments(load_project(args.project), args.base, args.output)
    print('Export completed in:', args.output)
    print('Physical-reference keys only; TEI <lb/> mapping is not yet established.')
    for wid, report in reports['audit']['witnesses'].items():
        print(f'{wid}: base_keys in validated={report["validated_linked_lines"]}, '
              f'working={report["working_linked_lines"]}; reason={report["reason"] or "ok"}')
    if reports['audit']['warnings']:
        print('WARNING: some secondary JSON files have zero or only unvalidated base_keys.')
        print('Use working/<witness>.json for unvalidated proposals; '
              'do not import the base witness JSON as a secondary witness.')


if __name__ == '__main__':
    main()
