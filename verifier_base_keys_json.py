"""Read-only inspection of a Varians alignment JSON file (Python 3.10+)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def inspect(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    meta = data.get('meta') or {}
    lines = [line for page in data.get('pages', []) for line in page.get('lines', [])]
    linked = [line for line in lines if line.get('base_keys')]
    print('File:', path)
    print('Witness:', meta.get('witness'), 'Reference:', meta.get('base_witness'), 'Role:', meta.get('role'))
    print('Pages:', len(data.get('pages', [])), 'Physical lines:', len(lines))
    print('Lines with base_keys:', len(linked))
    if meta.get('role') == 'base':
        print('NOTE: The pivot/reference witness normally has no base_keys.')
    elif not linked:
        print('WARNING: No base_keys in a secondary witness. Check validated/ vs working/,')
        print('the chosen reference, saved links and rapport_export.json.')
    else:
        print('The JSON contains base_keys; inspect how it is imported in Varians if needed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('json', nargs='+', help='One or more Varians alignment JSON files')
    args = parser.parse_args()
    for name in args.json:
        inspect(name)
