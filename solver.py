"""
Joker Poker & High-Low Solver Engine
Evaluates 5-card draw poker hands with 1 Joker (53-card deck) and High-Low Double Up.
"""

from typing import List, Tuple, Dict, Any, Optional
import itertools

# Card encoding:
# Standard cards: card_id = (rank << 2) | suit
# Ranks: 0 = '2', 1 = '3', ..., 8 = '10', 9 = 'J', 10 = 'Q', 11 = 'K', 12 = 'A'
# Suits: 0 = 'H' (Hearts), 1 = 'D' (Diamonds), 2 = 'C' (Clubs), 3 = 'S' (Spades)
# Joker: card_id = 52 (rank 13, suit 4)

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['H', 'D', 'C', 'S']
SUIT_SYMBOLS = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}
SUIT_NAMES = {'H': 'Hearts', 'D': 'Diamonds', 'C': 'Clubs', 'S': 'Spades'}

RANK_LOOKUP = {r: i for i, r in enumerate(RANKS)}
RANK_LOOKUP['T'] = 8  # Alias 'T' to 10 for standard poker notation
SUIT_LOOKUP = {s: i for i, s in enumerate(SUITS)}

# Payout Table (Joker Wild 53-Card Deck)
PAYOUT_TABLE = {
    'Royal Flush': 200,
    'Five of a Kind': 140,
    'Straight Flush': 60,
    'Quads': 30,
    'Full House': 16,
    'Flush': 14,
    'Straight': 8,
    'Trips': 4,
    'Two Pair': 4,
    'One Pair': 0,
    'High Card': 0,
}

# Bitmask precomputations
STRAIGHT_MASKS = set([0b11111 << i for i in range(9)] + [(1 << 12) | 0b1111])  # 9 normal + 1 wheel (A-2-3-4-5)
ROYAL_MASK = (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11) | (1 << 12)

STRAIGHT_4_MASKS = set()
for sm in STRAIGHT_MASKS:
    for b in range(13):
        if sm & (1 << b):
            STRAIGHT_4_MASKS.add(sm ^ (1 << b))

ROYAL_4_MASKS = set()
for b in range(8, 13):
    ROYAL_4_MASKS.add(ROYAL_MASK ^ (1 << b))


def card_from_str(card_str: str) -> int:
    """Parse card string like '10H', 'AS', '2D', 'TH', 'JK' or 'JOKER' into card_id (0..52)."""
    if not card_str:
        raise ValueError("Empty card string.")
    s = card_str.strip().upper()
    if s in ('JK', 'JOKER', 'WILD', 'JOKER1'):
        return 52
    
    # Handle suit symbol if present
    for suit_char, sym in [('H', '♥'), ('D', '♦'), ('C', '♣'), ('S', '♠')]:
        s = s.replace(sym, suit_char)
    
    suit_part = s[-1]
    rank_part = s[:-1]
    if rank_part == 'T':
        rank_part = '10'
    if suit_part not in SUIT_LOOKUP or rank_part not in RANK_LOOKUP:
        raise ValueError(f"Invalid card format: '{card_str}'. Example formats: '10H', 'AS', '2D', 'JK'")
    
    return (RANK_LOOKUP[rank_part] << 2) | SUIT_LOOKUP[suit_part]


def card_to_str(card_id: int) -> str:
    """Convert card_id to string representation, e.g. '10H', 'AS', 'JK'."""
    if card_id == 52:
        return 'JK'
    rank = card_id >> 2
    suit = card_id & 3
    return f"{RANKS[rank]}{SUITS[suit]}"


def card_to_display(card_id: int) -> str:
    """Convert card_id to user friendly display string with symbols, e.g. '10♥', 'A♠', '🃏 Joker'."""
    if card_id == 52:
        return '🃏 Joker'
    rank = card_id >> 2
    suit = card_id & 3
    return f"{RANKS[rank]}{SUIT_SYMBOLS[SUITS[suit]]}"


def eval_5_cards(cards: List[int]) -> Tuple[int, str]:
    """
    Evaluate 5 cards (with at most 1 Joker = 52).
    Returns (payout_multiplier, hand_name).
    Cards can be in any order.
    """
    c = sorted(cards)
    
    # Case 1: Joker is present (will be last element since 52 is highest ID)
    if c[4] == 52:
        c1, c2, c3, c4 = c[0], c[1], c[2], c[3]
        r1, s1 = c1 >> 2, c1 & 3
        r2, s2 = c2 >> 2, c2 & 3
        r3, s3 = c3 >> 2, c3 & 3
        r4, s4 = c4 >> 2, c4 & 3
        
        mask = (1 << r1) | (1 << r2) | (1 << r3) | (1 << r4)
        nd = bin(mask).count('1')
        
        if nd == 4:
            is_flush4 = (s1 == s2 == s3 == s4)
            if is_flush4:
                if mask in ROYAL_4_MASKS:
                    return 200, 'Royal Flush'
                if mask in STRAIGHT_4_MASKS:
                    return 60, 'Straight Flush'
                return 14, 'Flush'
            if mask in STRAIGHT_4_MASKS:
                return 8, 'Straight'
            return 0, 'One Pair'  # Joker forms a pair with 1 card -> 0 payout
            
        if nd == 3:
            # Pair + Joker -> Three of a Kind
            return 4, 'Trips'
            
        if nd == 2:
            # (3, 1) -> Joker makes Quads (30); (2, 2) -> Joker makes Full House (16)
            cnt1 = (r1 == r1) + (r2 == r1) + (r3 == r1) + (r4 == r1)
            if cnt1 == 1 or cnt1 == 3:
                return 30, 'Quads'
            return 16, 'Full House'
            
        # nd == 1: 4 of a kind + Joker -> Five of a Kind
        return 140, 'Five of a Kind'

    # Case 2: No Joker (Standard 5 cards)
    c1, c2, c3, c4, c5 = c[0], c[1], c[2], c[3], c[4]
    r1, s1 = c1 >> 2, c1 & 3
    r2, s2 = c2 >> 2, c2 & 3
    r3, s3 = c3 >> 2, c3 & 3
    r4, s4 = c4 >> 2, c4 & 3
    r5, s5 = c5 >> 2, c5 & 3
    
    mask = (1 << r1) | (1 << r2) | (1 << r3) | (1 << r4) | (1 << r5)
    nd = bin(mask).count('1')
    
    if nd == 5:
        is_flush = (s1 == s2 == s3 == s4 == s5)
        is_straight = mask in STRAIGHT_MASKS
        if is_flush and is_straight:
            if mask == ROYAL_MASK:
                return 200, 'Royal Flush'
            return 60, 'Straight Flush'
        if is_flush:
            return 14, 'Flush'
        if is_straight:
            return 8, 'Straight'
        return 0, 'High Card'
        
    if nd == 4:
        return 0, 'One Pair'
        
    if nd == 3:
        cnt1 = (r1 == r1) + (r2 == r1) + (r3 == r1) + (r4 == r1) + (r5 == r1)
        cnt2 = (r1 == r2) + (r2 == r2) + (r3 == r2) + (r4 == r2) + (r5 == r2)
        cnt3 = (r1 == r3) + (r2 == r3) + (r3 == r3) + (r4 == r3) + (r5 == r3)
        if cnt1 == 3 or cnt2 == 3 or cnt3 == 3:
            return 4, 'Trips'
        return 4, 'Two Pair'
        
    if nd == 2:
        cnt1 = (r1 == r1) + (r2 == r1) + (r3 == r1) + (r4 == r1) + (r5 == r1)
        if cnt1 == 1 or cnt1 == 4:
            return 30, 'Quads'
        return 16, 'Full House'
        
    return 0, 'High Card'


def analyze_all_holds(initial_cards: List[int], strategy: str = 'win_rate') -> Dict[str, Any]:
    """
    Evaluate all 32 hold combinations for the initial 5 cards.
    Strategies:
      - 'win_rate' (Default): Ranks holds by highest probability of making a qualifying winning hand
                              (Two Pair or better, >= 4x payout), breaking ties by EV.
      - 'ev': Ranks holds by Expected Value (average coins), breaking ties by win_rate.
    Returns structured analysis with best hold, full sorted rankings, and distribution.
    """
    if len(initial_cards) != 5:
        raise ValueError("Must provide exactly 5 cards.")
    if len(set(initial_cards)) != 5:
        raise ValueError("Cards must all be distinct.")
    for c in initial_cards:
        if not (0 <= c <= 52):
            raise ValueError(f"Card ID {c} out of valid range (0..52).")

    initial_set = set(initial_cards)
    remaining_deck = [c for c in range(53) if c not in initial_set]
    
    holds_results = []
    
    HAND_TYPES = [
        'Royal Flush', 'Five of a Kind', 'Straight Flush', 'Quads',
        'Full House', 'Flush', 'Straight', 'Trips', 'Two Pair',
        'One Pair', 'High Card'
    ]
    
    # Evaluate all 32 combinations (from hold 5 down to hold 0)
    for hold_count in range(5, -1, -1):
        for hold_indices in itertools.combinations(range(5), hold_count):
            held = [initial_cards[i] for i in hold_indices]
            n_draw = 5 - hold_count
            
            payout_sum = 0
            n_combos = 0
            hand_counts = {ht: 0 for ht in HAND_TYPES}
            
            if n_draw == 0:
                payout, hname = eval_5_cards(held)
                payout_sum = payout
                n_combos = 1
                hand_counts[hname] = 1
            else:
                held_tuple = tuple(held)
                for draw_cards in itertools.combinations(remaining_deck, n_draw):
                    n_combos += 1
                    full = held_tuple + draw_cards
                    payout, hname = eval_5_cards(list(full))
                    payout_sum += payout
                    hand_counts[hname] += 1
            
            ev = payout_sum / n_combos
            paying_combos = sum(hand_counts[ht] for ht in HAND_TYPES if PAYOUT_TABLE[ht] > 0)
            win_rate = paying_combos / n_combos
            
            discard_indices = tuple(i for i in range(5) if i not in hold_indices)
            
            holds_results.append({
                'hold_indices': list(hold_indices),
                'discard_indices': list(discard_indices),
                'held_cards': [card_to_str(c) for c in held],
                'held_display': [card_to_display(c) for c in held],
                'discarded_cards': [card_to_str(initial_cards[i]) for i in discard_indices],
                'discarded_display': [card_to_display(initial_cards[i]) for i in discard_indices],
                'ev': round(ev, 4),
                'win_rate': round(win_rate, 4),
                'total_combos': n_combos,
                'distribution': hand_counts
            })
            
    strat = (strategy or 'win_rate').strip().lower()
    if strat in ('ev', 'reward', 'max_reward'):
        holds_results.sort(key=lambda x: (x['ev'], x['win_rate']), reverse=True)
        strat_key = 'ev'
    else:
        holds_results.sort(key=lambda x: (x['win_rate'], x['ev']), reverse=True)
        strat_key = 'win_rate'
    best_hold = holds_results[0]
    
    current_payout, current_hand_name = eval_5_cards(initial_cards)
    
    return {
        'initial_hand': [card_to_str(c) for c in initial_cards],
        'initial_display': [card_to_display(c) for c in initial_cards],
        'current_hand_name': current_hand_name,
        'current_payout': current_payout,
        'best_hold': best_hold,
        'all_holds': holds_results,
        'strategy': strat_key
    }


def evaluate_high_low(open_card_str: str) -> Dict[str, Any]:
    """
    Calculate exact probabilities and advice for High & Low Double Up.
    Card strength: A > K > Q > J > 10 > 9 > 8 > 7 > 6 > 5 > 4 > 3 > 2 (Ace is 14, 2 is 2).
    Rule: Redraw on tie (matching number) - no loss!
    """
    s = open_card_str.strip().upper()
    for sym in ['♥', '♦', '♣', '♠', 'H', 'D', 'C', 'S']:
        s = s.replace(sym, '')
    if s == 'T':
        s = '10'
    
    if s not in RANK_LOOKUP:
        raise ValueError(f"Invalid rank '{open_card_str}'. Expected rank 2 to A.")
        
    rank_idx = RANK_LOOKUP[s]  # 0 to 12 (0 is '2', 12 is 'A')
    
    num_higher_cards = (12 - rank_idx) * 4
    num_lower_cards = rank_idx * 4
    num_tie_cards = 3
    total_remaining = 51
    
    raw_higher_prob = num_higher_cards / total_remaining
    raw_lower_prob = num_lower_cards / total_remaining
    raw_tie_prob = num_tie_cards / total_remaining
    
    decisive_total = num_higher_cards + num_lower_cards
    if decisive_total > 0:
        eff_higher_win_rate = num_higher_cards / decisive_total
        eff_lower_win_rate = num_lower_cards / decisive_total
    else:
        eff_higher_win_rate = 0.5
        eff_lower_win_rate = 0.5
        
    if eff_higher_win_rate > eff_lower_win_rate:
        recommendation = 'HIGHER'
        best_win_rate = eff_higher_win_rate
    elif eff_lower_win_rate > eff_higher_win_rate:
        recommendation = 'LOWER'
        best_win_rate = eff_lower_win_rate
    else:
        recommendation = 'NEUTRAL'
        best_win_rate = 0.50
        
    if best_win_rate == 1.0:
        risk_level = 'ZERO RISK'
        risk_color = '#10b981'
        advice = f"100% Guaranteed Win! Pick {recommendation}. No chance of losing."
    elif best_win_rate >= 0.90:
        risk_level = 'VERY LOW RISK'
        risk_color = '#10b981'
        advice = f"Extremely Safe ({best_win_rate*100:.1f}% Win Chance). Strongly recommend {recommendation}."
    elif best_win_rate >= 0.75:
        risk_level = 'LOW RISK'
        risk_color = '#3b82f6'
        advice = f"Favorable Odds ({best_win_rate*100:.1f}% Win Chance). Pick {recommendation}."
    elif best_win_rate >= 0.65:
        risk_level = 'MODERATE RISK'
        risk_color = '#f59e0b'
        advice = f"Moderate Edge ({best_win_rate*100:.1f}% Win Chance). Pick {recommendation}."
    elif best_win_rate > 0.50:
        risk_level = 'HIGH RISK'
        risk_color = '#f97316'
        advice = f"Slight Edge ({best_win_rate*100:.1f}% Win Chance). Caution: 41.7% chance to lose all coins!"
    else:
        risk_level = 'EXTREME RISK (COIN TOSS)'
        risk_color = '#ef4444'
        advice = "50/50 Coin Flip! Exactly equal chance of Higher or Lower. High danger of losing accumulated coins."

    return {
        'open_card_rank': s,
        'recommendation': recommendation,
        'best_win_rate': round(best_win_rate, 4),
        'eff_higher_win_rate': round(eff_higher_win_rate, 4),
        'eff_lower_win_rate': round(eff_lower_win_rate, 4),
        'raw_higher_prob': round(raw_higher_prob, 4),
        'raw_lower_prob': round(raw_lower_prob, 4),
        'raw_tie_prob': round(raw_tie_prob, 4),
        'higher_cards_count': num_higher_cards,
        'lower_cards_count': num_lower_cards,
        'tie_cards_count': num_tie_cards,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'advice': advice
    }


def generate_round_explanation(
    initial_cards_str: List[str],
    recommended_hold_indices: List[int],
    recommended_ev: float,
    user_held_indices: List[int],
    drawn_cards_str: List[str],
    final_cards_str: List[str],
    final_hand_name: str,
    payout_multiplier: int,
    high_low_steps: Optional[List[Dict[str, Any]]] = None,
    final_coins: Optional[int] = None,
    strategy: str = 'win_rate',
    recommended_win_rate: Optional[float] = None
) -> str:
    """Generate a human-readable explanation of the round outcome and variance."""
    explanation_lines = []

    # Standalone High & Low session
    if not initial_cards_str and high_low_steps:
        explanation_lines.append("[Standalone High & Low Session]")
        last_step = high_low_steps[-1]
        last_res = str(last_step.get('result', '')).upper()
        if 'LOSS' in last_res or 'BUST' in last_res:
            open_c = last_step.get('open_card', '?')
            rec_c = last_step.get('recommendation', '?')
            user_c = last_step.get('user_choice', rec_c)
            drawn_c = last_step.get('drawn_card', '?')
            win_pct = last_step.get('win_prob', 0) * 100
            if user_c == rec_c:
                explanation_lines.append(
                    f"Outcome: BUSTED on Step {len(high_low_steps)} (0 coins). Diagnostic: Followed optimal advice ({rec_c}), "
                    f"but drew {drawn_c} against open card {open_c}. Unfavorable draw variance ({100-win_pct:.1f}% underdog card)."
                )
            else:
                explanation_lines.append(
                    f"Outcome: BUSTED on Step {len(high_low_steps)} (0 coins). Diagnostic: Player misplay. Picked {user_c} "
                    f"when recommended move was {rec_c} ({win_pct:.1f}% win rate)."
                )
        else:
            explanation_lines.append(
                f"Outcome: CASHED OUT / WON ({final_coins or 'positive'} coins across {len(high_low_steps)} steps). "
                f"Diagnostic: Successfully navigated High & Low Double Up!"
            )
        return ' '.join(explanation_lines)

    is_optimal_play = (sorted(recommended_hold_indices) == sorted(user_held_indices))
    held_cards_str = [initial_cards_str[i] for i in user_held_indices] if initial_cards_str else []
    discarded_str = [initial_cards_str[i] for i in range(len(initial_cards_str)) if i not in user_held_indices] if initial_cards_str else []

    if payout_multiplier > 0:
        outcome_type = f"WIN ({final_hand_name} paying {payout_multiplier}x)"
    else:
        outcome_type = f"LOSS ({final_hand_name} paying 0x)"

    explanation_lines.append(f"Phase 1 Outcome: {outcome_type}.")

    if recommended_win_rate is not None:
        rec_stat = f"Win: {recommended_win_rate*100:.1f}% | EV: {recommended_ev:.2f}x" if strategy != 'ev' else f"EV: {recommended_ev:.2f}x | Win: {recommended_win_rate*100:.1f}%"
    else:
        rec_stat = f"EV: {recommended_ev:.2f}x"

    if is_optimal_play:
        explanation_lines.append(f"Strategy: Optimal move followed (Held: {held_cards_str}, {rec_stat}).")
        if payout_multiplier == 0:
            explanation_lines.append(
                f"Diagnostic: Unfavorable draw variance. Discarded {discarded_str} and drew {drawn_cards_str}, "
                f"which resulted in {final_hand_name}. In draw poker, even the mathematically optimal hold has "
                f"variance; this was an unlucky miss, not a misplay."
            )
        else:
            explanation_lines.append(
                f"Diagnostic: Great result! The hold connected with drawn cards {drawn_cards_str} to complete {final_hand_name}."
            )
    else:
        metric_label = "win rate" if strategy != 'ev' else "EV"
        rec_held = [initial_cards_str[i] for i in recommended_hold_indices]
        explanation_lines.append(
            f"Strategy: Suboptimal play detected! Recommended holding {rec_held} ({rec_stat}), "
            f"but player held {held_cards_str}."
        )
        if payout_multiplier == 0:
            explanation_lines.append(
                f"Diagnostic: Player took a lower {metric_label} hold, discarded {discarded_str}, and drew {drawn_cards_str} "
                f"ending in {final_hand_name} (0x)."
            )
        else:
            explanation_lines.append(
                f"Diagnostic: Player drew {drawn_cards_str} to make {final_hand_name} ({payout_multiplier}x), "
                f"though mathematically another hold was higher {metric_label} long-term."
            )

    # Add High & Low post-mortem if played
    if high_low_steps:
        last_step = high_low_steps[-1]
        last_res = str(last_step.get('result', '')).upper()
        if 'LOSS' in last_res or 'BUST' in last_res or (final_coins is not None and final_coins == 0):
            open_c = last_step.get('open_card', '?')
            rec_c = last_step.get('recommendation', '?')
            user_c = last_step.get('user_choice', rec_c)
            drawn_c = last_step.get('drawn_card', '?')
            win_pct = last_step.get('win_prob', 0) * 100
            if user_c == rec_c:
                explanation_lines.append(
                    f"Phase 2 Double Up: Busted on Step {len(high_low_steps)} with open [{open_c}] and drawn [{drawn_c}]. "
                    f"Player followed optimal advice ({rec_c}); loss was due to draw variance ({100-win_pct:.1f}% underdog card). "
                    f"Final coins: 0."
                )
            else:
                explanation_lines.append(
                    f"Phase 2 Double Up: Busted on Step {len(high_low_steps)}. Player misplay: picked {user_c} "
                    f"when recommended move was {rec_c} ({win_pct:.1f}% win rate). Final coins: 0."
                )
        elif 'CASHOUT' in last_res or 'WIN' in last_res:
            explanation_lines.append(
                f"Phase 2 Double Up: Successfully doubled up across {len(high_low_steps)} step(s)! "
                f"Final collected coins: {final_coins or 'doubled pot'}."
            )

    return ' '.join(explanation_lines)
