"""
Game Logging System for Joker Poker & High-Low Assistant
Maintains synchronized structured JSONL (game_logs.jsonl) and human-readable (game_logs.txt) logs.
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional
from solver import card_to_display, card_from_str

LOGS_DIR = os.path.dirname(os.path.abspath(__file__))
JSONL_PATH = os.path.join(LOGS_DIR, 'game_logs.jsonl')
TXT_PATH = os.path.join(LOGS_DIR, 'game_logs.txt')


def _format_card_safe(c: Any) -> str:
    """Format a card string or ID to display symbol, handling errors gracefully."""
    if not c:
        return 'None'
    try:
        cid = card_from_str(str(c)) if isinstance(c, str) else int(c)
        return card_to_display(cid)
    except Exception:
        return str(c)


def render_txt_entry(r: Dict[str, Any]) -> str:
    """Render a single round record into human-readable text."""
    lines = [
        "=" * 80,
        f"ROUND #{r['round_id']}  |  {r.get('timestamp_display', r.get('timestamp', ''))}",
        "=" * 80
    ]

    init_hand = r.get('initial_hand', [])
    if init_hand:
        strat_key = r.get('strategy', 'win_rate')
        strat_display = "🎯 Max Win Rate (High & Low Qualifier)" if strat_key != 'ev' else "💰 Max Reward (EV)"
        init_display = ' '.join(f"[{_format_card_safe(c)}]" for c in init_hand)
        rec_hold = ', '.join(_format_card_safe(c) for c in r.get('recommended_hold', [])) or 'None (Discard All)'
        user_held = ', '.join(_format_card_safe(c) for c in r.get('user_held', [])) or 'None (Discard All)'
        drawn = ', '.join(_format_card_safe(c) for c in r.get('drawn_cards', [])) or 'None (Held All)'
        final_display = ' '.join(f"[{_format_card_safe(c)}]" for c in r.get('final_hand', []))

        lines.extend([
            "[PHASE 1: 5-CARD DRAW POKER]",
            f"  Strategy Mode:    {strat_display}",
            f"  Dealt:            {init_display}",
            f"  Recommended Hold: {rec_hold} (EV: {r.get('recommended_ev', 0.0):.2f}x | Win: {r.get('recommended_win_rate', 0.0)*100:.1f}%)",
            f"  Player Held:      {user_held}",
            f"  Drawn Cards:      {drawn}",
            f"  Final Hand:       {final_display} -> {r.get('final_hand_name', 'High Card')} (Payout: {r.get('payout_multiplier', 0)}x)",
            f"  Base Poker Coins: Bet {r.get('bet_coins', 50)} -> Earned {r.get('bet_coins', 50) * r.get('payout_multiplier', 0)} coins"
        ])

        top_holds = r.get('top_holds', [])
        if top_holds and len(top_holds) > 1:
            lines.append("  Top Alternative Holds:")
            for idx, alt in enumerate(top_holds[:3], 1):
                alt_held = ', '.join(_format_card_safe(c) for c in alt.get('held_cards', [])) or 'None (Discard All)'
                lines.append(f"    #{idx}: Hold [{alt_held}] -> EV: {alt.get('ev', 0):.2f}x | Win: {alt.get('win_rate', 0)*100:.1f}%")
    else:
        lines.append("[STANDALONE HIGH & LOW DOUBLE UP]")

    # Phase 2 High & Low
    hl_steps = r.get('high_low_steps', [])
    if hl_steps:
        lines.append("")
        lines.append("[PHASE 2: HIGH & LOW DOUBLE UP CHANCE]")
        for s in hl_steps:
            step_num = s.get('step', 1)
            open_c = s.get('open_card', '?')
            rec_c = s.get('recommendation', '?')
            user_c = s.get('user_choice', rec_c)
            drawn_c = s.get('drawn_card', '?')
            res = s.get('result', '?')
            win_pct = s.get('win_prob', 0) * 100
            risk = s.get('risk_level', 'NORMAL')
            pot_info = f" | Pot: {s['pot']} coins" if 'pot' in s else ""
            lines.append(
                f"  Step {step_num}: Open [{open_c}] | Recommended: {rec_c} ({win_pct:.1f}% chance - {risk}) "
                f"| Choice: {user_c} | Drew: [{drawn_c}] | Outcome: {res}{pot_info}"
            )
        
        last_step = hl_steps[-1]
        last_res = str(last_step.get('result', '')).upper()
        if 'LOSS' in last_res or 'BUST' in last_res:
            lines.append(f"  Double Up Result: BUSTED at Step {len(hl_steps)}. All coins lost!")
        elif 'CASHOUT' in last_res or 'WIN' in last_res:
            lines.append(f"  Double Up Result: Successfully completed/cashed out {r.get('earned_coins', 0)} coins!")
    elif init_hand:
        lines.append("")
        if r.get('payout_multiplier', 0) >= 4:
            lines.append("[PHASE 2: HIGH & LOW] Qualified (Two Pair or better), but player cashed out or skipped.")
        else:
            lines.append("[PHASE 2: HIGH & LOW] Did not qualify (Requires Two Pair or better).")

    lines.extend([
        "",
        f"FINAL SUMMARY:",
        f"  Total Coins Won:  {r.get('earned_coins', 0)} coins",
        f"  Overall Outcome:  {r.get('outcome', 'UNKNOWN')}",
        f"  Post-Mortem:      {r.get('diagnostic', '')}",
        "=" * 80 + "\n\n"
    ])
    return '\n'.join(lines)


def _rebuild_txt_file(records: List[Dict[str, Any]]):
    """Rebuild game_logs.txt from structured records."""
    try:
        with open(TXT_PATH, 'w', encoding='utf-8') as f:
            for rec in records:
                f.write(render_txt_entry(rec))
    except Exception as e:
        print(f"Error rebuilding {TXT_PATH}: {e}")


def log_round(round_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log or update a completed poker round (including any High & Low outcomes)
    to both game_logs.jsonl and game_logs.txt.
    """
    now = datetime.datetime.now()
    round_id = round_data.get('round_id') or now.strftime('%Y%m%d-%H%M%S-%f')[:20]
    timestamp_iso = round_data.get('timestamp') or now.isoformat()
    timestamp_display = round_data.get('timestamp_display') or now.strftime('%Y-%m-%d %H:%M:%S')

    payout = round_data.get('payout_multiplier', 0)
    bet = round_data.get('bet_coins', 50)
    base_earned = bet * payout
    hl_steps = round_data.get('high_low_steps', [])

    # Determine earned coins and outcome accurately
    if 'earned_coins' in round_data:
        earned = round_data['earned_coins']
    else:
        earned = base_earned

    # Check if busted in High & Low
    has_busted = False
    if hl_steps:
        last_step = hl_steps[-1]
        last_res = str(last_step.get('result', '')).upper()
        if 'LOSS' in last_res or 'BUST' in last_res:
            has_busted = True
            earned = 0

    if has_busted:
        outcome = 'LOSS (Busted in High & Low)'
    elif hl_steps and ('CASHOUT' in str(hl_steps[-1].get('result', '')).upper() or 'WIN' in str(hl_steps[-1].get('result', '')).upper()):
        outcome = f"WIN (Double Up: {earned} Coins)"
    elif earned > 0:
        outcome = f"WIN ({round_data.get('final_hand_name', 'Poker')} paying {payout}x)"
    else:
        outcome = 'LOSS'

    round_record = {
        'round_id': round_id,
        'strategy': round_data.get('strategy', 'win_rate'),
        'timestamp': timestamp_iso,
        'timestamp_display': timestamp_display,
        'initial_hand': round_data.get('initial_hand', []),
        'initial_display': [_format_card_safe(c) for c in round_data.get('initial_hand', [])],
        'recommended_hold': round_data.get('recommended_hold', []),
        'recommended_ev': round_data.get('recommended_ev', 0.0),
        'recommended_win_rate': round_data.get('recommended_win_rate', 0.0),
        'top_holds': round_data.get('top_holds', []),
        'user_held': round_data.get('user_held', []),
        'drawn_cards': round_data.get('drawn_cards', []),
        'final_hand': round_data.get('final_hand', []),
        'final_display': [_format_card_safe(c) for c in round_data.get('final_hand', [])],
        'final_hand_name': round_data.get('final_hand_name', 'High Card'),
        'payout_multiplier': payout,
        'bet_coins': bet,
        'earned_coins': earned,
        'outcome': outcome,
        'diagnostic': round_data.get('diagnostic', ''),
        'high_low_steps': hl_steps
    }

    # Load existing records to check for round_id update
    existing_records = []
    found_idx = -1
    if os.path.exists(JSONL_PATH):
        try:
            with open(JSONL_PATH, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    line = line.strip()
                    if line:
                        try:
                            rec = json.loads(line)
                            if rec.get('round_id') == round_id:
                                found_idx = len(existing_records)
                            existing_records.append(rec)
                        except Exception:
                            pass
        except Exception as e:
            print(f"Error reading {JSONL_PATH}: {e}")

    if found_idx >= 0:
        existing_records[found_idx] = round_record
    else:
        existing_records.append(round_record)

    # Rewrite JSONL file
    with open(JSONL_PATH, 'w', encoding='utf-8') as f:
        for rec in existing_records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    # Rebuild human-readable TXT file
    _rebuild_txt_file(existing_records)

    return round_record


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent log records from game_logs.jsonl (newest first)."""
    if not os.path.exists(JSONL_PATH):
        return []
    records = []
    try:
        with open(JSONL_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
    except Exception as e:
        print(f"Error reading {JSONL_PATH}: {e}")
    return records[::-1][:limit]


def get_raw_txt_logs(max_lines: int = 400) -> str:
    """Retrieve the tail of game_logs.txt for display in the viewer."""
    if not os.path.exists(TXT_PATH):
        return "No game logs recorded yet. Play a hand to generate logs!"
    try:
        with open(TXT_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return ''.join(lines[-max_lines:])
    except Exception as e:
        return f"Error reading logs: {e}"


def clear_logs() -> bool:
    """Clear both log files."""
    try:
        if os.path.exists(JSONL_PATH):
            os.remove(JSONL_PATH)
        if os.path.exists(TXT_PATH):
            os.remove(TXT_PATH)
        return True
    except Exception as e:
        print(f"Error clearing logs: {e}")
        return False
