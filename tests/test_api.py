"""
Unit tests for the FastAPI layer (src/api/main.py).

Uses FastAPI's TestClient so no real HTTP server is needed.
All tests are fully deterministic — no I/O, no network.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def _minimal_body():
    """Minimal valid request body that satisfies every required Decision field."""
    return {
        "ticker": "TEST",
        "as_of": "2025-08-11",
        "recommendation": "BUY",
        "target_price_12m": 120.0,
        "expected_total_return_pct": 15.0,
        "risk_rating": "Medium",
        "thesis": ["Strong growth momentum"],
        "key_risks": ["Competition from incumbents"],
        "valuation": {"blended": 120.0},
        "scenarios": {
            "bull": {"prob": 0.25, "fair_value": 150.0},
            "base": {"prob": 0.50, "fair_value": 120.0},
            "bear": {"prob": 0.25, "fair_value": 90.0},
        },
    }


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


def test_health_returns_200():
    r = client.get("/health")
    assert r.status_code == 200


def test_health_body():
    r = client.get("/health")
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# POST /analyze — happy path
# ---------------------------------------------------------------------------


def test_analyze_minimal_returns_200():
    r = client.post("/analyze", json=_minimal_body())
    assert r.status_code == 200


def test_analyze_returns_decision_ticker():
    r = client.post("/analyze", json=_minimal_body())
    assert r.json()["ticker"] == "TEST"


def test_analyze_returns_decision_recommendation():
    r = client.post("/analyze", json=_minimal_body())
    assert r.json()["recommendation"] == "BUY"


def test_analyze_returns_technicals_block():
    r = client.post("/analyze", json=_minimal_body())
    assert "technicals" in r.json()


def test_analyze_returns_sentiment_block():
    r = client.post("/analyze", json=_minimal_body())
    assert "sentiment" in r.json()


def test_analyze_returns_valuation_block():
    r = client.post("/analyze", json=_minimal_body())
    data = r.json()
    assert "valuation" in data
    assert data["valuation"]["blended"] == 120.0


def test_analyze_returns_scenarios():
    r = client.post("/analyze", json=_minimal_body())
    scenarios = r.json()["scenarios"]
    assert set(scenarios.keys()) == {"bull", "base", "bear"}


# ---------------------------------------------------------------------------
# POST /analyze — with optional engine sections
# ---------------------------------------------------------------------------


def test_analyze_with_precomputed_technicals():
    body = _minimal_body()
    body["technicals"] = {"trend": "Up", "ma_cross": "50>200", "rsi_14": 72.0}
    r = client.post("/analyze", json=body)
    assert r.status_code == 200
    assert r.json()["technicals"]["rsi_14"] == 72.0
    assert r.json()["technicals"]["trend"] == "Up"


def test_analyze_with_sentiment_dict():
    body = _minimal_body()
    body["sentiment"] = {"analyst_consensus": "Buy", "avg_target": 130.0}
    r = client.post("/analyze", json=body)
    assert r.status_code == 200
    assert r.json()["sentiment"]["analyst_consensus"] == "Buy"


def test_analyze_with_fundamentals():
    body = _minimal_body()
    body["fundamentals"] = {"revenue_history": [100.0, 110.0, 121.0, 133.1]}
    r = client.post("/analyze", json=body)
    assert r.status_code == 200
    assert "rev_cagr_3y" in r.json()["assumptions"]


def test_analyze_with_macro():
    body = _minimal_body()
    body["macro"] = {"rate_regime": "Stable", "sector": "Technology"}
    r = client.post("/analyze", json=body)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /analyze — assumptions override
# ---------------------------------------------------------------------------


def test_analyze_assumptions_passthrough():
    body = _minimal_body()
    body["assumptions"] = {"rev_cagr_3y": 0.15}
    r = client.post("/analyze", json=body)
    assert r.status_code == 200
    assert r.json()["assumptions"]["rev_cagr_3y"] == 0.15


def test_analyze_caller_assumptions_not_overwritten_by_engine():
    body = _minimal_body()
    body["assumptions"] = {"rev_cagr_3y": 0.99}
    body["fundamentals"] = {"revenue_history": [100.0, 110.0, 121.0, 133.1]}
    r = client.post("/analyze", json=body)
    assert r.status_code == 200
    # Engine computes 0.1; caller supplied 0.99 — must not be overwritten
    assert abs(r.json()["assumptions"]["rev_cagr_3y"] - 0.99) < 1e-9


def test_analyze_no_assumptions_key_is_ok():
    """Omitting 'assumptions' entirely (None default) must not raise."""
    body = _minimal_body()
    r = client.post("/analyze", json=body)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /analyze — validation errors (422)
# ---------------------------------------------------------------------------


def test_analyze_invalid_recommendation_returns_422():
    body = _minimal_body()
    body["recommendation"] = "STRONG_BUY"
    r = client.post("/analyze", json=body)
    assert r.status_code == 422


def test_analyze_missing_ticker_returns_422():
    body = _minimal_body()
    del body["ticker"]
    r = client.post("/analyze", json=body)
    assert r.status_code == 422


def test_analyze_missing_valuation_returns_422():
    body = _minimal_body()
    del body["valuation"]
    r = client.post("/analyze", json=body)
    assert r.status_code == 422


def test_analyze_invalid_risk_rating_returns_422():
    body = _minimal_body()
    body["risk_rating"] = "Extreme"
    r = client.post("/analyze", json=body)
    assert r.status_code == 422


def test_analyze_scenario_prob_out_of_range_returns_422():
    body = _minimal_body()
    body["scenarios"]["bull"]["prob"] = 1.5
    r = client.post("/analyze", json=body)
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /analyze/{ticker} — template endpoint
# ---------------------------------------------------------------------------


def test_template_returns_200():
    r = client.get("/analyze/AAPL")
    assert r.status_code == 200


def test_template_ticker_injected():
    r = client.get("/analyze/AAPL")
    assert r.json()["ticker"] == "AAPL"


def test_template_ticker_uppercased():
    r = client.get("/analyze/aapl")
    assert r.json()["ticker"] == "AAPL"


def test_template_has_required_keys():
    r = client.get("/analyze/MSFT")
    data = r.json()
    required = [
        "ticker",
        "as_of",
        "recommendation",
        "target_price_12m",
        "expected_total_return_pct",
        "risk_rating",
        "thesis",
        "key_risks",
        "valuation",
        "scenarios",
    ]
    for key in required:
        assert key in data, f"Missing key: {key}"


def test_template_scenarios_have_three_keys():
    r = client.get("/analyze/TSLA")
    assert set(r.json()["scenarios"].keys()) == {"bull", "base", "bear"}


def test_template_different_tickers():
    for ticker in ["NVDA", "GOOG", "AMZN"]:
        r = client.get(f"/analyze/{ticker}")
        assert r.status_code == 200
        assert r.json()["ticker"] == ticker


# ---------------------------------------------------------------------------
# POST /analyze/html — HTML report endpoint
# ---------------------------------------------------------------------------


def test_analyze_html_returns_200():
    r = client.post("/analyze/html", json=_minimal_body())
    assert r.status_code == 200


def test_analyze_html_content_type_is_html():
    r = client.post("/analyze/html", json=_minimal_body())
    assert "text/html" in r.headers["content-type"]


def test_analyze_html_contains_ticker():
    r = client.post("/analyze/html", json=_minimal_body())
    assert "TEST" in r.text


def test_analyze_html_contains_recommendation():
    r = client.post("/analyze/html", json=_minimal_body())
    assert "BUY" in r.text


def test_analyze_html_is_valid_html_document():
    r = client.post("/analyze/html", json=_minimal_body())
    assert "<html" in r.text.lower()
