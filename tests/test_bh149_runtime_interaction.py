from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def serve_repo():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), lambda *args, **kwargs: QuietHandler(*args, directory=ROOT, **kwargs))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def browser_binary():
    for candidate in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'):
        path = shutil.which(candidate)
        if path:
            return path
    raise AssertionError('BH-149 behavioral regression requires a Chromium/Chrome binary')


def test_site_nav_does_not_starve_event_loop_and_ordinary_control_clicks():
    with serve_repo() as port:
        url = f'http://127.0.0.1:{port}/tests/browser_fixtures/photo.html'
        completed = subprocess.run(
            [
                browser_binary(),
                '--headless',
                '--no-sandbox',
                '--disable-gpu',
                '--virtual-time-budget=1000',
                '--dump-dom',
                url,
            ],
            capture_output=True,
            text=True,
            timeout=12,
            check=True,
        )

    dom = completed.stdout
    assert 'data-bh149-interaction="clicked"' in dom
    assert '<output id="interaction-result">clicked</output>' in dom
    assert 'Créer le PDF Photos → Relevé' in dom
    assert 'id="boldungo-site-nav"' in dom
