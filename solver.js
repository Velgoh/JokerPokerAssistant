/**
 * Joker Poker & High-Low Solver (browser version)
 */

(function(window) {
    'use strict';

    const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
    const SUITS = ['H', 'D', 'C', 'S'];
    const SUIT_SYMBOLS = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'};
    const SUIT_NAMES = {'H': 'Hearts', 'D': 'Diamonds', 'C': 'Clubs', 'S': 'Spades'};

    const RANK_LOOKUP = {};
    RANKS.forEach((r, i) => RANK_LOOKUP[r] = i);
    RANK_LOOKUP['T'] = 8; // Support 'T' notation for 10

    const SUIT_LOOKUP = {};
    SUITS.forEach((s, i) => SUIT_LOOKUP[s] = i);

    const PAYOUT_TABLE = {
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
        'High Card': 0
    };

    // Precompute straight masks
    const STRAIGHT_MASKS = new Set();
    for (let i = 0; i < 9; i++) {
        STRAIGHT_MASKS.add(0b11111 << i);
    }
    STRAIGHT_MASKS.add((1 << 12) | 0b1111); // Wheel A-2-3-4-5

    const ROYAL_MASK = (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11) | (1 << 12);

    const STRAIGHT_4_MASKS = new Set();
    STRAIGHT_MASKS.forEach(sm => {
        for (let b = 0; b < 13; b++) {
            if (sm & (1 << b)) {
                STRAIGHT_4_MASKS.add(sm ^ (1 << b));
            }
        }
    });

    const ROYAL_4_MASKS = new Set();
    for (let b = 8; b <= 12; b++) {
        ROYAL_4_MASKS.add(ROYAL_MASK ^ (1 << b));
    }

    function cardFromStr(cardStr) {
        if (!cardStr) throw new Error('Empty card string.');
        let s = cardStr.trim().toUpperCase();
        if (s === 'JK' || s === 'JOKER' || s === 'WILD' || s === 'JOKER1') return 52;

        s = s.replace('♥', 'H').replace('♦', 'D').replace('♣', 'C').replace('♠', 'S');
        const suitPart = s.slice(-1);
        let rankPart = s.slice(0, -1);
        if (rankPart === 'T') rankPart = '10';

        if (!(suitPart in SUIT_LOOKUP) || !(rankPart in RANK_LOOKUP)) {
            throw new Error(`Invalid card format: ${cardStr}`);
        }
        return (RANK_LOOKUP[rankPart] << 2) | SUIT_LOOKUP[suitPart];
    }

    function cardToStr(cardId) {
        if (cardId === 52) return 'JK';
        const rank = cardId >> 2;
        const suit = cardId & 3;
        return `${RANKS[rank]}${SUITS[suit]}`;
    }

    function cardToDisplay(cardId) {
        if (cardId === 52) return '🃏 Joker';
        const rank = cardId >> 2;
        const suit = cardId & 3;
        return `${RANKS[rank]}${SUIT_SYMBOLS[SUITS[suit]]}`;
    }

    function countBits(n) {
        let count = 0;
        while (n > 0) {
            count += n & 1;
            n >>= 1;
        }
        return count;
    }

    function eval5Cards(cards) {
        const c = cards.slice().sort((a, b) => a - b);

        // Case 1: Joker is present
        if (c[4] === 52) {
            const c1 = c[0], c2 = c[1], c3 = c[2], c4 = c[3];
            const r1 = c1 >> 2, s1 = c1 & 3;
            const r2 = c2 >> 2, s2 = c2 & 3;
            const r3 = c3 >> 2, s3 = c3 & 3;
            const r4 = c4 >> 2, s4 = c4 & 3;

            const mask = (1 << r1) | (1 << r2) | (1 << r3) | (1 << r4);
            const nd = countBits(mask);

            if (nd === 4) {
                const isFlush4 = (s1 === s2 && s2 === s3 && s3 === s4);
                if (isFlush4) {
                    if (ROYAL_4_MASKS.has(mask)) return [200, 'Royal Flush'];
                    if (STRAIGHT_4_MASKS.has(mask)) return [60, 'Straight Flush'];
                    return [14, 'Flush'];
                }
                if (STRAIGHT_4_MASKS.has(mask)) return [8, 'Straight'];
                return [0, 'One Pair'];
            }
            if (nd === 3) return [4, 'Trips'];
            if (nd === 2) {
                const cnt1 = (r1 === r1 ? 1 : 0) + (r2 === r1 ? 1 : 0) + (r3 === r1 ? 1 : 0) + (r4 === r1 ? 1 : 0);
                if (cnt1 === 1 || cnt1 === 3) return [30, 'Quads'];
                return [16, 'Full House'];
            }
            return [140, 'Five of a Kind'];
        }

        // Case 2: No Joker
        const c1 = c[0], c2 = c[1], c3 = c[2], c4 = c[3], c5 = c[4];
        const r1 = c1 >> 2, s1 = c1 & 3;
        const r2 = c2 >> 2, s2 = c2 & 3;
        const r3 = c3 >> 2, s3 = c3 & 3;
        const r4 = c4 >> 2, s4 = c4 & 3;
        const r5 = c5 >> 2, s5 = c5 & 3;

        const mask = (1 << r1) | (1 << r2) | (1 << r3) | (1 << r4) | (1 << r5);
        const nd = countBits(mask);

        if (nd === 5) {
            const isFlush = (s1 === s2 && s2 === s3 && s3 === s4 && s4 === s5);
            const isStraight = STRAIGHT_MASKS.has(mask);
            if (isFlush && isStraight) {
                if (mask === ROYAL_MASK) return [200, 'Royal Flush'];
                return [60, 'Straight Flush'];
            }
            if (isFlush) return [14, 'Flush'];
            if (isStraight) return [8, 'Straight'];
            return [0, 'High Card'];
        }

        if (nd === 4) return [0, 'One Pair'];

        if (nd === 3) {
            const cnt1 = (r1 === r1 ? 1 : 0) + (r2 === r1 ? 1 : 0) + (r3 === r1 ? 1 : 0) + (r4 === r1 ? 1 : 0) + (r5 === r1 ? 1 : 0);
            const cnt2 = (r1 === r2 ? 1 : 0) + (r2 === r2 ? 1 : 0) + (r3 === r2 ? 1 : 0) + (r4 === r2 ? 1 : 0) + (r5 === r2 ? 1 : 0);
            const cnt3 = (r1 === r3 ? 1 : 0) + (r2 === r3 ? 1 : 0) + (r3 === r3 ? 1 : 0) + (r4 === r3 ? 1 : 0) + (r5 === r3 ? 1 : 0);
            if (cnt1 === 3 || cnt2 === 3 || cnt3 === 3) return [4, 'Trips'];
            return [4, 'Two Pair'];
        }

        if (nd === 2) {
            const cnt1 = (r1 === r1 ? 1 : 0) + (r2 === r1 ? 1 : 0) + (r3 === r1 ? 1 : 0) + (r4 === r1 ? 1 : 0) + (r5 === r1 ? 1 : 0);
            if (cnt1 === 1 || cnt1 === 4) return [30, 'Quads'];
            return [16, 'Full House'];
        }

        return [0, 'High Card'];
    }

    function combinations(arr, k) {
        const results = [];
        function helper(start, combo) {
            if (combo.length === k) {
                results.push(combo.slice());
                return;
            }
            for (let i = start; i < arr.length; i++) {
                combo.push(arr[i]);
                helper(i + 1, combo);
                combo.pop();
            }
        }
        helper(0, []);
        return results;
    }

    function analyzeAllHolds(initialCards, strategy = 'win_rate') {
        if (initialCards.length !== 5) {
            throw new Error('Must provide exactly 5 cards.');
        }

        const initialSet = new Set(initialCards);
        const deck = [];
        for (let i = 0; i < 53; i++) {
            if (!initialSet.has(i)) deck.push(i);
        }

        const HAND_TYPES = [
            'Royal Flush', 'Five of a Kind', 'Straight Flush', 'Quads',
            'Full House', 'Flush', 'Straight', 'Trips', 'Two Pair',
            'One Pair', 'High Card'
        ];

        const allHolds = [];
        const deckLen = deck.length;

        for (let holdCount = 5; holdCount >= 0; holdCount--) {
            const holdIndicesList = combinations([0, 1, 2, 3, 4], holdCount);
            for (let h = 0; h < holdIndicesList.length; h++) {
                const holdIndices = holdIndicesList[h];
                const held = holdIndices.map(idx => initialCards[idx]);
                const nDraw = 5 - holdCount;

                let payoutSum = 0;
                let nCombos = 0;
                const handCounts = {};
                HAND_TYPES.forEach(ht => handCounts[ht] = 0);

                if (nDraw === 0) {
                    const [payout, hname] = eval5Cards(held);
                    payoutSum = payout;
                    nCombos = 1;
                    handCounts[hname] = 1;
                } else if (nDraw === 1) {
                    const h0 = held[0], h1 = held[1], h2 = held[2], h3 = held[3];
                    for (let i = 0; i < deckLen; i++) {
                        nCombos++;
                        const [payout, hname] = eval5Cards([h0, h1, h2, h3, deck[i]]);
                        payoutSum += payout;
                        handCounts[hname]++;
                    }
                } else if (nDraw === 2) {
                    const h0 = held[0], h1 = held[1], h2 = held[2];
                    for (let i = 0; i < deckLen; i++) {
                        const d0 = deck[i];
                        for (let j = i + 1; j < deckLen; j++) {
                            nCombos++;
                            const [payout, hname] = eval5Cards([h0, h1, h2, d0, deck[j]]);
                            payoutSum += payout;
                            handCounts[hname]++;
                        }
                    }
                } else if (nDraw === 3) {
                    const h0 = held[0], h1 = held[1];
                    for (let i = 0; i < deckLen; i++) {
                        const d0 = deck[i];
                        for (let j = i + 1; j < deckLen; j++) {
                            const d1 = deck[j];
                            for (let k = j + 1; k < deckLen; k++) {
                                nCombos++;
                                const [payout, hname] = eval5Cards([h0, h1, d0, d1, deck[k]]);
                                payoutSum += payout;
                                handCounts[hname]++;
                            }
                        }
                    }
                } else if (nDraw === 4) {
                    const h0 = held[0];
                    for (let i = 0; i < deckLen; i++) {
                        const d0 = deck[i];
                        for (let j = i + 1; j < deckLen; j++) {
                            const d1 = deck[j];
                            for (let k = j + 1; k < deckLen; k++) {
                                const d2 = deck[k];
                                for (let l = k + 1; l < deckLen; l++) {
                                    nCombos++;
                                    const [payout, hname] = eval5Cards([h0, d0, d1, d2, deck[l]]);
                                    payoutSum += payout;
                                    handCounts[hname]++;
                                }
                            }
                        }
                    }
                } else if (nDraw === 5) {
                    // Hold 0: 48 choose 5 = 1,712,304 combos evaluated directly without memory allocation
                    for (let i = 0; i < deckLen; i++) {
                        const d0 = deck[i];
                        for (let j = i + 1; j < deckLen; j++) {
                            const d1 = deck[j];
                            for (let k = j + 1; k < deckLen; k++) {
                                const d2 = deck[k];
                                for (let l = k + 1; l < deckLen; l++) {
                                    const d3 = deck[l];
                                    for (let m = l + 1; m < deckLen; m++) {
                                        nCombos++;
                                        const [payout, hname] = eval5Cards([d0, d1, d2, d3, deck[m]]);
                                        payoutSum += payout;
                                        handCounts[hname]++;
                                    }
                                }
                            }
                        }
                    }
                }

                const ev = payoutSum / nCombos;
                let payingCombos = 0;
                HAND_TYPES.forEach(ht => {
                    if (PAYOUT_TABLE[ht] > 0) payingCombos += handCounts[ht];
                });
                const winRate = payingCombos / nCombos;

                const discardIndices = [0, 1, 2, 3, 4].filter(i => !holdIndices.includes(i));

                allHolds.push({
                    hold_indices: holdIndices,
                    discard_indices: discardIndices,
                    held_cards: held.map(cardToStr),
                    held_display: held.map(cardToDisplay),
                    discarded_cards: discardIndices.map(i => cardToStr(initialCards[i])),
                    discarded_display: discardIndices.map(i => cardToDisplay(initialCards[i])),
                    ev: Math.round(ev * 10000) / 10000,
                    win_rate: Math.round(winRate * 10000) / 10000,
                    total_combos: nCombos,
                    distribution: handCounts
                });
            }
        }

        const strat = (strategy || 'win_rate').toString().trim().toLowerCase();
        const isEv = (strat === 'ev' || strat === 'reward' || strat === 'max_reward');

        if (isEv) {
            allHolds.sort((a, b) => b.ev - a.ev || b.win_rate - a.win_rate);
        } else {
            allHolds.sort((a, b) => b.win_rate - a.win_rate || b.ev - a.ev);
        }
        const bestHold = allHolds[0];
        const [currentPayout, currentHandName] = eval5Cards(initialCards);

        return {
            initial_hand: initialCards.map(cardToStr),
            initial_display: initialCards.map(cardToDisplay),
            current_hand_name: currentHandName,
            current_payout: currentPayout,
            best_hold: bestHold,
            all_holds: allHolds,
            strategy: isEv ? 'ev' : 'win_rate'
        };
    }

    function evaluateHighLow(openCardStr) {
        let s = openCardStr.trim().toUpperCase();
        s = s.replace('♥', '').replace('♦', '').replace('♣', '').replace('♠', '')
             .replace('H', '').replace('D', '').replace('C', '').replace('S', '');

        if (s === 'T') s = '10';

        if (!(s in RANK_LOOKUP)) {
            throw new Error(`Invalid rank '${openCardStr}'.`);
        }

        const rankIdx = RANK_LOOKUP[s];
        const numHigherCards = (12 - rankIdx) * 4;
        const numLowerCards = rankIdx * 4;
        const numTieCards = 3;
        const totalRemaining = 51;

        const rawHigherProb = numHigherCards / totalRemaining;
        const rawLowerProb = numLowerCards / totalRemaining;
        const rawTieProb = numTieCards / totalRemaining;

        const decisiveTotal = numHigherCards + numLowerCards;
        const effHigherWinRate = decisiveTotal > 0 ? numHigherCards / decisiveTotal : 0.5;
        const effLowerWinRate = decisiveTotal > 0 ? numLowerCards / decisiveTotal : 0.5;

        let recommendation = 'NEUTRAL';
        let bestWinRate = 0.5;

        if (effHigherWinRate > effLowerWinRate) {
            recommendation = 'HIGHER';
            bestWinRate = effHigherWinRate;
        } else if (effLowerWinRate > effHigherWinRate) {
            recommendation = 'LOWER';
            bestWinRate = effLowerWinRate;
        }

        let riskLevel = 'EXTREME RISK (COIN TOSS)';
        let riskColor = '#ef4444';
        let advice = '50/50 Coin Flip! Exactly equal chance of Higher or Lower. High danger of losing accumulated coins.';

        if (bestWinRate === 1.0) {
            riskLevel = 'ZERO RISK';
            riskColor = '#10b981';
            advice = `100% Guaranteed Win! Pick ${recommendation}. No chance of losing.`;
        } else if (bestWinRate >= 0.90) {
            riskLevel = 'VERY LOW RISK';
            riskColor = '#10b981';
            advice = `Extremely Safe (${(bestWinRate * 100).toFixed(1)}% Win Chance). Strongly recommend ${recommendation}.`;
        } else if (bestWinRate >= 0.75) {
            riskLevel = 'LOW RISK';
            riskColor = '#3b82f6';
            advice = `Favorable Odds (${(bestWinRate * 100).toFixed(1)}% Win Chance). Pick ${recommendation}.`;
        } else if (bestWinRate >= 0.65) {
            riskLevel = 'MODERATE RISK';
            riskColor = '#f59e0b';
            advice = `Moderate Edge (${(bestWinRate * 100).toFixed(1)}% Win Chance). Pick ${recommendation}.`;
        } else if (bestWinRate > 0.50) {
            riskLevel = 'HIGH RISK';
            riskColor = '#f97316';
            advice = `Slight Edge (${(bestWinRate * 100).toFixed(1)}% Win Chance). Caution: 41.7% chance to lose all coins!`;
        }

        return {
            open_card_rank: s,
            recommendation: recommendation,
            best_win_rate: Math.round(bestWinRate * 10000) / 10000,
            eff_higher_win_rate: Math.round(effHigherWinRate * 10000) / 10000,
            eff_lower_win_rate: Math.round(effLowerWinRate * 10000) / 10000,
            raw_higher_prob: Math.round(rawHigherProb * 10000) / 10000,
            raw_lower_prob: Math.round(rawLowerProb * 10000) / 10000,
            raw_tie_prob: Math.round(rawTieProb * 10000) / 10000,
            higher_cards_count: numHigherCards,
            lower_cards_count: numLowerCards,
            tie_cards_count: numTieCards,
            risk_level: riskLevel,
            risk_color: riskColor,
            advice: advice
        };
    }

    function generateRoundExplanation(params) {
        const {
            initial_cards_str = [],
            recommended_hold_indices = [],
            recommended_ev = 0.0,
            user_held_indices = [],
            drawn_cards_str = [],
            final_cards_str = [],
            final_hand_name = 'High Card',
            payout_multiplier = 0,
            high_low_steps = [],
            final_coins = null,
            strategy = 'win_rate',
            recommended_win_rate = null
        } = params;

        const explanationLines = [];

        // Standalone High & Low session
        if ((!initial_cards_str || initial_cards_str.length === 0) && high_low_steps && high_low_steps.length > 0) {
            explanationLines.push("[Standalone High & Low Session]");
            const lastStep = high_low_steps[high_low_steps.length - 1];
            const lastRes = String(lastStep.result || '').toUpperCase();
            if (lastRes.includes('LOSS') || lastRes.includes('BUST')) {
                const openC = lastStep.open_card || '?';
                const recC = lastStep.recommendation || '?';
                const userC = lastStep.user_choice || recC;
                const drawnC = lastStep.drawn_card || '?';
                const winPct = (lastStep.win_prob || 0) * 100;
                if (userC === recC) {
                    explanationLines.push(
                        `Outcome: BUSTED on Step ${high_low_steps.length} (0 coins). Diagnostic: Followed optimal advice (${recC}), ` +
                        `but drew ${drawnC} against open card ${openC}. Unfavorable draw variance (${(100 - winPct).toFixed(1)}% underdog card).`
                    );
                } else {
                    explanationLines.push(
                        `Outcome: BUSTED on Step ${high_low_steps.length} (0 coins). Diagnostic: Player misplay. Picked ${userC} ` +
                        `when recommended move was ${recC} (${winPct.toFixed(1)}% win rate).`
                    );
                }
            } else {
                explanationLines.push(
                    `Outcome: CASHED OUT / WON (${final_coins !== null ? final_coins : 'positive'} coins across ${high_low_steps.length} steps). ` +
                    `Diagnostic: Successfully navigated High & Low Double Up!`
                );
            }
            return explanationLines.join(' ');
        }

        const sortedRec = recommended_hold_indices.slice().sort((a, b) => a - b);
        const sortedUser = user_held_indices.slice().sort((a, b) => a - b);
        const isOptimalPlay = (sortedRec.length === sortedUser.length && sortedRec.every((v, i) => v === sortedUser[i]));
        const heldCardsStr = user_held_indices.map(i => initial_cards_str[i]);
        const discardedStr = initial_cards_str.filter((_, i) => !user_held_indices.includes(i));

        const outcomeType = (payout_multiplier > 0)
            ? `WIN (${final_hand_name} paying ${payout_multiplier}x)`
            : `LOSS (${final_hand_name} paying 0x)`;

        explanationLines.push(`Phase 1 Outcome: ${outcomeType}.`);

        let recStat;
        if (recommended_win_rate !== null && recommended_win_rate !== undefined) {
            recStat = (strategy !== 'ev')
                ? `Win: ${(recommended_win_rate * 100).toFixed(1)}% | EV: ${recommended_ev.toFixed(2)}x`
                : `EV: ${recommended_ev.toFixed(2)}x | Win: ${(recommended_win_rate * 100).toFixed(1)}%`;
        } else {
            recStat = `EV: ${recommended_ev.toFixed(2)}x`;
        }

        if (isOptimalPlay) {
            explanationLines.push(`Strategy: Optimal move followed (Held: [${heldCardsStr.join(', ')}], ${recStat}).`);
            if (payout_multiplier === 0) {
                explanationLines.push(
                    `Diagnostic: Unfavorable draw variance. Discarded [${discardedStr.join(', ')}] and drew [${drawn_cards_str.join(', ')}], ` +
                    `which resulted in ${final_hand_name}. In draw poker, even the mathematically optimal hold has ` +
                    `variance; this was an unlucky miss, not a misplay.`
                );
            } else {
                explanationLines.push(
                    `Diagnostic: Great result! The hold connected with drawn cards [${drawn_cards_str.join(', ')}] to complete ${final_hand_name}.`
                );
            }
        } else {
            const metricLabel = (strategy !== 'ev') ? 'win rate' : 'EV';
            const recHeld = recommended_hold_indices.map(i => initial_cards_str[i]);
            explanationLines.push(
                `Strategy: Suboptimal play detected! Recommended holding [${recHeld.join(', ')}] (${recStat}), ` +
                `but player held [${heldCardsStr.join(', ')}].`
            );
            if (payout_multiplier === 0) {
                explanationLines.push(
                    `Diagnostic: Player took a lower ${metricLabel} hold, discarded [${discardedStr.join(', ')}], and drew [${drawn_cards_str.join(', ')}] ` +
                    `ending in ${final_hand_name} (0x).`
                );
            } else {
                explanationLines.push(
                    `Diagnostic: Player drew [${drawn_cards_str.join(', ')}] to make ${final_hand_name} (${payout_multiplier}x), ` +
                    `though mathematically another hold was higher ${metricLabel} long-term.`
                );
            }
        }

        // Add High & Low post-mortem if played
        if (high_low_steps && high_low_steps.length > 0) {
            const lastStep = high_low_steps[high_low_steps.length - 1];
            const lastRes = String(lastStep.result || '').toUpperCase();
            if (lastRes.includes('LOSS') || lastRes.includes('BUST') || (final_coins !== null && final_coins === 0)) {
                const openC = lastStep.open_card || '?';
                const recC = lastStep.recommendation || '?';
                const userC = lastStep.user_choice || recC;
                const drawnC = lastStep.drawn_card || '?';
                const winPct = (lastStep.win_prob || 0) * 100;
                if (userC === recC) {
                    explanationLines.push(
                        `Phase 2 Double Up: Busted on Step ${high_low_steps.length} with open [${openC}] and drawn [${drawnC}]. ` +
                        `Player followed optimal advice (${recC}); loss was due to draw variance (${(100 - winPct).toFixed(1)}% underdog card). ` +
                        `Final coins: 0.`
                    );
                } else {
                    explanationLines.push(
                        `Phase 2 Double Up: Busted on Step ${high_low_steps.length}. Player misplay: picked ${userC} ` +
                        `when recommended move was ${recC} (${winPct.toFixed(1)}% win rate). Final coins: 0.`
                    );
                }
            } else if (lastRes.includes('CASHOUT') || lastRes.includes('WIN')) {
                explanationLines.push(
                    `Phase 2 Double Up: Successfully doubled up across ${high_low_steps.length} step(s)! ` +
                    `Final collected coins: ${final_coins !== null ? final_coins : 'doubled pot'}.`
                );
            }
        }

        return explanationLines.join(' ');
    }

    // Export to window
    window.PokerSolver = {
        RANKS,
        SUITS,
        SUIT_SYMBOLS,
        PAYOUT_TABLE,
        cardFromStr,
        cardToStr,
        cardToDisplay,
        eval5Cards,
        analyzeAllHolds,
        evaluateHighLow,
        generateRoundExplanation
    };

})(typeof window !== 'undefined' ? window : this);
