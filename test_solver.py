"""
Unit and Functional Tests for Joker Poker Assistant
Tests hand evaluations, Joker wildcards, all 32 hold EV calculations,
High & Low odds, tie redraw handling, and logging.
"""

import unittest
import os
import tempfile
import shutil
from solver import (
    card_from_str, card_to_str, card_to_display,
    eval_5_cards, analyze_all_holds, evaluate_high_low,
    generate_round_explanation, PAYOUT_TABLE
)
import logger

class TestPokerSolver(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.orig_jsonl = logger.JSONL_PATH
        cls.orig_txt = logger.TXT_PATH
        logger.JSONL_PATH = os.path.join(cls.test_dir, 'game_logs.jsonl')
        logger.TXT_PATH = os.path.join(cls.test_dir, 'game_logs.txt')

    @classmethod
    def tearDownClass(cls):
        logger.JSONL_PATH = cls.orig_jsonl
        logger.TXT_PATH = cls.orig_txt
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_card_parsing(self):
        self.assertEqual(card_from_str('10H'), (8 << 2) | 0)
        self.assertEqual(card_from_str('AS'), (12 << 2) | 3)
        self.assertEqual(card_from_str('2D'), (0 << 2) | 1)
        self.assertEqual(card_from_str('JK'), 52)
        self.assertEqual(card_from_str('JOKER'), 52)
        self.assertEqual(card_from_str('10♥'), (8 << 2) | 0)
        self.assertEqual(card_from_str('A♠'), (12 << 2) | 3)
        
        self.assertEqual(card_to_str((8 << 2) | 0), '10H')
        self.assertEqual(card_to_str(52), 'JK')
        self.assertEqual(card_to_display(52), '🃏 Joker')

    def test_all_hand_types_natural(self):
        # Royal Flush
        p, name = eval_5_cards([card_from_str(c) for c in ['10H', 'JH', 'QH', 'KH', 'AH']])
        self.assertEqual((p, name), (200, 'Royal Flush'))
        
        # Straight Flush
        p, name = eval_5_cards([card_from_str(c) for c in ['5D', '6D', '7D', '8D', '9D']])
        self.assertEqual((p, name), (60, 'Straight Flush'))
        
        # Wheel Straight Flush (A-2-3-4-5)
        p, name = eval_5_cards([card_from_str(c) for c in ['AD', '2D', '3D', '4D', '5D']])
        self.assertEqual((p, name), (60, 'Straight Flush'))
        
        # Four of a Kind (Quads)
        p, name = eval_5_cards([card_from_str(c) for c in ['9H', '9D', '9C', '9S', '2H']])
        self.assertEqual((p, name), (30, 'Quads'))
        
        # Full House
        p, name = eval_5_cards([card_from_str(c) for c in ['7S', '7D', '7H', '8C', '8D']])
        self.assertEqual((p, name), (16, 'Full House'))
        
        # Flush
        p, name = eval_5_cards([card_from_str(c) for c in ['2C', '5C', '7C', '9C', 'JC']])
        self.assertEqual((p, name), (14, 'Flush'))
        
        # Straight
        p, name = eval_5_cards([card_from_str(c) for c in ['6H', '7D', '8S', '9C', '10H']])
        self.assertEqual((p, name), (8, 'Straight'))
        
        # Wheel Straight (A-2-3-4-5)
        p, name = eval_5_cards([card_from_str(c) for c in ['AH', '2D', '3S', '4C', '5H']])
        self.assertEqual((p, name), (8, 'Straight'))
        
        # Three of a Kind (Trips)
        p, name = eval_5_cards([card_from_str(c) for c in ['4H', '4D', '4S', '9C', 'KD']])
        self.assertEqual((p, name), (4, 'Trips'))
        
        # Two Pair
        p, name = eval_5_cards([card_from_str(c) for c in ['4H', '4D', '8S', '8C', 'KD']])
        self.assertEqual((p, name), (4, 'Two Pair'))
        
        # One Pair (pays 0)
        p, name = eval_5_cards([card_from_str(c) for c in ['4H', '4D', '7S', '8C', 'KD']])
        self.assertEqual((p, name), (0, 'One Pair'))
        
        # High Card (pays 0)
        p, name = eval_5_cards([card_from_str(c) for c in ['2H', '5D', '7S', '9C', 'KD']])
        self.assertEqual((p, name), (0, 'High Card'))

    def test_joker_wildcards(self):
        # Joker Royal Flush
        p, name = eval_5_cards([card_from_str(c) for c in ['10S', 'JS', 'QS', 'KS', 'JK']])
        self.assertEqual((p, name), (200, 'Royal Flush'))
        
        # Five of a Kind
        p, name = eval_5_cards([card_from_str(c) for c in ['AS', 'AH', 'AD', 'AC', 'JK']])
        self.assertEqual((p, name), (140, 'Five of a Kind'))
        
        # Joker Straight Flush
        p, name = eval_5_cards([card_from_str(c) for c in ['5H', '6H', '8H', '9H', 'JK']])
        self.assertEqual((p, name), (60, 'Straight Flush'))
        
        # Joker Wheel Straight Flush
        p, name = eval_5_cards([card_from_str(c) for c in ['AH', '2H', '4H', '5H', 'JK']])
        self.assertEqual((p, name), (60, 'Straight Flush'))
        
        # Joker Quads
        p, name = eval_5_cards([card_from_str(c) for c in ['7H', '7D', '7S', 'KC', 'JK']])
        self.assertEqual((p, name), (30, 'Quads'))
        
        # Joker Full House (Two Pair + Joker)
        p, name = eval_5_cards([card_from_str(c) for c in ['7H', '7D', '9S', '9C', 'JK']])
        self.assertEqual((p, name), (16, 'Full House'))
        
        # Joker Flush
        p, name = eval_5_cards([card_from_str(c) for c in ['2D', '5D', '8D', 'KD', 'JK']])
        self.assertEqual((p, name), (14, 'Flush'))
        
        # Joker Straight
        p, name = eval_5_cards([card_from_str(c) for c in ['4H', '5D', '6S', '8C', 'JK']])
        self.assertEqual((p, name), (8, 'Straight'))
        
        # Joker Wheel Straight
        p, name = eval_5_cards([card_from_str(c) for c in ['AH', '2D', '4S', '5C', 'JK']])
        self.assertEqual((p, name), (8, 'Straight'))
        
        # Joker Trips (One Pair + Joker)
        p, name = eval_5_cards([card_from_str(c) for c in ['3H', '3D', '7S', '9C', 'JK']])
        self.assertEqual((p, name), (4, 'Trips'))
        
        # Joker High Card (no straight/flush, 4 singletons + Joker makes 1 pair -> pays 0)
        p, name = eval_5_cards([card_from_str(c) for c in ['2H', '4D', '7S', '9C', 'JK']])
        self.assertEqual((p, name), (0, 'One Pair'))

    def test_ev_hold_analysis(self):
        # Hand: 10H, JH, QH, KH, 2D (4 to Royal Flush)
        # Should recommend holding first 4 cards
        cards = [card_from_str(c) for c in ['10H', 'JH', 'QH', 'KH', '2D']]
        result = analyze_all_holds(cards)
        
        self.assertEqual(len(result['all_holds']), 32)
        best = result['best_hold']
        self.assertEqual(best['held_cards'], ['10H', 'JH', 'QH', 'KH'])
        self.assertEqual(best['discarded_cards'], ['2D'])
        # EV should be approximately 12.625
        self.assertAlmostEqual(best['ev'], 12.625, delta=0.01)
        self.assertGreater(best['ev'], 10.0)

    def test_quintuple_hold(self):
        # Dealt a pat Royal Flush: should recommend holding all 5 cards (EV=200)
        cards = [card_from_str(c) for c in ['10S', 'JS', 'QS', 'KS', 'AS']]
        result = analyze_all_holds(cards)
        best = result['best_hold']
        self.assertEqual(len(best['held_cards']), 5)
        self.assertEqual(best['ev'], 200.0)

    def test_joker_in_hand_analysis(self):
        # Joker in initial hand: Joker + 4 Aces
        cards = [card_from_str(c) for c in ['AS', 'AH', 'AD', 'AC', 'JK']]
        result = analyze_all_holds(cards)
        best = result['best_hold']
        self.assertEqual(len(best['held_cards']), 5)
        self.assertEqual(best['ev'], 140.0)

    def test_strategy_modes_divergence(self):
        # Hand: 2H, 2D, 5H, 8H, KH (Low pair vs 4 to a Flush)
        cards = [card_from_str(c) for c in ['2H', '2D', '5H', '8H', 'KH']]
        
        # Max Win Rate strategy (High & Low Qualifier):
        # Prefers holding made pair (2H, 2D) because win rate is ~33.17%, qualifying for High & Low
        res_win = analyze_all_holds(cards, strategy='win_rate')
        best_win = res_win['best_hold']
        self.assertEqual(best_win['held_cards'], ['2H', '2D'])
        self.assertAlmostEqual(best_win['win_rate'], 0.3317, delta=0.01)
        self.assertEqual(res_win['strategy'], 'win_rate')
        
        # Max Reward (EV) strategy:
        # Prefers holding 4 to a Flush (2H, 5H, 8H, KH) because EV is ~2.9167 (14x payout on hit),
        # even though win rate is only ~20.83%
        res_ev = analyze_all_holds(cards, strategy='ev')
        best_ev = res_ev['best_hold']
        self.assertEqual(best_ev['held_cards'], ['2H', '5H', '8H', 'KH'])
        self.assertAlmostEqual(best_ev['ev'], 2.9167, delta=0.01)
        self.assertEqual(res_ev['strategy'], 'ev')
        
        # Verify the two strategies picked different holds
        self.assertNotEqual(best_win['held_cards'], best_ev['held_cards'])

    def test_default_strategy_is_win_rate(self):
        # analyze_all_holds without strategy parameter must default to win_rate
        cards = [card_from_str(c) for c in ['2H', '2D', '5H', '8H', 'KH']]
        res_default = analyze_all_holds(cards)
        self.assertEqual(res_default['strategy'], 'win_rate')
        self.assertEqual(res_default['best_hold']['held_cards'], ['2H', '2D'])

    def test_strategy_tie_breaking(self):
        cards = [card_from_str(c) for c in ['10H', 'JH', 'QH', 'KH', '2D']]
        res_win = analyze_all_holds(cards, strategy='win_rate')
        res_ev = analyze_all_holds(cards, strategy='ev')
        
        # In win_rate mode, list should be sorted by win_rate descending, then EV descending
        for i in range(len(res_win['all_holds']) - 1):
            h1 = res_win['all_holds'][i]
            h2 = res_win['all_holds'][i+1]
            self.assertTrue(h1['win_rate'] > h2['win_rate'] or (h1['win_rate'] == h2['win_rate'] and h1['ev'] >= h2['ev']))
            
        # In ev mode, list should be sorted by EV descending, then win_rate descending
        for i in range(len(res_ev['all_holds']) - 1):
            h1 = res_ev['all_holds'][i]
            h2 = res_ev['all_holds'][i+1]
            self.assertTrue(h1['ev'] > h2['ev'] or (h1['ev'] == h2['ev'] and h1['win_rate'] >= h2['win_rate']))

    def test_high_low_evaluator(self):
        # Open card: Ace (highest) -> 100% win on Lower
        res_a = evaluate_high_low('A')
        self.assertEqual(res_a['recommendation'], 'LOWER')
        self.assertEqual(res_a['best_win_rate'], 1.0)
        self.assertEqual(res_a['higher_cards_count'], 0)
        self.assertEqual(res_a['lower_cards_count'], 48)
        self.assertEqual(res_a['tie_cards_count'], 3)
        
        # Open card: 2 (lowest) -> 100% win on Higher
        res_2 = evaluate_high_low('2')
        self.assertEqual(res_2['recommendation'], 'HIGHER')
        self.assertEqual(res_2['best_win_rate'], 1.0)
        self.assertEqual(res_2['higher_cards_count'], 48)
        self.assertEqual(res_2['lower_cards_count'], 0)
        
        # Open card: 8 -> Neutral 50/50
        res_8 = evaluate_high_low('8')
        self.assertEqual(res_8['recommendation'], 'NEUTRAL')
        self.assertEqual(res_8['best_win_rate'], 0.50)
        self.assertEqual(res_8['higher_cards_count'], 24)
        self.assertEqual(res_8['lower_cards_count'], 24)
        
        # Open card: 7 -> Higher is 58.33%
        res_7 = evaluate_high_low('7')
        self.assertEqual(res_7['recommendation'], 'HIGHER')
        self.assertAlmostEqual(res_7['best_win_rate'], 28/48, places=3)
        
        # Open card: 9 -> Lower is 58.33%
        res_9 = evaluate_high_low('9')
        self.assertEqual(res_9['recommendation'], 'LOWER')
        self.assertAlmostEqual(res_9['best_win_rate'], 28/48, places=3)

    def test_round_explanation_generation(self):
        exp_win = generate_round_explanation(
            initial_cards_str=['10H', 'JH', 'QH', 'KH', '2D'],
            recommended_hold_indices=[0, 1, 2, 3],
            recommended_ev=12.63,
            user_held_indices=[0, 1, 2, 3],
            drawn_cards_str=['AH'],
            final_cards_str=['10H', 'JH', 'QH', 'KH', 'AH'],
            final_hand_name='Royal Flush',
            payout_multiplier=200
        )
        self.assertIn('WIN (Royal Flush paying 200x)', exp_win)
        self.assertIn('Optimal move followed', exp_win)
        
        exp_loss = generate_round_explanation(
            initial_cards_str=['10H', 'JH', 'QH', 'KH', '2D'],
            recommended_hold_indices=[0, 1, 2, 3],
            recommended_ev=12.63,
            user_held_indices=[0, 1, 2, 3],
            drawn_cards_str=['3C'],
            final_cards_str=['10H', 'JH', 'QH', 'KH', '3C'],
            final_hand_name='High Card',
            payout_multiplier=0
        )
        self.assertIn('LOSS (High Card paying 0x)', exp_loss)
        self.assertIn('Unfavorable draw variance', exp_loss)

        # Test strategy-aware explanation for Win Rate mode
        exp_win_sub = generate_round_explanation(
            initial_cards_str=['2H', '2D', '5H', '8H', 'KH'],
            recommended_hold_indices=[0, 1],
            recommended_ev=1.70,
            user_held_indices=[0, 2, 3, 4],
            drawn_cards_str=['3S'],
            final_cards_str=['2H', '5H', '8H', 'KH', '3S'],
            final_hand_name='High Card',
            payout_multiplier=0,
            strategy='win_rate',
            recommended_win_rate=0.3317
        )
        self.assertIn('Suboptimal play detected', exp_win_sub)
        self.assertIn('Win: 33.2%', exp_win_sub)
        self.assertIn('lower win rate hold', exp_win_sub)

    def test_logger_functionality(self):
        # Test logging a round
        round_data = {
            'round_id': 'TEST-ROUND-001',
            'initial_hand': ['10H', 'JH', 'QH', 'KH', '2D'],
            'recommended_hold': ['10H', 'JH', 'QH', 'KH'],
            'recommended_ev': 12.63,
            'recommended_win_rate': 0.3125,
            'top_holds': [],
            'user_held': ['10H', 'JH', 'QH', 'KH'],
            'drawn_cards': ['3C'],
            'final_hand': ['10H', 'JH', 'QH', 'KH', '3C'],
            'final_hand_name': 'High Card',
            'payout_multiplier': 0,
            'bet_coins': 50,
            'earned_coins': 0,
            'diagnostic': 'Unlucky draw miss (variance).',
            'high_low_steps': []
        }
        res = logger.log_round(round_data)
        self.assertEqual(res['round_id'], 'TEST-ROUND-001')
        self.assertEqual(res['strategy'], 'win_rate')
        
        recent = logger.get_recent_logs(5)
        self.assertTrue(any(r['round_id'] == 'TEST-ROUND-001' for r in recent))
        
        raw_text = logger.get_raw_txt_logs(500)
        self.assertIn('TEST-ROUND-001', raw_text)
        self.assertIn('10♥', raw_text)
        self.assertIn('Strategy Mode:', raw_text)

    def test_t_rank_alias_and_case(self):
        # 'TH', 'ts', '10h', 'jk'
        self.assertEqual(card_from_str('TH'), (8 << 2) | 0)
        self.assertEqual(card_from_str('ts'), (8 << 2) | 3)
        self.assertEqual(card_from_str('10h'), (8 << 2) | 0)
        self.assertEqual(card_from_str('jk'), 52)
        
        # High Low with 'T'
        hl_t = evaluate_high_low('T')
        hl_10 = evaluate_high_low('10')
        self.assertEqual(hl_t['recommendation'], hl_10['recommendation'])
        self.assertEqual(hl_t['best_win_rate'], hl_10['best_win_rate'])

    def test_round_update_with_high_low_bust(self):
        # 1. Initially player wins Full House (+800 coins)
        round_data = {
            'round_id': 'TEST-BUST-001',
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
            'diagnostic': 'Hit Full House.',
            'high_low_steps': []
        }
        rec1 = logger.log_round(round_data)
        self.assertEqual(rec1['earned_coins'], 800)

        # 2. Player enters High & Low, wins Step 1, busts on Step 2
        round_data['high_low_steps'] = [
            {
                'step': 1, 'open_card': 'K', 'recommendation': 'LOWER', 'user_choice': 'LOWER',
                'drawn_card': '5', 'result': 'WIN', 'win_prob': 0.9231, 'risk_level': 'VERY LOW RISK', 'pot': 1600
            },
            {
                'step': 2, 'open_card': '5', 'recommendation': 'HIGHER', 'user_choice': 'HIGHER',
                'drawn_card': '2', 'result': 'LOSS', 'win_prob': 0.75, 'risk_level': 'LOW RISK', 'pot': 3200
            }
        ]
        round_data['diagnostic'] = generate_round_explanation(
            initial_cards_str=round_data['initial_hand'],
            recommended_hold_indices=[0, 1, 2, 3],
            recommended_ev=4.75,
            user_held_indices=[0, 1, 2, 3],
            drawn_cards_str=['7H'],
            final_cards_str=round_data['final_hand'],
            final_hand_name='Full House',
            payout_multiplier=16,
            high_low_steps=round_data['high_low_steps'],
            final_coins=0
        )
        rec2 = logger.log_round(round_data)

        # Confirm update: earned coins dropped to 0, outcome marked as bust!
        self.assertEqual(rec2['round_id'], 'TEST-BUST-001')
        self.assertEqual(rec2['earned_coins'], 0)
        self.assertIn('LOSS (Busted in High & Low)', rec2['outcome'])

        # Check raw text log
        raw_text = logger.get_raw_txt_logs(100)
        self.assertIn('TEST-BUST-001', raw_text)
        self.assertIn('BUSTED at Step 2', raw_text)
        self.assertIn('Total Coins Won:  0 coins', raw_text)

    def test_round_update_with_cashout(self):
        round_data = {
            'round_id': 'TEST-CASH-001',
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
            'earned_coins': 3200,
            'high_low_steps': [
                {
                    'step': 1, 'open_card': 'K', 'recommendation': 'LOWER', 'user_choice': 'LOWER',
                    'drawn_card': '5', 'result': 'WIN', 'win_prob': 0.9231, 'risk_level': 'VERY LOW RISK', 'pot': 1600
                },
                {
                    'step': 2, 'open_card': '5', 'recommendation': 'HIGHER', 'user_choice': 'HIGHER',
                    'drawn_card': '10', 'result': 'WIN', 'win_prob': 0.75, 'risk_level': 'LOW RISK', 'pot': 3200
                },
                {
                    'step': 3, 'open_card': '10', 'recommendation': 'LOWER', 'user_choice': 'CASHOUT',
                    'drawn_card': 'None', 'result': 'CASHOUT', 'win_prob': 0.6667, 'risk_level': 'MODERATE RISK', 'pot': 3200
                }
            ]
        }
        round_data['diagnostic'] = generate_round_explanation(
            initial_cards_str=round_data['initial_hand'],
            recommended_hold_indices=[0, 1, 2, 3],
            recommended_ev=4.75,
            user_held_indices=[0, 1, 2, 3],
            drawn_cards_str=['7H'],
            final_cards_str=round_data['final_hand'],
            final_hand_name='Full House',
            payout_multiplier=16,
            high_low_steps=round_data['high_low_steps'],
            final_coins=3200
        )
        rec = logger.log_round(round_data)
        self.assertEqual(rec['earned_coins'], 3200)
        self.assertIn('WIN', rec['outcome'])

        raw_text = logger.get_raw_txt_logs(100)
        self.assertIn('TEST-CASH-001', raw_text)
        self.assertIn('Total Coins Won:  3200 coins', raw_text)

    def test_standalone_high_low_logging(self):
        round_data = {
            'round_id': 'HL-STANDALONE-001',
            'initial_hand': [],
            'recommended_hold': [],
            'user_held': [],
            'drawn_cards': [],
            'final_hand': [],
            'final_hand_name': 'Direct HL',
            'payout_multiplier': 1,
            'bet_coins': 50,
            'earned_coins': 200,
            'high_low_steps': [
                {
                    'step': 1, 'open_card': 'K', 'recommendation': 'LOWER', 'user_choice': 'LOWER',
                    'drawn_card': '7', 'result': 'WIN', 'win_prob': 0.9231, 'risk_level': 'VERY LOW RISK', 'pot': 100
                },
                {
                    'step': 2, 'open_card': '7', 'recommendation': 'HIGHER', 'user_choice': 'HIGHER',
                    'drawn_card': 'Q', 'result': 'WIN', 'win_prob': 0.5833, 'risk_level': 'HIGH RISK', 'pot': 200
                }
            ],
            'diagnostic': 'Standalone High & Low: won 200 coins.'
        }
        rec = logger.log_round(round_data)
        self.assertEqual(rec['round_id'], 'HL-STANDALONE-001')
        raw_text = logger.get_raw_txt_logs(100)
        self.assertIn('HL-STANDALONE-001', raw_text)
        self.assertIn('STANDALONE HIGH & LOW DOUBLE UP', raw_text)


if __name__ == '__main__':
    unittest.main()
