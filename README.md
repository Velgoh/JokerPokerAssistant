# Joker Poker Assistant

A lightweight poker assistant and real-time expected value (EV) solver for 5-Card Draw Joker Wild Video Poker and High-Low Double Up games.

The solver evaluates holds across all 32 combinations using a 53-card deck (52 standard cards + 1 Joker) and calculates odds for High-Low Double Up rounds.

**[Click here to use the app live!](https://velgoh.github.io/JokerPokerAssistant/)**

---

## Features

* Dual Optimization Modes: Switch between Max Win Rate (qualifying for Double Up with Two Pair or better) and Max Reward (EV) to maximize average payout multipliers.
* 32-Hold Combinatorial Solver: Evaluates all 32 hold combinations in real time across the unseen 48-card deck.
* Joker Wildcard Support: Handles 53-card deck evaluations, including Five of a Kind (140x) and wild Royal Flushes (200x).
* High-Low Double Up Advisor: Computes win and loss probabilities for every rank (2 through Ace) with automatic free-redraw tie handling.
* 100% Client-Side and Offline: Fully self-contained web app running in any browser with zero server, build, or network dependencies.
* Diagnostic Round Logging: Automatically records hands, outcomes, and decision quality locally, showing whether a loss was an unlucky draw or a suboptimal hold.

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

## How to Use

### 1. Web App (Recommended)

Open the application directly in your browser:
**[Click here to use the app live!](https://velgoh.github.io/JokerPokerAssistant/)**

No installation, download, or setup required.

### 2. Offline / Local

1. Download or clone this repository.
2. Open `index.html` in your favorite web browser (Brave, Chrome, Firefox, Edge).
3. No server, build tools, or network connection required.

---

## Project Structure

```
JokerPokerAssistant/
├── .github/workflows/deploy.yml # GitHub Actions automated Pages deployment
├── index.html            # Dark arcade user interface
├── styles.css            # Responsive layout and card styling
├── app.js                # UI controller, card picker, and history manager
├── solver.js             # Client-side 32-hold EV and High-Low engine
├── favicon.svg           # Vector card icon
├── favicon.ico           # Browser shortcut icon
├── .nojekyll             # Static asset deployment bypass
├── LICENSE               # MIT License
└── README.md             # Documentation
```

---

## License

This project is open source and licensed under the [MIT License](LICENSE). You are free to use, modify, distribute, and build upon this software, provided that proper credit and attribution are given to the original author (Velgoh).

## Support
Glory to Mankind.
