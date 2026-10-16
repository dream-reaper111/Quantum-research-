# Quantum News Bias

A standalone Python research project that combines:

- GNews article retrieval
- VADER sentiment analysis
- article recency weighting
- publisher-diversity weighting
- a three-qubit Qiskit feature circuit
- local Aer simulation
- optional IBM Quantum hardware execution
- JSONL history logging

## Important

This project is an experiment. The quantum circuit is being used as a nonlinear
probabilistic feature transform. Its output should **not** be interpreted as proof
that quantum computing predicts markets better than classical models.

## 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install packages

```bash
pip install -r requirements.txt
```

## 3. Configure GNews

Create a free GNews account, then:

```bash
cp .env.example .env
nano .env
```

Add:

```text
GNEWS_API_KEY=YOUR_KEY
```

## 4. Run locally

```bash
python main.py "NVIDIA"
```

Other examples:

```bash
python main.py "Federal Reserve interest rates"
python main.py "Bitcoin" --shots 8192
python main.py "Tesla" --json
```

## 5. IBM Quantum hardware

First save IBM credentials using the procedure documented by IBM Quantum.
Then run:

```bash
python main.py "NVIDIA" --backend ibm
```

The program selects a least-busy operational IBM QPU with at least three qubits,
transpiles the circuit for that QPU, and submits it using Sampler job mode.

## Output

Example shape:

```text
CLASSICAL NEWS SENTIMENT
  Bias:             BULLISH
  Score:            +0.318
  Positive:          60.0%
  Neutral:           30.0%
  Negative:          10.0%

QUANTUM-DERIVED DISTRIBUTION
  Bias:             BULLISH
  Bullish:           55.8%
  Neutral:           28.3%
  Bearish:           15.9%
```

Every run is appended to:

```text
bias_history.jsonl
```

## Design

```text
GNews
  ↓
headline + description
  ↓
VADER sentiment
  ↓
recency + source weighting
  ↓
feature vector
  ↓
3-qubit Qiskit circuit
  ↓
Aer simulator OR IBM QPU
  ↓
bullish / neutral / bearish distribution
```

## Next logical upgrades

- FinBERT or another finance-specific language model
- multiple news providers
- source credibility weighting
- named-entity extraction
- ticker recognition
- macroeconomic feature feeds
- backtesting against future returns
- calibration/Brier scoring
- database storage
- web dashboard
