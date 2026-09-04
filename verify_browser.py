import subprocess
import threading
import time
import os
import json
import re
from server import ThreadingHTTPServer, PokerAssistantRequestHandler

PORT = 5991
TEST_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'browser_test.html')
THORIUM_PATH = r'C:\Program Files\Thorium\Application\thorium.exe'

report_event = threading.Event()
report_data = {}

class BrowserTestRequestHandler(PokerAssistantRequestHandler):
    def do_POST(self):
        if self.path == '/api/test_report':
            content_length = int(self.headers.get('Content-Length', 0))
            payload = self.rfile.read(content_length).decode('utf-8')
            global report_data
            report_data = json.loads(payload)
            report_event.set()
            self._send_json({'status': 'ok'})
            return
        super().do_POST()

HTML_CONTENT = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Browser Test Runner</title></head>
<body>
<iframe id="appFrame" src="/" style="width:1200px; height:900px;"></iframe>
<div id="test-status">Running browser tests...</div>
<script>
window.addEventListener('load', async () => {
    const frame = document.getElementById('appFrame');
    while (!frame.contentDocument || frame.contentDocument.readyState !== 'complete' || !frame.contentDocument.getElementById('stratWinRateBtn')) {
        await new Promise(r => setTimeout(r, 100));
    }
    await new Promise(r => setTimeout(r, 500));
    const doc = frame.contentDocument;
    const win = frame.contentWindow;
    const results = { passed: 0, failed: 0, tests: [] };

    function assert(cond, name, details) {
        if (cond) {
            results.passed++;
            results.tests.push({ status: 'PASS', name, details: details || '' });
        } else {
            results.failed++;
            results.tests.push({ status: 'FAIL', name, details: details || '' });
        }
    }

    try {
        // Test 1: Strategy buttons exist and default state
        const winBtn = doc.getElementById('stratWinRateBtn');
        const evBtn = doc.getElementById('stratEvBtn');
        assert(winBtn && evBtn, 'Strategy toggle buttons exist');
        assert(winBtn.classList.contains('active'), 'Default strategy button is Win Rate (active)');
        assert(!evBtn.classList.contains('active'), 'EV button is not active initially');

        // Test 2: Select preset pair_vs_flush
        const presetSelect = doc.getElementById('presetSelect');
        presetSelect.value = 'pair_vs_flush';
        presetSelect.dispatchEvent(new Event('change'));

        // Wait for evaluation to complete
        for (let i = 0; i < 60; i++) {
            const badge = doc.getElementById('recBadge');
            if (badge && badge.textContent.includes('MAX WIN RATE')) break;
            await new Promise(r => setTimeout(r, 250));
        }

        const recBadge = doc.getElementById('recBadge');
        const recAction = doc.getElementById('recActionText');
        const recEv = doc.getElementById('recEvVal');
        const recWin = doc.getElementById('recWinRateVal');

        assert(recBadge.textContent.includes('MAX WIN RATE'), 'recBadge shows MAX WIN RATE strategy', recBadge.textContent);
        assert(recAction.textContent.includes('2♥, 2♦') || recAction.textContent.includes('2'), 'Hold recommends made Pair in Win Rate mode', recAction.textContent);
        assert(recWin.textContent.includes('33.2%'), 'Win Rate displays 33.2%', recWin.textContent);
        assert(recEv.textContent.includes('1.70x'), 'EV displays 1.70x in Win Rate mode', recEv.textContent);

        const winBox = recWin.closest('.stat-box');
        assert(winBox.classList.contains('highlight-win'), 'Win Rate stat box has highlight-win');

        // Test 3: Click EV button
        evBtn.click();
        for (let i = 0; i < 60; i++) {
            const badge = doc.getElementById('recBadge');
            if (badge && badge.textContent.includes('MAX REWARD')) break;
            await new Promise(r => setTimeout(r, 250));
        }

        assert(evBtn.classList.contains('active'), 'EV button is active after click');
        assert(!winBtn.classList.contains('active'), 'Win Rate button is inactive after EV click');
        assert(recBadge.textContent.includes('MAX REWARD'), 'recBadge shows MAX REWARD (EV)', recBadge.textContent);
        assert(recAction.textContent.includes('5♥') || recAction.textContent.includes('8♥') || recAction.textContent.includes('K♥'), 'Hold recommends 4 to a Flush in EV mode', recAction.textContent);
        assert(recEv.textContent.includes('2.92x'), 'EV displays 2.92x', recEv.textContent);
        assert(recWin.textContent.includes('20.8%'), 'Win Rate displays 20.8% in EV mode', recWin.textContent);

        const evBox = recEv.closest('.stat-box');
        assert(evBox.classList.contains('highlight-ev'), 'EV stat box has highlight-ev');

        // Test 4: Switch back to Win Rate
        winBtn.click();
        for (let i = 0; i < 60; i++) {
            const badge = doc.getElementById('recBadge');
            const evVal = doc.getElementById('recEvVal');
            if (badge && badge.textContent.includes('MAX WIN RATE') && evVal && evVal.textContent.includes('1.70')) break;
            await new Promise(r => setTimeout(r, 250));
        }

        assert(winBtn.classList.contains('active'), 'Win Rate button active again');
        assert(recBadge.textContent.includes('MAX WIN RATE'), 'recBadge switched back to MAX WIN RATE', recBadge.textContent);
        assert(recAction.textContent.includes('2♥, 2♦') || recAction.textContent.includes('2'), 'Hold switched back to Pair', recAction.textContent);

        // Test 5: Client-side standalone PokerSolver
        assert(typeof win.PokerSolver !== 'undefined', 'PokerSolver exists on window');
        const cardIds = [win.PokerSolver.cardFromStr('2H'), win.PokerSolver.cardFromStr('2D'), win.PokerSolver.cardFromStr('5H'), win.PokerSolver.cardFromStr('8H'), win.PokerSolver.cardFromStr('KH')];
        const jsWin = win.PokerSolver.analyzeAllHolds(cardIds, 'win_rate');
        const jsEv = win.PokerSolver.analyzeAllHolds(cardIds, 'ev');
        assert(jsWin.best_hold.held_cards.length === 2, 'PokerSolver JS win_rate picks Pair (2 cards)');
        assert(jsEv.best_hold.held_cards.length === 4, 'PokerSolver JS ev picks Flush draw (4 cards)');
        assert(Math.abs(jsWin.best_hold.win_rate - 0.3317) < 0.005, 'PokerSolver JS win_rate math matches Python');
        assert(Math.abs(jsEv.best_hold.ev - 2.9167) < 0.01, 'PokerSolver JS EV math matches Python');

    } catch (err) {
        results.failed++;
        results.tests.push({ status: 'ERROR', name: 'Exception during test', details: err.toString() });
    }

    document.getElementById('test-status').textContent = 'Finished. Reporting...';
    await fetch('/api/test_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(results)
    });
});
</script>
</body>
</html>"""

def main():
    with open(TEST_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(HTML_CONTENT)

    server = ThreadingHTTPServer(('127.0.0.1', PORT), BrowserTestRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    proc = None
    try:
        cmd = [
            THORIUM_PATH,
            '--headless=new',
            '--disable-gpu',
            f'http://127.0.0.1:{PORT}/browser_test.html'
        ]
        proc = subprocess.Popen(cmd)
        finished = report_event.wait(timeout=60)
        if not finished:
            print("Timed out waiting for browser test report.")
            return 1

        print(f"Browser DOM & Interaction Tests: Passed: {report_data['passed']}, Failed: {report_data['failed']}")
        for t in report_data['tests']:
            status_symbol = "PASS" if t['status'] == 'PASS' else "FAIL"
            clean_details = str(t['details']).encode('ascii', errors='backslashreplace').decode('ascii')
            clean_name = str(t['name']).encode('ascii', errors='backslashreplace').decode('ascii')
            print(f"  [{status_symbol}] {clean_name}: {clean_details}")

        if report_data['failed'] > 0:
            return 1
        return 0

    finally:
        if proc:
            proc.terminate()
        server.shutdown()
        server.server_close()
        if os.path.exists(TEST_HTML_PATH):
            os.remove(TEST_HTML_PATH)

if __name__ == '__main__':
    exit(main())
