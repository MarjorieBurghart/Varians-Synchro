"""Ce que Varians-Synchro note dans son journal des erreurs, en plus des
exceptions non rattrapées : les erreurs montrées à l'utilisateur, avec leur
pile d'appels quand elles ont été levées ; un Manifest IIIF qui n'a pas
répondu à l'ajout d'un témoin (gardé dans le projet, marqué indisponible,
sans autre trace de l'erreur)."""
from __future__ import annotations

import logging

import pytest

from varians_synchro.core import new_project
from varians_synchro.errors import Localized, localized, localized_text
from varians_synchro.i18n import tr
from varians_synchro.resource_workflow import apply_witness_draft


@pytest.fixture
def journal(caplog):
    """Les écritures du journal (logger « varians_synchro » et ses enfants)."""
    caplog.set_level(logging.INFO, logger='varians_synchro')

    def records(part):
        return [record for record in caplog.records if record.name == f'varians_synchro.{part}']
    return records


def test_an_error_shown_to_the_user_is_written_with_its_trace(journal):
    try:
        raise OSError('disque plein')
    except OSError as exc:
        assert localized_text(exc) == 'disque plein'
    [record] = journal('interface')
    assert record.levelno == logging.WARNING and 'OSError' in record.getMessage()
    assert 'disque plein' in record.getMessage()
    assert record.exc_info and record.exc_info[0] is OSError


def test_an_error_built_without_raising_is_written_without_trace(journal):
    assert localized_text(ValueError('valeur')) == 'valeur'
    [record] = journal('interface')
    assert 'valeur' in record.getMessage() and not record.exc_info


def test_an_error_quoting_another_is_written_once(journal):
    inner = OSError('réseau coupé')
    outer = localized(ValueError, 'error.unexpected.text', error=inner)
    text = localized_text(outer)
    assert text == tr('error.unexpected.text', error='réseau coupé')
    assert len(journal('interface')) == 1


def test_a_message_that_is_not_an_error_is_not_written(journal):
    localized_text('Projet enregistré.')
    localized_text(Localized('error.unexpected.title'))
    assert journal('interface') == []


def test_a_manifest_that_does_not_answer_is_written(journal):
    url = 'https://example.org/iiif/manifest.json'

    def offline(address):
        raise OSError('hors ligne')

    apply_witness_draft(new_project('Essai'), identifier='F', manifests=[url], manifest_loader=offline)
    [record] = journal('iiif')
    assert record.levelno == logging.WARNING
    assert url in record.getMessage() and 'hors ligne' in record.getMessage() and "'F'" in record.getMessage()
    assert record.exc_info and record.exc_info[0] is OSError
