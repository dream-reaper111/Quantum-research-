# Quantum-research-
QUANT
# Quantum News Bias

Quantum News Bias is a standalone Python research project that combines live news sentiment analysis with IBM Qiskit to produce an experimental probabilistic market or topic bias.

The program pulls recent news articles, scores their sentiment, weights them by recency and source diversity, converts the resulting features into a small quantum circuit, and then compares the classical sentiment result against a quantum-derived probability distribution.

The project is designed for research, experimentation, and backtesting. It is not a financial trading system and should not be treated as financial advice.

---

## Features

- Pulls recent articles from GNews
- Uses a free-tier news API
- Performs sentiment analysis with VADER
- Scores positive, neutral, and negative sentiment
- Weights newer articles more heavily
- Reduces influence from repeated stories from the same source
- Builds a 3-qubit Qiskit circuit
- Runs locally with Qiskit Aer
- Supports optional IBM Quantum hardware execution
- Produces Bullish, Neutral, and Bearish probabilities
- Compares classical and quantum-derived bias
- Saves historical results to JSONL
- Supports JSON output for integration with other programs

---

# How It Works

```text
GNews API
   |
   v
Recent News Articles
   |
   v
Headline + Description Processing
   |
   v
VADER Sentiment Analysis
   |
   +---- Positive %
   +---- Neutral %
   +---- Negative %
   +---- Mean Sentiment
   |
   v
Recency Weighting
   |
   v
Source Diversity Weighting
   |
   v
Normalized Feature Vector
   |
   v
Qiskit Quantum Circuit
   |
   +---- Local Aer Simulator
   |
   OR
   |
   +---- IBM Quantum QPU
   |
   v
Quantum Measurements
   |
   v
Bullish / Neutral / Bearish Distribution
   |
   v
Classical vs Quantum Bias Comparison
```

---

# Requirements

Recommended:

- Python 3.11+
- Linux, Windows, or macOS
- Internet connection
- GNews API key

Optional:

- IBM Quantum account

---

# Installation

Clone or extract the project.

```bash
cd quantum_news_bias
```

Create a Python virtual environment.

```bash
python3 -m venv .venv
```

Activate it.

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies.

```bash
pip install -r requirements.txt
```

---

# GNews Setup

Create a GNews API account and obtain an API key.

Copy the example environment file.

```bash
cp .env.example .env
```

Open it.

```bash
nano .env
```

Add your key:

```text
GNEWS_API_KEY=YOUR_GNEWS_API_KEY
```

Do not upload your `.env` file to GitHub.

The included `.gitignore` prevents it from being committed accidentally.

---

# Basic Usage

Analyze NVIDIA news:

```bash
python main.py "NVIDIA"
```

Analyze Tesla:

```bash
python main.py "Tesla"
```

Analyze Bitcoin:

```bash
python main.py "Bitcoin"
```

Analyze Federal Reserve news:

```bash
python main.py "Federal Reserve interest rates"
```

You can use normal search phrases, not just stock tickers.

For example:

```bash
python main.py "US semiconductor industry"
```

```bash
python main.py "artificial intelligence regulation"
```

```bash
python main.py "oil prices Middle East"
```

---

# Example Output

```text
========================================================================
QUANTUM NEWS BIAS
========================================================================

Query:              NVIDIA
Articles analyzed:  10

CLASSICAL NEWS SENTIMENT

Bias:               BULLISH
Score:              +0.318

Positive:            60.0%
Neutral:             30.0%
Negative:            10.0%

QUANTUM-DERIVED DISTRIBUTION

Bias:               BULLISH

Bullish:             55.8%
Neutral:             28.3%
Bearish:             15.9%

Confidence:          68.1%

Backend:             AerSimulator
```

The program also displays the highest-impact articles used in the calculation.

---

# Local Quantum Simulation

Local simulation is the default mode.

Run:

```bash
python main.py "NVIDIA"
```

This uses:

```text
Qiskit AerSimulator
```

No IBM Quantum account is required.

---

# IBM Quantum Hardware

The program can optionally execute the circuit on an IBM Quantum processor.

You must first configure your IBM Quantum credentials using Qiskit.

Once configured, run:

```bash
python main.py "NVIDIA" --backend ibm
```

The program will attempt to select an operational IBM Quantum backend with enough qubits for the circuit.

It will then:

```text
Build Circuit
     |
     v
Select IBM Backend
     |
     v
Transpile Circuit
     |
     v
Submit Quantum Job
     |
     v
Retrieve Measurements
     |
     v
Calculate Bias Distribution
```

Quantum hardware jobs may take longer than local simulation depending on backend availability and queue times.

---

# Shots

Quantum measurements are repeated multiple times.

The default is:

```text
4096 shots
```

You can change this.

Example:

```bash
python main.py "NVIDIA" --shots 8192
```

More shots reduce sampling noise but require more computation.

---

# JSON Output

For integration with another program:

```bash
python main.py "NVIDIA" --json
```

Example:

```json
{
  "query": "NVIDIA",
  "article_count": 10,
  "classical_score": 0.318,
  "classical_bias": "BULLISH",
  "positive_share": 0.6,
  "neutral_share": 0.3,
  "negative_share": 0.1,
  "quantum_bullish": 0.558,
  "quantum_neutral": 0.283,
  "quantum_bearish": 0.159,
  "quantum_bias": "BULLISH",
  "confidence": 0.681,
  "backend": "AerSimulator"
}
```

---

# News Sentiment Layer

Each article's title and description are passed through VADER sentiment analysis.

The resulting compound score ranges roughly from:

```text
-1.0 = strongly negative
 0.0 = neutral
+1.0 = strongly positive
```

The application then calculates:

- weighted average sentiment
- positive article percentage
- neutral article percentage
- negative article percentage
- sentiment dispersion
- agreement between articles
- source diversity

---

# Recency Weighting

Newer articles receive more influence.

The weighting follows an exponential decay model.

Approximately every 48 hours, an article's contribution is reduced by half.

This prevents older stories from overpowering more recent developments.

---

# Source Diversity

If several articles come from the same publisher, that source receives reduced influence.

For example:

```text
Source A
Source A
Source A
Source A
Source B
Source C
```

will not be treated as six completely independent opinions.

This helps reduce duplicate reporting and publisher concentration.

---

# Quantum Layer

The program currently uses three qubits.

Conceptually:

```text
Qubit 0
Market/news sentiment direction

Qubit 1
Positive vs negative article balance

Qubit 2
Agreement / uncertainty
```

Additional information such as source diversity and sentiment dispersion is encoded through quantum rotations and phase operations.

The circuit includes:

```text
RY rotations
RZ rotations
Hadamard gates
CNOT gates
Controlled-Z gates
Measurement
```

The qubits are entangled so the final measurement distribution depends on interactions between the encoded features.

---

# Quantum Interpretation

Measured states are mapped into three output classes:

```text
Bullish
Neutral
Bearish
```

The result is represented as probabilities.

Example:

```text
Bullish: 63%
Neutral: 22%
Bearish: 15%
```

These values represent the circuit's measurement distribution after the classical news features have been encoded.

They should not be interpreted as literal probabilities that an asset will rise or fall.

---

# Classical vs Quantum Comparison

One of the main goals of the project is to compare:

```text
Classical Sentiment
        VS
Quantum-Derived Bias
```

Example:

```text
Classical:

Bullish
Score +0.41

Quantum:

Bullish 68%
Neutral 19%
Bearish 13%
```

More interesting cases occur when they disagree:

```text
Classical:

Bullish

Quantum:

Neutral
```

or:

```text
Classical:

Bearish

Quantum:

Bullish
```

These disagreements can later be analyzed through historical backtesting.

---

# Historical Logging

Each run is automatically appended to:

```text
bias_history.jsonl
```

Each line contains one JSON record.

This allows future analysis such as:

```text
News Bias
     |
     v
Quantum Bias
     |
     v
Future Price Movement
     |
     v
Accuracy / Correlation Analysis
```

---

# Project Structure

```text
quantum_news_bias/
│
├── main.py
│
├── requirements.txt
│
├── README.md
│
├── .env.example
│
├── .gitignore
│
├── .cache/
│
└── bias_history.jsonl
```

---

# Cache

News API responses are cached temporarily inside:

```text
.cache/
```

This reduces unnecessary API requests during repeated testing.

The current cache lifetime is approximately 30 minutes.

---

# Future Improvements

Possible upgrades include:

## AI Sentiment Model

Replace or supplement VADER with:

```text
FinBERT
DeBERTa
RoBERTa
LLM sentiment classification
```

Finance-specific language models may better understand phrases such as:

```text
earnings miss
guidance raised
downgrade
liquidity concerns
rate cut
margin expansion
regulatory probe
```

---

## Multiple News Sources

Add additional providers such as:

```text
NewsAPI
Alpha Vantage News
Finnhub
Polygon
Financial Modeling Prep
RSS feeds
SEC filings
Federal Reserve releases
Reuters-compatible feeds
```

This would reduce dependence on a single provider.

---

# Entity Recognition

Automatically detect:

```text
Company names
Stock tickers
Countries
Politicians
Central banks
Industries
Commodities
Cryptocurrencies
```

This would allow articles to influence several related assets simultaneously.

---

# Macroeconomic Data

Potential future inputs:

```text
Federal funds rate
CPI
PPI
GDP
Treasury yields
Oil prices
Gold
VIX
Dollar index
Unemployment
PMI
Consumer sentiment
```

---

# Geopolitical Inputs

Possible geopolitical features:

```text
wars
sanctions
elections
trade restrictions
shipping disruptions
energy disruptions
military conflicts
export bans
semiconductor restrictions
```

---

# Market Data

A future version could combine news with:

```text
Price
Volume
RSI
MACD
ATR
Volatility
Options flow
Open interest
Market breadth
VWAP
Support/resistance
```

---

# Backtesting

Historical backtesting is one of the most important future features.

The basic design would be:

```text
Historical News
      |
      v
Classical Sentiment
      |
      v
Quantum Bias
      |
      v
Future Market Return
      |
      v
Compare Prediction vs Reality
```

Possible time horizons:

```text
1 hour
4 hours
1 day
3 days
1 week
1 month
```

Metrics could include:

```text
Directional accuracy
Correlation
Precision
Recall
Brier score
Calibration error
Sharpe ratio
Maximum drawdown
```

---

# Research Goal

The useful question is not:

> Can a quantum computer magically predict the stock market?

The useful question is:

> Does quantum feature transformation provide measurable information that improves a classical model compared with classical features alone?

A proper experiment should compare at least three systems:

```text
Model A
Classical sentiment only

Model B
Quantum-derived features only

Model C
Classical + quantum features
```

Their results can then be compared against historical outcomes.

If Model C consistently performs better on unseen data, the quantum layer may contain useful information.

If it does not, the experiment still produces a useful negative result.

---

# Security

Never hard-code API keys.

Bad:

```python
API_KEY = "abc123..."
```

Use environment variables instead:

```python
api_key = os.getenv("GNEWS_API_KEY")
```

Keep `.env` inside `.gitignore`.

Never commit:

```text
GNews API keys
IBM Quantum credentials
Cloud API tokens
Database passwords
Private keys
```

---

# Disclaimer

Quantum News Bias is an experimental research project.

It does not provide financial advice, investment recommendations, or guaranteed predictions.

The quantum circuit is currently being used as an experimental nonlinear feature transformation.

A quantum-derived probability such as:

```text
Bullish: 70%
```

does not mean there is a verified 70% probability that an asset will increase in price.

Any predictive usefulness must be demonstrated through proper historical testing, out-of-sample evaluation, and statistical validation.

---

# Version

```text
Quantum News Bias
Version 1.0
Standalone Research Build
```

Future versions can expand the system into a hybrid news, market, macroeconomic, geopolitical, AI, and quantum research platform.
