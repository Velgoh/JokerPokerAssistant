# Joker Poker Assistant

A lightweight, high-performance mathematical assistant and real-time expected value (EV) solver designed for 5-Card Draw Joker Wild Video Poker and High-Low Double Up games.

The engine calculates mathematically optimal holds across all 32 possible combinations using a complete 53-card combinatorial model (52 standard cards + 1 Joker wildcard) and delivers exact probabilistic guidance for High-Low Double Up sessions.

**[Initiate Web Module](https://velgoh.github.io/JokerPokerAssistant/)**

---

## Features

* **Dual Optimization Engines:** Toggle seamlessly between **Max Win Rate** (maximizing qualification rate for Double Up rounds) and **Max Reward (EV)** (maximizing pure coin payout multipliers).
* **Exhaustive Combinatorial Solver:** Analyzes all 32 possible hold combinations in real time with zero approximations across remaining unseen deck states.
* **Joker Wildcard Integration:** Native handling of 53-card mechanics, including Five of a Kind (140x) and wild-assisted Royal Flushes (200x).
* **High-Low Double Up Advisor:** Computes exact win/loss probabilities and risk profiles for every rank (2 through Ace), with native free-redraw tie handling.
* **Dual Execution Modes:** Runs either through the ultra-fast Python standard library backend or 100% standalone inside any browser via the client-side JavaScript engine (`solver.js`).
* **Post-Mortem Diagnostics & Logging:** Automatically records round data into synchronized human-readable ASCII (`game_logs.txt`) and machine-parseable JSON Lines (`game_logs.jsonl`) logs, explaining whether a loss was draw variance or an incorrect hold.

---

## Payout Table & Game Rules

The game uses a **53-card deck** consisting of 52 standard playing cards (ranks 2 through Ace across Hearts, Diamonds, Clubs, and Spades) plus **1 Joker** wildcard. Hands achieving **Two Pair or better (4x)** qualify for the optional High-Low Double Up Chance.

| Hand Ranking | Description | Multiplier |
| :--- | :--- | :---: |
| **Royal Flush** | 10-J-Q-K-A suited (Natural or with Joker wildcard) | **x200** |
| **Five of a Kind** | Four cards of identical rank + Joker wildcard | **x140** |
| **Straight Flush** | Five suited consecutive cards (e.g. 5-6-7-8-9 suited) | **x60** |
| **Quads (Four of a Kind)** | Four cards of identical rank | **x30** |
| **Full House** | Three of a kind + One pair | **x16** |
| **Flush** | Five cards of identical suit | **x14** |
| **Straight** | Five consecutive cards (A-2-3-4-5 wheel up to 10-J-Q-K-A) | **x8** |
| **Trips (Three of a Kind)** | Three cards of identical rank | **x4** |
| **Two Pair** | Two distinct pairs (*Qualifies for Double Up!*) | **x4** |
| **One Pair** | Two cards of identical rank (*Does not qualify*) | **x0** |
| **High Card** | No combination formed | **x0** |

---

## High-Low Double Up Mechanics

* **Card Hierarchy (Descending):**
  A > K > Q > J > 10 > 9 > 8 > 7 > 6 > 5 > 4 > 3 > 2
* **Redraw Rule:** If the drawn card matches the rank of the face-up card, it is an automatic **free redraw** (no loss incurred; you replay the step).
* **Strategy & Risk Index:**
  * **Ace / 2:** Guaranteed Win (100% optimal pick — Zero Risk).
  * **King / 3:** Extremely Safe (91.7% win probability).
  * **Queen / 4:** Safe (83.3% win probability).
  * **Jack / 5:** Favorable (75.0% win probability).
  * **10 / 6:** Moderate Risk (66.7% win probability).
  * **9 / 7:** High Risk (58.3% win probability).
  * **8:** Pure 50/50 Coin Flip (50.0% win probability — cash out recommended if holding a high coin pot).

---

## How to Run Locally

### Option 1: Double-Click Launcher (Windows)
Double-click `run.bat` in the project root. It validates your Python environment, initializes the local server, and automatically opens the UI in your default browser.

### Option 2: Python Command Line
```powershell
python server.py
```
Then navigate to `http://127.0.0.1:5000` in your web browser. Zero third-party `pip` dependencies are required.

### Option 3: Standalone Browser Mode (Zero Server)
Open `index.html` directly in any modern browser (Chrome, Brave, Edge, Firefox). The built-in client solver (`solver.js`) executes all combinatorial calculations locally with full `localStorage` persistence.

---

## Project Structure

```
JokerPokerAssistant/
├── index.html        # Responsive cyber-arcade dark-mode interface
├── styles.css        # Visual styles, card themes, and mobile-friendly layout
├── app.js            # Frontend controller, draw management, and High-Low engine
├── solver.js         # In-browser client-side combinatorial solver engine
├── server.py         # Lightweight Python HTTP server & REST APIs (zero dependencies)
├── solver.py         # Backend mathematical EV engine and combinatorial solver
├── logger.py         # Dual JSONL and formatted ASCII round diagnostic logger
├── test_solver.py    # Comprehensive solver test suite (hand evals, EV, jokers)
├── test_e2e.py       # End-to-end HTTP REST API test suite
├── verify_browser.py # Headless browser DOM and interaction verification suite
├── run.bat           # Windows 1-click batch launcher
├── LICENSE           # MIT License
└── README.md         # Project documentation
```

---

## License

This project is open source and licensed under the [MIT License](LICENSE). You are free to use, modify, distribute, and build upon this software, provided that proper credit and attribution are given to the original author (Velgoh).

## Support
Glory to Mankind.
