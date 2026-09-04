import subprocess
import threading
import time
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = 5992
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
THORIUM_PATH = r'C:\Program Files\Thorium\Application\thorium.exe'

report_event = threading.Event()
report_data = {}

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class TestRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        if self.path == '/api/test_report':
            content_length = int(self.headers.get('Content-Length', 0))
            payload = self.rfile.read(content_length).decode('utf-8')
            global report_data
            report_data = json.loads(payload)
            report_event.set()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        super().do_POST()

    def do_GET(self):
        # Simulate GitHub Pages subpath: /JokerPokerAssistant/ -> serves static files
        if self.path.startswith('/JokerPokerAssistant/'):
            subpath = self.path[len('/JokerPokerAssistant/'):]
            if not subpath or subpath == '/':
                subpath = 'index.html'
            self.path = '/' + subpath
        super().do_GET()

HTML_TEST_RUNNER = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Comprehensive Browser & Pages Test</title></head>
<body>
<iframe id="appFrame" src="/JokerPokerAssistant/index.html" style="width:1280px; height:960px;"></iframe>
<div id="status">Running comprehensive suite...</div>
<script>
window.addEventListener('load', async () => {
    const frame = document.getElementById('appFrame');
    while (!frame.contentDocument || frame.contentDocument.readyState !== 'complete' || !frame.contentWindow.PokerSolver) {
        await new Promise(r => setTimeout(r, 100));
    }
    await new Promise(r => setTimeout(r, 400));

    const doc = frame.contentDocument;
    const win = frame.contentWindow;
    const results = { passed: 0, failed: 0, tests: [], consoleErrors: [] };

    // Capture console errors from iframe
    const origError = win.console.error;
    win.console.error = function(...args) {
        results.consoleErrors.push(args.join(' '));
        origError.apply(win.console, args);
    };

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
        // Test 1: Subpath loading & relative assets check
        assert(doc.title.includes('Joker Poker'), 'Page title loaded correctly via /JokerPokerAssistant/ subpath');
        const styleSheet = Array.from(doc.styleSheets).find(s => s.href && s.href.includes('styles.css'));
        assert(!!styleSheet, 'styles.css loaded correctly via relative path under subpath');

        const favicons = doc.querySelectorAll('link[rel*="icon"]');
        assert(favicons.length >= 2, 'Favicon links (SVG and ICO) present in document head');

        // Test 2: Tab Switching
        const tabs = ['phase1', 'phase2', 'logs', 'rules'];
        for (const t of tabs) {
            const btn = doc.querySelector(`.tab-btn[data-tab="${t}"]`);
            assert(!!btn, `Tab button for ${t} exists`);
            btn.click();
            await new Promise(r => setTimeout(r, 50));
            const pane = doc.getElementById(t);
            assert(pane && pane.classList.contains('active'), `Tab pane ${t} activated upon click`);
        }

        // Switch back to phase1
        doc.querySelector('.tab-btn[data-tab="phase1"]').click();
        await new Promise(r => setTimeout(r, 50));

        // Test 3: Random Hand and Card Selection
        const randomBtn = doc.getElementById('randomHandBtn');
        assert(!!randomBtn, 'Random hand button exists');
        randomBtn.click();
        await new Promise(r => setTimeout(r, 600));

        const filledSlots = doc.querySelectorAll('.card-slot.filled');
        assert(filledSlots.length === 5, 'Random hand deals exactly 5 filled cards');

        // Test 4: Clear Hand
        const clearBtn = doc.getElementById('clearHandBtn');
        clearBtn.click();
        await new Promise(r => setTimeout(r, 200));
        const remainingSlots = doc.querySelectorAll('.card-slot.filled');
        assert(remainingSlots.length === 0, 'Clear hand resets slots to empty');

        // Test 5: High-Low Interactive Solver (Tab phase2)
        doc.querySelector('.tab-btn[data-tab="phase2"]').click();
        await new Promise(r => setTimeout(r, 100));

        // Click Rank 2 (Ace/2 should be 100% win rate)
        const rank2Btn = doc.querySelector('.hl-rank-btn[data-rank="2"]');
        assert(!!rank2Btn, 'Rank 2 button exists in High-Low grid');
        rank2Btn.click();
        await new Promise(r => setTimeout(r, 200));

        const hlDir = doc.getElementById('hlDirection');
        const hlProb = doc.getElementById('hlProbBadge');
        assert(hlDir.textContent.includes('PICK HIGHER'), 'Rank 2 recommends PICK HIGHER', hlDir.textContent);
        assert(hlProb.textContent.includes('100.0%'), 'Rank 2 displays 100.0% Win Rate', hlProb.textContent);

        // Click Rank 8 (Coin flip)
        const rank8Btn = doc.querySelector('.hl-rank-btn[data-rank="8"]');
        rank8Btn.click();
        await new Promise(r => setTimeout(r, 200));
        assert(hlDir.textContent.includes('50/50') || hlDir.textContent.includes('COIN'), 'Rank 8 displays 50/50 advice', hlDir.textContent);

        // Test 6: Standalone Mode offline logs persistence
        const testRound = {
            round_id: 'TEST-OFFLINE-001',
            timestamp_display: 'Today 12:00',
            strategy: 'win_rate',
            outcome: 'WIN',
            earned_coins: 16,
            initial_hand: ['10S', 'JS', 'QS', 'KS', 'AS'],
            final_hand: ['10S', 'JS', 'QS', 'KS', 'AS'],
            final_hand_name: 'Royal Flush',
            payout_multiplier: 200,
            diagnostic: 'Test Royal Flush offline verification.'
        };
        win.localStorage.setItem('poker_assistant_logs', JSON.stringify([testRound]));

        // Switch to Logs Tab
        doc.querySelector('.tab-btn[data-tab="logs"]').click();
        await new Promise(r => setTimeout(r, 200));
        const historyCards = doc.querySelectorAll('.history-card');
        assert(historyCards.length >= 1, 'Local history card rendered from localStorage');
        assert(historyCards[0].textContent.includes('TEST-OFFLINE-001'), 'Offline round record displayed correctly');

        // Test 7: Zero console errors
        assert(results.consoleErrors.length === 0, 'No console errors encountered during test suite', results.consoleErrors.join('; '));

    } catch (e) {
        results.failed++;
        results.tests.push({ status: 'ERROR', name: 'Exception in suite', details: e.toString() });
    }

    await fetch('/api/test_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(results)
    });
});
</script>
</body>
</html>
"""

def main():
    runner_file = os.path.join(STATIC_DIR, 'suite_runner.html')
    with open(runner_file, 'w', encoding='utf-8') as f:
        f.write(HTML_TEST_RUNNER)

    server = ThreadingHTTPServer(('127.0.0.1', PORT), TestRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    proc = None
    try:
        proc = subprocess.Popen([
            THORIUM_PATH,
            '--headless=new',
            '--disable-gpu',
            f'http://127.0.0.1:{PORT}/suite_runner.html'
        ])
        finished = report_event.wait(timeout=30)
        if not finished:
            print("Timeout waiting for test runner report.")
            return 1

        print(f"Comprehensive Suite: Passed: {report_data['passed']}, Failed: {report_data['failed']}")
        for t in report_data['tests']:
            status_symbol = "PASS" if t['status'] == 'PASS' else "FAIL"
            clean_details = str(t.get('details', '')).encode('ascii', errors='backslashreplace').decode('ascii')
            print(f"  [{status_symbol}] {t['name']}: {clean_details}")

        if report_data['consoleErrors']:
            print("Console errors captured:")
            for err in report_data['consoleErrors']:
                print(f"  ERR: {str(err).encode('ascii', errors='backslashreplace').decode('ascii')}")

        return 0 if report_data['failed'] == 0 else 1
    finally:
        if proc:
            proc.terminate()
        server.shutdown()
        server.server_close()
        if os.path.exists(runner_file):
            os.remove(runner_file)

if __name__ == '__main__':
    exit(main())
