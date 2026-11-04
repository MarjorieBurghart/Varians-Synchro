"""Manifest IIIF indisponible : on peut réessayer.

Un Manifest qui ne répond pas à l'ajout est gardé, marqué indisponible.
Le donner de nouveau (ou « Réessayer » dans la fiche du témoin) l'interroge
une nouvelle fois : s'il répond, ses pages apparaissent ; sinon il reste
indisponible, avec la nouvelle erreur. Rien d'autre ne change.
"""
from __future__ import annotations

import pytest

from varians_synchro.core import new_project
from varians_synchro.resource_workflow import apply_witness_draft, unavailable_manifests

URL = 'https://example.org/iiif/manifest.json'
MANIFEST = {'canvases': [{'id': 'https://example.org/canvas/1', 'label': 'f. 1r'},
                         {'id': 'https://example.org/canvas/2', 'label': 'f. 1v'}]}


def offline(url):
    raise OSError('hors ligne')


def online(url):
    return MANIFEST


@pytest.fixture
def project():
    project = new_project('Essai')
    apply_witness_draft(project, identifier='F', manifests=[URL], manifest_loader=offline)
    return project


def _witness(project):
    return next(w for w in project['witnesses'] if w['id'] == 'F')


def test_an_unanswered_manifest_is_kept_as_unavailable(project):
    witness = _witness(project)
    assert unavailable_manifests(witness) == [URL]
    assert witness['pages'] == []
    assert witness['image_sources'][0]['error'] == 'hors ligne'


def test_giving_it_again_retries_it_and_creates_its_pages(project):
    source_id = _witness(project)['image_sources'][0]['id']
    apply_witness_draft(project, identifier='F', manifests=[URL], manifest_loader=online)
    witness = _witness(project)
    source = witness['image_sources'][0]
    assert len(witness['image_sources']) == 1 and source['id'] == source_id
    assert source['status'] == 'inspected' and 'error' not in source
    assert [page['label'] for page in witness['pages']] == ['f. 1r', 'f. 1v']
    assert unavailable_manifests(witness) == []


def test_the_same_address_written_differently_is_the_same_manifest(project):
    apply_witness_draft(project, identifier='F', manifests=['HTTPS://EXAMPLE.ORG/iiif/manifest.json#x'],
                        manifest_loader=online)
    assert len(_witness(project)['image_sources']) == 1
    assert unavailable_manifests(_witness(project)) == []


def test_a_manifest_still_unanswered_stays_unavailable_with_the_new_error(project):
    def refused(url):
        raise OSError('503')
    apply_witness_draft(project, identifier='F', manifests=[URL], manifest_loader=refused)
    witness = _witness(project)
    assert unavailable_manifests(witness) == [URL]
    assert witness['image_sources'][0]['error'] == '503'
    assert witness['pages'] == []


def test_an_available_manifest_is_not_queried_again(project):
    apply_witness_draft(project, identifier='F', manifests=[URL], manifest_loader=online)
    calls = []
    apply_witness_draft(project, identifier='F', manifests=[URL],
                        manifest_loader=lambda url: calls.append(url) or MANIFEST)
    assert calls == []
