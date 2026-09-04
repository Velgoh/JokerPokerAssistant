/**
 * Joker Poker & High-Low Assistant UI controller.
 * Connects to the local server or runs in-browser calculations.
 */

(function() {
    'use strict';

    // Application State
    const state = {
        serverOnline: false,
        strategy: (() => {
            try {
                return localStorage.getItem('poker_assistant_strategy') || localStorage.getItem('hololive_poker_strategy') || 'win_rate';
            } catch (e) {
                return 'win_rate';
            }
        })(), // Default strategy: 'win_rate' (High & Low Qualifier) vs 'ev' (Max Reward)
        hand: [null, null, null, null, null], // 5 card strings, e.g. '10H'
        currentAnalysis: null,
        userHoldOverrides: null, // Set of indices user manually held
        drawReplacements: [], // cards drawn
        activeDrawSlotIdx: null, // Currently selected draw slot for assignment
        lastCompletedRound: null,
        highLow: {
            roundId: null,
            openCard: null,
            currentAnalysis: null,
            currentPot: 50,
            initialPot: 50,
            baseHandName: 'Direct Play',
            streak: 0,
            history: [],
            isFinished: false
        }
    };

    // Constants
    const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
    const SUITS = ['H', 'D', 'C', 'S'];
    const SUIT_SYMBOLS = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'};
    const RANK_INDEX = {};
    RANKS.forEach((r, i) => RANK_INDEX[r] = i);
    RANK_INDEX['T'] = 8;

    // DOM Elements
    const elements = {
        serverStatusBadge: document.getElementById('serverStatusBadge'),
        statusText: document.getElementById('statusText'),
        stratWinRateBtn: document.getElementById('stratWinRateBtn'),
        stratEvBtn: document.getElementById('stratEvBtn'),
        handSlots: document.getElementById('handSlots'),
        handInstruction: document.getElementById('handInstruction'),
        clearHandBtn: document.getElementById('clearHandBtn'),
        randomHandBtn: document.getElementById('randomHandBtn'),
        presetSelect: document.getElementById('presetSelect'),
        jokerBtn: document.getElementById('jokerBtn'),
        analysisSection: document.getElementById('analysisSection'),
        recBadge: document.getElementById('recBadge'),
        recActionText: document.getElementById('recActionText'),
        recDiscardText: document.getElementById('recDiscardText'),
        recEvVal: document.getElementById('recEvVal'),
        recWinRateVal: document.getElementById('recWinRateVal'),
        currentHandNameVal: document.getElementById('currentHandNameVal'),
        currentHandPayoutVal: document.getElementById('currentHandPayoutVal'),
        distChips: document.getElementById('distChips'),
        holdsTableBody: document.getElementById('holdsTableBody'),
        toggleAllHoldsBtn: document.getElementById('toggleAllHoldsBtn'),
        drawInstructions: document.getElementById('drawInstructions'),
        drawInputsContainer: document.getElementById('drawInputsContainer'),
        autoFillDrawBtn: document.getElementById('autoFillDrawBtn'),
        finishRoundBtn: document.getElementById('finishRoundBtn'),
        roundResultBanner: document.getElementById('roundResultBanner'),
        roundResultTitle: document.getElementById('roundResultTitle'),
        roundResultDesc: document.getElementById('roundResultDesc'),
        goToHighLowBtn: document.getElementById('goToHighLowBtn'),
        // Phase 2
        hlRanksGrid: document.getElementById('hlRanksGrid'),
        hlDrawnGrid: document.getElementById('hlDrawnGrid'),
        hlAdviceCard: document.getElementById('hlAdviceCard'),
        hlDirection: document.getElementById('hlDirection'),
        hlProbBadge: document.getElementById('hlProbBadge'),
        hlRiskBadge: document.getElementById('hlRiskBadge'),
        hlAdviceText: document.getElementById('hlAdviceText'),
        higherBar: document.getElementById('higherBar'),
        lowerBar: document.getElementById('lowerBar'),
        redrawBar: document.getElementById('redrawBar'),
        higherPct: document.getElementById('higherPct'),
        lowerPct: document.getElementById('lowerPct'),
        redrawPct: document.getElementById('redrawPct'),
        hlRoundCount: document.getElementById('hlRoundCount'),
        hlPotDisplay: document.getElementById('hlPotDisplay'),
        hlHistoryList: document.getElementById('hlHistoryList'),
        hlWinBtn: document.getElementById('hlWinBtn'),
        hlRedrawBtn: document.getElementById('hlRedrawBtn'),
        hlLoseBtn: document.getElementById('hlLoseBtn'),
        hlCashoutBtn: document.getElementById('hlCashoutBtn'),
        // Logs
        historyList: document.getElementById('historyList'),
        rawLogViewer: document.getElementById('rawLogViewer'),
        cardsLogView: document.getElementById('cardsLogView'),
        rawTxtLogView: document.getElementById('rawTxtLogView'),
        refreshLogsBtn: document.getElementById('refreshLogsBtn'),
        clearLogsBtn: document.getElementById('clearLogsBtn'),
        // Toast
        toastNotification: document.getElementById('toastNotification')
    };

    // -------------------------------------------------------------
    // Toast Notifications
    // -------------------------------------------------------------
    let toastTimeout = null;
    function showToast(message, type = 'info', duration = 3200) {
        if (!elements.toastNotification) return;
        clearTimeout(toastTimeout);
        elements.toastNotification.className = `toast-notification ${type}`;
        elements.toastNotification.textContent = message;
        elements.toastNotification.classList.remove('hidden');
        toastTimeout = setTimeout(() => {
            elements.toastNotification.classList.add('hidden');
        }, duration);
    }

    // -------------------------------------------------------------
    // Initialize Application
    // -------------------------------------------------------------
    async function init() {
        initTabs();
        buildCardMatrix();
        buildHandSlots();
        buildHighLowRanks();
        buildHighLowDrawnRanks();
        bindEvents();
        await checkServerHealth();
        loadRecentLogs();
    }

    // -------------------------------------------------------------
    // Health / Server Connectivity
    // -------------------------------------------------------------
    async function checkServerHealth() {
        try {
            const resp = await fetch('/api/health');
            if (resp.ok) {
                const data = await resp.json();
                if (data.status === 'ok') {
                    state.serverOnline = true;
                    elements.serverStatusBadge.innerHTML = '<span class="status-dot online"></span><span class="status-text">Server Online</span>';
                    return;
                }
            }
        } catch (e) {
            // Offline fallback
        }
        state.serverOnline = false;
        elements.serverStatusBadge.innerHTML = '<span class="status-dot offline"></span><span class="status-text">Standalone Mode</span>';
    }

    // -------------------------------------------------------------
    // Tab Navigation
    // -------------------------------------------------------------
    function initTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const targetTab = btn.getAttribute('data-tab');
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                const targetPane = document.getElementById(targetTab);
                if (targetPane) targetPane.classList.add('active');

                if (targetTab === 'logs') loadRecentLogs();
            });
        });

        // Logs sub-tabs
        const logTabBtns = document.querySelectorAll('.log-tab-btn');
        logTabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                logTabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const tabName = btn.getAttribute('data-logtab');
                if (tabName === 'cardsView') {
                    elements.cardsLogView.classList.add('active');
                    elements.rawTxtLogView.classList.add('hidden');
                } else {
                    elements.cardsLogView.classList.remove('active');
                    elements.rawTxtLogView.classList.remove('hidden');
                    loadRawTextLog();
                }
            });
        });
    }

    // -------------------------------------------------------------
    // Card Matrix & Slots Construction
    // -------------------------------------------------------------
    function buildCardMatrix() {
        SUITS.forEach(suit => {
            const container = document.querySelector(`.matrix-cards[data-suit="${suit}"]`);
            if (!container) return;
            container.innerHTML = '';
            RANKS.forEach(rank => {
                const cardStr = `${rank}${suit}`;
                const btn = document.createElement('button');
                btn.className = 'selector-card';
                btn.setAttribute('data-card', cardStr);
                btn.textContent = rank;
                btn.addEventListener('click', () => onMatrixCardClick(cardStr));
                container.appendChild(btn);
            });
        });
    }

    function buildHandSlots() {
        elements.handSlots.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            const slot = document.createElement('div');
            slot.className = 'card-slot empty';
            slot.setAttribute('data-slot-index', i);
            slot.innerHTML = '<span style="opacity: 0.3; font-size: 1.2rem;">+</span>';
            slot.addEventListener('click', () => onSlotClick(i));
            elements.handSlots.appendChild(slot);
        }
    }

    function buildHighLowRanks() {
        elements.hlRanksGrid.innerHTML = '';
        RANKS.forEach(rank => {
            const btn = document.createElement('button');
            btn.className = 'hl-rank-btn';
            btn.textContent = rank;
            btn.setAttribute('data-rank', rank);
            btn.addEventListener('click', () => selectHighLowOpenCard(rank));
            elements.hlRanksGrid.appendChild(btn);
        });
    }

    function buildHighLowDrawnRanks() {
        if (!elements.hlDrawnGrid) return;
        elements.hlDrawnGrid.innerHTML = '';
        RANKS.forEach(rank => {
            const btn = document.createElement('button');
            btn.className = 'hl-drawn-btn';
            btn.textContent = rank;
            btn.setAttribute('data-drawn-rank', rank);
            btn.addEventListener('click', () => handleHighLowDrawnRank(rank));
            elements.hlDrawnGrid.appendChild(btn);
        });
    }

    // -------------------------------------------------------------
    // Hand Selection Interactions
    // -------------------------------------------------------------
    function onMatrixCardClick(cardStr) {
        // Mode 1: Assigning replacement card to an active draw slot
        if (state.activeDrawSlotIdx !== null) {
            const inHand = state.hand.includes(cardStr);
            const inDraw = state.drawReplacements.includes(cardStr);
            if (inHand || inDraw) {
                showToast(`Card ${cardStr} is already in use!`, 'danger');
                return;
            }

            state.drawReplacements[state.activeDrawSlotIdx] = cardStr;
            renderDrawInputs();
            updateMatrixDisabledStates();

            // Advance to next unfilled draw slot
            const nextEmpty = state.drawReplacements.indexOf(null);
            if (nextEmpty !== -1) {
                setActiveDrawSlot(nextEmpty);
            } else {
                state.activeDrawSlotIdx = null;
                if (elements.drawInstructions) {
                    elements.drawInstructions.textContent = 'All replacement cards chosen! Click "Complete Round" to log result.';
                }
            }
            return;
        }

        // Mode 2: Normal Hand Selection
        const existingIdx = state.hand.indexOf(cardStr);
        if (existingIdx !== -1) {
            state.hand[existingIdx] = null;
        } else {
            const firstEmpty = state.hand.indexOf(null);
            if (firstEmpty !== -1) {
                state.hand[firstEmpty] = cardStr;
            } else {
                showToast('All 5 slots filled! Tap a slot to remove or clear.', 'info');
            }
        }
        state.userHoldOverrides = null;
        renderHandSlots();
        updateMatrixDisabledStates();
        checkAndEvaluateHand();
    }

    function onSlotClick(slotIndex) {
        if (state.currentAnalysis) {
            if (!state.userHoldOverrides) {
                state.userHoldOverrides = new Set(state.currentAnalysis.best_hold.hold_indices);
            }
            if (state.userHoldOverrides.has(slotIndex)) {
                state.userHoldOverrides.delete(slotIndex);
            } else {
                state.userHoldOverrides.add(slotIndex);
            }
            renderHandSlots();
            renderDrawInputs();
            return;
        }

        if (state.hand[slotIndex]) {
            state.hand[slotIndex] = null;
            state.userHoldOverrides = null;
            renderHandSlots();
            updateMatrixDisabledStates();
            checkAndEvaluateHand();
        }
    }

    function renderHandSlots() {
        const slots = elements.handSlots.children;
        const isAnalyzed = !!state.currentAnalysis;
        const holdIndices = state.userHoldOverrides || (isAnalyzed ? new Set(state.currentAnalysis.best_hold.hold_indices) : null);

        for (let i = 0; i < 5; i++) {
            const slot = slots[i];
            const cardStr = state.hand[i];

            slot.className = 'card-slot';
            slot.innerHTML = '';

            if (!cardStr) {
                slot.classList.add('empty');
                slot.innerHTML = '<span style="opacity: 0.3; font-size: 1.2rem;">+</span>';
                continue;
            }

            slot.classList.add('filled');

            if (cardStr === 'JK') {
                slot.classList.add('is-joker');
                slot.innerHTML = `
                    <span class="joker-art">🃏</span>
                    <span class="joker-text">JOKER</span>
                `;
            } else {
                const suit = cardStr.slice(-1);
                const rank = cardStr.slice(0, -1);
                const isRed = (suit === 'H' || suit === 'D');
                slot.classList.add(isRed ? 'is-red' : 'is-black');
                slot.innerHTML = `
                    <span class="card-rank">${rank}</span>
                    <span class="card-suit">${SUIT_SYMBOLS[suit] || suit}</span>
                `;
            }

            if (isAnalyzed && holdIndices) {
                const isHeld = holdIndices.has(i);
                if (isHeld) {
                    slot.classList.add('hold-active');
                    const badge = document.createElement('span');
                    badge.className = 'hold-badge';
                    badge.textContent = 'HOLD';
                    slot.appendChild(badge);
                } else {
                    slot.classList.add('discard-active');
                    const badge = document.createElement('span');
                    badge.className = 'hold-badge';
                    badge.textContent = 'DISCARD';
                    slot.appendChild(badge);
                }
            }
        }
    }

    function updateMatrixDisabledStates() {
        const selectedHand = new Set(state.hand.filter(Boolean));
        const selectedDraw = new Set(state.drawReplacements.filter(Boolean));

        document.querySelectorAll('.selector-card').forEach(btn => {
            const card = btn.getAttribute('data-card');
            if (selectedHand.has(card)) {
                btn.classList.add('selected');
                btn.style.borderColor = 'var(--accent-cyan)';
                btn.style.boxShadow = '0 0 8px var(--accent-cyan)';
                btn.style.opacity = '1';
            } else if (selectedDraw.has(card)) {
                btn.classList.remove('selected');
                btn.style.borderColor = 'var(--accent-gold)';
                btn.style.boxShadow = '0 0 8px var(--accent-gold)';
                btn.style.opacity = '0.5';
            } else {
                btn.classList.remove('selected');
                btn.style.borderColor = '';
                btn.style.boxShadow = '';
                btn.style.opacity = '1';
            }
        });
    }

    // -------------------------------------------------------------
    // Hand Solver & EV Evaluation
    // -------------------------------------------------------------
    async function checkAndEvaluateHand() {
        const filledCards = state.hand.filter(Boolean);
        if (filledCards.length < 5) {
            elements.analysisSection.classList.add('hidden');
            state.currentAnalysis = null;
            state.activeDrawSlotIdx = null;
            elements.handInstruction.textContent = `Tap ${5 - filledCards.length} more card${5 - filledCards.length > 1 ? 's' : ''} to analyze`;
            renderHandSlots();
            return;
        }

        elements.handInstruction.textContent = 'Calculating best hold...';

        try {
            let analysis;
            if (state.serverOnline) {
                const resp = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        cards: filledCards,
                        strategy: state.strategy
                    })
                });
                const data = await resp.json();
                if (data.status === 'ok') analysis = data.result;
            }

            if (!analysis && window.PokerSolver) {
                const cardIds = filledCards.map(window.PokerSolver.cardFromStr);
                analysis = window.PokerSolver.analyzeAllHolds(cardIds, state.strategy);
            }

            if (analysis) {
                state.currentAnalysis = analysis;
                state.userHoldOverrides = new Set(analysis.best_hold.hold_indices);
                renderAnalysisResults(analysis);
                renderHandSlots();
                renderDrawInputs();
                elements.analysisSection.classList.remove('hidden');
                elements.handInstruction.textContent = 'Tap any card above to toggle HOLD / DISCARD override';
            }
        } catch (err) {
            console.error('Error evaluating hand:', err);
            elements.handInstruction.textContent = 'Error computing best move: ' + err.message;
        }
    }

    function renderAnalysisResults(analysis) {
        const best = analysis.best_hold;
        const heldDisplay = best.held_display.length > 0 ? best.held_display.join(', ') : 'None (Discard All)';
        const discDisplay = best.discarded_display.length > 0 ? best.discarded_display.join(', ') : 'None (Keep All)';

        // Update Strategy Badge & Highlight
        if (elements.recBadge) {
            if (state.strategy === 'win_rate') {
                elements.recBadge.textContent = '🎯 MAX WIN RATE STRATEGY (QUALIFIER)';
                elements.recBadge.style.borderColor = 'var(--accent-green)';
                elements.recBadge.style.color = 'var(--accent-green)';
            } else {
                elements.recBadge.textContent = '💰 MAX REWARD STRATEGY (EV)';
                elements.recBadge.style.borderColor = 'var(--accent-gold)';
                elements.recBadge.style.color = 'var(--accent-gold)';
            }
        }

        const evBox = elements.recEvVal ? elements.recEvVal.closest('.stat-box') : null;
        const winBox = elements.recWinRateVal ? elements.recWinRateVal.closest('.stat-box') : null;
        if (evBox && winBox) {
            if (state.strategy === 'win_rate') {
                winBox.className = 'stat-box highlight-win';
                evBox.className = 'stat-box';
            } else {
                evBox.className = 'stat-box highlight-ev';
                winBox.className = 'stat-box';
            }
        }

        elements.recActionText.textContent = `HOLD [ ${heldDisplay} ]`;
        elements.recDiscardText.textContent = `Discard: [ ${discDisplay} ]`;

        elements.recEvVal.textContent = `${best.ev.toFixed(2)}x`;
        elements.recWinRateVal.textContent = `${(best.win_rate * 100).toFixed(1)}%`;

        elements.currentHandNameVal.textContent = analysis.current_hand_name;
        elements.currentHandPayoutVal.textContent = `Payout: ${analysis.current_payout}x`;

        elements.distChips.innerHTML = '';
        const dist = best.distribution;
        const total = best.total_combos;

        for (const [handName, count] of Object.entries(dist)) {
            if (count > 0 && window.PokerSolver && window.PokerSolver.PAYOUT_TABLE[handName] > 0) {
                const pct = ((count / total) * 100).toFixed(1);
                const chip = document.createElement('div');
                chip.className = 'dist-chip';
                if (['Royal Flush', 'Five of a Kind', 'Straight Flush', 'Quads'].includes(handName)) {
                    chip.classList.add('highlight');
                }
                chip.innerHTML = `<strong>${handName}</strong>: ${pct}% (${count}/${total})`;
                elements.distChips.appendChild(chip);
            }
        }

        if (elements.toggleAllHoldsBtn) {
            elements.toggleAllHoldsBtn.textContent = 'Show All 32';
        }
        renderHoldsTable(analysis.all_holds.slice(0, 5));
    }

    function renderHoldsTable(holdsList) {
        elements.holdsTableBody.innerHTML = '';
        const isWinRate = (state.strategy === 'win_rate');

        holdsList.forEach((hold, idx) => {
            const tr = document.createElement('tr');
            if (idx === 0) tr.classList.add('best-row');

            const heldStr = hold.held_display.length > 0 ? hold.held_display.join(' ') : 'Discard All';
            const evColor = isWinRate ? 'var(--text-main)' : 'var(--accent-gold)';
            const winColor = isWinRate ? 'var(--accent-green)' : 'var(--text-main)';
            const winWeight = isWinRate ? '700' : '400';
            const evWeight = isWinRate ? '400' : '700';

            tr.innerHTML = `
                <td>#${idx + 1}</td>
                <td><strong>${heldStr}</strong></td>
                <td style="color: ${evColor}; font-weight: ${evWeight}; font-family: var(--font-mono);">${hold.ev.toFixed(2)}x</td>
                <td style="color: ${winColor}; font-weight: ${winWeight};">${(hold.win_rate * 100).toFixed(1)}%</td>
                <td><button class="btn btn-secondary btn-sm select-hold-btn">Apply</button></td>
            `;

            tr.querySelector('.select-hold-btn').addEventListener('click', () => {
                state.userHoldOverrides = new Set(hold.hold_indices);
                renderHandSlots();
                renderDrawInputs();
            });

            elements.holdsTableBody.appendChild(tr);
        });
    }

    // -------------------------------------------------------------
    // Interactive Draw Card Input (Zero Prompt - Click to Fill)
    // -------------------------------------------------------------
    function renderDrawInputs() {
        elements.drawInputsContainer.innerHTML = '';
        elements.roundResultBanner.classList.add('hidden');

        if (!state.currentAnalysis) return;

        const holdIndices = state.userHoldOverrides || new Set(state.currentAnalysis.best_hold.hold_indices);
        const discardedIndices = [0, 1, 2, 3, 4].filter(i => !holdIndices.has(i));

        if (discardedIndices.length === 0) {
            elements.drawInputsContainer.innerHTML = '<span style="font-size: 0.85rem; color: var(--accent-green); font-weight: 700;">You are holding all 5 cards! No draw required.</span>';
            state.drawReplacements = [];
            state.activeDrawSlotIdx = null;
            return;
        }

        // Preserve existing draw selections if length matches
        if (state.drawReplacements.length !== discardedIndices.length) {
            state.drawReplacements = new Array(discardedIndices.length).fill(null);
        }

        discardedIndices.forEach((discardIdx, slotIdx) => {
            const slot = document.createElement('div');
            slot.className = 'draw-slot';
            slot.setAttribute('data-draw-slot', slotIdx);

            if (state.activeDrawSlotIdx === slotIdx) {
                slot.classList.add('active-slot');
            }

            const card = state.drawReplacements[slotIdx];
            if (card) {
                slot.classList.add('filled');
                if (card === 'JK') {
                    slot.innerHTML = `<span style="font-size: 0.65rem; color: var(--accent-gold);">Draw #${slotIdx + 1}</span><span style="font-size: 1.2rem;">🃏</span>`;
                } else {
                    const suit = card.slice(-1);
                    const rank = card.slice(0, -1);
                    const isRed = (suit === 'H' || suit === 'D');
                    slot.classList.add(isRed ? 'is-red' : 'is-black');
                    slot.innerHTML = `
                        <span style="font-size: 0.6rem; opacity: 0.7;">Draw #${slotIdx + 1}</span>
                        <span style="font-size: 0.95rem; font-weight: 800;">${rank}${SUIT_SYMBOLS[suit] || suit}</span>
                    `;
                }
            } else {
                slot.innerHTML = `<span style="font-size: 0.65rem; color: var(--text-dim);">Draw #${slotIdx + 1}</span><span style="font-size: 1.1rem; color: var(--accent-cyan);">+</span>`;
            }

            slot.addEventListener('click', () => {
                if (state.drawReplacements[slotIdx]) {
                    // Click filled slot to clear it
                    state.drawReplacements[slotIdx] = null;
                    setActiveDrawSlot(slotIdx);
                } else {
                    setActiveDrawSlot(slotIdx);
                }
            });

            elements.drawInputsContainer.appendChild(slot);
        });

        // Set active slot if not yet set
        if (state.activeDrawSlotIdx === null && state.drawReplacements.includes(null)) {
            setActiveDrawSlot(state.drawReplacements.indexOf(null));
        }
    }

    function setActiveDrawSlot(idx) {
        state.activeDrawSlotIdx = idx;
        const slots = elements.drawInputsContainer.children;
        for (let i = 0; i < slots.length; i++) {
            if (i === idx) {
                slots[i].classList.add('active-slot');
            } else {
                slots[i].classList.remove('active-slot');
            }
        }
        if (elements.drawInstructions) {
            elements.drawInstructions.textContent = `Tap an available card in the selector above to assign to Draw #${idx + 1}:`;
        }
    }

    function autoFillRemainingDraw() {
        const inUse = new Set(state.hand.filter(Boolean).concat(state.drawReplacements.filter(Boolean)));
        const available = [];
        RANKS.forEach(r => SUITS.forEach(s => {
            const c = `${r}${s}`;
            if (!inUse.has(c)) available.push(c);
        }));
        if (!inUse.has('JK')) available.push('JK');

        // Shuffle available
        for (let i = available.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [available[i], available[j]] = [available[j], available[i]];
        }

        let pickIdx = 0;
        for (let i = 0; i < state.drawReplacements.length; i++) {
            if (!state.drawReplacements[i] && pickIdx < available.length) {
                state.drawReplacements[i] = available[pickIdx++];
            }
        }
        state.activeDrawSlotIdx = null;
        renderDrawInputs();
        updateMatrixDisabledStates();
        showToast('Auto-filled remaining draw slots with random cards!', 'info');
    }

    async function finishRoundAndLog() {
        if (!state.currentAnalysis) return;

        const holdIndices = Array.from(state.userHoldOverrides || state.currentAnalysis.best_hold.hold_indices);
        const discardedIndices = [0, 1, 2, 3, 4].filter(i => !holdIndices.includes(i));

        // Auto-fill any remaining unfilled slots if user forgot to click
        if (state.drawReplacements.some(c => !c)) {
            autoFillRemainingDraw();
        }

        // Assemble final hand
        const finalHand = [];
        holdIndices.forEach(i => finalHand.push(state.hand[i]));
        discardedIndices.forEach((dIdx, slotIdx) => {
            finalHand.push(state.drawReplacements[slotIdx]);
        });

        // Evaluate final hand
        let finalPayout = 0;
        let finalHandName = 'High Card';
        if (window.PokerSolver) {
            const finalIds = finalHand.map(window.PokerSolver.cardFromStr);
            const [p, name] = window.PokerSolver.eval5Cards(finalIds);
            finalPayout = p;
            finalHandName = name;
        }

        const betCoins = 50;
        const earnedCoins = betCoins * finalPayout;
        const roundId = 'R-' + Date.now().toString().slice(-8);

        // Display outcome banner
        elements.roundResultBanner.classList.remove('hidden');
        if (finalPayout > 0) {
            elements.roundResultTitle.textContent = `🎉 Won: ${finalHandName} (${finalPayout}x payout = ${earnedCoins} Coins!)`;
            if (finalPayout >= 4) {
                elements.roundResultDesc.textContent = 'Congratulations! You qualified for the High & Low Double Up Chance!';
                elements.goToHighLowBtn.style.display = 'inline-block';
            } else {
                elements.roundResultDesc.textContent = 'Nice win! Trips recorded.';
                elements.goToHighLowBtn.style.display = 'none';
            }
        } else {
            elements.roundResultTitle.textContent = `💀 Missed: ${finalHandName} (Payout: 0x)`;
            elements.roundResultDesc.textContent = 'Draw did not hit. Hand recorded to logs.';
            elements.goToHighLowBtn.style.display = 'none';
        }

        // Prepare log data
        const roundData = {
            round_id: roundId,
            strategy: state.strategy,
            initial_hand: state.hand.slice(),
            recommended_hold: state.currentAnalysis.best_hold.held_cards,
            recommended_ev: state.currentAnalysis.best_hold.ev,
            recommended_win_rate: state.currentAnalysis.best_hold.win_rate,
            top_holds: state.currentAnalysis.all_holds.slice(0, 3),
            user_held: holdIndices.map(i => state.hand[i]),
            drawn_cards: state.drawReplacements.filter(Boolean),
            final_hand: finalHand,
            final_hand_name: finalHandName,
            payout_multiplier: finalPayout,
            bet_coins: betCoins,
            earned_coins: earnedCoins,
            high_low_steps: []
        };

        state.lastCompletedRound = roundData;

        // Initialize High & Low state for Phase 2
        state.highLow.roundId = roundId;
        state.highLow.initialPot = earnedCoins > 0 ? earnedCoins : 50;
        state.highLow.currentPot = state.highLow.initialPot;
        state.highLow.baseHandName = finalHandName;
        state.highLow.streak = 0;
        state.highLow.history = [];
        state.highLow.isFinished = false;

        // Log to server or localStorage
        await saveRoundRecord(roundData);
        loadRecentLogs();
        showToast('Round completed and saved to logs!', 'success');
    }

    async function saveRoundRecord(roundData) {
        if (state.serverOnline) {
            try {
                await fetch('/api/log', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(roundData)
                });
                return;
            } catch (err) {
                console.warn('Server log failed, saving locally:', err);
            }
        }
        saveLogLocally(roundData);
    }

    function saveLogLocally(roundData) {
        const logs = JSON.parse(localStorage.getItem('poker_assistant_logs') || localStorage.getItem('hololive_poker_logs') || '[]');
        roundData.timestamp_display = roundData.timestamp_display || new Date().toLocaleString();
        roundData.round_id = roundData.round_id || ('LOCAL-' + Date.now().toString().slice(-6));

        if (!roundData.diagnostic && window.PokerSolver && window.PokerSolver.generateRoundExplanation) {
            const initCards = roundData.initial_hand || [];
            const recHold = roundData.recommended_hold || [];
            const userHeld = roundData.user_held || [];
            const recIndices = initCards.map((c, i) => recHold.includes(c) ? i : -1).filter(i => i >= 0);
            const userIndices = initCards.map((c, i) => userHeld.includes(c) ? i : -1).filter(i => i >= 0);

            roundData.diagnostic = window.PokerSolver.generateRoundExplanation({
                initial_cards_str: initCards,
                recommended_hold_indices: recIndices,
                recommended_ev: roundData.recommended_ev || 0.0,
                user_held_indices: userIndices,
                drawn_cards_str: roundData.drawn_cards || [],
                final_cards_str: roundData.final_hand || [],
                final_hand_name: roundData.final_hand_name || 'High Card',
                payout_multiplier: roundData.payout_multiplier || 0,
                high_low_steps: roundData.high_low_steps || [],
                final_coins: roundData.earned_coins,
                strategy: roundData.strategy || 'win_rate',
                recommended_win_rate: roundData.recommended_win_rate
            });
        }

        // Check if updating existing record
        const existingIdx = logs.findIndex(r => r.round_id === roundData.round_id);
        if (existingIdx >= 0) {
            logs[existingIdx] = roundData;
        } else {
            logs.unshift(roundData);
        }
        localStorage.setItem('poker_assistant_logs', JSON.stringify(logs.slice(0, 100)));
    }

    // -------------------------------------------------------------
    // Phase 2: High & Low Interactions (Interactive Drawn Card Progression)
    // -------------------------------------------------------------
    async function selectHighLowOpenCard(rank) {
        state.highLow.openCard = rank;

        document.querySelectorAll('.hl-rank-btn').forEach(btn => {
            if (btn.getAttribute('data-rank') === rank) {
                btn.classList.add('selected');
            } else {
                btn.classList.remove('selected');
            }
        });

        let result;
        if (state.serverOnline) {
            try {
                const resp = await fetch('/api/highlow', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({open_card: rank})
                });
                const data = await resp.json();
                if (data.status === 'ok') result = data.result;
            } catch (e) {
                console.warn('High-low API call failed, using client solver.');
            }
        }

        if (!result && window.PokerSolver) {
            result = window.PokerSolver.evaluateHighLow(rank);
        }

        if (result) {
            state.highLow.currentAnalysis = result;
            renderHighLowResult(result);
        }
    }

    function renderHighLowResult(r) {
        elements.hlDirection.className = 'decision-direction ' + r.recommendation.toLowerCase();
        if (r.recommendation === 'HIGHER') {
            elements.hlDirection.textContent = '⬆️ PICK HIGHER';
        } else if (r.recommendation === 'LOWER') {
            elements.hlDirection.textContent = '⬇️ PICK LOWER';
        } else {
            elements.hlDirection.textContent = '⚖️ COIN TOSS (50/50)';
        }

        elements.hlProbBadge.textContent = `${(r.best_win_rate * 100).toFixed(1)}% Win Rate (Net of Redraws)`;
        elements.hlRiskBadge.textContent = r.risk_level;
        elements.hlRiskBadge.style.backgroundColor = r.risk_color;
        elements.hlAdviceText.textContent = r.advice;

        elements.higherBar.style.width = `${(r.raw_higher_prob * 100).toFixed(1)}%`;
        elements.higherPct.textContent = `${(r.raw_higher_prob * 100).toFixed(1)}%`;

        elements.lowerBar.style.width = `${(r.raw_lower_prob * 100).toFixed(1)}%`;
        elements.lowerPct.textContent = `${(r.raw_lower_prob * 100).toFixed(1)}%`;

        elements.redrawBar.style.width = `${(r.raw_tie_prob * 100).toFixed(1)}%`;
        elements.redrawPct.textContent = `${(r.raw_tie_prob * 100).toFixed(1)}%`;
    }

    async function handleHighLowDrawnRank(drawnRank) {
        if (!state.highLow.openCard) {
            showToast('Please select the open card first!', 'danger');
            return;
        }

        const openRank = state.highLow.openCard;
        const openIdx = RANK_INDEX[openRank];
        const drawnIdx = RANK_INDEX[drawnRank];
        const rec = state.highLow.currentAnalysis || (window.PokerSolver && window.PokerSolver.evaluateHighLow(openRank));
        const userChoice = rec ? rec.recommendation : 'NEUTRAL';

        let outcomeType;
        if (drawnIdx === openIdx) {
            outcomeType = 'REDRAW';
        } else if (userChoice === 'HIGHER') {
            outcomeType = drawnIdx > openIdx ? 'WIN' : 'LOSS';
        } else if (userChoice === 'LOWER') {
            outcomeType = drawnIdx < openIdx ? 'WIN' : 'LOSS';
        } else {
            // Neutral 50/50
            outcomeType = drawnIdx > openIdx ? 'WIN' : 'LOSS';
        }

        await processHighLowOutcome(outcomeType, openRank, userChoice, drawnRank, rec);
    }

    async function processHighLowOutcome(outcomeType, openRank, userChoice, drawnRank, rec) {
        const stepNum = state.highLow.streak + 1;
        const winProb = rec ? rec.best_win_rate : 0.5;
        const riskLevel = rec ? rec.risk_level : 'NORMAL';

        const stepRecord = {
            step: stepNum,
            open_card: openRank,
            recommendation: rec ? rec.recommendation : userChoice,
            user_choice: userChoice,
            drawn_card: drawnRank,
            result: outcomeType,
            win_prob: winProb,
            risk_level: riskLevel,
            pot: state.highLow.currentPot
        };

        state.highLow.history.push(stepRecord);
        renderHighLowStepList();

        if (outcomeType === 'WIN') {
            state.highLow.streak++;
            state.highLow.currentPot *= 2;
            elements.hlRoundCount.textContent = state.highLow.streak + 1;
            elements.hlPotDisplay.textContent = state.highLow.currentPot;

            showToast(`🎉 Correct! Drew [${drawnRank}]. Pot doubled to ${state.highLow.currentPot} coins!`, 'success');

            // Drawn card automatically becomes new open card!
            await selectHighLowOpenCard(drawnRank);
            await syncHighLowLog(false);

        } else if (outcomeType === 'REDRAW') {
            showToast(`🔄 Tie / Redraw! Drew [${drawnRank}] matches open card. Go again with no loss.`, 'info');
            await syncHighLowLog(false);

        } else if (outcomeType === 'LOSS') {
            state.highLow.currentPot = 0;
            elements.hlPotDisplay.textContent = 0;
            state.highLow.isFinished = true;

            showToast(`💀 Busted! Drew [${drawnRank}]. Lost all double-up coins. Recorded to logs.`, 'danger');
            await syncHighLowLog(true, 'LOSS (Busted in High & Low)');

            // Reset after brief pause
            setTimeout(() => {
                state.highLow.streak = 0;
                state.highLow.currentPot = 50;
                elements.hlRoundCount.textContent = 1;
                elements.hlPotDisplay.textContent = 50;
            }, 3000);

        } else if (outcomeType === 'CASHOUT') {
            showToast(`💰 Cashed out ${state.highLow.currentPot} coins! Congratulations!`, 'success');
            await syncHighLowLog(true, `WIN (Double Up: ${state.highLow.currentPot} Coins)`);

            state.highLow.isFinished = true;
            state.highLow.streak = 0;
            state.highLow.currentPot = 50;
            elements.hlRoundCount.textContent = 1;
            elements.hlPotDisplay.textContent = 50;
        }
    }

    function renderHighLowStepList() {
        if (!elements.hlHistoryList) return;
        elements.hlHistoryList.innerHTML = '';
        if (state.highLow.history.length === 0) {
            elements.hlHistoryList.innerHTML = '<div class="text-muted" style="font-size: 0.75rem;">No steps taken yet in this streak.</div>';
            return;
        }

        state.highLow.history.forEach(s => {
            const div = document.createElement('div');
            const resClass = s.result.toLowerCase();
            div.className = `hl-history-step ${resClass}`;
            div.innerHTML = `
                <span><strong>#${s.step}</strong> [${s.open_card}] ➔ [${s.drawn_card}] (${s.user_choice})</span>
                <span><strong>${s.result}</strong> (Pot: ${s.pot}c)</span>
            `;
            elements.hlHistoryList.appendChild(div);
        });
    }

    async function syncHighLowLog(isFinal = false, finalOutcome = null) {
        const roundId = state.highLow.roundId || ('HL-' + Date.now().toString().slice(-8));
        state.highLow.roundId = roundId;

        const roundData = state.lastCompletedRound ? Object.assign({}, state.lastCompletedRound) : {
            round_id: roundId,
            initial_hand: [],
            recommended_hold: [],
            user_held: [],
            drawn_cards: [],
            final_hand: [],
            final_hand_name: state.highLow.baseHandName,
            payout_multiplier: 1,
            bet_coins: 50,
            earned_coins: state.highLow.currentPot
        };

        roundData.round_id = roundId;
        roundData.earned_coins = state.highLow.currentPot;
        roundData.high_low_steps = state.highLow.history.slice();

        if (finalOutcome) {
            roundData.outcome = finalOutcome;
        }

        await saveRoundRecord(roundData);
        loadRecentLogs();
    }

    // -------------------------------------------------------------
    // Logs Viewer
    // -------------------------------------------------------------
    async function loadRecentLogs() {
        let logs = [];
        if (state.serverOnline) {
            try {
                const resp = await fetch('/api/logs');
                const data = await resp.json();
                if (data.status === 'ok') logs = data.logs;
            } catch (e) {
                console.warn('Failed to load server logs, reading local.');
            }
        }

        if (logs.length === 0) {
            logs = JSON.parse(localStorage.getItem('poker_assistant_logs') || localStorage.getItem('hololive_poker_logs') || '[]');
        }

        elements.historyList.innerHTML = '';
        if (logs.length === 0) {
            elements.historyList.innerHTML = '<div class="empty-state">No games logged yet. Complete a round to generate logs!</div>';
            return;
        }

        logs.forEach(rec => {
            const card = document.createElement('div');
            const outcomeStr = String(rec.outcome || 'LOSS').toUpperCase();
            const isWin = outcomeStr.includes('WIN');
            card.className = `history-card ${isWin ? 'win' : 'loss'}`;

            const dealtDisplay = (rec.initial_display || rec.initial_hand || []).join(' ') || 'None (Direct HL)';
            const finalDisplay = (rec.final_display || rec.final_hand || []).join(' ') || 'None';

            let hlSummaryHtml = '';
            if (rec.high_low_steps && rec.high_low_steps.length > 0) {
                hlSummaryHtml = `
                    <div style="font-size: 0.72rem; color: var(--accent-gold); margin-top: 4px; font-family: var(--font-mono);">
                        🎲 Double Up: ${rec.high_low_steps.length} step(s) played. Final coins: ${rec.earned_coins}c
                    </div>
                `;
            }

            const stratBadge = (rec.strategy === 'ev')
                ? '<span class="strat-pill ev-pill" style="margin-left: 6px;">💰 EV</span>'
                : '<span class="strat-pill default" style="margin-left: 6px;">🎯 Win%</span>';

            card.innerHTML = `
                <div class="history-top">
                    <span><strong>${rec.round_id}</strong> ${stratBadge} | ${rec.timestamp_display || rec.timestamp}</span>
                    <span style="color: ${isWin ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 800;">
                        ${rec.outcome}: ${rec.earned_coins} Coins
                    </span>
                </div>
                <div class="history-hand-row">
                    <span style="color: var(--text-muted); font-size: 0.75rem;">Dealt:</span>
                    <span>${dealtDisplay}</span>
                    <span style="color: var(--text-muted); font-size: 0.75rem; margin-left: 8px;">Final:</span>
                    <span>${finalDisplay} (${rec.final_hand_name})</span>
                </div>
                ${hlSummaryHtml}
                <div class="history-diagnostic">
                    💡 <strong>Post-Mortem:</strong> ${rec.diagnostic || 'Normal play.'}
                </div>
            `;
            elements.historyList.appendChild(card);
        });
    }

    async function loadRawTextLog() {
        elements.rawLogViewer.textContent = 'Loading game_logs.txt...';
        if (state.serverOnline) {
            try {
                const resp = await fetch('/api/logs/raw');
                const data = await resp.json();
                if (data.status === 'ok') {
                    elements.rawLogViewer.textContent = data.raw_text;
                    return;
                }
            } catch (e) {
                console.warn('Error fetching raw log:', e);
            }
        }

        // Local fallback
        const logs = JSON.parse(localStorage.getItem('poker_assistant_logs') || localStorage.getItem('hololive_poker_logs') || '[]');
        elements.rawLogViewer.textContent = JSON.stringify(logs, null, 2);
    }

    async function clearAllLogs() {
        if (!confirm('Are you sure you want to clear all game logs?')) return;
        if (state.serverOnline) {
            try {
                await fetch('/api/logs/clear', {method: 'POST'});
            } catch (e) {
                console.warn('Server clear failed.');
            }
        }
        localStorage.removeItem('poker_assistant_logs');
        localStorage.removeItem('hololive_poker_logs');
        loadRecentLogs();
        loadRawTextLog();
        showToast('All logs cleared!', 'info');
    }

    // -------------------------------------------------------------
    // Presets & Event Handlers
    // -------------------------------------------------------------
    function bindEvents() {
        // Strategy Mode Toggles
        function setStrategy(strat) {
            if (state.strategy === strat) return;
            state.strategy = strat;
            try {
                localStorage.setItem('poker_assistant_strategy', strat);
            } catch (e) {}
            updateStrategyUI();
            const filledCount = state.hand.filter(Boolean).length;
            if (filledCount === 5) {
                state.userHoldOverrides = null;
                checkAndEvaluateHand();
            }
            const label = strat === 'win_rate' ? '🎯 Max Win Rate (Qualifier)' : '💰 Max Reward (EV)';
            showToast(`Strategy switched to: ${label}`, 'info');
        }

        function updateStrategyUI() {
            if (elements.stratWinRateBtn && elements.stratEvBtn) {
                if (state.strategy === 'win_rate') {
                    elements.stratWinRateBtn.classList.add('active');
                    elements.stratEvBtn.classList.remove('active');
                } else {
                    elements.stratWinRateBtn.classList.remove('active');
                    elements.stratEvBtn.classList.add('active');
                }
            }
        }

        updateStrategyUI();

        if (elements.stratWinRateBtn) {
            elements.stratWinRateBtn.addEventListener('click', () => setStrategy('win_rate'));
        }
        if (elements.stratEvBtn) {
            elements.stratEvBtn.addEventListener('click', () => setStrategy('ev'));
        }

        elements.clearHandBtn.addEventListener('click', () => {
            state.hand = [null, null, null, null, null];
            state.userHoldOverrides = null;
            state.drawReplacements = [];
            state.activeDrawSlotIdx = null;
            renderHandSlots();
            updateMatrixDisabledStates();
            checkAndEvaluateHand();
        });

        elements.randomHandBtn.addEventListener('click', dealRandomHand);

        elements.presetSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            if (!val) return;
            if (val === 'royal_draw') state.hand = ['10H', 'JH', 'QH', 'KH', '2D'];
            else if (val === 'pair_vs_flush') state.hand = ['2H', '2D', '5H', '8H', 'KH'];
            else if (val === 'five_kind_draw') state.hand = ['AS', 'AH', 'AD', 'AC', 'JK'];
            else if (val === 'straight_draw') state.hand = ['6H', '7D', '8S', '9C', '2D'];
            else if (val === 'flush_draw') state.hand = ['2H', '5H', '8H', 'JH', '4D'];
            else if (val === 'full_house') state.hand = ['7S', '7D', '7H', '8C', '8D'];
            else if (val === 'two_pair') state.hand = ['2D', '2C', '9C', '9S', 'JH'];
            else if (val === 'trips') state.hand = ['4D', '4S', '4C', '8H', 'KS'];
            else if (val === 'random') dealRandomHand();

            state.userHoldOverrides = null;
            state.drawReplacements = [];
            state.activeDrawSlotIdx = null;
            renderHandSlots();
            updateMatrixDisabledStates();
            checkAndEvaluateHand();
            e.target.value = '';
        });

        elements.jokerBtn.addEventListener('click', () => onMatrixCardClick('JK'));

        elements.toggleAllHoldsBtn.addEventListener('click', () => {
            if (!state.currentAnalysis) return;
            const isShowingAll = elements.toggleAllHoldsBtn.textContent.includes('Top 5');
            if (isShowingAll) {
                renderHoldsTable(state.currentAnalysis.all_holds.slice(0, 5));
                elements.toggleAllHoldsBtn.textContent = 'Show All 32';
            } else {
                renderHoldsTable(state.currentAnalysis.all_holds);
                elements.toggleAllHoldsBtn.textContent = 'Show Top 5 Only';
            }
        });

        if (elements.autoFillDrawBtn) {
            elements.autoFillDrawBtn.addEventListener('click', autoFillRemainingDraw);
        }

        elements.finishRoundBtn.addEventListener('click', finishRoundAndLog);

        elements.goToHighLowBtn.addEventListener('click', () => {
            document.querySelector('.tab-btn[data-tab="phase2"]').click();
            elements.hlPotDisplay.textContent = state.highLow.currentPot;
            showToast('Entered High & Low Double Up! Select the open card displayed on your screen.', 'info');
        });

        // High & Low Outcome buttons
        elements.hlWinBtn.addEventListener('click', () => {
            if (!state.highLow.openCard) {
                showToast('Please select the open card first!', 'danger');
                return;
            }
            processHighLowOutcome('WIN', state.highLow.openCard, 'HIGHER', 'Win (Manual)', state.highLow.currentAnalysis);
        });

        elements.hlRedrawBtn.addEventListener('click', () => {
            if (!state.highLow.openCard) {
                showToast('Please select the open card first!', 'danger');
                return;
            }
            processHighLowOutcome('REDRAW', state.highLow.openCard, 'NEUTRAL', state.highLow.openCard, state.highLow.currentAnalysis);
        });

        elements.hlLoseBtn.addEventListener('click', () => {
            if (!state.highLow.openCard) {
                showToast('Please select the open card first!', 'danger');
                return;
            }
            processHighLowOutcome('LOSS', state.highLow.openCard, 'LOWER', 'Bust (Manual)', state.highLow.currentAnalysis);
        });

        elements.hlCashoutBtn.addEventListener('click', () => {
            processHighLowOutcome('CASHOUT', state.highLow.openCard || 'None', 'CASHOUT', 'None', null);
        });

        elements.refreshLogsBtn.addEventListener('click', loadRecentLogs);
        elements.clearLogsBtn.addEventListener('click', clearAllLogs);
    }

    function dealRandomHand() {
        const deck = [];
        RANKS.forEach(r => SUITS.forEach(s => deck.push(`${r}${s}`)));
        deck.push('JK');

        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }

        state.hand = deck.slice(0, 5);
        state.userHoldOverrides = null;
        state.drawReplacements = [];
        state.activeDrawSlotIdx = null;
        renderHandSlots();
        updateMatrixDisabledStates();
        checkAndEvaluateHand();
    }

    // Start on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
