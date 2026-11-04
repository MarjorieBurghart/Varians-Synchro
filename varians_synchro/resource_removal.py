"""Retirer un témoin ou une ressource enregistrée (sans Qt).

Le retrait se calcule sur une copie du projet, puis remplace le projet d'un
bloc (tout ou rien) ; ``removal_impact`` en donne les conséquences avant que
l'utilisateur confirme. Règles :

- un fichier ALTO/PAGE retiré libère les pages qui lui étaient associées ;
  une source d'images retirée emporte ses pages ;
- les groupes qui touchent des lignes disparues sont gardés : ils deviennent
  périmés (``physical_alignment.link_is_stale``), exclus des calculs et de
  l'export, et l'utilisateur les dissocie ensuite ;
- retirer un témoin retire ses synchronisations et ses éditions TEI ; le
  témoin pivot ne peut pas être retiré tant qu'un autre n'est pas choisi ;
- aucun fichier n'est supprimé du disque.
"""
from __future__ import annotations

import copy

from .imaging import create_pages
from .physical_alignment import physical_lines

KINDS = ('images', 'xml', 'tei', 'hd')


def _witness(project, witness_id):
    witness = next((w for w in project.get('witnesses', []) if w['id'] == witness_id), None)
    if witness is None:
        raise ValueError('Témoin introuvable dans le projet.')
    return witness


def _line_ids(project):
    return {line['id'] for witness in project.get('witnesses', []) for line in physical_lines(witness)}


def _drop_resource(staged, witness_id, kind, source_id):
    witness = _witness(staged, witness_id)
    if kind == 'images':
        sources = witness.get('image_sources', [])
        if not any(s['id'] == source_id for s in sources):
            raise ValueError('Ressource introuvable dans ce témoin.')
        witness['image_sources'] = [s for s in sources if s['id'] != source_id]
        create_pages(witness)
        canvases = {page['id'] for page in witness['pages']}
        # Un lot HD dont aucun Canvas n'existe plus ne désigne plus rien.
        witness['hd_downloads'] = [batch for batch in witness.get('hd_downloads', [])
                                   if any(p.get('canvas_id') in canvases for p in batch.get('pages', []))]
        if not witness['hd_downloads']:
            witness.pop('hd_downloads')
    elif kind == 'xml':
        sources = witness.get('alto_sources', [])
        if not any(s['id'] == source_id for s in sources):
            raise ValueError('Ressource introuvable dans ce témoin.')
        witness['alto_sources'] = [s for s in sources if s['id'] != source_id]
        for page in witness.get('pages', []):
            if (page.get('alto_binding') or {}).get('source_id') == source_id:
                page['alto_binding'] = None
                page.pop('reading_region_order', None)
                page.pop('reading_line_order', None)
    elif kind == 'tei':
        resources = staged.get('text_resources', [])
        if not any(r['id'] == source_id and r.get('witness_id') == witness_id for r in resources):
            raise ValueError('Ressource introuvable dans ce témoin.')
        staged['text_resources'] = [r for r in resources if r['id'] != source_id]
        staged['alignment_sessions'] = [s for s in staged.get('alignment_sessions', [])
                                        if s.get('base_resource_id') != source_id]
    elif kind == 'hd':
        batches = witness.get('hd_downloads', [])
        if not any(b.get('directory') == source_id for b in batches):
            raise ValueError('Ressource introuvable dans ce témoin.')
        witness['hd_downloads'] = [b for b in batches if b.get('directory') != source_id]
    else:
        raise ValueError('Ressource introuvable dans ce témoin.')


def _drop_witness(staged, witness_id):
    _witness(staged, witness_id)
    if staged.get('pivot_witness_id') == witness_id:
        raise ValueError('Le témoin pivot ne peut pas être retiré : choisissez d’abord un autre témoin comme pivot.')
    staged['witnesses'] = [w for w in staged['witnesses'] if w['id'] != witness_id]
    staged['pair_sessions'] = [s for s in staged.get('pair_sessions', [])
                               if witness_id not in (s.get('reference_witness_id'), s.get('target_witness_id'))]
    removed_tei = {r['id'] for r in staged.get('text_resources', []) if r.get('witness_id') == witness_id}
    staged['text_resources'] = [r for r in staged.get('text_resources', []) if r['id'] not in removed_tei]
    staged['alignment_sessions'] = [
        s for s in staged.get('alignment_sessions', [])
        if s.get('base_resource_id') not in removed_tei
        and witness_id not in (s.get('target_witness_id'), s.get('base_witness_id'))]


def _staged(project, witness_id, kind, source_id):
    staged = copy.deepcopy(project)
    if kind is None:
        _drop_witness(staged, witness_id)
    else:
        _drop_resource(staged, witness_id, kind, source_id)
    return staged


def removal_impact(project, witness_id, kind=None, source_id=None):
    """Ce que le retrait changerait, sans rien changer : pages retirées ou
    libérées, lignes perdues, groupes touchés (dont validés) et, pour un
    témoin, synchronisations supprimées. Refuse comme le retrait lui-même."""
    staged = _staged(project, witness_id, kind, source_id)
    before = _witness(project, witness_id)
    lost = _line_ids(project) - _line_ids(staged)
    if kind is None:
        sessions = [s for s in project.get('pair_sessions', [])
                    if witness_id in (s.get('reference_witness_id'), s.get('target_witness_id'))]
        links = [link for s in sessions for link in s.get('links', [])]
        pages = len(before.get('pages', []))
    else:
        sessions = []
        links = [link for s in project.get('pair_sessions', []) for link in s.get('links', [])
                 if lost & set(link.get('reference_ids', []) + link.get('target_ids', []))]
        after = _witness(staged, witness_id)
        if kind == 'xml':
            pages = sum(bool(p.get('alto_binding')) for p in before.get('pages', [])) \
                - sum(bool(p.get('alto_binding')) for p in after.get('pages', []))
        else:
            pages = len(before.get('pages', [])) - len(after.get('pages', []))
    return {'pages': pages, 'lines': len(lost), 'groups': len(links),
            'validated': sum(link.get('state') == 'validated' for link in links), 'sessions': len(sessions)}


def _replace(project, staged):
    # Sur place : les vues ouvertes partagent l'objet projet.
    project.clear()
    project.update(staged)


def remove_resource(project, witness_id, kind, source_id):
    """Retire la ressource *source_id* (``kind`` : images, xml, tei, hd) du
    témoin ; ``source_id`` est le dossier d'un lot HD."""
    _replace(project, _staged(project, witness_id, kind, source_id))


def remove_witness(project, witness_id):
    """Retire le témoin, ses synchronisations et ses éditions TEI."""
    _replace(project, _staged(project, witness_id, None, None))
