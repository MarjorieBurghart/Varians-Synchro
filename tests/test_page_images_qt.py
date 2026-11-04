"""Images de page : formats bornés, miniatures IIIF bornées (red team B2, B5).

- Une « image » de page qui était en fait un SVG (ou un PDF) était décodée ;
  le SVG pouvait charger des fichiers locaux ou réseau. Seuls JPEG, PNG,
  TIFF, WebP et JPEG 2000 sont désormais décodés comme images de page.
- Les miniatures IIIF ne contrôlaient ni le schéma de l'adresse (un service
  ``file://`` lisait le disque) ni la taille de la réponse (600 Mo en
  mémoire pour une vignette).
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QBuffer, QByteArray, QCoreApplication, QEvent, QIODevice
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from varians_synchro import ui_widgets

SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
       b'<rect width="10" height="10" fill="red"/></svg>')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _png():
    image = QImage(4, 4, QImage.Format.Format_RGB32)
    image.fill(QColor(200, 10, 10))
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, 'PNG')
    return bytes(data)


def test_only_raster_page_images_are_decoded(app):
    assert not ui_widgets.decode_page_image(_png()).isNull()
    assert ui_widgets.decode_page_image(SVG).isNull()
    assert ui_widgets.decode_page_image(b'%PDF-1.4\n%...').isNull()


def test_a_local_svg_page_image_is_not_read(app, tmp_path):
    from PySide6.QtGui import QImageReader
    disguised = tmp_path / 'f001.jpg'
    disguised.write_bytes(SVG)
    assert not ui_widgets.page_image_reader_ok(QImageReader(str(disguised)))
    real = tmp_path / 'f002.png'
    real.write_bytes(_png())
    assert ui_widgets.page_image_reader_ok(QImageReader(str(real)))


def test_thumbnails_are_only_asked_over_http(app, monkeypatch):
    from varians_synchro.core import create_witness, new_project
    from varians_synchro import ui_pages
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    witness['pages'] = [{'id': f'c{n}', 'label': f'{n}r', 'image_kind': 'iiif', 'alto_binding': None,
                         'canvas': {'id': f'c{n}', 'image_service': service, 'iiif_image_version': 2,
                                    'width': 100, 'height': 100}}
                        for n, service in ((1, 'file:///etc'), (2, 'https://example.org/iiif/2'))]
    monkeypatch.setattr(ui_pages, 'create_pages', lambda w: w['pages'])
    dialog = ui_pages.PagesDialog(project, witness)
    asked = []
    monkeypatch.setattr(dialog._network, 'get', lambda request: asked.append(request.url().toString()) or
                        dialog._network.__class__.get(dialog._network, request))
    try:
        dialog._thumb_attempted.clear()
        monkeypatch.setattr(dialog, '_visible_item_ids', lambda: ['c1', 'c2'])
        dialog._load_visible_thumbnails()
        assert asked and all(url.startswith('https://') for url in asked)
    finally:
        for reply in list(dialog._remote_replies.values()):
            reply.abort()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_a_thumbnail_answer_is_bounded(app):
    from varians_synchro.ui_pages import THUMBNAIL_MAX_BYTES
    assert THUMBNAIL_MAX_BYTES <= 4_000_000
