# RETURNS — Portfolio Returns Tracker

**Real-time valuation and performance tracking engine for investment portfolios.**

Part of the **Hemrek Capital** product family. Built with Streamlit and powered by Yahoo Finance API.

---

## Features

- **Compare Portfolios Mode** — Upload and compare two different portfolios side-by-side
- **Live & Historical Valuations** — Track portfolio performance at current market prices or on any historical date
- **Multi-Market Support** — Global markets or Indian NSE (automatic `.NS` ticker suffix)
- **Instant P/L Analysis** — Automatic calculation of returns in dollars and percentages
- **Interactive Visualizations** — Performance distribution bar charts powered by Plotly
- **CSV Export** — Download portfolio holdings with formatted valuations
- **Obsidian Quant UI** — Premium institutional research terminal aesthetic synchronized with the Swing system

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

```bash
# Clone or download this repository
cd returns-main

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run returns.py
```

The application will open in your default browser at `http://localhost:8501`.

---

## Usage

### 1. Prepare Your Portfolio CSV

Create a CSV file with the following **required columns**:

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | string | Stock ticker symbol (e.g., `AAPL`, `RELIANCE`) |
| `units` | number | Number of shares/units held |
| `value` | number | Original investment value (cost basis) |

**Example CSV:**
```csv
symbol,units,value
AAPL,10,1500.00
MSFT,5,1200.00
GOOGL,2,2800.00
```

### 2. Configure Settings (Sidebar)

1. **Upload Portfolio CSV** — Select your prepared CSV file
2. **Market Type** — Choose `Global` or `Indian` (appends `.NS` for NSE)
3. **Valuation Mode** — Select `Live / Latest` or `Historical Date`
4. **Analysis Date** — (If historical) Pick the valuation date

### 3. Run Analysis

Click **"Fetch Valuations"** to retrieve market data and compute returns.

---

## Output

### Portfolio Metrics

- **Original Investment** — Total capital deployed
- **Current Valuation** — Market value at selected date
- **Total P/L** — Profit/loss in dollars and percentage
- **Positions** — Number of active holdings

### Detailed Holdings Tab

- Complete portfolio breakdown with per-symbol performance
- Color-coded returns (green for gains, red for losses)
- CSV download button for export

### Visual Analysis Tab

- **Allocation Pie Chart** — Current value distribution by symbol
- **Returns Bar Chart** — Percentage returns per symbol

---

## Architecture

```
returns-main/
├── returns.py          # Main application (entry point)
├── ui/                 # Swing Obsidian Quant Terminal UI module
│   ├── components.py
│   ├── theme.css
│   └── theme.py
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

### Tech Stack

- **Streamlit** — Web application framework
- **pandas** — Data manipulation and analysis
- **yfinance** — Market data from Yahoo Finance API
- **plotly** — Interactive charting and visualization

### Caching

Market data is cached for **10 minutes** to minimize API calls and improve performance.

---

## Design System

The UI strictly adheres to the **Obsidian Quant Terminal** design system shared with the `Swing` application — an institutional research terminal aesthetic.

**Key design principles:**
- Premium Obsidian `#0A0E17` canvas with Amber Gold `#D4A853` accents
- Hierarchical horizontal grids grouping metrics, tables, and charts
- Typography built on Syne (Display) and JetBrains Mono (Data)
- Frameless glassmorphic panels with subtle glowing borders

---

## Version

**Current Version:** v3.1.0

See [`CHANGELOG.md`](CHANGELOG.md) for release history.

---

## License

© 2026 Hemrek Capital. All rights reserved.

---

## Support

For issues or questions, contact the Hemrek Capital development team.
