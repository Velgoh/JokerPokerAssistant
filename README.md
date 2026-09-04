# Joker Poker Assistant

A lightweight poker assistant and real-time expected value (EV) solver for 5-Card Draw Joker Wild Video Poker and High-Low Double Up games.

The solver evaluates holds across all 32 combinations using a 53-card deck (52 standard cards + 1 Joker) and calculates odds for High-Low Double Up rounds.

[Launch Web App](https://velgoh.github.io/JokerPokerAssistant/)

---

## Features

* Dual Optimization Modes: Switch between Max Win Rate (qualifying for Double Up with Two Pair or better) and Max Reward (EV) to maximize average payout multipliers.
* 32-Hold Solver: Evaluates all 32 hold combinations in real time across the unseen 48-card deck.
* Joker Wildcard Support: Handles 53-card deck evaluations, including Five of a Kind (140x) and wild Royal Flushes (200x).
* High-Low Double Up Advisor: Computes win/loss probabilities and risk profiles for every rank (2 through Ace), with automatic free-redraw tie handling.
* Standalone Browser or Python Server: Run directly in any modern browser via client-side JavaScript (`solver.js`) or with the lightweight Python standard library backend (`server.py`).
* Diagnostic Round Logging: Automatically records hands and outcomes into formatted text (`game_logs.txt`) and JSON Lines (`game_logs.jsonl`) logs, showing whether a loss was draw variance or a suboptimal hold.

---

## Payout Table & Game Rules

The game uses a 53-card deck: 52 standard playing cards (ranks 2 through Ace across Hearts, Diamonds, Clubs, Spades) plus 1 Joker wildcard. Hands achieving Two Pair or better (4x) qualify for the High-Low Double Up Chance.

| Hand Ranking | Description | Multiplier |
| :--- | :--- | :---: |
| Royal Flush | 10-J-Q-K-A suited (natural or with Joker) | x200 |
| Five of a Kind | Four cards of identical rank + Joker | x140 |
| Straight Flush | Five suited consecutive cards | x60 |
| Quads (Four of a Kind) | Four cards of identical rank | x30 |
| Full House | Three of a kind + pair | x16 |
| Flush | Five cards of identical suit | x14 |
| Straight | Five consecutive ranks (A-2-3-4-5 up to 10-J-Q-K-A) | x8 |
| Trips (Three of a Kind) | Three cards of identical rank | x4 |
| Two Pair | Two distinct pairs (Qualifies for Double Up) | x4 |
| One Pair | Two cards of identical rank (Does not qualify) | x0 |
| High Card | No combination made | x0 |

---

## High-Low Double Up Mechanics

* Card Hierarchy (Descending):
  A > K > Q > J > 10 > 9 > 8 > 7 > 6 > 5 > 4 > 3 > 2
* Redraw Rule: If the drawn card matches the rank of the face-up card, it is a free redraw (no loss; replay the step).
* Strategy & Risk Index:
  * Ace / 2: Guaranteed win (100% win rate, zero risk).
  * King / 3: Very safe (91.7% win probability).
  * Queen / 4: Safe (83.3% win probability).
  * Jack / 5: Favorable (75.0% win probability).
  * 10 / 6: Moderate risk (66.7% win probability).
  * 9 / 7: High risk (58.3% win probability).
  * 8: 50.0% coin flip (cash out recommended if holding a high pot).

---

## How to Run Locally

### Option 1: Double-Click Launcher (Windows)
Double-click `run.bat` in the project root. It checks your Python environment, starts the local server, and opens the UI in your default browser.

### Option 2: Python Command Line
```powershell
python server.py
```
Then open `http://127.0.0.1:5000` in your web browser. No external packages or `pip install` needed.

### Option 3: Standalone Browser Mode (No Server)
Open `index.html` directly in any web browser (Chrome, Brave, Edge, Firefox). The client solver (`solver.js`) runs all calculations locally with `localStorage` persistence.

---

## Project Structure

```
JokerPokerAssistant/
├── index.html        # Clean cyber-arcade dark-mode interface
├── styles.css        # UI styling, card visuals, and mobile layout
├── app.js            # Frontend controller, card picker, and High-Low tracker
├── solver.js         # In-browser client-side solver engine
├── server.py         # Python HTTP server and REST endpoints (zero dependencies)
├── solver.py         # Mathematical EV solver and hand evaluator
├── logger.py         # Formatted text and JSONL round logger
├── test_solver.py    # Unit tests for hand evaluations and EV calculation
├── test_e2e.py       # Integration tests for server REST endpoints
├── verify_browser.py # Browser DOM verification script
├── run.bat           # Windows 1-click batch launcher
├── LICENSE           # MIT License
└── README.md         # Documentation
```

---

## License

This project is open source and licensed under the [MIT License](LICENSE). You are free to use, modify, distribute, and build upon this software, provided that proper credit and attribution are given to the original author (Velgoh).

## Support
Glory to Mankind.
