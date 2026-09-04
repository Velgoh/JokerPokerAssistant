"""
Lightweight HTTP Server for Joker Poker & High-Low Assistant
Zero third-party dependencies (uses Python standard library http.server).
"""

import os
import sys
import json
import webbrowser
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any

import solver
import logger

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class PokerAssistantRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        # Keep terminal output concise
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message: str, status: int = 400):
        self._send_json({'error': message, 'status': 'error'}, status=status)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        url_path = self.path.split('?')[0]
        
        if url_path == '/api/health':
            self._send_json({'status': 'ok', 'version': '1.0.0'})
            return
            
        elif url_path == '/api/logs':
            recent = logger.get_recent_logs(limit=50)
            self._send_json({'status': 'ok', 'logs': recent})
            return
            
        elif url_path == '/api/logs/raw':
            raw_text = logger.get_raw_txt_logs(max_lines=300)
            self._send_json({'status': 'ok', 'raw_text': raw_text})
            return
            
        # Default static file serving (index.html, styles.css, app.js, etc.)
        super().do_GET()

    def do_POST(self):
        url_path = self.path.split('?')[0]
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            req_data = json.loads(post_body.decode('utf-8')) if post_body else {}
        except json.JSONDecodeError:
            self._send_error("Invalid JSON payload.")
            return

        if url_path == '/api/evaluate':
            cards_input = req_data.get('cards', [])
            strategy = req_data.get('strategy', 'win_rate')
            if not isinstance(cards_input, list) or len(cards_input) != 5:
                self._send_error("Must provide exactly 5 card strings in 'cards'.")
                return
            try:
                card_ids = [solver.card_from_str(c) if isinstance(c, str) else int(c) for c in cards_input]
                analysis = solver.analyze_all_holds(card_ids, strategy=strategy)
                self._send_json({'status': 'ok', 'result': analysis})
            except Exception as e:
                self._send_error(str(e), status=400)
            return

        elif url_path == '/api/highlow':
            open_card = req_data.get('open_card', '')
            if not open_card:
                self._send_error("Must provide 'open_card' string.")
                return
            try:
                hl_result = solver.evaluate_high_low(open_card)
                self._send_json({'status': 'ok', 'result': hl_result})
            except Exception as e:
                self._send_error(str(e), status=400)
            return

        elif url_path == '/api/log':
            try:
                # Generate explanation if not provided
                if not req_data.get('diagnostic'):
                    init_cards = req_data.get('initial_hand', [])
                    rec_hold = req_data.get('recommended_hold', [])
                    rec_ev = req_data.get('recommended_ev', 0.0)
                    user_held = req_data.get('user_held', [])
                    drawn_cards = req_data.get('drawn_cards', [])
                    final_hand = req_data.get('final_hand', [])
                    final_name = req_data.get('final_hand_name', 'High Card')
                    payout = req_data.get('payout_multiplier', 0)
                    strategy = req_data.get('strategy', 'win_rate')
                    rec_win = req_data.get('recommended_win_rate')
                    
                    # Convert to indices
                    rec_indices = [i for i, c in enumerate(init_cards) if c in rec_hold]
                    user_indices = [i for i, c in enumerate(init_cards) if c in user_held]
                    
                    diag = solver.generate_round_explanation(
                        initial_cards_str=init_cards,
                        recommended_hold_indices=rec_indices,
                        recommended_ev=rec_ev,
                        user_held_indices=user_indices,
                        drawn_cards_str=drawn_cards,
                        final_cards_str=final_hand,
                        final_hand_name=final_name,
                        payout_multiplier=payout,
                        high_low_steps=req_data.get('high_low_steps', []),
                        final_coins=req_data.get('earned_coins'),
                        strategy=strategy,
                        recommended_win_rate=rec_win
                    )
                    req_data['diagnostic'] = diag
                    
                record = logger.log_round(req_data)
                self._send_json({'status': 'ok', 'record': record})
            except Exception as e:
                self._send_error(str(e), status=400)
            return

        elif url_path == '/api/logs/clear':
            success = logger.clear_logs()
            self._send_json({'status': 'ok' if success else 'error'})
            return

        else:
            self._send_error(f"Unknown POST endpoint: {url_path}", status=404)


def find_available_port(start_port: int = 5000, max_attempts: int = 50) -> int:
    """Find an open TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port


def main():
    port = 5000
    open_browser = True
    
    for arg in sys.argv[1:]:
        if arg.startswith('--port='):
            port = int(arg.split('=')[1])
        elif arg == '--no-browser':
            open_browser = False

    port = find_available_port(port)
    server_address = ('127.0.0.1', port)
    httpd = ThreadingHTTPServer(server_address, PokerAssistantRequestHandler)
    
    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print("  ✨ Joker Poker & High-Low Assistant ✨")
    print(f"  Server running at: {url}")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)
    
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
        httpd.server_close()
        print("Server stopped.")


if __name__ == '__main__':
    main()
