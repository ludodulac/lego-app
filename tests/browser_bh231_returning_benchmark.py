from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SURVEY = ROOT / 'frontend' / 'benchmarks' / 'real-house-5' / 'accepted-survey-v0.1.json'


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
    raise AssertionError('BH-231 browser proof requires Chromium/Chrome')


def main():
    accepted_survey = json.loads(SURVEY.read_text(encoding='utf-8'))
    stale_pending = {
        'survey': accepted_survey,
        'issues': [],
        'valid_for_scene_fusion': True,
    }

    with serve_repo() as port, sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=browser_binary(), args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 390, 'height': 844}, accept_downloads=True)
        context.add_init_script(
            script=f"""
            (() => {{
              if (location.pathname.endsWith('/photo.html')) {{
                localStorage.setItem('brickhouse.pendingArchitecturalSurvey', {json.dumps(json.dumps(stale_pending))});
                localStorage.setItem('brickhouse.knownFrontWidthM', '12.34');
                localStorage.setItem('brickhouse.lastRejectedArchitecturalScene', '{{\"stale\":true}}');
                localStorage.setItem('brickhouse.lastSceneValidationError', 'stale');
              }}
            }})();
            """
        )
        page = context.new_page()
        runtime_errors = []
        failed_requests = []
        page.on('pageerror', lambda error: runtime_errors.append(f'pageerror: {error}'))
        page.on('requestfailed', lambda request: failed_requests.append(f'{request.method} {request.url}: {request.failure}'))

        url = f'http://127.0.0.1:{port}/frontend/photo.html?benchmark=real-house-5&checkpoint=bh231-ci'
        response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
        assert response and response.ok
        page.wait_for_selector('body.boldungo-shell-enabled', timeout=15000)
        page.wait_for_function("() => document.querySelectorAll('.selected-photo-preview').length === 5", timeout=15000)

        cockpit = page.locator('.boldungo-cockpit')
        assert cockpit.get_attribute('data-shell-state') == 'photos'
        assert page.locator('#shell-state-title').text_content().strip() == '1. Photos'
        assert page.locator('.selected-photo-preview').count() == 5
        assert page.locator('#shell-primary-button').text_content().strip() == 'Créer le PDF'
        for key in (
            'brickhouse.pendingArchitecturalSurvey',
            'brickhouse.knownFrontWidthM',
            'brickhouse.lastRejectedArchitecturalScene',
            'brickhouse.lastSceneValidationError',
        ):
            assert page.evaluate('(key) => localStorage.getItem(key)', key) is None
        assert page.evaluate('1 + 1') == 2

        page.locator('[data-shell-state="survey"]').click(timeout=5000)
        assert cockpit.get_attribute('data-shell-state') == 'survey'
        page.locator('[data-shell-state="photos"]').click(timeout=5000)
        assert cockpit.get_attribute('data-shell-state') == 'photos'

        with page.expect_download(timeout=30000) as download_info:
            page.locator('#shell-primary-button').click(timeout=5000)
        download = download_info.value
        assert download.suggested_filename == 'BRICKHOUSE-SURVEY-pdf-handoff-0.10.pdf'
        assert download.failure() is None
        page.wait_for_function(
            "() => document.querySelector('#ai-package-status')?.textContent?.includes('brickhouse-survey-result.json')",
            timeout=15000,
        )
        assert not runtime_errors, runtime_errors
        assert not failed_requests, failed_requests
        context.close()
        browser.close()

    print('BH-231 local returning-browser benchmark proof passed')


if __name__ == '__main__':
    main()
