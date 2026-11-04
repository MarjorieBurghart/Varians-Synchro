"""Accès réseau bornés (red team B4, B8).

- Une redirection du serveur IIIF vers un autre schéma que http/https
  (``ftp://``…) était suivie : le contrôle http/https ne portait que sur
  l'adresse de départ.
- Un serveur qui répond goutte à goutte figeait l'attente indéfiniment : le
  délai ne portait que sur chaque lecture, pas sur le total.

Serveur HTTP local (127.0.0.1), arrêté à la fin de chaque test.
"""
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from varians_synchro import imaging
from varians_synchro.errors import localized_text
from varians_synchro.i18n import tr


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/redirect-ftp':
            self.send_response(302)
            self.send_header('Location', 'ftp://127.0.0.1:1/x')
            self.end_headers()
        elif self.path == '/redirect-http':
            self.send_response(302)
            self.send_header('Location', '/ok')
            self.end_headers()
        elif self.path == '/ok':
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')
        elif self.path == '/slow':
            self.send_response(200)
            self.send_header('Content-Length', '1000')
            self.end_headers()
            try:
                for _ in range(1000):
                    self.wfile.write(b'x')
                    self.wfile.flush()
                    time.sleep(0.1)
            except (BrokenPipeError, ConnectionResetError):
                pass


@pytest.fixture
def server():
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
    httpd.daemon_threads = True
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{httpd.server_address[1]}'
    httpd.shutdown()
    httpd.server_close()


def test_a_redirection_to_another_scheme_is_refused(server):
    with pytest.raises(ValueError) as refused:
        imaging._http_bytes(server + '/redirect-ftp')
    assert localized_text(refused.value) == tr('error.imaging.redirect_refused')


def test_a_redirection_within_http_is_followed(server):
    assert imaging._http_bytes(server + '/redirect-http') == b'ok'


def test_a_server_answering_drop_by_drop_is_given_up(server):
    started = time.monotonic()
    with pytest.raises(TimeoutError) as slow:
        imaging._http_bytes(server + '/slow', deadline=1)
    assert time.monotonic() - started < 5
    assert localized_text(slow.value) == tr('error.imaging.too_slow', seconds=1)
