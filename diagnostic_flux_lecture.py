#!/usr/bin/env python3
"""Read-only J1 report: witness streams, anchor intervals and contradictions.

Examples:
  python diagnostic_flux_lecture.py projet.vsynch --pair Mu F
  python diagnostic_flux_lecture.py projet.vsynch --pair Mu F --json bilan.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from varians_synchro.core import load_project
from varians_synchro.reading_stream import anchor_intervals, reading_stream


def diagnose(project, left: str, right: str) -> dict:
    witnesses = {w['id']:w for w in project.get('witnesses', [])}
    if left not in witnesses or right not in witnesses:
        raise ValueError('Les deux identifiants de témoins doivent exister dans le projet.')
    session = next((s for s in project.get('pair_sessions', [])
                    if {s['reference_witness_id'],s['target_witness_id']} == {left,right}), None)
    if session is None:
        raise ValueError('Aucune session physique entre ces témoins.')
    summary = anchor_intervals(project,session)
    index = {}
    for wid in (session['reference_witness_id'],session['target_witness_id']):
        index[wid] = {line['id']:line for line in reading_stream(witnesses[wid])}
    links = {link['id']:link for link in session.get('links', [])}
    conflicts=[]
    for issue in summary['warnings']:
        references=[]
        for link_id in (issue.get('previous_link_id'),issue['link_id']):
            if not link_id: continue
            link=links.get(link_id)
            if not link: continue
            locations={}
            for wid, ids in ((session['reference_witness_id'],link['reference_ids']),
                             (session['target_witness_id'],link['target_ids'])):
                locations[wid]=[{'folio':index[wid].get(uid,{}).get('page_label'),
                                 'line':index[wid].get(uid,{}).get('ordinal')}
                                for uid in ids]
            references.append({'link_id':link_id,'locations':locations})
        conflicts.append({'reason':issue['reason'],'anchors':references})
    return {
        'pair':[session['reference_witness_id'],session['target_witness_id']],
        'active_lines':{session['reference_witness_id']:summary['reference_count'],
                        session['target_witness_id']:summary['target_count']},
        'validated_anchors':len(summary['anchors']),
        'interval_count':len(summary['intervals']),
        'intervals':[{'reference_count':i['reference_count'],'target_count':i['target_count'],
                      'reference_folios':i['reference_pages'],'target_folios':i['target_pages'],
                      'needs_attention':i['needs_attention']} for i in summary['intervals']],
        'conflicts':conflicts,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',help='Existing .vsynch file (read-only)')
    parser.add_argument('--pair',nargs=2,required=True,metavar=('REFERENCE','TARGET'))
    parser.add_argument('--json',help='Optional path for JSON report')
    args=parser.parse_args()
    result=diagnose(load_project(args.project),*args.pair)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.json:
        Path(args.json).write_text(text+'\n',encoding='utf-8')
    print(text)

if __name__=='__main__':
    main()
