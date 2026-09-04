"""
End-to-end integration test for Joker Poker Assistant server and client.
"""

import urllib.request
import json
import threading
import time
import os
import unittest
import tempfile
import shutil
from server import ThreadingHTTPServer, PokerAssistantRequestHandler
import logger

class TestE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.orig_jsonl = logger.JSONL_PATH
        cls.orig_txt = logger.TXT_PATH
        logger.JSONL_PATH = os.path.join(cls.test_dir, 'game_logs.jsonl')
        logger.TXT_PATH = os.path.join(cls.test_dir, 'game_logs.txt')
        logger.clear_logs()
        cls.port = 5888
        cls.server = ThreadingHTTPServer(('127.0.0.1', cls.port), PokerAssistantRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        logger.JSONL_PATH = cls.orig_jsonl
        logger.TXT_PATH = cls.orig_txt
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def _post(self, path, payload):
        req = urllib.request.Request(
            f'http://127.0.0.1:{self.port}{path}',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))

    def _get(self, path):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.port}{path}') as res:
            return json.loads(res.read().decode('utf-8'))

    def test_health(self):
        data = self._get('/api/health')
        self.assertEqual(data['status'], 'ok')

    def test_evaluate_hand(self):
        # 4 to Royal Flush
        res = self._post('/api/evaluate', {'cards': ['10H', 'JH', 'QH', 'KH', '2D']})
        self.assertEqual(res['status'], 'ok')
        best = res['result']['best_hold']
        self.assertEqual(best['held_cards'], ['10H', 'JH', 'QH', 'KH'])
        self.assertGreater(best['ev'], 12.0)

    def test_evaluate_strategy_modes(self):
        # 1. Default strategy (win_rate)
        res_default = self._post('/api/evaluate', {'cards': ['2H', '2D', '5H', '8H', 'KH']})
        self.assertEqual(res_default['status'], 'ok')
        self.assertEqual(res_default['result']['strategy'], 'win_rate')
        self.assertEqual(res_default['result']['best_hold']['held_cards'], ['2H', '2D'])

        # 2. Explicit win_rate strategy
        res_win = self._post('/api/evaluate', {'cards': ['2H', '2D', '5H', '8H', 'KH'], 'strategy': 'win_rate'})
        self.assertEqual(res_win['status'], 'ok')
        self.assertEqual(res_win['result']['strategy'], 'win_rate')
        self.assertEqual(res_win['result']['best_hold']['held_cards'], ['2H', '2D'])
        self.assertAlmostEqual(res_win['result']['best_hold']['win_rate'], 0.3317, delta=0.01)

        # 3. Explicit ev strategy
        res_ev = self._post('/api/evaluate', {'cards': ['2H', '2D', '5H', '8H', 'KH'], 'strategy': 'ev'})
        self.assertEqual(res_ev['status'], 'ok')
        self.assertEqual(res_ev['result']['strategy'], 'ev')
        self.assertEqual(res_ev['result']['best_hold']['held_cards'], ['2H', '5H', '8H', 'KH'])
        self.assertAlmostEqual(res_ev['result']['best_hold']['ev'], 2.9167, delta=0.01)

    def test_highlow_evaluation(self):
        res_a = self._post('/api/highlow', {'open_card': 'A'})
        self.assertEqual(res_a['result']['recommendation'], 'LOWER')
        self.assertEqual(res_a['result']['risk_level'], 'ZERO RISK')

        res_8 = self._post('/api/highlow', {'open_card': '8'})
        self.assertEqual(res_8['result']['recommendation'], 'NEUTRAL')
        self.assertEqual(res_8['result']['best_win_rate'], 0.5)

    def test_log_and_diagnostics(self):
        # Log a round where player followed optimal advice and hit Full House
        round_win = {
            'round_id': 'E2E-WIN-001',
            'strategy': 'win_rate',
            'initial_hand': ['7S', '7D', '8C', '8D', '2H'],
            'recommended_hold': ['7S', '7D', '8C', '8D'],
            'recommended_ev': 4.75,
            'recommended_win_rate': 1.0,
            'top_holds': [],
            'user_held': ['7S', '7D', '8C', '8D'],
            'drawn_cards': ['7H'],
            'final_hand': ['7S', '7D', '8C', '8D', '7H'],
            'final_hand_name': 'Full House',
            'payout_multiplier': 16,
            'bet_coins': 50,
            'earned_coins': 800,
            'high_low_steps': [
                {
                    'step': 1,
                    'open_card': 'K',
                    'recommendation': 'LOWER',
                    'win_prob': 0.9167,
                    'user_choice': 'LOWER',
                    'drawn_card': '3',
                    'result': 'WIN'
                }
            ]
        }
        res_win = self._post('/api/log', round_win)
        self.assertEqual(res_win['status'], 'ok')
        self.assertIn('WIN', res_win['record']['outcome'])
        self.assertEqual(res_win['record']['strategy'], 'win_rate')

        # Check logs retrieval
        logs_data = self._get('/api/logs')
        self.assertEqual(logs_data['status'], 'ok')
        matching = [r for r in logs_data['logs'] if r['round_id'] == 'E2E-WIN-001']
        self.assertTrue(len(matching) > 0)
        self.assertEqual(matching[0]['strategy'], 'win_rate')

        # Check raw text log
        raw_data = self._get('/api/logs/raw')
        self.assertIn('E2E-WIN-001', raw_data['raw_text'])
        self.assertIn('Full House', raw_data['raw_text'])
        self.assertIn('HIGH & LOW DOUBLE UP CHANCE', raw_data['raw_text'])
        self.assertIn('Strategy Mode:', raw_data['raw_text'])

    def test_e2e_highlow_bust_lifecycle(self):
        # 1. Complete Phase 1 Poker (Win 800 coins)
        round_init = {
            'round_id': 'E2E-LIFECYCLE-001',
            'initial_hand': ['7S', '7D', '8C', '8D', '2H'],
            'recommended_hold': ['7S', '7D', '8C', '8D'],
            'recommended_ev': 4.75,
            'recommended_win_rate': 1.0,
            'top_holds': [],
            'user_held': ['7S', '7D', '8C', '8D'],
            'drawn_cards': ['7H'],
            'final_hand': ['7S', '7D', '8C', '8D', '7H'],
            'final_hand_name': 'Full House',
            'payout_multiplier': 16,
            'bet_coins': 50,
            'earned_coins': 800,
            'high_low_steps': []
        }
        res1 = self._post('/api/log', round_init)
        self.assertEqual(res1['record']['earned_coins'], 800)

        # 2. Player enters High & Low, guesses Higher on 7, draws 3 (Busted!)
        round_update = dict(round_init)
        round_update['high_low_steps'] = [
            {
                'step': 1,
                'open_card': '7',
                'recommendation': 'HIGHER',
                'win_prob': 0.5833,
                'user_choice': 'HIGHER',
                'drawn_card': '3',
                'result': 'LOSS',
                'risk_level': 'HIGH RISK',
                'pot': 1600
            }
        ]
        round_update['earned_coins'] = 0
        res2 = self._post('/api/log', round_update)
        self.assertEqual(res2['record']['earned_coins'], 0)
        self.assertIn('LOSS (Busted in High & Low)', res2['record']['outcome'])

        # Verify raw log reflects bust and zero coins
        raw_data = self._get('/api/logs/raw')
        self.assertIn('E2E-LIFECYCLE-001', raw_data['raw_text'])
        self.assertIn('BUSTED at Step 1', raw_data['raw_text'])
        self.assertIn('Total Coins Won:  0 coins', raw_data['raw_text'])


if __name__ == '__main__':
    unittest.main()
