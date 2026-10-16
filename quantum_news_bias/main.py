#!/usr/bin/env python3
"""
Quantum News Bias
-----------------
Standalone research tool:
1. Pulls recent news from GNews.
2. Scores headline/description sentiment with VADER.
3. Applies recency + source-diversity weighting.
4. Encodes the classical news features into a small Qiskit circuit.
5. Runs locally with Aer or optionally on an IBM Quantum backend.
6. Prints classical and quantum-derived bias side-by-side.

This is an experimental research tool, not a trading system or financial advice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import requests
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager

load_dotenv()

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
HISTORY_FILE = Path("bias_history.jsonl")


@dataclass
class Article:
    title: str
    description: str
    source: str
    url: str
    published_at: str
    sentiment: float = 0.0
    weight: float = 1.0


@dataclass
class BiasResult:
    query: str
    timestamp_utc: str
    article_count: int
    classical_score: float
    classical_bias: str
    positive_share: float
    neutral_share: float
    negative_share: float
    quantum_bullish: float
    quantum_neutral: float
    quantum_bearish: float
    quantum_bias: str
    confidence: float
    backend: str
    features: dict[str, float]


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def label_bias(score: float, threshold: float = 0.12) -> str:
    if score > threshold:
        return "BULLISH"
    if score < -threshold:
        return "BEARISH"
    return "NEUTRAL"


def cached_get(url: str, params: dict[str, Any], ttl_minutes: int = 30) -> dict:
    key_data = url + json.dumps(params, sort_keys=True)
    key = hashlib.sha256(key_data.encode()).hexdigest()
    path = CACHE_DIR / f"{key}.json"

    if path.exists():
        age = datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
        if age < ttl_minutes * 60:
            return json.loads(path.read_text())

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    path.write_text(json.dumps(data, indent=2))
    return data


def fetch_gnews(query: str, max_articles: int = 10) -> list[Article]:
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        raise RuntimeError("GNEWS_API_KEY is missing. Put it in your .env file.")

    params = {
        "q": query,
        "lang": "en",
        "max": min(max_articles, 10),
        "sortby": "publishedAt",
        "apikey": api_key,
    }
    data = cached_get("https://gnews.io/api/v4/search", params)
    articles = []

    for item in data.get("articles", []):
        articles.append(
            Article(
                title=(item.get("title") or "").strip(),
                description=(item.get("description") or "").strip(),
                source=((item.get("source") or {}).get("name") or "Unknown").strip(),
                url=(item.get("url") or "").strip(),
                published_at=(item.get("publishedAt") or "").strip(),
            )
        )

    # De-duplicate by normalized title.
    seen = set()
    unique = []
    for a in articles:
        key = " ".join(a.title.lower().split())
        if key and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


def age_hours(iso_time: str) -> float:
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600)
    except Exception:
        return 24.0


def analyze_articles(articles: list[Article]) -> dict[str, float]:
    analyzer = SentimentIntensityAnalyzer()

    source_counts = Counter(a.source for a in articles)
    weighted_scores = []
    raw_scores = []

    for a in articles:
        text = f"{a.title}. {a.description}".strip()
        score = analyzer.polarity_scores(text)["compound"]

        # Exponential recency decay: half influence about every 48 hours.
        recency_weight = math.exp(-math.log(2) * age_hours(a.published_at) / 48.0)

        # Reduce influence if many stories come from the same publisher.
        diversity_weight = 1.0 / math.sqrt(max(1, source_counts[a.source]))

        a.sentiment = score
        a.weight = recency_weight * diversity_weight

        raw_scores.append(score)
        weighted_scores.append((score, a.weight))

    if not weighted_scores:
        raise RuntimeError("No usable articles were returned for this query.")

    total_weight = sum(w for _, w in weighted_scores) or 1.0
    weighted_mean = sum(s * w for s, w in weighted_scores) / total_weight

    arr = np.array(raw_scores, dtype=float)
    positive = float(np.mean(arr > 0.05))
    negative = float(np.mean(arr < -0.05))
    neutral = max(0.0, 1.0 - positive - negative)
    dispersion = float(np.std(arr))
    agreement = clamp(abs(weighted_mean) / max(0.10, dispersion + 0.08), 0.0, 1.0)

    return {
        "sentiment_mean": float(clamp(weighted_mean, -1.0, 1.0)),
        "positive_share": positive,
        "neutral_share": neutral,
        "negative_share": negative,
        "dispersion": float(clamp(dispersion, 0.0, 1.0)),
        "agreement": agreement,
        "source_diversity": float(
            clamp(len(source_counts) / max(1, len(articles)), 0.0, 1.0)
        ),
    }


def build_quantum_circuit(features: dict[str, float]) -> QuantumCircuit:
    """
    Three measured qubits encode:
      q0: direction / sentiment mean
      q1: positive-vs-negative balance
      q2: agreement / uncertainty

    Entanglement deliberately couples the feature channels.
    This is an experimental feature transform, not proof of predictive advantage.
    """
    mean = clamp(features["sentiment_mean"], -1.0, 1.0)
    balance = clamp(features["positive_share"] - features["negative_share"], -1.0, 1.0)
    agreement = clamp(features["agreement"], 0.0, 1.0)
    diversity = clamp(features["source_diversity"], 0.0, 1.0)

    qc = QuantumCircuit(3, 3)

    # Map [-1, 1] -> [0, pi]
    qc.ry((mean + 1.0) * math.pi / 2.0, 0)
    qc.ry((balance + 1.0) * math.pi / 2.0, 1)
    qc.ry(agreement * math.pi, 2)

    # Encode source diversity as phase information.
    qc.rz(diversity * math.pi, 0)
    qc.rz((1.0 - diversity) * math.pi / 2.0, 1)

    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cz(2, 0)

    # Interference layer.
    qc.h(0)
    qc.ry(features["dispersion"] * math.pi / 2.0, 2)

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def counts_to_probabilities(counts: dict[str, int]) -> tuple[float, float, float]:
    """
    Convert 3-bit outcomes into directional classes.

    We use q0/q1 as directional votes:
      00 -> bearish
      11 -> bullish
      mixed -> neutral

    q2 modulates uncertainty by moving some mass toward neutral when q2=1.
    """
    total = sum(counts.values()) or 1
    bull = bear = neutral = 0.0

    for bits, n in counts.items():
        p = n / total
        bits = bits.replace(" ", "").zfill(3)

        # Qiskit bitstring is c2 c1 c0.
        q2, q1, q0 = [int(x) for x in bits[-3:]]

        if q0 == 1 and q1 == 1:
            bull += p
        elif q0 == 0 and q1 == 0:
            bear += p
        else:
            neutral += p

        if q2 == 1:
            # Uncertainty qubit moves a fraction of directional mass toward neutral.
            shift = 0.20 * p
            if q0 == 1 and q1 == 1:
                bull -= shift
                neutral += shift
            elif q0 == 0 and q1 == 0:
                bear -= shift
                neutral += shift

    s = bull + bear + neutral
    return bull / s, neutral / s, bear / s


def run_local(qc: QuantumCircuit, shots: int) -> tuple[dict[str, int], str]:
    try:
        from qiskit_aer import AerSimulator
    except ImportError as e:
        raise RuntimeError(
            "Local simulation requires qiskit-aer. Run: pip install qiskit-aer"
        ) from e

    backend = AerSimulator()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa = pm.run(qc)
    job = backend.run(isa, shots=shots)
    counts = job.result().get_counts()
    return dict(counts), "AerSimulator"


def run_ibm(qc: QuantumCircuit, shots: int) -> tuple[dict[str, int], str]:
    """
    IBM hardware path for qiskit-ibm-runtime 0.50+.

    Requires IBM credentials already saved locally, or the environment variables
    accepted by IBM's client. Open/free plans use job mode rather than sessions.
    """
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime.executor_sampler import Sampler

    service = QiskitRuntimeService()
    backend = service.least_busy(
        operational=True,
        simulator=False,
        min_num_qubits=3,
    )

    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa = pm.run(qc)

    sampler = Sampler(mode=backend)
    job = sampler.run([isa], shots=shots)
    result = job.result()[0]

    # The measurement register created by QuantumCircuit(3, 3) is named "c".
    counts = result.data.c.get_counts()
    return dict(counts), backend.name


def run_quantum(
    features: dict[str, float],
    backend_mode: str,
    shots: int,
) -> tuple[float, float, float, str]:
    qc = build_quantum_circuit(features)

    if backend_mode == "ibm":
        counts, backend_name = run_ibm(qc, shots)
    else:
        counts, backend_name = run_local(qc, shots)

    bull, neutral, bear = counts_to_probabilities(counts)
    return bull, neutral, bear, backend_name


def quantum_label(bull: float, neutral: float, bear: float) -> str:
    vals = {"BULLISH": bull, "NEUTRAL": neutral, "BEARISH": bear}
    return max(vals, key=vals.get)


def append_history(result: BiasResult) -> None:
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(result)) + "\n")


def print_report(result: BiasResult, articles: list[Article]) -> None:
    print("\n" + "=" * 72)
    print("QUANTUM NEWS BIAS")
    print("=" * 72)
    print(f"Query:              {result.query}")
    print(f"Articles analyzed:  {result.article_count}")
    print(f"Timestamp (UTC):    {result.timestamp_utc}")
    print()
    print("CLASSICAL NEWS SENTIMENT")
    print(f"  Bias:             {result.classical_bias}")
    print(f"  Score:            {result.classical_score:+.3f}")
    print(f"  Positive:         {result.positive_share * 100:5.1f}%")
    print(f"  Neutral:          {result.neutral_share * 100:5.1f}%")
    print(f"  Negative:         {result.negative_share * 100:5.1f}%")
    print()
    print("QUANTUM-DERIVED DISTRIBUTION")
    print(f"  Bias:             {result.quantum_bias}")
    print(f"  Bullish:          {result.quantum_bullish * 100:5.1f}%")
    print(f"  Neutral:          {result.quantum_neutral * 100:5.1f}%")
    print(f"  Bearish:          {result.quantum_bearish * 100:5.1f}%")
    print(f"  Confidence:       {result.confidence * 100:5.1f}%")
    print(f"  Backend:          {result.backend}")
    print()
    print("TOP ARTICLES")
    for i, a in enumerate(
        sorted(articles, key=lambda x: abs(x.sentiment) * x.weight, reverse=True)[:5],
        start=1,
    ):
        print(f"  {i}. [{a.sentiment:+.2f}] {a.title}")
        print(f"     {a.source} | {a.published_at}")
    print("=" * 72)
    print("Research only. Quantum probabilities are an experimental feature transform,")
    print("not evidence of a market-prediction advantage or financial advice.\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="News sentiment + Qiskit bias experiment")
    parser.add_argument("query", help='News query, e.g. "NVIDIA" or "Federal Reserve"')
    parser.add_argument("--backend", choices=["local", "ibm"], default="local")
    parser.add_argument("--articles", type=int, default=10)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    try:
        articles = fetch_gnews(args.query, args.articles)
        features = analyze_articles(articles)

        bull, neutral, bear, backend_name = run_quantum(
            features=features,
            backend_mode=args.backend,
            shots=args.shots,
        )

        classical_score = features["sentiment_mean"]
        confidence = clamp(
            0.55 * max(bull, neutral, bear) +
            0.25 * features["agreement"] +
            0.20 * features["source_diversity"],
            0.0,
            1.0,
        )

        result = BiasResult(
            query=args.query,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            article_count=len(articles),
            classical_score=classical_score,
            classical_bias=label_bias(classical_score),
            positive_share=features["positive_share"],
            neutral_share=features["neutral_share"],
            negative_share=features["negative_share"],
            quantum_bullish=bull,
            quantum_neutral=neutral,
            quantum_bearish=bear,
            quantum_bias=quantum_label(bull, neutral, bear),
            confidence=confidence,
            backend=backend_name,
            features=features,
        )

        append_history(result)

        if args.json:
            print(json.dumps(asdict(result), indent=2))
        else:
            print_report(result, articles)
        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
