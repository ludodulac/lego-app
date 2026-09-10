from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright

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
    # BH-149 is a responsiveness contract, not a serialization contract.
    # Chromium --dump-dom can stay alive after the page has rendered and accepted
    # input, which made the old harness report starvation without proving one.
    # Drive the same fixture through the real browser event loop instead: the
    # scheduled click must land, then a second user-style click must still work.
    with serve_repo() as port, sync_playwright() as p:
        url = f'http://127.0.0.1:{port}/tests/browser_fixtures/photo.html'
        browser = p.chromium.launch(
            headless=True,
            executable_path=browser_binary(),
            args=['--no-sandbox', '--disable-gpu'],
        )
        page = browser.new_page()
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=10000)
            assert response and response.ok
            page.wait_for_function(
                "document.documentElement.dataset.bh149Interaction === 'clicked'",
                timeout=5000,
            )
            assert page.locator('#interaction-result').text_content() == 'clicked'
            assert page.locator('#download-ai-package').text_content() == 'Créer le PDF Photos → Relevé'
            assert page.locator('#boldungo-site-nav').count() == 1

            page.locator('#ordinary-control').click(timeout=5000)
            assert page.evaluate("document.documentElement.dataset.bh149Interaction") == 'clicked'
        finally:
            browser.close()
